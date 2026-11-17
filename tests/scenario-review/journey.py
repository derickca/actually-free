#!/usr/bin/env python3
"""journey — the Scenario Review journeys (issue #28).

The scenario contract stands in docs/E2E.md, in the order a
person lives it. This file is that contract as walks: each
journey is a visitor's path through the public directory —
the app has no accounts, so no person's data stands in any
of them — driven on the rig through drive.py.

A journey returns { id, verdict, checks } in the shape the
results reporter seam (tools/reporter.py) shapes: a check
is { id, ok }, and the seam names it "<journey>:<check>" on
the wire, so check ids here are short plain phrases that
meet the store's name shape. A journey whose walk cannot
start at all comes back NOT-RUN with no checks; a journey
that walks and finds a step wanting comes back FAIL with
the step's check False. Detail a check carries stays in
the run's local record, never on the wire.
"""

import drive

# The six promises the What is free page names, as the
# contract's third journey checks for them.
SIX_PROMISES = ("No ads", "No in-app purchases", "No subscriptions",
                "No trials", "No nagging", "No surprise bundles")


def _result(journey_id, checks, walked_pages):
    verdict = "PASS" if all(c["ok"] for c in checks) else "FAIL"
    return {"id": journey_id, "verdict": verdict, "checks": checks,
            "pages": walked_pages}


def _not_run(journey_id):
    return {"id": journey_id, "verdict": "NOT-RUN", "checks": [],
            "pages": []}


def _check(check_id, outcome, key):
    entry = (outcome.get("checks") or {}).get(key) or {}
    return {"id": check_id, "ok": bool(entry.get("ok")),
            "detail": entry.get("detail", "")}


CORE_HOME_WALK = r"""
await waitFor(function () {
  return document.querySelectorAll("#grid .tile").length > 0;
}, 20000, "the catalogue grid");
var out = window.__srOut;
out.checks = { grid: { ok: true, detail:
  document.getElementById("result-count").textContent.trim() } };

var seg = document.querySelector(
  '#platform-seg [data-platform="android"]');
seg.click();
await waitFor(function () {
  return seg.classList.contains("on") &&
    document.querySelectorAll("#grid .tile").length > 0;
}, 15000, "the Android platform filter");
var tags = Array.prototype.map.call(
  document.querySelectorAll("#grid .tile .platform-tag"),
  function (e) { return e.getAttribute("aria-label"); });
out.checks.platform = {
  ok: tags.length > 0 && tags.every(function (t) {
    return t === "Android app"; }),
  detail: tags.length + " tiles shown" };

var chip = document.querySelector(
  '#category-chips .chip[data-cat]:not([data-cat=""])');
if (!chip) throw new Error("no category chip stands");
out.category = chip.getAttribute("data-cat");
chip.click();
await waitFor(function () {
  return chip.classList.contains("on") &&
    document.querySelectorAll("#grid .tile").length > 0;
}, 15000, "the category filter");
var count = document.getElementById("result-count")
  .textContent.trim();
out.checks.category = { ok: / of /.test(count),
  detail: count + " in " + out.category };

var tile = document.querySelector("#grid .tile");
out.tileHref = tile.getAttribute("href");
out.tileName = tile.querySelector("h3").textContent.trim();
"""

LISTING_WALK = r"""
await waitFor(function () {
  return document.querySelector("h1") &&
    document.querySelector("h1").textContent.trim().length > 0;
}, 15000, "the listing's name");
var out = window.__srOut;
out.checks = { name: { ok: true, detail:
  document.querySelector("h1").textContent.trim() } };
var link = document.querySelector(
  'a.store-badge[href^="https://"], a.store-badge[href^="http://"]');
out.checks.link = { ok: !!link,
  detail: link ? link.getAttribute("href") : "no store link stands" };
"""

