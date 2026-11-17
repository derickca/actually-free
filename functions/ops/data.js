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
  const session = await sessionOf(settings, request);
  const standing = standingOf(settings, session);

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
