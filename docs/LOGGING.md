# Log monitoring — Actually Free

How this app stands under the fleet's Log Monitoring standard. The
standard lives in agents-policy at
standards/operations/log-monitoring.md; this file is the app's own
contract under it.

Actually Free is a generated static directory with one signed-in
surface. The pages a visitor sees are built by generate.py from
the seed files and committed; publishing uploads the committed
tree. The visitor side has no accounts and no store of its own.
Since actually-free #32 the product also carries server-side
Functions: the MemberSpark sign-in road and the Ops surface at
/ops, with standing judged per request from the session. Every
part of the standard below is read against that shape.

## The logs the product keeps

Two logs stand now, both the product's own, in one KV store
bound on the Pages project as AF_LOGS (issue #50). The
writers stand in functions/lib/ops-log.js; the shapes are
the certifiablemedia shop's, carried over where they fit.

The audit log holds the Ops door's sign-in family, one entry
per event, under family keys:

- A sign-in refusal: {kind: "sign-in-refusal", action:
  "sign-in-refusal", door, reason, at}. The door is one of
  ops-door (the sign-in road),
  ops-page or ops-data (the surface gates). The reason is a
  fixed word from the door's own vocabulary: no-flow,
  foreign-issuer, iss-mismatch, state-mismatch, token-invalid
  or unverified at the callback, and no-standing where a
  signed-in arrival is answered with the surface's 404 face
  for want of standing. The writer refuses any word outside
  the fixed sets, so no road can store an entry outside them.
- A sign-in completion: {kind: "sign-in-completion", door:
  "ops-door", standing, at}, written by the callback beside
  the session it mints. The standing is the door's own word —
  ops, test, or none for a session that admits nothing.

No entry carries a personal field: no email, no sub, no
name. An entry proves an event at the door, never whose.

The error log holds the product's Function failures, one
entry per occurrence: {kind: "site-error", at, where,
signature, cause}. The signature is from a fixed list, one
per Function road (auth_road_failure, ops_page_failure,
ops_data_failure, ops_signout_failure); the where is the
road's fixed address pattern, never a request's own address;
and the cause is the failure's message, scrubbed (no address,
no token-shaped run, no long digit run) and bounded before it
stands.

Every writer is best-effort and never throws: each call site
awaits its write before the answer leaves, so the entry
stands before the answer does, and no answer ever changes
because its record could not be written. Where the store
does not stand bound, the writers write nothing and the door
answers exactly as it did before the logs stood. The writes
are the product's own machinery, never a person's act: they
ride the door's roads for every standing alike, and the test
gate's refusals are not audit events and write nothing.

Two pieces of the shop's shape do not stand here, because
nothing here reads them: the running audit sequence (it
feeds the shop's door answers and the centre's summaries;
this product's operator door — issue #55 — counts its
families from their entries and their key names, and no
sequence stands behind its answers, and it sends no
summaries) and the daily error counts (the per-occurrence
entries are the record; the door's errors answer counts
them per window at the ask, and no count is kept).

Before this build the product kept no log at all, and the
standard named that standing: a product with no log stands
named as having none, never as quiet and never as healthy.
The naming stands in the centre's log monitoring registry,
in derickca/MemberSpark at docs/spec/log-monitoring-
registry.md, and in the build spec beside it. The registry
entry was last checked on 2026-11-15, against the shape
before the Ops surface landed; its update to the standing
this file now records is the centre's to make.

## What the standard owes, and what arises now

One owed family arises here, and it stands built (issue
#50). The sign-in road takes sign-ins, and the refusals on
this product's own side of it — a callback with no standing
flow, a foreign issuer, a token that does not verify, and a
signed-in arrival the Ops surface answers with its 404 face
for want of standing — are written to the product's own
audit log at the moment they are answered, never to the
error log, as the standard names them. Completions stand
beside them. The centre's own audit log records the centre's
side of the exchange; this product now keeps the record of
its own door too. Product-side failures stand in the same
position and are covered the same way: a Function that fails
is answered to the caller as it was before, and the failure
is written to the error log under its road's fixed signature
before it propagates.

The rest of the owed families still never arise. The Ops surface
holds no acts: it only reads, so there are no admin changes to
record. Standing is judged from the centre's token and the
centre's TEST_ACCOUNT_SUBS placement; the product grants no
roles and holds no permissions, credentials or keys of its own
to change. It deletes nothing, takes no payments, suspends
nobody and holds no account of its own to erase, so no entry
could carry an account identifier, opaque or otherwise.
Configuration changes to the product stand in the repo's own
records and the provider's dashboard; the standard's first
paragraph puts the Cloudflare account's own audit log outside
its scope.

Client failures stand in the same position as before. When the
catalogue fails to load, the page answers the visitor and
records nothing. The product has no client log, and the visitor
side has no backend to receive one.

## What the centre reads, and what is sent

The centre reads this product's log answers through its
operator door (issue #55): the errors and audit questions
compose their answers live from these families at the ask,
each call written to the door's own audit log before it
answers. The logs' other
read-back is the Ops surface itself: the data read behind
the Doors panel carries the door's recent audit entries and
error entries, worded for the panel, to a session holding
the grant — and to no one else, the surface's ordinary 404
face standing for everyone else exactly as before. No log
summaries are sent to the centre — none are made.

The product's results reports are a different road, under the
E2E Testing standard: Build Tests, Release Review and Scenario
Review finishes are reported to the centre's run-record home, and
expectations stand registered for them (actually-free #29 and
#28). That road is this app's named exception to the door shape;
under the results-store retirement its finishes land in the
centre's own keeping (MemberSpark #1508), the end state
recorded on MemberSpark #1510. It
carries no log lines and no person's data: the reporter refuses
a check name shaped like an address or a token before the wire,
caps a check's values at 200 characters, names a commit by its
short stamp and names screenshots by file name only. The
Scenario Review's failure comments on actually-free #27 carry
the run, its times and the failed checks' names from a
throwaway rig — no screenshot and no person's data.

No heartbeat is owed for these logs. Their writers are the
door's own roads, exercised by every sign-in arrival, and no
centre read watches them; a silence in the entries reads on
the surface as what it is — no arrivals — and the panel names
the store's standing plainly when no store stands bound.

Entries carry no expiry: they stand in the store until the
store itself is cleared. The volume is the door's own
traffic — sign-ins and failures, nothing else writes — and
the standard's floors bind the logs that stand, which these
now do.

## Where visitor failures go

A visitor who finds a listing that broke its promise, a mistake to
correct or an app to suggest uses the feedback form. The form posts
to the Feedback service, which is a covered product with its own
logs and its own registry entry. That road is a person's submission
to another product, not a log of this one, and nothing about it is
summarized from here.

The visitor counter on the pages is MemberSpark's. Its counting,
its logs and its summaries are the centre's side of the line.

## If the shape changes

If this product grows acts of its own, a store or a door, the
standing ends. The two logs stand already (issue #50): any new
owed family joins the audit log in the same act as the feature
that needs it, an entry shape and fixed words first, never
after. The registry entry is updated in the same act, the
centre's reads start on the standard's clocks, and this file
is rewritten to name the roads.
