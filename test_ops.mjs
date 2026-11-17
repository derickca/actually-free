// The Ops surface suite (issue #32): drives the /ops Pages
// Functions against the MemberSpark kit's own fake — a stub
// centre with its own signing key (functions/lib/memberspark-
// kit/fake.js) — never real MemberSpark, never the live site.
//
// What it proves: the sign-in journey end to end; admission on
// the ops claim judged for this product; the ordinary-404 face
// (the site's own 404 bytes, status 404) for anyone without
// the grant, signed out or signed in; the test account's
// read-only standing — banner, X-Viewer mark, write refusals,
// the 15-minute session — against the 90-day Ops session; the
// cache fences (no-store on every surface answer, and the
// service worker's bypass standing in the generated sw.js and
// in generate.py's build_sw, so regeneration keeps it); the
// generated-module pins (the 404 module is 404.html's exact
// bytes); and the Actions standings read — public with no
// credential (the repo is public), the token sent as a Bearer
// header when one stands, and a refused read standing in the
// panels as Not read.
//
// Run: node test_ops.mjs
import { readFileSync } from "node:fs";
import { fileURLToPath, pathToFileURL } from "node:url";
import { dirname, join } from "node:path";

const ROOT = dirname(fileURLToPath(import.meta.url));
const ORIGIN = "https://actually-free.test";
const CLIENT_ID = "actually-free";
const CLIENT_SECRET = "ops-suite-secret";
const TEST_SUB = "test-sub-1";

const { fakeMemberSpark } = await import(
  pathToFileURL(join(ROOT, "functions/lib/memberspark-kit/fake.js"))
);
const { ROUTES } = await import(
  pathToFileURL(join(ROOT, "functions/lib/memberspark-kit/memberspark.js"))
);
const { NOT_FOUND_HTML } = await import(
  pathToFileURL(join(ROOT, "functions/lib/not-found-page.js"))
);
const { OPS_PAGE_HTML } = await import(
  pathToFileURL(join(ROOT, "functions/lib/ops-page.js"))
);
const { BUILD_RECORD } = await import(
  pathToFileURL(join(ROOT, "functions/lib/build-record.js"))
);
const opsPage = await import(pathToFileURL(join(ROOT, "functions/ops.js")));
const opsData = await import(pathToFileURL(join(ROOT, "functions/ops/data.js")));
const opsSignout = await import(
  pathToFileURL(join(ROOT, "functions/ops-signout.js"))
);
const authRoad = await import(
  pathToFileURL(join(ROOT, "functions/auth/memberspark/[[path]].js"))
);

const fake = await fakeMemberSpark({ issuer: "https://fake.memberspark.test" });
fake.seedClient({
  clientId: CLIENT_ID,
  clientSecret: CLIENT_SECRET,
  redirectUri: ORIGIN + ROUTES.callback,
});
fake.seedAccount({
  sub: "ops-person-1",
  name: "Ops Person",
  email: "ops@example.test",
  ops: [CLIENT_ID],
});
fake.seedAccount({
  sub: "plain-person-1",
  name: "Plain Person",
  email: "plain@example.test",
});
fake.seedAccount({
  sub: TEST_SUB,
  name: "Test Person",
  email: "test@example.test",
  ops: [CLIENT_ID],
});

const ENV = {
  MEMBERSPARK_CLIENT_ID: CLIENT_ID,
  MEMBERSPARK_CLIENT_SECRET: CLIENT_SECRET,
  MEMBERSPARK_ISSUER: fake.issuer,
  TEST_ACCOUNT_SUBS: JSON.stringify([TEST_SUB]),
  // The kit calls its fetch seam with plain addresses (the
  // kit's own test suites wire the fake the same way): wrap
  // the fake so each call arrives as a Request.
  __OPS_FETCH: async (url, opts) => fake.fetch(new Request(url, opts)),
};

