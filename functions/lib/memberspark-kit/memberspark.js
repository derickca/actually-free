// MemberSpark shared kit (Spec 4, "The shared kit"; MemberSpark#113).
//
// One small library, so each product does not write its own sign-in
// plumbing. Plain JavaScript using only Web-standard APIs, so it
// loads on Cloudflare Workers and on Node 20 alike, with no framework
// of its own. Products copy this folder at a pinned commit (OQ-22);
// the pinned commit is the version — see README.md in this folder.
//
// The kit holds no client secret of its own choosing and sets no
// session lifetime. Each product hands it its client id, client
// secret and MemberSpark address from its own Worker secrets and
// settings; session lifetime stays the product's own business.

// One flow cookie per sign-in flow, named by the flow's own state
// (#295/#256): two tabs — or a pop-up start beside a full-page
// start — each keep their own cookie, so no start overwrites
// another journey's flow, and each start writes only its own
// cookie (no read-modify-write for a second start to race). The
// bare name is the shape kits before this change wrote; callback
// still reads it as a fallback, so a journey started just before
// a product re-pins completes instead of stranding. The state in
// the name is no secret — it already travels in the authorize
// address; the nonce and PKCE verifier stay in the value.
const STATE_COOKIE = "__Host-ms_state";
const flowCookieName = (state) => STATE_COOKIE + "_" + state;
// The completion page's word to its opener (Spec 4, "The popup journey").
export const POPUP_COMPLETE_TYPE = "memberspark:sign-in-complete";
// The completion word's sibling (#327; mechanism corrected
// #359/#364): a pop-up journey that fails on the centre's side
// tells its opener with this word, posted by the kit's own
// callback page at the product's origin — the door's error page
// sends the pop-up window there with an error answer, because a
// word posted from MemberSpark's host could never pass the
// opener's own-origin listener — so the product page behind can
// show its one-line note: the journey's failure is never silent.
export const POPUP_FAILED_TYPE = "memberspark:sign-in-failed";
// The failed word's other sibling (#356, bridge Entries 112/147;
// mechanism corrected #359/#364): a person who declines in the
// pop-up is TOLD to the opener with this word. The word is posted
// by the kit's own callback page at the product's origin — the
// door sends the pop-up window there with an access_denied answer,
// the way completion reaches the same page with a code — because
// the opener's listener hears only its own origin, and a word
// posted from MemberSpark's host could never be heard. The word
// proves a decline — a product hearing it can stay silent. Its
// absence proves nothing: a window the browser, the OS or a crash
// closes never reaches any page that posts, so a product must
// never read silence as a decline.
export const POPUP_CANCELLED_TYPE = "memberspark:sign-in-cancelled";
// The silent road's signed-out word (#887): an arrival check
// (a prompt=none authorize, ridden in a hidden frame) that
// MemberSpark answers login_required — no session stands —
// tells its parent page with this word, posted by the kit's
// own callback page at the product's origin, the way every
// word in this family travels. It is the expected answer for
// a signed-out visitor, not a failure: the page stands as it
// was and sign-in is offered in place. A code answer posts
// the completion word instead; any other refusal posts the
// failed word, which the checker hears as no answer.
export const SILENT_REQUIRED_TYPE = "memberspark:sign-in-required";
// The silent road's could-not-ask word (#897): the centre's
// no-session answer reaches the callback marked
// ms_storage_access=withheld — the browser told the centre's
// own document, served in the frame at the centre's origin,
// that it granted no storage access there, so the session
// cookie may never have been carried and the negative proves
// nothing about the person. callback() posts this word
// instead of the required word, and the page-side checker
// hears it the way it hears a failure: onNoAnswer, the page
// standing exactly as it was. A negative the centre could
// ask about (the mark granted, or no mark at all — the
// session-standing answers and every centre before this one)
// keeps the required word: signed out is a verdict only
// where the question could be carried.
export const SILENT_UNKNOWN_TYPE = "memberspark:sign-in-unknown";
// There is deliberately no abandoned word beside these three
// (#265): a person who closes the pop-up by hand reaches no page
// that could post one — the window is simply gone. The opener
// learns that ending by watching its own pop-up's closed state
// (the watch in popupOpener, below) and answers it with a
// callback of its own, onAbandoned — a local fact, distinct from
// the decline the cancelled word proves and from a failure. It
// must never be folded into either: silence was never a decline
// (Entry 147), and a window the browser, the OS or a crash
// closes is not a word the centre sent.
const POPUP_WATCH_MS = 500; // the opener's closed-state poll while a pop-up attempt stands
// The name the opener gives the pop-up window (#402): one of the
// two marks the pop-up journey's answer pages judge their window
// by before closing it (outcomePageScript, below). A window a
// page script sent to the pop-up start — a tab another page
// opened, an ordinary tab that began there — does not carry it.
const POPUP_WINDOW_NAME = "memberspark-sign-in";
// The completion marker (#267): when a pop-up journey completes,
// callback() also leaves this cookie at the product's origin —
// script-readable on purpose (no HttpOnly), naming only the
// return path and the moment, the same contents as the completion
// page's own payload and no identity. It is the trace a reloaded
// product page recovers from: the completion word is posted to
// the opener window, but the listener that hears it lives in a
// document, and a reload or navigation replaces the document
// while the pop-up stands open — the word posts into a void and
// the pop-up closes, leaving a page that shows signed out while
// the session the callback made stands valid behind it. The
// page-side opener's resume() reads the marker on arming and
// answers onDone once; a listener that hears the word itself
// clears the marker, so one completion is never recovered twice.
// Five minutes is the gap it covers — a reload, a navigation
// away and back — not a second session store; the session cookie
// the product made is the standing truth, and after the marker
// is gone the next ordinary page load renders against it.
export const COMPLETED_COOKIE = "__Host-ms_completed";
const COMPLETED_TTL_SECONDS = 300;
const FLOW_TTL_SECONDS = 900; // the emailed sign-in link lives 15 minutes; the flow cookie lives at least as long (#295)
const JWKS_TTL_MS = 60 * 60 * 1000; // the key set, cached at most 1 hour
const MEMBER_TTL_MS = 5 * 60 * 1000; // membership answers, cached at most 5 minutes
const FEED_TTL_MS = 5 * 60 * 1000; // the change feed is re-read before a kept answer is used past this

// The product's own addresses (MemberSpark#193). The kit names
// them, so no product spells them for itself: one convention —
// hyphenated, the way the kit's own memberspark:sign-in-complete
// spells it — covers every route. The callback, signed-out,
// back-channel and events addresses stand here as the product
// registers them with MemberSpark.
export const ROUTES = {
  signIn: "/auth/memberspark/sign-in",
  popup: "/auth/memberspark/popup",
  silent: "/auth/memberspark/silent",
  callback: "/auth/memberspark/callback",
  initiateLogin: "/auth/memberspark/initiate-login",
  signedOut: "/auth/memberspark/signed-out",
  backchannelLogout: "/auth/memberspark/backchannel-logout",
  events: "/auth/memberspark/events",
};

// Standing aliases: spellings products already serve and links
// already name. An alias answers exactly as the canonical address
// does — the journey starts there; it never 404s and never
// redirects to the canonical spelling. Only the sign-in entry has
// one: it is the one address anything outside the product names.
const ROUTE_ALIASES = { "/auth/memberspark/signin": "signIn" };

