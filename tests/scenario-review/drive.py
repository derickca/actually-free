#!/usr/bin/env python3
"""drive — the Scenario Review suite's hands (issue #28).

Everything the journeys need to touch the rig: find the
headless Chrome shell, serve the rig, wait until it answers,
load a page and run a scripted walk inside it, and take a
screenshot. The suite waits on conditions, never on sleeps:
the server is polled until it answers, and a walk's script
polls the page until each condition it names stands, or its
budget runs out and the step reports the timeout.

A walk runs inside the page the way test_site.py's probes
do: the page's own HTML, fetched from the rig, with one
script added before </body>. The script drives the real
page — clicking the real controls — and writes its outcome
as JSON into document.title under an "SR:" mark, which
Chrome's --dump-dom then prints. Walks are async and poll
with waitFor(); nothing in a walk sleeps toward a result.

Screenshots use the shell's own --screenshot, the shape
tools/shots.py already uses for Build Tests.
"""

import glob
import json
import re
import subprocess
import threading
import time
import urllib.parse
import urllib.request
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

_shells = sorted(glob.glob(str(
    Path.home() / ".cache/ms-playwright/chromium_headless_shell-*"
    / "chrome-headless-shell-linux64/chrome-headless-shell")))
CHROME = _shells[-1] if _shells else ""

TITLE_MARK = "SR:"


def chrome_available():
    return bool(CHROME)


def wait_for_server(url, timeout=30.0, interval=0.2):
    """Poll url until it answers 200, or the budget runs
    out. Returns True when the server stands."""
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        try:
            with urllib.request.urlopen(url, timeout=5) as resp:
                if resp.status == 200:
                    return True
        except Exception:
            pass
        time.sleep(interval)
    return False


class _QuietHandler(SimpleHTTPRequestHandler):
    def log_message(self, *args):
        pass


class _RigHTTPServer(ThreadingHTTPServer):
    def handle_error(self, request, client_address):
        # A browser closing a connection mid-answer is the
        # rig's ordinary weather, not a failure to report.
        pass


class RigServer:
    """Serve a directory on 127.0.0.1 at an OS-chosen port."""

    def __init__(self, root):
        self.root = Path(root)
        handler = lambda *a, **kw: _QuietHandler(  # noqa: E731
            *a, directory=str(self.root), **kw)
        self.server = _RigHTTPServer(("127.0.0.1", 0), handler)
        self.port = self.server.server_address[1]
        self.thread = threading.Thread(
            target=self.server.serve_forever, daemon=True)

    def __enter__(self):
        self.thread.start()
        return self

    def __exit__(self, *exc):
        self.server.shutdown()
        self.server.server_close()

    def url(self, path):
        return f"http://127.0.0.1:{self.port}{path}"


def file_for(root, path):
    """The local file a pretty path stands for, the same
    mapping tools/shots.py uses: /app/x is app/x.html on
    disk, /suggest is suggest.html, / is the home page."""
    rel = path.strip("/")
    if not rel:
        return "/index.html"
    for cand in (rel, rel + ".html", rel + "/index.html"):
        if (Path(root) / cand).is_file():
            return "/" + cand
    return path


# The walk harness every probe runs under: waitFor polls a
# condition; done() writes the outcome into the title.
HARNESS = """
<script>
window.__srDone = false;
function __srDoneFn(payload) {
  if (window.__srDone) return;
  window.__srDone = true;
  document.title = "SR:" + encodeURIComponent(JSON.stringify(payload));
}
function __srWaitFor(fn, ms, label) {
  return new Promise(function (resolve, reject) {
    var t0 = Date.now();
    var iv = setInterval(function () {
      var ok = false;
      try { ok = fn(); } catch (e) {}
      if (ok) { clearInterval(iv); resolve(true); }
      else if (Date.now() - t0 > ms) {
        clearInterval(iv);
        reject(new Error("timed out waiting for " + label));
      }
    }, 100);
  });
}
window.addEventListener("load", function () {
  (async function () {
    try { await __srWalk(__srWaitFor); __srDoneFn(window.__srOut); }
    catch (e) {
      window.__srOut = window.__srOut || {};
      window.__srOut.error = e.message;
      __srDoneFn(window.__srOut);
    }
  })();
});
</script>
"""


def probe(rig_root, base_url, path, walk_js, width=1280,
          budget_ms=45000, timeout=120):
    """Load path from the rig with walk_js as its __srWalk,
    and return the walk's outcome dict. The walk receives
    waitFor and leaves its outcome in window.__srOut.
    Raises RuntimeError when Chrome cannot run the page."""
    served = file_for(rig_root, path)
    with urllib.request.urlopen(base_url + served, timeout=15) as resp:
        html = resp.read().decode("utf-8", "replace")
    if "</body>" not in html:
        raise RuntimeError(f"{path} carries no </body> to walk from")
    script = ("<script>window.__srOut = {};\n"
              f"async function __srWalk(waitFor) {{\n{walk_js}\n}}\n"
              "</script>")
    probed = html.replace("</body>", script + HARNESS + "</body>", 1)
    probe_file = Path(rig_root) / (
        served.lstrip("/").rsplit(".html", 1)[0] + "-srprobe.html")
    probe_file.write_text(probed, encoding="utf-8")
    try:
        out = subprocess.run(
            [CHROME, "--no-sandbox", "--no-proxy-server",
             "--disable-gpu", f"--virtual-time-budget={budget_ms}",
             "--dump-dom", f"--window-size={width},900",
             base_url + "/" + probe_file.relative_to(rig_root).as_posix()],
            capture_output=True, text=True, timeout=timeout)
    finally:
        probe_file.unlink(missing_ok=True)
    match = re.search(r"<title>(.*?)</title>", out.stdout, re.S)
    if not match:
        raise RuntimeError(f"no title came back from {path}")
    title = match.group(1)
    if not title.startswith(TITLE_MARK):
        raise RuntimeError(f"the walk on {path} never reported")
    return json.loads(urllib.parse.unquote(title[len(TITLE_MARK):]))


def screenshot(rig_root, base_url, path, out_file, width=1280):
    """Photograph path as the rig serves it. Returns True
    when the picture stands on disk."""
    served = file_for(rig_root, path)
    out_file = Path(out_file)
    out_file.parent.mkdir(parents=True, exist_ok=True)
    result = subprocess.run(
        [CHROME, "--headless", "--no-sandbox", "--no-proxy-server",
         "--disable-gpu", f"--screenshot={out_file}",
         f"--window-size={width},900", "--virtual-time-budget=15000",
         "--hide-scrollbars", base_url + served],
        capture_output=True, text=True, timeout=90)
    return result.returncode == 0 and out_file.exists()
