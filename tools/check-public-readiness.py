#!/usr/bin/env python3
"""Public-readiness guard: no personal information in tracked files.

The Privacy and Secrets Policy (agents-policy,
docs/privacy-and-secrets-policy.md, section 6) requires a
public-readiness guard that checks tracked files for personal
information. The names and values it looks for are themselves
private, so they never stand in this repo: they live in one
machine-local private file, provisioned by the owner once per
machine (the policy, section 3).

The file: the path in the AF_PRIVATE_FILE environment variable,
or ~/.actually-free-private/names.txt when the variable is unset.
One value per line; blank lines and lines starting with # are
ignored. Values are matched case-insensitively, on word
boundaries — so the GitHub account name, which the policy's
section 1 exempts and which contains a first name as a substring,
does not flood the report from every repository URL.

Run it by hand before a push, with the other local checks:

    python3 tools/check-public-readiness.py

It prints only the path and line number of each hit — never the
value it matched and never the line's text, because a report is
one of the places private information must never appear.

Exit codes: 0 = scanned, nothing found. 1 = hits found.
2 = NOT RUN (the private file is missing or unreadable) — a
check that could not run is not a pass, so the run says so.
"""

import os
import re
import subprocess
import sys

DEFAULT_PRIVATE_FILE = os.path.join(
    os.path.expanduser("~"), ".actually-free-private", "names.txt"
)


def load_needles():
    path = os.environ.get("AF_PRIVATE_FILE") or DEFAULT_PRIVATE_FILE
    try:
        with open(path, encoding="utf-8") as f:
            lines = f.read().splitlines()
    except OSError:
        return None, path
    needles = [
        line.strip()
        for line in lines
        if line.strip() and not line.strip().startswith("#")
    ]
    return needles, path


def tracked_files(root):
    out = subprocess.run(
        ["git", "-C", root, "ls-files"],
        capture_output=True, text=True, check=True,
    )
    return [line for line in out.stdout.splitlines() if line]


def main():
    needles, path = load_needles()
    if needles is None:
        print(f"NOT RUN: the private names file is not readable: {path}")
        print("The guard cannot scan without it; this is not a pass.")
        return 2
    if not needles:
        print(f"NOT RUN: the private names file holds no values: {path}")
        print("The guard cannot scan without values; this is not a pass.")
        return 2

    root = subprocess.run(
        ["git", "rev-parse", "--show-toplevel"],
        capture_output=True, text=True, check=True,
    ).stdout.strip()

    patterns = [
        re.compile(r"\b" + re.escape(n) + r"\b", re.IGNORECASE)
        for n in needles
    ]
    hits = 0
    for rel in tracked_files(root):
        full = os.path.join(root, rel)
        try:
            with open(full, encoding="utf-8", errors="ignore") as f:
                for lineno, line in enumerate(f, 1):
                    if any(p.search(line) for p in patterns):
                        print(f"HIT {rel}:{lineno}")
                        hits += 1
        except OSError:
            continue

    if hits:
        print(f"{hits} hit(s): personal information stands in tracked files.")
        return 1
    print("Clean: no tracked file carries a listed value.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
