#!/usr/bin/env python3
"""Actually Free — static site generator.

Reads ~/workspace/certifiable-apps/apps-seed.json, keeps the verified
listings (status=include + status=per-badge), adds QR Cards, and emits a
fully static site deployable as-is to Cloudflare Pages.

Regenerate everything with:  python3 generate.py
"""
import html
import json
import os
import re
import shutil

HERE = os.path.dirname(os.path.abspath(__file__))
SEED = os.path.expanduser("~/workspace/certifiable-apps/apps-seed.json")
SITE_URL = "https://free.certifiable.media"
TAGLINE = "Find the free apps they don't want you to see."
EMPTY_STATE = "Well, actually\u2026 we don't list anything matching that."
EMPTY_STATE_GEEK = ("Well, actually\u2026 your query returned 0 rows. "
                    "Have you tried turning it off and on again?")
PROMISES = ["No ads", "No in-app purchases", "No subscriptions"]
PER_BADGE_NOTE = ("The Play Store version of this app carries ads or in-app "
                  "purchases, so we only list the clean build.")

QR_CARDS = {
    "name": "QR Cards",
    "package": "derickca/qr-cards",
    "category": "Utilities",
    "subcategory": "QR codes",
    "stores": {"play": None, "fdroid": False,
               "github": "https://github.com/derickca/qr-cards"},
    "verification": {"play_labels_clean": None, "play_rating": None,
                     "fdroid_antifeatures": [], "method": "curated"},
    "notes": "",
    "status": "include",
    "made_by_us": True,
    "description": ("A free offline Android app that keeps QR codes for the "
                    "people, places, and things you actually need: vCards, "
                    "guest Wi-Fi, saved addresses. Searchable library with "
                    "color labels, present mode (full-screen QR at max "
                    "brightness), a dynamic editor for 9 card types, per-card "
                    "launcher shortcuts, and PNG/SVG export. No ads, no "
                    "accounts, fully offline."),
    "attrs": {"open_source": True, "offline": True, "no_account": True},
}

# Hand-written one-liners where the research notes don't yield a clean
# description. Kept plain and factual.
DESC_OVERRIDES = {
    "Open Camera": "Open-source camera app with manual controls.",
    "Audio Recorder": "Straightforward audio recorder.",
    "VLC": "The classic free media player \u2014 plays just about everything.",
    "Nova Video Player": "Video player with network streaming support.",
    "Next Player": "A clean, simple video player.",
    "Auxio": "Local music player with a clean interface.",
    "Vinyl Music Player": "Local music player.",
    "Vanilla Music": "Simple local music player.",
    "Phonograph Plus": "Material-design local music player (a Phonograph fork).",
    "AntennaPod": "Full-featured podcast player.",
    "Voice Audiobook Player": "Audiobook player with bookmarks and a sleep timer.",
    "NewPipe": "Lightweight YouTube app \u2014 no account, no ads.",
    "dotGallery (ReFra)": "Simple photo gallery.",
    "Feeder": "RSS feed reader.",
    "ReadYou": "RSS reader with a modern interface.",
    "KOReader": "Document reader for e-books and PDFs.",
    "ReadEra": "E-book and document reader.",
    "LxReader (CoolReader NG)": "E-book reader (a CoolReader NG fork).",
    "Pocket Paint": "Draw and edit images.",
    "Fossify Voice Recorder": "Voice recorder \u2014 offline, local storage.",
    "Fossify SMS Messenger": "Text messaging, minus the noise.",
    "Fossify Phone": "Dialer and phone app.",
    "Fossify Contacts": "Contacts manager.",
    "Koler": "Simple phone dialer.",
    "FairEmail": "Privacy-focused email client. The F-Droid build is fully unlocked.",
    "Aegis Authenticator": "Two-factor authenticator (TOTP/HOTP).",
    "KeePassDX": "Password manager (KeePass-compatible).",
    "FlorisBoard": "Privacy-focused keyboard.",
    "OpenBoard": "Open-source keyboard based on AOSP.",
    "Lawnchair": "Customizable Pixel-style launcher.",
    "Firefox": "The independent web browser.",
    "AdAway": "System-wide ad blocker (root or local VPN).",
    "NetGuard": "Firewall that blocks internet access per app. The F-Droid build is fully unlocked.",
    "Shelter": "Isolates apps using Android's work profile.",
    "Syncthing-Fork": "Decentralized file sync between your devices.",
    "Nextcloud": "File sync client (connects to a Nextcloud server).",
    "Termux": "Terminal emulator and Linux environment.",
    "Pedometer (PFA)": "Counts your steps in the background. Customize daily goals.",
    "Flashlight Tiramisu": "Flashlight with smoothly adjustable brightness.",
    "TrackerControl": "Monitors and blocks per-app trackers.",
    "Amaze File Manager": "An open-source file manager following the Material Design guidelines.",
}


def esc(s):
    return html.escape(str(s or ""), quote=True)


def slugify(package):
    return re.sub(r"[^a-z0-9]+", "-", package.lower()).strip("-")


def tidy(s, cap=190):
    s = re.sub(r"\s+", " ", s).strip()
    if len(s) > cap:
        cut = s.rfind(". ", 0, cap)
        s = s[:cut + 1] if cut > 60 else s[:cap - 1] + "\u2026"
    return s


def extract_description(rec):
    """Pull a plain one-line description out of the research notes."""
    name = rec["name"]
    if name in DESC_OVERRIDES:
        return DESC_OVERRIDES[name]
    notes = (rec.get("notes") or "").replace("\n", " ")
    m = re.search(r"F-Droid summary:\s*(.+?)(?:\s*License:|$)", notes)
    if m and len(m.group(1).strip()) > 12:
        return tidy(m.group(1))
    s = re.sub(r"^(VERDICT:[^\n]*?[\u2014\u2013\-]\s*|DISQUALIFIED on Play:[^\n]*?[\u2014\u2013\-]\s*"
               r"|FLAG:[^\n]*?[\u2014\u2013\-]\s*)", "", notes).strip()
    for sent in re.split(r"(?<=[.!?])\s+", s):
        low = sent.lower()
        if any(k in low for k in ["verdict", "disqualified", "labels clean",
                                  "labels verified", "anti-features",
                                  "f-droid clean", "play listing", "play build"]):
            continue
        if len(sent) > 15:
            return tidy(sent)
    return tidy(s[:200])


