"""Validation and incremental builds for the versioned Windows catalogue."""
import datetime
import json
import re
from pathlib import Path
from urllib.parse import urlsplit

INCLUDED = {'include', 'per-badge', 'free-enough'}
STATUSES = {'unverified', 'publisher', 'distributor', 'tested', 'unsupported'}


def valid_url(value):
    if not isinstance(value, str) or any(c.isspace() for c in value):
        return False
    try:
        p = urlsplit(value)
        return p.scheme in ('https', 'http') and bool(p.hostname) and not p.username and not p.password
    except ValueError:
        return False


def validate(records):
    errors = []
    packages, slugs = set(), set()
    for r in records:
        name = r.get('name', '<unnamed>')
        pkg = r.get('package', '')
        slug = re.sub(r'[^a-z0-9]+', '-', pkg.lower()).strip('-')
        if not pkg or pkg in packages or slug in slugs:
            errors.append(f'{name}: missing/duplicate package or slug')
        packages.add(pkg); slugs.add(slug)
        if r.get('platform') != 'windows':
            errors.append(f'{name}: platform must be windows')
        if r.get('status') not in INCLUDED | {'flag', 'exclude'}:
            errors.append(f'{name}: invalid publication status')
        if r.get('status') not in INCLUDED:
            continue
        urls = [r.get('official_url')] + [a.get('url') for a in r.get('alt_downloads', [])]
        for url in urls:
            if not valid_url(url):
                errors.append(f'{name}: invalid download URL {url!r}')
        winget = r.get('winget_id')
        if winget and not re.fullmatch(r'[A-Za-z0-9][A-Za-z0-9._+-]*\.[A-Za-z0-9._+-]+', winget):
            errors.append(f'{name}: invalid Winget identifier')
        evidence = r.get('windows11', {})
        status = evidence.get('status', 'unverified')
        if status not in STATUSES:
            errors.append(f'{name}: invalid Windows 11 status')
        if status != 'unverified':
            url = evidence.get('evidence_url', '')
            if not valid_url(url) or url.rstrip('/') == 'https://portableapps.com/download':
                errors.append(f'{name}: app-specific compatibility evidence required')
            try:
                datetime.date.fromisoformat(evidence.get('checked_at', ''))
            except (ValueError, TypeError):
                errors.append(f'{name}: compatibility check date required')
        if status == 'tested' and not all(evidence.get(k) for k in ('tested', 'version', 'architecture', 'build', 'test_report')):
            errors.append(f'{name}: tested status requires version, architecture, build and test report')
        if evidence.get('tested') and status != 'tested':
            errors.append(f'{name}: tested flag requires tested status')
    if errors:
        raise ValueError('\n'.join(errors))


def rebuild_windows(g):
    """Rebuild Windows pages; reuse existing report forms without reading secrets.

    Android records and pages remain the checked-in build snapshot. Full builds
    still use the Android research corpus. Missing old pages abort before writes.
    """
    root = Path(g.HERE)
    records = json.loads((root / 'data/windows-seed.json').read_text())
    validate(records)
    previous = json.loads((root / 'data/apps.json').read_text())
    android = [a for a in previous if a.get('platform', 'android') != 'windows']
    windows = [g.clean_record(r) for r in records if r.get('status') in INCLUDED]
    apps = sorted(android + windows, key=lambda a: a['name'].lower())
    # Clear derived links so excluded Windows siblings do not remain referenced.
    for app in apps:
        app.pop('sibling_slug', None); app.pop('sibling_platform', None)
    g.resolve_siblings(apps)
    pages = {}
    for app in windows:
        path = root / f"app/{app['slug']}.html"
        old = path.read_text()
        match = re.search(r'(?:<div class="feedback-row">|<p class="feedback-off").*?(?=\n  </article>)', old, re.S)
        if not match:
            raise ValueError(f'Cannot preserve report form in {path}; run full build with AF_ANDROID_SEED and feedback configuration')
        class ExistingForms:
            encoded = 'data-af-form=' in old
            def report_form(self, _app):
                return match.group(0)
        pages[path] = g.build_detail(app, ExistingForms())
    active = {a['slug'] for a in windows}
    removed = [root / f"app/{a['slug']}.html" for a in previous
               if a.get('platform') == 'windows' and a['slug'] not in active]
    for path, content in pages.items():
        path.write_text(content)
    for path in removed:
        path.unlink(missing_ok=True)
    g.write('data/apps.json', json.dumps(apps, indent=1, ensure_ascii=False) + '\n')
    g.write('sitemap.xml', g.build_sitemap(apps))
    # A fresh cache version is necessary to retire cached removed pages/data.
    build_id = datetime.datetime.now(datetime.timezone.utc).strftime('%Y%m%d%H%M%S')
    g.write('sw.js', g.build_sw(build_id))
    print(f'Windows build: {len(windows)} active, {len(removed)} withdrawn; Android snapshot preserved')
