#!/usr/bin/env python3
"""The results reporter's own suite (issue #29).

Drives tools/reporter.py against a local stub standing in
for the MemberSpark centre intake: the stub captures each
request — path, headers, body — and answers as the case
directs. The real intake and the real credential are never
touched; the token in the environment is a fake one.

Cases:
  1. A Build Tests run's three sends: the event declaration
     (its subject the run's id, due one hour, grace two),
     the start report and the finish report, each in the
     centre's shape, under the Bearer credential and the
     named user agent.
  2. A Release Review declaration carries its own standing
     window: due 30 minutes, grace two hours.
  3. A failing check fails the finish; an explicit result
     stands over the computed one.
  4. No credential standing: every send is a no-op printing
     the one plain line, and no request is made.
  5. A refused send (the stub answers 422) and an
     unreachable intake: the finish returns not-sent and
     never raises.
  6. A check name outside the centre's shape — a token-long
     run of letters, an email address, a name past 80
     characters — refuses the send before the wire.
  7. The Scenario Review seam: a suite's results shape into
     the group's start and finish, checks named
     "<journey>:<check>", the NOT-RUN journey named.
  8. The quarantine block: a fixture record's check stands
     in each finish with its skipped count advancing.
  9. expected and got ride within the 200-character cap
     and are dropped past it.

Usage:  python3 test_reporter.py
Exit 0 = every case passed, 1 = a failure (named on its line).
"""

import contextlib
import io
import json
import os
import sys
import tempfile
import threading
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT / "tools"))
import reporter as reporter_mod  # noqa: E402

failures = []


def check(name, cond, detail=""):
    print(f"[{'PASS' if cond else 'FAIL'}] {name}" +
          (f" — {detail}" if detail and not cond else ""))
    if not cond:
        failures.append(name)


class Stub:
    def __init__(self):
        self.requests = []  # (path, headers dict, parsed body)
        self.status = 201

        outer = self

        class Handler(BaseHTTPRequestHandler):
            def do_POST(self):
                length = int(self.headers.get("Content-Length") or 0)
                raw = self.rfile.read(length).decode("utf-8", "replace")
                try:
                    body = json.loads(raw)
                except Exception:
                    body = None
                outer.requests.append(
                    (self.path,
                     {k.lower(): v for k, v in self.headers.items()},
                     body))
                payload = json.dumps({"ok": True}).encode()
                self.send_response(outer.status)
                self.send_header("Content-Type", "application/json")
                self.send_header("Content-Length", str(len(payload)))
                self.end_headers()
                self.wfile.write(payload)

            def log_message(self, *args):
                pass

        self.server = HTTPServer(("127.0.0.1", 0), Handler)
        self.thread = threading.Thread(target=self.server.serve_forever,
                                       daemon=True)
        self.thread.start()
        self.url = f"http://127.0.0.1:{self.server.server_port}"

    def stop(self):
        self.server.shutdown()

    def bodies(self, path):
        return [b for (p, h, b) in self.requests if p == path]


def make_env(stub, tmp, token="fake-token"):
    env = {
        "MEMBERSPARK_RESULTS_INTAKE": stub.url,
        "AF_QUARANTINE_STATE_FILE": str(Path(tmp) / "q-state.json"),
    }
    if token is not None:
        env["MEMBERSPARK_RESULTS_TOKEN"] = token
    return env


