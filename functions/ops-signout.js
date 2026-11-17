// Sign-out (issue #32): end this product's session, then
// send the browser to MemberSpark's own sign-out with the
// session's sid as the hint, the kit's shape — no ID token
// travels in the address. The landing is the kit's
// signed-out address, which this product serves itself.
// Sign-out is one of the two acts the test standard leaves
// open to a test account (TA-7), so no gate stands here.
import { ROUTES } from "./lib/memberspark-kit/memberspark.js";
import { recordFunctionError } from "./lib/ops-log.js";
import { clearSessionCookieHeader } from "./lib/ops-session.js";
import {
  doorConfigured,
  getSettings,
  kitFor,
  notFoundResponse,
  sessionOf,
  standingOf,
} from "./lib/ops-door.js";

export async function onRequest({ request, env }) {
  const settings = getSettings(env);
  try {
    return await serve(request, settings);
  } catch (err) {
    // A failure of the road itself (issue #50): the error
    // log carries it before it propagates, and the failure
    // itself is unchanged.
    await recordFunctionError(settings, {
      signature: "ops_signout_failure",
      where: "/ops-signout",
      cause: err,
    });
    throw err;
  }
}

async function serve(request, settings) {
  const session = await sessionOf(settings, request);
  const standing = standingOf(settings, session);
  if (request.method !== "POST") {
    return notFoundResponse(settings, session, standing);
  }
  const origin = new URL(request.url).origin;
  const headers = {
    location: doorConfigured(settings)
      ? kitFor(settings, origin).signOutUrl(
          session ? session.sid : null,
          origin + ROUTES.signedOut
        )
      : "/",
    "cache-control": "no-store",
  };
  headers["set-cookie"] = clearSessionCookieHeader();
  if (standing === "test") headers["x-viewer"] = "read-only";
  return new Response(null, { status: 303, headers });
}
