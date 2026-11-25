// The operator door's assertion check (issue #55, on the
// fleet operator contract, MemberSpark docs/spec/
// operator-doors.md). The shape is the certifiable.media
// shop's (its functions/lib/operator-auth.js), carried over
// to this product's own settings and records.
//
// The door's credential (the OPERATOR_DOOR_SECRET placement)
// identifies the caller as MemberSpark Admin; the credential
// alone never opens the door. Every call also carries a
// short-lived assertion minted for that one call: an ES256
// JWT, typ "ms-operator-assertion", signed by the centre and
// verifiable at its published key set. The claims bind the
// call together: the issuer is the centre, the audience is
// this product's own id, jti is the call's lookup id, q is
// the question, subject is the body's subject, and the token
// lives sixty seconds from its iat. A call whose assertion
// is missing, expired, addressed to another product or
// naming a different question, subject or lookup than its
// body is refused — this module answers the verified claims,
// or null.
//
// Two shapes of assertion stand, and each is checked as it
// stands. An owner's call carries sub the owner's admin id
// and sid that session's id. A call the centre makes as
// itself carries sub "system" and sid present with the value
// null, and it is admitted only for the questions the
// contract names as its exception — here the five
// per-product questions and explain_finding. The sid claim
// is never absent on either shape: its absence is the
// machinery proof's own mark, and this door does not adopt
// the machinery proof, so a call carrying no sid claim is
// refused at this gate whatever else it names.
//
// The key set is held in the isolate for an hour and, where
// the platform offers its shared cache, in that cache for
// five minutes, so a burst of fresh isolates reads the
// origin once per shared-cache window instead of once per
// isolate; a kid the held set does not know forces one
// fresh read. The fetch rides a seam (env.__OPERATOR_FETCH)
// the suites use to stand a stub centre; production env
// never carries it.

// This product's own id at the centre: the audience every
// assertion for this door must name.
export const OPERATOR_PRODUCT_ID = "actually-free";
export const OPERATOR_ASSERTION_TYP = "ms-operator-assertion";
// The questions the centre may ask as itself (the
// contract's exception): the five per-product questions,
// and explain_finding beside them.
const SYSTEM_QUESTIONS = new Set([
  "errors",
  "audit",
  "backups",
  "test_standing",
  "adoption",
  "explain_finding",
]);
const JWKS_TTL_MS = 60 * 60 * 1000;
const JWKS_SHARED_TTL_SECONDS = 300;

export function operatorIssuer(env = {}) {
  return (env.MEMBERSPARK_ISSUER || "https://api.memberspark.ca").replace(
    /\/$/,
    ""
  );
}

function fetchImpl(env) {
  return typeof env.__OPERATOR_FETCH === "function"
    ? env.__OPERATOR_FETCH
    : fetch;
}

function b64urlDecodeToBytes(text) {
  const b64 = String(text).replace(/-/g, "+").replace(/_/g, "/");
  const bin = atob(b64 + "=".repeat((4 - (b64.length % 4)) % 4));
  const bytes = new Uint8Array(bin.length);
  for (let i = 0; i < bin.length; i++) bytes[i] = bin.charCodeAt(i);
  return bytes;
}

function b64urlDecodeToText(text) {
  return new TextDecoder().decode(b64urlDecodeToBytes(text));
}

let jwksCache = null;
let jwksCacheAt = 0;

// The platform's shared cache, where the runtime offers
// one (the Pages runtime does; the suites do not). Every
// use below is best-effort inside its try: a cache that
// cannot be read or stored to is no cache, and the origin
// road stands exactly as it did without one.
function sharedCache() {
  try {
    const caches = globalThis.caches;
    return caches && caches.default ? caches.default : null;
  } catch {
    return null;
  }
}

async function fetchKeySet(env, issuer) {
  const res = await fetchImpl(env)(issuer + "/.well-known/jwks.json");
  if (!res.ok) throw new Error("MemberSpark key set read failed: " + res.status);
  return res.json();
}

