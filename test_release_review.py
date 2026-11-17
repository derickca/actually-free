#!/usr/bin/env python3
"""The Release Review runner's own suite (issue #29).

Drives tools/release-review.py against fixtures: a fake
GitHub API standing in for the deploy workflow's record, a
fake fetch standing in for the live site, and a local stub
standing in for the results intake. The real GitHub API,
the real site and the real credential are never touched.

Cases:
  1. Publish detection: a run counts when its Publish step
     succeeded — a held run (the step skipped) and a failed
     run count for nothing — and the publish time is the
     step's own finish time.
  2. Day grouping and the due rule: a group is due when its
     last publish is at least 30 minutes old and its
     coverage stands unreviewed; a group past the 48-hour
     watch is not chased.
  3. Changed views: a compare's files map to the site's
     paths, and a generator or data change stands for the
     whole tree.
  4. A full review against the stubs: the finish report
     names both of the day's publishes, carries the
     heartbeat checks and the changed view's check, and
     the coverage state advances — a second tick at the
     same hour sends nothing.
  5. A new publish extends the day's coverage: the group
     falls due again once it is 30 minutes old.
  6. A lone first publish with no earlier commit to
     compare: the feature check stands in not_run and the
     review still reports.

Usage:  python3 test_release_review.py
Exit 0 = every case passed, 1 = a failure (named on its line).
"""

import importlib.util
import json
import sys
import tempfile
import threading
from datetime import datetime, timedelta, timezone
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT / "tools"))
import smoke  # noqa: E402


