# E2E testing — Actually Free

How this app is tested under the fleet's E2E Testing standard. The
standard lives in agents-policy at
standards/engineering/e2e-testing.md; this file is the app's own
contract under it.

Actually Free is a generated static directory. The public directory
has no backend, no visitor sign-in and no visitor accounts. Its one
signed-in surface is the Ops page at /ops, signed in through
MemberSpark (issue #32; docs/OPS.md carries that surface's own
contract). The pages a visitor sees are built by generate.py from
the seed files and committed; publishing uploads the committed
tree. Every group below is read against that shape.

## Build Tests

Build Tests run on a change, before the push, and they gate the push.

- The site surface: `python3 test_site.py` — it regenerates the tree,
  serves it locally and drives headless Chrome through the directory's
  behaviour at desktop and phone widths. Its smallest named subset:
  `python3 test_site.py --standards-only`.
- The catalogue surfaces: `python3 tools/check-windows.py`,
  `python3 tools/check-apple.py` and
  `python3 -m unittest test_windows_catalog.py test_apple_catalog.py`.
  The catalogue suites also run in the Catalogue validation workflow
  on every push to main and every pull request — a docs-only change
  runs nothing there (Test, Build and Release, §4).
- The Bing submission step: `python3 test_bing_submit.py` — it runs
  tools/bing-submit.py against a fixture tree and a local stub
  endpoint. The real Bing API and the real key are never touched.
- The deploy guards: `python3 test_deploy_guards.py` — it runs
  tools/check-publish-set.py and tools/check-removal-tripwire.py
  against fixture trees and a local stub sitemap. The live site
  is never touched.
