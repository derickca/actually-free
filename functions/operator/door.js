// The operator door for MemberSpark Admin (issue #55), on
// the fleet operator contract (MemberSpark docs/spec/
// operator-doors.md). The shape is the certifiable.media
// shop's door carried to this product: one POST address
// carrying the door's credential (the Bearer header against
// the OPERATOR_DOOR_SECRET placement, read by this door
// alone) plus a short-lived assertion minted for that one
// call, verified in functions/lib/operator-auth.js.
//
// The door ships dark: while no credential stands placed,
// every call answers the site's ordinary 404 page — the
// same bytes Pages serves for any missing page — so the
// door does not confirm it exists; a non-POST call answers
// the same face with the credential placed. With a
// credential placed, a call that fails the credential
// answers 401, and a call that fails the assertion answers
// 401, in the shop's shapes; a question this door does not
// name, and every act, answers 400. Refused calls write a
// best-effort entry to the door's refusal log; no answer
// ever changes for that write.
//
// Every admitted call writes its lookup to the product's
// own audit log (AF_LOGS, functions/lib/operator-log.js)
// before it answers, and the answer envelope says so —
// { answered_at, audit: { written: true, at }, answer } —
// because Admin refuses an answer that does not confirm
// the write. If the write fails, the door sends no answer.
//
// The questions are the ones this door names and no others:
// - explain_finding (subject: the finding reference,
//   verbatim) — the contract's one question that writes: an
//   explanation recorded in Admin for one of this product's
//   findings is carried into the product's own audit log
//   under the act name finding-explained, with the
//   assertion's admin id as the actor, before the door
//   answers { recorded: true }. A missing, empty or
//   over-2,000-character explanation is a request-shape
//   refusal, before any assertion work. For this question
//   the audit write is the finding entry itself.
// - errors, audit, backups, test_standing, adoption
//   (subject: the product's own id) — the per-product
//   questions, composed live from the product's own records
//   by functions/lib/operator-standing.js. A call naming
//   any other subject for one of these is refused: the
//   questions are about this product alone.
//
// No act is named for this product in the scenarios today,
// so every act is refused, as is every other question —
// a door that could be asked a new kind of question
// without a change to the contract is how roads widen
// quietly.
import {
  verifyOperatorAssertion,
  OPERATOR_PRODUCT_ID,
} from "../lib/operator-auth.js";
import {
  recordOperatorLookup,
  recordFindingExplanation,
  recordOperatorRefusal,
  listFamily,
  listFamilyKeys,
} from "../lib/operator-log.js";
import {
  buildErrorsAnswer,
  buildAuditAnswer,
  buildBackupsAnswer,
  buildTestStandingAnswer,
  buildAdoptionAnswer,
  AUDIT_FAMILIES,
} from "../lib/operator-standing.js";
import { NOT_FOUND_HTML } from "../lib/not-found-page.js";

const NO_STORE = { "cache-control": "no-store" };
const QUESTIONS = new Set([
  "explain_finding",
  "errors",
  "audit",
  "backups",
  "test_standing",
  "adoption",
]);
const PRODUCT_QUESTIONS = new Set([
  "errors",
  "audit",
  "backups",
  "test_standing",
  "adoption",
]);

function jsonResponse(body, status) {
  return new Response(JSON.stringify(body), {
    status,
    headers: { "content-type": "application/json", ...NO_STORE },
  });
}

// The dark face: the site's ordinary 404 page, byte for
// byte, so the door reads as no door at all.
function notFoundResponse() {
  return new Response(NOT_FOUND_HTML, {
    status: 404,
    headers: { "content-type": "text/html; charset=utf-8", ...NO_STORE },
  });
}

function envelope(at, answer) {
  return {
    answered_at: new Date().toISOString(),
    audit: { written: true, at },
    answer,
  };
}

async function readJsonBody(request) {
  try {
    const body = await request.json();
    return body && typeof body === "object" ? body : null;
  } catch {
    return null;
  }
}