let passed = 0;
let failed = 0;
function check(name, cond, extra) {
  if (cond) {
    passed++;
    console.log("PASS " + name);
  } else {
    failed++;
    console.log("FAIL " + name + (extra ? " — " + extra : ""));
  }
}
function setCookies(res) {
  return typeof res.headers.getSetCookie === "function"
    ? res.headers.getSetCookie()
    : [res.headers.get("set-cookie")].filter(Boolean);
}
function cookiePair(setCookie) {
  return setCookie.split(";")[0];
}
async function journey(sub) {
  const start = await authRoad.onRequest({
    request: new Request(ORIGIN + ROUTES.signIn),
    env: ENV,
  });
  const loc = start.headers.get("location") || "";
  const flowCookies = setCookies(start).map(cookiePair).join("; ");
  const authUrl = new URL(loc);
  authUrl.searchParams.set("fake_sub", sub);
  const authRes = await fake.fetch(new Request(authUrl));
  const back = authRes.headers.get("location") || "";
  const cb = await authRoad.onRequest({
    request: new Request(back, { headers: { cookie: flowCookies } }),
    env: ENV,
  });
  const cookies = setCookies(cb);
  const session = cookies.find((c) => c.startsWith("af-ops-session="));
  return {
    start,
    cb,
    cookies,
    sessionCookie: session ? cookiePair(session) : null,
  };
}
function sessionPayload(sessionCookie) {
  const value = sessionCookie.split("=").slice(1).join("=");
  const body = value.slice(0, value.lastIndexOf("."));
  return JSON.parse(
    Buffer.from(body.replace(/-/g, "+").replace(/_/g, "/"), "base64").toString(
      "utf8"
    )
  );
}
const get = (path, cookie) =>
  new Request(ORIGIN + path, cookie ? { headers: { cookie } } : {});

// ---------- pins: routes and generated modules ----------
const routes = JSON.parse(readFileSync(join(ROOT, "_routes.json"), "utf8"));
check(
  "routes include exactly the surface and the sign-in road",
  JSON.stringify(routes.include) ===
    JSON.stringify(["/ops", "/ops/*", "/ops-signout", "/auth/memberspark/*"])
);
check(
  "the 404 module is 404.html's exact bytes",
  NOT_FOUND_HTML === readFileSync(join(ROOT, "404.html"), "utf8")
);
check(
  "the ops page module carries the five panels",
  ["publishing", "checks", "site", "backup", "doors"].every((p) =>
    OPS_PAGE_HTML.includes('data-panel="' + p + '"')
  )
);

// ---------- signed out: the ordinary 404 face ----------
{
  const res = await opsPage.onRequest({ request: get("/ops"), env: ENV });
  const body = await res.text();
  check("signed-out /ops answers 404", res.status === 404);
  check("signed-out /ops is the ordinary 404 page", body === NOT_FOUND_HTML);
  check(
    "signed-out /ops carries no-store",
    res.headers.get("cache-control") === "no-store"
  );
  check("signed-out /ops has no viewer mark", !res.headers.get("x-viewer"));
}
{
  const res = await opsData.onRequest({
    request: get("/ops/data"),
    env: ENV,
  });
  check("signed-out /ops/data answers 404", res.status === 404);
  check(
    "signed-out /ops/data carries no-store",
    res.headers.get("cache-control") === "no-store"
  );
}

// ---------- callback guards ----------
{
  const res = await authRoad.onRequest({
    request: get(
      ROUTES.callback +
        "?code=x&state=y&iss=" +
        encodeURIComponent(fake.issuer)
    ),
    env: ENV,
  });
  check(
    "a callback with no flow restarts sign-in (303)",
    res.status === 303 &&
      (res.headers.get("location") || "").endsWith(ROUTES.signIn),
    "status " + res.status
  );
  check(
    "a no-flow callback mints no session",
    !setCookies(res).some((c) => c.startsWith("af-ops-session="))
  );
}
{
  const res = await authRoad.onRequest({
    request: get(
      ROUTES.callback + "?code=x&state=y&iss=https://evil.example"
    ),
    env: ENV,
  });
  const body = await res.text();
  check(
    "a foreign-issuer callback gets the not-a-return page, no session",
    res.status === 200 &&
      body !== NOT_FOUND_HTML &&
      !setCookies(res).some((c) => c.startsWith("af-ops-session=")),
    "status " + res.status
  );
}

