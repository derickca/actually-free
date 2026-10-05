# Actually Free — free.certifiable.media

A hand-curated directory of Android apps that are **actually free**:
no ads, no in-app purchases, no subscriptions. Every app is checked
before listing. Static site, vanilla HTML/CSS/JS, zero backend.

## Regenerate

One command rebuilds everything from the research corpus:

```
python3 generate.py
```

This reads `~/workspace/certifiable-apps/apps-seed.json`, keeps the
verified listings (`include` + `per-badge`), adds QR Cards, and emits:

- `data/apps.json` — the 79 listings as JSON
- `index.html` — the directory (tiles render client-side)
- `app/<slug>.html` — one static page per app (SEO: real title, meta, OG tags)
- `sitemap.xml`, `robots.txt`
- `assets/` — styles.css, app.js, config.js, mascots

## Derick's setup steps

1. **Create the repo** at `github.com/derickca/actually-free` (public fits
   the transparency brand) and push this folder.
2. **Cloudflare Pages**: connect the repo, then add the custom domain
   `free.certifiable.media` (free SSL included).
3. **Paste your Goatcounter code** into `assets/config.js` (`GOATCOUNTER_CODE`)
   and redeploy.
4. **Feedback via ntfy** (free tier, no account, no backend): save the secret
   topic to `~/.config/actually-free/ntfy-topic` on the build machine (one
   line, no quotes), or set the `AF_NTFY_TOPIC` env var, then regenerate.
   `generate.py` XOR-obfuscates the topic with a fresh random key on every
   build — it never appears in page source as plaintext. Subscribe to the
   topic in the ntfy app (Android) or at ntfy.sh to receive the reports;
   the free tier keeps messages ~12 hours. Without a topic, the feedback
   forms are replaced by a "not available yet" notice.

## Corpus rules (baked into generate.py)

- `per-badge` listings show F-Droid/GitHub badges only — the Play URL is
  stripped, with an explainer on the detail page.
- Transparency attributes (open source / offline / no account) are derived
  **conservatively**: open source iff on F-Droid; offline / no-account only
  when the research notes say so explicitly. Missing attribute = pill absent.
- The three locked promises (no ads, no IAP, no subscriptions) hold for
  every listed app by construction.

## Awaiting Derick's call (7 — not listed)

- **Retro Music** — FLAG: Play labels clean 2026-10-04, but a separate 'Retro Music Premium' unlocker app exists — verify the base app never upsells before featuring.
- **Aves Libre** — FLAG: the Play listing (deckers.thibault.aves) is label-clean, but a paid Pro version exists — the F-Droid 'Libre' build is the fully-free one, listed here.
- **Signal** — VERDICT: NEEDS HUMAN CALL — Play shows In-App Purchases label.
- **QKSMS** — VERDICT: NEEDS HUMAN CALL — Play shows In-App Purchases label; purpose unverified (likely donation option; QKSMS is FOSS). Not on F-Droid.
- **Thunderbird (K-9 Mail)** — VERDICT: NEEDS HUMAN CALL — Play shows In-App Purchases label, almost certainly the Thunderbird donation option (non-blocking). F-Droid build clean, no anti-features.
- **Bitwarden** — VERDICT: NEEDS HUMAN CALL — Play labels clean (no ads, no IAP chips) because Premium is sold via bitwarden.com, NOT Play billing.
- **RethinkDNS** — VERDICT: NEEDS HUMAN CALL — Play shows In-App Purchases label: the app sells its Rethink Proxy Network VPN subscription in-app (from $1.75/mo).

## Documented exclusions (6 — not listed, users will ask)

- **Telegram** — VERDICT: EXCLUDE — Telegram Premium is a paid subscription tier sold in-app (Play shows In-App Purchases label). Fails the 'no subscriptions / no paid tiers' rule.
- **Proton Mail** — VERDICT: EXCLUDE — Paid Plus/Unlimited tiers; Play shows In-App Purchases label. Free tier exists but the app has paid tiers → fails the promise.
- **Tutanota** — VERDICT: EXCLUDE — Paid tiers (Revolutionary/Premium); Play shows In-App Purchases label. Same reasoning as Proton Mail.
- **DuckDuckGo Browser** — VERDICT: EXCLUDE — DuckDuckGo Privacy Pro ($9.99/mo VPN) is sold in-app; Play shows In-App Purchases label. Paid tier in-app → fails the promise.
- **Automate** — VERDICT: EXCLUDE — Premium unlock via IAP (Play shows In-App Purchases label). Easer is the actually-free automation alternative.
- **Fennec F-Droid** — VERDICT: EXCLUDE — F-Droid flags it with the Tracking anti-feature (Mozilla telemetry).
- **Yubico Authenticator** — Generate OATH codes with a YubiKey over NFC. OpenAPK desc: Free download of Yubico Authenticator APK file and source code repo under Apache-2.0 license - Latest Version …
