// The operator door's product-standing answers (issue #55,
// MemberSpark #1021 and #1260): the per-product questions
// composed live from this product's own records — the
// AF_LOGS families the Ops door and this door write
// (functions/lib/ops-log.js and operator-log.js) and the
// run records the reporter seats (operator-log.js) — with
// no summary standing between the page and the data. The
// shapes are the contract's (MemberSpark docs/spec/
// operator-doors.md), in the words the certifiable.media
// shop's door answers in, carried to what this product
// actually keeps:
//
// - errors: this product keeps an error log — the
//   per-occurrence Function failures the Ops door's writers
//   record — so the standing is "present", on the Error
//   Review's hourly windows: the last closed hour and the
//   one before it.
// - audit: this product keeps no chain and no heartbeat, so
//   the answer states its families over the newest closed
//   UTC day (or the last closed hour, on the call's hour
//   form), each family's count witnessed by the family's
//   own key names counted without reading a value, and no
//   chain fields ride. No actor rides this answer: the
//   families carry counts only.
// - backups: this product keeps no backup points — its
//   whole content is the committed tree of its repo, the
//   standing its Ops surface states — so the points list
//   stands empty.
// - test_standing: the product's three groups, answered
//   from the run records the reporter seats in the
//   product's own store beside its centre sends.
// - adoption: this product holds no accounts of its own, so
//   the account fields carry the contract's marker, never
//   zeros and never omitted. It keeps no windowed activity
//   figure of its own — its views are read live from its
//   counter at the centre, a road no door carries — so no
//   active_figure rides.
//
// Every answer is composed live from the records, so each
// carries judged_at as the time it was composed, the
// contract's freshness mark.

const HOUR_MS = 60 * 60 * 1000;
const DAY_MS = 24 * HOUR_MS;

// The Error Review windows: the newest closed hour and the
// one before it.
export function errorWindows(now = new Date()) {
  const end = now.toISOString().slice(0, 14) + "00:00.000Z";
  const current = {
    start: new Date(Date.parse(end) - HOUR_MS).toISOString(),
    end,
  };
  const previous = {
    start: new Date(Date.parse(end) - 2 * HOUR_MS).toISOString(),
    end: current.start,
  };
  return { current, previous };
}

// The Audit Review window: the newest closed UTC day.
export function auditWindow(now = new Date()) {
  const end = now.toISOString().slice(0, 10) + "T00:00:00.000Z";
  return { start: new Date(Date.parse(end) - DAY_MS).toISOString(), end };
}

const inWindow = (at, window) =>
  typeof at === "string" && at >= window.start && at < window.end;

// ---------------- errors ----------------

// The errors answer: the log's standing (this product
// keeps one, so "present"), the current window's bounds
// and total, the previous window's total, the newest
// entry's time, and one line per signature either window
// saw — its count in each window and its first and last
// sightings in the whole log. The entries are the Ops
// door's per-occurrence Function failures, so the log they
// were counted from is named in the contract's set:
// "workers".
export function buildErrorsAnswer(siteErrors = [], now = new Date()) {
  const { current, previous } = errorWindows(now);
  const entries = (Array.isArray(siteErrors) ? siteErrors : []).filter(
    (e) => e && typeof e.at === "string" && typeof e.signature === "string"
  );
  let windowTotal = 0;
  let previousTotal = 0;
  let newestAt = null;
  const lines = new Map();
  for (const entry of entries) {
    if (!newestAt || entry.at > newestAt) newestAt = entry.at;
    let line = lines.get(entry.signature);
    if (!line) {
      line = {
        signature: entry.signature,
        count: 0,
        previous_count: 0,
        first_seen: entry.at,
        last_seen: entry.at,
      };
      lines.set(entry.signature, line);
    }
    if (entry.at < line.first_seen) line.first_seen = entry.at;
    if (entry.at > line.last_seen) line.last_seen = entry.at;
    if (inWindow(entry.at, current)) {
      line.count += 1;
      windowTotal += 1;
    } else if (inWindow(entry.at, previous)) {
      line.previous_count += 1;
      previousTotal += 1;
    }
  }
  const signatures = [...lines.values()]
    .filter((line) => line.count > 0 || line.previous_count > 0)
    .map((line) => ({ ...line, log: "workers" }))
    .sort((a, b) => (a.signature < b.signature ? -1 : 1));
  const answer = {
    log_state: "present",
    window_start: current.start,
    window_end: current.end,
    window_total: windowTotal,
    previous_window_total: previousTotal,
    signatures,
    judged_at: now.toISOString(),
  };
  if (newestAt) answer.newest_at = newestAt;
  return answer;
}

