#!/usr/bin/env python3
"""Removal tripwire: no live page vanishes in a publish unrecorded.

One of the publish guards the Test, Build and Release Standard
names (§1): a removal tripwire against what is live, placed
inside the deploy (issue #37). tools/check-publish-set.py proves
the staged set is complete against the staged sitemap and the
staged catalogue — but both sides of that proof come from the
same tree. If a page leaves the tree and the sitemap together,
or a bad generation shrinks both, every standing check passes
while the page vanishes from the site. This check compares the
sitemap the live site serves now against the sitemap this
publish is about to serve:

- A live URL missing from the staged sitemap is a removal.
- A removal recorded in retired-pages.txt passes, and is named
  in the output: a page retirement recorded as deliberate
  satisfies the tripwire.
- Any other removal fails, naming the URLs, and the deploy
  stops before anything is published.
- If the live sitemap cannot be read, the tripwire cannot pass:
  the check fails rather than waving the publish through.

Scope: sitemap URLs — the site's pages and listings. Assets
are not compared; they carry their own versioning rules.

Usage:  python3 tools/check-removal-tripwire.py
          [--live URL] [--live-file FILE] [--staged FILE]
          [--retired FILE]
Exit 0 = nothing unrecorded vanishes, 1 = a removal or a
failure to check.
"""

import re
import sys
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SITE = "https://actually-free.com"
LIVE_URL = SITE + "/sitemap.xml"
DEFAULT_STAGED = ROOT / "sitemap.xml"
DEFAULT_RETIRED = ROOT / "retired-pages.txt"


def sitemap_urls(text):
    return [u.strip() for u in re.findall(r"<loc>([^<]+)</loc>", text)]


def url_path(url):
    path = url[len(SITE):] if url.startswith(SITE) else url
    return path or "/"


def recorded_retirements(text):
    """One entry per line: a path (/suggest) or a full URL.

    Blank lines and lines starting with # are not entries; an
    entry is the first whitespace-separated token on its line, so
    a date or a reason may follow it on the same line.
    """
    paths = set()
    for line in text.splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        entry = line.split()[0]
        paths.add(url_path(entry))
    return paths


def find_removals(live_text, staged_text, retired_text):
    """Return (unrecorded, recorded) removal URL lists."""
    staged = set(sitemap_urls(staged_text))
    retired = recorded_retirements(retired_text)
    unrecorded, recorded = [], []
    for url in sitemap_urls(live_text):
        if url in staged:
            continue
        if url_path(url) in retired:
            recorded.append(url)
        else:
            unrecorded.append(url)
    return unrecorded, recorded


def fetch_live(url):
    req = urllib.request.Request(
        url, headers={"User-Agent": "actually-free-removal-tripwire"})
    with urllib.request.urlopen(req, timeout=20) as res:
        return res.read().decode("utf-8", errors="replace")


def run(live_text, staged_text, retired_text):
    if not sitemap_urls(live_text):
        print("check-removal-tripwire: the live sitemap lists no URLs — "
              "the tripwire cannot pass on an empty read.")
        return 1
    if not sitemap_urls(staged_text):
        print("check-removal-tripwire: the staged sitemap lists no URLs.")
        return 1
    unrecorded, recorded = find_removals(live_text, staged_text,
                                         retired_text)
    for url in recorded:
        print(f"check-removal-tripwire: recorded deliberate retirement: "
              f"{url}")
    if unrecorded:
        print(f"check-removal-tripwire: {len(unrecorded)} live page(s) "
              f"vanish in this publish with no retirement recorded:")
        for url in unrecorded:
            print(f"  - {url}")
        print("Record a deliberate retirement in retired-pages.txt, "
              "or restore the page.")
        return 1
    print(f"check-removal-tripwire: OK — {len(sitemap_urls(live_text))} "
          f"live URLs, {len(recorded)} recorded retirement(s), "
          f"nothing unrecorded vanishes.")
    return 0


def main(argv):
    live_file = staged_file = retired_file = None
    live_url = LIVE_URL
    args = list(argv)
    while args:
        flag = args.pop(0)
        if flag == "--live-file":
            live_file = Path(args.pop(0))
        elif flag == "--live":
            live_url = args.pop(0)
        elif flag == "--staged":
            staged_file = Path(args.pop(0))
        elif flag == "--retired":
            retired_file = Path(args.pop(0))
        else:
            print(f"check-removal-tripwire: unknown argument {flag}")
            return 1
    staged_path = staged_file or DEFAULT_STAGED
    retired_path = retired_file or DEFAULT_RETIRED
    try:
        staged_text = staged_path.read_text(encoding="utf-8")
    except OSError as err:
        print(f"check-removal-tripwire: cannot read the staged sitemap "
              f"{staged_path}: {err}")
        return 1
    retired_text = (retired_path.read_text(encoding="utf-8")
                    if retired_path.is_file() else "")
    if live_file is not None:
        try:
            live_text = live_file.read_text(encoding="utf-8")
        except OSError as err:
            print(f"check-removal-tripwire: cannot read the live sitemap "
                  f"file {live_file}: {err}")
            return 1
    else:
        try:
            live_text = fetch_live(live_url)
        except Exception as err:
            print(f"check-removal-tripwire: cannot read the live sitemap "
                  f"{live_url}: {err} — the tripwire cannot pass.")
            return 1
    return run(live_text, staged_text, retired_text)


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
