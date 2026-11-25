// The operator door suite (issue #55): drives the
// /operator/door and /operator/run-record Pages Functions
// directly against a stub centre — a real EC signing key
// whose key set the door reads through its fetch seam — and
// an in-memory AF_LOGS. Never real MemberSpark, never the
// live site.
//
// What it proves: the dark door (no credential placed, every
// call the ordinary 404 face); the credential's 401; the
// assertion's refusals (missing, expired, wrong audience,
// question, subject or lookup mismatch, the machinery shape
// refused at the proof gate); the centre-as-itself shape
// admitted for the standing questions and refused outside
// them; the audit entry standing before the answer, and a
// failed write answering nothing; each question's shape
// against planted records (the error windows and signatures,
// the audit families and their witnesses, the empty backup
// points, the test standing's runs and detail parts, the
// adoption markers); explain_finding's recorded answer and
// its shape refusals standing before any assertion work; an
// unnamed question and an act refused; and the run-record
// door the reporter seats finishes through, read back
// through the operator door's test_standing.
//
// Run: node test_operator_door.mjs
import { createSign, generateKeyPairSync } from "node:crypto";
import { readFileSync } from "node:fs";
import { fileURLToPath, pathToFileURL } from "node:url";
import { dirname, join } from "node:path";

const ROOT = dirname(fileURLToPath(import.meta.url));
const ORIGIN = "https://actually-free.test";
const ISSUER = "https://fake.memberspark.test";
const DOOR_SECRET = "operator-door-secret-for-the-suite";
const RUN_KEY = "run-record-key-for-the-suite";
const ADMIN_ID = "admin-1";
const PRODUCT = "actually-free";

const { NOT_FOUND_HTML } = await import(
  pathToFileURL(join(ROOT, "functions/lib/not-found-page.js"))
);
const door = await import(
  pathToFileURL(join(ROOT, "functions/operator/door.js"))
);
const runRecord = await import(
  pathToFileURL(join(ROOT, "functions/operator/run-record.js"))
);

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
const same = (a, b) => JSON.stringify(a) === JSON.stringify(b);

// ---------- the stub centre: a key set and nothing else ----------
const { privateKey, publicKey } = generateKeyPairSync("ec", {
  namedCurve: "P-256",
});
const publicJwk = publicKey.export({ format: "jwk" });
publicJwk.kid = "op-key-1";
publicJwk.use = "sig";
publicJwk.alg = "ES256";

const jwksFetch = async (url) => {
  if (String(url) === ISSUER + "/.well-known/jwks.json") {
    return new Response(JSON.stringify({ keys: [publicJwk] }), {
      status: 200,
      headers: { "content-type": "application/json" },
    });
  }
  return new Response("not found", { status: 404 });
};

function b64(text) {
  return Buffer.from(text).toString("base64url");
}
function mintAssertion(overrides = {}, drop = []) {
  const now = Math.floor(Date.now() / 1000);
  const header = { alg: "ES256", kid: "op-key-1", typ: "ms-operator-assertion" };
  const claims = {
    iss: ISSUER,
    aud: PRODUCT,
    sub: ADMIN_ID,
    sid: "sess-1",
    jti: "lookup-1",
    q: "errors",
    subject: PRODUCT,
    iat: now,
    exp: now + 60,
    ...overrides,
  };
  for (const key of drop) delete claims[key];
  const input = b64(JSON.stringify(header)) + "." + b64(JSON.stringify(claims));
  const signer = createSign("SHA256");
  signer.update(input);
  signer.end();
  const sig = signer.sign({ key: privateKey, dsaEncoding: "ieee-p1363" });
  return input + "." + sig.toString("base64url");
}

// ---------- the fake log store ----------
function fakeKv() {
  const map = new Map();
  return {
    map,
    async get(key, type) {
      const value = map.get(key);
      if (value === undefined) return null;
      return type === "json" ? JSON.parse(value) : value;
    },
    async put(key, value) {
      map.set(key, String(value));
    },
    async list({ prefix = "", cursor, limit = 1000 } = {}) {
      const names = [...map.keys()].filter((k) => k.startsWith(prefix)).sort();
      return { keys: names.map((name) => ({ name })), list_complete: true };
    },
  };
}
function brokenKv() {
  const inner = fakeKv();
  return {
    map: inner.map,
    get: inner.get,
    list: inner.list,
    async put() {
      throw new Error("the store refused the write");
    },
  };
}

