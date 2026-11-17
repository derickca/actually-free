# The MemberSpark shared kit

One small library, so each product does not write its own sign-in
plumbing (Spec 4, "The shared kit"). Plain JavaScript, Web-standard
APIs only; it loads on Cloudflare Workers and on Node 20, with no
framework of its own.

## Copying and the pin

A product copies this whole folder into its own repo at a pinned
commit of derickca/MemberSpark (OQ-22: a plain folder copy; the
pinned commit is the version). Record the commit you copied at.
Fixes land here first; a product takes a fix by copying again at a
newer commit.

Where your service carries a verdict for a kit-carried shape
(Spec 7, "The pop-up door": a verdict names the kit commit it was
proven against), the pin record carries the verdict too: a
`conformance` block naming the standard, the verdict and
`held_at_kit_commit` — the kit commit the verdict was proven
against — with a test that fails while the verdict names an older
commit than the pin. FundingSpark's `worker/kit/PINNED.json` and
GrabASpot's `vendor/memberspark-kit/PINNED.json` are the standing
examples. Re-audit before the pin's commit moves; the verdict
holds only at the commit it names.

**Re-pin adoption — the callback's word outcomes (#368).** The
callback answers a decline or a failure with a word outcome —
`{ cancelled: true, redirect }` or `{ failed: true, redirect }`
— carrying no identity. A product whose callback wiring grew up
around an older kit may read that answer as an arrival and
refuse it for having no subject; TaskSparkle's handler did
exactly that at pin 21c8050, and the word never reached its
answer. When you take a pin, check your handler against the
rule in Wiring below: the word outcomes are served exactly as
returned, before any of your own arrival logic.

**Re-pin adoption — the callback with no flow standing
(#370).** A callback arrival with no valid flow standing (a
refreshed completed callback, a bookmarked one, an expired
flow) is answered with a redirect to the product's sign-in
start — never a bare error status. `route()` serves that
answer itself at this pin. A product calling `callback()`
directly, whose catch answers the kit's throws with an error
status of its own, must answer the marked no-flow refusals
(`err.noFlow`) with the redirect instead; a catch-all error
status is the shape this rules out.