def derive_attrs(rec):
    """Conservative transparency attributes — only from explicit evidence."""
    notes = (rec.get("notes") or "").lower()
    stores = rec.get("stores") or {}
    attrs = {}
    if stores.get("fdroid"):
        attrs["open_source"] = True  # F-Droid main repo builds from source
    if re.search(r"offline|fully offline", notes):
        attrs["offline"] = True
    if re.search(r"no accounts?", notes):
        attrs["no_account"] = True
    return attrs


def clean_record(rec):
    stores = rec.get("stores") or {}
    ver = rec.get("verification") or {}
    per_badge = rec.get("status") == "per-badge"
    out_stores = {
        # Per-badge rule: strip the Play URL entirely for disqualified builds.
        "play": None if per_badge else (stores.get("play") or None),
        "fdroid": bool(stores.get("fdroid")),
        "github": stores.get("github") or None,
    }
    return {
        "name": rec["name"],
        "package": rec["package"],
        "slug": slugify(rec["package"]),
        "category": rec.get("category") or "Utilities",
        "subcategory": rec.get("subcategory") or "",
        "description": rec.get("description") or extract_description(rec),
        "stores": out_stores,
        "rating": ver.get("play_rating"),
        "attrs": rec.get("attrs") or derive_attrs(rec),
        "made_by_us": bool(rec.get("made_by_us")),
        "per_badge": per_badge,
    }


def load_corpus():
    with open(SEED, encoding="utf-8") as f:
        seed = json.load(f)
    kept = [clean_record(r) for r in seed
            if r.get("status") in ("include", "per-badge")]
    kept.append(clean_record(QR_CARDS))
    kept.sort(key=lambda a: a["name"].lower())
    return kept

# ---------------------------------------------------------------------------
# Shared HTML fragments
# ---------------------------------------------------------------------------

def head(title, description, og_path="", og_image=""):
    """<head> with SEO/OG basics. og_path like 'app/foo-bar.html' or ''."""
    url = SITE_URL + ("/" + og_path if og_path else "/")
    img = (SITE_URL + "/assets/" + og_image) if og_image else SITE_URL + "/assets/mascot-cartoon.webp"
    return f"""<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{esc(title)}</title>
<meta name="description" content="{esc(description)}">
<meta property="og:title" content="{esc(title)}">
<meta property="og:description" content="{esc(description)}">
<meta property="og:url" content="{esc(url)}">
<meta property="og:type" content="website">
<meta property="og:site_name" content="Actually Free">
<meta property="og:image" content="{esc(img)}">
<link rel="icon" href="/assets/mascot-cartoon.webp">
<link rel="stylesheet" href="/assets/styles.css">
</head>"""


def site_header(active="directory"):
    """Header shared by index + detail pages. Mode/theme switchers included."""
    dir_cls = ' class="active"' if active == "directory" else ""
    qr_cls = ' class="active"' if active == "qrcards" else ""
    return f"""<header class="site-header">
  <div class="header-inner">
    <a class="brand" href="/index.html">
      <img id="mascot" src="/assets/mascot-cartoon.webp" alt="Actually Guy, the Actually Free mascot" width="56" height="56">
      <span class="brand-text"><strong>Actually Free</strong><em>{esc(TAGLINE)}</em></span>
    </a>
    <nav class="tabs" aria-label="Site sections">
      <a href="/index.html"{dir_cls}>Directory</a>
      <a href="/app/derickca-qr-cards.html"{qr_cls}>QR Cards</a>
    </nav>
    <div class="switchers">
      <div class="switcher" role="group" aria-label="Site mode">
        <button data-mode="playful" class="on" title="Playful mode">Playful</button><button data-mode="geek" title="Geek mode: full 2000s internet">Geek</button>
      </div>
      <div class="switcher" role="group" aria-label="Color theme">
        <button data-theme="default" class="on" title="Follow system">Default</button><button data-theme="light" title="Light">Light</button><button data-theme="dark" title="Dark">Dark</button>
      </div>
    </div>
  </div>
  <div class="geek-badge" aria-hidden="true">best viewed at 800&times;600</div>
</header>"""


def promise_strip():
    items = " &middot; ".join(f"<span class='lock'>\u2713 {esc(p)}</span>" for p in PROMISES)
    return f"""<section class="promise-strip" aria-label="Our promise">
  <span class="promise-label">Every app here:</span> {items}
</section>"""


def site_footer():
    return f"""<footer class="site-footer">
  <div class="footer-inner">
    <p class="about"><strong>Actually Free</strong> is a hand-curated directory of Android apps that are
    actually free. Every app is checked before listing: no ads, no in-app purchases, no subscriptions.
    If an app breaks the promise, report it and we'll take a look.</p>
    <p class="footer-links">
      <a id="suggest-link" href="#">Suggest an app</a> &middot;
      <a href="/index.html">Directory</a> &middot;
      <a href="/app/derickca-qr-cards.html">QR Cards</a>
    </p>
    <p class="geek-webring" aria-hidden="true"><span>&larr; prev</span> &middot; <button id="random-app" type="button">random</button> &middot; <span>next &rarr;</span></p>
    <p class="construction" aria-hidden="true"><span>UNDER CONSTRUCTION</span></p>
    <p class="count-line">We count clicks, not people.</p>
  </div>
</footer>
<script src="/assets/config.js"></script>
<script src="/assets/app.js"></script>"""


# ---------------------------------------------------------------------------
# index.html — the directory shell (tiles render client-side from apps.json)
# ---------------------------------------------------------------------------

