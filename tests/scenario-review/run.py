#!/usr/bin/env python3
"""run — the Scenario Review suite's entry point (issue #28).

One round, in order:

1. Build a fresh rig: the committed tree (git archive of
   HEAD) unpacked into a throwaway directory, served
   locally by drive.py. The rig is destroyed when the
   round ends, however it ends.
2. Walk the contract's journeys (journey.py) as a visitor
   walks the public directory, photographing each walked
   page. Screenshots stay on this machine, in a weekday
   folder — ~/.actually-free/scenario-review/<Weekday>/ by
   default, AF_SCENARIO_SHOTS names another root — and
   never go to the centre.
3. Report the round to the centre's run-record home through
   the reporter seam (tools/reporter.py's
   report_scenario_review), under the group's standing
   interval registration: the suite declares nothing. With
   no reporter credential in the environment the seam
   prints its one plain line and sends nothing.
4. File the round on the standing failure issue (#27)
   through report_failure.py when — and only when — a
   scenario failed or never ran. A green round files
   nothing.

Quarantine: a check named in tools/quarantine.json is not
run; its journey records it as skipped in the round's
local record, and the report carries the quarantine block
with the runs-skipped counts, kept in a state file beside
the screenshots root. A quarantined scenario's journey
still walks its other checks.

  python3 tests/scenario-review/run.py [--no-report]
      [--no-file] [--started-by schedule|manual]

The exit is 1 when any scenario failed or never ran, else
0; the scheduled workflow pins its own exit to 0 behind
this, because a Review reports and never blocks. The
round's full record — every check with its detail — is
written to the screenshots folder as results.json and
printed as it stands.
"""

import json
import os
import shutil
import subprocess
import sys
import tempfile
from datetime import datetime, timezone
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent.parent
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(ROOT / "tools"))

import drive  # noqa: E402
import journey as journey_mod  # noqa: E402
import report_failure  # noqa: E402
import reporter as reporter_mod  # noqa: E402


def now_iso():
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def build_rig(dest):
    """Unpack the committed tree (HEAD) into dest."""
    archive = subprocess.run(
        ["git", "-C", str(ROOT), "archive", "HEAD"],
        capture_output=True, timeout=300, check=True)
    proc = subprocess.run(["tar", "-x", "-C", str(dest)],
                          input=archive.stdout, timeout=300)
    if proc.returncode != 0:
        raise RuntimeError("the rig's tree would not unpack")


def shots_root():
    named = os.environ.get("AF_SCENARIO_SHOTS")
    if named:
        return Path(named)
    return Path(os.path.expanduser("~/.actually-free/scenario-review"))


def quarantine_state_file(root):
    return root / "quarantine-state.json"


def apply_quarantine(results, root):
    """Split quarantined checks out of the walked results.

    Returns the payload's quarantine list: one entry per
    quarantined check the round would have run, with its
    runs-skipped count advanced once for this round."""
    record = reporter_mod.read_quarantine_record()
    names = {entry["check"] for entry in record}
    if not names:
        return []
    state_path = quarantine_state_file(root)
    try:
        state = json.loads(state_path.read_text(encoding="utf-8"))
    except Exception:
        state = {}
    carried = []
    for result in results:
        kept = []
        for check in result["checks"]:
            wire_name = f"{result['id']}:{check['id']}"
            if wire_name in names:
                skipped = int(state.get(wire_name, 0)) + 1
                state[wire_name] = skipped
                carried.append({"check": wire_name,
                                "skipped": skipped})
                check = {**check, "quarantined": True}
            kept.append(check)
        result["checks"] = kept
        walked = [c for c in kept if not c.get("quarantined")]
        if result["verdict"] != "NOT-RUN":
            result["verdict"] = (
                "PASS" if all(c["ok"] for c in walked) else "FAIL")
    state_path.parent.mkdir(parents=True, exist_ok=True)
    state_path.write_text(json.dumps(state, indent=1),
                          encoding="utf-8")
    return carried