def main():
    stub = Stub()
    tmp = tempfile.mkdtemp()
    try:
        env = make_env(stub, tmp)

        # Case 1: the three sends of a Build Tests run.
        run = reporter_mod.RunReporter(
            "Build Tests", "change", run_id="build-tests-case1",
            details={"commit": "123456789"}, env=env)
        run.declare(at="2026-11-17T10:00:00Z")
        run.start()
        outcome = run.finish(checks=[
            {"name": "Site suite", "ok": True},
            {"name": "Ops surface suite", "ok": True,
             "detail": "40 passed"},
        ])
        check("case 1: finish sent", outcome.get("sent") is True,
              str(outcome))
        decls = stub.bodies("/api/v1/centre/expectations")
        check("case 1: one declaration", len(decls) == 1,
              f"{len(decls)} declarations")
        if decls:
            d = decls[0]
            check("case 1: declaration shape",
                  set(d) == {"product", "group", "kind", "subject", "at",
                             "due_after_seconds", "grace_seconds"}
                  and d["product"] == "actually-free"
                  and d["group"] == "Build Tests"
                  and d["kind"] == "event"
                  and d["subject"] == "build-tests-case1"
                  and d["at"] == "2026-11-17T10:00:00Z"
                  and d["due_after_seconds"] == 3600
                  and d["grace_seconds"] == 7200,
                  json.dumps(d))
        reports = stub.bodies("/api/v1/centre/runs")
        check("case 1: start and finish sent", len(reports) == 2,
              f"{len(reports)} reports")
        if len(reports) == 2:
            start, finish = reports
            check("case 1: start shape",
                  start["phase"] == "start"
                  and start["product"] == "actually-free"
                  and start["group"] == "Build Tests"
                  and start["kind"] == "run"
                  and start["run_id"] == "build-tests-case1"
                  and start["started_by"] == "change"
                  and "result" not in start and "checks" not in start,
                  json.dumps(start))
            check("case 1: finish shape",
                  finish["phase"] == "finish"
                  and finish["result"] == "pass"
                  and finish["checks"] == [
                      {"name": "Site suite", "ok": True},
                      {"name": "Ops surface suite", "ok": True,
                       "detail": "40 passed"}]
                  and finish["details"]["passed"] == 2
                  and finish["details"]["failed"] == 0
                  and finish["details"]["not_run"] == []
                  and finish["details"]["quarantine"] == []
                  and finish["details"]["commit"] == "123456789",
                  json.dumps(finish))
        headers = [h for (p, h, b) in stub.requests]
        check("case 1: credential and agent headers",
              all(h.get("authorization") == "Bearer fake-token"
                  for h in headers)
              and all(h.get("user-agent") == "ActuallyFreeReporter/1.0"
                      for h in headers),
              json.dumps(headers[:1]))

        # Case 2: the Release Review window.
        stub.requests.clear()
        review = reporter_mod.RunReporter(
            "Release Review", "GitHub Actions",
            run_id="release-review-2026-11-17", env=env)
        review.declare(at="2026-11-17T15:00:00Z")
        decls = stub.bodies("/api/v1/centre/expectations")
        check("case 2: release window",
              len(decls) == 1
              and decls[0]["due_after_seconds"] == 1800
              and decls[0]["grace_seconds"] == 7200
              and decls[0]["subject"] == "release-review-2026-11-17",
              json.dumps(decls))

        # Case 3: failure and the explicit result.
        stub.requests.clear()
        run3 = reporter_mod.RunReporter(
            "Build Tests", "change", run_id="build-tests-case3", env=env)
        run3.finish(checks=[{"name": "Site suite", "ok": False,
                             "detail": "exit 1", "expected": "exit 0",
                             "got": "exit 1"}])
        run3b = reporter_mod.RunReporter(
            "Build Tests", "change", run_id="build-tests-case3b", env=env)
        run3b.finish(result="fail", checks=[{"name": "Site suite",
                                             "ok": True}])
        reports = stub.bodies("/api/v1/centre/runs")
        check("case 3: a failing check fails the finish",
              len(reports) == 2 and reports[0]["result"] == "fail"
              and reports[0]["details"]["failed"] == 1
              and reports[0]["checks"][0]["expected"] == "exit 0"
              and reports[0]["checks"][0]["got"] == "exit 1",
              json.dumps(reports[:1]))
        check("case 3: an explicit result stands",
              len(reports) == 2 and reports[1]["result"] == "fail",
              json.dumps(reports[1:]))

        # Case 4: no credential — no-op sends, the plain line.
        stub.requests.clear()
        bare = reporter_mod.RunReporter(
            "Build Tests", "change", run_id="build-tests-case4",
            env=make_env(stub, tmp, token=None))
        out = io.StringIO()
        with contextlib.redirect_stdout(out):
            o1 = bare.declare()
            o2 = bare.start()
            o3 = bare.finish(checks=[{"name": "Site suite", "ok": True}])
        check("case 4: unconfigured sends are no-ops",
              all(o.get("unconfigured") for o in (o1, o2, o3))
              and not stub.requests,
              f"{o1} {o2} {o3} requests={len(stub.requests)}")
        check("case 4: the plain line stands",
              out.getvalue().count("Results reporting is not configured")
              == 3,
              out.getvalue()[:200])

        # Case 5: refused and unreachable sends never raise.
        stub.status = 422
        run5 = reporter_mod.RunReporter(
            "Build Tests", "change", run_id="build-tests-case5", env=env)
        with contextlib.redirect_stdout(io.StringIO()):
            o5 = run5.finish(checks=[{"name": "Site suite", "ok": True}])
        stub.status = 201
        check("case 5: a refused send returns not-sent",
              o5.get("sent") is False and o5.get("status") == 422,
              str(o5))
        dead_env = dict(env)
        dead_env["MEMBERSPARK_RESULTS_INTAKE"] = "http://127.0.0.1:1"
        run5b = reporter_mod.RunReporter(
            "Build Tests", "change", run_id="build-tests-case5b",
            env=dead_env)
        with contextlib.redirect_stdout(io.StringIO()):
            o5b = run5b.finish(checks=[{"name": "Site suite", "ok": True}])
        check("case 5: an unreachable intake returns not-sent",
              o5b.get("sent") is False and "error" in o5b, str(o5b))

        # Case 6: names outside the shape refuse before the wire.
        stub.requests.clear()
        for bad in ("x" * 24, "someone@example.com", "n" * 81):
            run6 = reporter_mod.RunReporter(
                "Build Tests", "change", run_id="build-tests-case6",
                env=env)
            with contextlib.redirect_stdout(io.StringIO()):
                o6 = run6.finish(checks=[{"name": bad, "ok": True}])
            check(f"case 6: name refused ({bad[:16]}…)",
                  o6.get("sent") is False
                  and o6.get("refused_name") == bad,
                  str(o6))
        check("case 6: nothing reached the wire",
              not stub.bodies("/api/v1/centre/runs"),
              f"{len(stub.requests)} requests")

        # Case 7: the Scenario Review seam.
        stub.requests.clear()
        suite = {
            "startedAt": "2026-11-17T06:10:00Z",
            "finishedAt": "2026-11-17T06:12:00Z",
            "passed": 2, "failed": 1,
            "results": [
                {"id": "find-an-app", "verdict": "FAIL",
                 "checks": [{"id": "land", "ok": True},
                            {"id": "download", "ok": False}]},
                {"id": "suggest", "verdict": "NOT-RUN", "checks": []},
            ],
        }
        outcomes = reporter_mod.report_scenario_review(suite, env=env)
        reports = stub.bodies("/api/v1/centre/runs")
        check("case 7: the seam sends start and finish",
              outcomes["finish"].get("sent") is True
              and len(reports) == 2,
              f"{outcomes} requests={len(reports)}")
        if len(reports) == 2:
            finish = reports[1]
            check("case 7: the finish shape",
                  finish["group"] == "Scenario Review"
                  and finish["started_by"] == "schedule"
                  and finish["run_id"] == "20261117-061000"
                  and finish["result"] == "fail"
                  and finish["checks"] == [
                      {"name": "find-an-app:land", "ok": True},
                      {"name": "find-an-app:download", "ok": False}]
                  and finish["details"]["not_run"] == ["suggest"],
                  json.dumps(finish))

        # Case 8: the quarantine block advances.
        qfile = Path(tmp) / "quarantine.json"
        qfile.write_text(json.dumps(
            {"quarantined": [{"check": "Site suite",
                              "since": "2026-11-01"}]}), encoding="utf-8")
        seen = []
        for i in (1, 2):
            run8 = reporter_mod.RunReporter(
                "Build Tests", "change", run_id=f"build-tests-case8-{i}",
                env=env, quarantine_file=qfile)
            stub.requests.clear()
            run8.finish(checks=[{"name": "Ops surface suite", "ok": True}])
            reports = stub.bodies("/api/v1/centre/runs")
            if reports:
                seen.append(reports[0]["details"]["quarantine"])
        check("case 8: skipped counts advance 1 then 2",
              seen == [[{"check": "Site suite", "skipped": 1}],
                       [{"check": "Site suite", "skipped": 2}]],
              json.dumps(seen))

        # Case 9: expected and got at the cap.
        stub.requests.clear()
        run9 = reporter_mod.RunReporter(
            "Build Tests", "change", run_id="build-tests-case9", env=env)
        run9.finish(checks=[
            {"name": "Site suite", "ok": False,
             "expected": "e" * 200, "got": "g" * 201}])
        reports = stub.bodies("/api/v1/centre/runs")
        check("case 9: values ride within the cap only",
              len(reports) == 1
              and reports[0]["checks"][0].get("expected") == "e" * 200
              and "got" not in reports[0]["checks"][0],
              json.dumps(reports)[:200])
    finally:
        stub.stop()

    if failures:
        print(f"\nREPORTER SUITE FAILED: {len(failures)} check(s): "
              + ", ".join(failures))
        return 1
    print("\nReporter suite passed.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
