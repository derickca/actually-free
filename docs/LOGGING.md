# Log monitoring — Actually Free

How this app stands under the fleet's Log Monitoring standard. The
standard lives in agents-policy at docs/log-monitoring-standard.md;
this file is the app's own contract under it.

Actually Free is a generated static directory. It has no backend, no
sign-in, no accounts and no server-side store. The pages a visitor
sees are built by generate.py from the seed files and committed;
publishing uploads the committed tree. Every part of the standard
below is read against that shape.

## No log, by design

The product keeps no error log and no audit log. Nothing in the
product records an entry anywhere: there is no server side to write
one, no store to hold one and no sender to send one.

The standard names this standing. A product with no log sends no
summary and stands named as having none, never as quiet and never
as healthy. The naming stands in the centre's log monitoring
registry, in derickca/MemberSpark at docs/spec/log-monitoring-registry.md,
and in the build spec beside it. This file carries the same standing
in the app's own repo.

What follows from the standing:

- No summaries are owed to the central results store and none are
  sent. The store holds no report from this product, and that
  absence is the registered state, not a gap.
- No expectation rows stand for this product, and none should be
  registered. An expectation watches a sender; no sender stands.
- No heartbeat is owed. There is no log writer whose silence a
  heartbeat would prove.
- No retention rule stands, because nothing is kept. The standard's
  floors bind logs that exist, and none does.

## What the product never does

The audit log's owed families never arise here. The product takes
no sign-ins, so there are no refusals to record. It holds no roles,
permissions, credentials or keys of its own. It makes no
configuration changes, deletes nothing, takes no payments and
suspends nobody. There is no admin surface and no account to erase,
so no entry could carry an account identifier, opaque or otherwise.

Client failures stand in the same position. When the catalogue
fails to load, the page answers the visitor and records nothing.
The product has no client log, and growing one would need a backend
to receive it, which is the thing the design does without.

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

If this product ever grows a backend, accounts or an operator
surface, the standing ends. The two logs come first, before the
feature that needs them: an error log with signatures from a fixed
list, and an append-only audit log covering the standard's owed
families. The registry entry is updated in the same act, the
summaries start on the standard's clocks, and this file is rewritten
to name the roads.
