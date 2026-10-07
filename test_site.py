#!/usr/bin/env python3
"""Regression tests for the Actually Free site.

Covers the failure modes Derick has caught in review:
  1. Taxonomy placements (data/apps.json) — specific apps in expected homes.
  2. Subcategory filter order is alphabetical.
  3. Collapsed subcategory row: zero height, no overlap, gap preserved.
  4. Open subcategory row: stable height across subcategory selection.
  5. Mobile: subcategory row scrolls horizontally when chips overflow.

Usage: python3 test_site.py [--serve-port 8131]
Runs generate.py first, then serves and drives headless Chrome.
"""
import json
import subprocess
import sys
import time
import urllib.request
from collections import Counter
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

HERE = Path(__file__).parent
CHROME = str(Path.home() / ".cache/ms-playwright/chromium_headless_shell-1243"
             / "chrome-headless-shell-linux64/chrome-headless-shell")

FAILURES = []


def check(name, cond, detail=""):
    status = "PASS" if cond else "FAIL"
    print(f"[{status}] {name}" + (f" — {detail}" if detail and not cond else ""))
    if not cond:
        FAILURES.append(name)


def chrome_eval(url, js, width=1280, height=800, vtb=15000):
    """Load url in headless Chrome, run js after load, return document.title."""
    probe = f"""<script>setTimeout(function(){{try{{{js}}}catch(e){{
        document.title='ERROR:'+e.message;}}}},1800);</script></body>"""
    html = (HERE / "index.html").read_text().replace("</body>", probe)
    tmp = HERE / "_test_probe.html"
    tmp.write_text(html)
    try:
        out = subprocess.run(
            [CHROME, "--no-sandbox", "--no-proxy-server", "--disable-gpu",
             f"--virtual-time-budget={vtb}", "--dump-dom",
             f"--window-size={width},{height}",
             f"http://127.0.0.1:{PORT}/_test_probe.html"],
            capture_output=True, text=True, timeout=90)
        for line in out.stdout.splitlines():
            if "<title>" in line:
                s = line.split("<title>", 1)[1]
                return s.split("</title>", 1)[0]
    finally:
        tmp.unlink(missing_ok=True)
    return "ERROR:no-title"


