#!/usr/bin/env python3
"""Regression tests for the Actually Free site.

Covers the failure modes Derick has caught in review:
  1. Taxonomy placements (data/apps.json) — specific apps in expected homes.
  2. Subcategory filter order is alphabetical.
  3. Collapsed subcategory row: zero height, no overlap, gap preserved.
  4. Open subcategory row: stable height across subcategory selection.
  5. Mobile: subcategory row scrolls horizontally when chips overflow.

Usage: python3 test_site.py [--serve-port 8131] [--standards-only]
Runs generate.py first, then serves and drives headless Chrome.
--standards-only runs just the site-standards file checks (section 4g).
"""
import json
import re
import struct
import subprocess
import sys
import time
import urllib.request
from collections import Counter
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

HERE = Path(__file__).parent
# Resolve the newest installed headless shell rather than pinning a
# build number: the pinned 1243 path went stale when Playwright moved
# to 1248 and the whole browser section of this suite stopped running.
import glob as _glob
_shells = sorted(_glob.glob(str(
    Path.home() / ".cache/ms-playwright/chromium_headless_shell-*"
    / "chrome-headless-shell-linux64/chrome-headless-shell")))
CHROME = _shells[-1] if _shells else ""

FAILURES = []


def check(name, cond, detail=""):
    status = "PASS" if cond else "FAIL"
    print(f"[{status}] {name}" + (f" — {detail}" if detail and not cond else ""))
    if not cond:
        FAILURES.append(name)


def chrome_eval(url, js, width=1280, height=800, vtb=15000, ua=None):
    """Load url in headless Chrome, run js after load, return document.title."""
    probe = f"""<script>setTimeout(function(){{try{{{js}}}catch(e){{
        document.title='ERROR:'+e.message;}}}},1800);</script></body>"""
    html = (HERE / "index.html").read_text().replace("</body>", probe)
    tmp = HERE / "_test_probe.html"
    tmp.write_text(html)
    try:
        args = [CHROME, "--no-sandbox", "--no-proxy-server", "--disable-gpu",
                f"--virtual-time-budget={vtb}", "--dump-dom",
                f"--window-size={width},{height}"]
        if ua:
            args.append(f"--user-agent={ua}")
        args.append(f"http://127.0.0.1:{PORT}/_test_probe.html")
        out = subprocess.run(args, capture_output=True, text=True, timeout=90)
        for line in out.stdout.splitlines():
            if "<title>" in line:
                s = line.split("<title>", 1)[1]
                return s.split("</title>", 1)[0]
    finally:
        tmp.unlink(missing_ok=True)
    return "ERROR:no-title"


def _page_head(path):
    return path.read_text(encoding="utf-8").split("</head>", 1)[0]


def _png_size(path):
    data = path.read_bytes()
    if data[:8] != b"\x89PNG\r\n\x1a\n":
        return None
    return struct.unpack(">II", data[16:24])


