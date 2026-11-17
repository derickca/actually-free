// The Ops page's gate (issue #32): /ops is served by this
// Function, never as a published static page. A session
// holding the Ops grant — the Ops role's standing, or the
// test standing read-only — gets the full page
// (lib/ops-page.js, generated from build_ops_page in
// generate.py). Anyone else — signed out, or signed in
// without the grant — gets the site's ordinary 404 page
// (lib/not-found-page.js, generated from build_404) with
// status 404, the same face as any missing page: the answer
// names neither Ops nor a sign-in road, and no script of
// the Ops page runs for it (EV-OPS-37). Both answers carry
// no-store: which face a request gets turns on the session
// it carries, so no cache may keep one face for another
// request (EV-OPS-18). The data read's own answers stand in
// functions/ops/data.js.
import {
  DEFAULT_INITIALS_COMBO,
  initialsSvg,
} from "./lib/memberspark-kit/memberspark.js";
import { OPS_PAGE_HTML } from "./lib/ops-page.js";
import {
  recordFunctionError,
  recordSignInRefusal,
} from "./lib/ops-log.js";
import {
  TEST_BANNER,
  escHtml,
  getSettings,
  notFoundResponse,
  sessionOf,
  standingOf,
  testGate,
} from "./lib/ops-door.js";

const GLYPH =
  '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" aria-hidden="true"><circle cx="12" cy="8" r="3.6"/><path d="M4.5 20c1.2-3.6 4-5.4 7.5-5.4s6.3 1.8 7.5 5.4"/></svg>';

function accountMark(session) {
  // The person's own mark, drawn by the kit's initials
  // drawing from the claim's letters and combo — never
  // letters worked out from a name here. Where a token
  // carried no initials, a plain glyph in a solid disc
  // stands in its place.
  if (session.initials) {
    return (
      '<span class="ops-mark">' +
      initialsSvg(session.initialsCombo || DEFAULT_INITIALS_COMBO, session.initials, "opsmark") +
      "</span>"
    );
  }
  return '<span class="ops-mark ops-mark-fallback">' + GLYPH + "</span>";
}

export async function onRequest({ request, env }) {
  const settings = getSettings(env);
  try {
    return await serve(request, settings);
  } catch (err) {
    // A failure of the road itself (issue #50): the error
    // log carries it before it propagates, and the failure
    // itself is unchanged.
    await recordFunctionError(settings, {
      signature: "ops_page_failure",
      where: "/ops",
      cause: err,
    });
    throw err;
  }
}

async function serve(request, settings) {
  const session = await sessionOf(settings, request);
  const standing = standingOf(settings, session);

  // The gate's audit entry (issue #50): a signed-in arrival
  // answered with the 404 face for want of standing writes
  // its refusal before the answer leaves. A signed-out
  // arrival is the ordinary missing page and writes nothing;
  // a test account's gated write is the test gate's refusal,
  // not an audit event, and writes nothing either.
  if (session && !standing) {
    await recordSignInRefusal(settings, {
      door: "ops-page",
      reason: "no-standing",
    });
  }

  if (request.method !== "GET" && request.method !== "HEAD") {
    // TA-7: a test account's every change is refused at the
    // gate. No acts stand on this surface for anyone, so
    // every other write meets the same 404 face as a road
    // that does not stand.
    const gated = testGate(settings, session, standing, request);
    if (gated) return gated;
    return notFoundResponse(settings, session, standing);
  }

  if (!standing) return notFoundResponse(settings, session, standing);

  const html = OPS_PAGE_HTML
    .replace("<!--ACCOUNT_MARK-->", accountMark(session))
    .replace(
      "<!--ACCOUNT_NAME-->",
      escHtml(session.name || session.email || "Your MemberSpark account")
    )
    .replace(
      "<!--TEST_BANNER-->",
      standing === "test"
        ? '<div class="ops-banner">' + TEST_BANNER + "</div>"
        : ""
    );
  const headers = {
    "content-type": "text/html; charset=utf-8",
    "cache-control": "no-store",
  };
  if (standing === "test") headers["x-viewer"] = "read-only";
  return new Response(request.method === "HEAD" ? null : html, {
    status: 200,
    headers,
  });
}
