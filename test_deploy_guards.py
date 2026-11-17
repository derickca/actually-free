#!/usr/bin/env python3
"""The deploy guards' own suite (issue #37).

Runs tools/check-publish-set.py and tools/check-removal-tripwire.py
as subprocesses against fixture trees in temporary directories —
small staged sets in Actually Free's own shapes (the root, the two
extensionless top-level pages and /app/<slug> listing pages) — and,
for the tripwire's live read, a local stub serving a fixture
sitemap. The live site is never touched.

Cases:
  Publish-set check (tools/check-publish-set.py):
   1. A complete staged tree passes: every sitemap URL maps to a
      file, every listing has a page and a sitemap URL.
   2. A sitemap URL whose file is missing fails, and the failure
      names the URL.
   3. A listing whose page file is missing fails, and the failure
      names the listing.
   4. A listing whose page stands but whose sitemap URL is
      missing fails, and the failure names the listing.
   5. A staged sitemap listing no URLs fails.
  Removal tripwire (tools/check-removal-tripwire.py):
   6. A staged set equal to the live set passes.
   7. A live URL missing from the staged set, with no retirement
      recorded, fails and names the URL.
   8. The same removal, recorded in the retirements file,
      passes, and the output names it as a recorded retirement.
   9. An empty live sitemap fails — the tripwire cannot pass on
      an empty read.
  10. The live sitemap fetched over HTTP from a local stub, sets
      equal, passes — the road the deploy step itself takes.

Usage:  python3 test_deploy_guards.py
Exit 0 = every case passed, 1 = a failure (named on its line).
"""

import json
import subprocess
import sys
import tempfile
import threading
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path

ROOT = Path(__file__).resolve().parent
PUBLISH_SET = ROOT / "tools" / "check-publish-set.py"
TRIPWIRE = ROOT / "tools" / "check-removal-tripwire.py"
SITE = "https://actually-free.com"

SLUGS = ("7-zip-windows", "zotero-mac")


def sitemap_text(slugs=SLUGS, extra=()):
    urls = [f"{SITE}/", f"{SITE}/suggest", f"{SITE}/what-is-free"]
    urls += [f"{SITE}/app/{s}" for s in slugs]
    urls += list(extra)
    body = "".join(f"  <url><loc>{u}</loc></url>\n" for u in urls)
    return ('<?xml version="1.0" encoding="UTF-8"?>\n'
            '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n'
            + body + "</urlset>\n")


def write_tree(base, slugs=SLUGS, sitemap=None, drop_pages=(),
               drop_from_sitemap=()):
    """A staged-tree fixture: pages, listings and a sitemap."""
    base = Path(base)
    (base / "app").mkdir(parents=True, exist_ok=True)
    (base / "data").mkdir(parents=True, exist_ok=True)
    pages = {"index.html": "home", "suggest.html": "suggest",
             "what-is-free.html": "what is free"}
    for slug in slugs:
        pages[f"app/{slug}.html"] = f"listing {slug}"
    for rel, text in pages.items():
        if rel not in drop_pages:
            (base / rel).write_text(text, encoding="utf-8")
    kept = [s for s in slugs if s not in drop_from_sitemap]
    (base / "sitemap.xml").write_text(
        sitemap if sitemap is not None else sitemap_text(kept),
        encoding="utf-8")
    apps = [{"name": s, "slug": s} for s in slugs]
    (base / "data" / "apps.json").write_text(
        json.dumps(apps), encoding="utf-8")
    return base


def run(script, *args):
    return subprocess.run(
        [sys.executable, str(script), *[str(a) for a in args]],
        capture_output=True, text=True)


failures = []


def check(name, ok, detail=""):
    print(f"{'PASS' if ok else 'FAIL'}  {name}"
          + (f" — {detail}" if detail and not ok else ""))
    if not ok:
        failures.append(name)