// ---------- a person with no Ops grant: same 404 face ----------
{
  const j = await journey("plain-person-1");
  check("plain journey mints a session", Boolean(j.sessionCookie));
  check(
    "the session cookie stands first on the callback answer",
    j.cookies.length > 0 && j.cookies[0].startsWith("af-ops-session=")
  );
  const res = await opsPage.onRequest({
    request: get("/ops", j.sessionCookie),
    env: ENV,
  });
  check(
    "signed-in without the grant, /ops is the 404 face",
    res.status === 404 && (await res.text()) === NOT_FOUND_HTML
  );
  const data = await opsData.onRequest({
    request: get("/ops/data", j.sessionCookie),
    env: ENV,
  });
  check("signed-in without the grant, /ops/data is 404", data.status === 404);
}

// ---------- the Ops holder ----------
let opsCookie;
{
  const j = await journey("ops-person-1");
  opsCookie = j.sessionCookie;
  check("ops journey mints a session", Boolean(opsCookie));
  const payload = sessionPayload(opsCookie);
  const ttl = payload.exp - Math.floor(Date.now() / 1000);
  check(
    "the ops session runs 90 days",
    ttl > 7776000 - 300 && ttl <= 7776000 + 60,
    "ttl " + ttl
  );
  check(
    "the session stores the decision, never the ops claim",
    payload.opsAdmitted === true && !("ops" in payload)
  );
  const res = await opsPage.onRequest({
    request: get("/ops", opsCookie),
    env: ENV,
  });
  const body = await res.text();
  check("the holder's /ops answers 200", res.status === 200);
  check(
    "the holder's page carries the panels and their name",
    body.includes('data-panel="publishing"') && body.includes("Ops Person")
  );
  check(
    "the holder's page has no test banner and no viewer mark",
    !body.includes("Viewing as a test account") && !res.headers.get("x-viewer")
  );
  check(
    "the holder's page carries no-store",
    res.headers.get("cache-control") === "no-store"
  );
  const head = await opsPage.onRequest({
    request: new Request(ORIGIN + "/ops", {
      method: "HEAD",
      headers: { cookie: opsCookie },
    }),
    env: ENV,
  });
  check(
    "HEAD /ops answers 200 with no body",
    head.status === 200 && (await head.text()) === ""
  );
  const data = await opsData.onRequest({
    request: get("/ops/data", opsCookie),
    env: ENV,
  });
  const d = await data.json();
  check("the holder's /ops/data answers 200", data.status === 200);
  check(
    "the data names the Ops standing and the build record",
    d.identity && d.identity.standing === "Ops role" &&
      d.build && d.build.listings === BUILD_RECORD.listings &&
      d.backup && typeof d.backup.line === "string" && d.backup.line.length > 0
  );
  check(
    "the data's Actions panels stand in the read shape, never a not-configured note",
    d.publishing && typeof d.publishing.result === "string" &&
      d.checks && Array.isArray(d.checks.rows) &&
      !("note" in d.publishing) && !("note" in d.checks)
  );
  const tampered =
    opsCookie.slice(0, -2) + (opsCookie.endsWith("A") ? "B" : "A") + opsCookie.slice(-1);
  const forged = await opsPage.onRequest({
    request: get("/ops", tampered),
    env: ENV,
  });
  check("a tampered session reads as no session (404)", forged.status === 404);
}