def build_index(apps, categories):
    chips = "\n".join(
        f'      <button class="chip" data-cat="{esc(c)}">{esc(c)}</button>'
        for c in categories)
    return f"""<!DOCTYPE html>
<html lang="en" data-mode="playful" data-theme="default">
{head("Actually Free \u2014 " + TAGLINE,
      "A hand-curated directory of Android apps that are actually free: no ads, no in-app purchases, no subscriptions. " + TAGLINE)}
<body>
{site_header("directory")}
<main class="directory">
  <section class="hero">
    <h1>Actually free Android apps.</h1>
    <p class="tagline"><span class="marquee-text">{esc(TAGLINE)}</span></p>
  </section>
  {promise_strip()}
  <section class="controls" aria-label="Search and filter">
    <input id="search" type="search" placeholder="Search apps, e.g. &quot;flashlight&quot;\u2026"
           aria-label="Search apps" autocomplete="off">
    <div class="filter-row" id="category-chips" role="group" aria-label="Filter by category">
      <button class="chip on" data-cat="">All</button>
{chips}
    </div>
    <div class="filter-row" role="group" aria-label="Narrow it down">
      <button class="pill" data-attr="open_source">Open source</button>
      <button class="pill" data-attr="offline">Works offline</button>
      <button class="pill" data-attr="no_account">No account needed</button>
      <button class="pill" data-attr="made_by_us">Made by us</button>
    </div>
    <div class="filter-row sort-row">
      <label>Sort:
        <select id="sort">
          <option value="name">Name A\u2013Z</option>
          <option value="rating">Highest rated</option>
        </select>
      </label>
      <span id="result-count" class="result-count" aria-live="polite"></span>
    </div>
  </section>
  <section id="grid" class="grid" aria-label="Apps"></section>
  <p id="empty-state" class="empty-state" hidden></p>
</main>
{site_footer()}
</body>
</html>
"""

# ---------------------------------------------------------------------------
# Detail pages — one real static HTML page per app (SEO)
# ---------------------------------------------------------------------------

STORE_LABELS = [("play", "Play"), ("fdroid", "F-Droid"), ("github", "GitHub")]


def fdroid_url(package):
    return f"https://f-droid.org/en/packages/{package}/"


def store_badges(app, big=False):
    parts = []
    for key, label in STORE_LABELS:
        if key == "fdroid":
            url = fdroid_url(app["package"]) if app["stores"]["fdroid"] else None
        else:
            url = app["stores"][key]
        if url:
            cls = "store-badge big" if big else "store-badge"
            parts.append(
                f'<a class="{cls}" data-store="{key}" data-app="{esc(app["slug"])}" '
                f'href="{esc(url)}" rel="noopener">{esc(label)}</a>')
    return "\n".join(parts)


ATTR_LABELS = {"open_source": "Open source",
               "offline": "Works offline",
               "no_account": "No account needed"}


def transparency_pills(app):
    pills = [f'<span class="t-pill">\u2713 {esc(ATTR_LABELS[k])}</span>'
             for k in ("open_source", "offline", "no_account")
             if app["attrs"].get(k)]
    return "\n".join(pills)


def build_detail(app):
    title = f'{app["name"]} \u2014 actually free, no ads | Actually Free'
    desc = tidy(app["description"], 160)
    rating = (f'<p class="rating">\u2605 {esc(app["rating"])} on Google Play</p>'
              if app.get("rating") else "")
    ribbon = '<span class="made-by-us">Made by us</span>' if app["made_by_us"] else ""
    per_badge = (f'<p class="per-badge-note">{esc(PER_BADGE_NOTE)}</p>'
                 if app["per_badge"] else "")
    checks = "\n".join(
        f'<li><span class="lock">\u2713</span> {esc(p)}</li>' for p in PROMISES)
    pills = transparency_pills(app)
    pills_block = (f'<div class="transparency"><h2>Transparency</h2><div class="t-pills">\n{pills}\n</div></div>'
                   if pills else "")
    icon = f"https://f-droid.org/repo/{esc(app['package'])}/en-US/icon.png"
    letter = esc(app["name"][0].upper())
    return f"""<!DOCTYPE html>
<html lang="en" data-mode="playful" data-theme="default">
{head(title, desc, f"app/{app['slug']}.html")}
<body>
{site_header("qrcards" if app["made_by_us"] else "directory")}
<main class="detail">
  <p><a class="back" href="/index.html">&larr; Back to the directory</a></p>
  <article class="detail-card">
    <div class="detail-head">
      <span class="icon-wrap large">
        <img src="{icon}" alt="" loading="lazy"
             onerror="this.style.display='none';this.nextElementSibling.style.display='flex'">
        <span class="letter-tile" style="display:none">{letter}</span>
      </span>
      <div>
        <h1>{esc(app["name"])} {ribbon}</h1>
        <p class="cat">{esc(app["category"])}{" \u00b7 " + esc(app["subcategory"]) if app["subcategory"] else ""}</p>
        {rating}
      </div>
    </div>
    <p class="desc">{esc(app["description"])}</p>
    <h2>Get it</h2>
    <div class="get-it">
{store_badges(app, big=True)}
    </div>
    {per_badge}
    <h2>The promise</h2>
    <ul class="promise-checks">
{checks}
    </ul>
    {pills_block}
    <h2>Something wrong?</h2>
    <p class="feedback-note">Reports go to a human review queue. No timeline promised
    \u2014 this is a small pilot, but every report gets read.</p>
    <div class="feedback-row">
      <button data-feedback="doesnt-work" data-app="{esc(app['slug'])}">Doesn't work</button>
      <button data-feedback="broke-promise" data-app="{esc(app['slug'])}">Broke a promise</button>
      <button data-feedback="correction" data-app="{esc(app['slug'])}">Suggest a correction</button>
    </div>
  </article>
</main>
{site_footer()}
</body>
</html>
"""


def build_sitemap(apps):
    urls = [f"  <url><loc>{SITE_URL}/</loc></url>"]
    for app in apps:
        urls.append(f"  <url><loc>{SITE_URL}/app/{app['slug']}.html</loc></url>")
    return ("<?xml version=\"1.0\" encoding=\"UTF-8\"?>\n"
            "<urlset xmlns=\"http://www.sitemaps.org/schemas/sitemap/0.9\">\n"
            + "\n".join(urls) + "\n</urlset>\n")


ROBOTS = ("User-agent: *\nAllow: /\n"
          f"Sitemap: {SITE_URL}/sitemap.xml\n")

