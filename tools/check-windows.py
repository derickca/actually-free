#!/usr/bin/env python3
"""Validate the Windows seed; optionally report HTTP failures without delisting."""
import argparse
from concurrent.futures import ThreadPoolExecutor
import json
from pathlib import Path
import sys
import urllib.error
import urllib.request

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from windows_catalog import INCLUDED, validate


def check(url):
    for attempt in range(2):
        try:
            req = urllib.request.Request(url, headers={'User-Agent': 'ActuallyFree-LinkAudit/1.0'})
            with urllib.request.urlopen(req, timeout=20) as response:
                sample = response.read(32768).decode('utf-8', errors='replace')
                soft = any(t in sample.lower() for t in ('<title>404', '<title>page not found'))
                return {'url': url, 'final_url': response.url, 'status': response.status,
                        'review': 'possible soft 404' if soft else None}
        except (urllib.error.URLError, TimeoutError, OSError) as error:
            code = getattr(error, 'code', None)
            result = {'url': url, 'status': code, 'error': str(error),
                      'review': 'broken candidate' if code in (404, 410) else 'blocked or transient; manual review'}
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--check-links', action='store_true')
    parser.add_argument('--output', default='windows-link-check.json')
    args = parser.parse_args()
    rows = json.loads((ROOT / 'data/windows-seed.json').read_text())
    validate(rows)
    print(f'Validated {len(rows)} seed records')
    if args.check_links:
        urls = sorted({url for r in rows if r['status'] in INCLUDED
                       for url in [r['official_url']] + [a['url'] for a in r.get('alt_downloads', [])]})
        with ThreadPoolExecutor(max_workers=8) as pool:
            results = list(pool.map(check, urls))
        Path(args.output).write_text(json.dumps(results, indent=2) + '\n')
        print(f'Checked {len(urls)} destinations; {sum(bool(r.get("review")) for r in results)} need review. No listings changed.')


if __name__ == '__main__':
    main()
