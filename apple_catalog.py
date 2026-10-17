"""Validation for the macOS and iOS seed catalogues (Apple platforms).

Mirrors windows_catalog.py: the seed files are the reviewed source of
truth, generate.py assembles them into the site, and nothing ships
unless these checks pass. The bar is evidence: every included record
names the exact page its promise was verified on and the date.
"""
import datetime
import re
from urllib.parse import urlsplit

INCLUDED = {'include', 'per-badge', 'free-enough'}
STATUSES = INCLUDED | {'flag', 'exclude'}
MAC_ALT_LABELS = {'Mac App Store', 'Homebrew', 'GitHub', 'MacUpdate',
                  'F-Droid', 'SourceForge'}
IOS_PRIVACY = {'Data Not Collected', 'No tracking', 'Tracking declared',
               'Data collected, not tracked'}


def valid_url(value):
    if not isinstance(value, str) or any(c.isspace() for c in value):
        return False
    try:
        p = urlsplit(value)
        return p.scheme in ('https', 'http') and bool(p.hostname) \
            and not p.username and not p.password
    except ValueError:
        return False


def _is_appstore(url):
    try:
        p = urlsplit(url or '')
        return p.hostname in ('apps.apple.com', 'itunes.apple.com') \
            and '/app/' in p.path
    except ValueError:
        return False


def _slug(pkg):
    return re.sub(r'[^a-z0-9]+', '-', (pkg or '').lower()).strip('-')


def _base_errors(records, platform):
    errors = []
    packages, slugs = set(), set()
    for r in records:
        name = r.get('name', '<unnamed>')
        pkg = r.get('package', '')
        slug = _slug(pkg)
        if not pkg or pkg in packages or slug in slugs:
            errors.append(f'{name}: missing/duplicate package or slug')
        packages.add(pkg)
        slugs.add(slug)
        if r.get('platform') != platform:
            errors.append(f'{name}: platform must be {platform}')
        if r.get('status') not in STATUSES:
            errors.append(f'{name}: invalid publication status')
        if not r.get('name') or not r.get('category'):
            errors.append(f'{name}: name and category required')
    return errors


def _evidence_errors(r, name):
    errors = []
    ver = r.get('verification') or {}
    url = ver.get('evidence_url', '')
    if not valid_url(url):
        errors.append(f'{name}: verification evidence_url required '
                      f'(the exact page the promise was checked on)')
    try:
        datetime.date.fromisoformat(ver.get('checked_at', ''))
    except (ValueError, TypeError):
        errors.append(f'{name}: verification checked_at date required')
    return errors


def validate_macos(records):
    errors = _base_errors(records, 'macos')
    for r in records:
        if r.get('status') not in INCLUDED:
            continue
        name = r.get('name', '<unnamed>')
        store = (r.get('stores') or {}).get('appstore')
        if store and not _is_appstore(store):
            errors.append(f'{name}: stores.appstore must be an App Store app page')
        urls = [r.get('official_url')] + [a.get('url') for a in r.get('alt_downloads', [])]
        for url in urls:
            if url is not None and not valid_url(url):
                errors.append(f'{name}: invalid download URL {url!r}')
        for alt in r.get('alt_downloads', []):
            if alt.get('label') == 'Mac App Store' and not _is_appstore(alt.get('url')):
                errors.append(f'{name}: Mac App Store alternative must link to the App Store')
        if not r.get('official_url') and not store and not urls[1:]:
            errors.append(f'{name}: at least one download path required '
                          f'(official_url, Mac App Store or an alternative)')
        brew = r.get('brew_id')
        if brew and not re.fullmatch(r'[a-z0-9][a-z0-9@+._-]*', brew):
            errors.append(f'{name}: invalid Homebrew cask token')
        if r.get('status') == 'free-enough' and not r.get('free_enough_reason'):
            errors.append(f'{name}: free-enough records need free_enough_reason')
        errors += _evidence_errors(r, name)
    if errors:
        raise ValueError('\n'.join(errors))


def validate_ios(records):
    errors = _base_errors(records, 'ios')
    for r in records:
        if r.get('status') not in INCLUDED:
            continue
        name = r.get('name', '<unnamed>')
        store = (r.get('stores') or {}).get('appstore')
        if not _is_appstore(store or ''):
            errors.append(f'{name}: stores.appstore must be the app\'s App Store page')
        elif not re.search(r'/id\d+$', urlsplit(store).path):
            errors.append(f'{name}: App Store URL must end with the numeric app id')
        ver = r.get('verification') or {}
        if ver.get('method') != 'appstore':
            errors.append(f'{name}: verification method must be appstore')
        if r.get('status') == 'include':
            if ver.get('iap_free') is not True:
                errors.append(f'{name}: include requires iap_free verified '
                              f'(no In-App Purchases row on the App Store page)')
            if ver.get('no_ads_declared') is not True:
                errors.append(f'{name}: include requires no_ads_declared verified '
                              f'(age rating carries no Advertising descriptor)')
        if ver.get('privacy') not in IOS_PRIVACY:
            errors.append(f'{name}: verification privacy must be one of {sorted(IOS_PRIVACY)}')
        if r.get('status') == 'free-enough' and not r.get('free_enough_reason'):
            errors.append(f'{name}: free-enough records need free_enough_reason')
        errors += _evidence_errors(r, name)
    if errors:
        raise ValueError('\n'.join(errors))


def validate_cross_platform(apple_records, other_packages):
    """Apple packages and slugs must not collide with the rest of the
    catalogue: package is the corpus key and slug is the page path."""
    errors = []
    seen = set(other_packages)
    for r in apple_records:
        pkg = r.get('package', '')
        if pkg in seen:
            errors.append(f'{r.get("name")}: package {pkg} already used elsewhere; '
                          f'give the Apple listing its own key and link with sibling')
        seen.add(pkg)
    if errors:
        raise ValueError('\n'.join(errors))
