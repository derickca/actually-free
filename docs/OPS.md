# Admin and Ops — Actually Free

How this app stands under the fleet's Admin and Ops standard. The
standard lives in agents-policy at docs/admin-and-ops-standard.md;
this file is the app's own contract under it.

Actually Free is a generated static directory. It has no backend, no
sign-in, no accounts and no server-side store. The pages a visitor
sees are built by generate.py from the seed files and committed;
publishing uploads the committed tree. Every part of the standard
below is read against that shape.

## Where the control plane lives

The standard lets a control plane live in the product's machinery,
and this product's stands there whole:

- Publishing runs from .github/workflows/deploy-site.yml, on this
  repo's own self-hosted runner on Certifiable99. The PUBLISH_HOLD
  repository variable is the publish switch: auto publishes on the
  push, a whole number of minutes batches, held never publishes on
  its own, and a hand dispatch always publishes at once.
- The checks run inside the product: test_site.py before the push,
  and the catalogue and link workflows on theirs (GitHub-hosted,
  under the written exception in AGENTS.md). No check waits on
  Admin being up, and nothing in the pipeline reads Admin at all.
- Credentials stand as GitHub repository secrets: the Cloudflare
  token and account id that publish the site, and the results
  reporter token named in docs/E2E.md. GitHub's secret list carries
  their standings. No value stands in this repo or in any page.
- The Cloudflare Pages project actually-free holds the domain and
  its settings in the provider's dashboard.

## The work surfaces

Catalogue curation is the product's work. Suggestions arrive through
the Feedback service's road, as docs/LOGGING.md records. The records
the work is done on are the seed files and the generated tree, and
the work is done through this repo's issues and pull requests. That
is the product's machinery, and it is where the standard lets the
work stand.

## Backup standing

There is no server-side store to back up. The site's whole content
is the committed tree of this repo, so the repo is the record: a
lost or damaged site is republished from it by the deploy workflow,
and republishing is the restore. No backup points stand for a store
that does not exist.

## What the product never holds

- No persons. The product has no accounts and keeps no person
  records, so the standard's person acts (suspend, lift, erase,
  merge, note, email change) do not arise here; they bind a product
  that has persons.
- No operator door. Admin directs no acts at this product and asks
  it no question a door would answer. Its test standings travel by
  the results intake (docs/E2E.md) and its view counts by
  MemberSpark's counter; both are centre roads, not doors.
- No operator standing of its own. The product grants no standing
  inside itself: no enrolments, no per-app operator lists, no
  allowlists. The fleet's operator roles are defined in Admin, and
  nothing here mirrors them.
- No logs. docs/LOGGING.md carries that standing.

## The Ops surface gap

The standard requires every app to carry an Ops surface, and names
this product's shape: an app with no sign-in of its own still
carries an Ops surface, at /ops, and MemberSpark provides the
sign-in for it. No surface stands today. The gap is filed on this
repo as actually-free #32, with the build's requirements: admission
on the Ops role as the MemberSpark session carries it, the test
role admitted read-only for the Login Review, and the surface
fenced from the cache by construction, because this domain is
edge-cached and the site's service worker caches every same-origin
GET.

Until the surface stands, the standings it would show stand in the
machinery named above: the workflow runs and their summaries, the
switch's state in the repository variables, and the secret standings
in GitHub's list.

## If the shape changes

If this product grows accounts, a backend or acts of its own, the
standing ends. The Ops surface at /ops and a door contract naming
the product's own acts are owed in the same act as the feature that
needs them, and the two logs come first (docs/LOGGING.md). This
file is rewritten then to name the roads.
