#!/usr/bin/env python3
"""Actually Free — static site generator.

Reads ~/workspace/certifiable-apps/apps-seed.json, keeps the verified
listings (status=include + status=per-badge), adds QR Cards, and emits a
fully static site deployable as-is to Cloudflare Pages.

Regenerate everything with:  python3 generate.py
"""
import base64
import datetime
import html
import json
import os
import re
import secrets
import shutil
from collections import Counter

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

# The QR Cards glyph: same logo in the site header app-icon, the directory
# tile, and the detail page heading.
QR_GLYPH_SVG = (
    '<svg viewBox="0 0 32 32" aria-hidden="true">'
    '<rect x="4" y="4" width="10" height="10" rx="2" fill="#0f766e"/>'
    '<rect x="18" y="4" width="10" height="10" rx="2" fill="#0f766e"/>'
    '<rect x="4" y="18" width="10" height="10" rx="2" fill="#0f766e"/>'
    '<rect x="7" y="7" width="4" height="4" rx="1" fill="#ffffff"/>'
    '<rect x="21" y="7" width="4" height="4" rx="1" fill="#ffffff"/>'
    '<rect x="7" y="21" width="4" height="4" rx="1" fill="#ffffff"/>'
    '<rect x="18" y="18" width="3" height="3" fill="#0f766e"/>'
    '<rect x="23" y="18" width="3" height="3" fill="#0f766e"/>'
    '<rect x="18" y="23" width="3" height="3" fill="#0f766e"/>'
    '<rect x="25" y="25" width="3" height="3" fill="#0f766e"/>'
    "</svg>"
)

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
    "icon_svg": QR_GLYPH_SVG,
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
    "2048 Open Fun Game": "The 2048 sliding tile puzzle, clean and open source.",
    "Andor's Trail": "A classic-style offline RPG: quests, dungeons, no paywalls.",
    "Anuto TD": "Tower defense with deep mechanics and custom maps.",
    "Block Puzzle Stone Wars": "Block puzzle: fit the pieces, clear the board.",
    "Chogan": "Chogan: a modern abstract board game.",
    "CrossWords": "Crossword / Scrabble-style word game, solo or online.",
    "Dungeon Crawl Stone Soup": "Dungeon Crawl Stone Soup: the deep, unforgiving roguelike classic.",
    "Endless Sky": "A space trading and combat epic across the galaxy.",
    "Freebloks": "Blokus-style tile placement against the AI.",
    "Freedoom": "A complete free Doom-engine game: demons, shotguns, no ads.",
    "HyperRogue": "A roguelike on impossible non-Euclidean geometry.",
    "LibreSudoku": "Sudoku with puzzle packs and clean design.",
    "Lichess": "Free online chess: play, solve puzzles, no account needed to play.",
    "Luanti": "Luanti: open-source voxel sandbox (Minecraft-like), endless mods.",
    "Mindustry": "Factory-building tower defense: mine, automate, defend.",
    "Minesweeper": "Minesweeper done right, no ads, no nonsense.",
    "Open Patience": "A collection of solitaire card games.",
    "OpenTTD": "Transport Tycoon: build a transport empire from 1950 onward.",
    "Pixel Wheels": "Top-down arcade racer, quick races.",
    "Shattered Pixel Dungeon": "A polished turn-based roguelike: descend, loot, die, try again.",
    "Simon Tatham's Puzzles": "Over 40 of Simon Tatham's logic puzzles in one app.",
    "SuperTuxKart": "Kart racing with Tux and friends, single and multiplayer.",
    "The Battle for Wesnoth": "The classic turn-based fantasy strategy, full campaigns.",
    "Unciv": "An open-source remake of Civilization V for your phone.",
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


# Filter labels are single words with no textual overlap: "Comms & System"
# shortens to "Comms", and the one-off "Utilities / Comms & System" record
# (Material Files, a file manager) folds into "Utilities".
CATEGORY_FIXUPS = {
    "Comms & System": "Comms",
    "Utilities / Comms & System": "Utilities",
}