const KV = fakeKv();
const ENV = {
  OPERATOR_DOOR_SECRET: DOOR_SECRET,
  AF_RUN_RECORD_KEY: RUN_KEY,
  MEMBERSPARK_ISSUER: ISSUER,
  AF_LOGS: KV,
  __OPERATOR_FETCH: jwksFetch,
};

async function callDoor(body, { env = ENV, headers = {}, method = "POST" } = {}) {
  const init = { method, headers: { ...headers } };
  if (method === "POST") {
    init.headers["content-type"] = "application/json";
    init.body = typeof body === "string" ? body : JSON.stringify(body);
    if (!("authorization" in init.headers)) {
      init.headers.authorization = "Bearer " + DOOR_SECRET;
    }
  }
  return door.onRequest({
    request: new Request(ORIGIN + "/operator/door", init),
    env,
  });
}
async function callDoorOk(body, opts) {
  const res = await callDoor(body, opts);
  const text = await res.text();
  let json = null;
  try {
    json = JSON.parse(text);
  } catch {}
  return { res, json, text };
}
async function familyEntries(kv, family) {
  const { keys } = await kv.list({ prefix: family + ":" });
  const out = [];
  for (const k of keys) out.push(await kv.get(k.name, "json"));
  return out;
}
function plant(kv, family, entry) {
  kv.map.set(
    family + ":" + entry.at + ":" + Math.random().toString(36).slice(2),
    JSON.stringify(entry)
  );
}

// ---------- the dark door ----------
{
  const dark = { ...ENV, OPERATOR_DOOR_SECRET: "" };
  delete dark.OPERATOR_DOOR_SECRET;
  const post = await callDoor(
    { lookup_id: "l1", question: "errors", subject: PRODUCT, assertion: "x" },
    { env: dark }
  );
  check(
    "dark door: a POST answers the ordinary 404 face",
    post.status === 404 && (await post.text()) === NOT_FOUND_HTML
  );
  const get = await callDoor(null, { env: ENV, method: "GET" });
  check(
    "a GET answers the ordinary 404 face, credential placed or not",
    get.status === 404 && (await get.text()) === NOT_FOUND_HTML
  );
}

// ---------- the credential ----------
{
  const res = await callDoor(
    { lookup_id: "l1", question: "errors", subject: PRODUCT, assertion: "x" },
    { headers: { authorization: "Bearer wrong" } }
  );
  check("a credential miss answers 401", res.status === 401);
  const refusals = await familyEntries(KV, "operator-refusal");
  check(
    "the refused call stands in the door's refusal log",
    refusals.length === 1 && refusals[0].reason === "credential",
    JSON.stringify(refusals)
  );
}

// ---------- the assertion's refusals ----------
{
  const base = { lookup_id: "lookup-1", question: "errors", subject: PRODUCT };
  const cases = [
    ["a missing assertion is refused", { ...base }],
    ["an expired assertion is refused", {
      ...base,
      assertion: mintAssertion({ iat: 1000, exp: 1060 }),
    }],
    ["an assertion for another product is refused", {
      ...base,
      assertion: mintAssertion({ aud: "certifiablemedia" }),
    }],
    ["an assertion naming another question is refused", {
      ...base,
      assertion: mintAssertion({ q: "audit" }),
    }],
    ["an assertion naming another subject is refused", {
      ...base,
      assertion: mintAssertion({ subject: "someone-else" }),
    }],
    ["an assertion naming another lookup is refused", {
      ...base,
      assertion: mintAssertion({ jti: "lookup-2" }),
    }],
    ["an assertion living longer than sixty seconds is refused", {
      ...base,
      assertion: mintAssertion({ exp: Math.floor(Date.now() / 1000) + 3600 }),
    }],
    ["a system assertion carrying a session id is refused", {
      ...base,
      assertion: mintAssertion({ sub: "system", sid: "sess-9" }),
    }],
    ["a machinery-shaped assertion is refused at the proof gate", {
      ...base,
      assertion: mintAssertion({ sub: "machinery:machinery-acts" }, ["sid"]),
    }],
  ];
  for (const [name, body] of cases) {
    const res = await callDoor(body);
    check(name, res.status === 401, "status " + res.status);
  }
}