export async function onRequest(context) {
  const env = context.env || {};
  const secret = env.OPERATOR_DOOR_SECRET || "";
  if (!secret) return notFoundResponse();
  if (context.request.method !== "POST") return notFoundResponse();
  if (context.request.headers.get("authorization") !== "Bearer " + secret) {
    await recordOperatorRefusal(env, { reason: "credential" });
    return jsonResponse({ error: "Not admitted." }, 401);
  }
  const body = await readJsonBody(context.request);
  if (!body) return jsonResponse({ error: "Bad request." }, 400);
  // An act-shaped call: no act is named for this product,
  // so every act is refused before any assertion work.
  if (typeof body.act === "string" && body.act) {
    await recordOperatorRefusal(env, { reason: "act" });
    return jsonResponse({ error: "Unknown act." }, 400);
  }
  const question = body.question;
  if (!QUESTIONS.has(question)) {
    await recordOperatorRefusal(env, { reason: "question" });
    return jsonResponse({ error: "Unknown question." }, 400);
  }
  // explain_finding's explanation bound is a request-shape
  // refusal the contract places before any assertion work:
  // a missing, empty or over-long explanation answers 400
  // whatever assertion the call carries.
  if (question === "explain_finding") {
    const explanation = body.explanation;
    if (
      typeof explanation !== "string" ||
      explanation.length < 1 ||
      explanation.length > 2000
    ) {
      await recordOperatorRefusal(env, { reason: "shape" });
      return jsonResponse({ error: "Bad request." }, 400);
    }
  }
  const claims = await verifyOperatorAssertion(env, body.assertion, body);
  if (!claims) {
    await recordOperatorRefusal(env, { reason: "assertion" });
    return jsonResponse({ error: "Not admitted." }, 401);
  }
  const subject =
    body.subject === undefined || body.subject === null
      ? null
      : String(body.subject);
  if (!subject) return jsonResponse({ error: "Bad request." }, 400);
  // The per-product questions are about this product alone:
  // a subject that is not the product's own id is a request
  // this door does not answer, whatever the assertion the
  // call carries verified against.
  if (PRODUCT_QUESTIONS.has(question) && subject !== OPERATOR_PRODUCT_ID) {
    return jsonResponse({ error: "Bad request." }, 400);
  }

  const at = new Date().toISOString();

  if (question === "explain_finding") {
    // The contract's one question that writes: the
    // explanation stands in the product's own audit log
    // before the door answers, and a failed write sends no
    // answer. The subject is the finding reference, carried
    // verbatim; the entry is this call's audit write, so
    // the envelope confirms it as it confirms a lookup.
    const written = await recordFindingExplanation(env, {
      by: claims.sub,
      target: subject,
      explanation: body.explanation,
      at,
    });
    if (!written) {
      return jsonResponse(
        { error: "The audit record could not be written." },
        500
      );
    }
    return jsonResponse(envelope(at, { recorded: true }), 200);
  }

  // The audit write comes first: who looked (the
  // assertion's admin id, or the centre itself), at what,
  // which question, and that the road was Admin. A failed
  // write sends no answer.
  const lookupWritten = await recordOperatorLookup(env, {
    by: claims.sub,
    subject,
    question,
    at,
  });
  if (!lookupWritten) {
    return jsonResponse(
      { error: "The audit record could not be written." },
      500
    );
  }

  const now = new Date();
  let answer;
  if (question === "errors") {
    const held = await listFamily(env, "site-error");
    answer = buildErrorsAnswer(held.map((h) => h.entry), now);
  } else if (question === "audit") {
    const gathered = {};
    for (const [, prefix] of AUDIT_FAMILIES) {
      const [held, keys] = await Promise.all([
        listFamily(env, prefix),
        listFamilyKeys(env, prefix),
      ]);
      gathered[prefix] = { entries: held.map((h) => h.entry), keys };
    }
    // The contract's hour form rides the body: a window
    // field naming "hour" asks for the last closed hour in
    // the same shape; no field, or one naming "day", asks
    // for the newest closed day.
    answer = buildAuditAnswer(gathered, now, { window: body.window });
  } else if (question === "backups") {
    answer = buildBackupsAnswer(now);
  } else if (question === "test_standing") {
    const held = await listFamily(env, "test-run");
    answer = buildTestStandingAnswer(held.map((h) => h.entry), now);
  } else if (question === "adoption") {
    answer = buildAdoptionAnswer(now);
  }
  return jsonResponse(envelope(at, answer), 200);
}
