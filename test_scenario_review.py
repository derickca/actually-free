#!/usr/bin/env python3
"""Tests for the Scenario Review suite's machinery — issue #28.

Drives the suite's own files (tests/scenario-review/) against
local fixtures only: the journey registry against the contract
in docs/E2E.md, the wire names against the centre's name
shape, the report-failure file against a fake gh, the driver's
condition wait against a local server, and the run's payload
through the reporter seam's shaper. The browser walks
themselves are proven by the suite's own runs, not here; real
GitHub, the real intake and the real credential are never
touched.
"""

import json
import sys
import threading
import unittest
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

ROOT = Path(__file__).resolve().parent
SUITE = ROOT / "tests" / "scenario-review"
sys.path.insert(0, str(SUITE))
sys.path.insert(0, str(ROOT / "tools"))

import drive  # noqa: E402
import journey as journey_mod  # noqa: E402
import report_failure  # noqa: E402
import reporter as reporter_mod  # noqa: E402


class JourneyRegistryTests(unittest.TestCase):
    def test_the_contracts_three_journeys_stand(self):
        self.assertEqual(
            [jid for jid, _ in journey_mod.JOURNEYS],
            ["core", "suggest", "what-is-free"])

    def test_every_wire_name_meets_the_store_shape(self):
        # Walk each journey's check ids as the seam names
        # them: "<journey>:<check>" must pass the centre's
        # own refusal test.
        seen = {
            "core": ["home renders the catalogue grid",
                     "platform filter narrows the grid",
                     "category filter narrows the grid",
                     "listing opens from the grid",
                     "listing carries a store or download link"],
            "suggest": ["suggest page renders",
                        "suggest form stands",
                        "suggest form can be sent"],
            "what-is-free": ["what is free page renders",
                             "page names the six promises"],
        }
        for jid, check_ids in seen.items():
            for check_id in check_ids:
                refusal = reporter_mod.check_name_refusal(
                    f"{jid}:{check_id}")
                self.assertIsNone(refusal, f"{jid}:{check_id}")


class ReportFailureTests(unittest.TestCase):
    def _round(self, results):
        return {"runId": "scenario-review-20261117-061000",
                "startedAt": "2026-11-17T06:10:00Z",
                "finishedAt": "2026-11-17T06:11:00Z",
                "passed": 1, "failed": 2, "results": results}

    def test_green_round_files_nothing(self):
        calls = []

        def fake_runner(cmd, **kw):
            calls.append(cmd)

            class Done:
                returncode = 0
            return Done()

        green = self._round([
            {"id": "core", "verdict": "PASS", "checks": []}])
        green["failed"] = 0
        self.assertIsNone(report_failure.file_failures(
            green, runner=fake_runner))
        self.assertEqual(calls, [])

    def test_failed_and_never_ran_are_named(self):
        calls = []

        def fake_runner(cmd, **kw):
            calls.append(cmd)

            class Done:
                returncode = 0
            return Done()

        body = report_failure.file_failures(self._round([
            {"id": "core", "verdict": "FAIL", "checks": [
                {"id": "platform filter narrows the grid",
                 "ok": False, "detail": "0 tiles shown"},
                {"id": "home renders the catalogue grid",
                 "ok": True, "detail": ""}]},
            {"id": "suggest", "verdict": "NOT-RUN", "checks": []},
        ]), runner=fake_runner)
        self.assertEqual(len(calls), 1)
        self.assertEqual(calls[0][:4],
                         ["gh", "issue", "comment", "27"])
        self.assertIn("Failed: core", body)
        self.assertIn("platform filter narrows the grid", body)
        self.assertIn("Never ran: suggest", body)
        self.assertNotIn("home renders the catalogue grid —", body)


class DriveWaitTests(unittest.TestCase):
    def test_wait_for_server_reads_a_standing_server(self):
        handler = lambda *a, **kw: SimpleHTTPRequestHandler(  # noqa: E731
            *a, directory=str(ROOT), **kw)
        server = ThreadingHTTPServer(("127.0.0.1", 0), handler)
        port = server.server_address[1]
        threading.Thread(target=server.serve_forever,
                         daemon=True).start()
        try:
            self.assertTrue(drive.wait_for_server(
                f"http://127.0.0.1:{port}/", timeout=10))
        finally:
            server.shutdown()

    def test_wait_for_server_gives_up_on_a_dead_port(self):
        self.assertFalse(drive.wait_for_server(
            "http://127.0.0.1:9/", timeout=0.6, interval=0.1))


class SeamShapeTests(unittest.TestCase):
    def test_payload_shapes_to_the_stores_finish(self):
        payload = {
            "runId": "scenario-review-20261117-061000",
            "startedAt": "2026-11-17T06:10:00Z",
            "finishedAt": "2026-11-17T06:11:00Z",
            "passed": 2, "failed": 1,
            "results": [
                {"id": "core", "verdict": "PASS", "checks": [
                    {"id": "home renders the catalogue grid",
                     "ok": True}]},
                {"id": "suggest", "verdict": "NOT-RUN",
                 "checks": []},
            ],
        }
        shaped = reporter_mod.shape_scenario_reports(payload)
        self.assertEqual(shaped["finish"]["result"], "fail")
        self.assertEqual(shaped["finish"]["details"]["not_run"],
                         ["suggest"])
        self.assertEqual(
            shaped["finish"]["checks"][0]["name"],
            "core:home renders the catalogue grid")
        self.assertEqual(shaped["start"]["group"],
                         "Scenario Review")


if __name__ == "__main__":
    unittest.main(verbosity=2)
