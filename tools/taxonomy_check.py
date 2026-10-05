#!/usr/bin/env python3
"""Taxonomy drift check for the Actually Free directory.

Reads the seed corpus (same source as generate.py), counts live apps per
top-level category, and flags:
  - any top-level category with more than 80 apps (consider splitting)
  - any app in a generic bucket: Tools, Other, General, Misc, Miscellaneous
  - any malformed category name (contains "/")

Exits 0 when clean, 1 when drift is found, so it can gate manual work:
    python3 tools/taxonomy_check.py
"""
import json
import os
import sys

SEED = os.path.expanduser("~/workspace/certifiable-apps/apps-seed.json")
LIMIT = 80
GENERIC = {"tools", "other", "general", "misc", "miscellaneous"}
# Same label fixups as generate.py: the directory shortens "Comms & System"
# to "Comms" in the filter row, so the check counts what the site shows.
CATEGORY_FIXUPS = {
    "Comms & System": "Comms",
    "Utilities / Comms & System": "Utilities",
}

def live_category(rec):
    return CATEGORY_FIXUPS.get(rec["category"], rec["category"])

# Mirrors generate.py: QR Cards is hard-coded into the live corpus.
QR_CARDS = {"name": "QR Cards", "category": "Utilities",
            "subcategory": "QR codes", "status": "include"}

def main():
    with open(SEED) as f:
        seed = json.load(f)
    live = [r for r in seed if r.get("status") in ("include", "per-badge")]
    live.append(QR_CARDS)

    counts = {}
    for r in live:
        cat = live_category(r)
        counts[cat] = counts.get(cat, 0) + 1

    flags = []
    for cat in sorted(counts, key=counts.get, reverse=True):
        print(f"  {cat}: {counts[cat]}")
        if counts[cat] > LIMIT:
            flags.append(f"'{cat}' has {counts[cat]} apps (over {LIMIT}) - consider splitting it")

    for r in live:
        sub = (r.get("subcategory") or "").strip()
        if sub.lower() in GENERIC:
            flags.append(f"'{r['name']}' sits in generic bucket '{sub}'")
        if "/" in live_category(r):
            flags.append(f"'{r['name']}' has malformed category '{r['category']}'")

    if flags:
        print("\nDRIFT FOUND:")
        for fl in flags:
            print(f"  ! {fl}")
        return 1
    print("\nNo drift. Taxonomy is clean.")
    return 0

if __name__ == "__main__":
    sys.exit(main())
