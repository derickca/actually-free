# Secrets inventory — Actually Free

Every secret this project holds: its name, its store, its purpose
and when it was last set. This inventory never holds a value (the
Privacy and Secrets Policy, agents-policy
docs/privacy-and-secrets-policy.md, section 5).

| Name | Store | Purpose | Last set |
|---|---|---|---|
| CLOUDFLARE_ACCOUNT_ID | GitHub Actions secrets | The Cloudflare account the deploy and zone jobs act on. An account identifier, held as a secret because it names the account the deploy credential reaches. | 2026-10-24 |
| CLOUDFLARE_API_TOKEN | GitHub Actions secrets | Deploys the site to Cloudflare Pages (deploy-site.yml) and writes the www redirect rule (www-redirect.yml). Handed to a job for the run only. | 2026-10-24 |
| MEMBERSPARK_RESULTS_TOKEN | GitHub Actions secrets | The results-store reporter credential for product actually-free (centre registry id 31b0624a), placed by the MemberSpark centre for the reporting senders (actually-free #29). | 2026-11-15 |
| MEMBERSPARK_CLIENT_ID | Cloudflare Pages project settings (actually-free) | The Ops surface's MemberSpark client id — the client the centre registered for this product (actually-free #32). Not a secret in itself; it stands in the project's settings beside its secret. | Not yet placed (#32) |
| MEMBERSPARK_CLIENT_SECRET | Cloudflare Pages project settings (actually-free) | The Ops door's client secret, the pair to the client id above. Read by the sign-in road only; it never stands in the repo or a published file. | Not yet placed (#32) |
| TEST_ACCOUNT_SUBS | Cloudflare Pages project settings (actually-free) | The centre's placement naming the test accounts' subs for this product, so the Ops surface admits the test standing read-only (actually-free #32). Subs only, never an address. | Not yet placed (#32) |
| OPS_GITHUB_TOKEN | Cloudflare Pages project settings (actually-free) | Optional: a read-only GitHub token for the Ops surface's Actions standings (actually-free #32). Not needed while the repo stands public — the surface reads GitHub's public API with no credential, and the token is sent only when one stands. It is owed only if the repo goes private, when the unauthenticated read would be refused. | Not placed — not needed while the repo is public (#32) |

Standing notes:

- No published file holds a secret. The site is a static tree;
  the feedback form posts to the shared msg service with no
  per-build secret, and nothing in the published files is a
  credential. The Ops surface's door settings stand in the
  Pages project's own settings, read by its Functions at run
  time; they are never written into the tree the project
  publishes.
- PUBLISH_HOLD is a repository variable, not a secret: a publish
  switch whose value is meant to be read in the open.
- The site-verification files (BingSiteAuth.xml and the root
  verification .txt) are public by design — they prove ownership
  by being readable — and are not secrets.
- One master copy of every value lives in the owner's own
  password manager; no agent holds the backup (the policy,
  section 5).
- A write to this store needs the owner's explicit approval for
  that change. Before a secret is written, check this inventory:
  a name that already stands makes the write a replacement, and
  it is stated and approved as one. After a change, update the
  "last set" date here.
