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
     the key (yLeI01XugoQ5BJYoxbIO/w==, replaced at build time) embedded separately,
     decoded only at send time. Anti-spam, all client-side: honeypot trap,
     3-second open rule, 3-per-10-minutes / 10-per-day limits, length caps.
     Same pattern as FundingSpark. */
  (function () {
    "use strict";
    var K = "yLeI01XugoQ5BJYoxbIO/w==";
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

  var state = { apps: [], query: "", cat: "", subcat: "", attrs: {}, stores: {}, sort: "name" };
  var ACCENTS = { "Utilities": 210, "Media": 280, "Games": 0, "Communications": 160, "Lifestyle": 120, "System": 30 };

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
    var hay = norm([app.name, app.description, app.category, app.subcategory, (app.tags || []).join(" ")].join(" "));
    if (hay.indexOf(q) !== -1) return true;
    var hayTokens = tokens(hay);
    var qtokens = tokens(q);
    /* Typo tolerance starts at 5 characters. Shorter tokens match literally:
       fuzzy distance let 4-letter "food" match "for" (91 apps!) and 2-letter
       "qr" match "or", and subsequence matching caught "Al-Quran" for "qr". */
    var longEnough = qtokens.some(function (qt) { return qt.length >= 5; });
    if (!longEnough) {
      return qtokens.some(function (qt) { return hayTokens.indexOf(qt) !== -1; });
    }
    var nameNorm = norm(app.name);
    if (isSubsequence(q.replace(/\s+/g, ""), nameNorm.replace(/\s+/g, ""))) return true;
    return qtokens.some(function (qt) {
      if (qt.length < 5) return hayTokens.indexOf(qt) !== -1;
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
    var trustLine = app.free_enough
      ? '<span class="free-enough">Free Enough</span>'
      : '<span class="verified">\u2713 Verified actually-free</span>';
    return '<a class="tile" style="--accent-h:' + accent + '" href="/app/' + escHtml(app.slug) +
      '.html" data-slug="' + escHtml(app.slug) + '">' + ribbon +
      '<span class="tile-top">' + iconHtml +
      "<span><h3>" + wbrify(app.name) + "</h3>" +
      '<p class="sub">' + escHtml(app.subcategory || app.category) + "</p></span></span>" +
      rating +
      '<p class="desc">' + escHtml(app.description) + "</p>" +
      '<span class="badges">' + storeBadges(app) + needsBadge + "</span>" +
      trustLine + '</a>';
  }

  function filtered() {
    var q = norm(state.query);
    var list = state.apps.filter(function (app) {
      if (state.cat && app.category !== state.cat) return false;
      if (state.subcat && app.subcategory !== state.subcat) return false;
      for (var k in state.attrs) {
        if (k === "made_by_us") { if (!app.made_by_us) return false; }
        else if (k === "reviewed") { if (app.needs_review) return false; }
        else if (k === "free_enough") { if (!app.free_enough) return false; }
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
      var filtering = r.q || state.cat || state.subcat || Object.keys(state.attrs).length ||
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
  /* Subcategory drill-down: a second chip row appears once a top-level
     category is selected. SUBCATS is emitted inline by generate.py. */
  var subRow = document.getElementById("subcategory-chips");
  function renderSubcats() {
    var subs = (typeof SUBCATS !== "undefined" && state.cat && SUBCATS[state.cat]) || [];
    if (!subs.length) { subRow.hidden = true; subRow.innerHTML = ""; return; }
    subRow.hidden = false;
    subRow.innerHTML = subs.map(function (s) {
      return '<button class="chip' + (state.subcat === s ? " on" : "") +
             '" data-subcat="' + escHtml(s) + '">' + escHtml(s) + "</button>";
    }).join("");
    subRow.querySelectorAll(".chip").forEach(function (c) {
      c.addEventListener("click", function () {
        var s = c.getAttribute("data-subcat");
        state.subcat = (state.subcat === s) ? "" : s;
        gcEvent("filter/subcategory/" + encodeURIComponent(state.subcat || "all").slice(0, 60));
        renderSubcats();
        render();
      });
    });
  }
  document.querySelectorAll("#category-chips .chip").forEach(function (c) {
    c.addEventListener("click", function () {
      document.querySelectorAll("#category-chips .chip").forEach(function (x) { x.classList.remove("on"); });
      c.classList.add("on");
      state.cat = c.getAttribute("data-cat");
      state.subcat = "";
      gcEvent("filter/category/" + encodeURIComponent(state.cat || "all").slice(0, 60));
      renderSubcats();
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