// ---------- the two admitted shapes ----------
{
  const owner = await callDoorOk({
    lookup_id: "lookup-1",
    question: "errors",
    subject: PRODUCT,
    assertion: mintAssertion({}),
  });
  check(
    "an owner's call answers in the standing envelope",
    owner.res.status === 200 &&
      typeof owner.json.answered_at === "string" &&
      owner.json.audit && owner.json.audit.written === true &&
      typeof owner.json.audit.at === "string" &&
      owner.json.answer && owner.json.answer.log_state === "present",
    owner.text
  );
  const lookups = await familyEntries(KV, "operator-lookup");
  check(
    "the audit entry stands from the call, naming the asker, the subject and the question",
    lookups.length === 1 &&
      lookups[0].by === ADMIN_ID &&
      lookups[0].subject === PRODUCT &&
      lookups[0].question === "errors" &&
      lookups[0].road === "admin",
    JSON.stringify(lookups)
  );
  const system = await callDoorOk({
    lookup_id: "lookup-1",
    question: "errors",
    subject: PRODUCT,
    assertion: mintAssertion({ sub: "system", sid: null }),
  });
  check(
    "the centre-as-itself shape is admitted for a standing question",
    system.res.status === 200 && system.json.answer.log_state === "present",
    system.text
  );
}

// ---------- a failed audit write answers nothing ----------
{
  const res = await callDoor(
    {
      lookup_id: "lookup-1",
      question: "errors",
      subject: PRODUCT,
      assertion: mintAssertion({}),
    },
    { env: { ...ENV, AF_LOGS: brokenKv() } }
  );
  const text = await res.text();
  check(
    "a failed audit write answers 500 with no answer envelope",
    res.status === 500 && !text.includes("answered_at"),
    "status " + res.status + " " + text
  );
}

// ---------- refusals of shape ----------
{
  const unknown = await callDoor({
    lookup_id: "lookup-1",
    question: "standing",
    subject: "person-1",
    assertion: mintAssertion({ q: "standing", subject: "person-1" }),
  });
  check("a question this door does not name is refused", unknown.status === 400);
  const act = await callDoor({
    act_id: "act-1",
    act: "note",
    subject: "person-1",
    text: "a note",
    assertion: mintAssertion({
      sub: "system",
      sid: null,
      q: "act:note",
      subject: "person-1",
      jti: "act-1",
    }),
  });
  check("an act is refused — no act is named for this product", act.status === 400);
  const wrongSubject = await callDoor({
    lookup_id: "lookup-1",
    question: "errors",
    subject: "another-product",
    assertion: mintAssertion({ subject: "another-product" }),
  });
  check(
    "a per-product question naming another subject is refused",
    wrongSubject.status === 400
  );
}

// ---------- errors, from planted entries ----------
const nowIso = new Date().toISOString();
const hourEnd = nowIso.slice(0, 14) + "00:00.000Z";
const W = {
  start: new Date(Date.parse(hourEnd) - 3600000).toISOString(),
  end: hourEnd,
};
const P = {
  start: new Date(Date.parse(hourEnd) - 7200000).toISOString(),
  end: W.start,
};
const atMin = (base, min) => new Date(Date.parse(base) + min * 60000).toISOString();
{
  const kv = fakeKv();
  const env = { ...ENV, AF_LOGS: kv };
  const plantError = (at, signature) =>
    plant(kv, "site-error", {
      kind: "site-error", at, where: "/ops", signature, cause: "a cause",
    });
  plantError(atMin(W.start, 10), "ops_page_failure");
  plantError(atMin(W.start, 20), "ops_page_failure");
  plantError(atMin(W.start, 5), "ops_data_failure");
  plantError(atMin(P.start, 10), "ops_page_failure");
  plantError(new Date(Date.parse(W.start) - 259200000).toISOString(), "ops_page_failure");
  const { json } = await callDoorOk(
    {
      lookup_id: "lookup-1",
      question: "errors",
      subject: PRODUCT,
      assertion: mintAssertion({}),
    },
    { env }
  );
  const a = json.answer;
  check(
    "errors: the windows stand on the last closed hour and the one before",
    a.window_start === W.start && a.window_end === W.end &&
      a.window_total === 3 && a.previous_window_total === 1,
    JSON.stringify(a)
  );
  const line = (a.signatures || []).find((s) => s.signature === "ops_page_failure");
  check(
    "errors: a signature line carries both windows and its whole-log sightings",
    !!line && line.count === 2 && line.previous_count === 1 &&
      line.first_seen === new Date(Date.parse(W.start) - 259200000).toISOString() &&
      line.last_seen === atMin(W.start, 20) && typeof line.log === "string",
    JSON.stringify(a.signatures)
  );
  check(
    "errors: the newest entry and the freshness mark stand",
    a.newest_at === atMin(W.start, 20) && typeof a.judged_at === "string",
    JSON.stringify(a)
  );
}