// ---------- the Actions standings read ----------
// The publishing and checks standings are read from the
// repo's own Actions records through the door's fetch seam,
// judged here against a stub GitHub — never the live API.
// Each shape gets a fresh copy of the door module (so its
// read cache starts empty) and a fabricated holder session:
// opsData reads only the session's name and address.
const HOLDER_SESSION = {
  sub: "ops-person-1",
  name: "Ops Person",
  email: "ops@example.test",
};
function githubStub(answer) {
  const seen = [];
  const fetchImpl = async (url, opts = {}) => {
    const u = new URL(url);
    seen.push({ url, headers: (opts && opts.headers) || {} });
    if (u.hostname !== "api.github.com") {
      return fake.fetch(new Request(url, opts));
    }
    return answer(u);
  };
  return { fetchImpl, seen };
}
function githubAnswers() {
  const runsBody = (id) => ({
    workflow_runs: [{
      id,
      head_sha: "1234567890abcdef",
      status: "completed",
      conclusion: "success",
      created_at: "2026-11-17T10:00:00Z",
      updated_at: "2026-11-17T10:05:00Z",
    }],
  });
  const json = (body) =>
    new Response(JSON.stringify(body), {
      status: 200,
      headers: { "content-type": "application/json" },
    });
  return (u) => {
    if (u.pathname.endsWith("/actions/workflows/deploy-site.yml/runs")) {
      return json(runsBody(4242));
    }
    if (u.pathname.includes("/actions/runs/4242/jobs")) {
      return json({
        jobs: [{
          steps: [{
            name: "Publish to Cloudflare Pages",
            status: "completed",
            conclusion: "success",
          }],
        }],
      });
    }
    if (u.pathname.endsWith("/actions/workflows/catalogue-validation.yml/runs")) {
      return json(runsBody(4343));
    }
    if (u.pathname.endsWith("/actions/workflows/link-check.yml/runs")) {
      return json(runsBody(4444));
    }
    return new Response("not found (stub)", { status: 404 });
  };
}
async function opsDataWith(env, tag) {
  const door = await import(
    pathToFileURL(join(ROOT, "functions/lib/ops-door.js")) + "?github=" + tag
  );
  return door.opsData(door.getSettings(env), HOLDER_SESSION, "ops");
}
{
  const stub = githubStub(githubAnswers());
  const d = await opsDataWith({ ...ENV, __OPS_FETCH: stub.fetchImpl }, "plain");
  check(
    "with no GitHub token the public read returns the standings",
    d.publishing.result === "Success" &&
      d.publishing.published === "Published" &&
      d.publishing.commit === "1234567" &&
      d.checks.rows.length === 2 &&
      d.checks.rows.every((r) => r.result === "Success"),
    JSON.stringify(d.publishing)
  );
  check(
    "the no-token read sends no authorization header",
    stub.seen.length > 0 &&
      stub.seen.every((s) => !("authorization" in s.headers))
  );
}
{
  const stub = githubStub(githubAnswers());
  const d = await opsDataWith(
    {
      ...ENV,
      OPS_GITHUB_TOKEN: "ops-suite-github-token",
      __OPS_FETCH: stub.fetchImpl,
    },
    "token"
  );
  check(
    "with a token the read returns the same standings",
    d.publishing.result === "Success" &&
      d.publishing.published === "Published" &&
      d.checks.rows.length === 2
  );
  check(
    "the tokened read sends the token as its Bearer header",
    stub.seen.length > 0 &&
      stub.seen.every(
        (s) => s.headers.authorization === "Bearer ops-suite-github-token"
      )
  );
}
{
  const stub = githubStub(
    () => new Response("forbidden (stub)", { status: 403 })
  );
  const d = await opsDataWith({ ...ENV, __OPS_FETCH: stub.fetchImpl }, "refused");
  check(
    "a refused GitHub read stands as Not read, inventing nothing",
    d.publishing.result === "Not read" &&
      d.checks.rows.length === 2 &&
      d.checks.rows.every((r) => r.result === "Not read"),
    JSON.stringify(d.publishing)
  );
}

