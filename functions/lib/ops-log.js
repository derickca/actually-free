// The Ops door's own two logs (issue #50): an audit log of
// the door's sign-in refusals and completions, and an error
// log of the product's Function failures. Until this build
// the product's Functions wrote nothing anywhere, so a
// refusal or a completion at this door was recorded nowhere
// in the product — the centre's audit covers the centre's
// side of the exchange only (the #47 review; docs/LOGGING.md
// carries the standing).
//
// The shapes are the certifiablemedia shop's, carried over
// where they fit this product: entries under family keys in
// one KV store (the AF_LOGS binding), fixed vocabularies the
// writers themselves enforce, and no personal fields — no
// email, no sub, no name; an entry proves an event at the
// door, never whose. Two shop pieces do not fit and do not
// stand here: the running audit sequence (it feeds the
// shop's door answers and centre summaries; this product has
// no operator door and sends no summaries, so no count reads
// a sequence) and the daily error counts (the per-occurrence
// entries are the record here; nothing counts them).
//
// Every writer is best-effort and never throws: each call
// site awaits its write before the answer leaves, so the
// entry stands before the answer does, and no answer ever
// changes because its record could not be written — a door
// standing dark (no store bound) writes nothing and answers
// exactly as it did before this build. The writes are the
// product's own machinery, never a person's act: they ride
// the door's roads for every standing alike, and the test
// gate's refusals are not audit events and write nothing.

export const LOG_BINDING = "AF_LOGS";

// The doors an entry may name: the sign-in road itself and
// the two surface roads whose 404 face a no-standing arrival
// meets.
const REFUSAL_DOORS = new Set(["ops-door", "ops-page", "ops-data"]);

// The fixed refusal words: the door's own vocabulary — the
// callback road's problem words (iss-mismatch, state-
// mismatch, token-invalid), its two kit flags named plainly
// (no-flow, foreign-issuer), the unverifiable remainder, and
// the Ops gate's want-of-standing word.
const REFUSAL_REASONS = new Set([
  "no-flow",
  "foreign-issuer",
  "iss-mismatch",
  "state-mismatch",
  "token-invalid",
  "unverified",
  "no-standing",
]);

// A completion's standing, in the door's own words: the two
// standings standingOf judges, and "none" for a session that
// minted and admits nothing.
const COMPLETION_STANDINGS = new Set(["ops", "test", "none"]);

// The error log's fixed signature list: one per Function
// road this product carries.
const ERROR_SIGNATURES = new Set([
  "auth_road_failure",
  "ops_page_failure",
  "ops_data_failure",
  "ops_signout_failure",
]);

export const LOG_TEXT_BOUND = 500;