// ---------- audit, from planted families ----------
const dayEnd = nowIso.slice(0, 10) + "T00:00:00.000Z";
const D = new Date(Date.parse(dayEnd) - 86400000).toISOString().slice(0, 10);
{
  const kv = fakeKv();
  const env = { ...ENV, AF_LOGS: kv };
  plant(kv, "sign-in-refusal", {
    kind: "sign-in-refusal", action: "sign-in-refusal",
    door: "ops-door", reason: "no-standing", at: D + "T01:00:00.000Z",
  });
  plant(kv, "sign-in-refusal", {
    kind: "sign-in-refusal", action: "sign-in-refusal",
    door: "ops-page", reason: "token-invalid", at: D + "T02:00:00.000Z",
  });
  plant(kv, "sign-in-completion", {
    kind: "sign-in-completion", door: "ops-door",
    standing: "ops", at: D + "T03:00:00.000Z",
  });
  plant(kv, "operator-lookup", {
    kind: "operator-lookup", action: "operator_lookup", by: ADMIN_ID,
    subject: PRODUCT, question: "errors", road: "admin", at: D + "T04:00:00.000Z",
  });
  const { json } = await callDoorOk(
    {
      lookup_id: "lookup-1",
      question: "audit",
      subject: PRODUCT,
      assertion: mintAssertion({ q: "audit" }),
    },
    { env }
  );
  const a = json.answer;
  const fam = Object.fromEntries((a.families || []).map((f) => [f.family, f]));
  check(
    "audit: the families stand counted over the newest closed day, each with its witness",
    fam["sign-in refusals"] && fam["sign-in refusals"].audit_count === 2 &&
      fam["sign-in refusals"].witness_count === 2 &&
      fam["sign-in completions"] && fam["sign-in completions"].audit_count === 1 &&
      fam["operator lookups"] && fam["operator lookups"].audit_count === 1 &&
      fam["finding explanations"] && fam["finding explanations"].audit_count === 0 &&
      (a.families || []).every((f) => typeof f.witness === "string" && f.witness),
    JSON.stringify(a.families)
  );
  check(
    "audit: the window and the closed day stand, with the freshness mark",
    a.window_start === D + "T00:00:00.000Z" && a.window_end === dayEnd &&
      a.newest_closed_day === D && typeof a.judged_at === "string" &&
      // The ask's own lookup entry stands in the family
      // before the gather, as at the shop's door, so the
      // newest entry is the ask itself — never older than
      // the newest planted entry.
      typeof a.newest_at === "string" && a.newest_at >= D + "T04:00:00.000Z",
    JSON.stringify(a)
  );
  const lookupsAfter = await familyEntries(kv, "operator-lookup");
  check(
    "audit: the ask's own lookup entry stands in the family it was counted in",
    lookupsAfter.length === 2 &&
      lookupsAfter.some((e) => e.question === "audit" && e.by === ADMIN_ID),
    JSON.stringify(lookupsAfter)
  );
}