// ---------- the test account: read-only standing ----------
{
  const j = await journey(TEST_SUB);
  check("test journey mints a session", Boolean(j.sessionCookie));
  const payload = sessionPayload(j.sessionCookie);
  const ttl = payload.exp - Math.floor(Date.now() / 1000);
  check(
    "the test session runs 15 minutes (TA-17)",
    ttl > 600 && ttl <= 900 + 60,
    "ttl " + ttl
  );
  const res = await opsPage.onRequest({
    request: get("/ops", j.sessionCookie),
    env: ENV,
  });
  const body = await res.text();
  check(
    "the test account sees the page, with the banner (TA-6, TA-9)",
    res.status === 200 &&
      body.includes("Viewing as a test account. Read-only.")
  );
  check(
    "the test account's page carries the read-only mark",
    res.headers.get("x-viewer") === "read-only"
  );
  const data = await opsData.onRequest({
    request: get("/ops/data", j.sessionCookie),
    env: ENV,
  });
  const d = await data.json();
  check(
    "the test account reads the same data, marked read-only",
    data.status === 200 &&
      data.headers.get("x-viewer") === "read-only" &&
      d.identity && d.identity.standing.indexOf("Test account") === 0
  );
  const postPage = await opsPage.onRequest({
    request: new Request(ORIGIN + "/ops", {
      method: "POST",
      headers: { cookie: j.sessionCookie },
    }),
    env: ENV,
  });
  check(
    "a test account's write to /ops is refused 403 (TA-7)",
    postPage.status === 403 &&
      (await postPage.json()).error === "Read-only." &&
      postPage.headers.get("x-viewer") === "read-only"
  );
  const postData = await opsData.onRequest({
    request: new Request(ORIGIN + "/ops/data", {
      method: "POST",
      headers: { cookie: j.sessionCookie },
    }),
    env: ENV,
  });
  check(
    "a test account's write to /ops/data is refused 403 (TA-7)",
    postData.status === 403
  );
  const out = await opsSignout.onRequest({
    request: new Request(ORIGIN + "/ops-signout", {
      method: "POST",
      headers: { cookie: j.sessionCookie },
    }),
    env: ENV,
  });
  check(
    "sign-out stays open to a test account, clearing the session",
    out.status === 303 &&
      setCookies(out).some(
        (c) => c.startsWith("af-ops-session=;") && c.includes("Max-Age=0")
      )
  );
}

// ---------- sign-out for the holder ----------
{
  const res = await opsSignout.onRequest({
    request: new Request(ORIGIN + "/ops-signout", {
      method: "POST",
      headers: { cookie: opsCookie },
    }),
    env: ENV,
  });
  check(
    "the holder's sign-out clears the session and goes to the centre's sign-out",
    res.status === 303 &&
      (res.headers.get("location") || "").includes("/oauth2/logout") &&
      setCookies(res).some((c) => c.includes("Max-Age=0")) &&
      res.headers.get("cache-control") === "no-store"
  );
  const getOut = await opsSignout.onRequest({
    request: get("/ops-signout", opsCookie),
    env: ENV,
  });
  check("sign-out by GET is the 404 face", getOut.status === 404);
}

// ---------- the service worker fence ----------
{
  const sw = readFileSync(join(ROOT, "sw.js"), "utf8");
  const gen = readFileSync(join(ROOT, "generate.py"), "utf8");
  const fence = (text) =>
    text.includes('u.pathname === "/ops"') &&
    text.includes('u.pathname.startsWith("/ops/")') &&
    text.includes('u.pathname === "/ops-signout"') &&
    text.includes('u.pathname.startsWith("/auth/memberspark/")');
  check("the generated sw.js fences the surface and the sign-in road", fence(sw));
  check("generate.py's build_sw carries the fence (regeneration keeps it)", fence(gen));
}

console.log(
  "test_ops: " + passed + " passed, " + failed + " failed, " +
    (passed + failed) + " checks"
);
process.exit(failed ? 1 : 0);
