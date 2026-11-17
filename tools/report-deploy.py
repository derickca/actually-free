#!/usr/bin/env python3
"""Report a deploy's smoke run and declare its Release
Review expectation (issue #29).

Runs in the deploy workflow after the smoke step, whether
the smoke passed or failed, whenever the run published:

1. The deploy's Build Tests report. The event is the deploy:
   its expectation is declared (due one hour after, grace
   two hours) with the report's own run name as its subject,
   then the start and finish go, the finish carrying the
   smoke run's checks as tools/smoke.py recorded them in its
   --results file. When no results file stands — the smoke
   died before it could write one — the finish names the
   smoke's checks as not run and stands failed: the honest
   record of a smoke that never completed.
2. The day's Release Review declaration. The event is the
   publish: the expectation is declared with the day's
   review run name — release-review-<UTC day> — as its
   subject, due 30 minutes after the publish. Every publish
   of the day declares the same row; a later publish reopens
   it at its own time, so the row always owes one review of
   the whole day, due half an hour after the day's last
   publish. The Release Review runner (tools/release-
   review.py) sends the report that earns it.

Reporting never blocks a publish: this script is fail-soft
throughout and the workflow step's exit is pinned to 0
behind it. Environment: MEMBERSPARK_RESULTS_TOKEN (the
reporter credential), DEPLOY_RUN_ID (the deploy's workflow
run id), GITHUB_SHA (the published commit), SMOKE_RESULTS
(the smoke's --results file).
"""
import json
import os
import sys
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import reporter as reporter_mod  # noqa: E402

SMOKE_CHECK_NAMES = [
    "home: answers 200",
    "home: carries the grid",
    "apps.json: answers 200",
    "apps.json: holds listings",
    "listing: answers 200",
    "listing: carries its name",
]


def main():
    env = os.environ
    deploy_run = env.get("DEPLOY_RUN_ID") or "unknown"
    run_id = f"build-tests-deploy-{deploy_run}"
    details = {}
    sha = env.get("GITHUB_SHA") or ""
    if sha:
        details["commit"] = sha[:9]
    details["deploy_run"] = str(deploy_run)

    run = reporter_mod.RunReporter(
        "Build Tests", "GitHub Actions", run_id=run_id, details=details)
    run.declare()
    run.start()

    checks = None
    result = None
    results_path = env.get("SMOKE_RESULTS") or ""
    if results_path and Path(results_path).exists():
        try:
            recorded = json.loads(Path(results_path).read_text(encoding="utf-8"))
            checks = recorded.get("checks") or []
            result = recorded.get("result")
        except Exception:
            checks = None
    if checks is None:
        run.finish(result="fail", checks=[],
                   not_run=SMOKE_CHECK_NAMES)
    else:
        run.finish(result=result, checks=checks)

    day = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    review = reporter_mod.RunReporter(
        "Release Review", "GitHub Actions",
        run_id=f"release-review-{day}")
    review.declare()
    return 0


if __name__ == "__main__":
    sys.exit(main())
