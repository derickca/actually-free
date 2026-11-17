// The MemberSpark sign-in road (issue #32), on the pinned
// kit (functions/lib/memberspark-kit/, the commit
// docs/memberspark-kit/PINNED.json records). The Ops
// surface is this site's only signed-in face, so the road
// serves it alone: the sign-in start carries returnTo
// "/ops", and a completed sign-in mints the Ops session
// (functions/lib/ops-session.js) with the standing judged
// from the verified token — identity.hasOps for this
// product, read once here, the kit's rule — and lands on
// /ops, where the standing decides the face.
//
// The callback is called directly and its answer composed,
// per the kit's README: a word outcome (the person
// cancelled, declined, or MemberSpark answered a failure
// word) is served exactly as the kit returns it, before any
// arrival logic; a completed identity gets this product's
// session cookie FIRST on the answer, at Path=/, ahead of
// the kit's own flow-cookie clears, so no Set-Cookie after
// it can shadow it (the shop's #165). A callback with no
// standing flow (err.noFlow) is sent back to the sign-in
// start; a foreign issuer (err.unknownIssuer) gets the
// kit's not-a-return page; every other failure gets the
// kit's problem page. Every answer carries no-store.
//
// The door's own audit log (issue #50, lib/ops-log.js):
// every refusal above writes its entry before the answer
// leaves, and a completed sign-in writes its completion
// beside the session it mints — fixed words, no personal
// fields, best-effort. A failure this road cannot answer
// (a throwable that is no refusal) is written to the error
// log before it propagates.
//
// Two kit roads are not wired in this build and answer the
// site's ordinary 404 page: backchannel-logout (this
// product holds no session store for the centre to end by
// sid, and holds no standing session index) and events (no
// event handlers stand). Sign-out stands in
// functions/ops-signout.js, on the front-channel road.
import {
  ROUTES,
  routeName,
  signInNotReturnPage,
  signInProblemPage,
} from "../../lib/memberspark-kit/memberspark.js";
import { NOT_FOUND_HTML } from "../../lib/not-found-page.js";
import {
  recordFunctionError,
  recordSignInCompletion,
  recordSignInRefusal,
} from "../../lib/ops-log.js";
import {
  clearSessionCookieHeader,
  mintSessionCookie,
} from "../../lib/ops-session.js";
import {
  PRODUCT_ID,
  PRODUCT_NAME,
  doorConfigured,
  getSettings,
  kitFor,
  standingOf,
} from "../../lib/ops-door.js";

function htmlPage(html, extraHeaders = {}) {
  return new Response(html, {
    status: 200,
    headers: {
      "content-type": "text/html; charset=utf-8",
      "cache-control": "no-store",
      ...extraHeaders,
    },
  });
}

function plain404() {
  return new Response(NOT_FOUND_HTML, {
    status: 404,
    headers: {
      "content-type": "text/html; charset=utf-8",
      "cache-control": "no-store",
    },
  });
}

function redirect303(location) {
  return new Response(null, {
    status: 303,
    headers: { location, "cache-control": "no-store" },
  });
}

function problemReason(err) {
  const msg = String((err && err.message) || "");
  if (/iss is not|not the issuer/.test(msg)) return "iss-mismatch";
  if (/state does not match/.test(msg)) return "state-mismatch";
  if (/signature|signing key|expired|exp must|audience|aud is/.test(msg)) {
    return "token-invalid";
  }
  return undefined;
}

function signedOutPage(origin) {
  const html =
    "<!DOCTYPE html>\n" +
    '<html lang="en">\n<head>\n<meta charset="utf-8">\n' +
    '<meta name="viewport" content="width=device-width, initial-scale=1">\n' +
    "<title>Signed out \u2014 Actually Free</title>\n" +
    '<link rel="stylesheet" href="/assets/styles.css">\n</head>\n' +
    '<body>\n<main class="ops-main">\n<section class="ops-panel">\n' +
    "<h1>Signed out</h1>\n" +
    "<p>You have signed out of the Ops surface.</p>\n" +
    '<p><a href="/">Back to Actually Free</a> \u00b7 <a href="' +
    ROUTES.signIn +
    '">Sign in again</a></p>\n' +
    "</section>\n</main>\n</body>\n</html>\n";
  return htmlPage(html, { "set-cookie": clearSessionCookieHeader() });
}

