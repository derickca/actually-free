// The Ops surface's data read (issue #32): the standings
// the page fronts, as JSON — the build record, the
// publishing and checks standings read from the repo's own
// Actions records, and the backup standing in words. Reads
// only: this road writes nothing, and a session without
// standing gets the same 404 the page gives, naming
// nothing. A test-standing session reads the same content
// (TA-6) with the read-only mark on the answer (TA-9), and
// its every write is refused at the gate (TA-7).
import {
  recordFunctionError,
  recordSignInRefusal,
} from "../lib/ops-log.js";
import {
  getSettings,
  jsonResponse,
  notFoundResponse,
  opsData,
  sessionOf,
  standingOf,
  testGate,
} from "../lib/ops-door.js";

export async function onRequest({ request, env }) {
  const settings = getSettings(env);
  try {
    return await serve(request, settings);
  } catch (err) {
    // A failure of the road itself (issue #50): the error
    // log carries it before it propagates, and the failure
    // itself is unchanged.
    await recordFunctionError(settings, {
      signature: "ops_data_failure",
      where: "/ops/data",
      cause: err,
    });
    throw err;
  }
}

async function serve(request, settings) {
  const session = await sessionOf(settings, request);
  const standing = standingOf(settings, session);

  // The gate's audit entry (issue #50): a signed-in arrival
  // answered for want of standing writes its refusal before
  // the answer leaves, as at the page gate.
  if (session && !standing) {
    await recordSignInRefusal(settings, {
      door: "ops-data",
      reason: "no-standing",
    });
  }

  const gated = testGate(settings, session, standing, request);
  if (gated) return gated;
  if (request.method !== "GET" && request.method !== "HEAD") {
    return notFoundResponse(settings, session, standing);
  }
  if (!standing) {
    return jsonResponse(settings, session, standing, 404, { error: "Not found." });
  }
  const data = await opsData(settings, session, standing);
  return jsonResponse(
    settings,
    session,
    standing,
    200,
    request.method === "HEAD" ? {} : data
  );
}