async function readKeySet(env, issuer, { bypassShared = false } = {}) {
  const url = issuer + "/.well-known/jwks.json";
  const cache = sharedCache();
  if (cache && !bypassShared) {
    try {
      const hit = await cache.match(new Request(url));
      if (hit) {
        const shared = await hit.json();
        if (shared && typeof shared === "object") {
          jwksCache = shared;
          jwksCacheAt = Date.now();
          return shared;
        }
      }
    } catch {
      // The origin read below stands.
    }
  }
  const fresh = await fetchKeySet(env, issuer);
  jwksCache = fresh;
  jwksCacheAt = Date.now();
  if (cache) {
    try {
      await cache.put(
        new Request(url),
        new Response(JSON.stringify(fresh), {
          headers: {
            "content-type": "application/json",
            "cache-control": "public, max-age=" + JWKS_SHARED_TTL_SECONDS,
          },
        })
      );
    } catch {
      // Best-effort: a set that cannot be stored is read
      // from the origin again next time.
    }
  }
  return fresh;
}

async function keySet(env, issuer, force = false) {
  if (!force && jwksCache && Date.now() - jwksCacheAt < JWKS_TTL_MS) {
    return jwksCache;
  }
  return readKeySet(env, issuer, { bypassShared: force });
}

// The signature check: find the key by the token's kid,
// reading the set once more when the kid is unknown.
// Assertions are ES256 only — the contract names the
// algorithm, and no other key kind is tried.
async function verifyAssertionSignature(env, issuer, token) {
  const parts = String(token || "").split(".");
  if (parts.length !== 3) throw new Error("the assertion is not a JWT");
  const header = JSON.parse(b64urlDecodeToText(parts[0]));
  if (header.alg !== "ES256") throw new Error("the assertion's signing algorithm is not ES256");
  if (header.typ !== OPERATOR_ASSERTION_TYP) {
    throw new Error("the token is not an operator assertion");
  }
  let set = await keySet(env, issuer);
  let jwk = (set.keys || []).find((k) => k.kid === header.kid);
  if (!jwk) {
    set = await keySet(env, issuer, true);
    jwk = (set.keys || []).find((k) => k.kid === header.kid);
  }
  if (!jwk || jwk.kty !== "EC") throw new Error("no signing key published for the token's kid");
  const key = await crypto.subtle.importKey(
    "jwk", jwk, { name: "ECDSA", namedCurve: "P-256" }, false, ["verify"]
  );
  const ok = await crypto.subtle.verify(
    { name: "ECDSA", hash: "SHA-256" },
    key,
    b64urlDecodeToBytes(parts[2]),
    new TextEncoder().encode(parts[0] + "." + parts[1])
  );
  if (!ok) throw new Error("the assertion's signature does not check");
  return JSON.parse(b64urlDecodeToText(parts[1]));
}

// Verify one call's assertion against the call it rides on:
// the body it must name is { lookup_id, question, subject }.
// Answers the verified claims for a call that checks, or
// null for one that does not.
export async function verifyOperatorAssertion(env, assertion, call) {
  const issuer = operatorIssuer(env);
  if (!assertion || typeof assertion !== "string") return null;
  if (!call || typeof call !== "object") return null;
  const lookupId = typeof call.lookup_id === "string" ? call.lookup_id : "";
  const question = typeof call.question === "string" ? call.question : "";
  if (!lookupId || !question) return null;
  const bodySubject = call.subject === undefined ? null : call.subject;
  if (bodySubject !== null && typeof bodySubject !== "string") return null;

  let claims;
  try {
    claims = await verifyAssertionSignature(env, issuer, assertion);
  } catch {
    return null;
  }
  if (!claims || typeof claims !== "object") return null;
  if (claims.iss !== issuer) return null;
  if (claims.aud !== OPERATOR_PRODUCT_ID) return null;
  if (typeof claims.sub !== "string" || !claims.sub) return null;
  // The session rule, with the centre-as-itself exception.
  // The sid claim stands present on both admitted shapes —
  // the owner's session id, or null for the centre itself —
  // and absent on no call this door admits: an absent sid
  // is the machinery proof's mark, and that proof is not
  // adopted here.
  if (!("sid" in claims)) return null;
  if (claims.sub === "system") {
    if (claims.sid !== null || !SYSTEM_QUESTIONS.has(question)) return null;
  } else if (typeof claims.sid !== "string" || !claims.sid) {
    return null;
  }
  if (claims.jti !== lookupId) return null;
  if (claims.q !== question) return null;
  if (claims.subject !== bodySubject) return null;
  // The assertion's own life: sixty seconds from its iat,
  // the contract's shape. An expired assertion, or one
  // claiming a longer life than the contract gives it, is
  // refused.
  if (typeof claims.exp !== "number" || typeof claims.iat !== "number") return null;
  if (claims.exp - claims.iat <= 0 || claims.exp - claims.iat > 61) return null;
  if (claims.exp * 1000 <= Date.now()) return null;
  return claims;
}