CSS_CONTENT = r"""
/* ================= Actually Free =================
   Playful skin (default) + Geek 2000s skin, with an orthogonal
   Default/Light/Dark theme layer. Mode = skin, theme = palette. */

:root, :root[data-theme="light"] {
  --bg: #f2f6fb;
  --ink: #1d2836;
  --muted: #5d6f83;
  --card: #ffffff;
  --card-edge: #dbe5f1;
  --accent: #2f7fe0;
  --accent-soft: #e3eefc;
  --good: #189a52;
  --good-soft: #e2f5e9;
  --header-bg: #ffffff;
  --chip-bg: #e7eef7;
  --chip-on: #1d2836;
  --input-bg: #ffffff;
  --shadow: 0 2px 12px rgba(29, 40, 54, 0.09);
  --radius: 16px;
  --font: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif;
}
@media (prefers-color-scheme: dark) {
  :root:not([data-theme="light"]) {
    --bg: #10161f;
    --ink: #e8eef5;
    --muted: #93a3b8;
    --card: #1a2330;
    --card-edge: #2c3a4e;
    --accent: #5ea0f0;
    --accent-soft: #22344d;
    --good: #4cc47c;
    --good-soft: #173a26;
    --header-bg: #161e2a;
    --chip-bg: #243042;
    --chip-on: #e8eef5;
    --input-bg: #1a2330;
    --shadow: 0 2px 12px rgba(0, 0, 0, 0.4);
  }
}
:root[data-theme="dark"] {
  --bg: #10161f;
  --ink: #e8eef5;
  --muted: #93a3b8;
  --card: #1a2330;
  --card-edge: #2c3a4e;
  --accent: #5ea0f0;
  --accent-soft: #22344d;
  --good: #4cc47c;
  --good-soft: #173a26;
  --header-bg: #161e2a;
  --chip-bg: #243042;
  --chip-on: #e8eef5;
  --input-bg: #1a2330;
  --shadow: 0 2px 12px rgba(0, 0, 0, 0.4);
}

* { box-sizing: border-box; }
body {
  margin: 0;
  font-family: var(--font);
  background: var(--bg);
  color: var(--ink);
  line-height: 1.5;
  -webkit-text-size-adjust: 100%;
}
a { color: var(--accent); }

/* ---------- header ---------- */
.site-header {
  background: var(--header-bg);
  border-bottom: 1px solid var(--card-edge);
  position: sticky;
  top: 0;
  z-index: 50;
}
.header-inner {
  max-width: 1100px;
  margin: 0 auto;
  padding: 10px 16px;
  display: flex;
  align-items: center;
  gap: 16px;
  flex-wrap: wrap;
}
.brand { display: flex; align-items: center; gap: 12px; text-decoration: none; color: var(--ink); }
.brand img { border-radius: 12px; box-shadow: var(--shadow); }
.brand-text { display: flex; flex-direction: column; }
.brand-text strong { font-size: 1.25rem; letter-spacing: 0.2px; }
.brand-text em { font-style: normal; font-size: 0.8rem; color: var(--muted); }
.tabs { display: flex; gap: 4px; margin-left: auto; }
.tabs a {
  padding: 8px 14px;
  border-radius: 999px;
  text-decoration: none;
  color: var(--muted);
  font-weight: 600;
}
.tabs a.active, .tabs a:hover { background: var(--accent-soft); color: var(--ink); }
.switchers { display: flex; gap: 8px; }
.switcher { display: flex; border: 1px solid var(--card-edge); border-radius: 999px; overflow: hidden; }
.switcher button {
  border: 0;
  background: transparent;
  color: var(--muted);
  font: inherit;
  font-size: 0.78rem;
  font-weight: 600;
  padding: 7px 11px;
  cursor: pointer;
}
.switcher button.on { background: var(--ink); color: var(--bg); }
.geek-badge {
  display: none;
  text-align: center;
  font-size: 0.72rem;
  color: var(--muted);
  padding: 2px 0 6px;
}

/* ---------- layout ---------- */
main { max-width: 1100px; margin: 0 auto; padding: 20px 16px 48px; }
.hero h1 { font-size: clamp(1.6rem, 4vw, 2.4rem); margin: 0.4em 0 0.1em; }
.tagline { color: var(--muted); font-size: 1.05rem; margin: 0 0 1em; overflow: hidden; }

/* ---------- promise strip ---------- */
.promise-strip {
  background: var(--good-soft);
  border: 1px solid var(--card-edge);
  border-radius: var(--radius);
  padding: 10px 16px;
  margin: 0 0 18px;
  font-size: 0.95rem;
}
.promise-label { font-weight: 700; margin-right: 8px; }
.lock { color: var(--good); font-weight: 700; white-space: nowrap; }

/* ---------- controls ---------- */
.controls { margin-bottom: 20px; }
#search {
  width: 100%;
  font: inherit;
  font-size: 1.05rem;
  padding: 12px 16px;
  border: 1px solid var(--card-edge);
  border-radius: 999px;
  background: var(--input-bg);
  color: var(--ink);
  margin-bottom: 12px;
}
.filter-row { display: flex; flex-wrap: wrap; gap: 8px; margin-bottom: 10px; align-items: center; }
.chip, .pill {
  border: 1px solid var(--card-edge);
  background: var(--chip-bg);
  color: var(--ink);
  font: inherit;
  font-size: 0.85rem;
  font-weight: 600;
  padding: 7px 13px;
  border-radius: 999px;
  cursor: pointer;
}
.chip.on, .pill.on { background: var(--chip-on); color: var(--bg); border-color: var(--chip-on); }
.sort-row { justify-content: space-between; }
.sort-row select {
  font: inherit;
  padding: 7px 10px;
  border-radius: 10px;
  border: 1px solid var(--card-edge);
  background: var(--input-bg);
  color: var(--ink);
}
.result-count { color: var(--muted); font-size: 0.9rem; }

/* ---------- tile grid ---------- */
.grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(160px, 1fr));
  gap: 14px;
}
.tile {
  display: flex;
  flex-direction: column;
  gap: 8px;
  background:
    linear-gradient(180deg, rgba(255,255,255,0.5), rgba(255,255,255,0) 42%),
    var(--card);
  border: 1px solid var(--card-edge);
  border-radius: var(--radius);
  padding: 14px;
  text-decoration: none;
  color: var(--ink);
  box-shadow: var(--shadow);
  position: relative;
  transition: transform 0.12s ease;
}
.tile:hover { transform: translateY(-2px); }
.tile-top { display: flex; align-items: center; gap: 10px; }
.icon-wrap {
  width: 52px; height: 52px; flex: 0 0 52px;
  border-radius: 14px;
  overflow: hidden;
  background: linear-gradient(135deg, hsl(var(--accent-h, 210) 70% 88%), hsl(var(--accent-h, 210) 70% 76%));
  border: 2px solid hsl(var(--accent-h, 210) 65% 62%);
  display: flex; align-items: center; justify-content: center;
}
.icon-wrap img { width: 100%; height: 100%; object-fit: cover; }
.icon-wrap.large { width: 84px; height: 84px; flex-basis: 84px; border-radius: 20px; }
.letter-tile {
  width: 100%; height: 100%;
  align-items: center; justify-content: center;
  font-size: 1.7rem; font-weight: 800;
  color: hsl(var(--accent-h, 210) 60% 30%);
}
.tile h3 { margin: 0; font-size: 1rem; line-height: 1.25; }
.tile .sub { color: var(--muted); font-size: 0.8rem; margin: 0; }
.tile .desc { font-size: 0.83rem; color: var(--muted); margin: 0;
  display: -webkit-box; -webkit-line-clamp: 2; -webkit-box-orient: vertical; overflow: hidden; }
.tile .rating { font-size: 0.82rem; color: var(--muted); margin: 0; }
.badges { display: flex; flex-wrap: wrap; gap: 6px; margin-top: auto; }
.store-badge {
  font-size: 0.72rem; font-weight: 700;
  padding: 4px 10px;
  border-radius: 999px;
  background: var(--accent-soft);
  color: var(--accent);
  text-decoration: none;
  border: 1px solid var(--card-edge);
}
a.store-badge:hover { filter: brightness(0.96); }
.verified {
  font-size: 0.75rem; font-weight: 700; color: var(--good);
  display: inline-flex; align-items: center; gap: 4px;
}
.made-by-us {
  position: absolute; top: 10px; right: -6px;
  background: var(--accent); color: #fff;
  font-size: 0.68rem; font-weight: 800;
  padding: 3px 10px; border-radius: 999px 0 0 999px;
  box-shadow: var(--shadow);
}
.empty-state {
  text-align: center; font-size: 1.15rem; color: var(--muted);
  padding: 48px 16px;
}

/* ---------- detail page ---------- */
.detail { max-width: 760px; }
.back { text-decoration: none; font-weight: 600; }
.detail-card {
  background: var(--card);
  border: 1px solid var(--card-edge);
  border-radius: 20px;
  padding: 24px;
  box-shadow: var(--shadow);
  margin-top: 12px;
}
.detail-head { display: flex; gap: 18px; align-items: center; margin-bottom: 8px; }
.detail-head h1 { margin: 0 0 4px; font-size: 1.6rem; }
.detail-head .cat { color: var(--muted); margin: 0; }
.detail-head .rating { margin: 4px 0 0; color: var(--muted); }
.desc { font-size: 1.02rem; }
.detail-card h2 { font-size: 1.05rem; margin: 22px 0 10px; }
.get-it { display: flex; flex-wrap: wrap; gap: 10px; }
.store-badge.big { font-size: 0.95rem; padding: 10px 20px; }
.per-badge-note {
  background: var(--accent-soft);
  border-radius: 12px;
  padding: 10px 14px;
  font-size: 0.9rem;
}
.promise-checks { list-style: none; padding: 0; margin: 0; display: flex; flex-wrap: wrap; gap: 8px 20px; }
.promise-checks li { font-weight: 600; }
.t-pills { display: flex; flex-wrap: wrap; gap: 8px; }
.t-pill {
  background: var(--good-soft); color: var(--good);
  font-weight: 700; font-size: 0.85rem;
  padding: 6px 12px; border-radius: 999px;
}
.feedback-note { color: var(--muted); font-size: 0.9rem; }
.feedback-row { display: flex; flex-wrap: wrap; gap: 8px; }
.feedback-row button {
  font: inherit; font-size: 0.88rem; font-weight: 600;
  padding: 9px 14px; border-radius: 999px;
  border: 1px solid var(--card-edge);
  background: var(--chip-bg); color: var(--ink);
  cursor: pointer;
}
.feedback-row button:hover { border-color: var(--accent); }

/* ---------- footer ---------- */
.site-footer { border-top: 1px solid var(--card-edge); background: var(--header-bg); }
.footer-inner { max-width: 1100px; margin: 0 auto; padding: 24px 16px 32px; }
.about { max-width: 640px; color: var(--muted); font-size: 0.92rem; }
.footer-links { font-size: 0.92rem; }
.count-line { color: var(--muted); font-size: 0.85rem; font-style: italic; }
.geek-webring, .construction { display: none; }

/* ================================================================
   GEEK MODE — full 2000s internet skin over the same markup.
   The comedy lives in the chrome; content stays readable.
   ================================================================ */
:root[data-mode="geek"] {
  --font: "Comic Sans MS", "Comic Sans", "Chalkboard SE", "Times New Roman", serif;
  --radius: 0;
}
:root[data-mode="geek"] body {
  background-color: #00001a;
  background-image:
    radial-gradient(1.5px 1.5px at 12% 22%, #fff 50%, transparent 51%),
    radial-gradient(1px 1px at 68% 8%, #fff 50%, transparent 51%),
    radial-gradient(2px 2px at 84% 64%, #fff 50%, transparent 51%),
    radial-gradient(1px 1px at 32% 78%, #fff 50%, transparent 51%),
    radial-gradient(1.5px 1.5px at 52% 42%, #ffe97a 50%, transparent 51%),
    radial-gradient(1px 1px at 8% 58%, #fff 50%, transparent 51%),
    radial-gradient(1.5px 1.5px at 92% 30%, #fff 50%, transparent 51%),
    radial-gradient(1px 1px at 44% 92%, #fff 50%, transparent 51%);
  color: #e8e8ff;
  --bg: #00001a;
  --ink: #f2f2ff;
  --muted: #b9b9e6;
  --card: #101038;
  --card-edge: #3a3a8c;
  --accent: #7df9ff;
  --accent-soft: #1c1c5e;
  --good: #39ff6a;
  --good-soft: #0d3a1c;
  --header-bg: #0a0a2e;
  --chip-bg: #1c1c5e;
  --chip-on: #7df9ff;
  --input-bg: #0a0a2e;
  --shadow: none;
}
:root[data-mode="geek"] .site-header { border-bottom: 3px ridge #7df9ff; }
:root[data-mode="geek"] .brand-text strong { font-family: "Times New Roman", serif; color: #ffe97a; }
:root[data-mode="geek"] .tagline { overflow: hidden; white-space: nowrap; }
:root[data-mode="geek"] .marquee-text {
  display: inline-block;
  padding-left: 100%;
  animation: geek-marquee 14s linear infinite;
  color: #7df9ff;
}
@keyframes geek-marquee { to { transform: translateX(-100%); } }
:root[data-mode="geek"] .geek-badge { display: block; }
:root[data-mode="geek"] .hero h1 { font-family: "Times New Roman", serif; color: #ffe97a; }
:root[data-mode="geek"] .promise-strip { border: 3px outset #39ff6a; }
:root[data-mode="geek"] .tile {
  border: 3px outset #5a5ac8;
  background: var(--card);
  box-shadow: 4px 4px 0 #000;
}
:root[data-mode="geek"] .tile:hover { transform: none; border-style: inset; }
:root[data-mode="geek"] .icon-wrap { border-radius: 0; }
:root[data-mode="geek"] .detail-card { border: 3px ridge #7df9ff; }
:root[data-mode="geek"] .chip, :root[data-mode="geek"] .pill,
:root[data-mode="geek"] #search, :root[data-mode="geek"] .sort-row select {
  border-radius: 0;
  border: 2px outset #5a5ac8;
}
:root[data-mode="geek"] .chip.on, :root[data-mode="geek"] .pill.on { border-style: inset; }
:root[data-mode="geek"] .store-badge { border-radius: 0; border: 2px outset #5a5ac8; }
:root[data-mode="geek"] .made-by-us { border-radius: 0; }
:root[data-mode="geek"] .site-footer { border-top: 3px ridge #7df9ff; }
:root[data-mode="geek"] .geek-webring { display: block; text-align: center; color: var(--muted); }
:root[data-mode="geek"] .geek-webring button {
  font: inherit; color: var(--accent); background: none; border: none;
  text-decoration: underline; cursor: pointer; padding: 0;
}
:root[data-mode="geek"] .construction { display: block; text-align: center; margin: 14px 0 4px; }
:root[data-mode="geek"] .construction span {
  font-weight: 800; letter-spacing: 2px; color: #000;
  background: repeating-linear-gradient(45deg, #ffe97a 0 14px, #111 14px 28px);
  padding: 6px 18px;
  -webkit-text-stroke: 0;
}
:root[data-mode="geek"] .feedback-row button { border-radius: 0; border: 2px outset #5a5ac8; }
:root[data-mode="geek"] .switcher { border-radius: 0; }
:root[data-mode="geek"] .switcher button.on { background: #ffe97a; color: #000; }

@media (max-width: 640px) {
  .header-inner { gap: 10px; }
  .tabs { margin-left: 0; }
  .grid { grid-template-columns: repeat(auto-fill, minmax(140px, 1fr)); gap: 10px; }
  .detail-card { padding: 18px; }
}
"""