// ---------------- audit ----------------

// The families this product's records cover, in the
// answer's plain words: the operator door's own lookups
// and finding explanations, and the Ops door's sign-in
// audit log. None stands high-risk — this product takes no
// payment and makes no decision on a person — so no
// high_risk mark rides.
export const AUDIT_FAMILIES = Object.freeze([
  ["operator lookups", "operator-lookup"],
  ["finding explanations", "finding-explanation"],
  ["sign-in refusals", "sign-in-refusal"],
  ["sign-in completions", "sign-in-completion"],
]);

// The witness every family carries: the count was checked
// against the family's own key names, counted without
// reading a value — the store's list is a second road to
// the same entries, so the two counts agreeing is the
// family's proof it was counted whole.
export const AUDIT_WITNESS =
  "entries standing in the product's log store, counted from their key names alone";

// A key name's entry time: family ":" time ":" uuid, and
// the time itself carries colons, so the time is what
// stands between the family's prefix and the last colon.
function keyTime(family, key) {
  const rest = key.slice(family.length + 1);
  const cut = rest.lastIndexOf(":");
  return cut > 0 ? rest.slice(0, cut) : "";
}

// The audit answer: the families counted over the window
// the call names — the newest closed day, or the last
// closed hour on the hour form — each with its witness
// count from the family's key names; the newest closed
// day the answer stands on in both forms; the newest
// entry's time across the families' whole log; and the
// window the families were counted over.
export function buildAuditAnswer(gathered = {}, now = new Date(), options = {}) {
  const dayWindow = auditWindow(now);
  const hourForm = options && options.window === "hour";
  const window = hourForm ? errorWindows(now).current : dayWindow;
  const families = [];
  let newestAt = null;
  for (const [family, prefix] of AUDIT_FAMILIES) {
    const held = gathered[prefix] || { entries: [], keys: [] };
    let auditCount = 0;
    for (const entry of held.entries) {
      if (entry && typeof entry.at === "string") {
        if (!newestAt || entry.at > newestAt) newestAt = entry.at;
        if (inWindow(entry.at, window)) auditCount += 1;
      }
    }
    let witnessCount = 0;
    for (const key of held.keys) {
      if (inWindow(keyTime(prefix, key), window)) witnessCount += 1;
    }
    families.push({
      family,
      audit_count: auditCount,
      witness_count: witnessCount,
      witness: AUDIT_WITNESS,
    });
  }
  const answer = {
    families,
    newest_closed_day: dayWindow.start.slice(0, 10),
    window_start: window.start,
    window_end: window.end,
    judged_at: now.toISOString(),
  };
  if (newestAt) answer.newest_at = newestAt;
  return answer;
}

// ---------------- backups ----------------

// The backups answer: no point stands for this product —
// the repo is its record, as its Ops surface states — so
// the list stands empty, with the freshness mark.
export function buildBackupsAnswer(now = new Date()) {
  return { points: [], judged_at: now.toISOString() };
}

// ---------------- adoption ----------------

// The adoption answer: no accounts of its own, so every
// account field carries the contract's marker — never
// zeros, never omitted — and no active figure rides, for
// the reason the header states.
export function buildAdoptionAnswer(now = new Date()) {
  return {
    accounts_standing: "not applicable",
    new_day: "not applicable",
    new_week: "not applicable",
    new_month: "not applicable",
    active_day: "not applicable",
    active_week: "not applicable",
    active_month: "not applicable",
    judged_at: now.toISOString(),
  };
}

// ---------------- test_standing ----------------

// Each group's stated cadence, in the registry's words:
// the Build Tests and the Release Review run on their
// events — a change, a release — with the standing event
// windows the reporter declares by (tools/reporter.py's
// own windows: Build Tests due an hour after its event,
// Release Review thirty minutes after its, each with a
// two-hour grace); the Scenario Review runs on its
// interval, the registered twice-daily expectation, a
// twelve-hour period with a two-hour grace.
const TEST_CADENCE = Object.freeze({
  "Build Tests": { kind: "event", due_after_seconds: 3600, grace_seconds: 7200 },
  "Release Review": { kind: "event", due_after_seconds: 1800, grace_seconds: 7200 },
  "Scenario Review": { kind: "interval", period_seconds: 43200, grace_seconds: 7200 },
});
const TEST_GROUPS = Object.freeze(Object.keys(TEST_CADENCE));
const RUNS_FLOOR = 30;
const RUNS_WINDOW_MS = 30 * DAY_MS;