// The shop's scrubber, carried over with one tightening:
// log text keeps no address, no token-shaped run (twenty or
// more characters mixing letters and digits) and no digit
// run of twelve or more, and what survives is cut to the
// bound. The address pattern here cannot cross a quote or a
// brace, so an address standing inside a spaceless JSON body
// is stripped alone and the fields after it survive (the
// shop's pattern eats the body's tail there — its #197).
export function scrubLogText(value, bound = LOG_TEXT_BOUND) {
  let text = value === null || value === undefined ? "" : String(value);
  text = text
    .replace(/[^\s@",{}[\]]+@[^\s@",{}[\]]+\.[^\s@",{}[\]]+/g, "[stripped]")
    .replace(/[A-Za-z0-9+/=_-]{20,}/g, (run) =>
      /[A-Za-z]/.test(run) && /[0-9]/.test(run) ? "[stripped]" : run
    )
    .replace(/\d{12,}/g, "[stripped]")
    .replace(/\s+/g, " ")
    .trim();
  return text.length > bound ? text.slice(0, bound) : text;
}

function isoTime(at) {
  if (at instanceof Date) return at.toISOString();
  if (typeof at === "number" && Number.isFinite(at)) {
    return new Date(at).toISOString();
  }
  return new Date().toISOString();
}

function storeOf(settings) {
  return (settings && settings.logs) || null;
}

async function writeEntry(settings, family, entry) {
  try {
    const ns = storeOf(settings);
    if (!ns) return false;
    await ns.put(
      family + ":" + entry.at + ":" + crypto.randomUUID(),
      JSON.stringify(entry)
    );
    return true;
  } catch {
    return false;
  }
}

// One entry per refused sign-in: at the callback, the fixed
// reason the road names; at the Ops gate, a signed-in arrival
// answered with the 404 face for want of standing, under
// "no-standing". A word outside the fixed sets is refused by
// the writer and writes nothing.
export async function recordSignInRefusal(settings, input = {}) {
  const door = String(input.door || "");
  const reason = String(input.reason || "");
  if (!REFUSAL_DOORS.has(door) || !REFUSAL_REASONS.has(reason)) return false;
  return writeEntry(settings, "sign-in-refusal", {
    kind: "sign-in-refusal",
    action: "sign-in-refusal",
    door,
    reason,
    at: isoTime(input.at),
  });
}

// One entry per completed sign-in, written by the callback
// beside the session it mints: the standing the session
// carries, and no identity — the entry proves a mint, never
// whose.
export async function recordSignInCompletion(settings, input = {}) {
  const standing = String(input.standing || "");
  if (!COMPLETION_STANDINGS.has(standing)) return false;
  return writeEntry(settings, "sign-in-completion", {
    kind: "sign-in-completion",
    door: "ops-door",
    standing,
    at: isoTime(input.at),
  });
}

// One entry per Function failure on the product's own roads:
// when, the road's fixed where and signature, and the
// failure's cause — its message, scrubbed and bounded.
export async function recordFunctionError(settings, input = {}) {
  const signature = String(input.signature || "");
  if (!ERROR_SIGNATURES.has(signature)) return false;
  return writeEntry(settings, "site-error", {
    kind: "site-error",
    at: isoTime(input.at),
    where: String(input.where || ""),
    signature,
    cause: scrubLogText(
      input.cause instanceof Error
        ? input.cause.message
        : input.cause === null || input.cause === undefined
          ? ""
          : String(input.cause)
    ),
  });
}

// The family's newest entries, newest first. The keys carry
// their ISO time, so the store's own key order is the time
// order and the newest stand last; the read takes the tail.
async function listFamily(ns, family, limit) {
  const names = [];
  let cursor;
  do {
    const page = await ns.list({ prefix: family + ":", cursor, limit: 1000 });
    for (const key of page.keys || []) names.push(key.name);
    cursor = page.list_complete ? undefined : page.cursor;
  } while (cursor);
  const entries = [];
  for (const name of names.slice(-limit)) {
    const value = await ns.get(name, "json");
    if (value) entries.push(value);
  }
  return entries.reverse();
}

// The read the Ops surface fronts: the door's recent audit
// entries (refusals and completions together, newest first)
// and its recent error entries. note names the standing when
// there is nothing to show: "not-placed" where no store
// stands bound on the project, "not-read" where the read
// itself failed, "empty" where the store stands and no entry
// does yet.
export async function readDoorLog(settings, limit = 10) {
  const ns = storeOf(settings);
  if (!ns) return { entries: [], errors: [], note: "not-placed" };
  try {
    const [refusals, completions, errors] = await Promise.all([
      listFamily(ns, "sign-in-refusal", limit),
      listFamily(ns, "sign-in-completion", limit),
      listFamily(ns, "site-error", 5),
    ]);
    const entries = [...refusals, ...completions]
      .sort((a, b) => String(b.at).localeCompare(String(a.at)))
      .slice(0, limit);
    return {
      entries,
      errors,
      note: entries.length || errors.length ? null : "empty",
    };
  } catch {
    return { entries: [], errors: [], note: "not-read" };
  }
}
