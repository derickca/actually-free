#!/usr/bin/env python3
"""Validate the macOS and iOS seeds, including cross-catalogue collisions."""
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from apple_catalog import validate_macos, validate_ios, validate_cross_platform


def main():
    mac = json.loads((ROOT / 'data/macos-seed.json').read_text())
    ios = json.loads((ROOT / 'data/ios-seed.json').read_text())
    validate_macos(mac)
    print(f'Validated {len(mac)} macOS seed records')
    validate_ios(ios)
    print(f'Validated {len(ios)} iOS seed records')

    others = set()
    for path in (ROOT / 'data/windows-seed.json', ROOT / 'data/apps-seed.json'):
        if path.exists():
            others |= {r['package'] for r in json.loads(path.read_text())}
    seed = Path.home() / 'workspace/certifiable-apps/apps-seed.json'
    if seed.exists():
        others |= {r['package'] for r in json.loads(seed.read_text())}
    validate_cross_platform(mac + ios, others)
    print('No package collisions with the rest of the catalogue')

    apps = json.loads((ROOT / 'data/apps.json').read_text())
    slugs = {a['slug'] for a in apps}
    for r in mac + ios:
        if r.get('sibling') and r['sibling'] not in \
                {a['package'] for a in apps} | {x['package'] for x in mac + ios}:
            print(f"WARNING: {r['name']}: sibling {r['sibling']} not in the catalogue")
    print('Done.')


if __name__ == '__main__':
    main()