**Re-pin adoption — the arrival that is not a sign-in return
(#418).** A callback arrival with no `iss`, or one that is not
MemberSpark's, is refused with the refusal marked
(`err.unknownIssuer`). At this pin the product's catch serves
a marked refusal the kit's not-a-return page
(`signInNotReturnPage`) instead of the problem page: the
arrival is not a sign-in return and nothing went wrong, so
the problem page's apology no longer stands in its place.
Every other refusal keeps the problem page.

**Re-pin adoption — the problem page says the true thing per
reason (#533).** The shared problem page takes the failure's
reason now: a catch that already derives a reason from the
kit's refusals (GrabASpot's `x-sign-in-reason`, #709) hands it
in as `signInProblemPage({ productName, homeUrl, reason })`,
and for `iss-mismatch`, `state-mismatch`, `token-invalid` and
`flow-missing` the page states what happened instead of the
apology — those answers never were valid returns, and nothing
went wrong on our side. A catch that hands in no reason, or a
reason the page does not know, gets the standing page
unchanged, word for word; a catch serving the problem page
without a reason is not broken at this pin, only still
apologising for the foreign answers.

**Re-pin adoption — the journey's shape, recorded (#248).**
At this pin the kit records the shape a journey took, so it
never again rests on traces. The authorize address carries
no shape mark — nothing in an address may claim the mode —
so the record is made where the product itself speaks:
`callback()` reads the flow's mode before any check that
can throw and hands it back on every outcome — `mode` on
the identity return and on the word outcomes, `err.mode`
on the refusals it throws (the issuer refusal included) —
so a product that records its callbacks can record the
mode it read even when the journey dies at the callback.
The same mode rides the callback's code exchange
(`ms_mode`) to MemberSpark, which logs it in its audit
trail when the exchange succeeds. Nothing a product must
do changes at this pin; the field is there to be recorded.

## Files

- `memberspark.js` — the kit itself: `createMemberSparkKit(config)`
  for the product's Worker, `createMemberSparkBrowserKit(config)`
  for its page, the settled `WORDS`, the `ROUTES` table with
  its `routeName` matcher, and the two shared pages a product's
  catch serves: `signInProblemPage` for a genuine failure and
  `signInNotReturnPage` for an issuer refusal (#418).
- `fake.js` — `fakeMemberSpark()`: a fake MemberSpark with its own
  signing key, for product test suites. A product's suite sign-in
  test runs against the fake, never against real MemberSpark.
  Configure the kit under test from the fake's discovery document
  (`/.well-known/openid-configuration`), the way a product is told
  to configure itself — never by handing it the fake's own issuer
  variable, which is the value the fake answers and mints with, so
  no issuer judgement in the suite could ever see a
  configured-vs-actual split (#262). The fake can stand both
  splits: `discoveryIssuer` names another address in the
  document's issuer field than the fake answers with, and
  `tokenIssuer` mints its ID tokens under another issuer than the
  answers carry.
- `test/kit.test.mjs` — the kit's own suite, run with
  `node --test kit/test/kit.test.mjs`.
- `test/flow-cookies-295-256.test.mjs` — the flow-cookie checks:
  each sign-in flow stands in its own cookie, named by its state
  (`__Host-ms_state_<state>`), living 900 seconds (15 minutes), so two tabs — or
  a pop-up start beside a full-page start — never overwrite each
  other. A flow cookie under the old bare name still completes.
- `test/popup-context-356.test.mjs` — the pop-up context checks:
  the kit opener takes the full-page road, opening no window,
  where a pop-up cannot work — a plain phone browser tab, an
  installed app's context, an in-app web view — and still pops up
  on a desktop browser.
- `test/popup-cancelled-356.test.mjs` — the decline word: the
  kit's callback page posts `memberspark:sign-in-cancelled` to the
  opener, and the kit answers it through the optional
  `onCancelled` callback. The word proves a decline; its absence
  proves nothing — a window the browser, the OS or a crash closes
  posts nothing, and the product's unknown-case handling stands.
  The word is refused from any origin but the kit's own —
  MemberSpark's own host included (#364).
- `test/callback-words-368.test.mjs` — the word-outcome
  pass-through: through `route()`, a pop-up decline, a pop-up
  failure and a full-page decline each answer exactly as
  `callback()` built them, with `onIdentity` never run — the
  hook is not handed the nothing a word carries — while a
  completion still runs the hook first.
- `test/callback-noflow-370.test.mjs` — the no-flow callback:
  a callback arrival with no valid flow standing (no flow
  cookie, a state no standing flow carries, a refreshed
  completed callback) is answered by `route()` with a 303
  redirect to the sign-in start, while `callback()` itself
  still refuses the arrival and genuine failures still throw
  through `route()` for the product's problem page.
- `test/issuer-refusal-418.test.mjs` — the issuer refusal: a
  callback arrival with no `iss`, or one that is not
  MemberSpark's, is refused before any flow is acted on, with the
  refusal marked (`err.unknownIssuer`), so the product's catch
  serves the kit's not-a-return page
  (`signInNotReturnPage`) — the arrival is not a sign-in return
  and nothing went wrong — while a failure with a flow standing
  keeps the standing refusal and the standing problem page,
  word for word.
- `test/shape-marker-248.test.mjs` — the journey-shape marker:
  each start marks its authorize address with its shape, and
  the callback hands the mode it read back on every outcome —
  a completion, a decline, a failure, and the refusals it
  throws, the issuer refusal first among them — while an
  arrival with no flow of its own carries no mode at all.
- `test/popup-reload-267.test.mjs` — the reloaded-page checks:
  a pop-up completion also leaves a script-readable marker at
  the product's origin, and the opener's `resume()` arms a
  standing hearing, so a completion landing after the product
  page reloaded or navigated away is still heard by the page
  now standing; a completion that landed while no page stood
  to hear it is recovered from the marker, once, and never
  twice.
- `test/jwks-refetch-303.test.mjs` — the rotated-key checks: a
  token whose kid the cached key set does not know makes the kit
  refetch the set once, then fail if the kid is still unknown.
  There is no fallback to the first cached key — after a rotation
  a new key's tokens verify as soon as the refetch lands, a token
  from a genuinely unknown key fails, and concurrent callbacks
  share the one refetch.
- `test/verdict-pin-363.test.mjs` — the centre's verdict check:
  a service's pin record carrying a verdict must name the kit
  commit the verdict was proven against, and that commit must be
  the record's pin. A review runs it against a service's record
  (named by the PINNED_RECORD environment variable) before
  repeating the service's verdict; the hash checks read this
  repo's history and skip where it does not stand.
- `test/deleted-probe-1145.test.mjs` — the deletion
  confirmation checks: the events road's account.deleted probe
  confirms only when the centre's status and the centre's word
  stand together — 410 carrying the flat JSON error
  account_deleted. A bare 410, a 410 carrying a web page's body
  or another word, and the word under any other status each
  confirm nothing: the event is left unacted and the refusal
  answered, because a transport layer's 410 is not the centre's
  verdict.

## What the product hands the kit

```js
import { createMemberSparkKit } from "./kit/memberspark.js";

const ms = createMemberSparkKit({
  clientId: "galleryspark",            // the product's registered client id
  clientSecret: env.<client-secret>, // the product's Worker secret
  redirectUri: "https://galleryspark.ca/auth/memberspark/callback",
  issuer: "https://api.memberspark.ca", // staging: https://staging.memberspark.workers.dev
  apiBase: "https://api.memberspark.ca/v1",
  // staging apiBase: "https://staging.memberspark.workers.dev/api/v1"
});
```

The `issuer` is the address MemberSpark's discovery document names —
in production that is the API host, `https://api.memberspark.ca`,
never the site host `https://memberspark.ca`. The kit checks the
authorize answer's `iss` and every ID token against this value before
anything else: a product configured with the site host refuses every
genuine production callback at that first check, while staging —
one host, the same address on both sides — passes every journey.
Set it from discovery (`<issuer>/.well-known/openid-configuration`),
not from the address people see in the door.

The kit is built once and kept. Its guard against a replayed
logout or event token is a list the kit instance holds in
memory — a `jti` seen in the last two minutes is refused —
so a product that builds the kit again on every request
forgets every token it has seen, and the guard stands for
nothing. The kit asks MemberSpark for the scope
`openid profile email orgs`; there is no scope setting. The
addresses the kit builds stand under the issuer:
`/oauth2/authorize`, `/oauth2/token` and `/oauth2/logout`,
and the key set at `/.well-known/jwks.json`. A product that
writes any part of this road itself — the shop's owner door
is the standing example — builds those addresses exactly
so.

The kit holds no secret of its own and sets no session lifetime;
both stay the product's. `apiBase` names the membership API's base
address; when it is omitted the kit uses `<issuer>/api/v1`, which is
the staging and fake shape. `popupStartPath` names the product's own
address its page opens in the popup and its Worker routes to
`ms.startPopupSignIn(request)`; it defaults to
`/auth/memberspark/popup`.

**Staging Workers: one compatibility flag is required.** On
staging, the product's Worker and MemberSpark staging both stand on
this account's `workers.dev` addresses, and Cloudflare does not
route a Worker's `fetch()` to another Worker on the same zone: the
kit's server-side calls — the code exchange at `/oauth2/token`, the
key set at `/.well-known/jwks.json`, the membership API — answer
404 (error code 1042) from inside the product's Worker while the
same addresses answer normally from outside. The product's staging
Worker therefore carries
`compatibility_flags = ["global_fetch_strictly_public"]` in its
staging configuration, which routes its `fetch()` as if from the
public internet; the kit's addresses do not change. Production
needs nothing: its issuer stands on a custom domain, where the
same-zone limit does not apply. A service binding to the staging
Worker, handed to the kit as its `fetch`, also works; the flag is
the smaller step. (Found by SocietySpark's staging proof,
MemberSpark#215, and proven there with a probe Worker in this
account.)

The product's page constructs the page-side half on its own, with
no secret:

```js
import { createMemberSparkBrowserKit } from "./kit/memberspark.js";

const page = createMemberSparkBrowserKit({
  clientId: "galleryspark",
  redirectUri: "https://galleryspark.ca/auth/memberspark/callback",
});
page.signIn({ returnTo, onDone });
```

## The operator door

A product also stands an operator door for MemberSpark Admin; the
contract is
[docs/spec/operator-doors.md](../docs/spec/operator-doors.md). Two
facts about that door belong here, because a product meets them
while it wires the kit's roads:

- The centre sends the door's credential as its plain value in an
  `Authorization: Bearer` header. A door keeps the credential in
  one of two shapes: store its SHA-256 hash, hash the value the
  header carries, and compare the hashes — or store the plain
  value and compare it directly, or use it as the key of an HMAC
  over the call. The centre's registry holds the hash alone, and
  the centre never sends the hash: a door waiting for the hash on
  the wire refuses every real call.
- A call the centre makes as itself — the groups questions, the
  group_news act and the four per-product questions — carries an
  assertion whose `sub` is `system` and whose `sid` claim stands
  present with the value null. The claim is never absent. A door
  checks that shape; a door that checks for a missing `sid`
  refuses every call the centre makes as itself.

## Wiring

The product's Worker routes its own addresses to the kit:

- **The addresses stand in the kit** (MemberSpark#193): `ROUTES`
  names them — sign-in `/auth/memberspark/sign-in`, popup start
  `/auth/memberspark/popup`, callback
  `/auth/memberspark/callback`, initiate-login
  `/auth/memberspark/initiate-login`, signed-out
  `/auth/memberspark/signed-out`, back-channel logout
  `/auth/memberspark/backchannel-logout`, events
  `/auth/memberspark/events`. One convention — hyphenated —
  covers every route; a product does not spell them for itself.
  The sign-in entry also answers at `/auth/memberspark/signin`,
  a standing alias for the spelling products already serve: the
  journey starts there exactly as at the canonical address — it
  never 404s and never redirects to the canonical spelling. New
  links and documents name the canonical one.
- A product can hand any request under those addresses to
  `ms.route(request, hooks)`: it dispatches to the handlers
  below and returns null for an address the kit does not own,
  so the product's router falls through. On the callback,
  `hooks.onIdentity(identity, idToken)` runs before the redirect
  answers, so the product makes its session first — and it runs
  only when the callback hands back an identity: a decline or a
  failure answers a word outcome (`{ cancelled }` / `{ failed }`,
  below) with no identity in it, and `route` serves that
  outcome's redirect untouched, never handing the hook the
  nothing a word carries (#368). A callback arrival with no
  valid flow standing is answered by `route` itself (#370):
  `callback()`'s refusal for that moment carries a no-flow mark
  (`err.noFlow`), and `route` answers it with a 303 redirect to
  the sign-in start, so the person begins again; every other
  refusal still throws out of `route`, for the product's own
  catch. The
  back-channel route takes `hooks.endSessions`, and the events
  route `hooks.eventHandlers`. A product keeping its own router
  matches paths with `routeName(path)` instead — it answers
  both sign-in spellings with the one route name. The
  signed-out address is the product's own page: `route`
  returns null there, and the product serves it.
- **No chooser page stands in front of MemberSpark sign-in.** The
  product's sign-in entry IS the start of the journey: a tap on
  "Sign in or join" opens the popup (or, where no popup can open,
  sends the whole page through `ms.signIn(request)`'s redirect) with
  no page of the product's own in between. A "choose how to sign in"
  page stands only while a product genuinely offers more than one
  way in, and then every choice on it starts its journey directly —
  never a page whose only job is to hold one button.
- Sign-in link or button → the popup journey, below. The whole-page
  road still stands, at the sign-in entry address, for callers
  that cannot run a page script: `ms.signIn(request)` answers with
  the redirect to MemberSpark; state, nonce and PKCE ride in a
  short-lived `__Host-` cookie.
- The popup start address (`popupStartPath`) →
  `ms.startPopupSignIn(request)` — the `signIn` answer, with the
  flow marked as a popup journey in that same cookie. Nothing in any
  address or script-readable place claims the marking.
- The product's own page script → the kit's page-side opener,
  never the product's own writing of the popup contract. A page
  never holds the client secret: the secret is the product's
  Worker secret, for the server-side half alone. Where the Worker
  serves the page script, the full kit's opener stands:
  `ms.forBrowserFromWindow(window).signIn({ returnTo, onDone })`,
  or `ms.forBrowser({ open, addMessageListener })` where the page's
  powers are handed in directly. Where the page script is a static
  asset with no Worker behind it, the page-safe factory stands:
  `createMemberSparkBrowserKit({ clientId, redirectUri })` — it
  asks for no secret and holds none — then
  `.signIn({ returnTo, onDone })`. Either way the opener opens the
  popup start address in a window over the page. When the journey
  completes, `onDone` fires with the return path and the page
  refreshes its signed-in state without a page change. Where the
  window does not open, the answer is `{ mode: "redirect", url }`.
  **A page script's fallback sends the person to the full-page
  sign-in start, never the pop-up start** (#402): the fallback's
  destination is the sign-in entry address (`ms.signIn`'s
  redirect), not the address in the answer — a journey that runs
  in the whole tab must not carry the pop-up marking, or its
  answer pages would try to close the tab they stand in.
- **Arm the standing hearing on every page that offers sign-in.**
  The completion word is posted to the opener *window*, but the
  listener lives in the page's *document*: if the person reloads
  the product page, or navigates it, while the pop-up stands
  open, the document that started the journey is gone, the word
  posts into a void, the pop-up closes, and the page goes on
  showing signed out while the session the callback made stands
  valid behind it (#267). So on load the page also calls
  `page.resume({ onDone, onFailed, onCancelled })` with the same
  handlers it hands `signIn`. `resume` arms the same origin-gated
  listener without opening a window, so a completion landing on
  the document now standing is heard. A completion that already
  landed while no document stood to hear it leaves a
  script-readable marker cookie at the product's origin
  (`__Host-ms_completed`: the return path and the moment, no
  identity, five minutes); `resume` reads it on arming, clears
  it, and fires `onDone` once — the session behind the marker
  genuinely stands, so the recovery is honest, never a faked
  completion. A listener that hears the word itself clears the
  marker, so one completion is never recovered twice. One live
  listener stands per page across both calls: a `signIn` attempt
  retires a standing hearing and settles into the same slot, and
  the page calls `resume` again when it wants the hearing back.
  Silence is never read as an outcome: a pop-up the person
  closed posts nothing, and neither call settles anything for
  it (#265).
- The callback address → `const { identity, redirect } =
  await ms.callback(request)`; the product then makes its own
  session for `identity.sub` and answers with `redirect`.
  The answer the product sends carries its own session
  cookie first. The kit's `redirect` already carries the
  flow cookie's clear; the product composes the answer it
  sends — its session cookie ahead of the kit's `Set-Cookie`
  lines, not appended behind them — because a client that
  keeps only a redirect's first `Set-Cookie` (the Android
  WebView is the known one) keeps the first and drops the
  rest, and a session dropped there leaves the person signed
  out on a journey every log calls complete. The session
  cookie stands at `Path=/`, the host root, never the
  sign-in road's path — the product's pages stand outside
  that path, and a cookie kept under it never reaches them —
  with `HttpOnly`, `Secure`, `SameSite=Lax` and a `Max-Age`
  of the session's length. **Serve
  the word outcomes first, untouched (#368).** A decline or a
  failure comes back as a word outcome instead of an identity:
  `{ cancelled: true, redirect }` or `{ failed: true, redirect }`.
  The handler checks for `cancelled` / `failed` before any of
  its own arrival logic — session minting, subject presence,
  membership — and answers with that outcome's `redirect`
  exactly as the kit returned it. An outcome with no identity
  is a word to pass on, not an arrival to refuse: nothing is
  minted for it, and no refusal page stands in its place. (A
  full-page failure that is not a decline still throws, and the
  handler's catch renders the problem page — see "When sign-in
  fails".) **A callback arrival with no valid flow standing is
  its own moment (#370).** A refreshed completed callback, a
  bookmarked one, or a flow the browser has dropped as expired
  arrives with no journey standing: `callback()` refuses it —
  no session is made — with an error carrying the no-flow mark
  (`err.noFlow`): "no sign-in flow stands on this browser", or
  "state does not match" where a flow stands but none is this
  answer's. The handler answers a marked refusal with a
  redirect (303) to the product's sign-in start, so the person
  begins again — never a bare error status for it, and never
  the problem page either: nothing failed; the journey simply
  is not there. (Products serving `route()` inherit this
  answer; this paragraph is for handlers calling `callback()`
  directly.) **An arrival that is not a sign-in return at all is
  a third moment (#418).** A callback opened with no `iss`, or
  one that is not MemberSpark's — a bare or mistyped callback
  address, a probe — is refused before any flow is read, with
  the refusal marked (`err.unknownIssuer`). **What the refusal
  refuses, and when:** `callback()` refuses every arrival whose
  `iss` is absent or is not the configured issuer — on every
  journey shape, whether the arrival carries a code or an
  error — and it refuses before the flow cookie is read, so an
  error answer without `iss` never reaches the part of the
  handler that could act on it. MemberSpark's own answers
  carry `iss` on codes and errors alike (#902); a return
  without it is not MemberSpark's answer, whatever else it
  carries. The handler's catch
  serves a marked refusal the kit's not-a-return page,
  `signInNotReturnPage({ productName, homeUrl })`: it says the
  arrival is not a sign-in return and that nothing has gone
  wrong, with the one ruled action (the product's name alone,
  to its home). Never the problem page for this arrival — its
  apology ("Something went wrong on our side") is false here.
  Every other refusal keeps the problem page, exactly as
  ruled. The identity carries `sub`, `sid`, `name`, `email`,
  `initials`, `initials_combo`, `auth_time`, `ms_method`,
  `shared_device` and — where an Ops grant stands for the
  person — `ops` (#914): the word `all` while an
  every-app grant stands, otherwise the list of product ids
  the grant covers. A product admits to its Ops door by
  asking the identity, never by comparing the field itself:
  `identity.hasOps(productId)` (#946) answers from the same
  verified claims — true for the word `all` and for a list
  covering the named id, false for every other shape, an
  absent field included — so no product writes the
  comparison, whose two natural forms each fail: a membership
  check on the field reads false under `all` and throws where
  the field is absent, and a bare truthiness check admits a
  grant covering another product alone. The helper stands on
  the identity as the product receives it — the callback's
  return, and the identity `route()` hands `onIdentity`. The
  same judgement stands exported on its own as
  `opsCovers(ops, productId)` (#965), a pure helper judging
  any verified claims' `ops` value — above all a UserInfo
  answer, which the centre shapes identically — so the
  re-check road judges with the kit's code too, and no
  product writes the comparison on either road. It
  is a function, so it does not survive a JSON round-trip: a
  product that stores the identity and reads it back holds
  the field alone, and a stored standing is re-judged at the
  next sign-in, never by a resurrected helper. So a product
  stores the decision, never the claims — for use within
  the interval: at sign-in it calls
  `hasOps(own product)` once and persists the boolean, and
  it never persists the raw `ops` field for a later
  comparison — the serialisation boundary carries an answer
  rather than evidence. A stored decision goes stale the
  moment a grant is revoked, so the boolean serves only
  until the next re-check, and at each re-check the product
  reads the standing fresh and re-judges it: a helper
  stands for both roads — `hasOps` at sign-in, and
  `opsCovers` on the re-check's answer. A product
  reads the standing from this field, never by decoding the
  ID token itself: the field is
  taken from the token whose signature and claims the kit has
  just checked, so an unverified payload can produce no
  field. The kit does not read UserInfo. MemberSpark carries
  the same claim there, resolved fresh at each read, so a
  revocation shows there at the holder's next check — but
  that answer is the product's own server-to-server read to
  make, and `opsCovers(answer.ops, own product)` is the
  judgement it makes on it — the kit's code, not its own
  comparison — and the kit's field never comes from it; the field
  states the standing as it stood at this sign-in's mint.
  Store the `sid` beside the session: sign-out needs it. On a
  popup journey, `redirect` is the
  completion page: it posts `memberspark:sign-in-complete` to its
  opener, closes its window, and carries the return path and
  nothing else — no identity rides in it. The close is guarded
  (#402): the page closes only the window the kit opened as its
  pop-up (the opener-given window name, and an opener standing at
  the product's own origin); in any other window — a tab a page
  script sent to the pop-up start — it takes the person on to the
  return path standing in that window instead. The same answer also
  sets the completion marker cookie (#267), the script-readable
  trace a reloaded product page recovers from; a full-page
  journey sets none, and neither does a decline or a failure.
  The identity's `initials` and `initials_combo` are the
  person's account mark, worked out by the centre from the
  name and the person's pick: a product renders the mark
  from these fields and never works letters out from the
  name itself. The identity's `email` is an address the
  person has proven — MemberSpark holds no other kind, and
  the ID token carries `email_verified` standing true — so
  a product matches and links on it as a proven address, as
  Spec 4's step 5 describes.
- The initiate-login address → `ms.initiateLogin(request)`.
- Sign out → end the product's own session, then send the browser
  to `ms.signOutUrl(sid, postLogoutUri)`. No ID token travels in
  the address; the hint is the `sid`.
- The back-channel logout address →
  `ms.backchannelLogout(request, ({ sub, sid }) => endSessions(...))`.
  The token arrives form-encoded (`logout_token=<the token>`, as
  MemberSpark sends it); the kit unwraps it, and a body that is the
  bare token still reads. The events address reads its token the
  same way (`event_token=<the token>`, or the bare token).
- The events address → `ms.events(request, handlers)`, one handler
  per event kind (`account.updated`, `account.deleted`,
  `membership.changed`, `organization.disconnected`,
  `grant.revoked`, `ai_key.revoked`, `ai_key.renamed`,
  `keys.rotated`). A deletion is confirmed against the API (the
  account must answer 410) before the handler runs.
- Membership reads and acts → `ms.members.account(sub)`,
  `.organizations(sub)`, `.member(org, sub)`, `.members(org)`,
  `.organization(org)`, `.setPaidUpUntil(org, sub, date)`,
  `.createOrganization(name, termsVersion, actingIdToken)`,
  `.invite(org, emails, actingIdToken)`,
  `.joinRequest(org, actingIdToken)`, `.deletedAccounts(since)`.
  Answers are cached at most 5 minutes against the change feed; a
  stale answer never serves an admin act. A failed read throws an
  error carrying the status, the centre's parsed error body
  (`err.body`) and its top-level error word (`err.code`) — key on
  the word, never on the bare status: a suspension answers 403
  with the code `account_suspended` (Spec 2, the account roads'
  answer table).
- An AI-key route → `const who = await ms.aiKey(request, { access:
  "read" })`; an unmarked route counts as a write. The answer is
  `{ sub, keyId, keyName, access }` or a Response: 401 (bad key),
  503 with Retry-After (MemberSpark could not be checked), 429 with
  Retry-After (too many unknown keys from one source).
- The agent directions address → `ms.directions(lines, buildStamp)`. The shape carries the three answers, the check floor, the kit's own limits (the unknown-key rate and the check memories) and the owner's no-public-access ruling in his words. The product's own lines carry every limit its own code can refuse a call with, in numbers — the standing rule (Spec 2, "Directions state every limit", R7), pinned by a test in the product.

## The return path is validated by the kit

The kit validates `returnTo` itself, where the value enters —
`ms.signIn(request, { returnTo })`, `ms.startPopupSignIn(request)`
(which reads it from the popup start address's query string when
the product passes none), the page-side opener's `returnTo`, and
again where `ms.callback(request)` reads the flow cookie back.
Only a same-origin path stands: one leading `/`, never `//`, no
scheme, no backslash, no whitespace or control characters, no
`<`. Anything else becomes `"/"`.

That validation is in the kit on purpose (MemberSpark#212). The
return path is later interpolated into the popup completion
page's script and, on the blocked-popup fallback, used as the
whole redirect — so an unvalidated value was a script break-out
on the product's own origin and an open redirect off it. A
product is safe by default when it pins this kit; it does not
need a guard of its own to be safe.

An adopter's own entry guard is still welcome — FundingSpark's,
which also narrows the fallback to its own account page, is the
standing example — but it earns its keep as product policy (where
a signed-in person lands by default), never as the kit's safety
net. If a product writes one, it validates the value it hands the
kit the same way and never widens what the kit accepts.

The page-side opener holds one live listener at a time across
`signIn` and `resume`: a new call of either retires the previous
listener, and a settled attempt removes its own, so an abandoned
attempt leaves nothing live beyond the page's standing hearing
and `onDone` cannot fire twice.

## The popup journey, and why there is no embed

Sign-in runs in a popup window the product opens (Spec 4, "The
popup journey"; the owner's ruling stands in DECISIONS.md,
2026-11-10). The product's page stays on screen behind the window;
the sign-in itself is a real MemberSpark page in its own window,
where passkeys, Google and cookies all work the way they work on
any page.

Embedding the door inside the product's page instead is refused,
and a product must not build it. A passkey is tied to
memberspark.ca, and browsers — Safari above all — refuse it inside
another site's frame. Google never lets its sign-in page stand in
a frame, so that button would have to break out anyway. The email
link leaves any frame by nature: it opens in the person's mail app
and lands on MemberSpark's own page, so the journey would start
embedded and jump out mid-way. And a framed sign-in runs on
third-party cookies, which Safari blocks by default, so the
hand-off back to the product can fail without a word.

## When sign-in fails (#327)

The error pattern is ruled (DECISIONS.md, 2026-11-11) and the kit
carries the product's half of it:

- A person declining — the callback arriving with
  `error=access_denied` — is not a failure. `callback()` answers
  `{ cancelled: true, redirect }`. On a pop-up journey the redirect
  is a small page at the product's own origin that posts
  `POPUP_CANCELLED_TYPE` ("memberspark:sign-in-cancelled") to the
  opener and closes — under the same window guard as the
  completion page (#402): in a window that is not the kit's
  pop-up it takes the person back to the page the flow began on
  instead; the browser kit's `signIn` accepts
  `onCancelled` — a product hearing it stays silent. The word
  proves a decline; its absence proves nothing. A full-page
  journey returns to the page the flow began on. Never render a
  problem page for a decline.
- A pop-up journey that fails at the centre tells its opener the
  same way: the centre sends the pop-up window to the callback
  with an error answer, and `callback()` answers
  `{ failed: true, redirect }` — a page at the product's own
  origin that posts `POPUP_FAILED_TYPE`
  ("memberspark:sign-in-failed") and closes, under the same
  window guard (#402). The browser kit's
  `signIn` accepts `onFailed` — show `WORDS.signInFailed` as one
  line on the page; the page itself never moved. (The words are
  only ever posted from the product's own origin — the opener's
  listener hears no other — which is why the centre routes the
  window here instead of posting from its own host, #364.)
- Any other callback failure on a full-page journey throws, and
  the product's catch renders the problem page: its own, or the
  kit's shared one, `signInProblemPage({ productName, homeUrl })`
  — the promise ("We're looking into the problem for you."),
  exactly one action carrying the product's name alone, landing
  on a page that stands signed out and stays. No "Try again".
  A catch that holds the failure's reason — derived from the
  kit's own refusal messages, the way GrabASpot's
  `x-sign-in-reason` header carries it (#709) — hands it in as
  `signInProblemPage({ productName, homeUrl, reason })`, and
  the words follow the reason (#533): for `iss-mismatch`,
  `state-mismatch` and `token-invalid` the answer never was a
  valid return, so the page states that, with no apology and no
  promise (nothing went wrong on our side); for `flow-missing`
  it states plainly that no journey stands. A code exchange the
  door refused or could not answer (`exchange-<status>`), an
  unknown reason, and no reason at all keep the standing
  apology, word for word — those faults are genuinely the
  centre's or the product's.
- A callback arrival with no valid flow standing is not a
  failure (#370): a refreshed completed callback, a bookmarked
  one, an expired flow. The person is returned to the product's
  sign-in start by redirect and begins again — never a bare
  error status, and no problem page: nothing failed, the
  journey is simply not there. `callback()` refuses the
  arrival with a marked error (`err.noFlow`); `route()` serves
  the redirect itself (see Wiring).
- A callback arrival that is not a sign-in return at all is
  its own moment (#418): no `iss`, or an `iss` that is not
  MemberSpark's — a bare or mistyped callback address, a probe.
  `callback()` refuses it before any flow is read, with the
  refusal marked (`err.unknownIssuer`), and the product's catch
  serves the kit's not-a-return page,
  `signInNotReturnPage({ productName, homeUrl })` — it says the
  arrival is not a sign-in return and that nothing has gone
  wrong, with the one ruled action. The problem page never
  stands for this arrival: nothing went wrong on our side, and
  its apology sends the reader looking for a fault that does
  not exist.
- A silent check answers in words, and one of them is not
  an answer. The kit's `startSilentCheck` begins the check
  with `prompt=none`; the callback's answer posts its word
  to the page that framed the check: the complete word, or
  `memberspark:sign-in-required` where no session stands, or
  the failed word. Where the browser withheld storage
  access — the return carries `ms_storage_access=withheld` —
  the word is `memberspark:sign-in-unknown`: the check could
  not tell, and a product reads it as no answer, never as
  signed out.
- A blocked pop-up announces itself before the page leaves:
  `signIn` accepts `onBlocked`, called with `WORDS.popupBlocked`
  when the window does not open and the answer is the full-page
  redirect.
- A pop-up the person closes by hand posts no word at all — no
  page stands in the window to post one (#265). The browser kit
  watches its own pop-up while an attempt stands (a closed-state
  poll): a window gone with no word heard settles the attempt —
  listener removed, watch stopped — and `signIn` accepts
  `onAbandoned` for exactly that ending, so the page can say the
  attempt is over and offer its ordinary road onward. An
  abandonment is not a decline and not a failure: never answer
  it with the failure line, and never read it back as the
  cancelled word's fact. A word heard first (complete,
  cancelled, failed) stops the watch, so a settled journey is
  never also abandoned. Callers who hand the opener its powers
  themselves may hand a timer in the same shape
  (`every`/`stopEvery`); `forBrowserFromWindow` binds the page's
  own timers, and the ambient timers are the default otherwise.

## The words

`WORDS` carries the settled text: "Sign in or join", "Your
MemberSpark account", "Sign out", and the first-visit line. Use them
as they stand.
