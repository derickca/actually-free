# Windows catalogue fixes — 12 October 2026

## Result

The authoritative Windows data is `data/windows-seed.json`. The original audit
covered 476 Windows listings and 661 distinct configured destinations. This
change retains all 476 research records, publishes 468, and withholds eight
records pending a suitable download, category, or product identity. Withheld
records are absent from generated JSON, detail pages and the sitemap.

## Applied changes

- Corrected publisher/download destinations for LosslessCut, RustDesk, WizFile,
  SpeedyFox, DaVinci Resolve, Listary, Opera GX, Toucan, AppCompactor, Trellix
  Stinger, ReNamer, Stickies, Chromium, Qalculate, Converber, FUPX, ScreenToGif,
  IDPhotoStudio and Colour Contrast Analyser.
- Corrected repository alternatives for Celestia, winLAME, CopyQ, Colour
  Contrast Analyser and LosslessCut. Draw.io now opens desktop releases first
  and labels the browser version separately.
- Removed broken Microsoft Store alternatives for Krita, IrfanView and VLC;
  removed failed alternative/news routes for SpeedyFox, Converber, JPEGView,
  Smart Deblur, fre:ac, PhotoFilmStrip and Texter. Working primary routes remain.
- Separated Winget package identifiers from URLs for VSCodium and Stickies.
- Corrected the Trellix spelling while preserving its existing URL slug.
- Added the publisher's explicit Windows 11 taskbar limitation to 7+ Taskbar
  Tweaker. All other compatibility states default to unverified; historical
  automated support claims have not been imported without app-specific review.
- Added notices for abandoned HexChat, ambiguous Eraser editions, AniFX's
  third-party distributor, Chromium snapshots, Smart Deblur's old open-source
  edition, and free/paid edition distinctions for Resolve, ReNamer and Listary.
- Download buttons no longer universally claim that the destination is the
  developer. PortableApps, GitHub releases and the known AniFX distributor
  receive specific labels.

## Withheld listings

| Listing | Reason / next step |
|---|---|
| 2048 | Browser game, not a verified Windows binary. Add a browser category before republishing. |
| Strawberry Music Player | Current official Windows binaries require sponsorship. Reconsider only with a legitimate free current binary that meets the directory promise. |
| YUMI Legacy | Archived edition; maintained exFAT listing remains. |
| YUMI UEFI | Archived edition; maintained exFAT listing remains. |
| Process Hacker | Its destination is already represented by System Informer. |
| PortExpert | Publisher unavailable; verify an alternative distribution before republishing. |
| Startup Sentinel | Publisher unavailable; verify the existing alternate package before republishing. |
| Duplicate Files Finder | Broken URL and ambiguous product identity; do not silently substitute a different product. |

## Validation and rebuild

Run `python3 tools/check-windows.py`, `python3 generate.py --windows-only`, then
`python3 -m unittest test_windows_catalog.py`. CI validates the seed and checks
published records, buttons, compatibility notes, withdrawn pages and sitemap.
It rejects malformed URLs, package/slug collisions and unsupported evidence
claims, including the generic PortableApps platform download page.

The Windows-only build preserves existing report form markup and the Android
snapshot. It prepares every Windows page before writing, and aborts if an
existing page/form cannot be reused. Adding a new Windows listing needs the full
build. Configure that build with `AF_ANDROID_SEED=/path/to/apps-seed.json` and
its usual feedback configuration. The external Android research corpus has not
been reconstructed from generated output.

The legacy verdict importer refuses to overwrite audited records. Edit their
seed records directly so imported research does not silently undo corrections.

`python3 tools/check-windows.py --check-links --output /tmp/windows-links.json`
produces a redirect-aware HTTP report with retries. HTTP 403, timeouts and
other transient responses require review and never automatically delist apps.
A successful HTTP response does not establish product identity, a valid binary,
licence terms, or Windows 11 support. The checker flags a small set of soft-404
page titles; it is not a substitute for reviewing download pages.

## Evidence and remaining work

The corrected historical audit is [windows-audit-2026-10-12.md](windows-audit-2026-10-12.md).
Its original compatibility totals were withdrawn because generic platform-page
evidence contaminated some app-level results (ADR is a known example). Treat
its per-app compatibility labels as research leads only.

For each app, record `windows11.status` as `unverified`, `publisher`,
`distributor`, `tested` or `unsupported`. Any non-unverified status needs an
app-specific `evidence_url` and ISO `checked_at` date. A `tested` claim also
requires `tested: true`, `version`, `architecture`, `build`, and `test_report`.
Distributor evidence applies only to that distribution. Record minimum builds,
prerequisites and limitations in `notes`; never infer support from a generic
platform page or the ability to create Windows installation media.

No Windows executables were installed or run. Remaining work includes:

1. App-specific compatibility evidence review, followed by Windows 11 VM smoke
   tests: install/extract, launch, exercise a core task, save/reopen and uninstall.
   Test ARM separately; shell, driver and hardware apps need suitable machines.
2. Resolve Eraser edition identity and AniFX installer provenance.
3. Review remaining dated PortableApps news links and repository-only links for
   stable app-specific downloads; verify HTTPS before replacing HTTP links.
4. Audit Windows binary licensing and paid-feature limits against all six site
   promises; notes alone do not certify those promises.
5. Consider a future migration from legacy `official_url` to separate website,
   download, repository and mirror fields. This change keeps that existing key
   for compatibility, separates Winget, and removes the blanket official label.

These changes are prepared for repository review; they do not themselves certify
all 468 published applications or deploy the website.

## Validation performed

- Seven catalogue regression tests passed.
- All 25 newly introduced destinations returned HTTP 200 after redirects.
- Android JSON is unchanged; all 468 retained Windows feedback forms were
  compared with the previous commit and preserved exactly.
- Python compilation and `git diff --check` passed.
- Full Android rebuild and Windows executable smoke tests were not run because
  the external Android corpus and a Windows runtime are unavailable here.