def wire_results(results):
    """The results as the reporter seam takes them: check
    detail and quarantined marks stay in the local record;
    the wire carries ids and verdicts."""
    wired = []
    for result in results:
        wired.append({
            "id": result["id"],
            "verdict": result["verdict"],
            "checks": [{"id": c["id"], "ok": bool(c["ok"])}
                       for c in result["checks"]
                       if not c.get("quarantined")],
        })
    return wired


def main(argv):
    report = "--no-report" not in argv
    file_fail = "--no-file" not in argv
    started_by = "schedule"
    if "--started-by" in argv:
        started_by = argv[argv.index("--started-by") + 1]

    started_at = now_iso()
    run_id = ("scenario-review-"
              + started_at[:10].replace("-", "")
              + "-" + started_at[11:19].replace(":", ""))
    root = shots_root()
    weekday_dir = root / datetime.now().strftime("%A")
    weekday_dir.mkdir(parents=True, exist_ok=True)

    rig = Path(tempfile.mkdtemp(prefix="af-scenario-rig-"))
    results = []
    try:
        build_rig(rig)
        if not drive.chrome_available():
            print("Scenario Review: no headless Chrome shell "
                  "stands on this machine; no journey can run.")
            results = [journey_mod._not_run(jid)
                       for jid, _ in journey_mod.JOURNEYS]
        else:
            with drive.RigServer(rig) as server:
                base = f"http://127.0.0.1:{server.port}"
                if not drive.wait_for_server(base + "/"):
                    print("Scenario Review: the rig never answered.")
                    results = [journey_mod._not_run(jid)
                               for jid, _ in journey_mod.JOURNEYS]
                else:
                    for _jid, walk in journey_mod.JOURNEYS:
                        results.append(walk(rig, base))
                    for result in results:
                        for page in result.get("pages") or []:
                            slug = (page.strip("/")
                                    .removesuffix(".html")
                                    .replace("/", "-") or "home")
                            drive.screenshot(
                                rig, base, page,
                                weekday_dir / f"{run_id}-{slug}.png")
    finally:
        shutil.rmtree(rig, ignore_errors=True)

    quarantined = apply_quarantine(results, root)
    wired = wire_results(results)
    passed = sum(1 for r in wired if r["verdict"] == "PASS")
    failed = sum(1 for r in wired if r["verdict"] != "PASS")
    finished_at = now_iso()

    payload = {
        "runId": run_id,
        "startedAt": started_at,
        "finishedAt": finished_at,
        "passed": passed,
        "failed": failed,
        "results": wired,
        "quarantined": quarantined,
    }
    local_record = {**payload, "results": results}
    record_path = weekday_dir / f"{run_id}-results.json"
    record_path.write_text(json.dumps(local_record, indent=1),
                           encoding="utf-8")

    for result in results:
        print(f"Scenario Review: {result['id']}: {result['verdict']}")
        for check in result["checks"]:
            mark = "PASS" if check["ok"] else "FAIL"
            if check.get("quarantined"):
                mark = "QUARANTINED"
            detail = check.get("detail") or ""
            print(f"  [{mark}] {check['id']}"
                  + (f" — {detail}" if detail else ""))
    print(f"Scenario Review: {passed} passed, {failed} failed; "
          f"record at {record_path}")

    if report:
        outcomes = reporter_mod.report_scenario_review(
            payload, started_by=started_by)
        for phase, outcome in outcomes.items():
            if outcome.get("sent"):
                print(f"Scenario Review: {phase} report sent "
                      f"for {run_id}.")
            elif outcome.get("unconfigured"):
                print("Scenario Review: reporting is not "
                      "configured; nothing sent.")
            else:
                print(f"Scenario Review: {phase} report not "
                      f"sent: {outcome}")

    if file_fail and failed:
        report_failure.file_failures({**payload, "results": results})

    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