JS_CONTENT = r"""
/* Actually Free — directory client logic. Vanilla JS, no dependencies. */
(function () {
  "use strict";
  var cfg = window.AF_CONFIG || {};
  var GC = cfg.GOATCOUNTER_CODE || "";

  /* ---------- Goatcounter (skipped silently until Derick pastes a code) --- */
  function gcReady() { return GC && GC.indexOf("PASTE") !== 0 && window.goatcounter; }
  function gcEvent(path) {
    if (gcReady()) {
      try { window.goatcounter.count({ path: "event/" + path, event: true }); } catch (e) {}
    }
  }
  if (GC && GC.indexOf("PASTE") !== 0) {
    var s = document.createElement("script");
    s.async = true;
    s.setAttribute("data-goatcounter", "https://" + GC + ".goatcounter.com/count");
    s.src = "https://gc.zgo.at/count.js";
    document.head.appendChild(s);
  }

  /* ---------- mode + theme (persisted, orthogonal) ------------------------- */
  var root = document.documentElement;
  var MASCOTS = { playful: "/assets/mascot-cartoon.webp", geek: "/assets/mascot-geek.webp" };
  function applyMode(mode) {
    root.setAttribute("data-mode", mode);
    try { localStorage.setItem("af-mode", mode); } catch (e) {}
    document.querySelectorAll('[data-mode]').forEach(function (b) {
      if (b.tagName === "BUTTON") b.classList.toggle("on", b.getAttribute("data-mode") === mode);
    });
    var m = document.getElementById("mascot");
    if (m && MASCOTS[mode]) m.src = MASCOTS[mode];
    var empty = document.getElementById("empty-state");
    if (empty && !empty.hidden && state && state.query) renderEmpty();
  }
  function applyTheme(theme) {
    root.setAttribute("data-theme", theme);
    try { localStorage.setItem("af-theme", theme); } catch (e) {}
    document.querySelectorAll('[data-theme]').forEach(function (b) {
      if (b.tagName === "BUTTON") b.classList.toggle("on", b.getAttribute("data-theme") === theme);
    });
  }
  var savedMode = "playful", savedTheme = "default";
  try {
    savedMode = localStorage.getItem("af-mode") || "playful";
    savedTheme = localStorage.getItem("af-theme") || "default";
  } catch (e) {}
  applyMode(savedMode);
  applyTheme(savedTheme);
  document.querySelectorAll('button[data-mode]').forEach(function (b) {
    b.addEventListener("click", function () { applyMode(b.getAttribute("data-mode")); });
  });
  document.querySelectorAll('button[data-theme]').forEach(function (b) {
    b.addEventListener("click", function () { applyTheme(b.getAttribute("data-theme")); });
  });

  /* ---------- feedback buttons (detail pages) ------------------------------- */
  var FEEDBACK_SUBJECTS = {
    "doesnt-work": "App doesn't work",
    "broke-promise": "App broke a promise",
    "correction": "Listing correction"
  };
  document.querySelectorAll("[data-feedback]").forEach(function (b) {
    b.addEventListener("click", function () {
      var kind = b.getAttribute("data-feedback"), slug = b.getAttribute("data-app");
      gcEvent("feedback/" + kind + "/" + slug);
      var email = (cfg.FEEDBACK_EMAIL || "").indexOf("PASTE") === 0 ? "" : cfg.FEEDBACK_EMAIL;
      if (!email) { alert("Feedback email isn't configured yet \u2014 check back soon."); return; }
      var body = "App: " + location.href + "\n\nWhat happened:\n";
      location.href = "mailto:" + email +
        "?subject=" + encodeURIComponent("[Actually Free] " + (FEEDBACK_SUBJECTS[kind] || "Feedback")) +
        "&body=" + encodeURIComponent(body);
    });
  });

  /* ---------- suggest-an-app link ------------------------------------------- */
  var suggest = document.getElementById("suggest-link");
  if (suggest) {
    suggest.addEventListener("click", function (ev) {
      ev.preventDefault();
      gcEvent("suggest-app");
      var email = (cfg.FEEDBACK_EMAIL || "").indexOf("PASTE") === 0 ? "" : cfg.FEEDBACK_EMAIL;
      if (!email) { alert("Feedback email isn't configured yet \u2014 check back soon."); return; }
      location.href = "mailto:" + email +
        "?subject=" + encodeURIComponent("[Actually Free] App suggestion") +
        "&body=" + encodeURIComponent("App name:\nWhere to find it (Play/F-Droid/GitHub link):\nWhy it's actually free:\n");
    });
  }

  /* ---------- random app (geek webring) -------------------------------------- */
  var randomBtn = document.getElementById("random-app");
  if (randomBtn) {
    randomBtn.addEventListener("click", function () {
      if (state && state.apps.length) {
        var a = state.apps[Math.floor(Math.random() * state.apps.length)];
        location.href = "/app/" + a.slug + ".html";
      } else { location.href = "/index.html"; }
    });
  }

  /* ---------- directory grid ------------------------------------------------- */
  var grid = document.getElementById("grid");
  if (!grid) return; // not the directory page

  var state = { apps: [], query: "", cat: "", attrs: {}, sort: "name" };
  var ACCENTS = { "Utilities": 210, "Media": 280, "Comms & System": 160,
                  "Utilities / Comms & System": 190 };

  function norm(s) {
    return (s || "").toLowerCase().replace(/[^a-z0-9\s]/g, " ").replace(/\s+/g, " ").trim();
  }
  function tokens(s) { return norm(s).split(" ").filter(Boolean); }
  function levenshtein(a, b) {
    if (a === b) return 0;
    var m = a.length, n = b.length;
    if (!m) return n; if (!n) return m;
    var d = [], i, j;
    for (i = 0; i <= m; i++) d[i] = [i];
    for (j = 0; j <= n; j++) d[0][j] = j;
    for (i = 1; i <= m; i++) for (j = 1; j <= n; j++)
      d[i][j] = Math.min(d[i-1][j] + 1, d[i][j-1] + 1,
                         d[i-1][j-1] + (a[i-1] === b[j-1] ? 0 : 1));
    return d[m][n];
  }
  function isSubsequence(q, target) {
    var i = 0;
    for (var k = 0; k < target.length && i < q.length; k++)
      if (target[k] === q[i]) i++;
    return i === q.length;
  }
  function matches(app, q) {
    if (!q) return true;
    var hay = norm([app.name, app.description, app.category, app.subcategory].join(" "));
    if (hay.indexOf(q) !== -1) return true;
    var nameNorm = norm(app.name);
    if (isSubsequence(q.replace(/\s+/g, ""), nameNorm.replace(/\s+/g, ""))) return true;
    var hayTokens = tokens(hay);
    return tokens(q).some(function (qt) {
      return hayTokens.some(function (ht) { return levenshtein(qt, ht) <= 2; });
    });
  }

  function escHtml(s) {
    return String(s == null ? "" : s).replace(/[&<>"']/g, function (c) {
      return { "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c];
    });
  }
  function storeBadges(app) {
    var out = [];
    var defs = [["play", "Play", app.stores.play],
                ["fdroid", "F-Droid", app.stores.fdroid ? "https://f-droid.org/en/packages/" + app.package + "/" : null],
                ["github", "GitHub", app.stores.github]];
    defs.forEach(function (d) {
      if (d[2]) out.push('<span class="store-badge">' + d[1] + "</span>");
    });
    return out.join("");
  }
  function tile(app) {
    var accent = ACCENTS[app.category] != null ? ACCENTS[app.category] : 210;
    var icon = "https://f-droid.org/repo/" + encodeURIComponent(app.package) + "/en-US/icon.png";
    var letter = escHtml(app.name.charAt(0).toUpperCase());
    var rating = app.rating ? '<p class="rating">\u2605 ' + escHtml(app.rating) + "</p>" : "";
    var ribbon = app.made_by_us ? '<span class="made-by-us">Made by us</span>' : "";
    return '<a class="tile" style="--accent-h:' + accent + '" href="/app/' + escHtml(app.slug) +
      '.html" data-slug="' + escHtml(app.slug) + '">' + ribbon +
      '<span class="tile-top"><span class="icon-wrap">' +
      '<img src="' + icon + '" alt="" loading="lazy" onerror="this.style.display=\'none\';this.nextElementSibling.style.display=\'flex\'">' +
      '<span class="letter-tile" style="display:none">' + letter + "</span></span>" +
      "<span><h3>" + escHtml(app.name) + "</h3>" +
      '<p class="sub">' + escHtml(app.subcategory || app.category) + "</p></span></span>" +
      rating +
      '<p class="desc">' + escHtml(app.description) + "</p>" +
      '<span class="badges">' + storeBadges(app) + "</span>" +
      '<span class="verified">\u2713 Verified actually-free</span></a>';
  }

  function filtered() {
    var q = norm(state.query);
    var list = state.apps.filter(function (app) {
      if (state.cat && app.category !== state.cat) return false;
      for (var k in state.attrs) {
        if (k === "made_by_us") { if (!app.made_by_us) return false; }
        else if (!app.attrs[k]) return false;
      }
      return matches(app, q);
    });
    if (state.sort === "rating") {
      list.sort(function (a, b) { return (b.rating || -1) - (a.rating || -1); });
    } else {
      list.sort(function (a, b) { return a.name.toLowerCase().localeCompare(b.name.toLowerCase()); });
    }
    return { list: list, q: q };
  }

  function renderEmpty() {
    var empty = document.getElementById("empty-state");
    var mode = root.getAttribute("data-mode");
    empty.textContent = mode === "geek"
      ? "Well, actually\u2026 your query returned 0 rows. Have you tried turning it off and on again?"
      : "Well, actually\u2026 we don't list anything matching that.";
  }

  function render() {
    var r = filtered();
    var total = state.apps.length;
    grid.innerHTML = r.list.map(tile).join("");
    var empty = document.getElementById("empty-state");
    var count = document.getElementById("result-count");
    if (!r.list.length) {
      empty.hidden = false;
      renderEmpty();
      count.textContent = "0 of " + total;
    } else {
      empty.hidden = true;
      count.textContent = (r.q || state.cat || Object.keys(state.attrs).length)
        ? r.list.length + " of " + total
        : total + " actually-free apps";
    }
    grid.querySelectorAll(".tile").forEach(function (t) {
      t.addEventListener("click", function () { gcEvent("tile-view/" + t.getAttribute("data-slug")); });
    });
  }

  /* controls */
  var searchInput = document.getElementById("search");
  var searchTimer = null;
  searchInput.addEventListener("input", function () {
    clearTimeout(searchTimer);
    searchTimer = setTimeout(function () {
      state.query = searchInput.value;
      var r = filtered();
      gcEvent("search/" + (r.list.length ? "results/" : "zero/") + encodeURIComponent(norm(state.query)).slice(0, 80));
      render();
    }, 220);
  });
  document.querySelectorAll("#category-chips .chip").forEach(function (c) {
    c.addEventListener("click", function () {
      document.querySelectorAll("#category-chips .chip").forEach(function (x) { x.classList.remove("on"); });
      c.classList.add("on");
      state.cat = c.getAttribute("data-cat");
      gcEvent("filter/category/" + encodeURIComponent(state.cat || "all").slice(0, 60));
      render();
    });
  });
  document.querySelectorAll(".pill").forEach(function (p) {
    p.addEventListener("click", function () {
      var k = p.getAttribute("data-attr");
      if (state.attrs[k]) delete state.attrs[k]; else state.attrs[k] = true;
      p.classList.toggle("on", !!state.attrs[k]);
      gcEvent("filter/" + k);
      render();
    });
  });
  document.getElementById("sort").addEventListener("change", function (e) {
    state.sort = e.target.value;
    render();
  });

  fetch("/data/apps.json")
    .then(function (r) { return r.json(); })
    .then(function (apps) { state.apps = apps; render(); })
    .catch(function () {
      grid.innerHTML = "<p>Couldn't load the app list. Check back in a bit.</p>";
    });
})();
"""