SUGGEST_WALK = r"""
await waitFor(function () {
  return document.querySelector("h1") &&
    document.querySelector("h1").textContent.trim().length > 0;
}, 15000, "the Suggest page heading");
var out = window.__srOut;
var form = document.querySelector('form[data-af-form="suggest"]');
var fields = form ? form.querySelectorAll(
  'input[name="app_name"], input[name="app_link"], ' +
  'textarea[name="note"]') : [];
var submit = form ? form.querySelector(
  'button[type="submit"], input[type="submit"]') : null;
out.checks = {
  renders: { ok: true, detail:
    document.querySelector("h1").textContent.trim() },
  form: { ok: !!form && fields.length === 3,
    detail: form ? fields.length + " fields stand"
                 : "no suggest form stands" },
  submit: { ok: !!submit,
    detail: submit ? "the form's submit control stands"
                   : "no submit control stands" }
};
"""

WHAT_IS_FREE_WALK = r"""
await waitFor(function () {
  return document.body &&
    document.body.textContent.indexOf("No ads") !== -1;
}, 15000, "the promises on the page");
var out = window.__srOut;
var text = document.body.textContent;
var promises = __PROMISES__;
var missing = promises.filter(function (p) {
  return text.indexOf(p) === -1; });
out.checks = {
  renders: { ok: !!document.querySelector("h1"),
    detail: document.querySelector("h1")
      ? document.querySelector("h1").textContent.trim() : "" },
  promises: { ok: missing.length === 0,
    detail: missing.length ? "missing: " + missing.join(", ")
                           : "all six promises named" }
};
"""


def journey_core(rig_root, base_url):
    """Core journey — find an app and reach its download:
    land on the home page, choose a platform, filter by a
    category, open a listing, and the listing's store or
    download link stands on its page."""
    try:
        home = drive.probe(rig_root, base_url, "/", CORE_HOME_WALK)
    except Exception:
        return _not_run("core")
    checks = [
        _check("home renders the catalogue grid", home, "grid"),
        _check("platform filter narrows the grid", home, "platform"),
        _check("category filter narrows the grid", home, "category"),
    ]
    pages = ["/"]
    tile_href = home.get("tileHref")
    if not tile_href:
        checks.append({"id": "listing opens from the grid",
                       "ok": False, "detail": "no tile stood"})
        checks.append({"id": "listing carries a store or download link",
                       "ok": False, "detail": "no listing was opened"})
        return _result("core", checks, pages)
    try:
        listing = drive.probe(rig_root, base_url, tile_href,
                              LISTING_WALK)
    except Exception:
        checks.append({"id": "listing opens from the grid",
                       "ok": False, "detail": "the listing never loaded"})
        checks.append({"id": "listing carries a store or download link",
                       "ok": False, "detail": "no listing was opened"})
        return _result("core", checks, pages)
    pages.append(tile_href)
    name_check = _check("listing opens from the grid", listing, "name")
    tile_name = (home.get("tileName") or "").strip()
    if tile_name and name_check["detail"].strip() != tile_name:
        name_check["ok"] = False
        name_check["detail"] = (
            f"the page names {name_check['detail'].strip()!r}, "
            f"the tile named {tile_name!r}")
    checks.append(name_check)
    checks.append(_check("listing carries a store or download link",
                         listing, "link"))
    return _result("core", checks, pages)


def journey_suggest(rig_root, base_url):
    """Suggest an app: the Suggest page renders and its
    form stands."""
    try:
        out = drive.probe(rig_root, base_url, "/suggest", SUGGEST_WALK)
    except Exception:
        return _not_run("suggest")
    checks = [
        _check("suggest page renders", out, "renders"),
        _check("suggest form stands", out, "form"),
        _check("suggest form can be sent", out, "submit"),
    ]
    return _result("suggest", checks, ["/suggest"])


def journey_what_is_free(rig_root, base_url):
    """Read what free means: the What is free page renders
    and names the six promises."""
    # The walk's promise list rides as a JS array literal.
    walk = WHAT_IS_FREE_WALK.replace(
        "__PROMISES__",
        "[" + ", ".join(f'"{p}"' for p in SIX_PROMISES) + "]")
    try:
        out = drive.probe(rig_root, base_url, "/what-is-free", walk)
    except Exception:
        return _not_run("what-is-free")
    checks = [
        _check("what is free page renders", out, "renders"),
        _check("page names the six promises", out, "promises"),
    ]
    return _result("what-is-free", checks, ["/what-is-free"])


# The contract's journeys, in the order a person lives them.
JOURNEYS = (
    ("core", journey_core),
    ("suggest", journey_suggest),
    ("what-is-free", journey_what_is_free),
)
