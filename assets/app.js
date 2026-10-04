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
