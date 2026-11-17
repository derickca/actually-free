// The Ops surface's session (issue #32). The shape is the
// certifiablemedia shop's owner-door session, carried over:
// an HMAC-signed value under one cookie at Path=/ — the kit's
// shape, because the page the session exists for stands at
// /ops, outside the sign-in road's path, and a cookie kept
// under that path would never reach it (the shop's #165).
// The record carries the decision the sign-in made — the
// Ops boolean the kit's hasOps judged — never the raw ops
// claim, per the kit's rule: a product stores the decision,
// never the claims. The test standing is not stored at all:
// it is re-judged on every request from the TEST_ACCOUNT_SUBS
// placement, the way the centre re-places it.
//
// Lifetimes: ninety days for an Ops session (the session
// standard's length, 7776000 seconds, carried by both the
// record's exp and the cookie's Max-Age) and fifteen minutes
// for a test-standing session (TA-17), never extended. A
// shared-device sign-in (the token's shared_device word)
// gets no Max-Age: the session ends when the browser closes.

export const SESSION_COOKIE = "af-ops-session";
export const SESSION_TTL_SECONDS = 90 * 24 * 60 * 60;
export const TEST_SESSION_TTL_SECONDS = 15 * 60;

function b64urlEncodeBytes(bytes) {
  let bin = "";
  for (const byte of bytes) bin += String.fromCharCode(byte);
  return btoa(bin).replace(/\+/g, "-").replace(/\//g, "_").replace(/=+$/, "");
}

function b64urlEncodeText(text) {
  return b64urlEncodeBytes(new TextEncoder().encode(text));
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

async function hmacKey(secret) {
  return crypto.subtle.importKey(
    "raw",
    new TextEncoder().encode(secret),
    { name: "HMAC", hash: "SHA-256" },
    false,
    ["sign", "verify"]
  );
}

async function signValue(secret, payload) {
  const body = b64urlEncodeText(JSON.stringify(payload));
  const key = await hmacKey(secret);
  const sig = await crypto.subtle.sign("HMAC", key, new TextEncoder().encode(body));
  return body + "." + b64urlEncodeBytes(new Uint8Array(sig));
}

// A value is believed only when its signature checks and its
// own expiry stands in the future. Anything else reads as
// absent, in the open.
async function readSignedValue(secret, value) {
  if (!value || typeof value !== "string") return null;
  const dot = value.lastIndexOf(".");
  if (dot <= 0) return null;
  const body = value.slice(0, dot);
  let sig;
  try {
    sig = b64urlDecodeToBytes(value.slice(dot + 1));
  } catch {
    return null;
  }
  let ok;
  try {
    const key = await hmacKey(secret);
    ok = await crypto.subtle.verify("HMAC", key, sig, new TextEncoder().encode(body));
  } catch {
    return null;
  }
  if (!ok) return null;
  let payload;
  try {
    payload = JSON.parse(b64urlDecodeToText(body));
  } catch {
    return null;
  }
  if (!payload || typeof payload.exp !== "number" || payload.exp * 1000 <= Date.now()) {
    return null;
  }
  return payload;
}

// The cookie attributes are one shape — HttpOnly, Secure,
// SameSite=Lax at Path=/ — and a clear carries the same
// attributes its set carried, so the two never disagree. A
// null Max-Age omits the attribute: the browser keeps the
// cookie only until it closes (a shared-device session).
export function sessionCookieHeader(name, value, maxAgeSeconds) {
  return (
    name + "=" + value +
    "; Path=/; HttpOnly; Secure; SameSite=Lax" +
    (maxAgeSeconds === null || maxAgeSeconds === undefined
      ? ""
      : "; Max-Age=" + maxAgeSeconds)
  );
}

export function clearSessionCookieHeader() {
  return SESSION_COOKIE + "=; Path=/; HttpOnly; Secure; SameSite=Lax; Max-Age=0";
}

export function readCookies(request) {
  const header = request.headers.get("cookie") || "";
  const pairs = [];
  for (const part of header.split(";")) {
    const eq = part.indexOf("=");
    if (eq < 0) continue;
    pairs.push([part.slice(0, eq).trim(), part.slice(eq + 1).trim()]);
  }
  return pairs;
}

// The centre places the test accounts' subs as
// TEST_ACCOUNT_SUBS, this product's own placement — account
// subs only, never an address (TA-3). The placed shape is a
// JSON array of subs; a comma-separated list parses the same
// way, as the centre's own parser takes both. A value that
// parses as neither reads as no placement, so a malformed
// placement grants no standing rather than a wrong one. (The
// shop's parser, carried over.)
export function parseTestAccountSubs(value) {
  const raw = String(value || "").trim();
  if (!raw) return new Set();
  if (raw.startsWith("[")) {
    try {
      const parsed = JSON.parse(raw);
      if (Array.isArray(parsed)) {
        return new Set(
          parsed.map((part) => String(part || "").trim()).filter(Boolean)
        );
      }
    } catch {
      // Fall through to the comma-separated shape.
    }
  }
  return new Set(
    raw.split(",").map((part) => part.trim()).filter(Boolean)
  );
}

// Mint the session cookie for a completed sign-in. standing
// is "test" or "ops" as judged at the callback, and
// opsAdmitted is the decision the caller judged from the
// kit's identity (identity.hasOps for this product) — the
// session stores the decision, never the claim. Returns the
// Set-Cookie header value.
export async function mintSessionCookie(secret, identity, standing, opsAdmitted) {
  const ttl =
    standing === "test" ? TEST_SESSION_TTL_SECONDS : SESSION_TTL_SECONDS;
  const session = {
    sub: identity.sub ? String(identity.sub) : null,
    email: identity.email ? String(identity.email) : null,
    name: identity.name ? String(identity.name) : null,
    // The person's initials and their picked combo, as the
    // centre worked them out and the token carried them: the
    // Ops page renders the person's own mark from them, and
    // never works letters out from a name itself. Absent
    // where a token carries none.
    ...(typeof identity.initials === "string" && identity.initials
      ? { initials: identity.initials }
      : {}),
    ...(typeof identity.initials_combo === "string" && identity.initials_combo
      ? { initials_combo: identity.initials_combo }
      : {}),
    sid: identity.sid ? String(identity.sid) : null,
    // The decision, never the claim (the kit's rule).
    opsAdmitted: opsAdmitted === true,
    exp: Math.floor(Date.now() / 1000) + ttl,
  };
  const value = await signValue(secret, session);
  return sessionCookieHeader(
    SESSION_COOKIE,
    value,
    identity.shared_device ? null : ttl
  );
}

// Read the session a request carries. Every value presented
// under the cookie's name is tried until one verifies (the
// shop's #165 shape): a browser may present a stale value
// ahead of the standing one, and the first may be one the
// door no longer believes while the second stands.
export async function sessionFromRequest(secret, request) {
  if (!secret) return null;
  for (const [name, raw] of readCookies(request)) {
    if (name !== SESSION_COOKIE) continue;
    const session = await readSignedValue(secret, raw);
    if (!session || !session.sub) continue;
    return {
      sub: session.sub,
      email: typeof session.email === "string" ? session.email : null,
      name: typeof session.name === "string" ? session.name : null,
      initials: typeof session.initials === "string" ? session.initials : null,
      initialsCombo:
        typeof session.initials_combo === "string" ? session.initials_combo : null,
      sid: typeof session.sid === "string" ? session.sid : null,
      opsAdmitted: session.opsAdmitted === true,
    };
  }
  return null;
}
