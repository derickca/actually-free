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
        "Amaze File Manager": ("Productivity", "Files"),
        "Firefox": ("System", "Internet"),
        "Easer": ("System", "Automate"),
        "Maid": ("System", "Automate"),
        "Jidoujisho": ("Lifestyle", "Education"),
        "Storii - audiobookshelf client": ("Media", "Audio"),
        "BetterCounter": ("Lifestyle", "Health"),
        # Taxonomy v2 (2026-10-11)
        "Google Docs": ("Productivity", "Office"),
        "MJ PDF": ("Media", "Read"),
        "EtchDroid ISO to USB Writer": ("System", "Disks"),
        "CPU Info (open-source)": ("System", "Monitor"),
        "SD Maid 2/SE": ("System", "Maintenance"),
        "PlainApp": ("System", "Internet"),
        "Activity Manager": ("Utilities", "Gadgets"),
    }
    for name, want in expected.items():
        check(f"taxonomy: {name}", m.get(name) == want,
              f"got {m.get(name)}, want {want}")

    # 3. Subcategory shape: Media/Graphics gone, Home Theater exists, etc.
    subs = Counter((a["category"], a["subcategory"]) for a in apps)
    check("Media/Graphics merged into Photos", ("Media", "Graphics") not in subs)
    check("Media/Home Theater exists", ("Media", "Home Theater") in subs)
    check("Utilities/Files moved to System", ("Utilities", "Files") not in subs)
    # Taxonomy v2 (2026-10-11): Productivity top-level, Device split three ways
    check("Productivity/Files exists", ("Productivity", "Files") in subs)
    check("System/Files gone", ("System", "Files") not in subs)
    check("Productivity/Office exists", ("Productivity", "Office") in subs)
    check("System/Device split away", ("System", "Device") not in subs)
    check("System/Disks exists", ("System", "Disks") in subs)
    check("System/Monitor exists", ("System", "Monitor") in subs)
    check("System/Maintenance exists", ("System", "Maintenance") in subs)
    for old in [("Lifestyle", "Finance"), ("Lifestyle", "Navigation"),
                ("Lifestyle", "Tasks"), ("Lifestyle", "Productivity")]:
        check(f"v2: {old[0]}/{old[1]} moved out", old not in subs)
    check("no empty subcategories", all(n > 0 for n in subs.values()))

    # 4. Alphabetical subcategory order in the emitted JS derivation.
    #    (renderSubcats sorts; verify via the live page below.)

    # 4b. Personal Use mechanism (Stage 1, 2026-10-11): a synthetic
    # personal_use record must flow through clean_record into the data,
    # the filter defs, and the built assets. Fails without the Stage 1 fix.
    import importlib.util as _ilu
    _spec = _ilu.spec_from_file_location("gen", HERE / "generate.py")
    _gen = _ilu.module_from_spec(_spec)
    _spec.loader.exec_module(_gen)
    _rec = {"name": "Test Personal App", "package": "test.personal.app",
            "status": "include", "category": "Utilities",
            "subcategory": "Gadgets", "personal_use": True,
            "platform": "android"}
    _out = _gen.clean_record(_rec)
    check("personal_use: field set", _out.get("personal_use") is True,
          str(_out.get("personal_use")))
    check("personal_use: search tag", "personal use" in _out.get("tags", []),
          str(_out.get("tags")))
    check("personal_use: filter attr def",
          ("personal_use", "Personal Use") in _gen.FILTER_ATTRS)
    check("personal_use: attr matcher",
          _gen._attr_matches_py(_out, "personal_use") is True)
    _app_js = (HERE / "assets/app.js").read_text()
    check("personal_use: tile badge in app.js",
          'personal-use' in _app_js and 'personalBadge' in _app_js)
    _css = (HERE / "assets/styles.css").read_text()
    check("personal_use: badge CSS", ".personal-use {" in _css)
    _detail_src = (HERE / "generate.py").read_text()
    check("personal_use: detail note wired",
          "personal-use-note" in _detail_src)

    # 4c. Windows download sources (Stage 2, 2026-10-11): a synthetic
    # Windows record must produce the downloads structure and render the
    # official download prominently. Fails without the Stage 2 fix.
    _wrec = {"name": "Test Windows App", "package": "test.windows.app",
             "status": "include", "category": "Utilities",
             "subcategory": "Gadgets", "platform": "windows",
             "official_url": "https://example.com/download",
             "alt_downloads": [{"label": "PortableApps",
                                "url": "https://example.com/portable"}]}
    _wout = _gen.clean_record(_wrec)
    check("windows: downloads structure",
          _wout.get("downloads", {}).get("official") == "https://example.com/download" and
          len(_wout["downloads"]["alternatives"]) == 1,
          str(_wout.get("downloads")))
    _forms = _gen.NtfyForms(None)
    _whtml = _gen.build_detail(_wout, _forms)
    check("windows: official download button",
          "Visit download site" in _whtml and
          "https://example.com/download" in _whtml)
    check("windows: alternative labeled", "PortableApps" in _whtml)
    _arec = {"name": "Test Android App", "package": "test.android.app",
             "status": "include", "category": "Utilities",
             "subcategory": "Gadgets", "platform": "android",
             "stores": {"play": "https://example.com/play"}}
    _ahtml = _gen.build_detail(_gen.clean_record(_arec), _forms)
    check("android: store badges unchanged",
          "store-badge" in _ahtml and "Download from the developer" not in _ahtml)

    # 4e. Windows download completeness (2026-10-12): every Windows
    # listing must have at least one download URL (official primary or
    # alternative). An empty "Get it" section must never ship.
    _win_apps = [a for a in apps if a.get("platform") == "windows"]
    _no_dl = [a["name"] for a in _win_apps
              if not ((a.get("downloads") or {}).get("official")) and
              not ((a.get("downloads") or {}).get("alternatives"))]
    check("windows: every listing has a download",
          not _no_dl, f"{len(_no_dl)} without: {_no_dl[:5]}")
    _no_official = [a["name"] for a in _win_apps
                    if not ((a.get("downloads") or {}).get("official"))]
    # Official URL missing is a warning, not a failure: some listings
    # legitimately use a maintained distributor as primary.
    if _no_official:
        print(f"  [note] {len(_no_official)} Windows apps without official_url "
              f"(using distributor primary): {_no_official[:5]}")
    # 4f. Sibling cross-linking (Stage 3, 2026-10-11): only the newer
    # listing names its sibling; both pages must link each other.
    # Fails without the Stage 3 fix.
    _sib_a = _gen.clean_record({"name": "Test Sib A", "package": "test.sib.a",
                                "status": "include", "category": "Utilities",
                                "subcategory": "Gadgets", "platform": "android"})
    _sib_w = _gen.clean_record({"name": "Test Sib W", "package": "test.sib.w",
                                "status": "include", "category": "Utilities",
                                "subcategory": "Gadgets", "platform": "windows",
                                "sibling": "test.sib.a"})
    _gen.resolve_siblings([_sib_a, _sib_w])
    check("sibling: forward link",
          _sib_w.get("sibling_slug") == _sib_a["slug"] and
          _sib_w.get("sibling_platform") == "android",
          str((_sib_w.get("sibling_slug"), _sib_w.get("sibling_platform"))))
    check("sibling: backlink automatic",
          _sib_a.get("sibling_slug") == _sib_w["slug"] and
          _sib_a.get("sibling_platform") == "windows")
    _sib_html = _gen.build_detail(_sib_w, _forms)
    check("sibling: detail renders link",
          "Also available on" in _sib_html and
          f'/app/{_sib_a["slug"]}.html' in _sib_html and ">Android<" in _sib_html)

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
    # NOTE: transitions are disabled in this probe. Under
    # --virtual-time-budget the CSS animation clock freezes (getAnimations
    # showed the open transitions stuck at running@0), so the row's class
    # gets added but computed height/opacity never leave the closed values.
    # Real browsers animate it fine; here we assert the end state.
    # Polls (bounded) instead of a fixed sleep so slow loads don't flake.
    t = chrome_eval("", """
      var killAnim = document.createElement('style');
      killAnim.textContent = '*{transition:none !important;animation:none !important}';
      document.head.appendChild(killAnim);
      document.querySelector('#category-chips [data-cat="Utilities"]').click();
      var tries = 0;
      var iv = setInterval(function(){
        tries++;
        var col = document.getElementById('sub-collapse');
        var h = col.getBoundingClientRect().height;
        var op = getComputedStyle(col).opacity;
        if ((h > 20 && op === "1") || tries >= 25) {
          clearInterval(iv);
          var sub = document.getElementById('subcategory-chips');
          var attr = document.getElementById('attr-pills');
          var sb = sub.getBoundingClientRect(), ab = attr.getBoundingClientRect();
          var names = [];
          sub.querySelectorAll('.chip').forEach(function(c){ names.push(c.textContent); });
          var sorted = names.slice().sort(function(a,b){
            return a.toLowerCase() < b.toLowerCase() ? -1 : 1; });
          document.title = JSON.stringify({
            h: h,
            op: op,
            gap: ab.top - sb.bottom,
            alpha: JSON.stringify(names) === JSON.stringify(sorted),
            names: names.join(','),
            polls: tries
          });
        }
      }, 200);
    """)
    d = json.loads(t)
    check("open: visible with height", d["h"] > 20 and float(d["op"]) == 1, t)
    check("open: gap to attr row >= 8px", d["gap"] >= 8, t)
    check("open: subcategories alphabetical", d["alpha"], d.get("names", t))

    # 7. Stable height across subcategory selection (the 31px->37px jump).
    # Transitions disabled: under --virtual-time-budget the open animation
    # timing is racy (h1 measured 0 / 37.3 / 38.7 across runs); assert the
    # end state like test 6 does.
    t = chrome_eval("", """
      var killAnim = document.createElement('style');
      killAnim.textContent = '*{transition:none !important;animation:none !important}';
      document.head.appendChild(killAnim);
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

    # 9. Platform filter: Windows button filters the grid and the hero
    # follows. (Windows launch, 2026-10-12.)
    t = chrome_eval("", f"""
      var winSlugs = {json.dumps([a["slug"] for a in apps if a.get("platform") == "windows"])};
      document.querySelector('.platform-seg [data-platform="windows"]').click();
      setTimeout(function(){{
        var hero = document.getElementById('hero-title').textContent;
        var tiles = document.querySelectorAll('#grid .tile');
        var vis = 0, bad = 0;
        tiles.forEach(function(el){{
          if (el.offsetParent === null) return;
          vis++;
          if (winSlugs.indexOf(el.getAttribute('data-slug')) < 0) bad++;
        }});
        document.title = JSON.stringify({{hero: hero, vis: vis, bad: bad}});
      }}, 1200);
    """)
    d = json.loads(t)
    check("platform: Windows hero copy", d["hero"] == "Actually free Windows apps.", t)
    check("platform: Windows grid non-empty", d["vis"] > 0, t)
    check("platform: Windows grid has only Windows tiles", d["bad"] == 0, t)

    # 9b. Static hero matches the default filter state (2026-10-12): the
    # shipped <h1> is the first paint, and the default platform filter is
    # All — if they disagree, every load flashes a stale headline until
    # JS rewrites it.
    _static_index = (HERE / "index.html").read_text()
    check("hero: static headline matches default filter",
          '<h1 id="hero-title">Actually free apps.</h1>' in _static_index,
          "static h1 disagrees with the default All-platform filter")

    # 10. Filter survives tile -> detail -> back: set filters, reload the
    # page (what back-button navigation does), filters are restored.
    # (Derick, 2026-10-12.)
    t = chrome_eval("", """
      if (!sessionStorage.getItem('af-test-phase')) {
        sessionStorage.setItem('af-test-phase', '1');
        document.querySelector('.platform-seg [data-platform="windows"]').click();
        setTimeout(function(){
          document.querySelector('#category-chips [data-cat="Games"]').click();
          setTimeout(function(){ location.reload(); }, 500);
        }, 600);
      } else {
        sessionStorage.removeItem('af-test-phase');
        setTimeout(function(){
          var segOn = document.querySelector('.platform-seg [data-platform="windows"]').classList.contains('on');
          var catOn = document.querySelector('#category-chips [data-cat="Games"]').classList.contains('on');
          var hero = document.getElementById('hero-title').textContent;
          var tiles = document.querySelectorAll('#grid .tile').length;
          document.title = JSON.stringify({segOn: segOn, catOn: catOn, hero: hero, tiles: tiles});
        }, 2500);
      }
    """)
    d = json.loads(t)
    check("filters: platform restored after reload", d["segOn"], t)
    check("filters: category restored after reload", d["catOn"], t)
    check("filters: hero follows restored platform", d["hero"] == "Actually free Windows apps.", t)
    check("filters: grid non-empty after restore", d["tiles"] > 0, t)

    srv.shutdown()
    print()
    if FAILURES:
        print(f"{len(FAILURES)} FAILURES: {FAILURES}")
        return 1
    print("All tests passed.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