def clean_record(rec):
    stores = rec.get("stores") or {}
    ver = rec.get("verification") or {}
    per_badge = rec.get("status") == "per-badge"
    out_stores = {
        # Per-badge rule: strip the Play URL entirely for disqualified builds.
        "play": None if per_badge else (stores.get("play") or None),
        "fdroid": bool(stores.get("fdroid")),
        "izzy": stores.get("izzy") or None,
        "github": stores.get("github") or None,
        "openapk": stores.get("openapk") or None,
    }
    # Self-hosted real icon when the icon hunt found one; otherwise the
    # tile/detail page falls back to the letter tile.
    icon_file = os.path.join(HERE, "assets", "icons", rec["package"] + ".png")
    icon = ("assets/icons/" + rec["package"] + ".png"
            if os.path.exists(icon_file) else None)
    return {
        "name": rec["name"],
        "package": rec["package"],
        "slug": slugify(rec["package"]),
        "category": CATEGORY_FIXUPS.get(rec.get("category"), rec.get("category") or "Utilities"),
        # Money promises the listed build keeps. Every v1 listing satisfies
        # all three (it's the inclusion bar); stored explicitly so the
        # "Find apps with:" filters have real data if that ever changes.
        "promises": {"no_ads": True, "no_iap": True, "no_subs": True},
        "icon_svg": rec.get("icon_svg"),
        "icon": icon,
        "subcategory": rec.get("subcategory") or "",
        "description": rec.get("description") or extract_description(rec),
        "stores": out_stores,
        "rating": ver.get("play_rating"),
        "attrs": rec.get("attrs") or derive_attrs(rec),
        "made_by_us": bool(rec.get("made_by_us")),
        "per_badge": per_badge,
        "needs_review": bool(rec.get("needs_review")),
        "review_notes": rec.get("review_notes") or "",
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
# ntfy feedback — browser POSTs straight to ntfy.sh, no backend, no relay.
# The topic is a mild secret: it is NEVER written into page source as a plain
# string. Each build XORs it with a fresh random 16-byte key, stores base64 in
# the forms' data-t attributes, embeds the key separately in app.js, and the
# browser decodes it only at send time. (Same pattern as FundingSpark.)
# ---------------------------------------------------------------------------

NTFY_STORE = os.path.expanduser("~/.config/actually-free/ntfy-topic")
NTFY_UNAVAILABLE = ('<p class="feedback-off" role="note">'
                    'Feedback is not available yet.</p>')


def read_ntfy_topic():
    """The ntfy topic, first hit wins. Never printed, never written to output.

    Priority: AF_NTFY_TOPIC env var, then the durable local store
    (~/.config/actually-free/ntfy-topic), then a legacy NTFY_TOPIC value in
    assets/config.js (migrated to the store on first successful read).
    """
    env = os.environ.get("AF_NTFY_TOPIC", "").strip()
    if env:
        return env
    # Durable local store: bare topic on one line.
    try:
        with open(NTFY_STORE, encoding="utf-8") as f:
            bare = f.read().strip()
            if bare and not bare.startswith("PASTE"):
                return bare
    except OSError:
        pass
    # Legacy: NTFY_TOPIC value in assets/config.js (migrated to the store).
    try:
        with open(os.path.join(HERE, "assets", "config.js"), encoding="utf-8") as f:
            m = re.search(r'NTFY_TOPIC\s*:\s*"([^"]+)"', f.read())
    except OSError:
        m = None
    if m and not m.group(1).startswith("PASTE"):
        return m.group(1)
    return ""


def persist_ntfy_topic(topic):
    """Keep the topic on the build machine so later builds don't need config.js."""
    try:
        os.makedirs(os.path.dirname(NTFY_STORE), exist_ok=True)
        with open(NTFY_STORE, "w", encoding="utf-8") as f:
            f.write(topic + "\n")
        os.chmod(NTFY_STORE, 0o600)
    except OSError as e:
        print("warning: could not persist ntfy topic:", e)


class NtfyForms:
    """One build's worth of ntfy forms: fresh random key, XOR'd topic."""

    def __init__(self, topic):
        self.key = secrets.token_bytes(16)
        self.encoded = ""
        if topic:
            raw = topic.encode("utf-8")
            self.encoded = base64.b64encode(
                bytes(b ^ self.key[i % 16] for i, b in enumerate(raw))
            ).decode("ascii")

    @property
    def key_b64(self):
        return base64.b64encode(self.key).decode("ascii")

    @staticmethod
    def _trap():
        return ('<div class="af-trap" aria-hidden="true">'
                '<label>Leave this field empty '
                '<input type="text" name="website" tabindex="-1" autocomplete="off">'
                "</label></div>")

    @staticmethod
    def _done(text):
        return (f'<div data-af-done hidden>'
                f'<p class="af-thanks" tabindex="-1">{esc(text)}</p></div>')

    def report_form(self, app):
        """Per-app form behind the three feedback buttons (detail pages)."""
        if not self.encoded:
            return NTFY_UNAVAILABLE
        buttons = "\n".join(
            f'      <button type="button" data-feedback="{v}" '
            f'data-label="{lbl}">{lbl}</button>'
            for v, lbl in (("doesnt-work", "Doesn\u2019t work"),
                           ("broke-promise", "Broke a promise"),
                           ("correction", "Suggest a correction")))
        page_url = f"{SITE_URL}/app/{app['slug']}.html"
        return f"""<div class="feedback-row">
{buttons}
    </div>
    <div class="af-form-wrap">
      <form class="af-form" data-af-form="report" data-t="{self.encoded}" hidden novalidate>
        <input type="hidden" name="reason" value="doesnt-work">
        <input type="hidden" name="app_name" value="{esc(app['name'])}">
        <input type="hidden" name="page_url" value="{esc(page_url)}">
        <p class="af-form-head">Report: <strong data-reason-label>Doesn&rsquo;t work</strong>
          &mdash; {esc(app['name'])}</p>
        <label class="af-field">What&rsquo;s wrong?
          <textarea name="note" rows="4" maxlength="1000"></textarea>
        </label>
        {self._trap()}
        <p class="af-error" data-error role="alert"></p>
        <div class="af-actions">
          <button type="submit">Send report</button>
          <button type="button" data-af-cancel>Cancel</button>
        </div>
      </form>
      {self._done("Thank you. Your report has been sent.")}
    </div>"""

    def suggest_form(self, visible=False):
        """Suggest-an-app form. On its own page it's shown immediately, the
        redundant heading line is dropped, and Cancel is omitted (the back
        link above handles that)."""
        if not self.encoded:
            return NTFY_UNAVAILABLE
        hidden = "" if visible else " hidden"
        head = ("" if visible
                else '        <p class="af-form-head"><strong>Suggest an app</strong> for the directory</p>\n')
        cancel = ("" if visible
                  else '          <button type="button" data-af-cancel>Cancel</button>\n')
        return f"""<div class="af-form-wrap">
      <form class="af-form" data-af-form="suggest" data-t="{self.encoded}"{hidden} novalidate>
        <input type="hidden" name="page_url" value="{esc(SITE_URL)}/">
{head}
        <label class="af-field">App name
          <input type="text" name="app_name" maxlength="200" autocomplete="off">
        </label>
        <label class="af-field">Where to find it (Play / F-Droid / GitHub link)
          <input type="text" name="app_link" maxlength="300" inputmode="url" autocomplete="off">
        </label>
        <label class="af-field">Why it&rsquo;s actually free
          <textarea name="note" rows="3" maxlength="1000"></textarea>
        </label>
        {self._trap()}
        <p class="af-error" data-error role="alert"></p>
        <div class="af-actions">
          <button type="submit">Send suggestion</button>
{cancel}        </div>
      </form>
      {self._done("Thank you. Your suggestion has been sent.")}
    </div>"""

# ---------------------------------------------------------------------------
# Shared HTML fragments
# ---------------------------------------------------------------------------

def head(title, description, og_path="", og_image="og-share.png"):
    """<head> with SEO/OG basics. og_path like 'app/foo-bar.html' or ''."""
    url = SITE_URL + ("/" + og_path if og_path else "/")
    img = SITE_URL + "/assets/" + og_image
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
<meta property="og:image:width" content="1200">
<meta property="og:image:height" content="630">
<meta property="og:image:alt" content="Actually Free — find the free apps they don't want you to see.">
<meta name="twitter:card" content="summary_large_image">
<meta name="twitter:title" content="{esc(title)}">
<meta name="twitter:description" content="{esc(description)}">
<meta name="twitter:image" content="{esc(img)}">
<link rel="icon" href="/assets/mascot-friendly.webp">
<link rel="apple-touch-icon" href="/assets/icon-192.png">
<link rel="manifest" href="/manifest.webmanifest">
<meta name="theme-color" content="#fdf4e7">
<link rel="stylesheet" href="/assets/styles.css">
</head>"""


def site_header():
    """Header shared by index + detail pages. Mode/theme switchers included.

    No Directory/QR-Cards tab pair: QR Cards lives in the header as an
    Android-style app icon, and its detail page links back to the directory.
    """
    # Theme icons borrowed from FundingSpark: half-circle = follow system,
    # sun = light, moon = dark. Icon-only buttons keep the header to one row.
    theme_btns = "".join(
        f'<button data-theme="{v}"{ " class=\"on\"" if v == "default" else "" }'
        f' title="{t}" aria-label="{t}">{s}</button>'
        for v, (s, t) in {
            "default": ('<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" aria-hidden="true"><circle cx="12" cy="12" r="8.5"/><path d="M12 3.5v17a8.5 8.5 0 0 0 0-17z" fill="currentColor" stroke="none"/></svg>', "Follow system"),
            "light": ('<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" aria-hidden="true"><circle cx="12" cy="12" r="4"/><path d="M12 2.5v2M12 19.5v2M4.6 4.6 6 6M18 18l1.4 1.4M2.5 12h2M19.5 12h2M4.6 19.4 6 18M18 6l1.4-1.4"/></svg>', "Light"),
            "dark": ('<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linejoin="round" aria-hidden="true"><path d="M20 14.5A8 8 0 0 1 9.5 4a8 8 0 1 0 10.5 10.5z"/></svg>', "Dark"),
        }.items()
    )
    return f"""<header class="site-header">
  <div class="header-inner">
    <a class="brand" href="/">
      <img id="mascot" src="/assets/mascot-friendly.webp" alt="Actually Guy, the Actually Free mascot" width="56" height="56">
      <span class="brand-text"><strong>Actually Free</strong><em>{esc(TAGLINE)}</em></span>
    </a>
    <a class="qr-appicon" href="/app/derickca-qr-cards.html" title="QR Cards — a free app we made">
      <span class="qr-appicon-glyph" aria-hidden="true">{QR_GLYPH_SVG}</span>
      <span class="qr-appicon-label">QR Cards</span>
    </a>
    <div class="switchers">
      <div class="switcher" role="group" aria-label="Site mode">
        <button data-mode="playful" class="on" title="Playful mode">Playful</button><button data-mode="geek" title="Geek mode: full 2000s internet">Geek</button>
      </div>
      <div class="switcher theme-switcher" role="group" aria-label="Color theme">
        {theme_btns}
      </div>
    </div>
  </div>
</header>"""



def site_footer(forms):
    suggest_link = ('<a href="/suggest">Suggest an app</a>'
                    if forms.encoded else 'Suggest an app')
    return f"""<footer class="site-footer">
  <div class="footer-inner">
    <p class="about"><strong>Actually Free</strong> is a hand-curated directory of Android apps that are
    actually free. Every app is checked before listing: no ads, no in-app purchases, no subscriptions.
    If an app breaks the promise, report it and we'll take a look.</p>
    <p class="fine-print"><strong>The fine print:</strong> We don't own these apps (except QR Cards).
    Not every store is equally trustworthy &mdash; download with judgment, use at your own risk.</p>
    <p class="footer-links">
      {suggest_link} &middot;
      <a href="/what-is-free">What Is Free?</a> &middot;
      <a href="/">Directory</a> &middot;
      <a href="/app/derickca-qr-cards.html">QR Cards</a>
    </p>
    <p class="geek-webring" aria-hidden="true"><span>&larr; prev</span> &middot; <button id="random-app" type="button">random</button> &middot; <span>next &rarr;</span></p>
    <p class="construction" aria-hidden="true"><span>UNDER CONSTRUCTION</span></p>
    <p class="count-line">We count clicks, not people.</p>
  </div>
</footer>
<script src="/assets/config.js"></script>
<script src="/assets/app.js"></script>
<script>if("serviceWorker" in navigator){{navigator.serviceWorker.register("/sw.js").catch(function(){{}});}}</script>"""


# ---------------------------------------------------------------------------
# index.html — the directory shell (tiles render client-side from apps.json)
# ---------------------------------------------------------------------------

def build_index(apps, categories, forms):
    chips = "\n".join(
        f'      <button class="chip" data-cat="{esc(c)}">{esc(c)}</button>'
        for c in categories)
    return f"""<!DOCTYPE html>
<html lang="en" data-mode="playful" data-theme="default">
{head("Actually Free \u2014 " + TAGLINE,
      "A hand-curated directory of Android apps that are actually free: no ads, no in-app purchases, no subscriptions. " + TAGLINE)}
<body>
{site_header()}
<main class="directory">
  <section class="hero">
    <h1>Actually free Android apps.</h1>
    <p class="tagline"><span class="marquee-text">{esc(TAGLINE)}</span></p>
  </section>
  <p class="promise-line"><span class="lock">\u2713 No ads</span> \u00b7 <span class="lock">\u2713 No in-app purchases</span> \u00b7 <span class="lock">\u2713 No subscriptions</span></p>
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
      <button class="pill" data-attr="reviewed">Reviewed</button>
    </div>
    <div class="filter-row" role="group" aria-label="Filter by store">
      <button class="pill" data-store="fdroid">F-Droid</button>
      <button class="pill" data-store="izzy">IzzyOnDroid</button>
      <button class="pill" data-store="openapk">OpenAPK</button>
      <button class="pill" data-store="play">Google Play</button>
      <button class="pill" data-store="github">GitHub</button>
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
{site_footer(forms)}
</body>
</html>
"""

# ---------------------------------------------------------------------------
# Detail pages — one real static HTML page per app (SEO)
# ---------------------------------------------------------------------------

STORE_LABELS = [("fdroid", "F-Droid"), ("izzy", "IzzyOnDroid"), ("openapk", "OpenAPK"), ("play", "Play"), ("github", "GitHub")]


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


def build_detail(app, forms):
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
    # Real self-hosted icon when the icon hunt found one; otherwise the
    # letter tile. (The old f-droid.org hotlink guessed a URL pattern that
    # doesn't exist, so almost every app fell back to the letter.)
    icon_src = ("/" + app["icon"]) if app.get("icon") else None
    letter = esc(app["name"][0].upper())
    if app.get("icon_svg"):
        icon_block = f'<span class="icon-wrap large">{app["icon_svg"]}</span>'
    elif icon_src:
        icon_block = (
            '<span class="icon-wrap large">'
            f'<img src="{icon_src}" alt="" loading="lazy" '
            'onerror="this.style.display=\'none\';this.nextElementSibling.style.display=\'flex\'">'
            f'<span class="letter-tile" style="display:none">{letter}</span></span>')
    else:
        icon_block = (
            '<span class="icon-wrap large">'
            f'<span class="letter-tile" style="display:flex">{letter}</span></span>')
    review = (f'<div class="review-note"><h2>Needs further review</h2>'
              f'<p>{esc(app["review_notes"] or "This listing hasn\u2019t been fully verified yet \u2014 help us check it.")}</p></div>'
              if app.get("needs_review") else "")
    return f"""<!DOCTYPE html>
<html lang="en" data-mode="playful" data-theme="default">
{head(title, desc, f"app/{app['slug']}.html")}
<body>
{site_header()}
<main class="detail">
  <p><a class="back" href="/">&larr; Back to the directory</a></p>
  <article class="detail-card">
    <div class="detail-head">
      {icon_block}
      <div>
        <h1>{esc(app["name"])} {ribbon}</h1>
        <p class="cat">{esc(app["category"])}{" \u00b7 " + esc(app["subcategory"]) if app["subcategory"] else ""}</p>
        {rating}
      </div>
    </div>
    <p class="desc">{esc(app["description"])}</p>
    {review}
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
{forms.report_form(app)}
  </article>
</main>
{site_footer(forms)}
</body>
</html>
"""


def build_suggest(forms):
    # Suggest-an-app as its own page, styled like an app detail page.
    return f"""<!DOCTYPE html>
<html lang="en" data-mode="playful" data-theme="default">
{head("Suggest an app \u2014 Actually Free",
      "Suggest an Android app for the Actually Free directory: no ads, no in-app purchases, no subscriptions.",
      og_path="suggest")}
<body>
{site_header()}
<main class="detail">
  <p><a class="back" href="/">&larr; Back to the directory</a></p>
  <article class="detail-card">
    <div class="detail-head">
      <div>
        <h1>Suggest an app</h1>
        <p class="cat">Know an Android app that's actually free? Tell us where to find it and why.</p>
      </div>
    </div>
{forms.suggest_form(visible=True)}
  </article>
</main>
{site_footer(forms)}
</body>
</html>
"""


def build_free_bar(forms):
    # "What Is Free?" — the quality bar, in plain words. Derick's copy.
    return f"""<!DOCTYPE html>
<html lang="en" data-mode="playful" data-theme="default">
{head("What Is Free? \\u2014 Actually Free",
      "What \\u201cactually free\\u201d means: no ads, nothing to buy inside the app, no subscriptions, no paid versions.",
      og_path="what-is-free")}
<body>
{site_header()}
<main class="detail">
  <p><a class="back" href="/">&larr; Back to the directory</a></p>
  <article class="detail-card">
    <div class="detail-head">
      <div>
        <h1>What Do We Mean By Free?</h1>
        <p class="cat">Every app listed here has to clear the same bar:</p>
      </div>
    </div>
    <ul>
      <li><strong>No ads.</strong> None. Not a banner, not a pop-up, not a &ldquo;sponsored&rdquo; anything.</li>
      <li><strong>Nothing to buy inside the app.</strong> No extra levels, no coins, no unlocks.</li>
      <li><strong>No subscriptions.</strong> No monthly charges, no free trials that turn into charges.</li>
      <li><strong>No paid versions.</strong> No &ldquo;pro&rdquo; edition with the good features locked away.</li>
      <li><strong>No paid server.</strong> A free client that depends on a paid or subscription service is not free.</li>
    </ul>
    <p>Requesting donations is fine &mdash; as long as everything works whether you donate or not.</p>
    <p>We check app details before listing &mdash; some by hand, some with automated checks &mdash; but we have not installed or tested them all; use caution when installing.</p>
    <p>Anything marked <span class="needs-review">needs &#128064;</span> is still waiting on a human review.</p>
    <p><strong>Why the list is short:</strong> most &ldquo;free&rdquo; apps aren't actually free. They show you ads or sell you things. We'd rather list a few hundred apps we trust than thousands we don't.</p>
    <p>Know an app that belongs here? <a href="/suggest">Suggest it</a>. Spot one that broke the rules? Tell us and we'll pull it.</p>
  </article>
</main>
{site_footer(forms)}
</body>
</html>
"""


def build_sitemap(apps):
    urls = [f"  <url><loc>{SITE_URL}/</loc></url>",
            f"  <url><loc>{SITE_URL}/suggest</loc></url>",
            f"  <url><loc>{SITE_URL}/what-is-free</loc></url>"]
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
  --bg: #fdf4e7;
  --ink: #33241a;
  --muted: #8a6f5c;
  --card: #ffffff;
  --card-edge: #eed7b8;
  --accent: #c2570b;
  --accent-soft: #fce8d2;
  --on-accent: #ffffff;
  --good: #1f9d55;
  --good-soft: #e0f4e8;
  --header-bg: #fff9f0;
  --chip-bg: #f8e6cc;
  --chip-on: #33241a;
  --input-bg: #ffffff;
  --shadow: 0 2px 12px rgba(194, 87, 11, 0.14);
  --radius: 16px;
  --font: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif;
}
@media (prefers-color-scheme: dark) {
  :root:not([data-theme="light"]) {
    --bg: #1a1109;
    --ink: #f7ecda;
    --muted: #caa77f;
    --card: #251810;
    --card-edge: #4d3823;
    --accent: #f0a04b;
    --accent-soft: #3a2413;
    --on-accent: #241708;
    --good: #55c47e;
    --good-soft: #143a24;
    --header-bg: #201309;
    --chip-bg: #33200f;
    --chip-on: #f7ecda;
    --input-bg: #251810;
    --shadow: 0 2px 12px rgba(0, 0, 0, 0.45);
  }
}
:root[data-theme="dark"] {
  --bg: #1a1109;
  --ink: #f7ecda;
  --muted: #caa77f;
  --card: #251810;
  --card-edge: #4d3823;
  --accent: #f0a04b;
  --accent-soft: #3a2413;
  --on-accent: #241708;
  --good: #55c47e;
  --good-soft: #143a24;
  --header-bg: #201309;
  --chip-bg: #33200f;
  --chip-on: #f7ecda;
  --input-bg: #251810;
  --shadow: 0 2px 12px rgba(0, 0, 0, 0.45);
}

* { box-sizing: border-box; }
html, body { overflow-x: clip; } /* no horizontal scrolling, ever */
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
.brand-text strong { font-size: 1.25rem; letter-spacing: 0.2px; color: var(--accent); }
.brand-text em { font-style: normal; font-size: 0.8rem; color: var(--muted); }
/* QR Cards as an Android-style home-screen app icon, next to the switchers */
.qr-appicon {
  margin-left: auto;
  display: flex; flex-direction: column; align-items: center; gap: 2px;
  text-decoration: none; color: var(--ink);
  padding: 4px 8px; border-radius: 12px;
}
.qr-appicon:hover { background: var(--accent-soft); }
.qr-appicon-glyph {
  width: 46px; height: 46px; border-radius: 12px;
  background: #ffffff; border: 1px solid var(--card-edge);
  display: flex; align-items: center; justify-content: center;
  box-shadow: var(--shadow); overflow: hidden;
}
.qr-appicon-glyph svg { width: 36px; height: 36px; display: block; }
.qr-appicon-label { font-size: 0.68rem; font-weight: 600; color: var(--muted); white-space: nowrap; }
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
/* Icon-only theme buttons (FundingSpark's half-circle / sun / moon) */
.switcher.theme-switcher button { padding: 6px 9px; line-height: 0; }
.switcher.theme-switcher button svg { width: 17px; height: 17px; display: block; }
/* ---------- layout ---------- */
main { max-width: 1100px; margin: 0 auto; padding: 20px 16px 48px; }
.hero h1 { font-size: clamp(1.6rem, 4vw, 2.4rem); margin: 0.2em 0 0.1em; }
.tagline { color: var(--muted); font-size: 1.05rem; margin: 0 0 1em; overflow: hidden; }

/* ---------- promise line: checkmarks, no box, breathing room below ---------- */
.promise-line { margin: 20px 0 26px; font-size: 1rem; }
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
#search:focus { outline: 2px solid var(--accent); border-color: var(--accent); }
/* Filter rows never wrap: one row on desktop, horizontal scroll on narrow screens */
.filter-row { display: flex; flex-wrap: nowrap; gap: 8px; margin-bottom: 10px; align-items: center; overflow-x: auto; padding-bottom: 4px; }
.filter-row .chip, .filter-row .pill { flex: 0 0 auto; }
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
.chip.on, .pill.on { background: var(--accent); color: var(--on-accent); border-color: var(--accent); }
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
  grid-template-columns: repeat(auto-fill, minmax(200px, 1fr));
  gap: 14px;
}
.tile {
  display: flex;
  flex-direction: column;
  gap: 8px;
  min-width: 0;
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
.tile-top > span { min-width: 0; }
.icon-wrap {
  width: 52px; height: 52px; flex: 0 0 52px;
  border-radius: 14px;
  overflow: hidden;
  background: linear-gradient(135deg, hsl(var(--accent-h, 210) 70% 88%), hsl(var(--accent-h, 210) 70% 76%));
  border: 2px solid hsl(var(--accent-h, 210) 65% 62%);
  display: flex; align-items: center; justify-content: center;
}
.icon-wrap img { width: 100%; height: 100%; object-fit: cover; }
.icon-wrap svg { width: 100%; height: 100%; display: block; }
.icon-wrap.large { width: 84px; height: 84px; flex-basis: 84px; border-radius: 20px; }
.letter-tile {
  width: 100%; height: 100%;
  align-items: center; justify-content: center;
  font-size: 1.7rem; font-weight: 800;
  color: hsl(var(--accent-h, 210) 60% 30%);
}
.tile h3 { margin: 0; font-size: 1rem; line-height: 1.25; } /* <wbr> word seams only; never an arbitrary mid-word snap */
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
/* "needs review" — same pill shape as store badges, dashed = provisional */
.needs-review {
  font-size: 0.72rem; font-weight: 700;
  padding: 4px 10px;
  border-radius: 999px;
  background: var(--accent-soft);
  color: var(--accent);
  border: 1px dashed var(--accent);
}
.review-note {
  background: var(--accent-soft);
  border: 1px dashed var(--accent);
  border-radius: 12px;
  padding: 12px 16px;
  margin-top: 18px;
}
.review-note h2 { margin: 0 0 6px; }
.review-note p { margin: 0; }
/* "Made by us" sits as a small pill at the top of the tile, clear of the name */
.made-by-us {
  display: inline-block;
  align-self: flex-start;
  background: var(--accent); color: var(--on-accent);
  font-size: 0.68rem; font-weight: 800;
  padding: 3px 10px; border-radius: 999px;
  box-shadow: var(--shadow);
  white-space: nowrap;
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
.detail-head h1 { margin: 0 0 4px; font-size: 1.6rem; display: flex; align-items: center; gap: 8px; flex-wrap: wrap; }
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

/* ---------- ntfy feedback forms ---------- */
.af-form-wrap { margin-top: 12px; }
.af-form {
  background: var(--accent-soft);
  border: 1px solid var(--card-edge);
  border-radius: var(--radius);
  padding: 14px 16px;
  display: flex; flex-direction: column; gap: 10px;
  max-width: 560px;
}
.af-form[hidden] { display: none; }
.af-form-head { margin: 0; font-size: 0.95rem; }
.af-field { display: flex; flex-direction: column; gap: 6px; font-size: 0.9rem; font-weight: 600; }
.af-field input, .af-field textarea {
  font: inherit; font-weight: 400;
  padding: 9px 12px; border-radius: 10px;
  border: 1px solid var(--card-edge);
  background: var(--input-bg); color: var(--ink);
  width: 100%;
}
.af-field textarea { resize: vertical; }
.af-trap { position: absolute; left: -9999px; width: 1px; height: 1px; overflow: hidden; }
.af-error { color: #c0392b; font-size: 0.88rem; margin: 0; }
.af-error:empty { display: none; }
.af-actions { display: flex; gap: 8px; flex-wrap: wrap; }
.af-actions button {
  font: inherit; font-size: 0.88rem; font-weight: 700;
  padding: 9px 16px; border-radius: 999px; cursor: pointer;
  border: 1px solid var(--accent); background: var(--accent); color: var(--on-accent);
}
.af-actions button[data-af-cancel] { background: transparent; color: var(--ink); border-color: var(--card-edge); }
.af-thanks { font-weight: 600; color: var(--good); }
.feedback-off { color: var(--muted); font-style: italic; }

/* ---------- footer ---------- */
.site-footer { border-top: 1px solid var(--card-edge); background: var(--header-bg); }
.footer-inner { max-width: 1100px; margin: 0 auto; padding: 24px 16px 32px; }
.about { max-width: 640px; color: var(--muted); font-size: 0.92rem; }
.fine-print { max-width: 640px; color: var(--muted); font-size: 0.85rem; }
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
  --on-accent: #00001a;
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
:root[data-mode="geek"] .needs-review { border-radius: 0; }
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
:root[data-mode="geek"] .af-form { border-radius: 0; border: 2px outset #5a5ac8; }
:root[data-mode="geek"] .af-field input, :root[data-mode="geek"] .af-field textarea { border-radius: 0; }
:root[data-mode="geek"] .af-actions button { border-radius: 0; }
:root[data-mode="geek"] .chip.on, :root[data-mode="geek"] .pill.on {
  background: var(--chip-on); color: #00001a; border: 2px inset #5a5ac8;
}
:root[data-mode="geek"] .qr-appicon-glyph { border-radius: 0; }
:root[data-mode="geek"] .qr-appicon:hover { background: var(--accent-soft); }
:root[data-mode="geek"] .switcher { border-radius: 0; }
:root[data-mode="geek"] .switcher button.on { background: #ffe97a; color: #000; }

/* ============ Geek light theme: classic daytime 2000s web ============
   NOTE: the geek skin declares its palette variables on `body`, so the
   light overrides must live on `body` too — :root-level vars lose to the
   nearer body scope for every card and field. */
:root[data-mode="geek"][data-theme="light"] body {
  background-color: #c9c9e8;
  background-image: none;
  color: #1a1a4d;
  --bg: #c9c9e8;
  --ink: #1a1a4d;
  --muted: #4d4d8c;
  --card: #f2f2fb;
  --card-edge: #8c8cc9;
  --accent: #0000cc;
  --accent-soft: #dadaf5;
  --good: #0a7a2e;
  --good-soft: #d9f0de;
  --header-bg: #b3b3da;
  --chip-bg: #e0e0f4;
  --chip-on: #0000cc;
  --input-bg: #ffffff;
  --shadow: none;
  --on-accent: #ffffff;
}
:root[data-mode="geek"][data-theme="light"] .brand-text strong,
:root[data-mode="geek"][data-theme="light"] .hero h1 { color: #5a4a00; }
:root[data-mode="geek"][data-theme="light"] .marquee-text { color: #0000cc; }
:root[data-mode="geek"][data-theme="light"] .chip.on,
:root[data-mode="geek"][data-theme="light"] .pill.on { color: #ffffff; }
/* theme=default follows the system in geek mode too */
@media (prefers-color-scheme: light) {
  :root[data-mode="geek"]:not([data-theme="dark"]) body {
    background-color: #c9c9e8;
    background-image: none;
    color: #1a1a4d;
    --bg: #c9c9e8;
    --ink: #1a1a4d;
    --muted: #4d4d8c;
    --card: #f2f2fb;
    --card-edge: #8c8cc9;
    --accent: #0000cc;
    --accent-soft: #dadaf5;
    --good: #0a7a2e;
    --good-soft: #d9f0de;
    --header-bg: #b3b3da;
    --chip-bg: #e0e0f4;
    --chip-on: #0000cc;
    --input-bg: #ffffff;
    --shadow: none;
    --on-accent: #ffffff;
  }
  :root[data-mode="geek"]:not([data-theme="dark"]) .brand-text strong,
  :root[data-mode="geek"]:not([data-theme="dark"]) .hero h1 { color: #5a4a00; }
  :root[data-mode="geek"]:not([data-theme="dark"]) .marquee-text { color: #0000cc; }
  :root[data-mode="geek"]:not([data-theme="dark"]) .chip.on,
  :root[data-mode="geek"]:not([data-theme="dark"]) .pill.on { color: #ffffff; }
}

/* ---------- desktop refinements ---------- */
@media (min-width: 641px) {
  /* Playful desktop: the tagline repeats the hero heading, so it goes. Geek keeps it — classic. */
  :root[data-mode="playful"] .hero .tagline { display: none; }
}

@media (max-width: 640px) {
  /* The toggle column stacks so the header grows vertically instead of
     scrolling horizontally — horizontal scroll is never acceptable. */
  .header-inner { gap: 10px; flex-wrap: wrap; }
  /* Toggles share the row with the brand, stacked: mode toggle above, theme
     toggle below. (The QR icon is desktop-only now, so it all fits.) */
  .switchers { flex-direction: column; align-items: flex-end; gap: 6px; margin-left: auto; }
  .qr-appicon { display: none; } /* the QR Cards icon lives in the desktop header only */
  .brand-text em { display: none; } /* tagline hides on phones to save vertical room */
  .brand-text strong { font-size: 1.05rem; }
  .brand img { width: 44px; height: 44px; }
  .grid { grid-template-columns: repeat(auto-fill, minmax(160px, 1fr)); gap: 10px; }
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
  var MASCOTS = { playful: "/assets/mascot-friendly.webp", geek: "/assets/mascot-geek.webp" };
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

  /* ---------- ntfy feedback ------------------------------------------------
     The browser POSTs straight to ntfy.sh — no backend, no relay, no email.
     The topic is XOR-obfuscated per build: base64 in each form's data-t,
     the key (__NTFY_KEY__, replaced at build time) embedded separately,
     decoded only at send time. Anti-spam, all client-side: honeypot trap,
     3-second open rule, 3-per-10-minutes / 10-per-day limits, length caps.
     Same pattern as FundingSpark. */
  (function () {
    "use strict";
    var K = "__NTFY_KEY__";
    var API = "https://ntfy.sh/", STORE = "af.sends";
    var MIN_OPEN_MS = 3000, BURST = 3, BURST_MS = 600000,
        DAY = 10, DAY_MS = 86400000, BODY_BYTES = 3500;
    var memory = [];
    var REASONS = {
      "doesnt-work": "Doesn't work",
      "broke-promise": "Broke a promise",
      "correction": "Suggest a correction"
    };
    function unb64(s) {
      var t = atob(s), a = [];
      for (var i = 0; i < t.length; i++) a.push(t.charCodeAt(i));
      return a;
    }
    function topic(form) {
      var t = form.getAttribute("data-t");
      if (!t || !K) return "";
      var d = unb64(t), k = unb64(K), o = [];
      for (var i = 0; i < d.length; i++) o.push(d[i] ^ k[i % k.length]);
      return new TextDecoder().decode(new Uint8Array(o));
    }
    // Plain text only: strip control characters, cut at max characters.
    function clean(s, max, multi) {
      s = String(s || "").replace(/\r\n?/g, "\n");
      s = multi ? s.replace(/[\u0000-\u0008\u000b-\u001f\u007f-\u009f\u2028\u2029]/g, "")
                : s.replace(/[\u0000-\u001f\u007f-\u009f\u2028\u2029]/g, " ");
      return Array.from(s.trim()).slice(0, max).join("");
    }
    function cutBytes(s, n) {
      var enc = new TextEncoder();
      if (enc.encode(s).length <= n) return s;
      var chars = Array.from(s);
      while (chars.length && enc.encode(chars.join("")).length > n - 20)
        chars.length = Math.max(0, chars.length - 20);
      return chars.join("") + "\n[note shortened]";
    }
    function header(s) {   // header values must be Latin-1: the rest goes as RFC 2047 UTF-8
      return /^[\x20-\x7e]*$/.test(s) ? s
        : "=?UTF-8?B?" + btoa(unescape(encodeURIComponent(s))) + "?=";
    }
    function sends() {
      try {
        var v = JSON.parse(localStorage.getItem(STORE) || "[]");
        if (Array.isArray(v)) memory = v.filter(isFinite);
      } catch (e) { /* storage blocked */ }
      return memory;
    }
    function record(now) {
      memory = sends().filter(function (t) { return now - t < DAY_MS; });
      memory.push(now);
      try { localStorage.setItem(STORE, JSON.stringify(memory)); } catch (e) {}
    }
    function limited(now) {
      var l = sends();
      if (l.filter(function (t) { return now - t < DAY_MS; }).length >= DAY)
        return "You've reached today's limit for sending reports from this browser. Try again tomorrow.";
      if (l.filter(function (t) { return now - t < BURST_MS; }).length >= BURST)
        return "You've sent a few reports just now. Wait a few minutes and try again.";
      return "";
    }
    function val(form, name, max, multi) {
      var f = form.elements[name];
      return f ? clean(f.value, max, multi) : "";
    }
    function build(form) {
      var sent = new Date().toISOString().replace(/\.\d+Z$/, "Z"), m = {};
      if (form.getAttribute("data-af-form") === "suggest") {
        m.title = "App suggestion";
        m.tags = ["actually-free", "suggestion"];
        m.priority = "3";
        m.lines = ["App: " + val(form, "app_name", 200),
                   "Link: " + (val(form, "app_link", 300) || "(not given)"),
                   "Why free: " + (val(form, "note", 1000, true) || "(none)"),
                   "Page: " + val(form, "page_url", 300),
                   "Sent: " + sent];
      } else {
        var reason = val(form, "reason", 40);
        var label = REASONS[reason] || REASONS["doesnt-work"];
        var tag = reason === "broke-promise" ? "broke-promise"
                : reason === "correction" ? "correction" : "doesnt-work";
        var appName = val(form, "app_name", 200);
        m.title = label + ": " + appName;
        m.tags = ["actually-free", "feedback", tag];
        m.priority = tag === "broke-promise" ? "4" : "3";
        m.lines = ["App: " + appName,
                   "Page URL: " + val(form, "page_url", 300),
                   "Note: " + (val(form, "note", 1000, true) || "(none)"),
                   "Sent: " + sent];
      }
      m.title = clean(m.title, 200);
      m.body = cutBytes(m.lines.join("\n"), BODY_BYTES);
      return m;
    }
    function bind(form) {
      var wrap = form.parentNode,
          done = wrap.querySelector("[data-af-done]"),
          err = form.querySelector("[data-error]"),
          btn = form.querySelector("button[type=submit]"),
          opened = Date.now();
      function finish() {
        form.reset(); form.hidden = true;
        if (done) {
          done.hidden = false;
          var t = done.querySelector(".af-thanks");
          if (t) t.focus();
        }
      }
      form.addEventListener("af-open", function () {
        form.reset();
        if (done) done.hidden = true;
        err.textContent = "";
        opened = Date.now();
        form.hidden = false;
      });
      form.addEventListener("submit", function (e) {
        e.preventDefault();
        if (btn.disabled) return;
        err.textContent = "";
        var kind = form.getAttribute("data-af-form");
        if (kind === "suggest" && !val(form, "app_name", 200)) {
          err.textContent = "Give the app a name so we know what to look at.";
          return;
        }
        if (kind === "report" && !val(form, "note", 1000, true)) {
          err.textContent = "Write a short note so we know what to check.";
          return;
        }
        if (form.elements.website && form.elements.website.value) { finish(); return; }  // a bot: fake success, send nothing
        var now = Date.now();
        if (now - opened < MIN_OPEN_MS) {
          err.textContent = "Take a moment to check your note, then press Send again.";
          return;
        }
        var limit = limited(now);
        if (limit) { err.textContent = limit; return; }
        var t = topic(form);
        if (!t) { err.textContent = "Feedback is not available yet."; return; }
        var m = build(form);
        btn.disabled = true;
        record(now);
        fetch(API + encodeURIComponent(t), {
          method: "POST", body: m.body,
          headers: { "Title": header(m.title), "Tags": m.tags.join(","), "Priority": m.priority }
        })
          .then(function (r) {
            if (!r.ok) throw new Error("status " + r.status);
            gcEvent("feedback-sent/" + kind);
            finish();
          })
          .catch(function () {
            err.textContent = "That didn't go through. Try again in a minute.";
          })
          .then(function () { btn.disabled = false; });
      });
      var cancels = form.querySelectorAll("[data-af-cancel]");
      for (var i = 0; i < cancels.length; i++) {
        cancels[i].addEventListener("click", function () {
          form.reset(); form.hidden = true;
        });
      }
    }
    var forms = document.querySelectorAll("form[data-af-form]");
    for (var n = 0; n < forms.length; n++) bind(forms[n]);

    /* report buttons on detail pages: pick the reason, reveal the form */
    var rbtns = document.querySelectorAll("[data-feedback]");
    for (var b = 0; b < rbtns.length; b++) {
      rbtns[b].addEventListener("click", function () {
        var scope = this.closest("main") || document;
        var form = scope.querySelector("form[data-af-form=report]");
        if (!form) return;
        form.dispatchEvent(new CustomEvent("af-open"));  // resets + reveals; set reason after
        form.elements.reason.value = this.getAttribute("data-feedback");
        var lbl = form.querySelector("[data-reason-label]");
        if (lbl) lbl.textContent = this.getAttribute("data-label");
        if (form.elements.note) form.elements.note.focus();
      });
    }

  })();

  /* ---------- random app (geek webring) -------------------------------------- */
  var randomBtn = document.getElementById("random-app");
  if (randomBtn) {
    /* Random always lands on an app detail page — never the directory. On
       detail pages the app list isn't loaded yet, so fetch it on demand. */
    randomBtn.addEventListener("click", function () {
      function go(apps) {
        if (!apps || !apps.length) return;
        var a = apps[Math.floor(Math.random() * apps.length)];
        location.href = "/app/" + a.slug + ".html";
      }
      if (state && state.apps.length) { go(state.apps); }
      else {
        fetch("/data/apps.json").then(function (r) { return r.json(); })
          .then(go).catch(function () {});
      }
    });
  }

  /* ---------- directory grid ------------------------------------------------- */
  var grid = document.getElementById("grid");
  if (!grid) return; // not the directory page

  var state = { apps: [], query: "", cat: "", attrs: {}, stores: {}, sort: "name" };
  var ACCENTS = { "Utilities": 210, "Media": 280, "Comms": 160, "Games": 0 };

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
      /* Typo budget scales with token length: a flat distance of 2 lets a
         4-letter query like "food" match "for" (91 apps!), "from", "fork",
         "foss"... Short tokens get 1, longer ones keep 2. */
      var budget = qt.length <= 4 ? 1 : 2;
      return hayTokens.some(function (ht) { return levenshtein(qt, ht) <= budget; });
    });
  }

  function escHtml(s) {
    return String(s == null ? "" : s).replace(/[&<>"']/g, function (c) {
      return { "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c];
    });
  }
  function storeBadges(app) {
    var out = [];
    var defs = [["fdroid", "F-Droid", app.stores.fdroid ? "https://f-droid.org/en/packages/" + app.package + "/" : null],
                ["izzy", "IzzyOnDroid", app.stores.izzy],
                ["openapk", "OpenAPK", app.stores.openapk],
                ["play", "Play", app.stores.play],
                ["github", "GitHub", app.stores.github]];
    defs.forEach(function (d) {
      if (d[2]) out.push('<span class="store-badge">' + d[1] + "</span>");
    });
    return out.join("");
  }
  /* Word-boundary wrap opportunities for tile titles: <wbr> at camelCase /
     PascalCase / acronym seams ("AntennaPod" -> "Antenna|<wbr>Pod"), plus
     explicit seams for compound words with no case boundary ("Minesweeper"
     -> "Mine|<wbr>sweeper"). Applied after HTML-escaping (escaping never
     touches ASCII letters, so positions are stable). */
  var WBR_WORDS = {
    "minesweeper": "Mine<wbr>sweeper",
    "lawnchair": "Lawn<wbr>chair",
    "nextcloud": "Next<wbr>cloud",
    "personaldnsfilter": "personal<wbr>DNS<wbr>filter",
    "authenticator": "Authen<wbr>ticator",
    "messenger": "Messen<wbr>ger",
    "minimalist": "Mini<wbr>malist",
    "phonograph": "Phono<wbr>graph",
    "audiobook": "Audio<wbr>book",
    "pedometer": "Pedo<wbr>meter",
    "syncthing": "Sync<wbr>thing"
  };
  function wbrify(rawName) {
    /* Per word: explicit seams win, else camelCase/PascalCase/acronym seams.
       Escaping per word keeps positions stable (escHtml never touches the
       ASCII letters the patterns match). */
    return rawName.split(/([\s\-]+)/).map(function (word) {
      if (!/\S/.test(word)) return word;
      var low = word.toLowerCase();
      if (WBR_WORDS[low]) return WBR_WORDS[low];
      return escHtml(word).replace(/(?<=[a-z0-9])(?=[A-Z])|(?<=[A-Z])(?=[A-Z][a-z])/g, "<wbr>");
    }).join("");
  }

  function tile(app) {
    var accent = ACCENTS[app.category] != null ? ACCENTS[app.category] : 210;
    var letter = escHtml(app.name.charAt(0).toUpperCase());
    var iconHtml;
    if (app.icon_svg) {
      iconHtml = '<span class="icon-wrap">' + app.icon_svg + "</span>";
    } else if (app.icon) {
      iconHtml = '<span class="icon-wrap">' +
        '<img src="/' + escHtml(app.icon) + '" alt="" loading="lazy" onerror="this.style.display=\'none\';this.nextElementSibling.style.display=\'flex\'">' +
        '<span class="letter-tile" style="display:none">' + letter + "</span></span>";
    } else {
      iconHtml = '<span class="icon-wrap">' +
        '<span class="letter-tile" style="display:flex">' + letter + "</span></span>";
    }
    var rating = app.rating ? '<p class="rating">\u2605 ' + escHtml(app.rating) + "</p>" : "";
    var ribbon = app.made_by_us ? '<span class="made-by-us">Made by us</span>' : "";
    var needsBadge = app.needs_review ? '<span class="needs-review">needs 👀</span>' : "";
    return '<a class="tile" style="--accent-h:' + accent + '" href="/app/' + escHtml(app.slug) +
      '.html" data-slug="' + escHtml(app.slug) + '">' + ribbon +
      '<span class="tile-top">' + iconHtml +
      "<span><h3>" + wbrify(app.name) + "</h3>" +
      '<p class="sub">' + escHtml(app.subcategory || app.category) + "</p></span></span>" +
      rating +
      '<p class="desc">' + escHtml(app.description) + "</p>" +
      '<span class="badges">' + storeBadges(app) + needsBadge + "</span>" +
      '<span class="verified">\u2713 Verified actually-free</span></a>';
  }

  function filtered() {
    var q = norm(state.query);
    var list = state.apps.filter(function (app) {
      if (state.cat && app.category !== state.cat) return false;
      for (var k in state.attrs) {
        if (k === "made_by_us") { if (!app.made_by_us) return false; }
        else if (k === "reviewed") { if (app.needs_review) return false; }
        else if (!app.attrs[k]) return false;
      }
      for (var s in state.stores) {
        if (s === "play" && !app.stores.play) return false;
        else if (s === "fdroid" && !app.stores.fdroid) return false;
        else if (s === "izzy" && !app.stores.izzy) return false;
        else if (s === "github" && !app.stores.github) return false;
        else if (s === "openapk" && !app.stores.openapk) return false;
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
      var filtering = r.q || state.cat || Object.keys(state.attrs).length ||
                      Object.keys(state.stores).length;
      count.textContent = filtering
        ? r.list.length + " of " + total + " actually-free apps"
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
  document.querySelectorAll("[data-attr]").forEach(function (p) {
    p.addEventListener("click", function () {
      var k = p.getAttribute("data-attr");
      if (state.attrs[k]) delete state.attrs[k]; else state.attrs[k] = true;
      p.classList.toggle("on", !!state.attrs[k]);
      gcEvent("filter/" + k);
      render();
    });
  });
  document.querySelectorAll("[data-store]").forEach(function (p) {
    p.addEventListener("click", function () {
      var k = p.getAttribute("data-store");
      if (state.stores[k]) delete state.stores[k]; else state.stores[k] = true;
      p.classList.toggle("on", !!state.stores[k]);
      gcEvent("store/" + k);
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

CONFIG_JS_TEMPLATE = """/* Actually Free — site configuration.
   GOATCOUNTER_CODE: your Goatcounter site code (the subdomain part of your
   Goatcounter URL). Free signup at https://www.goatcounter.com — no API key
   needed. Until this is set, analytics are skipped silently.

   Feedback reports ("doesn't work" / "broke a promise" / corrections /
   app suggestions) go to ntfy.sh — free tier, no account, no backend. The
   topic is NOT stored here: generate.py reads it from the AF_NTFY_TOPIC
   environment variable or ~/.config/actually-free/ntfy-topic, XOR-obfuscates
   it with a fresh random key on every build, and embeds only base64 blobs in
   the pages. Subscribe to the topic in the ntfy app (Android) or at ntfy.sh
   to receive reports; the free tier keeps messages ~12 hours. */
window.AF_CONFIG = {{
  GOATCOUNTER_CODE: "{gc}"
}};
"""


def build_config_js():
    """config.js for the deployed site: Goatcounter code preserved, and the
    ntfy topic deliberately NOT stored here (see the ntfy section above)."""
    gc = ""
    try:
        with open(os.path.join(HERE, "assets", "config.js"), encoding="utf-8") as f:
            m = re.search(r'GOATCOUNTER_CODE\s*:\s*"([^"]*)"', f.read())
            if m:
                gc = m.group(1)
    except OSError:
        pass
    return CONFIG_JS_TEMPLATE.format(gc=gc or "PASTE-YOUR-CODE-HERE")

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
3. **Paste your Goatcounter code** into `assets/config.js` (`GOATCOUNTER_CODE`)
   and redeploy.
4. **Feedback via ntfy** (free tier, no account, no backend): save the secret
   topic to `~/.config/actually-free/ntfy-topic` on the build machine (one
   line, no quotes), or set the `AF_NTFY_TOPIC` env var, then regenerate.
   `generate.py` XOR-obfuscates the topic with a fresh random key on every
   build — it never appears in page source as plaintext. Subscribe to the
   topic in the ntfy app (Android) or at ntfy.sh to receive the reports;
   the free tier keeps messages ~12 hours. Without a topic, the feedback
   forms are replaced by a "not available yet" notice.

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


def build_pwa_icons():
    """192/512 PNG icons + a padded maskable 512, from the friendly mascot."""
    from PIL import Image
    src = Image.open(os.path.join(HERE, "assets", "mascot-friendly.webp")).convert("RGBA")
    icon192 = src.resize((192, 192), Image.LANCZOS)
    icon192.save(os.path.join(HERE, "assets", "icon-192.png"))
    icon512 = src.resize((512, 512), Image.LANCZOS)
    icon512.save(os.path.join(HERE, "assets", "icon-512.png"))
    # maskable: mascot at 72% on the site's light background so edges survive the mask
    canvas = Image.new("RGBA", (512, 512), "#fdf4e7")
    inner = src.resize((368, 368), Image.LANCZOS)
    canvas.alpha_composite(inner, (72, 72))
    canvas.save(os.path.join(HERE, "assets", "icon-maskable-512.png"))


MANIFEST = """{
  "name": "Actually Free",
  "short_name": "Actually Free",
  "description": "A hand-curated directory of Android apps that are actually free: no ads, no in-app purchases, no subscriptions.",
  "start_url": "/",
  "scope": "/",
  "display": "standalone",
  "orientation": "portrait",
  "background_color": "#fdf4e7",
  "theme_color": "#fdf4e7",
  "icons": [
    {"src": "/assets/icon-192.png", "sizes": "192x192", "type": "image/png"},
    {"src": "/assets/icon-512.png", "sizes": "512x512", "type": "image/png"},
    {"src": "/assets/icon-maskable-512.png", "sizes": "512x512", "type": "image/png", "purpose": "maskable"}
  ]
}
"""


def build_sw(build_id):
    """Cache-first service worker: installed pages work offline."""
    return f"""// Actually Free service worker — build {build_id}
const CACHE = "actually-free-{build_id}";
const PRECACHE = [
  "/", "/suggest", "/what-is-free", "/manifest.webmanifest",
  "/assets/styles.css", "/assets/app.js", "/assets/config.js",
  "/assets/icon-192.png", "/assets/icon-512.png"
];
self.addEventListener("install", (e) => {{
  e.waitUntil(caches.open(CACHE).then((c) => c.addAll(PRECACHE)).then(() => self.skipWaiting()));
}});
self.addEventListener("activate", (e) => {{
  e.waitUntil(
    caches.keys()
      .then((keys) => Promise.all(keys.filter((k) => k !== CACHE).map((k) => caches.delete(k))))
      .then(() => self.clients.claim())
  );
}});
self.addEventListener("fetch", (e) => {{
  const u = new URL(e.request.url);
  if (e.request.method !== "GET" || u.origin !== self.location.origin) return;
  e.respondWith(
    caches.match(e.request).then((hit) => {{
      if (hit) return hit;
      return fetch(e.request).then((res) => {{
        const copy = res.clone();
        caches.open(CACHE).then((c) => c.put(e.request, copy));
        return res;
      }}).catch(() => caches.match("/"));
    }})
  );
}});
"""


def apply_openapk(apps):
    """Attach OpenAPK listing URLs (from the cross-reference mapping) to apps."""
    path = os.path.join(HERE, "hidden-openapk-mapping.json")
    try:
        with open(path, encoding="utf-8") as f:
            mapping = {e["slug"]: e["openapk_url"] for e in json.load(f)}
    except (OSError, ValueError, KeyError):
        print("openapk: no mapping file, skipping")
        return
    n = 0
    for app in apps:
        url = mapping.get(app["slug"])
        if url:
            app["stores"]["openapk"] = url
            n += 1
    print(f"openapk: {n} apps linked")


GENERIC_SUBCATS = {"Tools", "Other", "General", "Misc", "Miscellaneous"}


def taxonomy_report(apps):
    """Build-time taxonomy health: per-category counts, plus loud (non-failing)
    warnings when a top-level category gets bloated or an app lands in a
    generic bucket. Keeps category bloat visible on every build."""
    counts = Counter(a["category"] for a in apps)
    print("taxonomy:")
    for cat, n in counts.most_common():
        print(f"  {cat}: {n}")
    for cat, n in counts.most_common():
        if n > 80:
            print(f"  WARNING: '{cat}' has {n} apps (over 80) - consider splitting it")
    for a in apps:
        if a.get("subcategory") in GENERIC_SUBCATS or "/" in a.get("category", ""):
            print(f"  WARNING: '{a['name']}' sits in a generic bucket "
                  f"({a['category']} / {a['subcategory']})")


def main():
    apps = load_corpus()
    categories = sorted({a["category"] for a in apps})
    print(f"{len(apps)} apps "
          f"({sum(1 for a in apps if a['made_by_us'])} made by us, "
          f"{sum(1 for a in apps if a['per_badge'])} per-badge)")

    topic = read_ntfy_topic()
    if topic:
        persist_ntfy_topic(topic)
        print("ntfy feedback: topic configured (XOR-obfuscated per build)")
    else:
        print("ntfy feedback: NO TOPIC SET — forms show 'not available yet'")
    forms = NtfyForms(topic)

    apply_openapk(apps)
    write("data/apps.json", json.dumps(apps, indent=1, ensure_ascii=False) + "\n")
    write("index.html", build_index(apps, categories, forms))
    write("suggest.html", build_suggest(forms))
    write("what-is-free.html", build_free_bar(forms))
    for app in apps:
        write(f"app/{app['slug']}.html", build_detail(app, forms))
    write("sitemap.xml", build_sitemap(apps))
    write("robots.txt", ROBOTS)
    write("assets/styles.css", CSS_CONTENT.strip() + "\n")
    app_js = JS_CONTENT.replace("__NTFY_KEY__", forms.key_b64)
    if "__NTFY_KEY__" in app_js:
        print("warning: ntfy key placeholder survived replacement")
    write("assets/app.js", app_js.strip() + "\n")
    write("assets/config.js", build_config_js())
    build_pwa_icons()
    build_id = datetime.datetime.now(datetime.timezone.utc).strftime("%Y%m%d%H%M")
    write("manifest.webmanifest", MANIFEST)
    write("sw.js", build_sw(build_id))
    print("pwa: manifest, sw.js (%s), icons" % build_id)
    write("README.md", build_readme())
    print("done: index, %d detail pages, sitemap, robots, assets, README"
          % len(apps))
    taxonomy_report(apps)


if __name__ == "__main__":
    main()
