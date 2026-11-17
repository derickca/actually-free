#!/usr/bin/env python3
"""report-failure — the Scenario Review suite's voice on
the tracker (issue #28).

One standing issue per app names the scenarios that failed
and the scenarios that never ran: for Actually Free that is
issue #27, "Scenario Review: failed and never-ran scenarios
(standing)". When a round carries a failure or a never-ran
scenario, this file posts that round's record to the issue
as one comment. A green round files nothing — this file is
never even called with one, and it posts nothing if it is.

The record names the run, when it ran, each failed scenario
with the checks that failed, and each scenario that never
ran. It carries no screenshot and no person's data: the
suite walks a throwaway rig with no accounts in it.

  python3 report_failure.py results.json [--dry-run]

--dry-run prints the comment instead of posting it, for
local rounds and for the suite's own tests.
"""

import json
import subprocess
import sys
from pathlib import Path

REPO = "derickca/actually-free"
ISSUE = 27


def failure_body(results):
    """The comment a non-green round files, or None when
    the round is green and nothing stands to file."""
    failed = [r for r in results.get("results") or []
              if r.get("verdict") == "FAIL"]
    not_run = [r for r in results.get("results") or []
               if r.get("verdict") == "NOT-RUN"]
    if not failed and not not_run:
        return None
    lines = [
        f"Scenario Review round {results.get('runId', '')} "
        f"({results.get('startedAt', '')} to "
        f"{results.get('finishedAt', '')}): "
        f"{results.get('passed', 0)} passed, "
        f"{results.get('failed', 0)} failed.",
        "",
    ]
    for journey in failed:
        lines.append(f"Failed: {journey['id']}")
        for check in journey.get("checks") or []:
            if not check.get("ok"):
                detail = check.get("detail") or ""
                lines.append(f"- {check['id']}"
                             + (f" — {detail}" if detail else ""))
        lines.append("")
    for journey in not_run:
        lines.append(f"Never ran: {journey['id']}")
    return "\n".join(lines).rstrip() + "\n"


def file_failures(results, repo=REPO, issue=ISSUE, runner=None):
    """Post the round's record to the standing issue.
    Returns the body filed, or None when the round is
    green. Filing never raises into the run: a gh failure
    is printed and the body still returned."""
    body = failure_body(results)
    if body is None:
        return None
    run = runner or subprocess.run
    try:
        run(["gh", "issue", "comment", str(issue), "--repo", repo,
             "--body", body],
            capture_output=True, text=True, timeout=120, check=True)
        print(f"Scenario Review: failures filed on issue #{issue}.")
    except Exception as exc:
        print(f"Scenario Review: could not file on issue "
              f"#{issue}: {exc}")
    return body


def main(argv):
    if len(argv) < 2:
        print("usage: report_failure.py results.json [--dry-run]")
        return 2
    results = json.loads(Path(argv[1]).read_text(encoding="utf-8"))
    body = failure_body(results)
    if body is None:
        print("Scenario Review: green round — nothing to file.")
        return 0
    if "--dry-run" in argv:
        print(body)
        return 0
    file_failures(results)
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