// A finish's detail part, in the contract's shape: the
// checks part every group carries — a list of { name, ok }
// with the check's own words riding as their fields — and,
// for the Scenario Review group alone, its own parts: the
// checks the run did not run, and its quarantined checks
// with their skipped counts. A finish that recorded no
// checks carries no checks part; a finish carrying no part
// at all carries no detail.
function finishDetail(finish, group) {
  const detail = {};
  if (Array.isArray(finish.checks) && finish.checks.length) {
    detail.checks = finish.checks
      .filter((c) => c && typeof c.name === "string")
      .map((c) => {
        const out = { name: c.name, ok: !!c.ok };
        if (typeof c.statement === "string" && c.statement) {
          out.statement = c.statement;
        } else {
          if (typeof c.detail === "string" && c.detail) out.detail = c.detail;
          if (typeof c.expected === "string" && c.expected) out.expected = c.expected;
          if (typeof c.got === "string" && c.got) out.got = c.got;
        }
        return out;
      });
  }
  if (group === "Scenario Review") {
    const parts =
      finish.details && typeof finish.details === "object" ? finish.details : {};
    if (Array.isArray(parts.not_run)) {
      detail.not_run = parts.not_run.filter((n) => typeof n === "string");
    }
    if (Array.isArray(parts.quarantine)) {
      detail.quarantine = parts.quarantine
        .filter((q) => q && typeof q.check === "string")
        .map((q) => {
          const out = { check: q.check };
          if (Number.isInteger(q.skipped) && q.skipped >= 0) {
            out.skipped = q.skipped;
          }
          return out;
        });
    }
  }
  return Object.keys(detail).length ? detail : null;
}

// The test_standing answer: one row per group the product
// runs, from the run records standing in its own store.
// A group's row names its last finished run — its result
// in the store's words and its time, both absent where the
// group has never finished a run — the count of the
// group's finishes the records hold, the newest finish's
// time, the group's runs (every run still open and the
// newest finishes: at least the newest thirty, and every
// finish of the last thirty days where that reaches
// further), and the cadence the product states for it.
export function buildTestStandingAnswer(reports = [], now = new Date()) {
  const byGroup = new Map(TEST_GROUPS.map((g) => [g, []]));
  for (const record of Array.isArray(reports) ? reports : []) {
    if (
      record &&
      byGroup.has(record.group) &&
      typeof record.run_id === "string" &&
      (record.phase === "start" || record.phase === "finish")
    ) {
      byGroup.get(record.group).push(record);
    }
  }
  const groups = TEST_GROUPS.map((group) => {
    const cadence = TEST_CADENCE[group];
    const records = byGroup.get(group);
    const finishes = records
      .filter((r) => r.phase === "finish")
      .sort((a, b) => String(b.finished_at).localeCompare(String(a.finished_at)));
    const newest = finishes[0] || null;
    const row = { group, kind: cadence.kind };
    if (cadence.period_seconds !== undefined) {
      row.period_seconds = cadence.period_seconds;
    }
    if (cadence.due_after_seconds !== undefined) {
      row.due_after_seconds = cadence.due_after_seconds;
    }
    if (cadence.grace_seconds !== undefined) {
      row.grace_seconds = cadence.grace_seconds;
    }
    row.finishes = finishes.length;
    if (newest) {
      if (typeof newest.result === "string") row.result = newest.result;
      if (typeof newest.finished_at === "string") {
        row.at = newest.finished_at;
        row.newest_finish_at = newest.finished_at;
      }
      const detail = finishDetail(newest, group);
      if (detail) row.detail = detail;
    }
    // The runs list: every run still open, and the newest
    // finishes — the newest thirty at least, and every
    // finish inside the last thirty days where that
    // reaches further — newest first.
    const cutoff = new Date(now.getTime() - RUNS_WINDOW_MS).toISOString();
    const keptFinishes = finishes.filter(
      (r, i) => i < RUNS_FLOOR || String(r.finished_at) >= cutoff
    );
    const open = records
      .filter((r) => r.phase === "start")
      .sort((a, b) => String(b.started_at).localeCompare(String(a.started_at)));
    row.runs = [
      ...open.map((r) => ({ run: r.run_id })),
      ...keptFinishes.map((r) => {
        const entry = { run: r.run_id };
        if (typeof r.result === "string") entry.result = r.result;
        if (typeof r.finished_at === "string") entry.at = r.finished_at;
        const detail = finishDetail(r, group);
        if (detail) entry.detail = detail;
        return entry;
      }),
    ];
    return row;
  });
  return { groups, judged_at: now.toISOString() };
}
