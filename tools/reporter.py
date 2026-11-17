#!/usr/bin/env python3
"""Results reporting for Actually Free — issue #29.

Every run of the app's groups reports to the central results
store (POST /api/v1/results/reports on the MemberSpark intake),
and the event groups declare their expectation on the same road
(POST /api/v1/results/expectations) as the event lands. The
shapes are the store's own, read from the centre's intake
(derickca/MemberSpark, service/src/results.js) and its sender
tool (service/tools/send-run-report.mjs):

  report:      { product, group, kind, run_id, phase,
                 started_by, started_at, finished_at, result,
                 checks, details, screenshots }
  declaration: { product, group, kind: "event", subject,
                 at, due_after_seconds, grace_seconds }

- product is this app's registered name, "actually-free"; group
  is the group's full standard name (Build Tests, Release
  Review, Scenario Review); kind is "run" on every report.
- phase is "start" or "finish". A start report carries no
  result and no checks. A finish report's result is "pass" or
  "fail"; its checks ride as { name, ok, detail?, expected?,
  got? } with expected and got the check's own short plain
  values (a non-empty string of at most 200 characters).
- An event declaration's subject is the run_id of the report
  that will earn it: the store matches a finish to its row by
  that name. The standing windows are the centre's: a change's
  or deploy's Build Tests report is due one hour after the
  event, a release's Release Review report 30 minutes after,
  each with a two-hour grace.
- A check's name meets the store's name shape (#649): at most
  80 characters of letters, digits, hyphens, underscores, dots,
  spaces, colons, slashes, apostrophes, parentheses, commas
  and em dashes, with no unbroken run of 20 or more letters
  and digits, and never an email address. A name outside the
  shape refuses the send before the wire, with the name and
  the broken rule printed — the centre's own shaper refuses
  the same way, so no report carrying such a name is built.
- Content positions — started_by, a check's detail, expected
  and got, the details block, the screenshot names — carry no
  email address and no token-shaped string. A commit stands
  in details as its short stamp (9 characters), never the
  full hash, which reads as a token.
- Screenshots never enter a report as images; a finish names
  their files in the top-level screenshots list.

The credential is the reporter token the centre minted for
this app, read at run time from the environment variable
MEMBERSPARK_RESULTS_TOKEN (a repository secret in GitHub
Actions; it never rests in this repo). The intake address
defaults to the production one and can be overridden with
MEMBERSPARK_RESULTS_INTAKE for rigs and suites.

Reporting never fails the run it describes. With no
credential standing, every send is a clean no-op that prints
one plain line saying reporting is not configured. A send
the intake refuses, or a road that does not answer, is
printed and returned, never raised.

Every finish report names the run's quarantined checks in
details.quarantine — one entry per quarantined check,
{ check, skipped }, the skipped count being the runs skipped
since its quarantine began. The source of truth for which
checks stand quarantined is the machine-readable record
beside this file, tools/quarantine.json; docs/E2E.md names
the same record, so the prose and the sender cannot drift.
The skipped counts stand in a small state file (default
~/.actually-free/quarantine-state.json, overridden by
AF_QUARANTINE_STATE_FILE), advanced once per finish per
quarantined check. When nothing stands quarantined the
block stands in the report as an empty list, never omitted.

The Scenario Review seam (the suite built under issue #28
calls it when its run ends): report_scenario_review() below
shapes a suite's results into the group's start and finish
reports, the way the centre's own shaper shapes them — checks named
"<journey>:<check>", a NOT-RUN journey's name in not_run,
started_by "schedule" (the group's standing expectation is
an interval registration the centre holds; the suite
declares nothing). The same shaping stands at the command
line for a suite in any language:

  python3 tools/reporter.py scenario --payload results.json

with results.json carrying { runId?, startedAt, finishedAt,
passed, failed, results: [{ id, verdict, checks:
[{ id, ok }] }], quarantined?: [{ check, skipped }] }.
"""

import json
import os
import re
import sys
import time
import urllib.error
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

PRODUCT = "actually-free"
DEFAULT_INTAKE = "https://api.memberspark.ca"
TOKEN_ENV = "MEMBERSPARK_RESULTS_TOKEN"
INTAKE_ENV = "MEMBERSPARK_RESULTS_INTAKE"
USER_AGENT = "ActuallyFreeReporter/1.0"

