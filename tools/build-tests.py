#!/usr/bin/env python3
"""Build Tests for Actually Free, run on a change (issue #29).

Runs the whole standing set named in docs/E2E.md — the site
suite, the catalogue checks and unittests, the Bing suite,
the deploy guards, the Ops suite, the reporter suite and the
Release Review suite — each as one check in the run's report,
and reports the run to the central results store as the
group's Build Tests run: the event expectation declared as
the run starts (due one hour after, grace two hours), the
start report, then the finish with each suite's verdict.

The suites still gate the push: this runner exits 1 when any
suite fails, exactly as running them one by one would.
Reporting rides along fail-soft — it never changes the exit,
and with no reporter credential in the environment it prints
its one plain line and sends nothing (the credential stands
as a repository secret for Actions; a change-time run sends
only when the machine's environment carries it).

  python3 tools/build-tests.py [--no-report]

Each suite can still be run on its own, as docs/E2E.md
names; this runner is the one-command shape that also
reports.
"""
import subprocess
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "tools"))
import reporter as reporter_mod  # noqa: E402

# (check name, command, timeout seconds). The names meet the
# results store's name shape; each suite's own output streams
# through, so a failure reads where it happened.
SUITES = [
    ("Site suite", ["python3", "test_site.py"], 1800),
    ("Windows catalogue check", ["python3", "tools/check-windows.py"], 600),
    ("Apple catalogue check", ["python3", "tools/check-apple.py"], 600),
    ("Catalogue unittests",
     ["python3", "-m", "unittest", "test_windows_catalog.py",
      "test_apple_catalog.py"], 600),
    ("Bing submission suite", ["python3", "test_bing_submit.py"], 600),
    ("Deploy guards suite", ["python3", "test_deploy_guards.py"], 600),
    ("Ops surface suite", ["node", "test_ops.mjs"], 600),
    ("Reporter suite", ["python3", "test_reporter.py"], 600),
    ("Release Review suite", ["python3", "test_release_review.py"], 600),
]


def commit_stamp():
    try:
        out = subprocess.run(
            ["git", "rev-parse", "HEAD"], cwd=ROOT,
            capture_output=True, text=True, timeout=30)
        stamp = out.stdout.strip()
        return stamp[:9] if stamp else None
    except Exception:
        return None


def main(argv):
    report = "--no-report" not in argv
    details = {}
    stamp = commit_stamp()
    if stamp:
        details["commit"] = stamp
    run = reporter_mod.RunReporter(
        "Build Tests", "change", details=details) if report else None
    if run is not None:
        run.declare()
        run.start()

    checks = []
    failed = 0
    for name, cmd, timeout in SUITES:
        print(f"\n=== {name}: {' '.join(cmd)}", flush=True)
        began = time.monotonic()
        try:
            proc = subprocess.run(cmd, cwd=ROOT, timeout=timeout)
            code = proc.returncode
        except subprocess.TimeoutExpired:
            code = "timeout"
        except Exception as e:
            code = str(e)
        seconds = round(time.monotonic() - began)
        ok = code == 0
        if not ok:
            failed += 1
        check = {"name": name, "ok": ok,
                 "detail": f"exit {code} in {seconds}s"}
        if not ok:
            check["expected"] = "exit 0"
            check["got"] = f"exit {code}"
        checks.append(check)
        print(f"=== {name}: {'PASS' if ok else 'FAIL'} "
              f"(exit {code}, {seconds}s)", flush=True)

    if run is not None:
        run.finish(checks=checks)
    if failed:
        print(f"\nBUILD TESTS FAILED: {failed} suite(s).")
        return 1
    print("\nBuild Tests passed.")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
