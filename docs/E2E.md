# E2E testing — Actually Free

How this app is tested under the fleet's E2E Testing standard. The
standard lives in agents-policy at docs/e2e-testing-standard.md; this
file is the app's own contract under it.

Actually Free is a generated static directory. It has no backend, no
sign-in and no accounts. The pages a visitor sees are built by
generate.py from the seed files and committed; publishing uploads the
committed tree. Every group below is read against that shape.

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
  on every push and pull request.
- The Bing submission step: `python3 test_bing_submit.py` — it runs
  tools/bing-submit.py against a fixture tree and a local stub
  endpoint. The real Bing API and the real key are never touched.
- One catalogue test on its own:
  `python3 -m unittest test_windows_catalog.WindowsCatalogueTests.test_seed`
  — the same shape names any single test in either catalogue file.
- No typecheck or lint command stands for this repo. The suites
  above are the whole gate.
- Screenshots: a change that touches a view takes screenshots of that
  view at 1280 and 390 widths with `python3 tools/shots.py`, and the
  person or agent landing the change looks at them before the push.
  Screenshots stay on the machine that took them; they never go to
  the results store.
- The public-readiness guard: `python3 tools/check-public-readiness.py`
  scans tracked files for personal information before a push. The
  values it looks for stand in one machine-local private file,
  never in this repo (the Privacy and Secrets Policy, section 6);
  a run that finds no private file reports NOT RUN, which is not
  a pass.

A flake budget stands over Build Tests and Scenario Review. A test
or scenario that fails and then passes, twice in a month, is
quarantined and an issue is filed. Before a quarantined item can be
deleted its failure is classified: a product fault is filed as its
own bug and the item stays as the bug's proof until the bug is
fixed; a harness fault starts a 14-day clock, and the item is
deleted at the end of it only when a replacement covers the same
journey or the owner signs off on the gap. A core journey is never
deleted. No test or scenario stands quarantined today.

## The deploy smoke

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

No Release Review runs yet. The runner and its reporting stand
filed on the tracker with the results reporting build, and this
declaration stands so the store's expectation follows it when they
land.

## Scenario Review

Scenario Review runs twice a day, internal on Certifiable99,
against a throwaway local copy of the committed tree. It never runs
on production and never on staging. The app has no accounts, so the
journeys use no person's data: they walk the public directory as a
visitor does.

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

The suite itself — run, journey, drive and report-failure files, a
fresh rig each run and the rig destroyed after it — stands filed on
the tracker as its own build. Until it lands, no Scenario Review
runs, and that absence stands recorded on the review issue rather
than passed over.

## The centre's groups and the test accounts

Login Review, Heartbeat Check and Standards Review are the centre's
groups, run by MemberSpark. This app has no sign-in, no accounts and
no owner or admin surfaces, so Login Review has no door to walk
here; the heartbeat the centre checks is the live site answering.

The product keeps no sign-ins, arrivals, claim rows or account
counts of its own, so there are no numbers for the standing test
accounts to be left out of. The visitor counter on the pages is
MemberSpark's; its counting is the centre's side of the line.

## Results

Every run reports to the central results store when the app's
reporter credential stands: Build Tests from the change and the
deploy smoke, Release Review from its runner, Scenario Review from
the suite. The centre mints the credential and registers the
expectations. Until then no report stands for this app in the
store, and that gap stands recorded on the review issue.