def standards_checks():
    """Section 4g: the fleet site standards (agents-policy
    docs/site-standards.md), checked against the generated files.
    A live check after deploy proves the same items on the real site;
    these keep the gaps from reopening in the build."""
    SITE = "https://free.certifiable.media"
    pages = {"index.html": SITE + "/",
             "suggest.html": SITE + "/suggest",
             "what-is-free.html": SITE + "/what-is-free"}
    for f in sorted((HERE / "app").glob("*.html")):
        pages[f"app/{f.name}"] = SITE + "/app/" + f.name[:-5]

    # Icons: a real favicon.ico, a true 32px PNG, the declared set.
    ico = HERE / "favicon.ico"
    check("standards: favicon.ico exists", ico.exists())
    if ico.exists():
        check("standards: favicon.ico is an icon file",
              ico.read_bytes()[:4] == b"\x00\x00\x01\x00")
    png32 = HERE / "assets" / "icon-32.png"
    check("standards: icon-32.png exists", png32.exists())
    if png32.exists():
        check("standards: icon-32.png is 32x32",
              _png_size(png32) == (32, 32), str(_png_size(png32)))
    home_head = _page_head(HERE / "index.html")
    for snippet, label in [
            ('sizes="32x32" href="/assets/icon-32.png"', "32"),
            ('sizes="192x192" href="/assets/icon-192.png"', "192"),
            ('sizes="512x512" href="/assets/icon-512.png"', "512")]:
        check(f"standards: head declares the {label}px PNG icon",
              snippet in home_head)
    check("standards: head declares apple-touch-icon",
          'rel="apple-touch-icon"' in home_head)

    # Canonicals, og:url, and one title + description per page.
    bad_canon, bad_ogurl, dupe_t, dupe_d = [], [], [], []
    titles, descs = {}, {}
    for rel, want in list(pages.items()) + [("404.html", None)]:
        head_html = _page_head(HERE / rel)
        if want is not None:
            m = re.search(r'<link rel="canonical" href="([^"]*)"',
                          head_html)
            if not m or m.group(1) != want:
                bad_canon.append(rel)
            m = re.search(r'<meta property="og:url" content="([^"]*)"',
                          head_html)
            if not m or m.group(1) != want:
                bad_ogurl.append(rel)
        t = re.search(r"<title>(.*?)</title>", head_html, re.S)
        d = re.search(r'<meta name="description" content="([^"]*)"',
                      head_html)
        if t:
            if t.group(1) in titles:
                dupe_t.append(rel)
            titles[t.group(1)] = rel
        if d:
            if d.group(1) in descs:
                dupe_d.append(rel)
            descs[d.group(1)] = rel
    check("standards: every page names its own canonical",
          not bad_canon, str(bad_canon[:5]))
    check("standards: og:url names the page's own address",
          not bad_ogurl, str(bad_ogurl[:5]))
    check("standards: no two pages share a title",
          not dupe_t, str(dupe_t[:5]))
    check("standards: no two pages share a description",
          not dupe_d, str(dupe_d[:5]))

    # Sitemap: each page once, at its canonical address, with lastmod.
    sm = (HERE / "sitemap.xml").read_text(encoding="utf-8")
    locs = re.findall(r"<loc>([^<]+)</loc>", sm)
    check("standards: sitemap lists each page once, at its canonical",
          sorted(locs) == sorted(pages.values()),
          f"{len(locs)} entries vs {len(pages)} pages")
    check("standards: sitemap carries no .html addresses",
          not any(u.endswith(".html") for u in locs))
    mods = re.findall(r"<lastmod>([^<]+)</lastmod>", sm)
    check("standards: every sitemap entry carries a lastmod",
          len(mods) == len(locs), f"{len(mods)} vs {len(locs)}")

    # Splash: declared size matches the file; og:locale present.
    size = _png_size(HERE / "assets" / "og-share.png")
    bad_dims, bad_locale = [], []
    sample = ["index.html", "suggest.html", "what-is-free.html",
              "app/" + sorted(p.name for p in
                              (HERE / "app").glob("*.html"))[0]]
    for rel in sample:
        head_html = _page_head(HERE / rel)
        mw = re.search(r'og:image:width" content="(\d+)"', head_html)
        mh = re.search(r'og:image:height" content="(\d+)"', head_html)
        if (not mw or not mh or size is None
                or (int(mw.group(1)), int(mh.group(1))) != size):
            bad_dims.append(rel)
        if 'og:locale" content="en_CA"' not in head_html:
            bad_locale.append(rel)
    check("standards: og:image declarations match the splash file",
          not bad_dims, str(bad_dims))
    check("standards: og:locale names en_CA", not bad_locale,
          str(bad_locale))

    # The 404 page and the Bing verification file exist.
    f404 = HERE / "404.html"
    check("standards: 404.html exists", f404.exists())
    if f404.exists():
        body = f404.read_text(encoding="utf-8")
        check("standards: 404 page says the page is not found",
              "page not found" in body.lower())
        check("standards: 404 page links back to the directory",
              'href="/"' in body)
        check("standards: 404 page carries header and footer",
              "site-header" in body and "site-footer" in body)
    bing = HERE / "BingSiteAuth.xml"
    check("standards: BingSiteAuth.xml exists with a user entry",
          bing.exists() and "<user>" in bing.read_text(encoding="utf-8"))


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
    _forms = _gen.FeedbackForms()
    _whtml = _gen.build_detail(_wout, _forms)
    check("windows: official download button",
          "Download from the developer" in _whtml and
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

    # 4g. Site standards (fleet standard, 2026-10-28).
    standards_checks()
    if "--standards-only" in sys.argv:
        print()
        if FAILURES:
            print(f"{len(FAILURES)} FAILURES: {FAILURES}")
            return 1
        print("All standards checks passed.")
        return 0

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

    # 11. Arrival auto-detect (Derick, 2026-10-16): a fresh visit with no
    # saved filters preselects the visitor's own platform, headline
    # included; one tap on All clears it; platforms with no listings and
    # unknown platforms land on All. Each probe clears saved filters and
    # reloads once so the arrival is genuinely fresh.
    UA_ANDROID = ("Mozilla/5.0 (Linux; Android 14; Pixel 8) "
                  "AppleWebKit/537.36 (KHTML, like Gecko) "
                  "Chrome/126.0.0.0 Mobile Safari/537.36")
    UA_WINDOWS = ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                  "AppleWebKit/537.36 (KHTML, like Gecko) "
                  "Chrome/126.0.0.0 Safari/537.36")
    UA_LINUX = ("Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 "
                "(KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36")
    UA_IPHONE = ("Mozilla/5.0 (iPhone; CPU iPhone OS 17_0 like Mac OS X) "
                 "AppleWebKit/605.1.15 (KHTML, like Gecko) "
                 "Version/17.0 Mobile/15E148 Safari/604.1")

    def arrival_probe(phase_key, measure_js):
        return f"""
      if (!sessionStorage.getItem('{phase_key}')) {{
        sessionStorage.setItem('{phase_key}', '1');
        sessionStorage.removeItem('af-filters');
        location.reload();
      }} else {{
        sessionStorage.removeItem('{phase_key}');
        setTimeout(function(){{ {measure_js} }}, 1600);
      }}
    """

    # 11a. Android arrival: Android preselected, hero follows, grid is
    # Android-only, and tapping All restores the full grid.
    t = chrome_eval("", arrival_probe("af-test-arrive-android", f"""
          var andSlugs = {json.dumps([a["slug"] for a in apps if a.get("platform") == "android"])};
          var segOn = document.querySelector('.platform-seg [data-platform="android"]').classList.contains('on');
          var hero = document.getElementById('hero-title').textContent;
          var tiles = document.querySelectorAll('#grid .tile');
          var bad = 0;
          tiles.forEach(function(el){{ if (andSlugs.indexOf(el.getAttribute('data-slug')) < 0) bad++; }});
          var visBefore = tiles.length;
          document.querySelector('.platform-seg [data-platform=""]').click();
          setTimeout(function(){{
            var allSegOn = document.querySelector('.platform-seg [data-platform=""]').classList.contains('on');
            var total = document.querySelectorAll('#grid .tile').length;
            document.title = JSON.stringify({{segOn: segOn, hero: hero, visBefore: visBefore,
              bad: bad, allSegOn: allSegOn, totalAfterClear: total}});
          }}, 900);
    """), ua=UA_ANDROID)
    d = json.loads(t)
    check("arrive: Android segment preselected", d["segOn"], t)
    check("arrive: Android hero copy", d["hero"] == "Actually free Android apps.", t)
    check("arrive: Android grid non-empty", d["visBefore"] > 0, t)
    check("arrive: Android grid has only Android tiles", d["bad"] == 0, t)
    check("arrive: one tap on All clears", d["allSegOn"] and d["totalAfterClear"] == len(apps), t)

    # 11b. Windows arrival: Windows preselected, hero follows.
    t = chrome_eval("", arrival_probe("af-test-arrive-windows", """
          var segOn = document.querySelector('.platform-seg [data-platform="windows"]').classList.contains('on');
          var hero = document.getElementById('hero-title').textContent;
          document.title = JSON.stringify({segOn: segOn, hero: hero});
    """), ua=UA_WINDOWS)
    d = json.loads(t)
    check("arrive: Windows segment preselected", d["segOn"], t)
    check("arrive: Windows hero copy", d["hero"] == "Actually free Windows apps.", t)

    # 11c. Unknown platform (Linux desktop): no filter applied.
    t = chrome_eval("", arrival_probe("af-test-arrive-linux", """
          var allOn = document.querySelector('.platform-seg [data-platform=""]').classList.contains('on');
          var hero = document.getElementById('hero-title').textContent;
          var total = document.querySelectorAll('#grid .tile').length;
          document.title = JSON.stringify({allOn: allOn, hero: hero, total: total});
    """), ua=UA_LINUX)
    d = json.loads(t)
    check("arrive: unknown platform lands on All", d["allOn"], t)
    check("arrive: unknown platform hero copy", d["hero"] == "Actually free apps.", t)
    check("arrive: unknown platform sees full grid", d["total"] == len(apps), t)

    # 11d. iPhone arrival: iOS listings exist (since 2026-10-16), so the
    # iOS segment is preselected and the hero follows.
    t = chrome_eval("", arrival_probe("af-test-arrive-iphone", """
          var segOn = document.querySelector('.platform-seg [data-platform="ios"]').classList.contains('on');
          var hero = document.getElementById('hero-title').textContent;
          var total = document.querySelectorAll('#grid .tile').length;
          document.title = JSON.stringify({segOn: segOn, hero: hero, total: total});
    """), ua=UA_IPHONE)
    d = json.loads(t)
    check("arrive: iPhone segment preselected", d["segOn"], t)
    check("arrive: iPhone hero copy", d["hero"] == "Actually free iOS apps.", t)
    check("arrive: iPhone grid non-empty", d["total"] > 0, t)

    # 12. Saved state vs auto-detect (Derick, 2026-10-16): he visited on
    # his Android phone, saw the Android view, then it reverted to All.
    # Cause: the pre-detection build had already saved a filter state
    # with platform "" into the tab session, and the new build treated
    # that saved default as a deliberate choice, skipping detection.
    # Rule: detection applies unless the visitor has actually chosen a
    # platform (platformChosen). A saved "" with no choice behind it is
    # not a choice. Each probe seeds af-filters, reloads, then measures.
    def seeded_probe(phase_key, saved, measure_js):
        return f"""
      if (!sessionStorage.getItem('{phase_key}')) {{
        sessionStorage.setItem('{phase_key}', '1');
        sessionStorage.setItem('af-filters', {json.dumps(json.dumps(saved))});
        location.reload();
      }} else {{
        sessionStorage.removeItem('{phase_key}');
        setTimeout(function(){{ {measure_js} }}, 1600);
      }}
    """
    SAVED_DEFAULT = {"query": "", "cat": "", "subcat": "", "platform": "",
                     "attrs": {}, "stores": {}, "sort": "name"}

    # 12a. Saved default (no choice ever made) under an Android UA:
    # detection must still apply.
    t = chrome_eval("", seeded_probe("af-test-seed-default", SAVED_DEFAULT, """
          var segOn = document.querySelector('.platform-seg [data-platform="android"]').classList.contains('on');
          var hero = document.getElementById('hero-title').textContent;
          document.title = JSON.stringify({segOn: segOn, hero: hero});
    """), ua=UA_ANDROID)
    d = json.loads(t)
    check("saved: untouched default does not block detection", d["segOn"], t)
    check("saved: hero follows detection over default", d["hero"] == "Actually free Android apps.", t)

    # 12b. Deliberate All (platformChosen) under an Android UA: the
    # visitor's tap wins, detection stays out.
    t = chrome_eval("", seeded_probe("af-test-seed-all",
                    dict(SAVED_DEFAULT, platformChosen=True), """
          var allOn = document.querySelector('.platform-seg [data-platform=""]').classList.contains('on');
          var hero = document.getElementById('hero-title').textContent;
          document.title = JSON.stringify({allOn: allOn, hero: hero});
    """), ua=UA_ANDROID)
    d = json.loads(t)
    check("saved: deliberate All beats detection", d["allOn"], t)
    check("saved: deliberate All hero copy", d["hero"] == "Actually free apps.", t)

    # 12c. Deliberate Windows under an Android UA: explicit choice wins.
    t = chrome_eval("", seeded_probe("af-test-seed-windows",
                    dict(SAVED_DEFAULT, platform="windows", platformChosen=True), """
          var segOn = document.querySelector('.platform-seg [data-platform="windows"]').classList.contains('on');
          var hero = document.getElementById('hero-title').textContent;
          document.title = JSON.stringify({segOn: segOn, hero: hero});
    """), ua=UA_ANDROID)
    d = json.loads(t)
    check("saved: deliberate Windows beats Android detection", d["segOn"], t)
    check("saved: deliberate Windows hero copy", d["hero"] == "Actually free Windows apps.", t)

    srv.shutdown()
    print()
    if FAILURES:
        print(f"{len(FAILURES)} FAILURES: {FAILURES}")
        return 1
    print("All tests passed.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