GROUPS = ("Build Tests", "Release Review", "Scenario Review")

# The standing event windows, in seconds: the centre's own
# defaults for the two event groups this app declares.
EVENT_WINDOWS = {
    "Build Tests": {"due_after_seconds": 3600, "grace_seconds": 7200},
    "Release Review": {"due_after_seconds": 1800, "grace_seconds": 7200},
}

RUN_ID_SHAPE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]{0,80}$")
NAME_SHAPE = re.compile(r"^[A-Za-z0-9 .:_/'(),—-]{1,80}$")
NAME_TOKEN_RUN = re.compile(r"[A-Za-z0-9]{20,}")
EMAIL_SHAPE = re.compile(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}")
CHECK_VALUE_CAP = 200
QUARANTINE_CAP = 50

QUARANTINE_FILE = Path(__file__).with_name("quarantine.json")


def now_iso():
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def check_name_refusal(name):
    """None when the name meets the store's shape, else the
    broken rule in plain words (the centre's shaper's test,
    mirrored)."""
    if not isinstance(name, str) or not name:
        return "it is not a standing name"
    if EMAIL_SHAPE.search(name):
        return "a check name cannot be an email address"
    if len(name) > 80:
        return f"it runs to {len(name)} characters, past the 80 a name may carry"
    if NAME_TOKEN_RUN.search(name):
        return ("it carries an unbroken run of 20 or more letters "
                "and digits, which reads as a token")
    if not NAME_SHAPE.match(name):
        return "it carries a character the store's names do not carry"
    return None


def read_quarantine_record(file=QUARANTINE_FILE):
    try:
        parsed = json.loads(Path(file).read_text(encoding="utf-8"))
        entries = parsed if isinstance(parsed, list) else parsed.get("quarantined")
        if not isinstance(entries, list):
            return []
        return [e for e in entries
                if isinstance(e, dict) and isinstance(e.get("check"), str)
                and e["check"]][:QUARANTINE_CAP]
    except Exception:
        return []


def _default_state_file():
    return Path(os.path.expanduser("~/.actually-free/quarantine-state.json"))