// ---------- backups and adoption: the honest empty shapes ----------
{
  const backups = await callDoorOk({
    lookup_id: "lookup-1",
    question: "backups",
    subject: PRODUCT,
    assertion: mintAssertion({ q: "backups" }),
  });
  check(
    "backups: no point stands, and the answer says so with its mark",
    backups.res.status === 200 &&
      same(backups.json.answer.points, []) &&
      typeof backups.json.answer.judged_at === "string",
    backups.text
  );
  const adoption = await callDoorOk({
    lookup_id: "lookup-1",
    question: "adoption",
    subject: PRODUCT,
    assertion: mintAssertion({ q: "adoption" }),
  });
  const a = adoption.json.answer;
  check(
    "adoption: no accounts of its own — the markers stand, never zeros, never omitted",
    a.accounts_standing === "not applicable" &&
      a.new_day === "not applicable" && a.new_week === "not applicable" &&
      a.new_month === "not applicable" && a.active_day === "not applicable" &&
      a.active_week === "not applicable" && a.active_month === "not applicable" &&
      !("active_figure" in a) && typeof a.judged_at === "string",
    adoption.text
  );
}

// ---------- explain_finding ----------
{
  const bad = await callDoor({
    lookup_id: "lookup-1",
    question: "explain_finding",
    subject: "audit:sign-in refusals:2026-11-24",
    assertion: "not-a-real-assertion",
  });
  check(
    "explain_finding: a missing explanation is a shape refusal, before any assertion work",
    bad.status === 400
  );
  const empty = await callDoor({
    lookup_id: "lookup-1",
    question: "explain_finding",
    subject: "audit:sign-in refusals:2026-11-24",
    explanation: "",
    assertion: mintAssertion({ q: "explain_finding", subject: "audit:sign-in refusals:2026-11-24" }),
  });
  check("explain_finding: an empty explanation is refused", empty.status === 400);
  const over = await callDoor({
    lookup_id: "lookup-1",
    question: "explain_finding",
    subject: "audit:sign-in refusals:2026-11-24",
    explanation: "x".repeat(2001),
    assertion: mintAssertion({ q: "explain_finding", subject: "audit:sign-in refusals:2026-11-24" }),
  });
  check("explain_finding: an explanation past 2,000 characters is refused", over.status === 400);
  const okCall = await callDoorOk({
    lookup_id: "lookup-1",
    question: "explain_finding",
    subject: "audit:sign-in refusals:2026-11-24",
    explanation: "The refusals were the test account's own sign-ins.",
    assertion: mintAssertion({ q: "explain_finding", subject: "audit:sign-in refusals:2026-11-24" }),
  });
  check(
    "explain_finding: the acceptance answer is the envelope with recorded",
    okCall.res.status === 200 && okCall.json.answer.recorded === true &&
      okCall.json.audit.written === true,
    okCall.text
  );
  const entries = await familyEntries(KV, "finding-explanation");
  check(
    "explain_finding: the entry stands in the product's own log under its act name",
    entries.length === 1 &&
      entries[0].action === "finding-explained" &&
      entries[0].by === ADMIN_ID &&
      entries[0].target === "audit:sign-in refusals:2026-11-24" &&
      entries[0].explanation === "The refusals were the test account's own sign-ins.",
    JSON.stringify(entries)
  );
}

