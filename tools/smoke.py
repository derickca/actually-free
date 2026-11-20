#!/usr/bin/env python3
"""Deploy smoke for Actually Free — the checks named in docs/E2E.md.

Runs against the production copy that just published, in the deploy
run's first minutes. Three happy paths:

  1. The home page answers 200 and carries the directory's grid.
  2. data/apps.json answers 200, parses, and holds listings.
  3. The first listing's page answers 200 and carries its name.

Read-only. Exit 1 on any failure: in the deploy workflow that red
run is the loud alarm the E2E standard names, there being no
promotion to hold. Run by hand any time:

  python3 tools/smoke.py [--base https://actually-free.com]

--results <file> also writes the run's checks as JSON —
{ checks: [{ name, ok, detail? }], result } — the shape the
deploy's Build Tests report sends to the centre's run-
record home (issue #29). The Release Review runner imports
run_checks() for its heartbeat: the same three checks, one
source.
"""
import json
import sys
import urllib.request

BASE = "https://actually-free.com"
UA = {"User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/130.0 Safari/537.36"}

failures = []
results = []


def get(url):
    req = urllib.request.Request(url, headers=UA)
    with urllib.request.urlopen(req, timeout=20) as resp:
        return resp.status, resp.read().decode("utf-8", "replace")


def check(name, cond, detail=""):
    print(f"[{'PASS' if cond else 'FAIL'}] {name}" +
          (f" — {detail}" if detail and not cond else ""))
    entry = {"name": name, "ok": bool(cond)}
    if detail and not cond:
        entry["detail"] = detail
    results.append(entry)
    if not cond:
        failures.append(name)


def run_checks(base=BASE):
    """The three named checks as data: a list of
    { name, ok, detail? } in the centre home's shape. The
    command line prints them as it goes; importers (the
    Release Review runner's heartbeat) take the list."""
    failures.clear()
    results.clear()
    base = base.rstrip("/")

    try:
        status, home = get(base + "/")
        check("home: answers 200", status == 200, f"status {status}")
        check("home: carries the grid", 'id="grid"' in home)
    except Exception as e:
        check("home: answers 200", False, str(e))
        home = ""

    apps = []
    try:
        status, raw = get(base + "/data/apps.json")
        check("apps.json: answers 200", status == 200, f"status {status}")
        apps = json.loads(raw)
        check("apps.json: holds listings", len(apps) > 0,
              f"{len(apps)} listings")
    except Exception as e:
        check("apps.json: answers 200", False, str(e))

    if apps:
        first = apps[0]
        try:
            status, page = get(f"{base}/app/{first['slug']}")
            check("listing: answers 200", status == 200, f"status {status}")
            check("listing: carries its name", first["name"] in page,
                  first["name"])
        except Exception as e:
            check("listing: answers 200", False, str(e))

    return list(results)


def main():
    base = BASE
    if "--base" in sys.argv:
        base = sys.argv[sys.argv.index("--base") + 1].rstrip("/")

    checks = run_checks(base)

    if "--results" in sys.argv:
        out = sys.argv[sys.argv.index("--results") + 1]
        with open(out, "w", encoding="utf-8") as f:
            json.dump({"checks": checks,
                       "result": "fail" if failures else "pass"}, f, indent=2)

    if failures:
        print(f"\nSMOKE FAILED: {len(failures)} check(s): "
              + ", ".join(failures))
        return 1
    print("\nSmoke passed.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