class RunReporter:
    """One run's reports: declare its expectation, send its
    start, send its finish. Every road is fail-soft."""

    def __init__(self, group, started_by, run_id=None, details=None,
                 env=None, quarantine_file=QUARANTINE_FILE,
                 quarantine_state_file=None, opener=None):
        if group not in GROUPS:
            raise ValueError(f"unknown group {group!r}")
        self.group = group
        self.started_by = started_by
        self.env = env if env is not None else os.environ
        self.token = self.env.get(TOKEN_ENV) or None
        self.intake = (self.env.get(INTAKE_ENV) or DEFAULT_INTAKE).rstrip("/")
        self.run_id = run_id or self._make_run_id(group)
        self.started_at = now_iso()
        self.details = dict(details or {})
        self.quarantine_file = quarantine_file
        self.quarantine_state_file = (
            quarantine_state_file
            or self.env.get("AF_QUARANTINE_STATE_FILE")
            or _default_state_file())
        self._opener = opener or self._urlopen

    @staticmethod
    def _make_run_id(group):
        slug = re.sub(r"[^a-z0-9]+", "-", group.lower()).strip("-")
        stamp = format(int(time.time() * 1000), "x")
        return f"{slug}-{stamp}"

    # -- the wire -------------------------------------------------

    @staticmethod
    def _urlopen(req, timeout=20):
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            return resp.status, resp.read().decode("utf-8", "replace")

    def _post(self, path, payload):
        """One send. Returns {"sent": bool, ...}; never raises."""
        if not self.token:
            print("Results reporting is not configured "
                  f"({TOKEN_ENV} is not set); this send is skipped.")
            return {"sent": False, "unconfigured": True}
        req = urllib.request.Request(
            self.intake + path,
            data=json.dumps(payload).encode("utf-8"),
            method="POST",
            headers={
                "authorization": "Bearer " + self.token,
                "content-type": "application/json",
                # The intake's edge refuses a runtime's default
                # user agent outright (Cloudflare error 1010);
                # name the sender, as the centre's own tool does.
                "user-agent": USER_AGENT,
            })
        try:
            status, raw = self._opener(req)
        except urllib.error.HTTPError as e:
            try:
                raw = e.read().decode("utf-8", "replace")
            except Exception:
                raw = ""
            print(f"Results report: the intake refused the send "
                  f"({e.code}): {raw[:200]}")
            return {"sent": False, "status": e.code}
        except Exception as e:
            print(f"Results report: the send did not reach the "
                  f"intake: {e}")
            return {"sent": False, "error": str(e)}
        if status not in (200, 201):
            print(f"Results report: the intake answered {status}: "
                  f"{raw[:200]}")
            return {"sent": False, "status": status}
        return {"sent": True, "status": status}

    # -- the three acts -------------------------------------------

    def declare(self, at=None, due_after_seconds=None,
                grace_seconds=None):
        """Declare this run's event expectation: the row the
        finish report will earn, its subject this run's id.
        Only the two event groups declare; a Scenario Review
        run's expectation is the centre's standing interval
        registration, and declaring for it is a no-op."""
        if self.group not in EVENT_WINDOWS:
            return {"sent": False, "not_event_group": True}
        window = EVENT_WINDOWS[self.group]
        payload = {
            "product": PRODUCT,
            "group": self.group,
            "kind": "event",
            "subject": self.run_id,
            "at": at or self.started_at,
            "due_after_seconds":
                window["due_after_seconds"] if due_after_seconds is None
                else due_after_seconds,
            "grace_seconds":
                window["grace_seconds"] if grace_seconds is None
                else grace_seconds,
        }
        outcome = self._post("/api/v1/results/expectations", payload)
        if outcome.get("sent"):
            print(f"Results report: {self.group} expectation declared "
                  f"for {self.run_id}.")
        return outcome

    def _core(self, phase, extra):
        return {
            "product": PRODUCT,
            "group": self.group,
            "kind": "run",
            "run_id": self.run_id,
            "phase": phase,
            "started_by": self.started_by,
            "started_at": self.started_at,
            **extra,
        }

    def start(self):
        extra = {}
        if self.details:
            extra["details"] = dict(self.details)
        outcome = self._post("/api/v1/results/reports",
                             self._core("start", extra))
        if outcome.get("sent"):
            print(f"Results report: {self.group} start sent "
                  f"for {self.run_id}.")
        return outcome

    def _quarantine_block(self):
        if "quarantine" in self.details:
            return self.details["quarantine"]
        entries = read_quarantine_record(self.quarantine_file)
        if not entries:
            return []
        counts = {}
        try:
            parsed = json.loads(
                Path(self.quarantine_state_file).read_text(encoding="utf-8"))
            if isinstance(parsed, dict) and isinstance(parsed.get("counts"), dict):
                counts = parsed["counts"]
        except Exception:
            counts = {}
        block = []
        for entry in entries:
            skipped = counts.get(entry["check"])
            skipped = skipped + 1 if isinstance(skipped, int) else 1
            counts[entry["check"]] = skipped
            block.append({"check": entry["check"], "skipped": skipped})
        try:
            state = Path(self.quarantine_state_file)
            state.parent.mkdir(parents=True, exist_ok=True)
            state.write_text(json.dumps({"counts": counts}, indent=2) + "\n",
                             encoding="utf-8")
        except Exception:
            pass  # the count then stands at this run alone
        return block

    @staticmethod
    def _emit_check(check):
        out = {"name": check["name"], "ok": bool(check["ok"])}
        if check.get("detail"):
            out["detail"] = str(check["detail"])
        for key in ("expected", "got"):
            value = check.get(key)
            if isinstance(value, str) and value and len(value) <= CHECK_VALUE_CAP:
                out[key] = value
        return out

    def finish(self, result=None, checks=(), not_run=(), screenshots=()):
        """Send the finish report. A check name outside the
        store's shape refuses the send before the wire, the
        way the centre's shaper refuses it."""
        emitted = []
        for check in checks:
            refusal = check_name_refusal(check.get("name"))
            if refusal:
                print(f"Results report: the check name "
                      f"{check.get('name')!r} refuses the store's "
                      f"name shape: {refusal}. Nothing was sent.")
                return {"sent": False, "refused_name": check.get("name")}
            emitted.append(self._emit_check(check))
        failed = sum(1 for c in emitted if not c["ok"])
        if result is None:
            result = "fail" if failed else "pass"
        report = self._core("finish", {
            "finished_at": now_iso(),
            "result": result,
            "checks": emitted,
            "details": {
                **self.details,
                "passed": len(emitted) - failed,
                "failed": failed,
                "not_run": list(not_run),
                "quarantine": self._quarantine_block(),
            },
        })
        if screenshots:
            report["screenshots"] = list(screenshots)
        outcome = self._post("/api/v1/results/reports", report)
        if outcome.get("sent"):
            print(f"Results report: {self.group} finish sent "
                  f"for {self.run_id} ({result}).")
        return outcome


