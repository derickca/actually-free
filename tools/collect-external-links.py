#!/usr/bin/env python3
"""Collect every external URL from the catalogue data files.

Walks data/apps.json and data/windows-seed.json recursively and prints
(or writes) the sorted set of unique http/https URLs, one per line.
Used by the link-check workflow; safe to run locally too.

Usage: python tools/collect-external-links.py [output-file]
"""
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SOURCES = [ROOT / "data" / "apps.json", ROOT / "data" / "windows-seed.json"]


def walk(node, found):
    if isinstance(node, str):
        if node.startswith(("http://", "https://")) and " " not in node and "{" not in node:
            found.add(node.strip())
    elif isinstance(node, dict):
        for value in node.values():
            walk(value, found)
    elif isinstance(node, list):
        for item in node:
            walk(item, found)


def main():
    urls = set()
    for source in SOURCES:
        walk(json.loads(source.read_text(encoding="utf-8")), urls)
    lines = "\n".join(sorted(urls)) + "\n"
    if len(sys.argv) > 1:
        Path(sys.argv[1]).write_text(lines, encoding="utf-8")
    else:
        sys.stdout.write(lines)
    print(f"{len(urls)} unique external URLs", file=sys.stderr)


if __name__ == "__main__":
    main()