def main():
    global PORT
    PORT = int(sys.argv[sys.argv.index("--serve-port") + 1]) if "--serve-port" in sys.argv else 8131

    # 1. Regenerate
    r = subprocess.run([sys.executable, "generate.py"], cwd=HERE, capture_output=True, text=True)
    check("generate.py exits 0", r.returncode == 0, r.stderr[-500:] if r.returncode else "")
    r = subprocess.run(["node", "--check", "assets/app.js"], cwd=HERE, capture_output=True)
    check("app.js syntax OK", r.returncode == 0)

    apps = json.loads((HERE / "data/apps.json").read_text())
    m = {a["name"]: (a["category"], a["subcategory"]) for a in apps}

    # 2. Taxonomy placements (Derick's rulings)
    expected = {
        "Chess Clock": ("Games", "Puzzle"),
        "Suspension Setup": ("Lifestyle", "Health"),
        "Krita": ("Media", "Photos"),
        "Jellyfin": ("Media", "Home Theater"),
        "Amaze File Manager": ("System", "Files"),
        "Firefox": ("System", "Internet"),
        "Easer": ("System", "Automate"),
        "Maid": ("System", "Automate"),
        "Jidoujisho": ("Lifestyle", "Education"),
        "Storii - audiobookshelf client": ("Media", "Audio"),
        "BetterCounter": ("Lifestyle", "Health"),
    }
    for name, want in expected.items():
        check(f"taxonomy: {name}", m.get(name) == want,
              f"got {m.get(name)}, want {want}")

    # 3. Subcategory shape: Media/Graphics gone, Home Theater exists, etc.
    subs = Counter((a["category"], a["subcategory"]) for a in apps)
    check("Media/Graphics merged into Photos", ("Media", "Graphics") not in subs)
    check("Media/Home Theater exists", ("Media", "Home Theater") in subs)
    check("Utilities/Files moved to System", ("Utilities", "Files") not in subs)
    check("System/Files exists", ("System", "Files") in subs)
    check("no empty subcategories", all(n > 0 for n in subs.values()))

    # 4. Alphabetical subcategory order in the emitted JS derivation.
    #    (renderSubcats sorts; verify via the live page below.)

    # Serve + browser checks
    class H(SimpleHTTPRequestHandler):
        def log_message(self, *a):
            pass
    srv = ThreadingHTTPServer(("127.0.0.1", PORT), H)
    import threading, os
    os.chdir(HERE)
    threading.Thread(target=srv.serve_forever, daemon=True).start()
    time.sleep(0.5)

    # 5. Collapsed state: zero height, no overlap, gap to attr pills.
    t = chrome_eval("", """
      var col = document.getElementById('sub-collapse');
      var cat = document.getElementById('category-chips');
      var attr = document.getElementById('attr-pills');
      var cb = cat.getBoundingClientRect(), ab = attr.getBoundingClientRect();
      document.title = JSON.stringify({
        h: col.getBoundingClientRect().height,
        op: getComputedStyle(col).opacity,
        gap: ab.top - cb.bottom
      });
    """)
    d = json.loads(t)
    check("collapsed: zero height", d["h"] < 1, t)
    check("collapsed: invisible", float(d["op"]) == 0, t)
    check("collapsed: gap to attr row >= 8px (no overlap)", d["gap"] >= 8, t)

    # 6. Open state: visible, gap to attr row, alphabetical chips.
    t = chrome_eval("", """
      document.querySelector('#category-chips [data-cat="Utilities"]').click();
      setTimeout(function(){
        var col = document.getElementById('sub-collapse');
        var sub = document.getElementById('subcategory-chips');
        var attr = document.getElementById('attr-pills');
        var sb = sub.getBoundingClientRect(), ab = attr.getBoundingClientRect();
        var names = [];
        sub.querySelectorAll('.chip').forEach(function(c){ names.push(c.textContent); });
        var sorted = names.slice().sort(function(a,b){
          return a.toLowerCase() < b.toLowerCase() ? -1 : 1; });
        document.title = JSON.stringify({
          h: col.getBoundingClientRect().height,
          op: getComputedStyle(col).opacity,
          gap: ab.top - sb.bottom,
          alpha: JSON.stringify(names) === JSON.stringify(sorted),
          names: names.join(',')
        });
      }, 900);
    """)
    d = json.loads(t)
    check("open: visible with height", d["h"] > 20 and float(d["op"]) == 1, t)
    check("open: gap to attr row >= 8px", d["gap"] >= 8, t)
    check("open: subcategories alphabetical", d["alpha"], d.get("names", t))

    # 7. Stable height across subcategory selection (the 31px->37px jump).
    t = chrome_eval("", """
      document.querySelector('#category-chips [data-cat="Utilities"]').click();
      setTimeout(function(){
        var sub = document.getElementById('subcategory-chips');
        var h1 = sub.getBoundingClientRect().height;
        document.querySelector('#subcategory-chips [data-subcat="Time"]').click();
        setTimeout(function(){
          var h2 = sub.getBoundingClientRect().height;
          document.querySelector('#subcategory-chips [data-subcat="Apps"]').click();
          setTimeout(function(){
            var h3 = sub.getBoundingClientRect().height;
            document.title = JSON.stringify({h1:h1, h2:h2, h3:h3});
          }, 700);
        }, 700);
      }, 900);
    """)
    d = json.loads(t)
    stable = abs(d["h1"] - d["h2"]) < 1 and abs(d["h2"] - d["h3"]) < 1
    check("open: height stable across subcategory selection", stable, t)

    # 8. Mobile: subcategory row scrolls horizontally.
    t = chrome_eval("", """
      document.querySelector('#category-chips [data-cat="System"]').click();
      setTimeout(function(){
        var sub = document.getElementById('subcategory-chips');
        document.title = JSON.stringify({
          scrollW: sub.scrollWidth, clientW: sub.clientWidth,
          overflowX: getComputedStyle(sub).overflowX
        });
      }, 900);
    """, width=390, height=844)
    d = json.loads(t)
    check("mobile: subcategory row scrolls (scrollWidth > clientWidth)",
          d["scrollW"] > d["clientW"] + 20, t)

    srv.shutdown()
    print()
    if FAILURES:
        print(f"{len(FAILURES)} FAILURES: {FAILURES}")
        return 1
    print("All tests passed.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
