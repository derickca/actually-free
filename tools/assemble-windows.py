#!/usr/bin/env python3
"""Assemble data/windows-seed.json from vetting verdict files.

Usage: python3 tools/assemble-windows.py <verdicts.json> [...] [--append]

Each verdict file is an array of:
  {"name", "verdict": "include"|"skip", "basket", "license": "oss"|"freeware",
   "personal_use", "free_enough", "free_enough_reason", "needs_account",
   "official_url", "alt_downloads": [{"label","url"}], "description", "notes"}

Only verdict=include rows become seed records. Without --append the seed
file is rewritten from the given verdict files; with --append new records
are added (existing packages are replaced by package id).
"""
import json
import os
import re
import sys

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SEED_PATH = os.path.join(HERE, "data", "windows-seed.json")


def package_id(name):
    base = re.sub(r"[^a-z0-9]+", ".", name.lower()).strip(".")
    return (base or "app") + ".windows"


def to_record(v):
    cat, _, sub = v["basket"].partition("/")
    return {
        "name": v["name"],
        "package": package_id(v["name"]),
        "platform": "windows",
        "status": "free-enough" if v.get("free_enough") else "include",
        "category": cat,
        "subcategory": sub,
        "description": v.get("description") or "",
        "license": v.get("license") or "",
        "personal_use": bool(v.get("personal_use")),
        "free_enough_reason": v.get("free_enough_reason") or "",
        "official_url": v.get("official_url") or "",
        "alt_downloads": v.get("alt_downloads") or [],
        "attrs": {
            "open_source": (v.get("license") == "oss"),
            "needs_account": bool(v.get("needs_account")),
        },
        "notes": v.get("notes") or "",
    }


def main():
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    append = "--append" in sys.argv[1:]
    if not args:
        print("usage: assemble-windows.py <verdicts.json> [...] [--append]")
        sys.exit(2)

    records = {}
    if append and os.path.exists(SEED_PATH):
        for r in json.load(open(SEED_PATH, encoding="utf-8")):
            records[r["package"]] = r

    n_skip = 0
    for path in args:
        verdicts = json.load(open(path, encoding="utf-8"))
        for v in verdicts:
            if v.get("verdict") != "include":
                n_skip += 1
                continue
            r = to_record(v)
            records[r["package"]] = r

    # disambiguate duplicate package ids
    seen = {}
    final = []
    for pkg, r in sorted(records.items()):
        if pkg in seen:
            i = 2
            while f"{pkg}.{i}" in seen:
                i += 1
            r["package"] = f"{pkg}.{i}"
            pkg = r["package"]
        seen[pkg] = True
        final.append(r)

    os.makedirs(os.path.dirname(SEED_PATH), exist_ok=True)
    with open(SEED_PATH, "w", encoding="utf-8") as f:
        json.dump(final, f, indent=1, ensure_ascii=False)
        f.write("\n")
    print(f"wrote {len(final)} records to data/windows-seed.json "
          f"({n_skip} verdict=skip omitted)")


if __name__ == "__main__":
    main()