CONFIG_JS = """/* Actually Free — site configuration.
   Derick: fill in the two values below, then redeploy. Nothing else needed. */
window.AF_CONFIG = {
  // Goatcounter site code: the subdomain part of your Goatcounter URL.
  // e.g. if your dashboard is at actuallyfree.goatcounter.com, put "actuallyfree".
  // Free signup at https://www.goatcounter.com — no API key needed.
  // Until this is set, analytics are skipped silently.
  GOATCOUNTER_CODE: "PASTE-YOUR-CODE-HERE",

  // Email address that receives "broke a promise" reports, corrections,
  // and app suggestions (plain mailto links — no backend, no accounts).
  FEEDBACK_EMAIL: "PASTE-FEEDBACK-EMAIL-HERE"
};
"""

README_MD = """# Actually Free — free.certifiable.media

A hand-curated directory of Android apps that are **actually free**:
no ads, no in-app purchases, no subscriptions. Every app is checked
before listing. Static site, vanilla HTML/CSS/JS, zero backend.

## Regenerate

One command rebuilds everything from the research corpus:

```
python3 generate.py
```

This reads `~/workspace/certifiable-apps/apps-seed.json`, keeps the
verified listings (`include` + `per-badge`), adds QR Cards, and emits:

- `data/apps.json` — the 79 listings as JSON
- `index.html` — the directory (tiles render client-side)
- `app/<slug>.html` — one static page per app (SEO: real title, meta, OG tags)
- `sitemap.xml`, `robots.txt`
- `assets/` — styles.css, app.js, config.js, mascots

## Derick's setup steps

1. **Create the repo** at `github.com/derickca/actually-free` (public fits
   the transparency brand) and push this folder.
2. **Cloudflare Pages**: connect the repo, then add the custom domain
   `free.certifiable.media` (free SSL included).
3. **Paste two values** into `assets/config.js` and redeploy:
   - `GOATCOUNTER_CODE` — your Goatcounter site code (free signup, no API key)
   - `FEEDBACK_EMAIL` — where "broke a promise" reports and suggestions go

## Corpus rules (baked into generate.py)

- `per-badge` listings show F-Droid/GitHub badges only — the Play URL is
  stripped, with an explainer on the detail page.
- Transparency attributes (open source / offline / no account) are derived
  **conservatively**: open source iff on F-Droid; offline / no-account only
  when the research notes say so explicitly. Missing attribute = pill absent.
- The three locked promises (no ads, no IAP, no subscriptions) hold for
  every listed app by construction.

## Awaiting Derick's call (7 — not listed)

{awaiting}

## Documented exclusions (6 — not listed, users will ask)

{excluded}
"""


