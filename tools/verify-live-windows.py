#!/usr/bin/env python3
"""Compare live Windows JSON and rendered pages with the checked-in build.

Requires curl. Does not submit forms or install applications.
"""
from concurrent.futures import ThreadPoolExecutor
import json
from pathlib import Path
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]
BASE = 'https://free.certifiable.media'

def get(path):
    result = subprocess.run(['curl', '-f', '-s', '-S', '-L', '--retry', '1',
                             '--max-time', '30', BASE + path], capture_output=True, text=True)
    if result.returncode:
        raise RuntimeError(f'{path}: {result.stderr.strip()}')
    return result.stdout

def main():
    expected = json.loads((ROOT / 'data/apps.json').read_text())
    live = json.loads(get('/data/apps.json'))
    windows = lambda apps: [a for a in apps if a.get('platform') == 'windows']
    if windows(live) != windows(expected):
        raise SystemExit(f'NOT DEPLOYED: live has {len(windows(live))} Windows records; expected {len(windows(expected))}, or content differs.')
    def check(app):
        path = f"/app/{app['slug']}.html"
        if get(path) != (ROOT / path.lstrip('/')).read_text():
            return f'{path}: rendered page differs'
    with ThreadPoolExecutor(max_workers=8) as pool:
        errors = [e for e in pool.map(check, windows(expected)) if e]
    if get('/sitemap.xml') != (ROOT / 'sitemap.xml').read_text():
        errors.append('Sitemap differs')
    if get('/sw.js') != (ROOT / 'sw.js').read_text():
        errors.append('Service worker differs')
    if errors:
        raise SystemExit('\n'.join(errors))
    print(f'VERIFIED: {len(windows(expected))} Windows records, all retained detail pages, sitemap and service worker match the build.')

if __name__ == '__main__':
    main()
