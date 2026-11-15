#!/usr/bin/env python3
"""The Bing submission script's own suite (issue #40).

Runs tools/bing-submit.py as a subprocess against a fixture
publish set — a throwaway tree whose sitemap names five URLs
in Actually Free's own shapes (the root, two extensionless
top-level pages and two /app/<slug> listing pages) — and a
local stub standing in for Bing's SubmitUrlbatch endpoint.
The real Bing API and the real key are never touched: the
stub captures each request and answers as the case directs,
and the key the script fetches is a fake one printed by a
stub op-secret.sh.

Cases:
  1. First run (no manifest): the whole sitemap set goes in
     one POST — the endpoint path, the apikey query, the
     siteUrl and urlList body all as the API takes them — and
     the manifest is written with every URL's hash.
  2. Second run, nothing changed: no request is made.
  3. One page's bytes change: exactly that URL is submitted,
     and the manifest advances for it alone.
  4. The stub answers 500: the run still exits 0, the failure
     is reported, and the manifest does not advance — a rerun
     submits the same URL again.
  5. The key fetch refuses: the run still exits 0, the failure
     is reported, no request is made, the manifest stands.
  6. --dry-run: the pending URL is named, no request is made,
     the manifest stands.
  7. The stub enforces a daily quota smaller than the batch
     (the answer Bing's real API gave the first production
     run, ErrorCode 8): the refused batch is retried at
     exactly the remaining quota, those URLs are accepted,
     the rest stay due, and the next run submits them.
  8. A 105-page set goes in batches of at most 100.

Usage:  python3 test_bing_submit.py
Exit 0 = every case passed, 1 = a failure (named on its line).
"""

import hashlib
import json
import os
import subprocess
import sys
import tempfile
import threading
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path

ROOT = Path(__file__).resolve().parent
SCRIPT = ROOT / "tools" / "bing-submit.py"
SITE = "https://actually-free.com"
FAKE_KEY = "fake-key-for-the-stub"

PAGES = {
    "/": "home page v1",
    "/suggest": "suggest page v1",
    "/what-is-free": "what is free v1",
    "/app/7-zip-windows": "7-zip windows v1",
    "/app/zotero-mac": "zotero mac v1",
}


def url_to_file(url):
    path = url[len(SITE):]
    if path in ("", "/"):
        return "index.html"
    if path.endswith("/"):
        return path.lstrip("/") + "index.html"
    return path.lstrip("/") + ".html"


class Stub:
    """A local stand-in for the SubmitUrlbatch endpoint: records
    (path, body) per request and answers the status it's set to."""

    def __init__(self):
        self.requests = []
        self.status = 200
        # None = no quota. A number = the day's remaining quota,
        # enforced the way Bing's real API enforces it: a batch
        # that runs past it is refused whole with ErrorCode 8.
        self.quota = None
        outer = self

        class Handler(BaseHTTPRequestHandler):
            def do_POST(self):
                n = int(self.headers.get("Content-Length") or 0)
                raw = self.rfile.read(n).decode()
                outer.requests.append((self.path, raw))
                status = outer.status
                body = b'{"d": null}'
                if status == 200 and outer.quota is not None:
                    count = len(json.loads(raw).get("urlList") or [])
                    if count > outer.quota:
                        status = 400
                        body = json.dumps({
                            "ErrorCode": 8,
                            "Message": "ERROR!!! Quota remaining "
                            f"for today: {outer.quota}, "
                            f"Submitted: {count}"}).encode()
                    else:
                        outer.quota -= count
                self.send_response(status)
                self.send_header("Content-Type", "application/json")
                self.send_header("Content-Length", str(len(body)))
                self.end_headers()
                self.wfile.write(body)

            def log_message(self, *a):
                pass

        self.server = HTTPServer(("127.0.0.1", 0), Handler)
        self.port = self.server.server_address[1]
        threading.Thread(target=self.server.serve_forever,
                         daemon=True).start()

    @property
    def endpoint(self):
        return (f"http://127.0.0.1:{self.port}"
                f"/webmaster/api.svc/json/SubmitUrlbatch")


failures = []


def check(name, ok, detail=""):
    print(f"{'PASS' if ok else 'FAIL'}  {name}"
          + (f" — {detail}" if detail and not ok else ""))
    if not ok:
        failures.append(name)