def build_readme():
    with open(SEED, encoding="utf-8") as f:
        seed = json.load(f)
    def line(r):
        note = re.sub(r"\s+", " ", r.get("notes") or "").strip()
        return f"- **{r['name']}** — {tidy(note, 170)}"
    awaiting = "\n".join(line(r) for r in seed if r.get("status") == "flag")
    excluded = "\n".join(line(r) for r in seed if r.get("status") == "exclude")
    return README_MD.format(awaiting=awaiting, excluded=excluded)


def write(path, content):
    full = os.path.join(HERE, path)
    os.makedirs(os.path.dirname(full), exist_ok=True)
    with open(full, "w", encoding="utf-8") as f:
        f.write(content)


def main():
    apps = load_corpus()
    categories = sorted({a["category"] for a in apps})
    print(f"{len(apps)} apps "
          f"({sum(1 for a in apps if a['made_by_us'])} made by us, "
          f"{sum(1 for a in apps if a['per_badge'])} per-badge)")

    write("data/apps.json", json.dumps(apps, indent=1, ensure_ascii=False) + "\n")
    write("index.html", build_index(apps, categories))
    for app in apps:
        write(f"app/{app['slug']}.html", build_detail(app))
    write("sitemap.xml", build_sitemap(apps))
    write("robots.txt", ROBOTS)
    write("assets/styles.css", CSS_CONTENT.strip() + "\n")
    write("assets/app.js", JS_CONTENT.strip() + "\n")
    write("assets/config.js", CONFIG_JS)
    write("README.md", build_readme())
    print("done: index, %d detail pages, sitemap, robots, assets, README"
          % len(apps))


if __name__ == "__main__":
    main()