def main():
    with tempfile.TemporaryDirectory() as tmp:
        tmp = Path(tmp)

        # --- Publish-set check -----------------------------------
        good = write_tree(tmp / "good")
        r = run(PUBLISH_SET, "--staged-dir", good)
        check("1. a complete staged tree passes",
              r.returncode == 0 and "OK" in r.stdout, r.stdout + r.stderr)

        no_file = write_tree(tmp / "no-file",
                             sitemap=sitemap_text(
                                 extra=[f"{SITE}/app/ghost-mac"]))
        r = run(PUBLISH_SET, "--staged-dir", no_file)
        check("2. a sitemap URL with no file fails, naming it",
              r.returncode == 1 and "ghost-mac" in r.stdout,
              r.stdout + r.stderr)

        no_page = write_tree(tmp / "no-page",
                             drop_pages={"app/zotero-mac.html"})
        r = run(PUBLISH_SET, "--staged-dir", no_page)
        check("3. a listing with no page fails, naming it",
              r.returncode == 1 and "zotero-mac" in r.stdout,
              r.stdout + r.stderr)

        no_entry = write_tree(tmp / "no-entry",
                              drop_from_sitemap={"zotero-mac"})
        r = run(PUBLISH_SET, "--staged-dir", no_entry)
        check("4. a listing with no sitemap URL fails, naming it",
              r.returncode == 1 and "zotero-mac" in r.stdout,
              r.stdout + r.stderr)

        empty = write_tree(tmp / "empty")
        (empty / "sitemap.xml").write_text(
            '<?xml version="1.0" encoding="UTF-8"?>\n'
            '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">'
            "\n</urlset>\n", encoding="utf-8")
        r = run(PUBLISH_SET, "--staged-dir", empty)
        check("5. a staged sitemap listing no URLs fails",
              r.returncode == 1, r.stdout + r.stderr)

        # --- Removal tripwire ------------------------------------
        live_full = tmp / "live-full.xml"
        live_full.write_text(sitemap_text(), encoding="utf-8")
        staged_full = tmp / "staged-full.xml"
        staged_full.write_text(sitemap_text(), encoding="utf-8")
        staged_missing = tmp / "staged-missing.xml"
        staged_missing.write_text(sitemap_text(slugs=("7-zip-windows",)),
                                  encoding="utf-8")
        retired = tmp / "retired.txt"
        retired.write_text(
            "# retirements\n"
            "/app/zotero-mac 2026-11-17 — delisted by the owner\n",
            encoding="utf-8")
        no_retired = tmp / "retired-empty.txt"
        no_retired.write_text("# retirements\n", encoding="utf-8")

        r = run(TRIPWIRE, "--live-file", live_full,
                "--staged", staged_full, "--retired", no_retired)
        check("6. a staged set equal to the live set passes",
              r.returncode == 0 and "OK" in r.stdout, r.stdout + r.stderr)

        r = run(TRIPWIRE, "--live-file", live_full,
                "--staged", staged_missing, "--retired", no_retired)
        check("7. an unrecorded removal fails, naming the URL",
              r.returncode == 1 and "zotero-mac" in r.stdout,
              r.stdout + r.stderr)

        r = run(TRIPWIRE, "--live-file", live_full,
                "--staged", staged_missing, "--retired", retired)
        check("8. a recorded removal passes, named as recorded",
              r.returncode == 0
              and "recorded deliberate retirement" in r.stdout
              and "zotero-mac" in r.stdout, r.stdout + r.stderr)

        live_empty = tmp / "live-empty.xml"
        live_empty.write_text("", encoding="utf-8")
        r = run(TRIPWIRE, "--live-file", live_empty,
                "--staged", staged_full, "--retired", no_retired)
        check("9. an empty live read fails",
              r.returncode == 1, r.stdout + r.stderr)

        # Case 10: the live sitemap over HTTP, from a local stub.
        class Handler(BaseHTTPRequestHandler):
            def do_GET(self):
                body = sitemap_text().encode()
                self.send_response(200)
                self.send_header("Content-Type", "application/xml")
                self.send_header("Content-Length", str(len(body)))
                self.end_headers()
                self.wfile.write(body)

            def log_message(self, *args):
                pass

        server = HTTPServer(("127.0.0.1", 0), Handler)
        thread = threading.Thread(target=server.serve_forever,
                                  daemon=True)
        thread.start()
        try:
            live_url = (f"http://127.0.0.1:{server.server_port}"
                        "/sitemap.xml")
            r = run(TRIPWIRE, "--live", live_url,
                    "--staged", staged_full, "--retired", no_retired)
        finally:
            server.shutdown()
        check("10. the live sitemap fetched over HTTP passes",
              r.returncode == 0 and "OK" in r.stdout, r.stdout + r.stderr)

    total = 10
    print(f"test_deploy_guards: {total - len(failures)}/{total} "
          "cases passed"
          + (f"; FAILURES in: {', '.join(failures)}" if failures
             else ""))
    return 1 if failures else 0


if __name__ == "__main__":
    sys.exit(main())
