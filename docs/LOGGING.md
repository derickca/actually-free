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

The product keeps no error log and no audit log. Nothing in the
product writes an entry anywhere: the Functions record nothing,
the pages record nothing and no sender sends a log anywhere.

The standard names this standing. A product with no log stands
named as having none, never as quiet and never as healthy. The
naming stands in the centre's log monitoring registry, in
derickca/MemberSpark at docs/spec/log-monitoring-registry.md, and
in the build spec beside it. This file carries the same standing
in the app's own repo. The registry entry was last checked on
2026-11-15, against the shape before the Ops surface landed; the
gap the next section names stands from that landing, and the
entry's update is the centre's to make.

## What the standard owes, and what arises now

One owed family arises here now. The sign-in road takes sign-ins,
and the refusals on this product's own side of it — a callback
with no standing flow, a foreign issuer, a token that does not
verify, and a signed-in arrival the Ops surface answers with its
404 face for want of standing — are answered to the person and
recorded nowhere in this product. The standard names sign-in
refusals and security events as events that must be audited, and
a refused sign-in is written to the audit log, never the error
log. The centre's own audit log records the centre's side of the
exchange; this product keeps no record of its own door. The gap
stands named here: it closes with an audit log of the product's
own, a build of its own, and not with a sentence in this file.
Product-side failures stand in the same position: a Function that
fails is answered to the caller and recorded nowhere, where the
standard's error log would carry it under a signature from a
fixed list.

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

The product has no operator door, so the centre reads no log
answers from it and none are owed: no log stands to answer from.
No log summaries are sent to the centre — none exist to send.

The product's results reports are a different road, under the
E2E Testing standard: Build Tests, Release Review and Scenario
Review finishes are reported to the central results store, and
expectations stand registered for them (actually-free #29 and
#28). That road is this app's named exception to the door shape
and stands until its door stands (MemberSpark #1260). It
carries no log lines and no person's data: the reporter refuses
a check name shaped like an address or a token before the wire,
caps a check's values at 200 characters, names a commit by its
short stamp and names screenshots by file name only. The
Scenario Review's failure comments on actually-free #27 carry
the run, its times and the failed checks' names from a
throwaway rig — no screenshot and no person's data.

No heartbeat is owed for a log. There is no log writer whose
silence a heartbeat would prove.

No retention rule stands for a log, because no log is kept. The
standard's floors bind logs that exist, and none does.

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
standing ends. The two logs come first, before the feature that
needs them: an error log with signatures from a fixed list, and
an append-only audit log covering the standard's owed families —
the sign-in family among them, from the first day. The registry
entry is updated in the same act, the centre's reads start on the
standard's clocks, and this file is rewritten to name the roads.
