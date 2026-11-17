#!/usr/bin/env python3
"""Publish-set check: the staged tree holds the whole public site.

One of the publish guards the Test, Build and Release Standard
names (§1), placed inside the deploy (issue #37). The deploy
uploads the staged tree as it stands, so before anything is
published this check proves the staged tree is complete against
its own sitemap and its own catalogue:

1. Every URL in the staged sitemap.xml maps to a file in the
   staged tree, so a page named in the sitemap but missing from
   the tree fails here instead of 404ing on the live site.
2. Every listing in the staged data/apps.json has its page in
   the tree and its URL in the staged sitemap, so a listing
   whose page or sitemap entry a bad generation dropped fails
   here too.

Both sides of this proof come from the staged tree; the guard
against a page leaving the tree and the sitemap together is
the removal tripwire (tools/check-removal-tripwire.py), which
compares the staged sitemap against the live one.

Usage:  python3 tools/check-publish-set.py [--staged-dir DIR]
Exit 0 = the staged set is complete, 1 = failures found. With
no --staged-dir, the repository root is checked — the committed
tree is the site, so the same check runs before a push.
"""

import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SITE = "https://actually-free.com"


def url_to_file(url):
    path = url[len(SITE):] if url.startswith(SITE) else url
    if path in ("", "/"):
        return "index.html"
    if path.endswith("/"):
        return path.lstrip("/") + "index.html"
    return path.lstrip("/") + ".html"


def check(staged):
    failures = []

    sitemap_path = staged / "sitemap.xml"
    if not sitemap_path.is_file():
        return [f"no sitemap.xml in the staged tree: {staged}"]
    urls = re.findall(r"<loc>([^<]+)</loc>",
                      sitemap_path.read_text(encoding="utf-8"))
    if not urls:
        failures.append("the staged sitemap.xml lists no URLs")
    url_set = set(urls)

    for url in urls:
        rel = url_to_file(url)
        if not (staged / rel).is_file():
            failures.append(
                f"sitemap URL has no file in the staged tree: "
                f"{url} -> {rel}")

    apps_path = staged / "data" / "apps.json"
    if not apps_path.is_file():
        failures.append(f"no data/apps.json in the staged tree: "
                        f"{staged}")
        return failures
    try:
        apps = json.loads(apps_path.read_text(encoding="utf-8"))
    except ValueError as err:
        failures.append(f"data/apps.json does not parse: {err}")
        return failures
    for app in apps:
        slug = app.get("slug")
        if not slug:
            failures.append("a listing in data/apps.json has no slug")
            continue
        if not (staged / "app" / f"{slug}.html").is_file():
            failures.append(
                f"listing has no page in the staged tree: "
                f"{slug} -> app/{slug}.html")
        if f"{SITE}/app/{slug}" not in url_set:
            failures.append(
                f"listing has no URL in the staged sitemap: "
                f"{slug} -> {SITE}/app/{slug}")
    return failures


def main(argv):
    staged = ROOT
    args = list(argv)
    while args:
        flag = args.pop(0)
        if flag == "--staged-dir":
            staged = Path(args.pop(0))
        else:
            print(f"check-publish-set: unknown argument {flag}")
            return 1
    if not staged.is_dir():
        print(f"check-publish-set: the staged tree does not exist: "
              f"{staged}")
        return 1
    failures = check(staged)
    if failures:
        print(f"check-publish-set: {len(failures)} failure(s):")
        for f in failures:
            print(f"  - {f}")
        return 1
    urls = re.findall(r"<loc>([^<]+)</loc>",
                      (staged / "sitemap.xml").read_text(
                          encoding="utf-8"))
    apps = json.loads((staged / "data" / "apps.json").read_text(
        encoding="utf-8"))
    print(f"check-publish-set: OK — {len(urls)} sitemap URLs mapped "
          f"to files, {len(apps)} listings with a page and a sitemap "
          f"URL, in {staged}.")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