def load(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


rr = load("release_review", ROOT / "tools" / "release-review.py")

failures = []


def check(name, cond, detail=""):
    print(f"[{'PASS' if cond else 'FAIL'}] {name}" +
          (f" — {detail}" if detail and not cond else ""))
    if not cond:
        failures.append(name)


def at(day, hour, minute=0):
    return datetime(2026, 11, day, hour, minute, tzinfo=timezone.utc)


def iso(moment):
    return moment.strftime("%Y-%m-%dT%H:%M:%SZ")


def make_run(run_id, conclusion, publish_conclusion, finished):
    steps = []
    if publish_conclusion is not None:
        steps.append({"name": "Publish to Cloudflare Pages",
                      "conclusion": publish_conclusion,
                      "completed_at": iso(finished)})
    return {
        "run": {"id": run_id, "conclusion": conclusion,
                "head_sha": f"sha{run_id}"},
        "jobs": [{"steps": steps}],
    }


class FakeApi:
    def __init__(self, records, compares=None, parents=None):
        self.records = records  # list of make_run dicts
        self.compares = compares or {}
        self.parents = parents or {}

    def deploy_runs(self):
        return [r["run"] for r in self.records]

    def jobs(self, run_id):
        for r in self.records:
            if r["run"]["id"] == run_id:
                return r["jobs"]
        return []

    def compare_files(self, base, head):
        return self.compares.get((base, head), [])

    def commit_parent(self, sha):
        return self.parents.get(sha)


class IntakeStub:
    def __init__(self):
        self.bodies = []

        outer = self

        class Handler(BaseHTTPRequestHandler):
            def do_POST(self):
                length = int(self.headers.get("Content-Length") or 0)
                raw = self.rfile.read(length).decode("utf-8", "replace")
                outer.bodies.append((self.path, json.loads(raw)))
                payload = b'{"ok": true}'
                self.send_response(201)
                self.send_header("Content-Type", "application/json")
                self.send_header("Content-Length", str(len(payload)))
                self.end_headers()
                self.wfile.write(payload)

            def log_message(self, *args):
                pass

        self.server = HTTPServer(("127.0.0.1", 0), Handler)
        threading.Thread(target=self.server.serve_forever,
                         daemon=True).start()
        self.url = f"http://127.0.0.1:{self.server.server_port}"

    def stop(self):
        self.server.shutdown()

    def reports(self):
        return [b for (p, b) in self.bodies
                if p == "/api/v1/results/reports"]


APPS = [{"slug": "foo", "name": "Foo App"},
        {"slug": "bar", "name": "Bar App"}]


def fake_fetch(url):
    if url.endswith("/data/apps.json"):
        return 200, json.dumps(APPS)
    if url.endswith("/app/foo"):
        return 200, "<html><h1>Foo App</h1></html>"
    if url.endswith("/app/bar"):
        return 200, "<html><h1>Bar App</h1></html>"
    if url.endswith("/") or url.rstrip("/").endswith("actually-free.com"):
        return 200, '<html><div id="grid"></div></html>'
    return 404, "nope"


def main():
    # Case 1: publish detection.
    records = [
        make_run(11, "success", "success", at(17, 9)),
        make_run(12, "success", "skipped", at(17, 10)),
        make_run(13, "failure", "success", at(17, 11)),
        make_run(14, "success", None, at(17, 12)),
    ]
    api = FakeApi(records)
    publishes = rr.find_publishes(api)
    check("case 1: only the standing publish counts",
          len(publishes) == 1
          and publishes[0]["run_id"] == "11"
          and publishes[0]["at"] == at(17, 9)
          and publishes[0]["sha"] == "sha11",
          json.dumps([{k: str(v) for k, v in p.items()}
                      for p in publishes]))

    # Case 2: grouping and the due rule.
    two = [
        {"run_id": "21", "sha": "sha21", "at": at(17, 9)},
        {"run_id": "22", "sha": "sha22", "at": at(17, 15)},
    ]
    groups = rr.group_by_day(two)
    check("case 2: one day, one group",
          list(groups) == ["2026-11-17"] and len(groups["2026-11-17"]) == 2,
          json.dumps(list(groups)))
    check("case 2: not due at 29 minutes",
          rr.due_groups(groups, {}, at(17, 15, 29)) == [])
    check("case 2: due at 31 minutes",
          [d for d, _ in rr.due_groups(groups, {}, at(17, 15, 31))]
          == ["2026-11-17"])
    state = {"reviewed": {"2026-11-17": {"publish_ids": ["21", "22"]}}}
    check("case 2: covered coverage is not due",
          rr.due_groups(groups, state, at(17, 16)) == [])
    state_half = {"reviewed": {"2026-11-17": {"publish_ids": ["21"]}}}
    check("case 2: extended coverage is due again",
          [d for d, _ in rr.due_groups(groups, state_half, at(17, 16))]
          == ["2026-11-17"])
    old = [{"run_id": "23", "sha": "sha23", "at": at(14, 9)}]
    check("case 2: past the watch is not chased",
          rr.due_groups(rr.group_by_day(old), {}, at(17, 12)) == [])

    # Case 3: changed views.
    paths, tree_wide = rr.changed_views(
        ["index.html", "app/foo.html", "suggest.html", "404.html",
         "data/apps.json", "assets/app.js", "docs/E2E.md",
         "generate.py"])
    check("case 3: files map to paths, the tree stands wide",
          paths == ["/", "/app/foo", "/suggest", "/data/apps.json"]
          and tree_wide is True,
          f"{paths} wide={tree_wide}")
    paths2, wide2 = rr.changed_views(["app/foo.html", "README.md"])
    check("case 3: a page-only change is not tree-wide",
          paths2 == ["/app/foo"] and wide2 is False,
          f"{paths2} wide={wide2}")

    intake = IntakeStub()
    tmp = tempfile.mkdtemp()
    try:
        env = {
            "MEMBERSPARK_RESULTS_TOKEN": "fake-token",
            "MEMBERSPARK_RESULTS_INTAKE": intake.url,
            "AF_QUARANTINE_STATE_FILE": str(Path(tmp) / "q.json"),
            "AF_RELEASE_REVIEW_STATE": str(Path(tmp) / "state.json"),
            "AF_SITE_BASE": "https://actually-free.com",
        }
        smoke.get = fake_fetch

        # Case 4: a full review, then a quiet second tick.
        records = [
            make_run(31, "success", "success", at(17, 9)),
            make_run(32, "success", "success", at(17, 15)),
        ]
        api = FakeApi(records,
                      compares={("sha31", "sha32"): ["app/foo.html"]})
        outcome = rr.main(env=env, now=at(17, 15, 31), api=api,
                          fetch=fake_fetch)
        check("case 4: the runner exits 0", outcome == 0, str(outcome))
        finishes = [b for b in intake.reports()
                    if b["phase"] == "finish"]
        check("case 4: one finish report",
              len(finishes) == 1, f"{len(finishes)} finishes")
        if finishes:
            f = finishes[0]
            names = [c["name"] for c in f["checks"]]
            check("case 4: the report names the day and its publishes",
                  f["group"] == "Release Review"
                  and f["run_id"] == "release-review-2026-11-17"
                  and f["started_by"] == "schedule"
                  and f["details"]["publishes"] == ["31", "32"]
                  and f["details"]["commit"] == "sha32"[:9],
                  json.dumps(f)[:300])
            check("case 4: heartbeat and feature checks stand",
                  "home: answers 200" in names
                  and "apps.json: holds listings" in names
                  and "Changed view /app/foo" in names
                  and f["result"] == "pass",
                  ", ".join(names))
        before = len(intake.bodies)
        rr.main(env=env, now=at(17, 15, 45), api=api, fetch=fake_fetch)
        check("case 4: a covered day sends nothing more",
              len(intake.bodies) == before,
              f"{before} -> {len(intake.bodies)}")

        # Case 5: a new publish extends the coverage.
        records.append(make_run(33, "success", "success", at(17, 18)))
        api = FakeApi(records,
                      compares={("sha31", "sha33"): ["app/foo.html"]})
        rr.main(env=env, now=at(17, 18, 31), api=api, fetch=fake_fetch)
        finishes = [b for b in intake.reports()
                    if b["phase"] == "finish"]
        check("case 5: the extended day is reviewed again",
              len(finishes) == 2
              and finishes[1]["details"]["publishes"] == ["31", "32", "33"],
              f"{len(finishes)} finishes")

        # Case 6: a lone first publish, nothing to compare.
        intake.bodies.clear()
        records = [make_run(41, "success", "success", at(17, 8))]
        api = FakeApi(records)  # no parent stands for sha41
        outcome = rr.run_review(api, fake_fetch,
                                "https://actually-free.com",
                                "2026-11-17", rr.find_publishes(api),
                                None, env=env)
        finishes = [b for b in intake.reports()
                    if b["phase"] == "finish"]
        check("case 6: the review still reports, feature not run",
              outcome.get("sent") is True
              and len(finishes) == 1
              and finishes[0]["details"]["not_run"]
              == ["Changed views answer"],
              json.dumps(finishes)[:300])
    finally:
        intake.stop()

    if failures:
        print(f"\nRELEASE REVIEW SUITE FAILED: {len(failures)} check(s): "
              + ", ".join(failures))
        return 1
    print("\nRelease Review suite passed.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
