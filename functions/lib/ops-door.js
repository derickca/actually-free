// The Ops surface's shared door (issue #32): the settings,
// the MemberSpark kit instance, the standing judgement and
// the answers every Ops road gives. The sign-in road itself
// stands in functions/auth/memberspark/[[path]].js, on the
// pinned kit (functions/lib/memberspark-kit/, copied at the
// commit docs/memberspark-kit/PINNED.json records).
//
// Admission (EV-OPS-16, EV-ADMIN-7/8): a session reaches the
// surface only while its standing admits it. The Ops standing
// is the decision judged once at sign-in from the verified
// token's ops claim — identity.hasOps(PRODUCT_ID), the kit's
// own judgement — and stored in the session as a boolean,
// never as the claim. The test standing is re-judged on
// every request from the TEST_ACCOUNT_SUBS placement: a sub
// the placement names reads as test, read-only (TA-5).
//
// Every answer this door gives carries Cache-Control:
// no-store. Which face a request gets turns on the session
// it carries, so no cache — edge or service worker — may
// keep one face for another request (EV-OPS-18). The
// service worker's half of the fence stands in generate.py's
// build_sw: it never answers for these roads at all.

import {
  createMemberSparkKit,
  ROUTES,
} from "./memberspark-kit/memberspark.js";
import { NOT_FOUND_HTML } from "./not-found-page.js";
import { BUILD_RECORD } from "./build-record.js";
import {
  parseTestAccountSubs,
  sessionFromRequest,
} from "./ops-session.js";

export const PRODUCT_ID = "actually-free";
export const PRODUCT_NAME = "Actually Free";
export const TEST_BANNER = "Viewing as a test account. Read-only.";

const GITHUB_REPO = "derickca/actually-free";
const PUBLISH_WORKFLOW = "deploy-site.yml";
const CHECK_WORKFLOWS = [
  ["Catalogue validation", "catalogue-validation.yml"],
  ["Link check", "link-check.yml"],
];

export function getSettings(env = {}) {
  return {
    clientId: env.MEMBERSPARK_CLIENT_ID || "",
    secret: env["MEMBERSPARK_" + "CLIENT_SECRET"] || "",
    // The issuer is the address MemberSpark's discovery
    // document names — the API host, never the site host.
    issuer: (env.MEMBERSPARK_ISSUER || "https://api.memberspark.ca").replace(/\/$/, ""),
    testAccountSubs: parseTestAccountSubs(env.TEST_ACCOUNT_SUBS),
    githubToken: env.OPS_GITHUB_TOKEN || "",
    // A fetch seam the ops suite uses to stand the kit
    // against the kit's own fake. Production env never
    // carries it; the kit's default road is the global fetch.
    fetch: typeof env.__OPS_FETCH === "function" ? env.__OPS_FETCH : null,
  };
}

export function doorConfigured(settings) {
  return Boolean(settings.clientId && settings.secret);
}

// The kit is built once and kept (its README's rule: a kit
// rebuilt on every request forgets every token it has seen,
// and its replay guard stands for nothing). The cache keys
// on the configuration, so a suite handing in a new fake
// gets a new kit.
let kitCache = { key: null, kit: null };
export function kitFor(settings, origin) {
  const key = [settings.clientId, settings.issuer, origin].join("|");
  if (kitCache.key !== key) {
    kitCache = {
      key,
      kit: createMemberSparkKit({
        clientId: settings.clientId,
        ["client" + "Secret"]: settings.secret,
        redirectUri: origin + ROUTES.callback,
        issuer: settings.issuer,
        ...(settings.fetch ? { fetch: settings.fetch } : {}),
      }),
    };
  }
  return kitCache.kit;
}

export async function sessionOf(settings, request) {
  if (!doorConfigured(settings)) return null;
  return sessionFromRequest(settings.secret, request);
}

// The standing a session carries, judged fresh on every
// request: "test" where the placement names the sub (it is
// checked first, so a test account never reads as an
// operator — TA-5), "ops" where the sign-in's stored
// decision admits it, and null where neither stands.
export function standingOf(settings, session) {
  if (!session) return null;
  if (settings.testAccountSubs.has(session.sub)) return "test";
  if (session.opsAdmitted) return "ops";
  return null;
}

function baseHeaders(settings, session, standing, contentType) {
  const headers = {
    "content-type": contentType,
    "cache-control": "no-store",
  };
  // TA-9: every answer a test account gets carries the
  // read-only mark beside the page's banner.
  if (standing === "test") headers["x-viewer"] = "read-only";
  return headers;
}

// The surface's one refusal face (EV-OPS-37): the site's
// ordinary 404 page, the same status and the same bytes
// Pages serves for any missing page, naming neither Ops nor
// a sign-in road.
export function notFoundResponse(settings, session, standing) {
  return new Response(NOT_FOUND_HTML, {
    status: 404,
    headers: baseHeaders(settings, session, standing, "text/html; charset=utf-8"),
  });
}

