// The run-record door (issue #55): the road the product's
// own reporter (tools/reporter.py) seats a run's record
// through, so the record stands in the product's own store
// (AF_LOGS) and the operator door's test_standing question
// can answer from it. The shape follows the certifiable
// .media shop's run-record door: one POST address carrying
// a key of its own, apart from any other door's credential.
//
// The door ships dark: while no key stands placed (the
// AF_RUN_RECORD_KEY placement, read by this door alone),
// every call answers 404, so the door does not confirm it
// exists. With a key placed, a call that fails the key
// answers 401; a body that is not a run report for this
// product answers 400; and a record that could not be
// written answers 500, so the reporter's fail-soft send
// prints the refusal and the run it describes never fails
// for it. The reporter declares its event expectations at
// the centre alone — a declaration is the centre's row,
// not a run — so this door takes starts and finishes only.
import { recordTestRun } from "../lib/operator-log.js";
import { OPERATOR_PRODUCT_ID } from "../lib/operator-auth.js";

const NO_STORE = { "cache-control": "no-store" };
const GROUPS = new Set(["Build Tests", "Release Review", "Scenario Review"]);

function jsonResponse(body, status) {
  return new Response(JSON.stringify(body), {
    status,
    headers: { "content-type": "application/json", ...NO_STORE },
  });
}

export async function onRequest(context) {
  const env = context.env || {};
  const key = env.AF_RUN_RECORD_KEY || "";
  if (!key) return jsonResponse({ error: "Not found." }, 404);
  if (context.request.method !== "POST") {
    return jsonResponse({ error: "Not found." }, 404);
  }
  if (context.request.headers.get("authorization") !== "Bearer " + key) {
    return jsonResponse({ error: "Not admitted." }, 401);
  }
  let body = null;
  try {
    body = await context.request.json();
  } catch {
    body = null;
  }
  if (
    !body ||
    typeof body !== "object" ||
    body.product !== OPERATOR_PRODUCT_ID ||
    !GROUPS.has(body.group) ||
    body.kind !== "run" ||
    (body.phase !== "start" && body.phase !== "finish") ||
    typeof body.run_id !== "string" ||
    !body.run_id ||
    typeof body.started_at !== "string" ||
    !body.started_at ||
    (body.phase === "finish" &&
      (typeof body.finished_at !== "string" || !body.finished_at ||
        (body.result !== "pass" && body.result !== "fail")))
  ) {
    return jsonResponse({ error: "Bad request." }, 400);
  }
  const written = await recordTestRun(env, body);
  if (!written) {
    return jsonResponse({ error: "The run record could not be written." }, 500);
  }
  return jsonResponse({ recorded: true }, 200);
}