// The route a product-side path belongs to, or null when the kit
// does not own it. A query string, when one rides along, is cut.
export function routeName(path) {
  const pathname = String(path || "").split(/[?#]/)[0];
  for (const [name, p] of Object.entries(ROUTES)) if (p === pathname) return name;
  return ROUTE_ALIASES[pathname] || null;
}

// The settled words (Site Standards Part 11, A1), the same in every product.
export const WORDS = {
  signInOrJoin: "Sign in or join",
  yourAccount: "Your MemberSpark account",
  signOut: "Sign out",
  firstVisit:
    "MemberSpark is the one account for the services we make. Sign in once, and your MemberSpark ID works at each of them.",
  // The one line a product page shows when a pop-up journey fails
  // (#327): what happened, and that it is being looked into.
  signInFailed: "Sign-in didn't finish. We're looking into it.",
  // Said on the product page before a blocked pop-up sends the
  // whole page to the sign-in page instead (#327).
  popupBlocked:
    "Your browser blocked the sign-in window, so we'll take you to the sign-in page instead, and bring you back here.",
};

// The shared problem page (#327), for a product that does not
// supply its own: the ruled pattern as one small page at the
// product's own origin — the promise, and exactly one action, the
// product's name alone, landing on the product's home, a page that
// stands signed out and stays. No "Try again": retrying a fault on
// the centre's side loops the person into it; the page they land
// on carries its ordinary sign-in button when they want it.
//
// The words follow the reason, when the product's catch hands
// one in (#533): the apology above is true only where the fault
// is genuinely the centre's or the product's — a code exchange
// the door refused or could not answer (exchange-<status>), and
// every other failure the kit cannot prove foreign. A catch
// derives the reason from the kit's own refusal messages
// (GrabASpot's x-sign-in-reason, #709, is the standing shape),
// and for the reasons that prove the answer never was a valid
// return the apology tells a false story — nothing went wrong
// on our side, and nobody is looking into a problem that is not
// there — so those reasons carry their own true statement
// instead, in the shape #418 set for the not-a-return page. No
// reason, or a reason the page does not know, keeps the standing
// apology, word for word.
const PROBLEM_PAGE_WORDS = {
  "iss-mismatch":
    "The answer that came back did not come from MemberSpark, so it could not sign you in. Nothing has gone wrong on our side.",
  "state-mismatch":
    "The answer that came back does not belong to a sign-in journey standing on this browser, so it could not sign you in. Nothing has gone wrong on our side.",
  "token-invalid":
    "The answer that came back could not be checked as MemberSpark's, so it could not sign you in. Nothing has gone wrong on our side.",
  "flow-missing":
    "No sign-in journey stands on this browser, so this answer could not sign you in. A journey stands only a short while. Head to the product and sign in from there.",
};
export function signInProblemPage({ productName, homeUrl, reason }) {
  const escAttr = (v) => String(v).replace(/&/g, "&amp;").replace(/"/g, "&quot;");
  const escText = (v) => String(v).replace(/&/g, "&amp;").replace(/</g, "&lt;");
  const words = PROBLEM_PAGE_WORDS[reason] ||
    "Something went wrong on our side, not yours. We're looking into the problem for you.";
  return "<!doctype html><title>We couldn't sign you in</title>" +
    "<h1>We couldn't sign you in</h1>" +
    "<p>" + words + "</p>" +
    '<p><a href="' + escAttr(homeUrl) + '">' + escText(productName) + "</a></p>";
}

// The not-a-return page (#418), for an issuer refusal: the
// callback address was opened with no iss, or one that is not
// MemberSpark's — a bare or mistyped callback address, a probe.
// That arrival is not a sign-in return at all, and nothing went
// wrong on our side, so the problem page's apology tells the
// wrong story. This page says what the arrival is, in plain
// words, and carries the ruled pattern's one action — the
// product's name alone, landing on the product's home — so the
// person has a way onward to a real sign-in.
export function signInNotReturnPage({ productName, homeUrl }) {
  const escAttr = (v) => String(v).replace(/&/g, "&amp;").replace(/"/g, "&quot;");
  const escText = (v) => String(v).replace(/&/g, "&amp;").replace(/</g, "&lt;");
  return "<!doctype html><title>This is not a sign-in return</title>" +
    "<h1>This is not a sign-in return</h1>" +
    "<p>This address is the end of a sign-in: MemberSpark sends you back here after you sign in. Opened on its own it cannot sign you in, and nothing has gone wrong. Head to the product and sign in from there.</p>" +
    '<p><a href="' + escAttr(homeUrl) + '">' + escText(productName) + "</a></p>";
}

// The Ops standing's shape (#812), read off a bare claims
// value: the word "all" while an every-app grant stands,
// otherwise the list of named product ids. Any other shape is
// no standing — the centre mints only these two — so a bare
// product id as a string, the word in another case, a number,
// or a list with a non-string in it all read as no standing,
// even where the raw value names a product.
function opsStandingValue(ops) {
  if (ops === "all") return "all";
  if (Array.isArray(ops) && ops.every((id) => typeof id === "string")) return ops;
  return undefined;
}

// The one judgement on that standing (#965), exported so a
// product judges any verified claims' ops value with it —
// above all a UserInfo answer, which the kit does not read:
// the centre carries the same claim there, in the same shape
// (service/src/auth.js resolves both roads through the one
// opsForSession), and a product re-checking standing on its
// own read — GrabASpot's staff door, every fifteen minutes —
// asks opsCovers(answer.ops, own product) instead of writing
// the comparison itself. True only for the word "all" or a
// list covering the named id; every other shape, an absent
// field included, is false. identity.hasOps (#946) answers
// through this same function, so the sign-in road and the
// re-check road can never part.
export function opsCovers(ops, productId) {
  const standing = opsStandingValue(ops);
  return standing === "all" ||
    (Array.isArray(standing) && standing.includes(productId));
}

// The initials (#436; the Initials Standard,
// docs/standards/initials.html at the centre): the twelve
// combos, the one drawing of a person's mark, and the one
// picker — the same pieces the centre itself renders (the
// service's src/initials.js; the two copies are one design).
// A product renders the letters and the combo the centre hands
// it — in the sign-in identity beside name and email, and on
// members.account — and never works letters out from a name
// itself: the derivation is the centre's alone (Part 2). The
// picker a product offers in its account screen is this one;
// its form posts the chosen combo's name in the `combo` field
// to the address it is handed, and the product writes the pick
// through members.setInitialsCombo, which answers with the
// person's mark so the new pick renders at once (Part 5).
export const INITIALS_COMBOS = ["Meadow Split", "Sunset Rays", "Mint Waves", "Berry Waves", "Dusk Drift", "Halftone Pop", "Peach Halftone", "Contour", "Lagoon Rings", "Mint Glow", "Ember Glow", "Aurora"];
export const DEFAULT_INITIALS_COMBO = "Aurora";
const INITIALS_META = [
  { name: "Meadow Split", font: "ink", shadow: "grey" },
  { name: "Sunset Rays", font: "paper", shadow: "dark" },
  { name: "Mint Waves", font: "paper", shadow: "dark" },
  { name: "Berry Waves", font: "paper", shadow: "dark" },
  { name: "Dusk Drift", font: "paper", shadow: "dark" },
  { name: "Halftone Pop", font: "paper", shadow: "dark" },
  { name: "Peach Halftone", font: "ink", shadow: "grey" },
  { name: "Contour", font: "ink", shadow: "grey" },
  { name: "Lagoon Rings", font: "ink", shadow: "grey-wide" },
  { name: "Mint Glow", font: "ink", shadow: "grey" },
  { name: "Ember Glow", font: "ink", shadow: "grey" },
  { name: "Aurora", font: "paper", shadow: "dark" }
];
const INITIALS_BY_NAME = new Map(INITIALS_META.map((c) => [c.name, c]));
const INITIALS_DEFS = `<defs>
<radialGradient id="i-pink"><stop offset="0%" stop-color="#eb208c" stop-opacity=".95"/><stop offset="100%" stop-color="#eb208c" stop-opacity="0"/></radialGradient>
<radialGradient id="i-mint"><stop offset="0%" stop-color="#00eeb9" stop-opacity=".9"/><stop offset="100%" stop-color="#00eeb9" stop-opacity="0"/></radialGradient>
<radialGradient id="i-orange"><stop offset="0%" stop-color="#fa8c2e" stop-opacity=".9"/><stop offset="100%" stop-color="#fa8c2e" stop-opacity="0"/></radialGradient>
<linearGradient id="i-dusk" x1="0" y1="0" x2="1" y2="1"><stop offset="0%" stop-color="#372f8f"/><stop offset="52%" stop-color="#eb208c"/><stop offset="100%" stop-color="#fa8c2e"/></linearGradient>
<radialGradient id="i-mintglow" cx="50%" cy="46%" r="78%"><stop offset="0%" stop-color="#eafff7"/><stop offset="38%" stop-color="#7df0cd"/><stop offset="72%" stop-color="#12c2a4"/><stop offset="100%" stop-color="#07594f"/></radialGradient>
<radialGradient id="i-emberglow" cx="50%" cy="46%" r="78%"><stop offset="0%" stop-color="#fffaf0"/><stop offset="38%" stop-color="#ffd9a3"/><stop offset="72%" stop-color="#fa8c2e"/><stop offset="100%" stop-color="#c23a17"/></radialGradient>
<filter id="i-shd" x="-80%" y="-80%" width="260%" height="260%"><feDropShadow dx="0" dy="3.2" stdDeviation="2.9" flood-color="#1d1a2e" flood-opacity="0.92"/></filter>
<filter id="i-shg" x="-80%" y="-80%" width="260%" height="260%"><feDropShadow dx="0" dy="2" stdDeviation="3.6" flood-color="#9a9aa6" flood-opacity="0.34"/></filter>
<filter id="i-shgs" x="-90%" y="-90%" width="280%" height="280%"><feDropShadow dx="0" dy="2.5" stdDeviation="4.6" flood-color="#8f8f9c" flood-opacity="0.42"/></filter>
</defs>`;
const INITIALS_BODIES = {
  "Meadow Split": `<rect width="100" height="100" fill="#7ff3d3"/><path d="M0,60 C30,52 70,40 100,30 L100,100 L0,100 Z" fill="#d1da99"/>`,
  "Sunset Rays": `<rect width="100" height="100" fill="#fff8ee"/><polygon points="0,100 0.0,-110.0 32.9,-107.4" fill="#f9552c"/><polygon points="0,100 32.9,-107.4 64.9,-99.7" fill="#fa8c2e"/><polygon points="0,100 64.9,-99.7 95.3,-87.1" fill="#f9552c"/><polygon points="0,100 95.3,-87.1 123.4,-69.9" fill="#fa8c2e"/><polygon points="0,100 123.4,-69.9 148.5,-48.5" fill="#f9552c"/><polygon points="0,100 148.5,-48.5 169.9,-23.4" fill="#fa8c2e"/><polygon points="0,100 169.9,-23.4 187.1,4.7" fill="#f9552c"/><polygon points="0,100 187.1,4.7 199.7,35.1" fill="#fa8c2e"/><polygon points="0,100 199.7,35.1 207.4,67.1" fill="#f9552c"/><polygon points="0,100 207.4,67.1 210.0,100.0" fill="#fa8c2e"/>`,
  "Mint Waves": `<rect width="100" height="100" fill="#00eeb9"/><path d="M0,46 C20,38 35,54 55,47 C75,40 88,50 100,45 L100,100 L0,100 Z" fill="#07b9a7"/><path d="M0,54 C22,47 38,61 58,54 C78,48 88,57 100,52 L100,100 L0,100 Z" fill="#372f8f"/>`,
  "Berry Waves": `<rect width="100" height="100" fill="#eb208c"/><path d="M0,50 C25,42 40,60 60,52 C80,45 90,54 100,50 L100,100 L0,100 Z" fill="#372f8f"/><path d="M0,76 C25,69 40,83 60,76 C80,70 90,79 100,75 L100,100 L0,100 Z" fill="#f9552c"/>`,
  "Dusk Drift": `<rect width="100" height="100" fill="url(#i-dusk)"/>`,
  "Halftone Pop": `<rect width="100" height="100" fill="#372f8f"/><circle cx="5" cy="5" r="0.9" fill="#00eeb9"/><circle cx="16" cy="5" r="1.1" fill="#00eeb9"/><circle cx="27" cy="5" r="1.2" fill="#00eeb9"/><circle cx="38" cy="5" r="1.4" fill="#00eeb9"/><circle cx="49" cy="5" r="1.6" fill="#00eeb9"/><circle cx="60" cy="5" r="1.8" fill="#00eeb9"/><circle cx="71" cy="5" r="2.0" fill="#00eeb9"/><circle cx="82" cy="5" r="2.2" fill="#00eeb9"/><circle cx="93" cy="5" r="2.4" fill="#00eeb9"/><circle cx="5" cy="16" r="1.1" fill="#00eeb9"/><circle cx="16" cy="16" r="1.2" fill="#00eeb9"/><circle cx="27" cy="16" r="1.4" fill="#00eeb9"/><circle cx="38" cy="16" r="1.6" fill="#00eeb9"/><circle cx="49" cy="16" r="1.8" fill="#00eeb9"/><circle cx="60" cy="16" r="2.0" fill="#00eeb9"/><circle cx="71" cy="16" r="2.2" fill="#00eeb9"/><circle cx="82" cy="16" r="2.4" fill="#00eeb9"/><circle cx="93" cy="16" r="2.6" fill="#00eeb9"/><circle cx="5" cy="27" r="1.2" fill="#00eeb9"/><circle cx="16" cy="27" r="1.4" fill="#00eeb9"/><circle cx="27" cy="27" r="1.6" fill="#00eeb9"/><circle cx="38" cy="27" r="1.8" fill="#00eeb9"/><circle cx="49" cy="27" r="2.0" fill="#00eeb9"/><circle cx="60" cy="27" r="2.2" fill="#00eeb9"/><circle cx="71" cy="27" r="2.4" fill="#00eeb9"/><circle cx="82" cy="27" r="2.6" fill="#00eeb9"/><circle cx="93" cy="27" r="2.7" fill="#00eeb9"/><circle cx="5" cy="38" r="1.4" fill="#00eeb9"/><circle cx="16" cy="38" r="1.6" fill="#00eeb9"/><circle cx="27" cy="38" r="1.8" fill="#00eeb9"/><circle cx="38" cy="38" r="2.0" fill="#00eeb9"/><circle cx="49" cy="38" r="2.2" fill="#00eeb9"/><circle cx="60" cy="38" r="2.4" fill="#00eeb9"/><circle cx="71" cy="38" r="2.6" fill="#00eeb9"/><circle cx="82" cy="38" r="2.7" fill="#00eeb9"/><circle cx="93" cy="38" r="2.9" fill="#00eeb9"/><circle cx="5" cy="49" r="1.6" fill="#00eeb9"/><circle cx="16" cy="49" r="1.8" fill="#00eeb9"/><circle cx="27" cy="49" r="2.0" fill="#00eeb9"/><circle cx="38" cy="49" r="2.2" fill="#00eeb9"/><circle cx="49" cy="49" r="2.4" fill="#00eeb9"/><circle cx="60" cy="49" r="2.6" fill="#00eeb9"/><circle cx="71" cy="49" r="2.7" fill="#00eeb9"/><circle cx="82" cy="49" r="2.9" fill="#00eeb9"/><circle cx="93" cy="49" r="3.1" fill="#00eeb9"/><circle cx="5" cy="60" r="1.8" fill="#00eeb9"/><circle cx="16" cy="60" r="2.0" fill="#00eeb9"/><circle cx="27" cy="60" r="2.2" fill="#00eeb9"/><circle cx="38" cy="60" r="2.4" fill="#00eeb9"/><circle cx="49" cy="60" r="2.6" fill="#00eeb9"/><circle cx="60" cy="60" r="2.7" fill="#00eeb9"/><circle cx="71" cy="60" r="2.9" fill="#00eeb9"/><circle cx="82" cy="60" r="3.1" fill="#00eeb9"/><circle cx="93" cy="60" r="3.3" fill="#00eeb9"/><circle cx="5" cy="71" r="2.0" fill="#00eeb9"/><circle cx="16" cy="71" r="2.2" fill="#00eeb9"/><circle cx="27" cy="71" r="2.4" fill="#00eeb9"/><circle cx="38" cy="71" r="2.6" fill="#00eeb9"/><circle cx="49" cy="71" r="2.7" fill="#00eeb9"/><circle cx="60" cy="71" r="2.9" fill="#00eeb9"/><circle cx="71" cy="71" r="3.1" fill="#00eeb9"/><circle cx="82" cy="71" r="3.3" fill="#00eeb9"/><circle cx="93" cy="71" r="3.5" fill="#00eeb9"/><circle cx="5" cy="82" r="2.2" fill="#00eeb9"/><circle cx="16" cy="82" r="2.4" fill="#00eeb9"/><circle cx="27" cy="82" r="2.6" fill="#00eeb9"/><circle cx="38" cy="82" r="2.7" fill="#00eeb9"/><circle cx="49" cy="82" r="2.9" fill="#00eeb9"/><circle cx="60" cy="82" r="3.1" fill="#00eeb9"/><circle cx="71" cy="82" r="3.3" fill="#00eeb9"/><circle cx="82" cy="82" r="3.5" fill="#00eeb9"/><circle cx="93" cy="82" r="3.7" fill="#00eeb9"/><circle cx="5" cy="93" r="2.4" fill="#00eeb9"/><circle cx="16" cy="93" r="2.6" fill="#00eeb9"/><circle cx="27" cy="93" r="2.7" fill="#00eeb9"/><circle cx="38" cy="93" r="2.9" fill="#00eeb9"/><circle cx="49" cy="93" r="3.1" fill="#00eeb9"/><circle cx="60" cy="93" r="3.3" fill="#00eeb9"/><circle cx="71" cy="93" r="3.5" fill="#00eeb9"/><circle cx="82" cy="93" r="3.7" fill="#00eeb9"/><circle cx="93" cy="93" r="3.9" fill="#00eeb9"/>`,
  "Peach Halftone": `<rect width="100" height="100" fill="#fff8ee"/><circle cx="5" cy="5" r="4.2" fill="#f9552c"/><circle cx="16" cy="5" r="3.8" fill="#f9552c"/><circle cx="27" cy="5" r="3.5" fill="#f9552c"/><circle cx="38" cy="5" r="3.3" fill="#f9552c"/><circle cx="49" cy="5" r="3.2" fill="#f9552c"/><circle cx="60" cy="5" r="3.2" fill="#f9552c"/><circle cx="71" cy="5" r="3.4" fill="#f9552c"/><circle cx="82" cy="5" r="3.7" fill="#f9552c"/><circle cx="93" cy="5" r="4.1" fill="#f9552c"/><circle cx="5" cy="16" r="3.8" fill="#f9552c"/><circle cx="16" cy="16" r="3.3" fill="#f9552c"/><circle cx="27" cy="16" r="3.0" fill="#f9552c"/><circle cx="38" cy="16" r="2.7" fill="#f9552c"/><circle cx="49" cy="16" r="2.6" fill="#f9552c"/><circle cx="60" cy="16" r="2.6" fill="#f9552c"/><circle cx="71" cy="16" r="2.9" fill="#f9552c"/><circle cx="82" cy="16" r="3.3" fill="#f9552c"/><circle cx="93" cy="16" r="3.7" fill="#f9552c"/><circle cx="5" cy="27" r="3.5" fill="#f9552c"/><circle cx="16" cy="27" r="3.0" fill="#f9552c"/><circle cx="27" cy="27" r="2.5" fill="#f9552c"/><circle cx="38" cy="27" r="2.1" fill="#f9552c"/><circle cx="49" cy="27" r="1.8" fill="#f9552c"/><circle cx="60" cy="27" r="2.0" fill="#f9552c"/><circle cx="71" cy="27" r="2.4" fill="#f9552c"/><circle cx="82" cy="27" r="2.9" fill="#f9552c"/><circle cx="93" cy="27" r="3.4" fill="#f9552c"/><circle cx="5" cy="38" r="3.3" fill="#f9552c"/><circle cx="16" cy="38" r="2.7" fill="#f9552c"/><circle cx="27" cy="38" r="2.1" fill="#f9552c"/><circle cx="38" cy="38" r="1.3" fill="#f9552c"/><circle cx="49" cy="38" r="0.9" fill="#f9552c"/><circle cx="60" cy="38" r="1.2" fill="#f9552c"/><circle cx="71" cy="38" r="1.9" fill="#f9552c"/><circle cx="82" cy="38" r="2.6" fill="#f9552c"/><circle cx="93" cy="38" r="3.1" fill="#f9552c"/><circle cx="5" cy="49" r="3.2" fill="#f9552c"/><circle cx="16" cy="49" r="2.6" fill="#f9552c"/><circle cx="27" cy="49" r="1.8" fill="#f9552c"/><circle cx="38" cy="49" r="0.9" fill="#f9552c"/><circle cx="49" cy="49" r="0.3" fill="#f9552c"/><circle cx="60" cy="49" r="0.8" fill="#f9552c"/><circle cx="71" cy="49" r="1.6" fill="#f9552c"/><circle cx="82" cy="49" r="2.5" fill="#f9552c"/><circle cx="93" cy="49" r="3.1" fill="#f9552c"/><circle cx="5" cy="60" r="3.2" fill="#f9552c"/><circle cx="16" cy="60" r="2.6" fill="#f9552c"/><circle cx="27" cy="60" r="2.0" fill="#f9552c"/><circle cx="38" cy="60" r="1.2" fill="#f9552c"/><circle cx="49" cy="60" r="0.8" fill="#f9552c"/><circle cx="60" cy="60" r="1.1" fill="#f9552c"/><circle cx="71" cy="60" r="1.9" fill="#f9552c"/><circle cx="82" cy="60" r="2.5" fill="#f9552c"/><circle cx="93" cy="60" r="3.1" fill="#f9552c"/><circle cx="5" cy="71" r="3.4" fill="#f9552c"/><circle cx="16" cy="71" r="2.9" fill="#f9552c"/><circle cx="27" cy="71" r="2.4" fill="#f9552c"/><circle cx="38" cy="71" r="1.9" fill="#f9552c"/><circle cx="49" cy="71" r="1.6" fill="#f9552c"/><circle cx="60" cy="71" r="1.9" fill="#f9552c"/><circle cx="71" cy="71" r="2.3" fill="#f9552c"/><circle cx="82" cy="71" r="2.8" fill="#f9552c"/><circle cx="93" cy="71" r="3.3" fill="#f9552c"/><circle cx="5" cy="82" r="3.7" fill="#f9552c"/><circle cx="16" cy="82" r="3.3" fill="#f9552c"/><circle cx="27" cy="82" r="2.9" fill="#f9552c"/><circle cx="38" cy="82" r="2.6" fill="#f9552c"/><circle cx="49" cy="82" r="2.5" fill="#f9552c"/><circle cx="60" cy="82" r="2.5" fill="#f9552c"/><circle cx="71" cy="82" r="2.8" fill="#f9552c"/><circle cx="82" cy="82" r="3.2" fill="#f9552c"/><circle cx="93" cy="82" r="3.6" fill="#f9552c"/><circle cx="5" cy="93" r="4.1" fill="#f9552c"/><circle cx="16" cy="93" r="3.7" fill="#f9552c"/><circle cx="27" cy="93" r="3.4" fill="#f9552c"/><circle cx="38" cy="93" r="3.1" fill="#f9552c"/><circle cx="49" cy="93" r="3.1" fill="#f9552c"/><circle cx="60" cy="93" r="3.1" fill="#f9552c"/><circle cx="71" cy="93" r="3.3" fill="#f9552c"/><circle cx="82" cy="93" r="3.6" fill="#f9552c"/><circle cx="93" cy="93" r="4.0" fill="#f9552c"/>`,
  "Contour": `<rect width="100" height="100" fill="#fff8ee"/><circle cx="82" cy="14" r="9" fill="none" stroke="#07b9a7" stroke-width="4.5"/><circle cx="82" cy="14" r="19.5" fill="none" stroke="#00eeb9" stroke-width="4.5"/><circle cx="82" cy="14" r="30" fill="none" stroke="#a4bc45" stroke-width="4.5"/><circle cx="82" cy="14" r="40.5" fill="none" stroke="#07b9a7" stroke-width="4.5"/><circle cx="82" cy="14" r="51" fill="none" stroke="#00eeb9" stroke-width="4.5"/><circle cx="82" cy="14" r="61.5" fill="none" stroke="#a4bc45" stroke-width="4.5"/><circle cx="82" cy="14" r="72" fill="none" stroke="#07b9a7" stroke-width="4.5"/><circle cx="82" cy="14" r="82.5" fill="none" stroke="#00eeb9" stroke-width="4.5"/><circle cx="82" cy="14" r="93" fill="none" stroke="#a4bc45" stroke-width="4.5"/><circle cx="82" cy="14" r="103.5" fill="none" stroke="#07b9a7" stroke-width="4.5"/><circle cx="82" cy="14" r="114" fill="none" stroke="#00eeb9" stroke-width="4.5"/><circle cx="82" cy="14" r="124.5" fill="none" stroke="#a4bc45" stroke-width="4.5"/>`,
  "Lagoon Rings": `<rect width="100" height="100" fill="#b8146d"/><circle cx="14" cy="86" r="126" fill="#b8146d"/><circle cx="14" cy="86" r="108" fill="#eb208c"/><circle cx="14" cy="86" r="90" fill="#fbcfe4"/><circle cx="14" cy="86" r="72" fill="#f58ec2"/><circle cx="14" cy="86" r="54" fill="#fbcfe4"/><circle cx="14" cy="86" r="36" fill="#f58ec2"/><circle cx="14" cy="86" r="18" fill="#eb208c"/>`,
  "Mint Glow": `<rect width="100" height="100" fill="url(#i-mintglow)"/>`,
  "Ember Glow": `<rect width="100" height="100" fill="url(#i-emberglow)"/>`,
  "Aurora": `<rect width="100" height="100" fill="#372f8f"/><circle cx="16" cy="12" r="48" fill="url(#i-pink)"/><circle cx="88" cy="84" r="52" fill="url(#i-mint)"/><circle cx="84" cy="8" r="34" fill="url(#i-orange)"/><circle cx="10" cy="88" r="30" fill="url(#i-mint)" opacity="0.7"/>`
};
const INITIALS_SHADOW_SUFFIX = { dark: "shd", grey: "shg", "grey-wide": "shgs" };
const INITIALS_FONT_FILL = { ink: "#1d1a2e", paper: "#fff8ee" };
// Letter size as a share of the box (Part 2): two letters stand
// at 34% in paper and 36% in ink; a single letter at 42% in
// paper and 45% in ink. The box is 100 units, so the share is
// the font-size.
const INITIALS_LETTER_SIZE = { ink: { two: 36, one: 45 }, paper: { two: 34, one: 42 } };

// One combo drawn with the letters it is given: the standard's
// drawing, its pattern clipped by the circle, the letters
// centred in the combo's colour at Part 2's size, carrying the
// combo's Part 3 shadow. An unknown combo name draws Aurora,
// the assigned default. Every id in the drawing is re-prefixed
// with `prefix` (letters, digits and dashes), so a page can
// stand many marks at once. Decorative unless a title is
// handed in.
export function initialsSvg(combo, letters, prefix = "ix", title = null) {
  const meta = INITIALS_BY_NAME.get(combo) || INITIALS_BY_NAME.get(DEFAULT_INITIALS_COMBO);
  const p = String(prefix || "ix").replace(/[^A-Za-z0-9-]/g, "") || "ix";
  const escText = (v) => String(v == null ? "" : v).replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;");
  const defs = INITIALS_DEFS.replaceAll('id="i-', 'id="' + p + "-");
  const body = INITIALS_BODIES[meta.name].replaceAll("url(#i-", "url(#" + p + "-");
  const text = String(letters == null ? "" : letters);
  const size = INITIALS_LETTER_SIZE[meta.font][text.length > 1 ? "two" : "one"];
  const label = title ? ' role="img" aria-label="' + escText(title) + '"' : ' aria-hidden="true"';
  return '<svg viewBox="0 0 100 100"' + label + ">" +
    defs +
    '<clipPath id="' + p + '-clip"><circle cx="50" cy="50" r="50"/></clipPath>' +
    '<g clip-path="url(#' + p + '-clip)">' + body + "</g>" +
    '<text x="50" y="51" font-family="\'Bricolage Grotesque\',sans-serif" text-anchor="middle" dominant-baseline="central" font-size="' + size + '" font-weight="800" fill="' + INITIALS_FONT_FILL[meta.font] + '" filter="url(#' + p + "-" + INITIALS_SHADOW_SUFFIX[meta.shadow] + ')">' + escText(text) + "</text>" +
    "</svg>";
}

// The one picker (Part 5), as markup: a grid of the twelve,
// each drawn with the person's own letters, the combo's name
// standing under its drawing, the current pick marked — the
// radio stands checked and the option carries the current
// class. Styling rides the ms-picker classes, the centre's own
// account page carrying the same design.
export function initialsPicker({ current, letters, action }) {
  const cur = INITIALS_BY_NAME.has(current) ? current : DEFAULT_INITIALS_COMBO;
  const options = INITIALS_META.map((c, i) => {
    const checked = c.name === cur;
    return '<label class="ms-picker__option' + (checked ? " ms-picker__option--current" : "") + '">' +
      '<input type="radio" name="combo" value="' + c.name + '"' + (checked ? " checked" : "") + ">" +
      '<span class="ms-picker__mark">' + initialsSvg(c.name, letters, "pk" + i) + "</span>" +
      '<span class="ms-picker__name">' + c.name + "</span>" +
      "</label>";
  }).join("");
  return '<form method="post" action="' + action + '" class="ms-picker">' +
    '<div class="ms-picker__grid" role="radiogroup" aria-label="Initials background">' + options + "</div>" +
    '<p><button class="ms-btn ms-btn--secondary" type="submit">Save initials</button></p>' +
    "</form>";
}

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
function randomText(bytes) {
  return b64urlEncode(crypto.getRandomValues(new Uint8Array(bytes)));
}
async function sha256b64url(text) {
  const digest = await crypto.subtle.digest("SHA-256", new TextEncoder().encode(text));
  return b64urlEncode(new Uint8Array(digest));
}
function readCookies(request) {
  const header = request.headers.get("cookie") || "";
  const out = [];
  for (const part of header.split(";")) {
    const at = part.indexOf("=");
    if (at > 0) out.push([part.slice(0, at).trim(), part.slice(at + 1).trim()]);
  }
  return out;
}
function readCookie(request, name) {
  for (const [n, v] of readCookies(request)) if (n === name) return v;
  return null;
}
// The flow cookie an answer belongs to (#295/#256): the answer's
// own state names its cookie. The bare cookie name is the shape
// kits before per-flow cookies wrote — read as a fallback so a
// journey started just before a product re-pins still completes.
// An answer carrying no usable state falls back to a lone standing
// flow, whose state check then refuses it in the usual words.
function findFlowCookie(request, state) {
  const cookies = readCookies(request);
  if (state) {
    const named = cookies.find(([n]) => n === flowCookieName(state));
    if (named) return { name: named[0], raw: named[1] };
  }
  const legacy = cookies.find(([n]) => n === STATE_COOKIE);
  if (legacy) return { name: legacy[0], raw: legacy[1] };
  if (!state) {
    const flows = cookies.filter(([n]) => n.startsWith(STATE_COOKIE + "_"));
    if (flows.length === 1) return { name: flows[0][0], raw: flows[0][1] };
  }
  return null;
}
function clearFlowCookie(name = STATE_COOKIE) {
  return `${name}=; Path=/; HttpOnly; Secure; SameSite=Lax; Max-Age=0`;
}

// A callback arrival with no valid flow standing (#370): a
// refreshed completed callback (completion cleared its flow
// cookie), a bookmarked one, a flow the browser has dropped as
// expired, or an answer whose state no standing flow carries.
// The refusal still throws — a forged state and a missing flow
// are refused, and no session is made on any of these arrivals —
// but the error carries the noFlow mark, so the kit's own router
// can tell this moment from a genuine failure: route() answers a
// marked refusal with a redirect to the product's sign-in start
// (the person begins again), where a genuine failure keeps
// throwing for the product's problem page. A product calling
// callback() directly answers a marked refusal the same way.
function noFlowError(message) {
  const err = new Error(message);
  err.noFlow = true;
  return err;
}

// A callback arrival whose iss is missing or is not MemberSpark's
// (#418): not a sign-in return at all — a bare or mistyped
// callback address, a probe. callback() refuses it before any
// flow is acted on — the one earlier read is the mode taken for
// the journey's record (#248), which touches nothing and rides
// the refusal itself. The refusal still throws, but the error
// carries the unknownIssuer mark, so a product's catch can tell
// this arrival from a genuine failure and serve the not-a-return
// page (signInNotReturnPage) instead of the problem page: for
// this arrival the apology's story is false, because nothing
// went wrong on our side.
function issuerRefusalError(message) {
  const err = new Error(message);
  err.unknownIssuer = true;
  return err;
}

// A return path is a same-origin path and nothing else
// (MemberSpark#212): one leading slash, never two (a
// protocol-relative address), no backslash (browsers read it as a
// slash), no scheme, no whitespace or control characters, no "<"
// (the value is interpolated into the completion page). Anything
// else becomes "/". The kit validates where the value enters —
// signIn and startPopupSignIn — and again where callback reads it
// back out of the flow cookie, so a flow cookie written before
// validation stood, or by a hostile hand, cannot carry an unsafe
// value into the completion page or the fallback redirect either.
function safeReturnPath(value) {
  if (typeof value !== "string" || value.length === 0) return "/";
  if (value[0] !== "/" || value[1] === "/" || value[1] === "\\") return "/";
  if (/[\\<>\s\u0000-\u001f\u007f]/.test(value)) return "/";
  return value;
}

// Split a compact JWS and check the parts the kit always checks: the
// header names ES256 and the expected typ. Signature checking is
// verifySignature(); the claims are the caller's to finish.
function splitToken(token, expectedTyp) {
  const parts = String(token || "").split(".");
  if (parts.length !== 3) throw new Error("not a compact JWS");
  const header = JSON.parse(new TextDecoder().decode(b64urlDecode(parts[0])));
  if (header.alg !== "ES256") throw new Error("refused algorithm: " + header.alg);
  if (expectedTyp && header.typ !== expectedTyp) {
    throw new Error(`refused typ: ${header.typ} (wanted ${expectedTyp})`);
  }
  const claims = JSON.parse(new TextDecoder().decode(b64urlDecode(parts[1])));
  return { header, claims, signingInput: parts[0] + "." + parts[1], signature: parts[2] };
}

// AI key pieces (Spec 2, "AI keys"): msk_<product>_<id>_<secret>_<check>.
// The check is the first 6 base32 characters of the body's SHA-256,
// the same construction the service mints with.
const B32 = "ABCDEFGHIJKLMNOPQRSTUVWXYZ234567";
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
async function aiKeyCheck(body) {
  const digest = new Uint8Array(await crypto.subtle.digest("SHA-256", new TextEncoder().encode(body)));
  return base32Of(digest).slice(0, 6);
}
function parseAiKey(key) {
  const m = /^msk_([a-z0-9-]+)_([A-Z2-7]{16})_([A-Z2-7]{32})_([A-Z2-7]{6})$/.exec(String(key || ""));
  if (!m) return null;
  return { product: m[1], keyId: m[2], secret: m[3], check: m[4], body: `msk_${m[1]}_${m[2]}_${m[3]}` };
}

export function createMemberSparkKit(config) {
  const cfg = {
    scope: "openid profile email orgs",
    fetch: (...args) => fetch(...args),
    now: () => Date.now(),
    apiBase: null, // handed in by a test (the fake); defaults to the issuer's own addresses
    popupStartPath: ROUTES.popup, // the product's own address its Worker routes to startPopupSignIn
    silentStartPath: ROUTES.silent, // the product's own address its Worker routes to startSilentCheck
    logoutHint: null, // the sid of the sign-in being ended, when the product holds it
    ...config,
  };
  if (!cfg.clientId) throw new Error("the kit needs a clientId");
  if (!cfg.clientSecret) throw new Error("the kit needs a clientSecret");
  if (!cfg.redirectUri) throw new Error("the kit needs a redirectUri");
  // No default issuer (#280): the site host stood here and every
  // product that omitted the setting inherited it silently, then
  // refused every journey at the issuer check. A missing issuer
  // fails loudly at construction instead — set it from MemberSpark's
  // discovery document (in production, https://api.memberspark.ca).
  if (!cfg.issuer) throw new Error("the kit needs an issuer — set it from MemberSpark's discovery document (in production https://api.memberspark.ca, never the site host)");
  cfg.issuer = cfg.issuer.replace(/\/$/, "");
  const origin = new URL(cfg.redirectUri).origin;
  const api = (path) => (cfg.apiBase ? cfg.apiBase + path : cfg.issuer + "/api/v1" + path);
  const oauth = (path) => (cfg.apiBase ? new URL(cfg.apiBase).origin + "/oauth2" + path : cfg.issuer + "/oauth2" + path);

  let jwks = null, jwksAt = 0;
  // The one key-set read in flight (#303): every caller that needs
  // a read while one is running shares it, so a burst of callbacks
  // meeting an unknown kid together costs one refetch, not a
  // stampede. The read's own result — or its failure — is what
  // every waiter gets.
  let jwksReading = null;
  function readKeySet() {
    if (jwksReading) return jwksReading;
    const reading = (async () => {
      const res = await cfg.fetch(cfg.issuer + "/.well-known/jwks.json");
      if (!res.ok) throw new Error("key set read failed: " + res.status);
      const fresh = await res.json();
      jwks = fresh;
      jwksAt = cfg.now();
      return fresh;
    })();
    jwksReading = reading;
    const settle = () => { if (jwksReading === reading) jwksReading = null; };
    reading.then(settle, settle);
    return reading;
  }
  async function keySet(force = false) {
    if (!force && jwks && cfg.now() - jwksAt < JWKS_TTL_MS) return jwks;
    return readKeySet();
  }
  async function verifySignature(token, expectedTyp) {
    const t = splitToken(token, expectedTyp);
    let set = await keySet();
    let jwk = (set.keys || []).find((k) => k.kid === t.header.kid);
    if (!jwk) {
      // An unknown kid (#303): the cached set may predate a key
      // rotation. Read the set once more, then look again; still
      // unknown fails, in the open. There is no fallback to the
      // first cached key — that fallback refused every callback
      // for up to an hour after a rotation (it checked the new
      // key's tokens against the old key), and it let a token
      // whose kid merely lied check out whenever keys[0] happened
      // to be its signing key. A failed refetch fails the
      // verification with it, the same way.
      set = await keySet(true);
      jwk = (set.keys || []).find((k) => k.kid === t.header.kid);
      if (!jwk) {
        if (!(set.keys || []).length) throw new Error("no signing key published");
        throw new Error("no signing key published for kid: " + t.header.kid);
      }
    }
    const key = await crypto.subtle.importKey(
      "jwk", jwk, { name: "ECDSA", namedCurve: "P-256" }, false, ["verify"]);
    const ok = await crypto.subtle.verify(
      { name: "ECDSA", hash: "SHA-256" }, key,
      b64urlDecode(t.signature), new TextEncoder().encode(t.signingInput));
    if (!ok) throw new Error("signature does not check");
    return t.claims;
  }
  function checkClaims(claims, { audience, nonce } = {}) {
    if (claims.iss !== cfg.issuer) throw new Error("iss is not the MemberSpark address given");
    if (audience && claims.aud !== audience) throw new Error("aud is not this product");
    const nowSec = Math.floor(cfg.now() / 1000);
    if (typeof claims.exp !== "number" || claims.exp <= nowSec) throw new Error("token is past exp");
    if (nonce !== undefined && claims.nonce !== nonce) throw new Error("nonce does not match");
    return claims;
  }

  // The Ops standing a verified token's claims carry (#812):
  // the word "all" while an every-app grant stands, otherwise
  // the list of named product ids. Any other shape is no
  // standing — the centre mints only these two, and a product
  // admits by the claim covering its own id, so a shape that
  // is neither must never reach one.
  function opsStanding(claims) {
    return opsStandingValue(claims.ops);
  }

  // ---- sign-in ----
  async function signIn(request, { returnTo, popup = false, silent = false } = {}) {
    const state = randomText(32);
    const nonce = randomText(32);
    const verifier = randomText(32);
    const challenge = await sha256b64url(verifier);
    const flow = { state, nonce, verifier, path: returnTo ? safeReturnPath(returnTo) : safeReturnPath(new URL(request.url).pathname) };
    // A popup journey is marked in the flow cookie, which only this
    // product's server can read (HttpOnly). Nothing in the address or
    // in any script-readable place claims it, so no caller can ask
    // for the popup answer on a journey it did not start as one.
    if (popup) flow.mode = "popup";
    // A silent flow (#887) is marked the same way, in the same
    // cookie only this product's server can read: callback()
    // answers it with a word page for its parent window, never
    // a window of its own. The authorize carries prompt=none —
    // the ask the centre's gate answers without a page.
    if (silent) flow.mode = "silent";
    const authorize = new URL(oauth("/authorize"));
    const authorizeParams = new URLSearchParams({
      client_id: cfg.clientId,
      redirect_uri: cfg.redirectUri,
      response_type: "code",
      scope: cfg.scope,
      state, nonce,
      code_challenge: challenge,
      code_challenge_method: "S256",
    });
    if (silent) authorizeParams.set("prompt", "none");
    authorize.search = authorizeParams.toString();
    const headers = new Headers({ location: authorize.toString() });
    headers.append("set-cookie",
      `${flowCookieName(state)}=${b64urlEncode(new TextEncoder().encode(JSON.stringify(flow)))}; Path=/; HttpOnly; Secure; SameSite=Lax; Max-Age=${FLOW_TTL_SECONDS}`);
    return new Response(null, { status: 302, headers });
  }

  // The popup journey's start (Spec 4, "The popup journey"). The
  // product routes its popup start address here; its own page opened
  // that address in a popup window, and this answers with the same
  // authorize redirect signIn builds, with the flow marked as a
  // popup journey so callback() answers with the completion page.
  function startPopupSignIn(request, { returnTo } = {}) {
    const asked = returnTo || new URL(request.url).searchParams.get("returnTo") || undefined;
    return signIn(request, { returnTo: asked, popup: true });
  }

  // The silent check's start (#887): the product routes its
  // silent address here; its own page loaded that address in
  // a hidden frame, and this answers with the prompt=none
  // authorize redirect signIn builds, with the flow marked
  // as a silent journey so callback() answers with a word
  // page for the parent window.
  function startSilentCheck(request, { returnTo } = {}) {
    const asked = returnTo || new URL(request.url).searchParams.get("returnTo") || undefined;
    return signIn(request, { returnTo: asked, silent: true });
  }

  async function callback(request) {
    const url = new URL(request.url);
    const found = findFlowCookie(request, url.searchParams.get("state"));
    // The mode this answer's flow was started with, read before
    // any check that can throw (#248): the issuer refusal below
    // used to fire before the flow was ever read, so a failure at
    // the callback destroyed the only product-side trace of the
    // journey's shape — the 2026-11-11 pop-up journey that died
    // here could not be told from a full-page one in any record.
    // The read is for the record only: it changes no answer, and
    // every check below runs in its standing order. A flow that
    // does not parse, or whose state is not this answer's, gives
    // no mode — another journey's shape is never claimed as this
    // one's, and an arrival with no flow of its own (the no-flow
    // refusals below) carries none.
    let markedMode = null;
    if (found) {
      try {
        const parsed = JSON.parse(new TextDecoder().decode(b64urlDecode(found.raw)));
        if (parsed && parsed.state === url.searchParams.get("state")) {
          markedMode = parsed.mode === "popup" || parsed.mode === "silent" ? parsed.mode : "page";
        }
      } catch {
        // An unreadable flow gives no mode; the checks below
        // refuse it in their standing words.
      }
    }
    if (url.searchParams.get("iss") !== cfg.issuer) {
      const refusal = issuerRefusalError("the answer's iss is not MemberSpark's");
      if (markedMode) refusal.mode = markedMode;
      throw refusal;
    }
    if (!found) {
      // No valid flow stands for this answer (#370): either none
      // stands at all, or a flow stands but none of them is this
      // answer's — a state mismatch, in the words the refusal has
      // always used. Both refusals carry the no-flow mark.
      const anyFlow = readCookies(request).some(
        ([n]) => n === STATE_COOKIE || n.startsWith(STATE_COOKIE + "_"));
      if (anyFlow) throw noFlowError("state does not match");
      throw noFlowError("no sign-in flow stands on this browser");
    }
    const flow = JSON.parse(new TextDecoder().decode(b64urlDecode(found.raw)));
    // The journey's mode, in the record's two words (#248): it
    // rides every outcome below — the word outcomes, the success
    // return and the refusals the exchange can still throw — so
    // the product can record the shape this journey took.
    const mode = flow.mode === "popup" ? "popup" : flow.mode === "silent" ? "silent" : "page";
    // An answer carrying an error instead of a code (#327): a
    // person declining — access_denied — is not a failure. The
    // full-page journey returns to the page the flow began on.
    // A pop-up journey answers the way completion does (#359/#364):
    // a small page at the product's own origin posts the word to
    // the opener and closes — where the window is the kit's own
    // pop-up (#402; in any other window the page takes the person
    // back to the page the flow began on, standing in that
    // window) — cancelled for a decline, failed for any other
    // refusal. The words ride this page because the
    // door's own pages stand on MemberSpark's host, and the
    // opener's listener hears only its own origin: a word posted
    // by the door itself could never be heard. The door routes
    // the pop-up window here instead (the decline is an
    // access_denied answer; a failure is an error answer), and
    // never touches the opener. A full-page refusal that is not
    // a decline still throws, and the caller's catch renders the
    // problem page.
    const answerError = url.searchParams.get("error");
    if (answerError) {
      const backTo = safeReturnPath(flow.path || "/");
      const headers = new Headers();
      headers.append("set-cookie", clearFlowCookie(found.name));
      const wordPage = (type) => {
        const payload = JSON.stringify({ type }).replace(/</g, "\\u003c");
        const html = "<!doctype html><title>" + WORDS.signInOrJoin + "</title>" +
          "<p>" + WORDS.signInOrJoin + "</p>" +
          "<script>" + outcomePageScript(payload, backTo) + "</" + "script>" +
          '<p><a href="' + backTo.replace(/&/g, "&amp;").replace(/"/g, "&quot;") +
          '">Continue</a></p>';
        headers.set("content-type", "text/html; charset=utf-8");
        return new Response(html, { status: 200, headers });
      };
      const silentWordPage = (type) => {
        const payload = JSON.stringify({ type, returnTo: backTo }).replace(/</g, "\u003c");
        const html = "<!doctype html><title>" + WORDS.signInOrJoin + "</title>" +
          "<p>" + WORDS.signInOrJoin + "</p>" +
          "<script>" + silentOutcomePageScript(payload) + "</" + "script>" +
          '<p><a href="' + backTo.replace(/&/g, "&amp;").replace(/"/g, "&quot;") +
          '">Continue</a></p>';
        headers.set("content-type", "text/html; charset=utf-8");
        return new Response(html, { status: 200, headers });
      };
      if (mode === "silent") {
        // #887: the frame's answer. login_required is the
        // signed-out answer — the required word, and the
        // outcome carries no identity. Any other refusal is
        // the failed word: the page-side checker hears it as
        // no answer, never as a sign-out.
        // #897: a login_required the centre marked withheld
        // (ms_storage_access) is not that verdict: the
        // browser would not carry the question, so the word
        // is the unknown word, which the checker hears as no
        // answer. The mark granted, or no mark, keeps the
        // required word.
        if (answerError === "login_required") {
          if (url.searchParams.get("ms_storage_access") === "withheld") {
            return { silent: true, signedIn: false, noAnswer: true, mode, redirect: silentWordPage(SILENT_UNKNOWN_TYPE) };
          }
          return { silent: true, signedIn: false, mode, redirect: silentWordPage(SILENT_REQUIRED_TYPE) };
        }
        return { silent: true, signedIn: false, failed: true, mode, redirect: silentWordPage(POPUP_FAILED_TYPE) };
      }
      if (answerError === "access_denied") {
        if (flow.mode === "popup") {
          return { cancelled: true, mode, redirect: wordPage(POPUP_CANCELLED_TYPE) };
        }
        headers.set("location", backTo);
        return { cancelled: true, mode, redirect: new Response(null, { status: 302, headers }) };
      }
      if (flow.mode === "popup") {
        return { failed: true, mode, redirect: wordPage(POPUP_FAILED_TYPE) };
      }
      const refused = new Error("sign-in was refused: " + answerError);
      refused.mode = mode;
      throw refused;
    }
    // A flow found by the standing fallback (the legacy bare
    // name, or a lone flow for an answer with no usable state)
    // whose state this answer does not carry: the answer belongs
    // to no standing flow, so the refusal carries the mark too
    // (#370).
    if (url.searchParams.get("state") !== flow.state) throw noFlowError("state does not match");
    const code = url.searchParams.get("code");
    // From here the flow stands validated as this answer's own,
    // so the refusals the exchange can still throw carry its
    // mode (#248): a journey that dies at the exchange is still
    // a journey whose shape stands recorded.
    let tokens, claims;
    try {
      if (!code) throw new Error("no code in the answer");
      const res = await cfg.fetch(oauth("/token"), {
        method: "POST",
        headers: {
          "content-type": "application/x-www-form-urlencoded",
          authorization: "Basic " + btoa(cfg.clientId + ":" + cfg.clientSecret),
        },
        body: new URLSearchParams({
          grant_type: "authorization_code",
          code,
          redirect_uri: cfg.redirectUri,
          code_verifier: flow.verifier,
          // The journey's shape, told to MemberSpark at the one
          // authenticated server-to-server moment the journey
          // offers (#248): this exchange is the product's own
          // server speaking over its own credential, with the
          // mode it read from the flow cookie above — never a
          // claim in an address or in any script-readable place,
          // which the marking doctrine forbids. MemberSpark logs
          // it as the journey's taken shape when the exchange
          // succeeds, and acts on it in no way.
          ms_mode: mode,
        }).toString(),
      });
      if (!res.ok) throw new Error("code exchange failed: " + res.status);
      tokens = await res.json();
      claims = checkClaims(await verifySignature(tokens.id_token, "JWT"),
        { audience: cfg.clientId, nonce: flow.nonce });
    } catch (err) {
      if (err && typeof err === "object") err.mode = mode;
      throw err;
    }
    const returnTo = safeReturnPath(flow.path || "/");
    let redirect;
    if (flow.mode === "popup") {
      // The popup journey's answer (Spec 4, "The popup journey"): a
      // small page at the product's own origin, so it may speak to
      // its opener. It names only the return path the product itself
      // kept in its flow cookie — no identity rides in it; the
      // session the product makes from the identity above is what
      // the opener's refresh finds. It closes the window it stands
      // in where that window is the pop-up the kit opened (#402);
      // in any other window it takes the person on to returnTo
      // standing in that window, and where no opener stands it
      // links on to returnTo.
      // The "<" escape is the backstop (MemberSpark#212): the
      // stringified payload stands inside a script element, where
      // a "</script>" in the value would close the element and let
      // the rest parse as HTML. The escape keeps the JSON valid.
      const payload = JSON.stringify({ type: POPUP_COMPLETE_TYPE, returnTo }).replace(/</g, "\\u003c");
      const html = "<!doctype html><title>" + WORDS.signInOrJoin + "</title>" +
        "<p>" + WORDS.signInOrJoin + "</p>" +
        "<script>" + outcomePageScript(payload, returnTo) + "</" + "script>" +
        '<p><a href="' + returnTo.replace(/&/g, "&amp;").replace(/"/g, "&quot;") +
        '">Continue</a></p>';
      const headers = new Headers({ "content-type": "text/html; charset=utf-8" });
      headers.append("set-cookie", clearFlowCookie(found.name));
      // The completion marker (#267): set beside the cleared
      // flow cookie, before the completion page's script runs,
      // so it stands in the browser's jar even when the word it
      // posts is never heard — the opener reloaded, navigated, or
      // mid-reload at this moment. Script-readable on purpose:
      // the reloaded page's resume() reads it. Only a completion
      // sets it — a decline and a failure leave no marker (their
      // words, unheard, strand nothing the person must recover:
      // no session was made).
      headers.append("set-cookie",
        `${COMPLETED_COOKIE}=${b64urlEncode(new TextEncoder().encode(JSON.stringify({ returnTo, at: Math.floor(cfg.now() / 1000) })))}; Path=/; Secure; SameSite=Lax; Max-Age=${COMPLETED_TTL_SECONDS}`);
      redirect = new Response(html, { status: 200, headers });
    } else if (flow.mode === "silent") {
      // The silent journey's answer (#887): the same small
      // page shape at the product's own origin, but it speaks
      // to its parent window — the page that framed the check
      // — with the completion word, and it neither closes nor
      // navigates: the frame is the parent's to remove, and
      // the page behind never moved. No completion marker is
      // left: the check runs again on every arrival, so a
      // word the parent missed heals on the next page load,
      // against the session this callback made.
      const payload = JSON.stringify({ type: POPUP_COMPLETE_TYPE, returnTo }).replace(/</g, "\u003c");
      const html = "<!doctype html><title>" + WORDS.signInOrJoin + "</title>" +
        "<p>" + WORDS.signInOrJoin + "</p>" +
        "<script>" + silentOutcomePageScript(payload) + "</" + "script>" +
        '<p><a href="' + returnTo.replace(/&/g, "&amp;").replace(/"/g, "&quot;") +
        '">Continue</a></p>';
      const headers = new Headers({ "content-type": "text/html; charset=utf-8" });
      headers.append("set-cookie", clearFlowCookie(found.name));
      redirect = new Response(html, { status: 200, headers });
    } else {
      const headers = new Headers({ location: returnTo });
      headers.append("set-cookie", clearFlowCookie(found.name));
      redirect = new Response(null, { status: 302, headers });
    }
    // #946: the Ops standing, read once from the verified
    // claims — the identity's field states it and its hasOps
    // helper judges it, both from this same reading, so the
    // two can never part.
    const ops = opsStanding(claims);
    return {
      identity: {
        sub: claims.sub, sid: claims.sid, name: claims.name, email: claims.email,
        // #436: the initials beside name and email — the letters
        // the centre worked out from the name and the combo (the
        // person's pick, or Aurora, the assigned default). A
        // product renders the person's own mark from these and
        // never works letters out from the name itself.
        initials: claims.initials, initials_combo: claims.initials_combo,
        auth_time: claims.auth_time, ms_method: claims.ms_method,
        shared_device: claims.shared_device === true,
        // #914: the Ops standing (#812), read from these same
        // verified claims — the word "all", or the list of
        // product ids the person's grant covers — so a product
        // admits off the kit's field instead of decoding the
        // token itself. Where no grant stands the field is
        // absent, and a payload the signature did not cover
        // reaches no identity at all.
        ops,
        // #946: the judgement on that standing, so no product
        // writes the comparison itself — the two natural checks
        // each fail, in opposite directions: ops.includes(id)
        // reads false under "all" and throws where the field
        // is absent, and a bare truthiness check admits a
        // grant covering another product alone. True only for
        // the word "all" or a list covering the named id;
        // every other shape, an absent field included, is
        // false. The helper answers from the standing as
        // verified here, held in this closure — not from the
        // field as it may later be rewritten. It answers
        // through opsCovers (#965), the kit's one exported
        // judgement, so a UserInfo answer a product reads
        // itself is judged by the same code.
        hasOps(productId) {
          return opsCovers(ops, productId);
        },
      },
      idToken: tokens.id_token,
      mode,
      // A silent journey's outcome names itself (#887), the
      // way a decline names itself cancelled: the router
      // serves its word page untouched either way, and a
      // product calling callback() directly can tell the
      // frame's answer from a page journey's.
      ...(mode === "silent" ? { silent: true, signedIn: true } : {}),
      redirect,
    };
  }

  async function initiateLogin(request) {
    const url = new URL(request.url);
    if (url.searchParams.get("iss") !== cfg.issuer) {
      return new Response("unknown issuer", { status: 400 });
    }
    const target = url.searchParams.get("target_link_uri") || "/";
    const parsed = new URL(target, origin);
    if (parsed.origin !== origin) {
      return new Response("target is not on this product's own domain", { status: 400 });
    }
    return signIn(request, { returnTo: parsed.pathname + parsed.search });
  }

  // The dispatcher (MemberSpark#193): hand it any request under
  // the product's /auth/memberspark/ addresses and it answers the
  // kit's routes — the sign-in entry under both spellings, the
  // popup start, initiate-login, the callback, the back-channel
  // logout and the events address. It returns null for anything
  // else, the signed-out address included: that page is the
  // product's own, and the kit only names its address. On the
  // callback, hooks.onIdentity(identity, idToken) runs before the
  // kit's redirect answers, so the product makes its session
  // first. The back-channel route stands only when the product
  // hands in its endSessions; without it the request falls
  // through, the same as a path the kit does not own. On the
  // callback, onIdentity runs only when the answer carries an
  // identity: a decline or a failure answers a word outcome
  // ({ cancelled } / { failed }) with no identity in it, and the
  // router serves that outcome's redirect untouched — the hook
  // is never handed the nothing a word carries (#368). A
  // callback arrival with no valid flow standing (#370) is
  // answered here too: callback()'s refusal carries the no-flow
  // mark, and the router answers it with a redirect to the
  // sign-in start, so the person begins again — never a bare
  // error status. An issuer refusal (#418) passes through still
  // carrying its mark, so the product's catch can serve the
  // not-a-return page instead of the problem page. Every other
  // refusal still throws, for the product's problem-page handling.
  async function route(request, hooks = {}) {
    const url = new URL(request.url);
    const name = routeName(url.pathname);
    if (!name) return null;
    switch (name) {
      case "signIn":
        return signIn(request, { returnTo: url.searchParams.get("returnTo") || "/" });
      case "popup":
        return startPopupSignIn(request);
      case "silent":
        return startSilentCheck(request);
      case "initiateLogin":
        return initiateLogin(request);
      case "callback": {
        let done;
        try {
          done = await callback(request);
        } catch (err) {
          if (err && err.noFlow) {
            return new Response(null, { status: 303, headers: { location: ROUTES.signIn } });
          }
          throw err;
        }
        if (done.identity && hooks.onIdentity) await hooks.onIdentity(done.identity, done.idToken);
        return done.redirect;
      }
      case "backchannelLogout":
        return hooks.endSessions ? backchannelLogout(request, hooks.endSessions) : null;
      case "events":
        return events(request, hooks.eventHandlers || {});
      default:
        return null; // signedOut: the product's own page
    }
  }

  // ---- the page-side half, for the product's own page script ----
  //
  // The one implementation stands below, outside this factory, so
  // the page-safe factory (createMemberSparkBrowserKit) shares it:
  // the popup semantics exist exactly once in this file.
  const { forBrowser, forBrowserFromWindow } =
    popupOpener({ popupStartPath: cfg.popupStartPath, origin });
  const silent = silentChecker({ silentStartPath: cfg.silentStartPath, origin });

  // The browser's road to MemberSpark's sign-out (Spec 2, "Sign-out
  // on this device", step 1). No ID token travels in the address:
  // logout_hint is the sid of the sign-in, which the product stored
  // beside its session at callback time.
  function signOutUrl(sid, returnTo) {
    const out = new URL(oauth("/logout"));
    const hint = sid || cfg.logoutHint || "";
    out.search = new URLSearchParams({
      client_id: cfg.clientId,
      ...(hint ? { logout_hint: hint } : {}),
      ...(returnTo ? { post_logout_redirect_uri: returnTo } : {}),
    }).toString();
    return out.toString();
  }

  // ---- tokens MemberSpark sends the product ----

  // Shared check for logout and event tokens: ES256 only, the right
  // typ for the address it arrived at, not past exp, and a jti not
  // seen in the last 2 minutes — a replayed token does nothing.
  const seenJti = new Map();
  async function checkSentToken(request, expectedTyp) {
    // The token arrives form-encoded (#292): the service POSTs
    // logout_token=<the token> as application/x-www-form-urlencoded,
    // the shape OpenID Connect Back-Channel Logout sets out. Unwrap
    // the field the address names when the body is form-shaped; a
    // body that is the bare token still reads as itself.
    const body = (await request.text()).trim();
    const field = expectedTyp === "logout+jwt" ? "logout_token" : "event_token";
    const token = (new URLSearchParams(body).get(field) || body).trim();
    const t = splitToken(token, expectedTyp);
    const claims = checkClaims(await verifySignature(token, expectedTyp), { audience: cfg.clientId });
    const nowMs = cfg.now();
    for (const [jti, at] of seenJti) if (nowMs - at > 2 * 60 * 1000) seenJti.delete(jti);
    if (!claims.jti || seenJti.has(claims.jti)) throw new Error("replayed or jti-less token");
    seenJti.set(claims.jti, nowMs);
    return claims;
  }

  async function backchannelLogout(request, endSessions) {
    let claims;
    try {
      claims = await checkSentToken(request, "logout+jwt");
    } catch (e) {
      return new Response(String(e.message || e), { status: 400 });
    }
    await endSessions({ sub: claims.sub, sid: claims.sid });
    return new Response(null, { status: 200 });
  }

  async function events(request, handlers) {
    let claims;
    try {
      claims = await checkSentToken(request, "event+jwt");
    } catch (e) {
      return new Response(String(e.message || e), { status: 400 });
    }
    const kinds = Object.keys(claims.events || {});
    const kind = kinds[0];
    if (kind === "keys.rotated") await keySet(true);
    if (kind === "account.deleted") {
      // A forged deletion would make a product delete a person's
      // data: confirm it first. The centre's verdict is the status
      // and the word together — 410 carrying the flat JSON error
      // account_deleted (#907, #1145). The status alone is never
      // the verdict: a transport layer (a proxy, a CDN, a routing
      // answer) can return 410 with no centre body at all, and a
      // product acting on the bare status would delete a person's
      // data on a transport answer. Any other answer — another
      // status, a 410 carrying another word, a 410 whose body
      // does not read as the centre's JSON — confirms nothing,
      // and the event is left unacted.
      const probe = await apiFetch(`/accounts/${encodeURIComponent(claims.sub)}`);
      let word = null;
      if (probe.status === 410) {
        let body = null;
        try { body = JSON.parse(await probe.text()); } catch { body = null; }
        word = body && typeof body.error === "string" ? body.error : null;
      }
      if (probe.status !== 410 || word !== "account_deleted") {
        return new Response("deletion not confirmed", { status: 400 });
      }
    }
    const handler = handlers[kind];
    if (handler) {
      await handler({
        sub: claims.sub, organization_id: claims.organization_id,
        subs: claims.subs, key_id: claims.key_id,
      });
    }
    return new Response(null, { status: 200 });
  }

  // ---- the membership API ----
  const basic = () => "Basic " + btoa(cfg.clientId + ":" + cfg.clientSecret);
  async function apiFetch(path, opts = {}) {
    return cfg.fetch(api(path), {
      ...opts,
      headers: { authorization: basic(), ...(opts.body ? { "content-type": "application/json" } : {}), ...(opts.headers || {}) },
    });
  }
  async function apiJson(path, opts = {}) {
    const res = await apiFetch(path, opts);
    if (!res.ok) {
      const err = new Error("MemberSpark API " + res.status + " on " + path);
      err.status = res.status;
      // The centre's error answers are flat JSON objects whose
      // top-level error field carries the word a caller keys on
      // (Spec 2, the account roads' answer table) — the
      // suspension's account_suspended above all (#889). The
      // body rides the thrown error — body whole, and its error
      // word as code — so a caller keys on the word, never on
      // the bare status: a bare 403 is also what a
      // misconfigured client registration would draw, and
      // keying on it would sign every person out. A body that
      // does not parse carries nulls, and the status stands as
      // the caller's only fact, as before.
      let body = null;
      try { body = JSON.parse(await res.text()); } catch { body = null; }
      err.body = body;
      err.code = body && typeof body.error === "string" ? body.error : null;
      throw err;
    }
    return res.status === 204 ? null : res.json();
  }

  const memberCache = new Map();
  let feedCursor = null, feedAt = 0;
  async function refreshFeed() {
    try {
      const res = await apiFetch("/changes" + (feedCursor ? "?since=" + encodeURIComponent(feedCursor) : ""));
      if (res.ok) {
        const feed = await res.json();
        for (const change of feed.changes || []) {
          for (const key of [...memberCache.keys()]) {
            if (key.includes(change.sub || "") || key.includes(change.organization_id || "")) memberCache.delete(key);
          }
        }
        if (feed.cursor) feedCursor = feed.cursor;
      }
    } catch { /* the feed is a freshness aid; the 5-minute cache stands without it */ }
    feedAt = cfg.now();
  }
  async function cached(key, load) {
    const hit = memberCache.get(key);
    if (hit && cfg.now() - hit.at < MEMBER_TTL_MS) {
      if (cfg.now() - feedAt > FEED_TTL_MS) { await refreshFeed(); return cached(key, load); }
      return hit.value;
    }
    const value = await load();
    memberCache.set(key, { value, at: cfg.now() });
    return value;
  }

  const members = {
    account: (sub) => cached("account:" + sub, () => apiJson(`/accounts/${encodeURIComponent(sub)}`)),
    // #436: the pick, written from a product's account screen —
    // the person's own ID token rides as the acting proof (the
    // createOrganization shape). The answer carries the letters
    // and the new combo ({ sub, initials, initials_combo }), so
    // the product renders the person's mark at once; the cached
    // account read is dropped so the next read is fresh.
    setInitialsCombo: async (sub, combo, actingIdToken) => {
      const out = await apiJson(`/accounts/${encodeURIComponent(sub)}/initials`,
        { method: "POST", body: JSON.stringify({ combo, acting_id_token: actingIdToken }) });
      memberCache.delete("account:" + sub);
      return out;
    },
    organizations: (sub) => cached("orgs:" + sub, () => apiJson(`/accounts/${encodeURIComponent(sub)}/organizations`)),
    member: (org, sub) => cached(`member:${org}:${sub}`, async () => {
      const res = await apiFetch(`/organizations/${encodeURIComponent(org)}/members/${encodeURIComponent(sub)}`);
      if (res.status === 404) return null;
      if (!res.ok) throw new Error("MemberSpark API " + res.status);
      return res.json();
    }),
    members: (org) => cached("members:" + org, () => apiJson(`/organizations/${encodeURIComponent(org)}/members`)),
    organization: (org) => cached("org:" + org, () => apiJson(`/organizations/${encodeURIComponent(org)}`)),
    setPaidUpUntil: (org, sub, date) => apiJson(
      `/organizations/${encodeURIComponent(org)}/members/${encodeURIComponent(sub)}/paid-up-until`,
      { method: "PUT", body: JSON.stringify({ paid_up_until: date }) }),
    createOrganization: (name, organizationTermsVersion, actingIdToken) => apiJson("/organizations",
      { method: "POST", body: JSON.stringify({ name, organization_terms_version: organizationTermsVersion, acting_id_token: actingIdToken }) }),
    invite: (org, emails, actingIdToken) => apiJson(
      `/organizations/${encodeURIComponent(org)}/invitations`,
      { method: "POST", body: JSON.stringify({ emails, acting_id_token: actingIdToken }) }),
    joinRequest: (org, actingIdToken) => apiJson(
      `/organizations/${encodeURIComponent(org)}/join-requests`,
      { method: "POST", body: JSON.stringify({ acting_id_token: actingIdToken }) }),
    deletedAccounts: (since) => apiJson("/deleted-accounts" + (since ? "?since=" + encodeURIComponent(since) : "")),
  };

  // ---- AI keys ----
  const aiCache = new Map();
  const unknownBySource = new Map();
  async function aiKey(request, route) {
    const deny = (status, reason, retryAfter) => new Response(
      JSON.stringify({ error: reason, reason }),
      { status, headers: { "content-type": "application/json", ...(retryAfter ? { "retry-after": String(retryAfter) } : {}) } });
    const header = request.headers.get("authorization") || "";
    if (!header.startsWith("Bearer ")) return deny(401, "invalid");
    const parsed = parseAiKey(header.slice("Bearer ".length).trim());
    if (!parsed) return deny(401, "invalid");
    // Refused with no call: a bad checksum. A key naming another
    // product is not refused here (#1094, the AI API spec's R1):
    // the string's home segment names the product the key was
    // minted at, not the only product it may serve — its scope
    // list can cover this product too, and only the centre's
    // check can judge that, because the list, the caller's grant
    // and the stored hash all stand there. So the key goes to
    // the check below and the centre's answer decides.
    if ((await aiKeyCheck(parsed.body)) !== parsed.check) return deny(401, "invalid");
    const source = request.headers.get("cf-connecting-ip") || "unknown";
    const attempts = (unknownBySource.get(source) || []).filter((at) => cfg.now() - at < 60 * 1000);
    if (attempts.length >= 20) return deny(429, "rate_limited", 60);
    const hash = await sha256b64url(header.slice("Bearer ".length).trim());
    const hit = aiCache.get(hash);
    if (hit && cfg.now() < hit.until) {
      if (!hit.result) return deny(401, "invalid");
      const need = route && route.access === "read" ? "read" : "write";
      if (need === "write" && hit.result.access !== "write") return deny(401, "invalid");
      return hit.result;
    }
    let answer;
    try {
      const res = await apiFetch("/ai-keys/check", {
        method: "POST", body: JSON.stringify({ key: header.slice("Bearer ".length).trim() }),
      });
      if (!res.ok) throw new Error("check failed " + res.status);
      answer = await res.json();
    } catch {
      return deny(503, "unavailable", 60); // could not check: 503, never 401
    }
    if (!answer.valid) {
      attempts.push(cfg.now()); unknownBySource.set(source, attempts);
      aiCache.set(hash, { result: null, until: cfg.now() + 60 * 1000 });
      return deny(401, "invalid");
    }
    // An unmarked route is a write; a read key is refused there.
    const need = route && route.access === "read" ? "read" : "write";
    if (need === "write" && answer.access !== "write") return deny(401, "invalid");
    const ttl = answer.access === "write" ? 60 * 1000 : MEMBER_TTL_MS;
    const result = { sub: answer.sub, keyId: answer.key_id, keyName: answer.key_name, access: answer.access };
    aiCache.set(hash, { result, until: cfg.now() + ttl });
    return result;
  }

  // The agent directions page (Spec 2, "Three answers the AI can
  // tell apart"): plain text, build stamp at the top, naming 401,
  // 503 with Retry-After and 429 with Retry-After, and the floor on
  // how often to check. The standing lines also carry the kit's
  // own limits and the road's standing (Spec 2, "Directions state
  // every limit", R7 #1106): the unknown-key rate in numbers, the
  // check memories and what they mean for a change at MemberSpark,
  // and the owner's ruling in his words — so every product that
  // serves this shape states them by standing, and only a
  // product's own limits are left to its own lines.
  function directions(lines, buildStamp) {
    const body = [
      `Build: ${buildStamp || "unstamped"}`,
      "",
      ...(lines || []),
      "",
      "Answers you can tell apart:",
      "401 — your key is not valid. Do not retry it; ask the person for a new key.",
      "503 (with Retry-After) — MemberSpark could not be checked just now. Wait, then retry; your key may still be good.",
      "429 (with Retry-After) — too many checks. Wait the time named, then retry.",
      "Check no more often than every 5 minutes, or use this service's own live updates.",
      "All API use need to be from real MemberSpark users. No public access.",
      "Limits that can refuse a call: twenty keys that fail the check from one address inside a minute earn that address a 429 for a minute. This service remembers a check — a write key for a minute, a read key for five minutes, a refusal for a minute — so a change at MemberSpark, a revocation above all, can take that long to stand here.",
    ].join("\n");
    return new Response(body, { headers: { "content-type": "text/plain; charset=utf-8" } });
  }

  return { signIn, startPopupSignIn, startSilentCheck, silentForBrowser: silent.forBrowser, silentForBrowserFromWindow: silent.forBrowserFromWindow, forBrowser, forBrowserFromWindow, callback, initiateLogin, signOutUrl, backchannelLogout, events, members, aiKey, directions, route, routeName, routes: ROUTES, words: WORDS };
}

// ---- the page-side half, shared by both factories ----
//
// The server half cannot open windows; a product's page can.
// forBrowser() hands the kit the two things a page has and Node
// and Workers do not — a way to open a window and a way to hear a
// message — the way cfg.fetch hands in the network. Nothing here
// touches a global, so the kit still loads on Workers and Node.
// The popup semantics live here exactly once: the full kit's
// forBrowser and the page-safe factory both run through this.
// Whether a pop-up can work on this window (#356): the standard's
// test — a pop-up may open only where it can open AND its
// completion can reach the page that opened it. The signals, each
// read only when the window offers it (a window whose signals
// cannot be read abstains, and the pop-up road stands, as it did
// before the guard):
// — an installed app's context (a standalone-class display mode,
//   or iOS's home-screen flag): full-page.
// — an in-app web view (Android's "; wv)", or an iPhone-class
//   browser identity with no Safari in it): full-page.
// — a plain phone browser tab: GrabASpot's proven test — a narrow
//   width or a coarse primary pointer (#689 finding 13(e)) — takes
//   the full-page road, because there a pop-up opens as a whole
//   new tab and the page that opened it is often lost.
function popupCanWorkHere(win) {
  try {
    const nav = win.navigator || {};
    const ua = nav.userAgent || "";
    if (typeof win.matchMedia === "function") {
      for (const mode of ["standalone", "fullscreen", "minimal-ui", "window-controls-overlay"]) {
        if (win.matchMedia(`(display-mode: ${mode})`).matches) return false;
      }
      if (win.matchMedia("(max-width: 640px)").matches) return false;
      if (win.matchMedia("(pointer: coarse)").matches) return false;
    }
    if (nav.standalone === true) return false;
    if (ua.includes("; wv)")) return false;
    if (/(iPhone|iPod|iPad)/.test(ua) && !/Safari/.test(ua)) return false;
  } catch {
    // A window whose signals cannot be read abstains.
  }
  return true;
}

// The script the pop-up journey's answer pages carry — the
// completion page and the word pages share it (#402). It posts
// its word to the opener, as it always has, and then ends the
// window's part in the journey — but the close is guarded: a
// page may close only the window the kit opened as its pop-up,
// judged by the two marks that window carries and a sent tab
// does not — the opener-given name (POPUP_WINDOW_NAME, above)
// and an opener standing at this page's own origin (the
// completion page stands at the product's origin, and so does
// the page that opened the genuine pop-up). The opener read
// sits inside the guard's try: an opener a browser will not
// let the page judge — a closed opener, a cross-origin read a
// browser refuses — fails the mark, which is itself the
// answer. Where the marks do not stand — a tab a page script
// sent to the pop-up start on the redirect answer, an ordinary
// tab that began there — the page does not close: it takes the
// person onward standing in the tab, to the same destination
// the full-page road's redirect names (the caller hands it:
// the return path for a completion, the page the flow began
// on for a word). The onward path arrives through
// safeReturnPath, which refuses "<", so the JSON string
// carrying it cannot break out of the script element (the
// #212 backstop's ground).
function outcomePageScript(payload, onwardPath) {
  return "try{if(window.opener){window.opener.postMessage(" + payload +
    ", window.location.origin);}}catch(e){}" +
    "var msPop=false;" +
    "try{msPop=window.name===" + JSON.stringify(POPUP_WINDOW_NAME) +
    "&&!!window.opener&&window.opener.location.origin===window.location.origin;}catch(e){}" +
    "if(msPop){window.close();}else{window.location.replace(" +
    JSON.stringify(onwardPath) + ");}";
}

// The script the silent journey's answer pages carry (#887):
// the completion page and the word pages share it. It posts
// its word to the parent window — the page that framed the
// check stands at this page's own origin, so the origin it
// names is its own — and does nothing else: no close (a frame
// is not the page's window to close), no navigation (the
// person's page never moved). Where no parent stands — the
// page opened on its own, a shape the silent road is never
// started in — it posts nothing and the page simply stands.
function silentOutcomePageScript(payload) {
  return "try{if(window.parent&&window.parent!==window){window.parent.postMessage(" + payload +
    ", window.location.origin);}}catch(e){}";
}

// The door's size, and where it opens (#355): the owner found the
// pop-up landing far from the window he was using, because the kit
// asked the browser for a size and no position, leaving placement
// to the browser's own rule. The opener now carries a position too:
// centred over the opener window, computed at open time from the
// opener's own screen position and outer size, and clamped inside
// the available space of the screen the opener sits on (so a
// second display's offset carries through, and an opener near an
// edge never pushes the door off-screen). The geometry arrives as
// a power, the way the open and listen powers do — a read of the
// opener window handed in by forBrowserFromWindow, or by a caller
// with its own read. A missing power, an abstaining read, or a
// half-readable one keeps the size-only request exactly as before.
// Placement stays a request: a browser may adjust it (user
// settings, OS tiling); what the kit now guarantees is that it
// asks for the centre of the window the person is using.
const POPUP_WIDTH = 480;
const POPUP_HEIGHT = 640;

function popupFeatures(geometry) {
  const sizeOnly = `popup=yes,width=${POPUP_WIDTH},height=${POPUP_HEIGHT}`;
  let g = null;
  try { g = typeof geometry === "function" ? geometry() : null; } catch { g = null; }
  if (!g) return sizeOnly;
  const fields = [g.left, g.top, g.width, g.height, g.availLeft, g.availTop, g.availWidth, g.availHeight];
  if (!fields.every((n) => typeof n === "number" && Number.isFinite(n))) return sizeOnly;
  if (g.width <= 0 || g.height <= 0 || g.availWidth <= 0 || g.availHeight <= 0) return sizeOnly;
  const clamp = (v, lo, hi) => Math.min(Math.max(v, lo), Math.max(lo, hi));
  const left = clamp(Math.round(g.left + (g.width - POPUP_WIDTH) / 2),
    g.availLeft, g.availLeft + g.availWidth - POPUP_WIDTH);
  const top = clamp(Math.round(g.top + (g.height - POPUP_HEIGHT) / 2),
    g.availTop, g.availTop + g.availHeight - POPUP_HEIGHT);
  return `${sizeOnly},left=${left},top=${top}`;
}

// The geometry read for a real window: its on-screen position
// (screenX/screenY, with the older screenLeft/screenTop names as
// the fallback), its outer size, and the available rect of its
// screen — the part not taken by OS bars, on the display the
// window sits on. availLeft/availTop are not offered everywhere;
// absent them, that display's origin stands.
function popupGeometryOfWindow(win) {
  return () => {
    try {
      const scr = win.screen || {};
      return {
        left: typeof win.screenX === "number" ? win.screenX : win.screenLeft,
        top: typeof win.screenY === "number" ? win.screenY : win.screenTop,
        width: win.outerWidth,
        height: win.outerHeight,
        availLeft: typeof scr.availLeft === "number" ? scr.availLeft : 0,
        availTop: typeof scr.availTop === "number" ? scr.availTop : 0,
        availWidth: scr.availWidth,
        availHeight: scr.availHeight,
      };
    } catch {
      return null;
    }
  };
}

function popupOpener({ popupStartPath, origin }) {
  // The one live sign-in attempt for pages built from this opener:
  // a new attempt retires the previous attempt's listener
  // (MemberSpark#212).
  let liveListener = null;
  function forBrowser(powers) {
    const openWindow = powers && powers.open;
    const hearMessage = powers && powers.addMessageListener;
    const unhearMessage = powers && powers.removeMessageListener;
    if (typeof openWindow !== "function" || typeof hearMessage !== "function") {
      throw new Error("forBrowser needs the page's open and addMessageListener");
    }
    // The context probe (#356): handed in by forBrowserFromWindow
    // from the page's own window, or by a caller with its own read
    // of the context. Where it answers that a pop-up cannot work
    // here, the start takes the full-page road instead of opening
    // a window (in signIn, below).
    const canPopup = powers && powers.canPopup;
    // The placement read (#355): handed in by
    // forBrowserFromWindow from the page's own window, or by a
    // caller with its own read of the opener window. Where it
    // answers, the open asks for the door centred over this
    // window; where it does not, the open asks for size only, as
    // it did before.
    const geometry = powers && powers.geometry;
    // The watch powers (#265): a repeating timer, handed in the
    // same shape as the listen powers — `every` may hand back its
    // own stopper, or `stopEvery` stops what it returned. Where
    // neither is handed in, the ambient timers are the timer (a
    // page's own setInterval, the shape forBrowserFromWindow binds
    // explicitly), unref'd where the platform offers it so a test
    // rig's standing attempt never holds its process open.
    const everyTimer = powers && powers.every;
    const stopEveryTimer = powers && powers.stopEvery;
    function startWatch(tick) {
      // A timer that cannot be started — a window double without
      // one, a power that throws — leaves the attempt standing
      // unwatched, never broken: the watch is an ending's witness,
      // not a load the sign-in itself rests on.
      try {
        if (typeof everyTimer === "function") {
          const handle = everyTimer(POPUP_WATCH_MS, tick);
          if (typeof handle === "function") return handle;
          if (typeof stopEveryTimer === "function") return () => stopEveryTimer(handle);
          return () => {};
        }
        if (typeof globalThis.setInterval === "function") {
          const handle = globalThis.setInterval(tick, POPUP_WATCH_MS);
          if (handle && typeof handle.unref === "function") handle.unref();
          return () => globalThis.clearInterval(handle);
        }
      } catch { /* no watch; the attempt stands as it did before #265 */ }
      return () => {};
    }
    // The cookie powers (#267): a read and a write of the page's
    // own cookie jar, for the completion marker callback() leaves
    // behind. Handed in by forBrowserFromWindow from the page's
    // document, or by a caller with its own jar. A caller who
    // hands neither still gets the standing hearing (resume,
    // below) — only the marker recovery is absent.
    const readCookiePower = powers && powers.readCookie;
    const writeCookiePower = powers && powers.writeCookie;
    // The marker's return path, or null when no marker stands.
    // A marker that cannot be read names nothing: it is cleared
    // rather than left to wedge every later page load.
    function readMarker() {
      if (typeof readCookiePower !== "function") return null;
      let raw = null;
      try { raw = readCookiePower(COMPLETED_COOKIE); } catch { raw = null; }
      if (!raw) return null;
      try {
        const named = JSON.parse(new TextDecoder().decode(b64urlDecode(raw)));
        if (!named || typeof named.returnTo !== "string") throw new Error("the marker names no return path");
        return safeReturnPath(named.returnTo);
      } catch {
        clearMarker();
        return null;
      }
    }
    function clearMarker() {
      if (typeof writeCookiePower !== "function") return;
      try { writeCookiePower(`${COMPLETED_COOKIE}=; Path=/; Secure; SameSite=Lax; Max-Age=0`); } catch {}
    }
    // One outcome listener, shared by signIn's attempt and
    // resume's standing hearing (#267): the same origin gate (the
    // words are only ever heard from the product's own origin,
    // #364), the same three words, the same settle-once shape.
    // fallbackPath is where a completion word carrying no return
    // path lands — the attempt's own asked path, or "/" for a
    // standing hearing, which started no journey of its own.
    // Arming retires whatever listener stood before it in this
    // page (the one-live-listener rule, #212). The returned
    // handle's settle ends the whole hearing — the listener comes
    // off and the pop-up watch (#265), once the attempt attaches
    // it, stops with it, whichever road settled the attempt: a
    // word, a superseding call, the blocked road, or the watch
    // itself.
    function armOutcomeListener({ onDone, onFailed, onCancelled } = {}, fallbackPath) {
      let finished = false;
      const listener = (event) => {
        if (finished || !event || event.origin !== origin) return;
        const data = event.data || {};
        if (data.type === POPUP_FAILED_TYPE) {
          finished = true;
          settle();
          if (typeof onFailed === "function") onFailed();
          return;
        }
        if (data.type === POPUP_CANCELLED_TYPE) {
          finished = true;
          settle();
          if (typeof onCancelled === "function") onCancelled();
          return;
        }
        if (data.type !== POPUP_COMPLETE_TYPE) return;
        finished = true;
        settle();
        // The completion stands heard: its marker must not
        // recover it a second time on a later page load (#267).
        clearMarker();
        if (typeof onDone === "function") onDone(safeReturnPath(data.returnTo || fallbackPath));
      };
      const stopHearing = hearMessage(listener);
      let removeListener = () => {};
      if (typeof stopHearing === "function") {
        // addMessageListener handed back a remover: use it.
        removeListener = () => stopHearing();
      } else if (typeof unhearMessage === "function") {
        // No remover came back; settle through the remove power.
        removeListener = () => unhearMessage(listener);
      }
      let stopWatch = () => {};
      let settle = () => {
        removeListener();
        stopWatch();
        if (liveListener === settle) liveListener = null;
      };
      liveListener = settle;
      return {
        settle,
        // The watch's two questions (#265): has a word already
        // ended this attempt, and — the window closed first —
        // mark it ended before settling, so nothing else can
        // answer for it.
        isFinished: () => finished,
        finish: () => { finished = true; },
        watch: (tick) => { stopWatch = startWatch(tick); },
      };
    }
    // signIn({ returnTo, onDone }): open the product's own popup
    // start address in a window over this page. When the journey
    // completes, the completion page stands at this page's origin and
    // posts POPUP_COMPLETE_TYPE to its opener; onDone(returnTo) is
    // then the product's to refresh its signed-in state without a
    // page change. A window that does not open means popups are
    // blocked or do not exist here: the answer names the fallback,
    // and the caller's fallback sends the whole page to the
    // full-page sign-in start — never this pop-up start (#402): a
    // journey that runs in the whole tab must not carry the
    // pop-up marking, or its answer pages would try to close the
    // tab they stand in. A context where a pop-up cannot work
    // (the #356 probe) takes that same full-page road from the
    // start, with no window opened.
    // While the pop-up stands, the opener watches it (#265): if
    // the window closes with no word heard — the person closed it
    // by hand, or the browser took it — the attempt settles on
    // this side and onAbandoned answers, so the page can show its
    // word for an attempt that ended with nothing signed in. A
    // word heard first stops the watch: a completed, declined or
    // failed journey is never also an abandonment.
    function signIn({ returnTo = "/", onDone, onFailed, onBlocked, onCancelled, onAbandoned, startUrl } = {}) {
      const own = new URL(popupStartPath, origin);
      const asked = safeReturnPath(returnTo);
      if (returnTo) own.searchParams.set("returnTo", asked);
      const startAddress = startUrl || own.toString();
      // One live attempt per page (MemberSpark#212): a new call
      // retires the previous attempt's listener before adding its
      // own, so an abandoned attempt leaves nothing live and one
      // completion cannot fire two onDone calls — the second with
      // the abandoned attempt's stale return path. The listener is
      // also removed when its own attempt settles.
      if (liveListener) liveListener();
      // The full-page road by rule (#356): in a context where a
      // pop-up cannot work, no window is opened at all — the
      // answer is the blocked case's answer, without the blocked
      // words: nothing was blocked; this is the road the rule
      // names for this context.
      if (typeof canPopup === "function" && !canPopup()) {
        return { mode: "redirect", url: startAddress };
      }
      const arm = armOutcomeListener({ onDone, onFailed, onCancelled }, asked);
      const win = openWindow(startAddress, POPUP_WINDOW_NAME,
        popupFeatures(geometry));
      if (!win) {
        arm.settle();
        // The fallback announces itself before the page leaves
        // (#327): the caller's onBlocked shows the note — the
        // settled words are the kit's — then sends the page on.
        if (typeof onBlocked === "function") onBlocked(WORDS.popupBlocked);
        return { mode: "redirect", url: startAddress };
      }
      // The watch (#265): while this attempt stands, poll the
      // pop-up's own closed state. A manual close posts no word —
      // no page stands in the window to post one — so the closed
      // state is the only honest witness. When it reads closed
      // with no word heard, the attempt ends here: settle, then
      // answer onAbandoned — the attempt ended as an abandonment,
      // never as a decline (the cancelled word's fact) and never
      // as a failure. The read is guarded: a closed check that
      // throws reads as still open, and the words keep their say.
      arm.watch(() => {
        if (arm.isFinished()) return;
        let closed = false;
        try { closed = win.closed === true; } catch { closed = false; }
        if (!closed) return;
        arm.finish();
        arm.settle();
        if (typeof onAbandoned === "function") onAbandoned();
      });
      return { mode: "popup", url: startAddress };
    }
    // resume({ onDone, onFailed, onCancelled }): arm this page's
    // standing hearing for the outcome of a sign-in journey this
    // browser started — including one started by an earlier
    // document of this same window (#267). The completion word is
    // posted to the opener window, which a reload or a navigation
    // does not replace; the listener that hears it lives in a
    // document, which they do. A page that loads while a journey
    // may be in flight — every product page that offers sign-in —
    // calls resume() with the same handlers it hands signIn, so a
    // completion landing on the document now standing is heard
    // and onDone refreshes the signed-in state. A completion that
    // already landed while no document stood to hear it left the
    // marker (readMarker, above): resume reads it on arming,
    // clears it, and fires onDone once, just after arming, so the
    // stop handle is in the caller's hand first. Silence is never
    // read as an outcome: a pop-up the person closed posts
    // nothing, and resume settles nothing for it — that ending is
    // the attempt's own watch to witness (#265), and resume arms
    // no watch: it opened no window. One live listener stands per
    // page, shared with signIn: arming either retires whatever
    // stood, and a settled signIn attempt leaves the slot free
    // for the page to resume again. Returns the stop handle.
    function resume({ onDone, onFailed, onCancelled } = {}) {
      if (liveListener) liveListener();
      const arm = armOutcomeListener({ onDone, onFailed, onCancelled }, "/");
      const recovered = readMarker();
      if (recovered === null) return arm.settle;
      clearMarker();
      let stopped = false;
      const stop = () => { stopped = true; arm.settle(); };
      queueMicrotask(() => {
        if (!stopped && typeof onDone === "function") onDone(recovered);
      });
      return stop;
    }
    return { signIn, resume };
  }

  // forBrowser bound to a real page's window in one call. The
  // addMessageListener hands back the remover, so a settled or
  // superseded attempt's listener comes off the window.
  function forBrowserFromWindow(win) {
    return forBrowser({
      open: (url, name, features) => win.open(url, name, features),
      canPopup: () => popupCanWorkHere(win),
      geometry: popupGeometryOfWindow(win),
      // The marker powers (#267): the page's own cookie jar,
      // read and written through document.cookie. Only the
      // marker is ever touched — the flow cookie is HttpOnly
      // and no script-readable place holds it, by design.
      readCookie: (name) => {
        try {
          for (const part of String(win.document.cookie || "").split(";")) {
            const at = part.indexOf("=");
            if (at > 0 && part.slice(0, at).trim() === name) return part.slice(at + 1).trim();
          }
        } catch {}
        return null;
      },
      writeCookie: (str) => { try { win.document.cookie = str; } catch {} },
      addMessageListener: (fn) => {
        win.addEventListener("message", fn);
        return () => win.removeEventListener("message", fn);
      },
      removeMessageListener: (fn) => win.removeEventListener("message", fn),
      // The watch's timer (#265), bound the way the listener is:
      // every hands back its own stopper.
      every: (ms, fn) => {
        const handle = win.setInterval(fn, ms);
        return () => win.clearInterval(handle);
      },
    });
  }

  return { forBrowser, forBrowserFromWindow };
}

// The page-side arrival check (#887), sibling to popupOpener
// and built from the same powers: where the pop-up road opens
// a window, this road frames the product's silent start
// address in a hidden frame, and hears the answer in the
// pop-up road's message shape — the completion word for
// signed-in, the sign-in-required word for signed-out. A
// failed word, the unknown word (#897: the centre's negative
// arrived marked as one the browser may never have carried),
// and a bound that passes with no word heard (the centre
// unreachable, the frame refused), all answer onNoAnswer:
// the check learned nothing, and the page stands exactly as
// it was — never a sign-out, which only the required word
// may say. One live check per page, as with the pop-up
// attempts (#212): a new check retires the last.
const SILENT_TICK_MS = 500; // the checker's bound poll, the pop-up watch's own interval
const SILENT_BOUND_MS = 10000; // a check that has heard nothing in ten seconds is no answer
function silentChecker({ silentStartPath, origin }) {
  let liveSettle = null;
  function forBrowser(powers) {
    const framePower = powers && powers.frame;
    const hearMessage = powers && powers.addMessageListener;
    const unhearMessage = powers && powers.removeMessageListener;
    if (typeof framePower !== "function" || typeof hearMessage !== "function") {
      throw new Error("silentForBrowser needs the page's frame and addMessageListener");
    }
    const everyTimer = powers && powers.every;
    const stopEveryTimer = powers && powers.stopEvery;
    function startBound(tick) {
      try {
        if (typeof everyTimer === "function") {
          const handle = everyTimer(SILENT_TICK_MS, tick);
          if (typeof handle === "function") return handle;
          if (typeof stopEveryTimer === "function") return () => stopEveryTimer(handle);
          return () => {};
        }
        if (typeof globalThis.setInterval === "function") {
          const handle = globalThis.setInterval(tick, SILENT_TICK_MS);
          if (handle && typeof handle.unref === "function") handle.unref();
          return () => globalThis.clearInterval(handle);
        }
      } catch { /* no bound; the check stands until a word or a superseding call */ }
      return () => {};
    }
    function checkSignedIn({ returnTo = "/", onSignedIn, onSignedOut, onNoAnswer } = {}) {
      if (liveSettle) liveSettle();
      const own = new URL(silentStartPath, origin);
      const asked = safeReturnPath(returnTo);
      if (returnTo) own.searchParams.set("returnTo", asked);
      let finished = false;
      let removeFrame = () => {};
      let stopBound = () => {};
      let removeListener = () => {};
      function settle() {
        if (finished) return;
        finished = true;
        removeListener();
        stopBound();
        try { removeFrame(); } catch {}
        if (liveSettle === settle) liveSettle = null;
      }
      const listener = (event) => {
        if (finished || !event || event.origin !== origin) return;
        const data = event.data || {};
        if (data.type === POPUP_COMPLETE_TYPE) {
          const back = safeReturnPath(data.returnTo || asked);
          settle();
          if (typeof onSignedIn === "function") onSignedIn(back);
        } else if (data.type === SILENT_REQUIRED_TYPE) {
          settle();
          if (typeof onSignedOut === "function") onSignedOut();
        } else if (data.type === SILENT_UNKNOWN_TYPE) {
          settle();
          if (typeof onNoAnswer === "function") onNoAnswer();
        } else if (data.type === POPUP_FAILED_TYPE) {
          settle();
          if (typeof onNoAnswer === "function") onNoAnswer();
        }
      };
      const stopHearing = hearMessage(listener);
      if (typeof stopHearing === "function") removeListener = () => stopHearing();
      else if (typeof unhearMessage === "function") removeListener = () => unhearMessage(listener);
      liveSettle = settle;
      let elapsed = 0;
      stopBound = startBound(() => {
        elapsed += SILENT_TICK_MS;
        if (elapsed >= SILENT_BOUND_MS) {
          settle();
          if (typeof onNoAnswer === "function") onNoAnswer();
        }
      });
      try {
        const remover = framePower(own.toString());
        if (typeof remover === "function") removeFrame = remover;
      } catch {
        settle();
        if (typeof onNoAnswer === "function") onNoAnswer();
      }
      return { settle };
    }
    return { checkSignedIn };
  }
  function forBrowserFromWindow(win) {
    return forBrowser({
      frame: (address) => {
        const f = win.document.createElement("iframe");
        f.style.display = "none";
        f.setAttribute("aria-hidden", "true");
        f.src = address;
        win.document.body.appendChild(f);
        return () => { try { f.remove(); } catch {} };
      },
      addMessageListener: (fn) => {
        win.addEventListener("message", fn);
        return () => win.removeEventListener("message", fn);
      },
      removeMessageListener: (fn) => win.removeEventListener("message", fn),
      every: (ms, fn) => {
        const handle = win.setInterval(fn, ms);
        return () => win.clearInterval(handle);
      },
    });
  }
  return { forBrowser, forBrowserFromWindow };
}

// The page-safe factory (MemberSpark#202): the page-side half on
// its own, for a product page script served as a static asset. A
// page never holds the client secret — the secret is the product's
// Worker secret, for the server-side half alone — so this factory
// asks for the client id and the callback address only, and never
// a secret. It binds the page's window at construction and returns
// signIn ready to call; forBrowser and forBrowserFromWindow stand
// beside it for a page that hands its powers in itself. A product
// calls this; it never re-implements the popup contract.
export function createMemberSparkBrowserKit(config) {
  const cfg = {
    popupStartPath: ROUTES.popup, // the product's own address its Worker routes to startPopupSignIn
    silentStartPath: ROUTES.silent, // the product's own address its Worker routes to startSilentCheck
    ...config,
  };
  if (!cfg.clientId) throw new Error("the kit needs a clientId");
  if (!cfg.redirectUri) throw new Error("the kit needs a redirectUri");
  const origin = new URL(cfg.redirectUri).origin;
  const opener = popupOpener({ popupStartPath: cfg.popupStartPath, origin });
  const silent = silentChecker({ silentStartPath: cfg.silentStartPath, origin });
  const page = typeof window !== "undefined" ? opener.forBrowserFromWindow(window) : null;
  const silentPage = typeof window !== "undefined" ? silent.forBrowserFromWindow(window) : null;
  function signIn(args) {
    if (!page) {
      throw new Error("the browser kit's signIn needs the page's window — construct it in the page, or hand the powers in with forBrowser");
    }
    return page.signIn(args);
  }
  function resume(args) {
    if (!page) {
      throw new Error("the browser kit's resume needs the page's window — construct it in the page, or hand the powers in with forBrowser");
    }
    return page.resume(args);
  }
  function checkSignedIn(args) {
    if (!silentPage) {
      throw new Error("the browser kit's checkSignedIn needs the page's window — construct it in the page, or hand the powers in with silentForBrowser");
    }
    return silentPage.checkSignedIn(args);
  }
  return { signIn, resume, checkSignedIn, forBrowser: opener.forBrowser, forBrowserFromWindow: opener.forBrowserFromWindow, silentForBrowser: silent.forBrowser, silentForBrowserFromWindow: silent.forBrowserFromWindow };
}