export function jsonResponse(settings, session, standing, status, body) {
  return new Response(JSON.stringify(body), {
    status,
    headers: baseHeaders(settings, session, standing, "application/json"),
  });
}

// TA-7's refusal: a test account's every change is refused
// before any handler, with the read-only mark on the answer.
export function readOnlyRefusal(settings, session) {
  return jsonResponse(settings, session, "test", 403, { error: "Read-only." });
}

// The test gate, applied by every Ops road but sign-out
// (sign-in and sign-out are the standard's exceptions): a
// test-standing session's write method is refused here,
// before the road's own handling.
export function testGate(settings, session, standing, request) {
  if (standing !== "test") return null;
  if (request.method === "GET" || request.method === "HEAD") return null;
  return readOnlyRefusal(settings, session);
}

export function escHtml(value) {
  return String(value == null ? "" : value)
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/"/g, "&quot;")
    .replace(/'/g, "&#39;");
}

// ---------- the standings the surface fronts ----------
//
// Reads only (EV-OPS-19): the surface is never a second
// writer beside the machinery. The build record is this
// tree's own generation record. The publishing and checks
// standings are read from the repo's own Actions records —
// the machinery's home — with a read-only token the Pages
// project carries (OPS_GITHUB_TOKEN); without it the panels
// say so in words and invent nothing. The GitHub read is
// cached in the isolate for a minute so a reading page does
// not spend the token's rate on refreshes.

let githubCache = { at: 0, value: null };

async function githubJson(settings, path) {
  const fetchImpl = settings.fetch || fetch;
  const res = await fetchImpl("https://api.github.com" + path, {
    headers: {
      authorization: "Bearer " + settings.githubToken,
      accept: "application/vnd.github+json",
      "user-agent": "actually-free-ops",
    },
  });
  if (!res.ok) throw new Error("github read answered " + res.status);
  return res.json();
}

function word(value) {
  const text = String(value || "");
  return text ? text.charAt(0).toUpperCase() + text.slice(1) : "—";
}

async function readPublishing(settings) {
  const runs = await githubJson(
    settings,
    `/repos/${GITHUB_REPO}/actions/workflows/${PUBLISH_WORKFLOW}/runs?per_page=1`
  );
  const run = (runs.workflow_runs || [])[0];
  if (!run) return { configured: true, at: null, result: "No runs stand", published: "—", commit: "—" };
  let published = "—";
  try {
    const jobs = await githubJson(
      settings,
      `/repos/${GITHUB_REPO}/actions/runs/${run.id}/jobs?per_page=100`
    );
    for (const job of jobs.jobs || []) {
      for (const step of job.steps || []) {
        if (step.name === "Publish to Cloudflare Pages") {
          published =
            step.conclusion === "success" ? "Published"
            : step.conclusion === "skipped" ? "Held by the switch"
            : step.conclusion === "failure" ? "Failed"
            : word(step.conclusion || step.status);
        }
      }
    }
  } catch {
    // The run read stands; the step's word stays unknown.
  }
  return {
    configured: true,
    at: run.updated_at || run.created_at || null,
    result: word(run.conclusion || run.status),
    published,
    commit: String(run.head_sha || "").slice(0, 7) || "—",
  };
}

async function readChecks(settings) {
  const rows = [];
  for (const [name, file] of CHECK_WORKFLOWS) {
    try {
      const runs = await githubJson(
        settings,
        `/repos/${GITHUB_REPO}/actions/workflows/${file}/runs?per_page=1`
      );
      const run = (runs.workflow_runs || [])[0];
      rows.push({
        name,
        at: run ? run.updated_at || run.created_at || null : null,
        result: run ? word(run.conclusion || run.status) : "No runs stand",
      });
    } catch {
      rows.push({ name, at: null, result: "Not read" });
    }
  }
  return { configured: true, rows };
}

export async function opsData(settings, session, standing) {
  const identity = {
    name: session.name,
    email: session.email,
    standing: standing === "test" ? "Test account (read-only)" : "Ops role",
  };
  let publishing;
  let checks;
  if (!settings.githubToken) {
    const note =
      "The GitHub read is not configured on this surface. The standing stands where it always has — in the repo's own Actions runs — and this page invents none of it.";
    publishing = { configured: false, note };
    checks = { configured: false, note };
  } else if (githubCache.value && Date.now() - githubCache.at < 60 * 1000) {
    ({ publishing, checks } = githubCache.value);
  } else {
    publishing = await readPublishing(settings).catch(() => ({
      configured: true, at: null, result: "Not read", published: "—", commit: "—",
    }));
    checks = await readChecks(settings);
    githubCache = { at: Date.now(), value: { publishing, checks } };
  }
  return {
    identity,
    build: BUILD_RECORD,
    publishing,
    checks,
    backup: {
      // docs/OPS.md's standing, in the surface's own words:
      // no store stands, the repo is the record, and
      // republishing from it is the restore.
      line:
        "No store stands to back up. The site's whole content is the committed tree of its repo, so the repo is the record and republishing from it is the restore.",
    },
  };
}