// ---------- the run-record door, and test_standing read back ----------
{
  const dark = { ...ENV };
  delete dark.AF_RUN_RECORD_KEY;
  const darkRes = await runRecord.onRequest({
    request: new Request(ORIGIN + "/operator/run-record", {
      method: "POST",
      headers: { "content-type": "application/json" },
      body: "{}",
    }),
    env: dark,
  });
  check("the run-record door stands dark while no key is placed", darkRes.status === 404);
  const wrong = await runRecord.onRequest({
    request: new Request(ORIGIN + "/operator/run-record", {
      method: "POST",
      headers: {
        "content-type": "application/json",
        authorization: "Bearer wrong",
      },
      body: "{}",
    }),
    env: ENV,
  });
  check("the run-record door refuses a wrong key", wrong.status === 401);

  const kv = fakeKv();
  const env = { ...ENV, AF_LOGS: kv };
  const sendRun = async (report) =>
    runRecord.onRequest({
      request: new Request(ORIGIN + "/operator/run-record", {
        method: "POST",
        headers: {
          "content-type": "application/json",
          authorization: "Bearer " + RUN_KEY,
        },
        body: JSON.stringify(report),
      }),
      env,
    });
  const badRun = await sendRun({ product: PRODUCT, group: "Build Tests", kind: "run", phase: "finish" });
  check("the run-record door refuses a report with no run id", badRun.status === 400);
  const base = {
    product: PRODUCT, group: "Build Tests", kind: "run",
    started_by: "change", started_at: "2026-11-24T10:00:00Z",
  };
  const s1 = await sendRun({ ...base, run_id: "bt-1", phase: "start" });
  const f1 = await sendRun({
    ...base, run_id: "bt-1", phase: "finish",
    finished_at: "2026-11-24T10:05:00Z", result: "pass",
    checks: [{ name: "Site suite", ok: true }],
  });
  const f2 = await sendRun({
    ...base, run_id: "bt-2", phase: "finish",
    started_at: "2026-11-24T11:00:00Z", finished_at: "2026-11-24T11:05:00Z",
    result: "fail",
    checks: [{ name: "Site suite", ok: false, detail: "3 checks failed" }],
  });
  const s3 = await sendRun({
    ...base, run_id: "bt-3", phase: "start", started_at: "2026-11-24T12:00:00Z",
  });
  const sr = await sendRun({
    product: PRODUCT, group: "Scenario Review", kind: "run",
    run_id: "sr-1", phase: "finish", started_by: "schedule",
    started_at: "2026-11-24T06:10:00Z", finished_at: "2026-11-24T06:12:00Z",
    result: "pass",
    checks: [{ name: "home:loads", ok: true }],
    details: {
      passed: 1, failed: 0,
      not_run: ["journey-b"],
      quarantine: [{ check: "journey-a:check-1", skipped: 2 }],
    },
  });
  check(
    "the run-record door records starts and finishes",
    [s1, f1, f2, s3, sr].every((r) => r.status === 200),
    [s1, f1, f2, s3, sr].map((r) => r.status).join(",")
  );

  const { json } = await callDoorOk(
    {
      lookup_id: "lookup-1",
      question: "test_standing",
      subject: PRODUCT,
      assertion: mintAssertion({ q: "test_standing" }),
    },
    { env }
  );
  const groups = Object.fromEntries(
    (json.answer.groups || []).map((g) => [g.group, g])
  );
  const bt = groups["Build Tests"] || {};
  check(
    "test_standing: a group's finishes, newest finish and cadence stand",
    bt.finishes === 2 && bt.result === "fail" &&
      bt.at === "2026-11-24T11:05:00Z" &&
      bt.newest_finish_at === "2026-11-24T11:05:00Z" &&
      bt.kind === "event" && bt.due_after_seconds === 3600 &&
      bt.grace_seconds === 7200,
    JSON.stringify(bt)
  );
  const runs = Object.fromEntries((bt.runs || []).map((r) => [r.run, r]));
  check(
    "test_standing: the runs list carries open runs and finishes, the newest finish's checks riding",
    runs["bt-3"] && !("result" in runs["bt-3"]) && !("at" in runs["bt-3"]) &&
      runs["bt-2"] && runs["bt-2"].result === "fail" &&
      runs["bt-2"].detail && runs["bt-2"].detail.checks &&
      runs["bt-2"].detail.checks[0].detail === "3 checks failed" &&
      runs["bt-1"] && runs["bt-1"].result === "pass",
    JSON.stringify(bt.runs)
  );
  const rr = groups["Release Review"] || {};
  check(
    "test_standing: a group that has never finished reads as never finished",
    rr.finishes === 0 && !("result" in rr) && !("at" in rr) &&
      !("newest_finish_at" in rr) && rr.kind === "event" &&
      rr.due_after_seconds === 1800,
    JSON.stringify(rr)
  );
  const srRow = groups["Scenario Review"] || {};
  check(
    "test_standing: the Scenario Review detail parts ride the group's row",
    srRow.kind === "interval" && srRow.period_seconds === 43200 &&
      srRow.detail && same(srRow.detail.not_run, ["journey-b"]) &&
      same(srRow.detail.quarantine, [{ check: "journey-a:check-1", skipped: 2 }]) &&
      srRow.detail.checks && srRow.detail.checks[0].name === "home:loads",
    JSON.stringify(srRow)
  );
  check(
    "test_standing: the freshness mark stands",
    typeof json.answer.judged_at === "string",
    JSON.stringify(json.answer.judged_at)
  );
}

console.log(
  "test_operator_door: " + passed + " passed, " + failed + " failed, " +
    (passed + failed) + " checks"
);
process.exit(failed ? 1 : 0);