def main():
    stub = Stub()
    with tempfile.TemporaryDirectory() as td:
        td = Path(td)
        staged = td / "site"
        locs = []
        for path, text in PAGES.items():
            f = staged / url_to_file(SITE + path)
            f.parent.mkdir(parents=True, exist_ok=True)
            f.write_text(text)
            locs.append(f"  <url><loc>{SITE}{path}</loc></url>")
        (staged / "sitemap.xml").write_text(
            '<?xml version="1.0" encoding="UTF-8"?>\n'
            '<urlset xmlns="http://www.sitemaps.org/schemas/'
            'sitemap/0.9">\n' + "\n".join(locs) + "\n</urlset>\n")
        manifest = td / "manifest.json"

        helper = td / "op-secret.sh"
        helper.write_text(
            "#!/bin/sh\n"
            "case \"$1\" in\n"
            "  *Bing*) printf '%s' '" + FAKE_KEY + "' ;;\n"
            "  *) echo 'unexpected reference' >&2; exit 4 ;;\n"
            "esac\n")
        helper.chmod(0o755)
        refusing = td / "op-secret-refusing.sh"
        refusing.write_text(
            "#!/bin/sh\necho '[error] no item found' >&2\nexit 4\n")
        refusing.chmod(0o755)

        def run(helper_path=helper, extra=()):
            env = dict(os.environ)
            env.update({
                "BING_STAGED_DIR": str(staged),
                "BING_MANIFEST": str(manifest),
                "BING_SUBMIT_ENDPOINT": stub.endpoint,
                "OP_SECRET_SH": str(helper_path),
            })
            env.pop("BING_WEBMASTER_API_KEY", None)
            env.pop("GITHUB_STEP_SUMMARY", None)
            return subprocess.run(
                [sys.executable, str(SCRIPT), *extra],
                capture_output=True, text=True, env=env, timeout=60)

        def manifest_urls():
            return json.loads(manifest.read_text())["urls"]

        all_urls = sorted(SITE + p for p in PAGES)

        # Case 1 — first run submits the whole set, in one POST,
        # shaped as the API takes it, and writes the manifest.
        r = run()
        check("case 1: first run exits 0", r.returncode == 0,
              r.stderr[-300:])
        check("case 1: exactly one request", len(stub.requests) == 1,
              f"{len(stub.requests)} requests")
        if stub.requests:
            path, body = stub.requests[0]
            check("case 1: endpoint path and apikey query",
                  path == "/webmaster/api.svc/json/SubmitUrlbatch"
                  f"?apikey={FAKE_KEY}", path)
            payload = json.loads(body)
            check("case 1: body carries the site and every URL",
                  payload.get("siteUrl") == SITE
                  and sorted(payload.get("urlList") or []) == all_urls,
                  body[:200])
        check("case 1: manifest written with every URL",
              manifest.is_file()
              and sorted(manifest_urls()) == all_urls)
        if manifest.is_file():
            want = hashlib.sha256(b"home page v1").hexdigest()
            check("case 1: manifest hash is the staged bytes' hash",
                  manifest_urls().get(SITE + "/") == want)

        # Case 2 — nothing changed: no request.
        stub.requests.clear()
        r = run()
        check("case 2: unchanged run exits 0 and sends nothing",
              r.returncode == 0 and not stub.requests
              and "no changed URLs" in r.stdout,
              f"rc={r.returncode} requests={len(stub.requests)}")

        # Case 3 — one page changes: exactly its URL is submitted.
        (staged / "suggest.html").write_text("suggest page v2")
        stub.requests.clear()
        r = run()
        sent = []
        if stub.requests:
            sent = json.loads(stub.requests[0][1]).get("urlList") or []
        check("case 3: only the changed URL is submitted",
              r.returncode == 0 and sent == [SITE + "/suggest"],
              f"sent={sent}")
        want = hashlib.sha256(b"suggest page v2").hexdigest()
        check("case 3: manifest advanced for that URL alone",
              manifest_urls().get(SITE + "/suggest") == want)

        # Case 4 — Bing answers 500: exit 0, failure reported,
        # manifest holds, and a rerun retries the same URL.
        (staged / "index.html").write_text("home page v2")
        stub.status = 500
        before = manifest.read_text()
        stub.requests.clear()
        r = run()
        check("case 4: a 500 still exits 0 and is reported",
              r.returncode == 0 and "FAILED" in r.stdout
              and len(stub.requests) == 1,
              f"rc={r.returncode} out={r.stdout.strip()[:160]}")
        check("case 4: manifest did not advance",
              manifest.read_text() == before)
        stub.status = 200
        stub.requests.clear()
        r = run()
        sent = []
        if stub.requests:
            sent = json.loads(stub.requests[0][1]).get("urlList") or []
        check("case 4: the rerun retries the unsubmitted URL",
              sent == [SITE + "/"], f"sent={sent}")

        # Case 5 — the key fetch refuses: exit 0, reported, no
        # request, manifest stands.
        (staged / "app" / "7-zip-windows.html").write_text(
            "7-zip windows v2")
        before = manifest.read_text()
        stub.requests.clear()
        r = run(helper_path=refusing)
        check("case 5: a refused fetch exits 0, reports, sends nothing",
              r.returncode == 0 and "FAILED" in r.stdout
              and not stub.requests
              and manifest.read_text() == before,
              f"rc={r.returncode} requests={len(stub.requests)}")

        # Case 6 — dry run names the pending URL and touches
        # nothing.
        stub.requests.clear()
        r = run(extra=("--dry-run",))
        check("case 6: dry run names the pending URL only",
              r.returncode == 0
              and (SITE + "/app/7-zip-windows") in r.stdout
              and not stub.requests
              and manifest.read_text() == before,
              f"out={r.stdout.strip()[:160]}")

        # Case 7 — the day's quota (3) is smaller than the batch
        # (the whole 5-page set): the batch is refused whole,
        # retried at exactly the quota, and the rest stay due
        # until the next run.
        manifest.unlink()
        stub.quota = 3
        stub.requests.clear()
        r = run()
        check("case 7: a quota refusal still exits 0",
              r.returncode == 0, f"rc={r.returncode}")
        check("case 7: two requests — the refused batch, the fit",
              len(stub.requests) == 2,
              f"{len(stub.requests)} requests")
        check("case 7: manifest holds exactly the quota's worth",
              sorted(manifest_urls()) == all_urls[:3],
              f"manifest={sorted(manifest_urls())}")
        check("case 7: the spent quota is reported",
              "quota is spent" in r.stdout
              and "3 of 5" in r.stdout,
              f"out={r.stdout.strip()[:200]}")
        stub.quota = None
        stub.requests.clear()
        r = run()
        check("case 7: the next run submits what stayed due",
              r.returncode == 0
              and sorted(manifest_urls()) == all_urls,
              f"manifest={sorted(manifest_urls())}")

        # Case 8 — 105 pages go in batches of at most 100.
        staged2 = td / "site2"
        locs = []
        for i in range(105):
            f = staged2 / "app" / f"p{i:03}.html"
            f.parent.mkdir(parents=True, exist_ok=True)
            f.write_text(f"page {i} v1")
            locs.append(
                f"  <url><loc>{SITE}/app/p{i:03}</loc></url>")
        (staged2 / "sitemap.xml").write_text(
            '<?xml version="1.0" encoding="UTF-8"?>\n'
            '<urlset xmlns="http://www.sitemaps.org/schemas/'
            'sitemap/0.9">\n' + "\n".join(locs) + "\n</urlset>\n")
        manifest2 = td / "manifest2.json"
        env = dict(os.environ)
        env.update({
            "BING_STAGED_DIR": str(staged2),
            "BING_MANIFEST": str(manifest2),
            "BING_SUBMIT_ENDPOINT": stub.endpoint,
            "OP_SECRET_SH": str(helper),
        })
        env.pop("BING_WEBMASTER_API_KEY", None)
        env.pop("GITHUB_STEP_SUMMARY", None)
        stub.requests.clear()
        r = subprocess.run(
            [sys.executable, str(SCRIPT)],
            capture_output=True, text=True, env=env, timeout=60)
        sizes = [len(json.loads(b).get("urlList") or [])
                 for _, b in stub.requests]
        check("case 8: 105 pages accepted in batches of at most 100",
              r.returncode == 0 and sizes == [100, 5]
              and len(json.loads(
                  manifest2.read_text())["urls"]) == 105,
              f"rc={r.returncode} sizes={sizes}")

    print(f"test_bing_submit: {8 - len(failures)}/8 cases passed"
          if not failures else
          f"test_bing_submit: FAILURES in: {', '.join(failures)}")
    return 1 if failures else 0


if __name__ == "__main__":
    sys.exit(main())