# -- the Scenario Review seam (issue #28) ---------------------------


def shape_scenario_reports(suite, started_by="schedule"):
    """A Scenario Review suite's results in the store's start
    and finish shapes — the centre's own shaper's mapping:
    checks named "<journey>:<check>", a NOT-RUN journey's name
    in not_run, the counts in details."""
    run_id = suite.get("runId") or (
        suite["startedAt"][:10].replace("-", "")
        + "-" + suite["startedAt"][11:19].replace(":", ""))
    checks = []
    not_run = []
    for journey in suite.get("results") or []:
        if journey.get("verdict") == "NOT-RUN":
            not_run.append(journey["id"])
        for check in journey.get("checks") or []:
            checks.append({"name": f"{journey['id']}:{check['id']}",
                           "ok": bool(check.get("ok"))})
    quarantine = []
    for entry in suite.get("quarantined") or suite.get("quarantine") or []:
        if not isinstance(entry, dict):
            continue
        name = entry.get("check") or entry.get("name") or entry.get("id")
        if not name:
            continue
        shaped = {"check": str(name)}
        skipped = entry.get("skipped", entry.get("runs_skipped"))
        if isinstance(skipped, int) and skipped >= 0:
            shaped["skipped"] = skipped
        quarantine.append(shaped)
    base = {
        "product": PRODUCT,
        "group": "Scenario Review",
        "kind": "run",
        "run_id": run_id,
        "started_by": started_by,
        "started_at": suite["startedAt"],
    }
    finish = {
        **base,
        "phase": "finish",
        "finished_at": suite["finishedAt"],
        "result": "fail" if (suite.get("failed") or 0) > 0 else "pass",
        "checks": checks,
        "details": {
            "passed": suite.get("passed"),
            "failed": suite.get("failed"),
            "not_run": not_run,
            **({"quarantine": quarantine} if quarantine else {}),
        },
    }
    return {"start": {**base, "phase": "start"}, "finish": finish}


def report_scenario_review(suite, started_by="schedule", env=None):
    """The call #28's suite makes when its run ends: shape its
    results and send the start and finish reports. Returns
    the two sends' outcomes; reporting never raises."""
    shaped = shape_scenario_reports(suite, started_by)
    reporter = RunReporter("Scenario Review", started_by,
                           run_id=shaped["start"]["run_id"], env=env)
    reporter.started_at = suite["startedAt"]
    start_outcome = reporter._post("/api/v1/results/reports", shaped["start"])
    finish_outcome = reporter._post("/api/v1/results/reports", shaped["finish"])
    return {"start": start_outcome, "finish": finish_outcome}


def main(argv):
    if len(argv) >= 2 and argv[1] == "scenario":
        payload_at = argv.index("--payload") if "--payload" in argv else -1
        if payload_at < 0 or payload_at + 1 >= len(argv):
            print("usage: reporter.py scenario --payload results.json")
            return 2
        suite = json.loads(Path(argv[payload_at + 1]).read_text(encoding="utf-8"))
        started_by = "schedule"
        if "--started-by" in argv:
            started_by = argv[argv.index("--started-by") + 1]
        report_scenario_review(suite, started_by)
        return 0  # reporting never blocks the suite it describes
    print("usage: reporter.py scenario --payload results.json")
    return 2


if __name__ == "__main__":
    sys.exit(main(sys.argv))