// The door's audit writes (issue #50): every refusal this
// road answers writes its entry to the product's own audit
// log before the answer leaves, under the fixed word the
// road names — the kit flags in plain words, or the problem
// page's own reason. A completed sign-in writes its
// completion beside the session it mints. The writes are
// best-effort (lib/ops-log.js): no answer changes because
// its record could not be written. Answers the refusal here
// (the restart redirect, the not-a-return page) or returns
// null, leaving the problem page to the caller.
async function auditRefusal(settings, err, origin) {
  if (err && err.noFlow) {
    await recordSignInRefusal(settings, { door: "ops-door", reason: "no-flow" });
    return redirect303(ROUTES.signIn);
  }
  if (err && err.unknownIssuer) {
    await recordSignInRefusal(settings, {
      door: "ops-door",
      reason: "foreign-issuer",
    });
    return htmlPage(
      signInNotReturnPage({
        productName: PRODUCT_NAME,
        homeUrl: origin + "/",
      })
    );
  }
  if (err instanceof Error) {
    await recordSignInRefusal(settings, {
      door: "ops-door",
      reason: problemReason(err) || "unverified",
    });
  }
  return null;
}

async function handleCallback(settings, ms, request) {
  let done;
  try {
    done = await ms.callback(request);
  } catch (err) {
    const answered = await auditRefusal(
      settings,
      err,
      new URL(request.url).origin
    );
    if (answered) return answered;
    return htmlPage(
      signInProblemPage({
        productName: PRODUCT_NAME,
        homeUrl: new URL(request.url).origin + "/",
        reason: problemReason(err),
      })
    );
  }
  if (!done.identity) {
    // A word outcome, or the popup completion page: the
    // kit's answer stands exactly as returned, and no
    // session is minted on it.
    return done.redirect;
  }
  const identity = done.identity;
  const standing = standingOf(settings, {
    sub: identity.sub,
    opsAdmitted: identity.hasOps(PRODUCT_ID),
  });
  const cookie = await mintSessionCookie(
    settings.secret,
    identity,
    standing,
    identity.hasOps(PRODUCT_ID)
  );
  // The completion's audit entry, beside the session it
  // mints (issue #50): the standing the session carries,
  // and no identity.
  await recordSignInCompletion(settings, {
    standing: standing === null ? "none" : standing,
  });
  // Compose: this product's session cookie goes FIRST on
  // the answer, ahead of the kit's own Set-Cookie lines, at
  // Path=/ so it reaches /ops (the shop's #165 shape).
  const source = done.redirect;
  const headers = new Headers(source.headers);
  const kitCookies =
    typeof headers.getSetCookie === "function"
      ? headers.getSetCookie()
      : [headers.get("set-cookie")].filter(Boolean);
  headers.delete("set-cookie");
  headers.append("set-cookie", cookie);
  for (const line of kitCookies) headers.append("set-cookie", line);
  headers.set("cache-control", "no-store");
  return new Response(source.body, { status: source.status, headers });
}

export async function onRequest({ request, env }) {
  const settings = getSettings(env);
  const url = new URL(request.url);
  const name = routeName(url.pathname);
  if (!name) return plain404();
  if (!doorConfigured(settings)) return plain404();
  const ms = kitFor(settings, url.origin);
  try {
    if (name === "signIn") {
      // Called directly, never through route(): the kit's
      // generic dispatcher has no slot for the return.
      return await ms.signIn(request, { returnTo: "/ops" });
    }
    if (name === "callback") {
      return await handleCallback(settings, ms, request);
    }
    if (name === "signedOut") return signedOutPage(url.origin);
    if (name === "backchannelLogout" || name === "events") {
      // Not wired in this build (see the header note).
      return plain404();
    }
    const res = await ms.route(request, {});
    return res || plain404();
  } catch (err) {
    const answered = await auditRefusal(settings, err, url.origin);
    if (answered) return answered;
    if (err instanceof Error) {
      return htmlPage(
        signInProblemPage({
          productName: PRODUCT_NAME,
          homeUrl: url.origin + "/",
          reason: problemReason(err),
        })
      );
    }
    // Not an answerable refusal: the road itself failed.
    // The error log carries it before it propagates (issue
    // #50), and the failure itself is unchanged.
    await recordFunctionError(settings, {
      signature: "auth_road_failure",
      where: "/auth/memberspark/*",
      cause: err,
    });
    throw err;
  }
}
