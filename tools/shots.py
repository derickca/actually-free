#!/usr/bin/env python3
"""Screenshots for Build Tests — the views named in docs/E2E.md.

Serves the committed tree locally and photographs each view at
desktop (1280) and phone (390) widths into shots/, for the person
or agent landing a change to look at before the push. Screenshots
stay on this machine; they never go to the centre.

Usage: python3 tools/shots.py [path ...]
Paths default to the home page, Suggest, What is free, and the
first listing's page. Name a change's own views when they differ.
"""
import glob
import json
import subprocess
import sys
import threading
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

HERE = Path(__file__).parent.parent
SHOTS = HERE / "shots"
WIDTHS = (1280, 390)

_shells = sorted(glob.glob(str(
    Path.home() / ".cache/ms-playwright/chromium_headless_shell-*"
    / "chrome-headless-shell-linux64/chrome-headless-shell")))
CHROME = _shells[-1] if _shells else ""


def name_for(path):
    slug = path.strip("/").replace("/", "-")
    return slug if slug else "home"


def file_for(path):
    """The local file a pretty path stands for: /app/x is app/x.html
    on disk, and Pages serves the one from the other."""
    rel = path.strip("/")
    if not rel:
        return "/"
    for cand in (rel, rel + ".html", rel + "/index.html"):
        if (HERE / cand).is_file():
            return "/" + cand
    return path


def main():
    if not CHROME:
        print("No headless Chrome shell found under ~/.cache/ms-playwright.")
        return 1
    paths = sys.argv[1:]
    if not paths:
        apps = json.loads((HERE / "data/apps.json").read_text())
        paths = ["/", "/suggest", "/what-is-free",
                 f"/app/{apps[0]['slug']}"]

    handler = lambda *a, **kw: SimpleHTTPRequestHandler(
        *a, directory=str(HERE), **kw)
    server = ThreadingHTTPServer(("127.0.0.1", 0), handler)
    port = server.server_address[1]
    threading.Thread(target=server.serve_forever, daemon=True).start()

    SHOTS.mkdir(exist_ok=True)
    try:
        for path in paths:
            for width in WIDTHS:
                out = SHOTS / f"{name_for(path)}-{width}.png"
                subprocess.run(
                    [CHROME, "--headless", "--no-sandbox",
                     "--no-proxy-server", "--disable-gpu",
                     f"--screenshot={out}", f"--window-size={width},900",
                     "--virtual-time-budget=15000", "--hide-scrollbars",
                     f"http://127.0.0.1:{port}{file_for(path)}"],
                    check=True, capture_output=True, timeout=60)
                print(f"{out.relative_to(HERE)}")
    finally:
        server.shutdown()
    return 0


if __name__ == "__main__":
    sys.exit(main())