- The Ops surface: `node test_ops.mjs` — it drives the /ops
  Pages Functions against the MemberSpark kit's own fake (a
  stub centre with its own signing key): the sign-in journey,
  admission on the ops claim, the ordinary-404 face for
  non-holders, the test account's read-only standing and
  banner, the session lifetimes, and the cache fences (the
  no-store answers and the service worker's bypass). Real
  MemberSpark and the live site are never touched.
- The results reporter: `python3 test_reporter.py` — it
  drives tools/reporter.py against a local stub intake: the
  declaration and report shapes, the event windows, the
  unconfigured no-op, the fail-soft sends, the name shape's
  refusals, the Scenario Review seam and the quarantine
  block. The real intake and the real credential are never
  touched.
- The Release Review runner: `python3 test_release_review.py`
  — it drives tools/release-review.py against a fake deploy
  record, a fake site and a stub intake: publish detection,
  day grouping, the due rule, the changed-view mapping and
  a full review's report. Real GitHub, the real site and
  the real credential are never touched.
- The Scenario Review machinery: `python3
  test_scenario_review.py` — it drives the suite's own files
  (tests/scenario-review/) against local fixtures: the
  journey registry against this contract, the wire names
  against the centre's name shape, the report-failure file
  against a fake gh, the driver's condition wait against a
  local server, and the run's payload through the reporter
  seam's shaper. The browser walks themselves are proven by
  running the suite itself, not here. Real GitHub, the real
  intake and the real credential are never touched.
- The whole set in one run: `python3 tools/build-tests.py`
  runs every suite above as one check each and reports the
  run as the change's Build Tests run (see Results). It
  exits as the suites exit; each suite still runs on its
  own, as named above.
- One catalogue test on its own:
  `python3 -m unittest test_windows_catalog.WindowsCatalogueTests.test_seed`
  — the same shape names any single test in either catalogue file.
- No typecheck or lint command stands for this repo. The suites
  above are the whole gate.
- Screenshots: a change that touches a view takes screenshots of that
  view at 1280 and 390 widths with `python3 tools/shots.py`, and the
  person or agent landing the change looks at them before the push
  and says so in the commit or on the issue. Screenshots stay on
  the machine that took them; they never go to the centre.
- The public-readiness guard: `python3 tools/check-public-readiness.py`
  scans tracked files for personal information before a push. The
  values it looks for stand in one machine-local private file,
  never in this repo (the Privacy and Secrets Policy, section 6);
  a run that finds no private file reports NOT RUN, which is not
  a pass.

A flake budget stands over Build Tests and Scenario Review. A test
or scenario that fails and then passes, twice in a month, is
quarantined and an issue is filed. The machine-readable record of
what stands quarantined is tools/quarantine.json, named here so
the prose and the reporter cannot drift; every finish report
carries the record's checks with their runs-skipped counts in
its quarantine block, an empty list when nothing stands
quarantined. Before a quarantined item can be
deleted its failure is classified: a product fault is filed as its
own bug and the item stays as the bug's proof until the bug is
fixed; a harness fault starts a 14-day clock, and the item is
deleted at the end of it only when a replacement covers the same
journey or the owner signs off on the gap. A core journey is never
deleted. No test or scenario stands quarantined today.

## The deploy smoke

Landing and publishing are separate acts (the PUBLISH_HOLD switch
in AGENTS.md); a hand dispatch publishes at once. A docs-only push
runs no deploy at all: documentation is nothing the service serves
(Test, Build and Release, §4), so the deploy workflow's push trigger
ignores Markdown-only pushes, the same exclusion the Catalogue
validation workflow carries. The docs ride the next real publish's
archive, and no publish means no Release Review row is declared for
a change that published nothing.

Two publish guards stand inside the deploy before the publish
step, in the same workflow (issue #37): the publish-set check
(tools/check-publish-set.py) proves the staged tree is complete
against its own sitemap and catalogue, and the removal tripwire
(tools/check-removal-tripwire.py) compares the staged sitemap
against the live one — a live page missing from the staged set
stops the publish unless its retirement stands recorded in
retired-pages.txt. The standard's third guard, the
destructive-migration guard, does not apply here: the site has
no migrations and holds no stored data. A trip fails the run
before anything is published, and stops that one publish only.

At deploy, Build Tests smoke the copy that just published, on
production, in the publish run itself. The checks stand named here
and run as `python3 tools/smoke.py`, a step in
.github/workflows/deploy-site.yml after the publish step:

1. The home page answers 200 and carries the directory's grid.
2. data/apps.json answers 200, parses, and holds listings.
3. The first listing's page answers 200 and carries its name.

There is no preview copy and no promotion to hold, so a red smoke
fails the deploy run: that failure is the loud alarm. A held publish
runs no smoke, because nothing reached production.

The checks that run on production — this smoke and the Release
Review below — write nothing on production. They read the site and
the deploy record; their only writes are their results reports and
runner-local state. No repo test sends email, and no repo suite
signs in through Google: the repo's sign-in tests run against the
kit's fake, and any real sign-in proof is the centre's Login Review
alone.

The smoke's checks also go to the centre's run-record home as the
deploy's Build Tests report (see Results): a step after the smoke
declares the deploy's expectation and sends the start and finish,
whether the smoke passed or failed, whenever the run published.
The same step declares the day's Release Review expectation for
the publish. Reporting never blocks the publish — the step is
fail-soft and its exit is pinned to 0.

## Release Review

Releases group by day. Publishing is batched by the PUBLISH_HOLD
switch, so a day can carry several publishes or none; one Release
Review covers the day's publishes, runs 30 minutes after the day's
last publish, and names each publish it covers. No publish day, no
Release Review.

The review checks the app's heartbeat — the site answers and the
home page renders with its catalogue — and one feature check on what
the day's publishes changed: the changed views, walked as a visitor
walks them. Release Review never blocks; it reports.

The runner stands: tools/release-review.py, woken every 15
minutes by the Release Review workflow on this repo's own runner.
It reads the day's publishes from the deploy workflow's own record
in the GitHub API — a publish stands when a deploy run's Publish
step succeeded — groups them by UTC day, and reviews each group
whose last publish is at least 30 minutes old and whose coverage
no review has earned yet. The heartbeat is the deploy smoke's own
three checks; the feature check compares the previous publish to
the day's last, walks each changed view (at most ten), and samples
the home page, the catalogue and the first listings when the
change stands for the whole tree. The report goes under the day's
run name, release-review-<UTC day>, naming each publish it covers
in its details. Coverage state stands on the runner at
~/.actually-free/release-review-state.json and advances only when
the centre accepted the finish.

Two honest differences from the bare declaration above, recorded
plainly: the 30 minutes is measured to the next quarter-hour tick
— GitHub Actions has no "30 minutes after that publish" trigger,
and its scheduler can fire late besides; the expectation's
two-hour grace absorbs both — and a day whose publishes are
separated by a quiet gap of 30 minutes or more can receive an
interim review naming the publishes so far. A later publish
reopens the day's expectation, and the day's final review
supersedes the interim one as a correction under the same run
name: the day's standing review is always the newest, naming
every publish of the day. Groups whose last publish is more than
48 hours old stand outside the runner's watch; the standing
starts with the runner.

## Scenario Review

Scenario Review runs twice a day, internal on Certifiable99,
against a throwaway local copy of the committed tree. It never runs
on production and never on staging. The journeys use no account and
no person's data: they walk the public directory as a visitor does
and never walk the Ops surface.

The contract, in the order a person lives it:

- **Core journey — find an app and reach its download.** Land on the
  home page, choose a platform, filter by a category, open a
  listing, and the listing's store or download link stands on its
  page.
- Suggest an app: the Suggest page renders and its form stands.
- Read what free means: the What is free page renders and names the
  six promises.

One standing issue on the tracker, "Scenario Review: failed and
never-ran scenarios (standing)", names the scenarios that failed
and the scenarios that never ran. A green round files nothing.

The suite stands built (issue #28) in the standard's appendix
shape — four files at tests/scenario-review/, beside this
contract:

- run.py builds the fresh rig (a git archive of the committed
  tree, unpacked into a throwaway directory and served
  locally), walks the journeys, photographs each walked page,
  reports the round and files its failures, and the rig is
  destroyed when the round ends, however it ends.
- journey.py is the contract above as walks: the core journey
  lands on the home page, chooses the Android platform,
  filters by the first category that stands, opens the first
  listing the filtered grid offers, and checks the listing's
  store or download link stands on its page; the Suggest
  journey checks the page renders and its form stands with
  its fields and submit control; the What is free journey
  checks the page renders and names the six promises.
- drive.py is the suite's hands: it finds the headless Chrome
  shell, serves the rig, and walks a page by running a script
  inside the real page. The suite waits on conditions, never
  on sleeps — the server is polled until it answers and a
  walk polls the page until each condition it names stands.
- report_failure.py files a round on the standing issue
  (#27): one comment naming the run, each failed scenario
  with its failed checks, and each scenario that never ran.
  A green round files nothing.

The twice-daily run is the Scenario Review workflow
(.github/workflows/scenario-review.yml): 06:10 and 18:10 UTC
on this repo's own self-hosted runner on Certifiable99,
internal only. Screenshots stay on the runner in weekday
folders under ~/.actually-free/scenario-review/ and never go
to the centre; the round's full record stands beside
them as a results file. The round reports to the centre's
run-record home through the reporter seam (see Results) under
the standing interval registration, and its exit is pinned
to 0 in the workflow: the review reports, it never blocks.

## The centre's groups and the test accounts

Login Review, Heartbeat Check and Standards Review are the centre's
groups, run by MemberSpark. None of them is built or run from this
repo.

Login Review walks this app on production: the public home, and,
once a day, the app's owner surface — the Ops page at /ops, through
its MemberSpark sign-in. The standing test account is admitted
there read-only: its standing is judged on every request by its sub
against the TEST_ACCOUNT_SUBS placement the centre made on the
Pages project, with the test account's banner on the page, its
X-Viewer mark on the other answers and a 15-minute session, under
the test-accounts standard. Its live proof stands on issue #32: on
2026-11-17 the centre's Login Review legs signed the test account
in at this site's door and /ops served with the banner standing.
Login Review is the only road that signs in through Google; no
repo group, suite or lane does.

Heartbeat Check is the centre's, every 30 minutes on production:
the live site answers, and the Ops sign-in starts cleanly. Its
alarms are the centre's to raise. The Release Review runner's own
heartbeat above covers the public site alone; the sign-in start
stands under this check and Login Review, not under that runner.

Standards Review is the centre's, twice a day: it renders the live
site, measures the shared chrome the site standards require and
reports only. No group compares screenshots automatically.

The product keeps no sign-ins, arrivals, claim rows or account
counts of its own, so there are no product numbers for the standing
test accounts to be left out of; the standings the Ops page shows
are machinery standings — listings, publishes and checks — not
account counts. The visitor counter on the pages is MemberSpark's;
its counting is the centre's side of the line. The test accounts'
identifiers stand only as subs in the centre's TEST_ACCOUNT_SUBS
placement; no tracked file in this repo carries the list.

## Results

The standing machinery, as built under issue #29 on the centre's
own record for this app (MemberSpark #1258), reports every run to
the centre's run-record home: Build Tests from the change and the
deploy smoke, Release Review from its runner, Scenario Review from
the suite. The sender is tools/reporter.py, on the centre home's own
intake shape (POST /api/v1/centre/runs); the Scenario Review
seam — the shaping call the suite makes when its run ends — stands
in the same file, and the suite built under issue #28 calls it.
The home is the run-record home in the centre's own sign-in store
(MemberSpark #1508), where this app's finishes land under the
results-store retirement (issue #53; the end state stands on
MemberSpark #1510).

One tension stands open against that machinery, recorded on issue
#46: the standard as amended on 2026-11-16 (the owner's direct-reads
ruling) says a product's Build Tests and Release Review standing is
not reported to the store — MemberSpark Admin reads it from the
product's own store through its operator door — and the watchers
spec carries the same scope, with no expectation row standing for
either group. This app has no operator door: docs/OPS.md records
that Admin asks it no question a door would answer. The centre's
#1258 record for this app, made after that amendment, holds the
reporter credential and the event declarations below as this app's
standing road. Which of the two the centre settles on — a door for
this app, or the standard amended to name this road — is the
MemberSpark chat's to clear. Until it is cleared, the paragraphs
below state the machinery as it stands; they do not claim the
tension away.

The reporter credential stands minted by the centre and placed as
the MEMBERSPARK_RESULTS_TOKEN repository secret; senders read it
from the environment at run time, and it never rests in this repo.
With no credential in the environment a sender prints one plain
line saying reporting is not configured and sends nothing — a
change-time run on a machine without the credential still gates
the push on its suites alone. Reporting never fails the run it
describes.

The expectations stand as the centre holds them. Scenario
Review's is a standing interval registration — twice a day,
period 43200 seconds, grace 7200 — so the suite declares nothing.
Build Tests and Release Review carry no standing registration:
each event declares its own row through the same intake under
the same credential, the row's subject the run name of the report
that will earn it. A change and a deploy each declare a Build
Tests row due one hour after the event, grace two hours; a
publish declares the day's Release Review row due 30 minutes
after it, grace two hours. Those two event roads are the ones the
tension above stands against. The standing failure issue for
Scenario Review is the tracker's "Scenario Review: failed and
never-ran scenarios (standing)" and its cadence word is
twice-daily — the two words the centre registered the interval
from.

A run is proven at the far end: a claim that a run ran names the
read that would fail if it never ran — the centre's record, the
workflow's run record or the door's answer — never a sender-side
success, a passing unit test or a valid credential alone. An
absence a never-ran run and a ran-and-reported-nothing run both
produce proves neither.
