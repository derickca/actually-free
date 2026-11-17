// The fake MemberSpark (Spec 4): a stand-in with its own signing key,
// for product test suites. A product's suite sign-in test runs
// against the fake, never against real MemberSpark. The fake answers
// discovery, key set, token, membership, logout and events in the
// service's shapes, so a product can prove its wiring offline.
//
// Everything lives in memory and goes away with the process. The fake
// is seeded with invented people and organizations only.

const B32 = "ABCDEFGHIJKLMNOPQRSTUVWXYZ234567";
function b64urlEncode(bytes) {
  let s = "";
  for (const b of bytes) s += String.fromCharCode(b);
  return btoa(s).replace(/\+/g, "-").replace(/\//g, "_").replace(/=+$/, "");
}
function b64urlDecode(text) {
  const s = String(text).replace(/-/g, "+").replace(/_/g, "/");
  const padded = s + "=".repeat((4 - (s.length % 4)) % 4);
  const bin = atob(padded);
  const out = new Uint8Array(bin.length);
  for (let i = 0; i < bin.length; i++) out[i] = bin.charCodeAt(i);
  return out;
}
function base32Of(bytes) {
  let out = "";
  let buffer = 0, bits = 0;
  for (const byte of bytes) {
    buffer = (buffer << 8) | byte;
    bits += 8;
    while (bits >= 5) { bits -= 5; out += B32[(buffer >> bits) & 31]; }
  }
  if (bits > 0) out += B32[(buffer << (5 - bits)) & 31];
  return out;
}
function randomText(bytes, alphabet) {
  const rand = crypto.getRandomValues(new Uint8Array(bytes));
  if (alphabet) return [...rand].map((b) => alphabet[b % alphabet.length]).join("");
  return b64urlEncode(rand);
}
async function sha256(bytesOrText) {
  const data = typeof bytesOrText === "string" ? new TextEncoder().encode(bytesOrText) : bytesOrText;
  return new Uint8Array(await crypto.subtle.digest("SHA-256", data));
}

export async function fakeMemberSpark(options = {}) {
  const issuer = (options.issuer || "https://fake.memberspark.test").replace(/\/$/, "");
  // Two divergence shapes for the issuer checks (#262), each
  // defaulting to the fake's own issuer so a fake that does not
  // ask for a split stands in the service's honest shape: a
  // discovery document whose issuer field names another address
  // than the fake answers with (discoveryIssuer), and ID tokens
  // minted under another issuer than the answers carry
  // (tokenIssuer). A suite configured from the document, the way
  // a product is told to configure itself, can see both splits;
  // a suite handed the fake's own variable never could.
  const discoveryIssuer = (options.discoveryIssuer || issuer).replace(/\/$/, "");
  const tokenIssuer = (options.tokenIssuer || issuer).replace(/\/$/, "");
  const keyPair = await crypto.subtle.generateKey(
    { name: "ECDSA", namedCurve: "P-256" }, true, ["sign", "verify"]);
  const publicJwk = await crypto.subtle.exportKey("jwk", keyPair.publicKey);
  publicJwk.kid = "fake-key-1";
  publicJwk.alg = "ES256";
  publicJwk.use = "sig";

  const clients = new Map(); // client_id -> { secret, redirectUri }
  const codes = new Map(); // code -> flow
  const accounts = new Map(); // sub -> { sub, name, email, deleted, suspended }
  const orgs = new Map(); // id -> { id, name }
  const memberships = new Map(); // orgId -> Map(sub -> membership row)
  const aiKeys = new Map(); // full key -> { sub, key_id, key_name, access, valid, covers }
  const sentTo = []; // every token the fake was asked to send, for assertions

  function seedClient({ clientId, clientSecret, redirectUri }) {
    clients.set(clientId, { secret: clientSecret, redirectUri });
  }
  // The centre's initials rule (Initials Standard, Part 2;
  // #436), the fake's copy of the service's src/initials.js:
  // the first letter of the first token and of the last, in
  // capitals; one letter for a single token; trailing suffixes
  // (Jr., Sr., II, III, IV) dropped first; an accented letter
  // keeps its accent. The pick reads as Aurora until one is
  // seeded or written.
  const SUFFIXES = new Set(["jr", "sr", "ii", "iii", "iv"]);
  function deriveInitials(name) {
    const tokens = String(name == null ? "" : name).trim().split(/\s+/).filter(Boolean);
    while (tokens.length > 1) {
      const last = tokens[tokens.length - 1].toLowerCase().replace(/\.+$/, "");
      if (!SUFFIXES.has(last)) break;
      tokens.pop();
    }
    if (!tokens.length) return "";
    const first = (token) => {
      for (const ch of token) if (/\p{L}/u.test(ch)) return ch.toUpperCase();
      return "";
    };
    return tokens.length === 1 ? first(tokens[0]) : first(tokens[0]) + first(tokens[tokens.length - 1]);
  }
  const comboOf = (account) => account.combo || "Aurora";
  // The silent road's standing answer for authorize asks
  // with prompt=none: null (the default) answers a code, as
  // the fake always has; { signedIn: false, storageAccess }
  // answers the no-session return above, and
  // { standing: true } answers the session-standing return
  // (a stale proof's straight redirect, with no
  // storage-access mark).
  let silentSeed = null;
  function seedSilent(answer) { silentSeed = answer || null; }
  function seedAccount({ sub, name, email, initialsCombo, suspended, ops }) {
    accounts.set(sub, { sub, name, email, deleted: false, suspended: Boolean(suspended), combo: initialsCombo || null, ops: ops || null });
  }
  function seedOrganization({ id, name, members }) {
    orgs.set(id, { id, name });
    const rows = new Map();
    for (const m of members || []) {
      rows.set(m.sub, {
        sub: m.sub, role: m.role || "member", status: m.status || "active",
        paid_up_until: m.paid_up_until || null,
      });
    }
    memberships.set(id, rows);
  }
  // covers names the products standing in the key's list — its
  // scopes, in the real road's words. It defaults to the home
  // product alone: the shape every key stood in before #334 made
  // keys multi-app, and the shape a key that reaches no other
  // product still stands in. levels names the same list with a
  // level per product (#1101): the check then answers each
  // caller at the level the key holds there, as the real road
  // answers from the key's scope entries. A key minted with
  // levels stands in for its home product at its home level
  // wherever a single access is asked for.
  async function mintAiKey({ clientId, sub, access, covers, levels }) {
    const keyId = randomText(16, B32);
    const secret = randomText(32, B32);
    const check = base32Of(await sha256(`msk_${clientId}_${keyId}_${secret}`)).slice(0, 6);
    const key = `msk_${clientId}_${keyId}_${secret}_${check}`;
    aiKeys.set(key, {
      sub, key_id: keyId, key_name: "Fake key", valid: true,
      access: levels ? levels[clientId] : access,
      covers: levels ? Object.keys(levels) : (covers || [clientId]),
      levels: levels || null,
    });
    return key;
  }

  async function signJwt(claims, typ) {
    const header = { alg: "ES256", typ, kid: "fake-key-1" };
    const enc = (obj) => b64urlEncode(new TextEncoder().encode(JSON.stringify(obj)));
    const input = enc(header) + "." + enc(claims);
    const sig = await crypto.subtle.sign(
      { name: "ECDSA", hash: "SHA-256" }, keyPair.privateKey, new TextEncoder().encode(input));
    return input + "." + b64urlEncode(new Uint8Array(sig));
  }
  const nowSec = () => Math.floor(Date.now() / 1000);

  // sendLogout / sendEvent hand the product's wired endpoint a signed
  // token the way the real service does. sendLogout sends the service's
  // shape (#292): a form body, logout_token=<the token>, as OpenID
  // Connect Back-Channel Logout sets out — the shape the service's own
  // sendBackchannel POSTs. sendEvent sends the built sender's shape
  // too (form-encoded event_token, #229); the kit still reads a
  // bare-token body at both addresses, for senders that predate
  // the form shape.
  async function sendLogout(url, { clientId, sub, sid }) {
    const token = await signJwt({
      iss: issuer, aud: clientId, iat: nowSec(), exp: nowSec() + 120,
      jti: randomText(16), sub, sid,
      events: { "http://schemas.openid.net/event/backchannel-logout": {} },
    }, "logout+jwt");
    sentTo.push({ kind: "logout", url, token });
    return globalThis.fetch(url, {
      method: "POST",
      headers: { "content-type": "application/x-www-form-urlencoded" },
      body: "logout_token=" + encodeURIComponent(token),
    });
  }
  async function sendEvent(url, { clientId, kind, sub, organization_id, subs, key_id }) {
    const token = await signJwt({
      iss: issuer, aud: clientId, iat: nowSec(), exp: nowSec() + 120,
      jti: randomText(16), sub, organization_id, subs, key_id,
      events: { [kind]: {} },
    }, "event+jwt");
    sentTo.push({ kind, url, token });
    return globalThis.fetch(url, {
      method: "POST",
      headers: { "content-type": "application/x-www-form-urlencoded" },
      body: "event_token=" + encodeURIComponent(token),
    });
  }

  function json(body, status = 200) {
    return new Response(JSON.stringify(body), { status, headers: { "content-type": "application/json" } });
  }
  function clientFromBasic(request) {
    const header = request.headers.get("authorization") || "";
    if (!header.startsWith("Basic ")) return null;
    const [id, secret] = atob(header.slice(6)).split(":");
    const client = clients.get(id);
    return client && client.secret === secret ? id : null;
  }

  async function handle(request) {
    const url = new URL(request.url);
    const path = url.pathname;

    if (path === "/.well-known/openid-configuration") {
      return json({
        issuer: discoveryIssuer,
        authorization_endpoint: issuer + "/oauth2/authorize",
        token_endpoint: issuer + "/oauth2/token",
        jwks_uri: issuer + "/.well-known/jwks.json",
        end_session_endpoint: issuer + "/oauth2/logout",
        code_challenge_methods_supported: ["S256"],
      });
    }
    if (path === "/.well-known/jwks.json") return json({ keys: [publicJwk] });

    if (path === "/oauth2/authorize") {
      const client = clients.get(url.searchParams.get("client_id"));
      if (!client || url.searchParams.get("redirect_uri") !== client.redirectUri) {
        return new Response("unknown client or redirect", { status: 400 });
      }
      // The silent road's negative answers, when a test has
      // seeded one (seedSilent): the parameters the centre's
      // answers put at the callback. The no-session answer
      // carries error, its description, state, iss, and
      // (#897) the storage-access mark the centre's in-frame
      // document reports — the centre serves a document
      // whose two exits land at the callback with exactly
      // these parameters. The session-standing answer (a
      // stale proof) is the centre's own straight redirect:
      // error, its description, state and iss, and no mark,
      // because a session the gate could read is proof the
      // cookie was carried. The service test pins the
      // centre's emissions (silent-access-897.mjs), and this
      // fake mirrors them, so a kit test consumes the
      // emitted shapes end to end rather than a hand-built
      // return (the standing rule from MemberSpark #902).
      if (url.searchParams.get("prompt") === "none" && silentSeed && silentSeed.standing === true) {
        const back = new URL(client.redirectUri);
        back.search = new URLSearchParams({
          error: "login_required",
          error_description: "MemberSpark needs a fresh sign-in before this product can be told.",
          state: url.searchParams.get("state") || "",
          iss: issuer,
        }).toString();
        return new Response(null, { status: 302, headers: { location: back.toString() } });
      }
      if (url.searchParams.get("prompt") === "none" && silentSeed && silentSeed.signedIn === false) {
        const back = new URL(client.redirectUri);
        back.search = new URLSearchParams({
          error: "login_required",
          error_description: "No MemberSpark session stands for this browser.",
          state: url.searchParams.get("state") || "",
          iss: issuer,
          ms_storage_access: silentSeed.storageAccess === "withheld" ? "withheld" : "granted",
        }).toString();
        return new Response(null, { status: 302, headers: { location: back.toString() } });
      }
      const sub = url.searchParams.get("fake_sub") || "fake-person-1";
      if (!accounts.has(sub)) seedAccount({ sub, name: "Fake Person", email: "fake@example.test" });
      const code = randomText(24);
      codes.set(code, {
        sub,
        nonce: url.searchParams.get("nonce"),
        challenge: url.searchParams.get("code_challenge"),
        clientId: url.searchParams.get("client_id"),
        redirectUri: client.redirectUri,
      });
      const back = new URL(client.redirectUri);
      back.search = new URLSearchParams({
        code, state: url.searchParams.get("state") || "", iss: issuer,
      }).toString();
      return new Response(null, { status: 302, headers: { location: back.toString() } });
    }

    if (path === "/oauth2/token" && request.method === "POST") {
      const body = new URLSearchParams(await request.text());
      const flow = codes.get(body.get("code"));
      if (!flow) return json({ error: "invalid_grant" }, 400);
      codes.delete(body.get("code"));
      const verifierHash = b64urlEncode(await sha256(body.get("code_verifier") || ""));
      if (verifierHash !== flow.challenge) return json({ error: "invalid_grant" }, 400);
      const account = accounts.get(flow.sub);
      const claims = {
        iss: tokenIssuer, aud: flow.clientId, sub: flow.sub, sid: "fake-session-1",
        email: account.email, email_verified: true, name: account.name,
        initials: deriveInitials(account.name), initials_combo: comboOf(account),
        nonce: flow.nonce, auth_time: nowSec(), ms_method: "passkey",
        shared_device: false, iat: nowSec(), exp: nowSec() + 300,
      };
      // The Ops standing (#812), minted as the service mints
      // it: the word "all" or the list of named product ids,
      // and no claim at all where no grant stands. The seed
      // carries the grant (seedAccount's ops); nothing is
      // invented here.
      if (account.ops) claims.ops = account.ops;
      const idToken = await signJwt(claims, "JWT");
      return json({ id_token: idToken, token_type: "Bearer", expires_in: 300 });
    }

    if (path === "/oauth2/logout") return new Response("signed out (fake)", { status: 200 });

    if (path.startsWith("/api/v1/")) {
      if (!clientFromBasic(request)) return json({ error: "unauthorized" }, 401);
      const rest = path.slice("/api/v1".length);
      let m;
      if ((m = /^\/accounts\/([^/]+)$/.exec(rest))) {
        const account = accounts.get(decodeURIComponent(m[1]));
        if (!account) return json({ error: "account_not_found" }, 404);
        if (account.deleted) return json({ error: "account_deleted" }, 410);
        if (account.suspended) return json({ error: "account_suspended" }, 403);
        return json({ sub: account.sub, name: account.name, email: account.email, initials: deriveInitials(account.name), initials_combo: comboOf(account) });
      }
      if ((m = /^\/accounts\/([^/]+)\/initials$/.exec(rest)) && request.method === "POST") {
        // #436: a property's picker write — the pick lands on
        // the account, and the answer carries the mark, the way
        // the real centre answers. The acting token is checked
        // the way the centre checks it: the fake's own
        // signature, its issuer, the calling product as
        // audience, and the person named in it is the person
        // whose pick this is.
        const sub = decodeURIComponent(m[1]);
        const account = accounts.get(sub);
        if (!account) return json({ error: "account_not_found" }, 404);
        if (account.deleted) return json({ error: "account_deleted" }, 410);
        if (account.suspended) return json({ error: "account_suspended" }, 403);
        const body = await request.json().catch(() => ({}));
        const COMBOS = ["Meadow Split", "Sunset Rays", "Mint Waves", "Berry Waves", "Dusk Drift", "Halftone Pop", "Peach Halftone", "Contour", "Lagoon Rings", "Mint Glow", "Ember Glow", "Aurora"];
        if (!COMBOS.includes(body.combo)) return json({ error: "unknown combo" }, 400);
        const parts = String(body.acting_id_token || "").split(".");
        let claims = null;
        if (parts.length === 3) {
          try {
            const okSig = await crypto.subtle.verify(
              { name: "ECDSA", hash: "SHA-256" }, keyPair.publicKey, b64urlDecode(parts[2]),
              new TextEncoder().encode(parts[0] + "." + parts[1]));
            if (okSig) claims = JSON.parse(new TextDecoder().decode(b64urlDecode(parts[1])));
          } catch { claims = null; }
        }
        if (!claims || claims.iss !== tokenIssuer || claims.aud !== clientFromBasic(request) ||
            claims.sub !== sub || claims.exp <= nowSec() ||
            typeof claims.auth_time !== "number" || nowSec() - claims.auth_time > 900) {
          return json({ error: "acting token does not name this account" }, 403);
        }
        account.combo = body.combo;
        return json({ sub, initials: deriveInitials(account.name), initials_combo: account.combo });
      }
      if ((m = /^\/accounts\/([^/]+)\/organizations$/.exec(rest))) {
        const sub = decodeURIComponent(m[1]);
        const mine = [];
        for (const [orgId, rows] of memberships) {
          if (rows.has(sub)) mine.push({ id: orgId, name: orgs.get(orgId).name, role: rows.get(sub).role, status: rows.get(sub).status });
        }
        return json(mine);
      }
      if ((m = /^\/accounts\/([^/]+)\/ai-keys$/.exec(rest))) {
        const sub = decodeURIComponent(m[1]);
        const mine = [...aiKeys.entries()].filter(([, k]) => k.sub === sub)
          .map(([key, k]) => ({ key, key_id: k.key_id, key_name: k.key_name, access: k.access }));
        return json(mine);
      }
      if ((m = /^\/organizations\/([^/]+)$/.exec(rest))) {
        const org = orgs.get(decodeURIComponent(m[1]));
        return org ? json(org) : json({ error: "not found" }, 404);
      }
      if ((m = /^\/organizations\/([^/]+)\/members$/.exec(rest))) {
        const rows = memberships.get(decodeURIComponent(m[1]));
        return json(rows ? [...rows.values()] : []);
      }
      if ((m = /^\/organizations\/([^/]+)\/members\/([^/]+)$/.exec(rest))) {
        const row = memberships.get(decodeURIComponent(m[1]))?.get(decodeURIComponent(m[2]));
        return row ? json(row) : json({ error: "not found" }, 404);
      }
      if ((m = /^\/organizations\/([^/]+)\/members\/([^/]+)\/paid-up-until$/.exec(rest)) && request.method === "PUT") {
        const row = memberships.get(decodeURIComponent(m[1]))?.get(decodeURIComponent(m[2]));
        if (!row) return json({ error: "not found" }, 404);
        row.paid_up_until = (await request.json()).paid_up_until;
        return json(row);
      }
      if (rest === "/organizations" && request.method === "POST") {
        const body = await request.json();
        const id = "org-" + randomText(6).toLowerCase();
        seedOrganization({ id, name: body.name, members: [] });
        return json({ id, name: body.name }, 201);
      }
      if ((m = /^\/organizations\/([^/]+)\/invitations$/.exec(rest)) && request.method === "POST") {
        return new Response(null, { status: 202 });
      }
      if ((m = /^\/organizations\/([^/]+)\/join-requests$/.exec(rest)) && request.method === "POST") {
        return new Response(null, { status: 202 });
      }
      if (rest === "/changes") return json({ changes: [], cursor: String(Date.now()) });
      if (rest === "/deleted-accounts") {
        return json({ accounts: [...accounts.values()].filter((a) => a.deleted).map((a) => a.sub) });
      }
      if (rest === "/ai-keys/check" && request.method === "POST") {
        const { key } = await request.json();
        const found = aiKeys.get(key);
        if (!found || !found.valid) return json({ valid: false });
        // The centre answers for the calling product, named by
        // its Basic credential: the key serves the caller only
        // when the caller's product stands in the key's list —
        // the fake's covers, the real road's scope list judged
        // with the caller's standing grant (#334, #1094).
        const caller = clientFromBasic(request);
        if (!found.covers.includes(caller)) return json({ valid: false });
        // A key with a level per product answers the caller at
        // its own level there (#1101); a one-level key answers
        // its level at every product it covers.
        const access = found.levels ? found.levels[caller] : found.access;
        return json({ valid: true, sub: found.sub, key_id: found.key_id, key_name: found.key_name, access });
      }
      return json({ error: "not found" }, 404);
    }

    return new Response("not found (fake)", { status: 404 });
  }

  return { issuer, fetch: handle, seedClient, seedAccount, seedOrganization, seedSilent, mintAiKey, sendLogout, sendEvent, sentTo, accounts, orgs, memberships, aiKeys };
}
