// The operator door's own records (issue #55), standing in
// the same store as the Ops door's logs (the AF_LOGS
// binding; functions/lib/ops-log.js carries that door's
// families). Three families are this door's:
//
// - operator-lookup: one entry per admitted call, written
//   before the answer leaves — who looked (the assertion's
//   admin id, or the centre itself on a system call), at
//   what, which question, and that the road was Admin. The
//   contract's audit-before-answer rule stands on this
//   write: its writer answers whether the entry stands, and
//   the door sends no answer where it does not.
// - finding-explanation: the one writing question's entries,
//   under the door's own act name for them (below), with the
//   finding reference carried verbatim as the target and the
//   explanation's words as written.
// - operator-refusal: one entry per refused call, best-
//   effort — the refusal's answer never changes for it, as
//   the shop's door records its refusals.
//
// A fourth family is the run record the reporter seats
// (issue #55): test-run, one record per run of the product's
// own groups, keyed by group and run id, holding the
// reporter's start or finish report whole — the record the
// door's test_standing question answers from.
//
// Unlike the Ops door's writers (best-effort, never read
// back by their callers), these writers answer true or
// false and their callers act on it: the door's contract is
// that an unrecorded call is an unanswered call. Entries
// carry no email and no token; a lookup's actor is the
// assertion's admin id, which the contract names as the
// write's own content.

export const FINDING_EXPLAINED_ACT = "finding-explained";

const REFUSAL_REASONS = new Set(["credential", "assertion", "question", "act", "shape"]);

function isoTime(at) {
  if (at instanceof Date) return at.toISOString();
  if (typeof at === "number" && Number.isFinite(at)) {
    return new Date(at).toISOString();
  }
  return new Date().toISOString();
}

function storeOf(env) {
  return (env && env.AF_LOGS) || null;
}

async function writeEntry(env, family, entry) {
  try {
    const ns = storeOf(env);
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

// One entry per admitted lookup, written before the answer:
// who looked, at what, which question, and that the road
// was Admin.
export async function recordOperatorLookup(env, input = {}) {
  return writeEntry(env, "operator-lookup", {
    kind: "operator-lookup",
    action: "operator_lookup",
    by: String(input.by || ""),
    subject: String(input.subject || ""),
    question: String(input.question || ""),
    road: "admin",
    at: isoTime(input.at),
  });
}

// The one writing question's entry: the explanation stands
// in the product's own audit log under the door's act name,
// with the assertion's sub as the actor, the finding
// reference as the target carried verbatim, and the
// explanation's words as written.
export async function recordFindingExplanation(env, input = {}) {
  return writeEntry(env, "finding-explanation", {
    kind: "finding-explanation",
    action: FINDING_EXPLAINED_ACT,
    by: String(input.by || ""),
    target: String(input.target || ""),
    explanation: String(input.explanation || ""),
    at: isoTime(input.at),
  });
}

// One entry per refused call, best-effort: a word outside
// the fixed set writes nothing, and no answer ever changes
// because this write could not land.
export async function recordOperatorRefusal(env, input = {}) {
  const reason = String(input.reason || "");
  if (!REFUSAL_REASONS.has(reason)) return false;
  return writeEntry(env, "operator-refusal", {
    kind: "operator-refusal",
    action: "operator-refusal",
    door: "operator-door",
    reason,
    at: isoTime(input.at),
  });
}

// One run's record, seated by the run-record door from the
// reporter's own report: keyed by the group and the run's
// id, so a finish lands on the same key its start did, and
// the record standing is the run's latest word.
export async function recordTestRun(env, report) {
  try {
    const ns = storeOf(env);
    if (!ns) return false;
    await ns.put(
      "test-run:" + report.group + ":" + report.run_id,
      JSON.stringify(report)
    );
    return true;
  } catch {
    return false;
  }
}

// A family's entries whole, oldest first: the keys carry
// their ISO time, so the store's own key order is the time
// order. The door's families are small — this product's
// logs are per-occurrence records at a directory's volume —
// and the standing answers compose from the whole family,
// as the shop's door composes from its own.
export async function listFamily(env, family) {
  const ns = storeOf(env);
  if (!ns) return [];
  const entries = [];
  let cursor;
  do {
    const page = await ns.list({ prefix: family + ":", cursor, limit: 1000 });
    for (const key of page.keys || []) {
      const value = await ns.get(key.name, "json");
      if (value) entries.push({ key: key.name, entry: value });
    }
    cursor = page.list_complete ? undefined : page.cursor;
  } while (cursor);
  return entries;
}

// A family's key names alone, oldest first: the audit
// answer's witness counts stand on these, counted from the
// names without reading a value.
export async function listFamilyKeys(env, family) {
  const ns = storeOf(env);
  if (!ns) return [];
  const names = [];
  let cursor;
  do {
    const page = await ns.list({ prefix: family + ":", cursor, limit: 1000 });
    for (const key of page.keys || []) names.push(key.name);
    cursor = page.list_complete ? undefined : page.cursor;
  } while (cursor);
  return names;
}
