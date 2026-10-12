# Actually Free: Windows download and Windows 11 audit

**Site:** https://free.certifiable.media/
**Audit date:** 12 October 2026
**Catalogue source:** https://free.certifiable.media/data/apps.json

## Findings at a glance

All **476 Windows catalogue entries** were included. The audit attempted all **661 distinct configured download destinations**, including primary and alternative URLs. The complete per-app register and link-error register below identify the coverage and unresolved work.

**The catalogue cannot currently be certified as entirely downloadable and Windows 11 compatible.** There are broken destinations, a malformed URL, an incorrectly attributed official website, a confirmed Windows 11 taskbar incompatibility, paid Windows binary access presented as unrestricted free software, and substantial gaps in explicit Windows 11 evidence.

### What was and was not verified

- Fetched the live catalogue, checked configured URLs with redirect-following HTTP GET requests, inspected returned pages and download navigation, and followed selected download pages. Repeated failed HTTP checks and consulted publisher/project sources for important findings.
- Checked documentation for Windows 11 support. A developer statement and a PortableApps packaging statement are reported separately.
- **No Windows 11 machine was available. No applications were installed or executed, no downloaded executable was security-certified, and no full installer transfer/hash/signature verification was performed.** A working page or a link to an EXE is not an installation test.
- Automated page inspection does not fully exercise JavaScript-only flows, Store region/login behaviour, consent forms, or every mirror. GitHub source repositories and automatically detected links are not counted as confirmed binary downloads.
- “Windows 11 not established” means insufficient evidence in the pages checked, not proven incompatibility. Some familiar, compatible apps remain in this category because this audit does not substitute general reputation for evidence.
- The public homepage retrieved through web search initially showed an older Android-only snapshot. The directly fetched live HTML and JSON included Windows; this audit uses the live JSON, not the stale search snapshot.
- This is the historical pre-change audit. Implementation and remaining work are recorded in windows-maintenance.md.

### Correction to compatibility evidence

The original automated compatibility totals are withdrawn. At least one app
(ADR) inherited evidence from the generic PortableApps platform download page,
which does not establish app-specific support. Per-app compatibility labels in
the historical register below are preliminary leads, not accepted evidence.
Do not import them into the catalogue without checking the exact app, edition
and architecture. The implementation defaults to unverified; no Windows apps
were installed or executed during this audit.

### Initial URL response totals

| Result | Unique destinations |
|---|---:|
| Invalid/error | 2 |
| 200 | 611 |
| 406 | 4 |
| 404 | 16 |
| 410 | 3 |
| 502 | 8 |
| 403 | 16 |
| 466 | 1 |

The totals above describe the initial probe. The error register records rechecks. HTTP 200 can still be a placeholder, source repository, wrong product, or unsuitable download route. HTTP 403/406/466, timeouts and gateway errors are access limitations, not sufficient evidence that the public URL is permanently broken.

## Prioritized app-specific recommendations

**P1:** correct before treating the affected download/listing as verified. **P2:** improve the destination, edition identification, or support disclosure.

### F01 · P1 · 7+ Taskbar Tweaker

Not compatible with the standard Windows 11 taskbar. The publisher limits the old-taskbar workaround to Windows 11 23H2 and earlier.

**Recommendation:** Exclude from a Windows 11-compatible collection, or explicitly mark it as Windows 7–10 / legacy only. Do not recommend restoring an obsolete taskbar just to satisfy the listing.

**Evidence:** [https://ramensoftware.com/7-taskbar-tweaker](https://ramensoftware.com/7-taskbar-tweaker)

### F02 · P1 · Strawberry Music Player

Current official Windows binaries require paid sponsorship. The catalogue has free_enough=false and promises no subscriptions, so its unrestricted-free presentation is misleading.

**Recommendation:** Remove from the strictly free Windows collection unless a current, legitimate, free Windows binary is independently verified. Explain the paid binary access if retained elsewhere; source availability alone is insufficient.

**Evidence:** [https://www.strawberrymusicplayer.org/](https://www.strawberrymusicplayer.org/)

### F03 · P1 · Lossless Cut

The primary link is losslesscut.net, whereas the developer identifies losslesscut.app and the mifi/lossless-cut GitHub repository as the only official sources. A working page is not proof of official provenance.

**Recommendation:** Replace the primary link with the verified official site. Offer the developer's GitHub release downloads for the free Windows version, distinguishing paid store versions.

**Evidence:** [https://losslesscut.app/](https://losslesscut.app/)

**Proposed destination:** [https://losslesscut.app/](https://losslesscut.app/) — direct follow-up: HTTP 200.

### F04 · P1 · VSCodium

The alternative URL is the package identifier VSCodium.VSCodium, not an absolute web URL. It cannot function as an external download URL as stored.

**Recommendation:** Remove this value from the URL field. Show `winget install --id VSCodium.VSCodium -e` as a copyable command instead, or use the official website. Validate URL schemes during the build.

**Evidence:** [https://free.certifiable.media/data/apps.json](https://free.certifiable.media/data/apps.json)

### F05 · P1 · Celestia

The alternative GitHub URL Anthony-B/Celestia-Project returned HTTP 404.

**Recommendation:** Replace the alternative with the current CelestiaProject repository/release page. Retain the working primary project website.

**Evidence:** [https://github.com/CelestiaProject/Celestia/releases](https://github.com/CelestiaProject/Celestia/releases)

**Proposed destination:** [https://github.com/CelestiaProject/Celestia/releases](https://github.com/CelestiaProject/Celestia/releases) — direct follow-up: <urlopen error timed out>.

### F06 · P1 · winLAME

The alternative GitHub URL hypercubemc/winlame returned HTTP 404.

**Recommendation:** Replace it with the repository identified by the official winLAME project, vividos/winLAME.

**Evidence:** [https://github.com/vividos/winLAME](https://github.com/vividos/winLAME)

**Proposed destination:** [https://github.com/vividos/winLAME](https://github.com/vividos/winLAME) — direct follow-up: HTTP 200.

### F07 · P2 · CopyQ

The alternative points to git-cgallagher/copyq rather than the upstream repository linked by the official CopyQ website.

**Recommendation:** Use hluk/CopyQ/releases for upstream Windows installers and portable archives. Keep any fork only if explicitly labelled and intentionally selected.

**Evidence:** [https://github.com/hluk/CopyQ](https://github.com/hluk/CopyQ)

**Proposed destination:** [https://github.com/hluk/CopyQ/releases](https://github.com/hluk/CopyQ/releases) — direct follow-up: HTTP 200.

### F08 · P2 · Colour Contrast Analyser

The alternative GitHub owner differs from the official Colour Contrast Analyser project.

**Recommendation:** Replace the alternative with ThePacielloGroup/CCAe/releases. The main TPGi URL redirects to Vispero's product page; update to the canonical destination when convenient.

**Evidence:** [https://vispero.com/lp/color-contrast-checker/](https://vispero.com/lp/color-contrast-checker/)

**Proposed destination:** [https://github.com/ThePacielloGroup/CCAe/releases](https://github.com/ThePacielloGroup/CCAe/releases) — direct follow-up: HTTP 200.

### F09 · P2 · Draw.io

The primary destination is the browser editor, not the desktop download page.

**Recommendation:** Use the official drawio-desktop releases for a Windows download. Keep the existing address under a separate Open web app action.

**Evidence:** [https://github.com/jgraph/drawio-desktop/releases](https://github.com/jgraph/drawio-desktop/releases)

**Proposed destination:** [https://github.com/jgraph/drawio-desktop/releases](https://github.com/jgraph/drawio-desktop/releases) — direct follow-up: HTTP 200.

### F10 · P2 · 2048

The linked project is the HTML/JavaScript browser game source repository, not a normal Windows installer distribution.

**Recommendation:** Reclassify as a browser game, or explicitly describe downloading source and opening the web game locally. Do not imply an ordinary native Windows installer is available.

**Evidence:** [https://github.com/gabrielecirulli/2048](https://github.com/gabrielecirulli/2048)

### F11 · P1 · RustDesk

The configured /download/ URL returned HTTP 404.

**Recommendation:** Use the official GitHub releases page linked from the RustDesk site; select the Windows architecture explicitly.

**Evidence:** [https://rustdesk.com/](https://rustdesk.com/)

**Proposed destination:** [https://github.com/rustdesk/rustdesk/releases/latest](https://github.com/rustdesk/rustdesk/releases/latest) — direct follow-up: HTTP 200.

### F12 · P1 · WizFile

The configured URL ending /download/ returned 404; the version without the trailing slash resolves to the product download page.

**Recommendation:** Remove the trailing slash. Preserve the personal-use limitation in the app listing.

**Evidence:** [https://antibody-software.com/wizfile/download](https://antibody-software.com/wizfile/download)

**Proposed destination:** [https://antibody-software.com/wizfile/download](https://antibody-software.com/wizfile/download) — direct follow-up: HTTP 200.

### F13 · P1 · SpeedyFox

The configured /speedyfox/ URL returned 404; /speedyfox without the trailing slash resolves and offers Windows downloads.

**Recommendation:** Use the working slashless product URL. Test current browser-profile compatibility separately; an old downloadable executable is not proof it remains suitable for every browser version.

**Evidence:** [https://crystalidea.com/speedyfox](https://crystalidea.com/speedyfox)

**Proposed destination:** [https://crystalidea.com/speedyfox](https://crystalidea.com/speedyfox) — direct follow-up: HTTP 200.

### F14 · P1 · Krita, IrfanView, VLC Media Player

The configured Microsoft Store alternatives returned HTTP 410 (Gone) in this audit.

**Recommendation:** Remove or replace these alternatives after verifying app identity, publisher, region availability and price in the Store. The existing primary publisher links are separate routes. Do not replace desktop VLC with the reduced-feature VLC UWP edition by accident.

**Evidence:** [https://free.certifiable.media/data/apps.json](https://free.certifiable.media/data/apps.json)

### F15 · P2 · YUMI Legacy, YUMI UEFI

Both point to the same current YUMI page as YUMI exFAT. That publisher page identifies Legacy and UEFI-only builds as archived and unsupported.

**Recommendation:** Archive these two listings or label them historical. Keep the supported variant clearly named and link to its section. Do not infer that Windows 11 installation media support proves host application compatibility.

**Evidence:** [https://pendrivelinux.com/yumi-multiboot-usb-creator/](https://pendrivelinux.com/yumi-multiboot-usb-creator/)

### F16 · P2 · DaVinci Resolve

The link lands on the vendor's general homepage rather than the Resolve product/download page.

**Recommendation:** Link directly to the Resolve product page and identify the free edition, Windows architecture, registration step and hardware requirements.

**Evidence:** [https://www.blackmagicdesign.com/products/davinciresolve](https://www.blackmagicdesign.com/products/davinciresolve)

**Proposed destination:** [https://www.blackmagicdesign.com/products/davinciresolve](https://www.blackmagicdesign.com/products/davinciresolve) — direct follow-up: HTTP 200.

### F17 · P2 · Listary

The primary link points to the Pro sales page despite the listing being for a free app.

**Recommendation:** Use the official free-download route and explain the free edition's restrictions and personal-use terms.

**Evidence:** [https://www.listary.com/](https://www.listary.com/)

**Proposed destination:** [https://www.listary.com/download](https://www.listary.com/download) — direct follow-up: HTTP 200.

### F18 · P2 · Opera GX

The primary URL is the general Opera homepage, also used for the separate Opera listing.

**Recommendation:** Use the Opera GX product page so visitors select the correct browser.

**Evidence:** [https://www.opera.com/gx](https://www.opera.com/gx)

**Proposed destination:** [https://www.opera.com/gx](https://www.opera.com/gx) — direct follow-up: HTTP 200.

### F19 · P2 · Toucan

The primary URL is the PortableApps homepage rather than Toucan's page.

**Recommendation:** Use the app-specific page. PortableApps publishes Windows 11 in Toucan's system requirements; that statement concerns its packaged version.

**Evidence:** [https://portableapps.com/apps/utilities/toucan](https://portableapps.com/apps/utilities/toucan)

**Proposed destination:** [https://portableapps.com/apps/utilities/toucan](https://portableapps.com/apps/utilities/toucan) — direct follow-up: HTTP 200.

### F20 · P2 · PortableApps.com AppCompactor

The primary URL is the PortableApps homepage rather than AppCompactor's page.

**Recommendation:** Use the app-specific AppCompactor page. Search found the canonical page, but direct web retrieval was inconsistent, so recheck before changing the production link.

**Evidence:** [https://portableapps.com/apps/utilities/portableapps.com_appcompactor](https://portableapps.com/apps/utilities/portableapps.com_appcompactor)

**Proposed destination:** [https://portableapps.com/apps/utilities/portableapps.com_appcompactor](https://portableapps.com/apps/utilities/portableapps.com_appcompactor) — direct follow-up: HTTP 200.

### F21 · P2 · Trelix Stinger

The listing name misspells Trellix and the primary link is a corporate homepage.

**Recommendation:** Rename to Trellix Stinger and use its official free-tool download page. Describe it as an on-demand scanner rather than full antivirus protection.

**Evidence:** [https://www.trellix.com/downloads/free-tools/stinger/](https://www.trellix.com/downloads/free-tools/stinger/)

**Proposed destination:** [https://www.trellix.com/downloads/free-tools/stinger/](https://www.trellix.com/downloads/free-tools/stinger/) — direct follow-up: HTTP 200.

### F22 · P2 · ReNamer

The primary link opens the changelog instead of a product/download page.

**Recommendation:** Use the product page with installer and portable options, and specify the Lite/free edition restrictions.

**Evidence:** [https://www.den4b.com/products/renamer](https://www.den4b.com/products/renamer)

**Proposed destination:** [https://www.den4b.com/products/renamer](https://www.den4b.com/products/renamer) — direct follow-up: HTTP 200.

### F23 · P2 · Stickies

The primary URL is a version-history page, adding an unnecessary step.

**Recommendation:** Use the download page, which explicitly lists Windows 11 compatibility and provides EXE/ZIP choices.

**Evidence:** [https://www.zhornsoftware.co.uk/stickies/download.html](https://www.zhornsoftware.co.uk/stickies/download.html)

**Proposed destination:** [https://www.zhornsoftware.co.uk/stickies/download.html](https://www.zhornsoftware.co.uk/stickies/download.html) — direct follow-up: <urlopen error timed out>.

### F24 · P2 · Chromium

The primary destination is the project homepage. Chromium's official download guidance describes snapshot builds without automatic updates.

**Recommendation:** Point to the official download instructions and make the update limitations clear; do not present source/snapshot acquisition as equivalent to a maintained consumer browser installer.

**Evidence:** [https://www.chromium.org/getting-involved/download-chromium/](https://www.chromium.org/getting-involved/download-chromium/)

**Proposed destination:** [https://www.chromium.org/getting-involved/download-chromium/](https://www.chromium.org/getting-involved/download-chromium/) — direct follow-up: HTTP 200.

### F25 · P2 · HexChat

The linked upstream repository is archived/read-only (since February 2024). This is a maintenance warning, not proof of Windows 11 incompatibility.

**Recommendation:** Mark as unmaintained and verify a usable Windows binary plus a Windows 11 smoke test before retaining a compatibility badge.

**Evidence:** [https://github.com/hexchat/hexchat](https://github.com/hexchat/hexchat)

### F26 · P2 · Process Hacker, System Informer

Both catalogue entries share the System Informer repository, so Process Hacker's link now targets its successor rather than a distinct current product.

**Recommendation:** Consolidate into System Informer with Process Hacker as an alias, or explicitly label the old entry as a predecessor.

**Evidence:** [https://github.com/winsiderss/systeminformer](https://github.com/winsiderss/systeminformer)

### F27 · P2 · Eraser Classic, Eraser .Net

Both entries share the same Eraser website. Separate edition-specific downloads and Windows 11 evidence were not established.

**Recommendation:** Verify the exact version intended by each entry. Consolidate duplicates or label a historical build precisely; do not give both entries the same assumed support status.

**Evidence:** [https://eraser.heidi.ie](https://eraser.heidi.ie)

### F28 · P2 · AniFX

The field labelled official points to Software Informer, a third-party download directory.

**Recommendation:** Relabel as third-party and verify the publisher/binary provenance, or replace with an independently verified publisher source. Do not equate aggregator OS tags with publisher support.

**Evidence:** [https://anifx.informer.com/](https://anifx.informer.com/)

### F29 · P2 · Qalculate

The primary link is pinned to release v5.12.0.

**Recommendation:** Prefer the project's current release landing page after verifying the Windows assets, unless intentionally offering a named historical version. Pinning a release silently prevents users receiving newer fixes.

**Evidence:** [https://github.com/Qalculate/qalculate-qt/releases/tag/v5.12.0](https://github.com/Qalculate/qalculate-qt/releases/tag/v5.12.0)

### F30 · P1 · Converber

Both the configured Xyntec primary URL and the alternative 2019 PortableApps news URL returned HTTP 404.

**Recommendation:** Replace with the current PortableApps app page and identify it as the portable package.

**Evidence:** [https://portableapps.com/apps/utilities/converber_portable](https://portableapps.com/apps/utilities/converber_portable)

**Proposed destination:** [https://portableapps.com/apps/utilities/converber_portable](https://portableapps.com/apps/utilities/converber_portable) — direct follow-up: HTTP 200.

### F31 · P1 · FUPX

The primary gurupia.wordpress.com/fupx/ URL returned HTTP 404.

**Recommendation:** Use the current FUPX Portable page as a clearly labelled package source; do not substitute an unrelated similarly named tool.

**Evidence:** [https://portableapps.com/apps/utilities/free_upx_portable](https://portableapps.com/apps/utilities/free_upx_portable)

**Proposed destination:** [https://portableapps.com/apps/utilities/free_upx_portable](https://portableapps.com/apps/utilities/free_upx_portable) — direct follow-up: HTTP 200.

### F32 · P1 · PortExpert, Startup Sentinel

The configured KC Softwares homepage links returned HTTP 404.

**Recommendation:** Mark download routes unavailable until an app-specific maintained archive or publisher-approved package is verified. Avoid treating a stale product homepage as a Windows 11 support statement.

**Evidence:** [https://www.kcsoftwares.com](https://www.kcsoftwares.com)

### F33 · P1 · Duplicate Files Finder

The configured MindGems URL returned HTTP 404. MindGems offers Fast Duplicate File Finder; the catalogue name alone does not establish whether this is the intended product.

**Recommendation:** Confirm product identity first. If it is the MindGems product, rename to Fast Duplicate File Finder and link its official page, distinguishing free and paid features.

**Evidence:** [https://www.mindgems.com/products/Fast-Duplicate-File-Finder/Fast-Duplicate-File-Finder-About.htm](https://www.mindgems.com/products/Fast-Duplicate-File-Finder/Fast-Duplicate-File-Finder-About.htm)

### F34 · P1 · JPEGView, Smart Deblur, fre:ac

The configured PortableApps alternative URL returned HTTP 404.

**Recommendation:** Remove or repair the failing alternative; keep the primary project link where valid. Validate the actual package and edition instead of guessing a corrected slug.

**Evidence:** [https://free.certifiable.media/data/apps.json](https://free.certifiable.media/data/apps.json)

### F35 · P2 · ScreenToGif

The old website now redirects to nicke.tech/n-studio?migrated=true; the retrieved page did not expose a usable ScreenToGif download.

**Recommendation:** Prefer the existing developer GitHub project and its releases until the migrated site download route is verified. The developer wiki lists Windows 10/11 requirements.

**Evidence:** [https://github.com/NickeManarin/ScreenToGif/wiki](https://github.com/NickeManarin/ScreenToGif/wiki)

### F36 · P1 · PhotoFilmStrip

The configured SourceForge alternative returned HTTP 404.

**Recommendation:** Repair or remove the alternative. Use the primary publisher download page to establish the correct distribution source.

**Evidence:** [https://www.photofilmstrip.org/en/download/](https://www.photofilmstrip.org/en/download/)

### F37 · P2 · Texter

The historical Lifehacker alternative returned HTTP 404.

**Recommendation:** Remove the dead historical link or present it as an archive reference rather than a download. Retain the PortableApps download route if appropriate.

**Evidence:** [https://portableapps.com/apps/utilities/texter_portable](https://portableapps.com/apps/utilities/texter_portable)

### F38 · P2 · IDPhotoStudio

The primary KC Softwares download index returns a legacy product table with 2012 release dates and a notice about optional sponsors in some full installers. It is not a clear current IDPhotoStudio download page.

**Recommendation:** Prefer the existing app-specific PortableApps alternative after validating that exact package. The PortableApps page lists Windows 11; do not extend that package statement to an old vendor installer or assume the index guarantees no bundled offers.

**Evidence:** [https://portableapps.com/apps/graphics_pictures/idphotostudio-portable](https://portableapps.com/apps/graphics_pictures/idphotostudio-portable)

**Proposed destination:** [https://portableapps.com/apps/graphics_pictures/idphotostudio-portable](https://portableapps.com/apps/graphics_pictures/idphotostudio-portable) — direct follow-up: HTTP 200.

## Cross-catalogue changes

1. **Separate website, download page, source repository, mirror and package command.** Do not label all values in `downloads.official` as official publisher downloads; several are third-party packages. Store a URL only in URL fields. Keep `winget_id` and copyable install commands separate.
2. **Make the Windows 11 badge evidence-based.** Record the exact edition/version, x64 or ARM64, minimum OS/build, prerequisites, support-evidence URL, verification date and result. Use distinct states: publisher supported, packager supported, tested, unsupported and unverified.
3. **Prefer stable app-specific landing pages.** Replace old news announcements, corporate homepages and pinned historical releases where a current app page exists. A source repository is useful as a secondary link; the main action should lead clearly to a Windows release.
4. **Check the free Windows binary, not merely the source licence.** The paid Strawberry binary route is an immediate example. Keep optional paid editions, personal-use restrictions and Store pricing visible. This audit is not a complete re-audit of every app against all six “Actually Free” promises.
5. **Use HTTPS where a working equivalent is verified.** The catalogue contains 58 distinct configured HTTP URLs. Do not blindly rewrite them; follow redirects and verify each HTTPS endpoint first.
6. **Add recurring build checks.** Validate absolute URL schemes; follow redirects; distinguish 404/410 from bot protection and transient failures; detect soft error pages; record final destinations; verify the expected app identity; and check Windows binary availability separately from HTTP status. Retry before hiding listings.
7. **Use version-aware Windows testing for the unresolved list.** On a clean supported Windows 11 x64 VM, obtain the named release from the chosen source, verify publisher signature/checksum where published, install/extract, launch, perform one core task, save/reopen where applicable, and uninstall. Record version, OS build, result and evidence. Test ARM64 separately if advertised. Driver, shell-extension, GPU, USB and security tools also need the appropriate real hardware/privilege tests.
8. **Do not expand a packaging compatibility claim to a different edition.** Keep legacy editions, successors and portable wrappers identifiable; YUMI and Process Hacker/System Informer illustrate why this matters.

## Complete app-by-app register

Every Windows entry is listed once, in catalogue order. “Detected” is an automated page-inspection result, not certification. Findings refer to the numbered recommendations above. Click the evidence link for the Windows 11 source. Entries without a specific finding still need the follow-up implied by their download/support status.

| # | App | Primary destination | Download assessment | Windows 11 evidence | Findings / next step |
|---:|---|---|---|---|---|
| 1 | 2048 | [Current link](https://github.com/gabrielecirulli/2048) | Web/source destination | Web destination; native route needs correction · [evidence](https://github.com/gabrielecirulli/2048) | F10 |
| 2 | 4st Attack | [Current link](https://portableapps.com/apps/games/4st-attack-portable) | Binary/archive link detected; payload untested | Packager lists Windows 11 · [evidence](https://portableapps.com/apps/games/4st-attack-portable) | Verify selected binary / smoke test |
| 3 | 7+ Taskbar Tweaker | [Current link](https://rammichael.com/7-taskbar-tweaker) | Binary/archive link detected; payload untested | Unsupported standard taskbar · [evidence](https://ramensoftware.com/7-taskbar-tweaker) | F01 |
| 4 | 7-Zip | [Current link](https://www.7-zip.org/download.html) | Binary/archive link detected; payload untested | Publisher lists Windows 11 · [evidence](https://www.7-zip.org/) | Verify selected binary / smoke test |
| 5 | A Note | [Current link](https://portableapps.com/apps/office/a-note-portable) | Binary/archive link detected; payload untested | Packager lists Windows 11 · [evidence](https://portableapps.com/apps/office/a-note-portable) | Verify selected binary / smoke test |
| 6 | ADR | [Current link](https://portableapps.com/news/2017-06-08--a-dark-room-portable-1.4-released) | Old release announcement | Packager lists Windows 11 · [evidence](https://portableapps.com/download) | Verify selected binary / smoke test |
| 7 | Aegisub | [Current link](https://aegisub.org/) | Download/release navigation detected | Windows 11 not established · [evidence](https://aegisub.org/) | Verify support / run smoke test |
| 8 | AIMP | [Current link](https://www.aimp.ru/) | Download/release navigation detected | Windows 11 not established · [evidence](https://www.aimp.ru/) | Verify support / run smoke test |
| 9 | AkelPad | [Current link](http://akelpad.sourceforge.net/en/index.php) | Download/release navigation detected | Windows 11 not established · [evidence](http://akelpad.sourceforge.net/en/index.php) | Verify support / run smoke test |
| 10 | AndreaMosaic | [Current link](https://www.andreaplanet.com/andreamosaic/) | Download/release navigation detected | Publisher lists Windows 11 · [evidence](https://www.andreaplanet.com/andreamosaic/download/) | Verify selected binary / smoke test |
| 11 | Angry IP Scanner | [Current link](https://angryip.org/) | Download/release navigation detected | Windows 11 not established · [evidence](https://angryip.org/) | Verify support / run smoke test |
| 12 | AniFX | [Current link](https://anifx.informer.com/) | Download/release navigation detected | Windows 11 not established · [evidence](https://anifx.informer.com/) | F28 |
| 13 | Ant Renamer | [Current link](https://antp.be/software/renamer/) | Download/release navigation detected | Windows 11 not established · [evidence](https://antp.be/software/renamer/) | Verify support / run smoke test |
| 14 | Apache OpenOffice | [Current link](https://www.openoffice.org/download/) | Download/release navigation detected | Windows 11 not established · [evidence](https://www.openoffice.org/download/) | Verify support / run smoke test |
| 15 | AquaSnap | [Current link](https://www.nurgo-software.com/products/aquasnap) | Download route not established from retrieved page | Windows 11 not established · [evidence](https://www.nurgo-software.com/products/aquasnap) | Verify support / run smoke test |
| 16 | Armagetron Advanced | [Current link](https://www.armagetronad.org/) | Download/release navigation detected | Windows 11 not established · [evidence](https://www.armagetronad.org/) | Verify support / run smoke test |
| 17 | Artha | [Current link](https://artha.sourceforge.net/wiki/index.php/Home) | Download/release navigation detected | Windows 11 not established · [evidence](https://artha.sourceforge.net/wiki/index.php/Home) | Verify support / run smoke test |
| 18 | AssaultCube | [Current link](https://assault.cubers.net/) | Binary/archive link detected; payload untested | Windows 11 not established · [evidence](https://assault.cubers.net/) | Verify support / run smoke test |
| 19 | Atomic Tanks | [Current link](http://atanks.sourceforge.net/) | Download/release navigation detected | Packager lists Windows 11 · [evidence](https://portableapps.com/apps/games/atomic_tanks_portable) | Verify selected binary / smoke test |
| 20 | Attribute Changer | [Current link](https://www.petges.lu/download/) | Binary/archive link detected; payload untested | Publisher lists Windows 11 · [evidence](https://www.petges.lu/download/) | Verify selected binary / smoke test |
| 21 | Audacious | [Current link](https://audacious-media-player.org/) | Download/release navigation detected | Windows 11 not established · [evidence](https://audacious-media-player.org/) | Verify support / run smoke test |
| 22 | Audacity | [Current link](https://www.audacityteam.org/) | Binary/archive link detected; payload untested | Publisher lists Windows 11 · [evidence](https://www.audacityteam.org/download/windows) | Verify selected binary / smoke test |
| 23 | AutoDrum | [Current link](http://openmidiproject.opal.ne.jp/AutoDrum_en.html) | Download route not established from retrieved page | Publisher lists Windows 11 · [evidence](http://openmidiproject.opal.ne.jp/AutoDrum_en.html) | Verify selected binary / smoke test |
| 24 | AutoHotkey | [Current link](https://www.autohotkey.com/) | Blocked/error: HTTP 403 | Windows 11 not established · [evidence](https://www.autohotkey.com/) | Verify support / run smoke test |
| 25 | Autoruns | [Current link](https://learn.microsoft.com/en-us/sysinternals/downloads/autoruns) | Binary/archive link detected; payload untested | Windows 11 not established · [evidence](https://learn.microsoft.com/en-us/sysinternals/downloads/autoruns) | Verify support / run smoke test |
| 26 | Avidemux | [Current link](https://avidemux.org/download) | Binary/archive link detected; payload untested | Windows 11 not established · [evidence](https://avidemux.org/download) | Verify support / run smoke test |
| 27 | BabelMap | [Current link](https://www.babelstone.co.uk/Software/BabelMap.html) | Binary/archive link detected; payload untested | Publisher lists Windows 11 · [evidence](https://www.babelstone.co.uk/Software/BabelMap.html) | Verify selected binary / smoke test |
| 28 | BabelPad | [Current link](http://babelstone.co.uk/Software/BabelPad.html) | Binary/archive link detected; payload untested | Publisher lists Windows 11 · [evidence](http://babelstone.co.uk/Software/BabelPad.html) | Verify selected binary / smoke test |
| 29 | Balabolka | [Current link](https://www.cross-plus-a.com/balabolka.htm) | Binary/archive link detected; payload untested | Windows 11 not established · [evidence](https://www.cross-plus-a.com/balabolka.htm) | Verify support / run smoke test |
| 30 | Battle for Wesnoth | [Current link](https://www.wesnoth.org/downloads) | Download route not established from retrieved page | Windows 11 not established · [evidence](https://www.wesnoth.org/downloads) | Verify support / run smoke test |
| 31 | Beret | [Current link](https://portableapps.com/node/61768) | Binary/archive link detected; payload untested | Packager lists Windows 11 · [evidence](https://portableapps.com/node/61768) | Verify selected binary / smoke test |
| 32 | Betterbird | [Current link](https://www.betterbird.eu/) | Download/release navigation detected | Windows 11 not established · [evidence](https://www.betterbird.eu/) | Verify support / run smoke test |
| 33 | Big Solitaires 3D | [Current link](http://big3dsol.sourceforge.net/index.html) | Download/release navigation detected | Windows 11 not established · [evidence](http://big3dsol.sourceforge.net/index.html) | Verify support / run smoke test |
| 34 | Bitwarden Desktop | [Current link](https://bitwarden.com/download/) | Download/release navigation detected | Windows 11 not established · [evidence](https://bitwarden.com/download/) | Verify support / run smoke test |
| 35 | Blank And Secure | [Current link](https://www.softwareok.com) | Generic vendor/directory destination | Windows 11 not established · [evidence](https://www.softwareok.com) | Verify support / run smoke test |
| 36 | BleachBit | [Current link](https://www.bleachbit.org) | Download/release navigation detected | Publisher lists Windows 11 · [evidence](https://www.bleachbit.org/download) | Verify selected binary / smoke test |
| 37 | Blender | [Current link](https://www.blender.org) | Download/release navigation detected | Publisher lists Windows 11 · [evidence](https://www.blender.org/download/) | Verify selected binary / smoke test |
| 38 | BOINC | [Current link](https://boinc.berkeley.edu/) | Download/release navigation detected | Windows 11 not established · [evidence](https://boinc.berkeley.edu/) | Verify support / run smoke test |
| 39 | Brain Workshop | [Current link](https://brainworkshop.sourceforge.net/) | Download/release navigation detected | Windows 11 not established · [evidence](https://brainworkshop.sourceforge.net/) | Verify support / run smoke test |
| 40 | BriskPlayer | [Current link](https://github.com/briskplayer/briskplayer) | Source repository; inspect release assets | Windows 11 not established · [evidence](https://github.com/briskplayer/briskplayer) | Verify support / run smoke test |
| 41 | Brutal Chess | [Current link](https://portableapps.com/apps/games/brutal_chess_portable) | Binary/archive link detected; payload untested | Packager lists Windows 11 · [evidence](https://portableapps.com/apps/games/brutal_chess_portable) | Verify selected binary / smoke test |
| 42 | BYOND | [Current link](https://www.byond.com) | Blocked/error: HTTP 403 | Windows 11 not established · [evidence](https://www.byond.com) | Verify support / run smoke test |
| 43 | Caesium | [Current link](https://saerasoft.com/caesium) | Binary/archive link detected; payload untested | Windows 11 not established · [evidence](https://saerasoft.com/caesium) | Verify support / run smoke test |
| 44 | calibre | [Current link](https://calibre-ebook.com/) | Download/release navigation detected | Windows 11 not established · [evidence](https://calibre-ebook.com/) | Verify support / run smoke test |
| 45 | Canabalt | [Current link](https://canabalt.com/) | Download route not established from retrieved page | Windows 11 not established · [evidence](https://canabalt.com/) | Verify support / run smoke test |
| 46 | Capture2Text | [Current link](https://capture2text.sourceforge.net/) | Download/release navigation detected | Windows 11 not established · [evidence](https://capture2text.sourceforge.net/) | Verify support / run smoke test |
| 47 | cdrtfe | [Current link](https://portableapps.com/apps/music_video/cdrtfe_portable) | Binary/archive link detected; payload untested | Packager lists Windows 11 · [evidence](https://portableapps.com/apps/music_video/cdrtfe_portable) | Verify selected binary / smoke test |
| 48 | Celestia | [Current link](https://celestiaproject.space/) | Download route not established from retrieved page | Windows 11 not established · [evidence](https://celestiaproject.space/) | F05 |
| 49 | Checksum Control | [Current link](https://portableapps.com/news/2016-05-19--checksum-control-portable-2.4.1-released) | Old release announcement | Packager lists Windows 11 · [evidence](https://portableapps.com/download) | Verify selected binary / smoke test |
| 50 | Cherrytree | [Current link](https://www.giuspen.net/cherrytree/) | Binary/archive link detected; payload untested | Windows 11 not established · [evidence](https://www.giuspen.net/cherrytree/) | Verify support / run smoke test |
| 51 | Chromium | [Current link](https://www.chromium.org) | Download route not established from retrieved page | Windows 11 not established · [evidence](https://www.chromium.org) | F24 |
| 52 | Chromium B.S.U. | [Current link](https://portableapps.com/node/61772) | Binary/archive link detected; payload untested | Packager lists Windows 11 · [evidence](https://portableapps.com/node/61772) | Verify selected binary / smoke test |
| 53 | ClamWin | [Current link](http://www.clamwin.com) | Download/release navigation detected | Windows 11 not established · [evidence](http://www.clamwin.com) | Verify support / run smoke test |
| 54 | Clicky Gone | [Current link](https://portableapps.com/apps/utilities/clicky-gone-portable) | Binary/archive link detected; payload untested | Packager lists Windows 11 · [evidence](https://portableapps.com/apps/utilities/clicky-gone-portable) | Verify selected binary / smoke test |
| 55 | Colour Contrast Analyser | [Current link](https://www.tpgi.com/color-contrast-checker/) | Binary/archive link detected; payload untested | Windows 11 not established · [evidence](https://www.tpgi.com/color-contrast-checker/) | F08 |
| 56 | Converber | [Current link](http://www.xyntec.com/unit-converter-download.htm) | Unavailable: HTTP 404 | Packager lists Windows 11 · [evidence](https://portableapps.com/apps/utilities/converber_portable) | F30 |
| 57 | ConvertAll | [Current link](http://bellz.org/ConvertAll-py/index.html) | Download/release navigation detected | Windows 11 not established · [evidence](http://bellz.org/ConvertAll-py/index.html) | Verify support / run smoke test |
| 58 | Cook Timer | [Current link](https://portableapps.com/apps/utilities/cook_timer_portable) | Binary/archive link detected; payload untested | Packager lists Windows 11 · [evidence](https://portableapps.com/apps/utilities/cook_timer_portable) | Verify selected binary / smoke test |
| 59 | CopyQ | [Current link](https://hluk.github.io/CopyQ/) | Download/release navigation detected | Windows 11 not established · [evidence](https://hluk.github.io/CopyQ/) | F07 |
| 60 | Coreinfo | [Current link](https://learn.microsoft.com/en-us/sysinternals/downloads/coreinfo) | Binary/archive link detected; payload untested | Publisher lists Windows 11 · [evidence](https://learn.microsoft.com/en-us/sysinternals/downloads/coreinfo) | Verify selected binary / smoke test |
| 61 | Cppcheck | [Current link](https://github.com/cppcheck-opensource/cppcheck/releases) | Download/release navigation detected | Windows 11 not established · [evidence](https://github.com/cppcheck-opensource/cppcheck/releases) | Verify support / run smoke test |
| 62 | CPU-Z | [Current link](https://www.cpuid.com/softwares/cpu-z.html) | Binary/archive link detected; payload untested | Windows 11 not established · [evidence](https://www.cpuid.com/softwares/cpu-z.html) | Verify support / run smoke test |
| 63 | CpuFrequenz | [Current link](http://www.softwareok.com/?seite=Microsoft/CpuFrequenz) | Download/release navigation detected | Publisher lists Windows 11 · [evidence](http://www.softwareok.com/?seite=Microsoft/CpuFrequenz) | Verify selected binary / smoke test |
| 64 | Cryptomator | [Current link](https://cryptomator.org/) | Download/release navigation detected | Windows 11 not established · [evidence](https://cryptomator.org/) | Verify support / run smoke test |
| 65 | CrystalDiskInfo | [Current link](https://crystalmark.info/) | Download/release navigation detected | Windows 11 not established · [evidence](https://crystalmark.info/) | Verify support / run smoke test |
| 66 | CrystalDiskMark | [Current link](https://crystalmark.info/en/) | Download/release navigation detected | Windows 11 not established · [evidence](https://crystalmark.info/en/) | Verify support / run smoke test |
| 67 | CrystalMark Retro | [Current link](https://crystalmark.info/en/software/crystalmarkretro/) | Download/release navigation detected | Packager lists Windows 11 · [evidence](https://portableapps.com/apps/utilities/crystalmark-retro-portable) | Verify selected binary / smoke test |
| 68 | Cube | [Current link](https://cubeengine.com/) | Blocked/error: HTTP 502 | Windows 11 not established · [evidence](https://cubeengine.com/) | Verify support / run smoke test |
| 69 | Daphne | [Current link](https://www.drk.com.ar/en/legacy/daphne-windows-task-manager-replacement/) | Binary/archive link detected; payload untested | Windows 11 not established · [evidence](https://www.drk.com.ar/en/legacy/daphne-windows-task-manager-replacement/) | Verify support / run smoke test |
| 70 | darktable | [Current link](https://www.darktable.org/) | Download route not established from retrieved page | Windows 11 not established · [evidence](https://www.darktable.org/) | Verify support / run smoke test |
| 71 | Database Browser | [Current link](https://www.etl-tools.com/products/database-browser.html) | Download/release navigation detected | Windows 11 not established · [evidence](https://www.etl-tools.com/products/database-browser.html) | Verify support / run smoke test |
| 72 | Dave Gnukem | [Current link](http://djoffe.com/gnukem/) | Binary/archive link detected; payload untested | Windows 11 not established · [evidence](http://djoffe.com/gnukem/) | Verify support / run smoke test |
| 73 | DaVinci Resolve | [Current link](https://www.blackmagicdesign.com) | Generic vendor/directory destination | Windows 11 not established · [evidence](https://www.blackmagicdesign.com) | F16 |
| 74 | DB Browser for SQLite | [Current link](https://sqlitebrowser.org/) | Download/release navigation detected | Windows 11 not established · [evidence](https://sqlitebrowser.org/) | Verify support / run smoke test |
| 75 | DebugView | [Current link](https://learn.microsoft.com/en-us/sysinternals/downloads/debugview) | Binary/archive link detected; payload untested | Publisher lists Windows 11 · [evidence](https://learn.microsoft.com/en-us/sysinternals/downloads/debugview) | Verify selected binary / smoke test |
| 76 | Delta Chat Desktop | [Current link](https://delta.chat) | Download route not established from retrieved page | Windows 11 not established · [evidence](https://delta.chat) | Verify support / run smoke test |
| 77 | DesktopSnowOK | [Current link](http://www.softwareok.com/?Download=DesktopSnowOK) | Binary/archive link detected; payload untested | Publisher lists Windows 11 · [evidence](http://www.softwareok.com/?Download=DesktopSnowOK) | Verify selected binary / smoke test |
| 78 | Detect It Easy | [Current link](https://github.com/horsicq/Detect-It-Easy) | Source repository; inspect release assets | Windows 11 not established · [evidence](https://github.com/horsicq/Detect-It-Easy) | Verify support / run smoke test |
| 79 | Dia | [Current link](https://wiki.gnome.org/Apps/Dia) | Download/release navigation detected | Windows 11 not established · [evidence](https://wiki.gnome.org/Apps/Dia) | Verify support / run smoke test |
| 80 | Dicom | [Current link](https://portableapps.com/node/59248) | Binary/archive link detected; payload untested | Packager lists Windows 11 · [evidence](https://portableapps.com/node/59248) | Verify selected binary / smoke test |
| 81 | DiffImg | [Current link](https://portableapps.com/news/2014-09-11--diffimg-portable-2.2.0-released) | Old release announcement | Packager lists Windows 11 · [evidence](https://portableapps.com/download) | Verify selected binary / smoke test |
| 82 | Diffpdf | [Current link](https://www.qtrac.eu/diffpdf.html) | Blocked/error: HTTP 502 | Windows 11 not established · [evidence](https://www.qtrac.eu/diffpdf.html) | Verify support / run smoke test |
| 83 | digiKam | [Current link](https://www.digikam.org/) | Download/release navigation detected | Windows 11 not established · [evidence](https://www.digikam.org/) | Verify support / run smoke test |
| 84 | Disk Cleaner | [Current link](https://diskcleaner.nl/) | Blocked/error: HTTP 502 | Windows 11 not established · [evidence](https://diskcleaner.nl/) | Verify support / run smoke test |
| 85 | DiskMon | [Current link](https://docs.microsoft.com/en-us/sysinternals/downloads/diskmon) | Binary/archive link detected; payload untested | Windows 11 not established · [evidence](https://docs.microsoft.com/en-us/sysinternals/downloads/diskmon) | Verify support / run smoke test |
| 86 | Ditto | [Current link](https://github.com/sabrogden/Ditto/releases) | Download/release navigation detected | Packager lists Windows 11 · [evidence](https://portableapps.com/apps/utilities/ditto_portable) | Verify selected binary / smoke test |
| 87 | DM2 | [Current link](https://github.com/igr/dm2/releases) | Download/release navigation detected | Windows 11 not established · [evidence](https://github.com/igr/dm2/releases) | Verify support / run smoke test |
| 88 | Dolphin | [Current link](https://dolphin-emu.org/) | Blocked/error: HTTP 403 | Windows 11 not established · [evidence](https://dolphin-emu.org/) | Verify support / run smoke test |
| 89 | Domino-Chain | [Current link](https://domino-chain.gitlab.io/) | Binary/archive link detected; payload untested | Windows 11 not established · [evidence](https://domino-chain.gitlab.io/) | Verify support / run smoke test |
| 90 | Don't Panic! | [Current link](https://portableapps.com/apps/utilities/dont_panic_portable) | Binary/archive link detected; payload untested | Packager lists Windows 11 · [evidence](https://portableapps.com/apps/utilities/dont_panic_portable) | Verify selected binary / smoke test |
| 91 | Don't Sleep | [Current link](https://www.softwareok.com/?Download=DontSleep) | Binary/archive link detected; payload untested | Publisher lists Windows 11 · [evidence](https://www.softwareok.com/?Download=DontSleep) | Verify selected binary / smoke test |
| 92 | DOSBox | [Current link](https://www.dosbox.com/) | Blocked/error: HTTP 403 | Windows 11 not established · [evidence](https://www.dosbox.com/) | Verify support / run smoke test |
| 93 | Draw.io | [Current link](https://app.diagrams.net/) | Web/source destination | Web destination; native route needs correction · [evidence](https://app.diagrams.net/) | F09 |
| 94 | DSpeech | [Current link](http://dimio.altervista.org/eng/) | Binary/archive link detected; payload untested | Windows 11 not established · [evidence](http://dimio.altervista.org/eng/) | Verify support / run smoke test |
| 95 | DSynchronize | [Current link](https://dimio.altervista.org/eng/) | Blocked/error: HTTP 502 | Windows 11 not established · [evidence](https://dimio.altervista.org/eng/) | Verify support / run smoke test |
| 96 | DTaskManager | [Current link](http://dimio.altervista.org/eng/) | Binary/archive link detected; payload untested | Packager lists Windows 11 · [evidence](https://portableapps.com/apps/utilities/dtaskmanager_portable) | Verify selected binary / smoke test |
| 97 | Duplicate Files Finder | [Current link](https://www.mindgems.com/products/Duplicate-Files-Finder/Duplicate-Files-Finder-Download.htm) | Unavailable: HTTP 404 | Windows 11 not established · [evidence](https://www.mindgems.com/products/Duplicate-Files-Finder/Duplicate-Files-Finder-Download.htm) | F33 |
| 98 | Duplicati | [Current link](https://duplicati.com/download) | Binary/archive link detected; payload untested | Windows 11 not established · [evidence](https://duplicati.com/download) | Verify support / run smoke test |
| 99 | DVDStyler | [Current link](https://www.dvdstyler.org/) | Download/release navigation detected | Windows 11 not established · [evidence](https://www.dvdstyler.org/) | Verify support / run smoke test |
| 100 | EarTrumpet | [Current link](https://eartrumpet.app) | Download route not established from retrieved page | Publisher lists Windows 11 · [evidence](https://github.com/File-New-Project/EarTrumpet) | Verify selected binary / smoke test |
| 101 | Ekiga | [Current link](https://www.ekiga.org/) | Binary/archive link detected; payload untested | Windows 11 not established · [evidence](https://www.ekiga.org/) | Verify support / run smoke test |
| 102 | Element Desktop | [Current link](https://element.io) | Download/release navigation detected | Windows 11 not established · [evidence](https://element.io) | Verify support / run smoke test |
| 103 | Emsisoft Emergency Kit | [Current link](https://www.emsisoft.com/en/emergency-kit/) | Download/release navigation detected | Windows 11 not established · [evidence](https://www.emsisoft.com/en/emergency-kit/) | Verify support / run smoke test |
| 104 | Eraser .Net | [Current link](https://eraser.heidi.ie) | Blocked/error: HTTP 403 | Windows 11 not established · [evidence](https://eraser.heidi.ie) | F27 |
| 105 | Eraser Classic | [Current link](https://eraser.heidi.ie) | Blocked/error: HTTP 403 | Windows 11 not established · [evidence](https://eraser.heidi.ie) | F27 |
| 106 | EraserDrop | [Current link](https://portableapps.com/apps/security/eraserdrop-portable) | Binary/archive link detected; payload untested | Packager lists Windows 11 · [evidence](https://portableapps.com/apps/security/eraserdrop-portable) | Verify selected binary / smoke test |
| 107 | Espanso | [Current link](https://github.com/espanso/espanso) | Source repository; inspect release assets | Windows 11 not established · [evidence](https://github.com/espanso/espanso) | Verify support / run smoke test |
| 108 | Everything | [Current link](https://www.voidtools.com/downloads/) | Binary/archive link detected; payload untested | Windows 11 not established · [evidence](https://www.voidtools.com/downloads/) | Verify support / run smoke test |
| 109 | ExifToolGUI | [Current link](https://github.com/FrankBijnen/ExifToolGui) | Source repository; inspect release assets | Windows 11 not established · [evidence](https://github.com/FrankBijnen/ExifToolGui) | Verify support / run smoke test |
| 110 | Explorer++ | [Current link](https://www.explorerplusplus.com/download) | Binary/archive link detected; payload untested | Windows 11 not established · [evidence](https://www.explorerplusplus.com/download) | Verify support / run smoke test |
| 111 | Falkon | [Current link](https://www.falkon.org) | Download/release navigation detected | Windows 11 not established · [evidence](https://www.falkon.org) | Verify support / run smoke test |
| 112 | FanControl | [Current link](https://github.com/Rem0o/FanControl.Releases) | Source repository; inspect release assets | Publisher lists Windows 11 · [evidence](https://github.com/Rem0o/FanControl.Releases) | Verify selected binary / smoke test |
| 113 | FastCopy | [Current link](https://fastcopy.jp/) | Binary/archive link detected; payload untested | Windows 11 not established · [evidence](https://fastcopy.jp/) | Verify support / run smoke test |
| 114 | FastStone Image Viewer | [Current link](https://www.faststone.org/) | Download/release navigation detected | Windows 11 not established · [evidence](https://www.faststone.org/) | Verify support / run smoke test |
| 115 | FeedRoller | [Current link](https://portableapps.com/apps/internet/feedroller-portable) | Binary/archive link detected; payload untested | Packager lists Windows 11 · [evidence](https://portableapps.com/apps/internet/feedroller-portable) | Verify selected binary / smoke test |
| 116 | Ferdium | [Current link](https://ferdium.org/) | Download/release navigation detected | Windows 11 not established · [evidence](https://ferdium.org/) | Verify support / run smoke test |
| 117 | File Converter | [Current link](https://file-converter.io) | Binary/archive link detected; payload untested | Publisher lists Windows 11 · [evidence](https://file-converter.io) | Verify selected binary / smoke test |
| 118 | FileAlyzer | [Current link](https://www.safer-networking.org/products/filealyzer/download/) | Binary/archive link detected; payload untested | Windows 11 not established · [evidence](https://www.safer-networking.org/products/filealyzer/download/) | Verify support / run smoke test |
| 119 | FileOptimizer | [Current link](https://portableapps.com/node/64805) | Binary/archive link detected; payload untested | Packager lists Windows 11 · [evidence](https://portableapps.com/node/64805) | Verify selected binary / smoke test |
| 120 | FileVoyager | [Current link](https://www.filevoyager.com/) | Download/release navigation detected | Windows 11 not established · [evidence](https://www.filevoyager.com/) | Verify support / run smoke test |
| 121 | FileZilla | [Current link](https://filezilla-project.org) | Blocked/error: <urlopen error timed out> | Windows 11 not established · [evidence](https://filezilla-project.org) | Verify support / run smoke test |
| 122 | Finance Explorer | [Current link](https://portableapps.com/news/2018-11-21--finance-explorer-portable-8.2.0-released) | Old release announcement | Packager lists Windows 11 · [evidence](https://portableapps.com/download) | Verify selected binary / smoke test |
| 123 | Flow Launcher | [Current link](https://flowlauncher.com) | Binary/archive link detected; payload untested | Windows 11 not established · [evidence](https://flowlauncher.com) | Verify support / run smoke test |
| 124 | FocusWriter | [Current link](https://gottcode.org/focuswriter/) | Download/release navigation detected | Windows 11 not established · [evidence](https://gottcode.org/focuswriter/) | Verify support / run smoke test |
| 125 | Folding@home | [Current link](https://foldingathome.org) | Download/release navigation detected | Windows 11 not established · [evidence](https://foldingathome.org) | Verify support / run smoke test |
| 126 | FontForge | [Current link](https://fontforge.org/en-US/downloads/windows/) | Download/release navigation detected | Windows 11 not established · [evidence](https://fontforge.org/en-US/downloads/windows/) | Verify support / run smoke test |
| 127 | FontViewOK | [Current link](https://www.softwareok.com/?Download=FontViewOK) | Binary/archive link detected; payload untested | Publisher lists Windows 11 · [evidence](https://www.softwareok.com/?Download=FontViewOK) | Verify selected binary / smoke test |
| 128 | foobar2000 | [Current link](https://www.foobar2000.org/) | Download/release navigation detected | Windows 11 not established · [evidence](https://www.foobar2000.org/) | Verify support / run smoke test |
| 129 | Fotografix | [Current link](https://www.lmadhavan.com/fotografix/) | Download/release navigation detected | Publisher lists Windows 11 · [evidence](https://www.lmadhavan.com/fotografix/) | Verify selected binary / smoke test |
| 130 | FotoSketcher | [Current link](https://www.fotosketcher.com/) | Download/release navigation detected | Windows 11 not established · [evidence](https://www.fotosketcher.com/) | Verify support / run smoke test |
| 131 | fre:ac | [Current link](https://www.freac.org/) | Download/release navigation detected | Windows 11 not established · [evidence](https://www.freac.org/) | F34 |
| 132 | Free Download Manager | [Current link](https://www.freedownloadmanager.org) | Binary/archive link detected; payload untested | Publisher lists Windows 11 · [evidence](https://www.freedownloadmanager.org) | Verify selected binary / smoke test |
| 133 | FreeCAD | [Current link](https://www.freecad.org/downloads.php) | Binary/archive link detected; payload untested | Windows 11 not established · [evidence](https://www.freecad.org/downloads.php) | Verify support / run smoke test |
| 134 | Freeciv | [Current link](https://www.freeciv.org/) | Download/release navigation detected | Windows 11 not established · [evidence](https://www.freeciv.org/) | Verify support / run smoke test |
| 135 | FreeCommander | [Current link](https://freecommander.com/en/downloads/) | Binary/archive link detected; payload untested | Windows 11 not established · [evidence](https://freecommander.com/en/downloads/) | Verify support / run smoke test |
| 136 | FreeFileSync | [Current link](https://freefilesync.org/download.php) | Binary/archive link detected; payload untested | Windows 11 not established · [evidence](https://freefilesync.org/download.php) | Verify support / run smoke test |
| 137 | Frhed | [Current link](https://portableapps.com/apps/development/frhed_portable) | Binary/archive link detected; payload untested | Packager lists Windows 11 · [evidence](https://portableapps.com/apps/development/frhed_portable) | Verify selected binary / smoke test |
| 138 | FUPX | [Current link](https://gurupia.wordpress.com/fupx/) | Blocked/error: <urlopen error timed out> | Packager lists Windows 11 · [evidence](https://portableapps.com/apps/utilities/free_upx_portable) | F31 |
| 139 | Geany | [Current link](https://www.geany.org/download/releases/) | Binary/archive link detected; payload untested | Windows 11 not established · [evidence](https://www.geany.org/download/releases/) | Verify support / run smoke test |
| 140 | GeekUninstaller | [Current link](https://geekuninstaller.com/) | Download/release navigation detected | Windows 11 not established · [evidence](https://geekuninstaller.com/) | Verify support / run smoke test |
| 141 | Get Sudoku | [Current link](https://portableapps.com/node/43374) | Download/release navigation detected | Packager lists Windows 11 · [evidence](https://portableapps.com/download) | Verify selected binary / smoke test |
| 142 | GIMP | [Current link](https://www.gimp.org/) | Download/release navigation detected | Windows 11 not established · [evidence](https://www.gimp.org/) | Verify support / run smoke test |
| 143 | gMKVExtractGUI | [Current link](https://github.com/Gpower2/gMKVExtractGUI) | Source repository; inspect release assets | Windows 11 not established · [evidence](https://github.com/Gpower2/gMKVExtractGUI) | Verify support / run smoke test |
| 144 | GnuCash | [Current link](http://www.gnucash.org) | Binary/archive link detected; payload untested | Publisher lists Windows 11 · [evidence](http://www.gnucash.org) | Verify selected binary / smoke test |
| 145 | GoldenDict | [Current link](http://goldendict.org/) | Download/release navigation detected | Windows 11 not established · [evidence](http://goldendict.org/) | Verify support / run smoke test |
| 146 | Golly | [Current link](https://portableapps.com/apps/games/golly-portable) | Binary/archive link detected; payload untested | Packager lists Windows 11 · [evidence](https://portableapps.com/apps/games/golly-portable) | Verify selected binary / smoke test |
| 147 | Google Chrome | [Current link](https://www.google.com/chrome/) | Download/release navigation detected | Windows 11 not established · [evidence](https://www.google.com/chrome/) | Verify support / run smoke test |
| 148 | Gopherus | [Current link](https://portableapps.com/news/2023-02-14--gopherus-portable-1.2.2-released) | Old release announcement | Packager lists Windows 11 · [evidence](https://portableapps.com/download) | Verify selected binary / smoke test |
| 149 | GPG Plugin | [Current link](https://portableapps.com/apps/security/gpg-plugin-portable) | Binary/archive link detected; payload untested | Packager lists Windows 11 · [evidence](https://portableapps.com/apps/security/gpg-plugin-portable) | Verify selected binary / smoke test |
| 150 | gPodder | [Current link](https://gpodder.github.io/) | Binary/archive link detected; payload untested | Windows 11 not established · [evidence](https://gpodder.github.io/) | Verify support / run smoke test |
| 151 | GPU-Z | [Current link](https://www.techpowerup.com/download/techpowerup-gpu-z/) | Download/release navigation detected | Windows 11 not established · [evidence](https://www.techpowerup.com/download/techpowerup-gpu-z/) | Verify support / run smoke test |
| 152 | Gramps | [Current link](https://gramps-project.org) | Download route not established from retrieved page | Windows 11 not established · [evidence](https://gramps-project.org) | Verify support / run smoke test |
| 153 | Greenfish Icon Editor Pro | [Current link](http://greenfishsoftware.org/gfie.php) | Binary/archive link detected; payload untested | Windows 11 not established · [evidence](http://greenfishsoftware.org/gfie.php) | Verify support / run smoke test |
| 154 | Greenshot | [Current link](https://getgreenshot.org) | Download/release navigation detected | Windows 11 not established · [evidence](https://getgreenshot.org) | Verify support / run smoke test |
| 155 | grepWin | [Current link](https://tools.stefankueng.com/grepWin.html) | Download/release navigation detected | Windows 11 not established · [evidence](https://tools.stefankueng.com/grepWin.html) | Verify support / run smoke test |
| 156 | Gridy | [Current link](https://portableapps.com/apps/utilities/gridy-portable) | Binary/archive link detected; payload untested | Packager lists Windows 11 · [evidence](https://portableapps.com/apps/utilities/gridy-portable) | Verify selected binary / smoke test |
| 157 | gVim | [Current link](https://www.vim.org/download.php) | Binary/archive link detected; payload untested | Windows 11 not established · [evidence](https://www.vim.org/download.php) | Verify support / run smoke test |
| 158 | HandBrake | [Current link](https://handbrake.fr/) | Download/release navigation detected | Windows 11 not established · [evidence](https://handbrake.fr/) | Verify support / run smoke test |
| 159 | HDHacker | [Current link](http://dimio.altervista.org/eng/) | Binary/archive link detected; payload untested | Windows 11 not established · [evidence](http://dimio.altervista.org/eng/) | Verify support / run smoke test |
| 160 | Hedgewars | [Current link](https://hedgewars.org/) | Download/release navigation detected | Windows 11 not established · [evidence](https://hedgewars.org/) | Verify support / run smoke test |
| 161 | Heroic Games Launcher | [Current link](https://heroicgameslauncher.com/) | Binary/archive link detected; payload untested | Publisher lists Windows 11 · [evidence](https://heroicgameslauncher.com/downloads) | Verify selected binary / smoke test |
| 162 | Hex-a-Hop | [Current link](https://portableapps.com/apps/games/hex-a-hop_portable) | Binary/archive link detected; payload untested | Packager lists Windows 11 · [evidence](https://portableapps.com/apps/games/hex-a-hop_portable) | Verify selected binary / smoke test |
| 163 | HexChat | [Current link](https://github.com/hexchat/hexchat) | Source repository; inspect release assets | Windows 11 not established · [evidence](https://github.com/hexchat/hexchat) | F25 |
| 164 | HijackThis | [Current link](https://github.com/dragokas/hijackthis) | Source repository; inspect release assets | Windows 11 not established · [evidence](https://github.com/dragokas/hijackthis) | Verify support / run smoke test |
| 165 | HomeBank | [Current link](https://www.gethomebank.org) | Download/release navigation detected | Publisher lists Windows 11 · [evidence](https://www.gethomebank.org/en/downloads.php) | Verify selected binary / smoke test |
| 166 | HWiNFO | [Current link](https://www.hwinfo.com) | Download/release navigation detected | Windows 11 not established · [evidence](https://www.hwinfo.com) | Verify support / run smoke test |
| 167 | HWMonitor | [Current link](https://www.cpuid.com/softwares/hwmonitor.html) | Binary/archive link detected; payload untested | Windows 11 not established · [evidence](https://www.cpuid.com/softwares/hwmonitor.html) | Verify support / run smoke test |
| 168 | I Have No Tomatoes | [Current link](https://portableapps.com/node/64119) | Binary/archive link detected; payload untested | Packager lists Windows 11 · [evidence](https://portableapps.com/node/64119) | Verify selected binary / smoke test |
| 169 | IceBreaker | [Current link](https://portableapps.com/apps/games/icebreaker_portable) | Binary/archive link detected; payload untested | Packager lists Windows 11 · [evidence](https://portableapps.com/apps/games/icebreaker_portable) | Verify selected binary / smoke test |
| 170 | IDPhotoStudio | [Current link](https://kcsoftwares.com/download.php?avt) | Binary/archive link detected; payload untested | Packager lists Windows 11 · [evidence](https://portableapps.com/apps/graphics_pictures/idphotostudio-portable) | F38 |
| 171 | ImageGlass | [Current link](https://imageglass.org/) | Blocked/error: HTTP 403 | Windows 11 not established · [evidence](https://imageglass.org/) | Verify support / run smoke test |
| 172 | IniTranslator | [Current link](https://portableapps.com/apps/development/initranslator-portable) | Binary/archive link detected; payload untested | Packager lists Windows 11 · [evidence](https://portableapps.com/apps/development/initranslator-portable) | Verify selected binary / smoke test |
| 173 | Inkscape | [Current link](https://inkscape.org) | Blocked/error: The read operation timed out | Windows 11 not established · [evidence](https://inkscape.org) | Verify support / run smoke test |
| 174 | InnoUnpacker | [Current link](https://www.rathlev-home.de/index-e.html?tools/prog-e.html#unpack) | Download route not established from retrieved page | Windows 11 not established · [evidence](https://www.rathlev-home.de/index-e.html?tools/prog-e.html#unpack) | Verify support / run smoke test |
| 175 | IrfanView | [Current link](https://www.irfanview.com/) | Download/release navigation detected | Publisher lists Windows 11 · [evidence](https://www.irfanview.com/) | F14 |
| 176 | Iron | [Current link](https://www.srware.net/en/software_srware_iron.php) | Binary/archive link detected; payload untested | Publisher lists Windows 11 · [evidence](https://www.srware.net/en/software_srware_iron.php) | Verify selected binary / smoke test |
| 177 | Isotoxin | [Current link](https://portableapps.com/apps/internet/isotoxin-portable) | Binary/archive link detected; payload untested | Packager lists Windows 11 · [evidence](https://portableapps.com/apps/internet/isotoxin-portable) | Verify selected binary / smoke test |
| 178 | Jooleem | [Current link](https://portableapps.com/apps/games/jooleem_portable) | Binary/archive link detected; payload untested | Packager lists Windows 11 · [evidence](https://portableapps.com/apps/games/jooleem_portable) | Verify selected binary / smoke test |
| 179 | Joplin | [Current link](https://joplinapp.org) | Download/release navigation detected | Windows 11 not established · [evidence](https://joplinapp.org) | Verify support / run smoke test |
| 180 | JPEGView | [Current link](https://github.com/sylikc/jpegview) | Source repository; inspect release assets | Publisher lists Windows 11 · [evidence](https://github.com/sylikc/jpegview) | F34 |
| 181 | K-Meleon | [Current link](http://kmeleonbrowser.org) | Download/release navigation detected | Windows 11 not established · [evidence](http://kmeleonbrowser.org) | Verify support / run smoke test |
| 182 | Kanri | [Current link](https://kanriapp.com/download) | Binary/archive link detected; payload untested | Windows 11 not established · [evidence](https://kanriapp.com/download) | Verify support / run smoke test |
| 183 | KchmViewer | [Current link](https://github.com/eBookProjects/uChmViewer) | Source repository; inspect release assets | Windows 11 not established · [evidence](https://github.com/eBookProjects/uChmViewer) | Verify support / run smoke test |
| 184 | Kdenlive | [Current link](https://kdenlive.org/) | Download/release navigation detected | Windows 11 not established · [evidence](https://kdenlive.org/) | Verify support / run smoke test |
| 185 | KeePass Classic | [Current link](https://keepass.info) | Download/release navigation detected | Publisher lists Windows 11 · [evidence](https://keepass.info/download.html) | Verify selected binary / smoke test |
| 186 | KeePass Professional | [Current link](https://keepass.info) | Download/release navigation detected | Publisher lists Windows 11 · [evidence](https://keepass.info/download.html) | Verify selected binary / smoke test |
| 187 | KeePassXC | [Current link](https://keepassxc.org) | Download/release navigation detected | Publisher lists Windows 11 · [evidence](https://keepassxc.org/download/) | Verify selected binary / smoke test |
| 188 | KiCad | [Current link](https://www.kicad.org/download/) | Download/release navigation detected | Publisher lists Windows 11 · [evidence](https://www.kicad.org/download/windows/) | Verify selected binary / smoke test |
| 189 | KiTTY | [Current link](https://www.9bis.com/kitty/) | Download route not established from retrieved page | Windows 11 not established · [evidence](https://www.9bis.com/kitty/) | Verify support / run smoke test |
| 190 | Kobo Deluxe | [Current link](http://olofson.net/kobodl/) | Binary/archive link detected; payload untested | Windows 11 not established · [evidence](http://olofson.net/kobodl/) | Verify support / run smoke test |
| 191 | Krita | [Current link](https://krita.org/) | Download route not established from retrieved page | Windows 11 not established · [evidence](https://krita.org/) | F14 |
| 192 | Kudu | [Current link](https://usekudu.com/) | Download/release navigation detected | Publisher lists Windows 11 · [evidence](https://usekudu.com/) | Verify selected binary / smoke test |
| 193 | KVIrc | [Current link](https://kvirc.net/?id=releases&platform=win64&version=5.2.4&lang=) | Binary/archive link detected; payload untested | Windows 11 not established · [evidence](https://kvirc.net/?id=releases&platform=win64&version=5.2.4&lang=) | Verify support / run smoke test |
| 194 | Lagrange | [Current link](https://gmi.skyjake.fi/lagrange) | Download/release navigation detected | Windows 11 not established · [evidence](https://gmi.skyjake.fi/lagrange) | Verify support / run smoke test |
| 195 | LameXP | [Current link](https://lamexp.sourceforge.net/) | Download/release navigation detected | Packager lists Windows 11 · [evidence](https://portableapps.com/apps/music_video/lamexp-portable) | Verify selected binary / smoke test |
| 196 | LAN Messenger | [Current link](https://portableapps.com/node/62011) | Binary/archive link detected; payload untested | Packager lists Windows 11 · [evidence](https://portableapps.com/download) | Verify selected binary / smoke test |
| 197 | LazPaint | [Current link](https://lazpaint.github.io/) | Binary/archive link detected; payload untested | Windows 11 not established · [evidence](https://lazpaint.github.io/) | Verify support / run smoke test |
| 198 | LBreakout2 | [Current link](https://portableapps.com/node/64436) | Binary/archive link detected; payload untested | Packager lists Windows 11 · [evidence](https://portableapps.com/node/64436) | Verify selected binary / smoke test |
| 199 | LibreCAD | [Current link](https://librecad.org/) | Download/release navigation detected | Windows 11 not established · [evidence](https://librecad.org/) | Verify support / run smoke test |
| 200 | LibreOffice | [Current link](https://www.libreoffice.org/download/) | Binary/archive link detected; payload untested | Publisher lists Windows 11 · [evidence](https://www.libreoffice.org/system-requirements/) | Verify selected binary / smoke test |
| 201 | LibreWolf | [Current link](https://librewolf.net) | Download/release navigation detected | Windows 11 not established · [evidence](https://librewolf.net) | Verify support / run smoke test |
| 202 | LICEcap | [Current link](https://www.cockos.com/licecap/) | Binary/archive link detected; payload untested | Windows 11 not established · [evidence](https://www.cockos.com/licecap/) | Verify support / run smoke test |
| 203 | Lightscreen | [Current link](https://lightscreen.com.ar/) | Download/release navigation detected | Windows 11 not established · [evidence](https://lightscreen.com.ar/) | Verify support / run smoke test |
| 204 | Links | [Current link](http://links.twibright.com) | Download/release navigation detected | Windows 11 not established · [evidence](http://links.twibright.com) | Verify support / run smoke test |
| 205 | Listary | [Current link](http://www.listary.com/pro) | Download/release navigation detected | Publisher lists Windows 11 · [evidence](https://www.listary.com/download) | F17 |
| 206 | LMarbles | [Current link](http://portableapps.com/apps/games/lmarbles_portable) | Binary/archive link detected; payload untested | Packager lists Windows 11 · [evidence](http://portableapps.com/apps/games/lmarbles_portable) | Verify selected binary / smoke test |
| 207 | LMMS | [Current link](https://lmms.io/) | Download/release navigation detected | Publisher lists Windows 11 · [evidence](https://lmms.io/download/) | Verify selected binary / smoke test |
| 208 | LocalSend | [Current link](https://localsend.org/download) | Download/release navigation detected | Windows 11 not established · [evidence](https://localsend.org/download) | Verify support / run smoke test |
| 209 | Logseq | [Current link](https://logseq.com) | Download route not established from retrieved page | Windows 11 not established · [evidence](https://logseq.com) | Verify support / run smoke test |
| 210 | Lossless Cut | [Current link](https://losslesscut.net/) | Wrong official-source attribution | Windows 11 not established · [evidence](https://losslesscut.net/) | F03 |
| 211 | Lucas Chess | [Current link](https://lucaschess.pythonanywhere.com/) | Download/release navigation detected | Windows 11 not established · [evidence](https://lucaschess.pythonanywhere.com/) | Verify support / run smoke test |
| 212 | Lynx | [Current link](https://lynx.invisible-island.net) | Download route not established from retrieved page | Windows 11 not established · [evidence](https://lynx.invisible-island.net) | Verify support / run smoke test |
| 213 | MahJongg Solitaire 3D | [Current link](https://www.reto-schoelly.com/downloads) | Binary/archive link detected; payload untested | Packager lists Windows 11 · [evidence](https://portableapps.com/apps/games/mahjongg-solitaire-3d-portable) | Verify selected binary / smoke test |
| 214 | Mana Plus | [Current link](http://manaplus.org/) | Download/release navigation detected | Windows 11 not established · [evidence](http://manaplus.org/) | Verify support / run smoke test |
| 215 | ManiaDrive | [Current link](https://portableapps.com/apps/games/maniadrive-portable) | Binary/archive link detected; payload untested | Packager lists Windows 11 · [evidence](https://portableapps.com/apps/games/maniadrive-portable) | Verify selected binary / smoke test |
| 216 | Marble | [Current link](https://marble.kde.org/) | Download route not established from retrieved page | Windows 11 not established · [evidence](https://marble.kde.org/) | Verify support / run smoke test |
| 217 | Maxthon | [Current link](https://www.maxthon.com) | Download/release navigation detected | Windows 11 not established · [evidence](https://www.maxthon.com) | Verify support / run smoke test |
| 218 | MBox Viewer | [Current link](https://github.com/eneam/mboxviewer/releases) | Download/release navigation detected | Packager lists Windows 11 · [evidence](https://portableapps.com/apps/utilities/mbox-viewer-portable) | Verify selected binary / smoke test |
| 219 | Media Player Classic - BE | [Current link](https://github.com/Aleksoid1978/MPC-BE) | Source repository; inspect release assets | Publisher lists Windows 11 · [evidence](https://github.com/Aleksoid1978/MPC-BE) | Verify selected binary / smoke test |
| 220 | Media Player Classic - HC | [Current link](https://github.com/clsid2/mpc-hc) | Source repository; inspect release assets | Publisher lists Windows 11 · [evidence](https://github.com/clsid2/mpc-hc) | Verify selected binary / smoke test |
| 221 | MediaInfo | [Current link](https://mediaarea.net/en/MediaInfo/Download/Windows) | Binary/archive link detected; payload untested | Publisher lists Windows 11 · [evidence](https://mediaarea.net/en/MediaInfo/Download/Windows) | Verify selected binary / smoke test |
| 222 | MicroSIP | [Current link](https://www.microsip.org) | Download/release navigation detected | Windows 11 not established · [evidence](https://www.microsip.org) | Verify support / run smoke test |
| 223 | Microsoft Safety Scanner | [Current link](https://learn.microsoft.com/en-us/defender-endpoint/safety-scanner-download) | Download/release navigation detected | Publisher lists Windows 11 · [evidence](https://learn.microsoft.com/en-us/defender-endpoint/safety-scanner-download) | Verify selected binary / smoke test |
| 224 | MilkyTracker | [Current link](https://milkytracker.org/) | Download/release navigation detected | Windows 11 not established · [evidence](https://milkytracker.org/) | Verify support / run smoke test |
| 225 | Mines-Perfect | [Current link](https://portableapps.com/apps/games/mines-perfect_portable) | Binary/archive link detected; payload untested | Packager lists Windows 11 · [evidence](https://portableapps.com/apps/games/mines-perfect_portable) | Verify selected binary / smoke test |
| 226 | Miranda NG | [Current link](https://miranda-ng.org) | Binary/archive link detected; payload untested | Windows 11 not established · [evidence](https://miranda-ng.org) | Verify support / run smoke test |
| 227 | Mixxx | [Current link](https://mixxx.org/) | Download/release navigation detected | Windows 11 not established · [evidence](https://mixxx.org/) | Verify support / run smoke test |
| 228 | MKVToolNix | [Current link](https://mkvtoolnix.download/) | Download/release navigation detected | Windows 11 not established · [evidence](https://mkvtoolnix.download/) | Verify support / run smoke test |
| 229 | Mnemosyne | [Current link](https://mnemosyne-proj.org/) | Download/release navigation detected | Windows 11 not established · [evidence](https://mnemosyne-proj.org/) | Verify support / run smoke test |
| 230 | Money Manager Ex | [Current link](https://github.com/moneymanagerex/moneymanagerex/releases) | Download/release navigation detected | Windows 11 not established · [evidence](https://github.com/moneymanagerex/moneymanagerex/releases) | Verify support / run smoke test |
| 231 | Monster 2 | [Current link](https://portableapps.com/apps/games/monster_2_portable) | Binary/archive link detected; payload untested | Packager lists Windows 11 · [evidence](https://portableapps.com/apps/games/monster_2_portable) | Verify selected binary / smoke test |
| 232 | Moonlight | [Current link](https://moonlight-stream.org/) | Download/release navigation detected | Windows 11 not established · [evidence](https://moonlight-stream.org/) | Verify support / run smoke test |
| 233 | Mozilla Firefox | [Current link](https://www.mozilla.org/firefox/new/) | Download/release navigation detected | Windows 11 not established · [evidence](https://www.mozilla.org/firefox/new/) | Verify support / run smoke test |
| 234 | Mozilla Firefox Developer Edition | [Current link](https://www.mozilla.org/firefox/developer/) | Download/release navigation detected | Windows 11 not established · [evidence](https://www.mozilla.org/firefox/developer/) | Verify support / run smoke test |
| 235 | Mozilla Thunderbird | [Current link](https://www.thunderbird.net/) | Download/release navigation detected | Windows 11 not established · [evidence](https://www.thunderbird.net/) | Verify support / run smoke test |
| 236 | Mp3splt-gtk | [Current link](https://sourceforge.net/projects/mp3splt/) | Download/release navigation detected | Windows 11 not established · [evidence](https://sourceforge.net/projects/mp3splt/) | Verify support / run smoke test |
| 237 | MPV | [Current link](https://mpv.io/) | Download route not established from retrieved page | Windows 11 not established · [evidence](https://mpv.io/) | Verify support / run smoke test |
| 238 | Mumble | [Current link](https://www.mumble.info/) | Download/release navigation detected | Windows 11 not established · [evidence](https://www.mumble.info/) | Verify support / run smoke test |
| 239 | MuseScore | [Current link](https://musescore.org/) | Download/release navigation detected | Windows 11 not established · [evidence](https://musescore.org/) | Verify support / run smoke test |
| 240 | MusicBee | [Current link](https://www.getmusicbee.com/) | Download/release navigation detected | Publisher lists Windows 11 · [evidence](https://www.getmusicbee.com/) | Verify selected binary / smoke test |
| 241 | MusicBrainz Picard | [Current link](https://picard.musicbrainz.org/downloads/) | Windows downloads seen via web retrieval | Publisher lists Windows 11 · [evidence](https://picard.musicbrainz.org/downloads/) | Verify selected binary / smoke test |
| 242 | MyPaint | [Current link](https://mypaint.app/) | Download route not established from retrieved page | Windows 11 not established · [evidence](https://mypaint.app/) | Verify support / run smoke test |
| 243 | MyPAL | [Current link](https://github.com/Feodor2/Mypal) | Source repository; inspect release assets | Windows 11 not established · [evidence](https://github.com/Feodor2/Mypal) | Verify support / run smoke test |
| 244 | NanaZip | [Current link](https://github.com/M2Team/NanaZip/releases) | Download/release navigation detected | Windows 11 not established · [evidence](https://github.com/M2Team/NanaZip/releases) | Verify support / run smoke test |
| 245 | NAPS2 | [Current link](https://www.naps2.com/) | Binary/archive link detected; payload untested | Windows 11 not established · [evidence](https://www.naps2.com/) | Verify support / run smoke test |
| 246 | Nemp | [Current link](https://www.nemp-online.de/) | Blocked/error: <urlopen error timed out> | Windows 11 not established · [evidence](https://www.nemp-online.de/) | Verify support / run smoke test |
| 247 | NetHack | [Current link](https://www.nethack.org/common/index.html) | Download/release navigation detected | Publisher lists Windows 11 · [evidence](https://www.nethack.org/common/index.html) | Verify selected binary / smoke test |
| 248 | netPanzer | [Current link](https://github.com/netpanzer/netpanzer/releases) | Download/release navigation detected | Windows 11 not established · [evidence](https://github.com/netpanzer/netpanzer/releases) | Verify support / run smoke test |
| 249 | Neverball | [Current link](https://neverball.org/) | Download/release navigation detected | Packager lists Windows 11 · [evidence](https://portableapps.com/apps/games/neverball_portable) | Verify selected binary / smoke test |
| 250 | Notepad++ | [Current link](https://notepad-plus-plus.org/downloads/) | Download/release navigation detected | Windows 11 not established · [evidence](https://notepad-plus-plus.org/downloads/) | Verify support / run smoke test |
| 251 | Notepad2 | [Current link](http://www.flos-freeware.ch/notepad2.html) | Binary/archive link detected; payload untested | Windows 11 not established · [evidence](http://www.flos-freeware.ch/notepad2.html) | Verify support / run smoke test |
| 252 | Notepad2-mod | [Current link](https://xhmikosr.github.io/notepad2-mod/) | Binary/archive link detected; payload untested | Windows 11 not established · [evidence](https://xhmikosr.github.io/notepad2-mod/) | Verify support / run smoke test |
| 253 | Notes | [Current link](https://notes-foss.com) | Download/release navigation detected | Windows 11 not established · [evidence](https://notes-foss.com) | Verify support / run smoke test |
| 254 | NSIS | [Current link](https://nsis.sourceforge.io/) | Download/release navigation detected | Windows 11 not established · [evidence](https://nsis.sourceforge.io/) | Verify support / run smoke test |
| 255 | NVDA | [Current link](https://www.nvaccess.org/) | Download/release navigation detected | Windows 11 not established · [evidence](https://www.nvaccess.org/) | Verify support / run smoke test |
| 256 | O&O ShutUp10++ | [Current link](https://www.oo-software.com/en/shutup10) | Download/release navigation detected | Publisher lists Windows 11 · [evidence](https://www.oo-software.com/en/shutup10) | Verify selected binary / smoke test |
| 257 | OBS Studio | [Current link](https://obsproject.com/) | Binary/archive link detected; payload untested | Publisher lists Windows 11 · [evidence](https://obsproject.com/) | Verify selected binary / smoke test |
| 258 | Obsidian | [Current link](https://obsidian.md) | Download/release navigation detected | Windows 11 not established · [evidence](https://obsidian.md) | Verify support / run smoke test |
| 259 | On-Screen Keyboard | [Current link](https://portableapps.com/apps/accessibility/on-screen_keyboard_portable) | Binary/archive link detected; payload untested | Packager lists Windows 11 · [evidence](https://portableapps.com/apps/accessibility/on-screen_keyboard_portable) | Verify selected binary / smoke test |
| 260 | OneLoupe | [Current link](https://portableapps.com/apps/accessibility/oneloupe-portable) | Binary/archive link detected; payload untested | Packager lists Windows 11 · [evidence](https://portableapps.com/apps/accessibility/oneloupe-portable) | Verify selected binary / smoke test |
| 261 | Opal | [Current link](https://github.com/CodeDead/opal) | Source repository; inspect release assets | Windows 11 not established · [evidence](https://github.com/CodeDead/opal) | Verify support / run smoke test |
| 262 | OpenMPT | [Current link](https://openmpt.org/) | Download/release navigation detected | Windows 11 not established · [evidence](https://openmpt.org/) | Verify support / run smoke test |
| 263 | OpenRGB | [Current link](https://openrgb.org/) | Binary/archive link detected; payload untested | Windows 11 not established · [evidence](https://openrgb.org/) | Verify support / run smoke test |
| 264 | OpenShot | [Current link](https://www.openshot.org/) | Download/release navigation detected | Windows 11 not established · [evidence](https://www.openshot.org/) | Verify support / run smoke test |
| 265 | OpenTTD | [Current link](https://www.openttd.org/downloads/openttd-releases/latest) | Binary/archive link detected; payload untested | Windows 11 not established · [evidence](https://www.openttd.org/downloads/openttd-releases/latest) | Verify support / run smoke test |
| 266 | Opera | [Current link](https://www.opera.com) | Download/release navigation detected | Windows 11 not established · [evidence](https://www.opera.com) | Verify support / run smoke test |
| 267 | Opera GX | [Current link](https://www.opera.com) | Download/release navigation detected | Windows 11 not established · [evidence](https://www.opera.com) | F18 |
| 268 | Otter Browser | [Current link](https://otter-browser.org/) | Download route not established from retrieved page | Windows 11 not established · [evidence](https://otter-browser.org/) | Verify support / run smoke test |
| 269 | Paint.NET | [Current link](https://www.getpaint.net/) | Blocked/error: HTTP 406 | Publisher lists Windows 11 · [evidence](https://paint.net/download.html) | Verify selected binary / smoke test |
| 270 | Password Safe | [Current link](https://pwsafe.org) | Binary/archive link detected; payload untested | Windows 11 not established · [evidence](https://pwsafe.org) | Verify support / run smoke test |
| 271 | Pathological | [Current link](https://portableapps.com/apps/games/pathological_portable) | Binary/archive link detected; payload untested | Packager lists Windows 11 · [evidence](https://portableapps.com/apps/games/pathological_portable) | Verify selected binary / smoke test |
| 272 | Paul Stretch | [Current link](https://portableapps.com/apps/music_video/paul_stretch_portable) | Binary/archive link detected; payload untested | Packager lists Windows 11 · [evidence](https://portableapps.com/apps/music_video/paul_stretch_portable) | Verify selected binary / smoke test |
| 273 | PChat | [Current link](https://www.portablefreeware.com/index.php?id=1731) | Blocked/error: HTTP 403 | Windows 11 not established · [evidence](https://www.portablefreeware.com/index.php?id=1731) | Verify support / run smoke test |
| 274 | PCI-Z | [Current link](http://www.pci-z.com/current/PCI-Z.exe) | Direct executable response; not executed | Windows 11 not established · [evidence](http://www.pci-z.com/current/PCI-Z.exe) | Verify support / run smoke test |
| 275 | PDF Arranger | [Current link](https://github.com/pdfarranger/pdfarranger) | Source repository; inspect release assets | Windows 11 not established · [evidence](https://github.com/pdfarranger/pdfarranger) | Verify support / run smoke test |
| 276 | PDF-XChange Editor | [Current link](https://www.pdf-xchange.com/) | Download/release navigation detected | Windows 11 not established · [evidence](https://www.pdf-xchange.com/) | Verify support / run smoke test |
| 277 | PDFsam Basic | [Current link](https://pdfsam.org/) | Download/release navigation detected | Windows 11 not established · [evidence](https://pdfsam.org/) | Verify support / run smoke test |
| 278 | PDFTK Builder | [Current link](https://pdftk-builder-enhanced.sourceforge.io/) | Binary/archive link detected; payload untested | Windows 11 not established · [evidence](https://pdftk-builder-enhanced.sourceforge.io/) | Verify support / run smoke test |
| 279 | PeaZip | [Current link](https://peazip.github.io/) | Download/release navigation detected | Windows 11 not established · [evidence](https://peazip.github.io/) | Verify support / run smoke test |
| 280 | PeerBlock | [Current link](http://www.peerblock.com) | Binary/archive link detected; payload untested | Windows 11 not established · [evidence](http://www.peerblock.com) | Verify support / run smoke test |
| 281 | Pencil Project | [Current link](http://pencil.evolus.vn/) | Download/release navigation detected | Windows 11 not established · [evidence](http://pencil.evolus.vn/) | Verify support / run smoke test |
| 282 | Pencil2D | [Current link](https://www.pencil2d.org/download) | Binary/archive link detected; payload untested | Windows 11 not established · [evidence](https://www.pencil2d.org/download) | Verify support / run smoke test |
| 283 | PhotoDemon | [Current link](https://photodemon.org/) | Binary/archive link detected; payload untested | Publisher lists Windows 11 · [evidence](https://photodemon.org/) | Verify selected binary / smoke test |
| 284 | PhotoFilmStrip | [Current link](https://www.photofilmstrip.org/en/download/) | Download/release navigation detected | Windows 11 not established · [evidence](https://www.photofilmstrip.org/en/download/) | F36 |
| 285 | PhotoFiltre | [Current link](https://www.photofiltre-studio.com/) | Download route not established from retrieved page | Windows 11 not established · [evidence](https://www.photofiltre-studio.com/) | Verify support / run smoke test |
| 286 | Pidgin | [Current link](https://pidgin.im/) | Download/release navigation detected | Windows 11 not established · [evidence](https://pidgin.im/) | Verify support / run smoke test |
| 287 | Pingus | [Current link](http://pingus.seul.org/download.html) | Binary/archive link detected; payload untested | Windows 11 not established · [evidence](http://pingus.seul.org/download.html) | Verify support / run smoke test |
| 288 | Pinta | [Current link](https://www.pinta-project.com/) | Download/release navigation detected | Windows 11 not established · [evidence](https://www.pinta-project.com/) | Verify support / run smoke test |
| 289 | Pixelorama | [Current link](https://www.pixelorama.org/) | Download/release navigation detected | Windows 11 not established · [evidence](https://www.pixelorama.org/) | Verify support / run smoke test |
| 290 | Playnite | [Current link](https://playnite.link/) | Binary/archive link detected; payload untested | Windows 11 not established · [evidence](https://playnite.link/) | Verify support / run smoke test |
| 291 | PNotes | [Current link](http://portableapps.com/apps/office/pnotes_portable) | Binary/archive link detected; payload untested | Packager lists Windows 11 · [evidence](http://portableapps.com/apps/office/pnotes_portable) | Verify selected binary / smoke test |
| 292 | PNotes.NET | [Current link](https://pnotes.net/) | Download route not established from retrieved page | Windows 11 not established · [evidence](https://pnotes.net/) | Verify support / run smoke test |
| 293 | PokerTH | [Current link](https://www.pokerth.net) | Download/release navigation detected | Windows 11 not established · [evidence](https://www.pokerth.net) | Verify support / run smoke test |
| 294 | PopMan | [Current link](http://ch-software.de/popman/) | Download/release navigation detected | Windows 11 not established · [evidence](http://ch-software.de/popman/) | Verify support / run smoke test |
| 295 | PortableApps.com AppCompactor | [Current link](https://portableapps.com) | Generic vendor/directory destination | Packager lists Windows 11 · [evidence](https://portableapps.com/download) | F20 |
| 296 | PortableApps.com Installer | [Current link](https://portableapps.com/development/portableapps.com_installer) | Download/release navigation detected | Packager lists Windows 11 · [evidence](https://portableapps.com/download) | Verify selected binary / smoke test |
| 297 | PortableApps.com Launcher | [Current link](http://portableapps.com/apps/development/portableapps.com_launcher) | Binary/archive link detected; payload untested | Packager lists Windows 11 · [evidence](http://portableapps.com/apps/development/portableapps.com_launcher) | Verify selected binary / smoke test |
| 298 | PortableApps.com Platform | [Current link](https://portableapps.com/Download) | Binary/archive link detected; payload untested | Packager lists Windows 11 · [evidence](https://portableapps.com/Download) | Verify selected binary / smoke test |
| 299 | PortExpert | [Current link](https://www.kcsoftwares.com) | Unavailable: HTTP 404 | Windows 11 not established · [evidence](https://www.kcsoftwares.com) | F32 |
| 300 | PotPlayer | [Current link](https://potplayer.daum.net/) | Blocked/error: <urlopen error timed out> | Windows 11 not established · [evidence](https://potplayer.daum.net/) | Verify support / run smoke test |
| 301 | PowerToys | [Current link](https://github.com/microsoft/PowerToys) | Source repository; inspect release assets | Windows 11 not established · [evidence](https://github.com/microsoft/PowerToys) | Verify support / run smoke test |
| 302 | PrivaZer | [Current link](https://privazer.com/en/downloadupdate.php) | Binary/archive link detected; payload untested | Windows 11 not established · [evidence](https://privazer.com/en/downloadupdate.php) | Verify support / run smoke test |
| 303 | Process Explorer | [Current link](https://learn.microsoft.com/en-us/sysinternals/downloads/process-explorer) | Binary/archive link detected; payload untested | Publisher lists Windows 11 · [evidence](https://learn.microsoft.com/en-us/sysinternals/downloads/process-explorer) | Verify selected binary / smoke test |
| 304 | Process Hacker | [Current link](https://github.com/winsiderss/systeminformer) | Source repository; inspect release assets | Windows 11 not established · [evidence](https://github.com/winsiderss/systeminformer) | F26 |
| 305 | Process Monitor | [Current link](https://learn.microsoft.com/en-us/sysinternals/downloads/procmon) | Binary/archive link detected; payload untested | Publisher lists Windows 11 · [evidence](https://learn.microsoft.com/en-us/sysinternals/downloads/procmon) | Verify selected binary / smoke test |
| 306 | ProcessKO | [Current link](https://www.softwareok.com/?seite=Freeware/ProcessKO) | Download/release navigation detected | Publisher lists Windows 11 · [evidence](https://www.softwareok.com/?seite=Freeware/ProcessKO) | Verify selected binary / smoke test |
| 307 | Project Invincible | [Current link](https://portableapps.com/news/2013-01-06--project-invincible-portable-2.02-released) | Old release announcement | Packager lists Windows 11 · [evidence](https://portableapps.com/download) | Verify selected binary / smoke test |
| 308 | PuTTY | [Current link](https://putty.software/) | Download/release navigation detected | Windows 11 not established · [evidence](https://putty.software/) | Verify support / run smoke test |
| 309 | Puzzle Collection | [Current link](https://www.chiark.greenend.org.uk/~sgtatham/puzzles/) | Binary/archive link detected; payload untested | Packager lists Windows 11 · [evidence](https://portableapps.com/apps/games/puzzle_collection_portable) | Verify selected binary / smoke test |
| 310 | Q-Dir | [Current link](https://www.softwareok.com/?seite=Freeware/Q-Dir) | Download/release navigation detected | Publisher lists Windows 11 · [evidence](https://www.softwareok.com/?seite=Freeware/Q-Dir) | Verify selected binary / smoke test |
| 311 | Q-Eye | [Current link](https://www.etl-tools.com/) | Generic vendor/directory destination | Windows 11 not established · [evidence](https://www.etl-tools.com/) | Verify support / run smoke test |
| 312 | Qalculate | [Current link](https://github.com/Qalculate/qalculate-qt/releases/tag/v5.12.0) | Binary/archive link detected; payload untested | Windows 11 not established · [evidence](https://github.com/Qalculate/qalculate-qt/releases/tag/v5.12.0) | F29 |
| 313 | qBittorrent | [Current link](https://www.qbittorrent.org) | Download/release navigation detected | Windows 11 not established · [evidence](https://www.qbittorrent.org) | Verify support / run smoke test |
| 314 | qBittorrent Enhanced | [Current link](https://github.com/c0re100/qBittorrent-Enhanced-Edition) | Source repository; inspect release assets | Publisher lists Windows 11 · [evidence](https://github.com/c0re100/qBittorrent-Enhanced-Edition) | Verify selected binary / smoke test |
| 315 | Qmmp | [Current link](https://qmmp.ylsoftware.com/) | Download/release navigation detected | Windows 11 not established · [evidence](https://qmmp.ylsoftware.com/) | Verify support / run smoke test |
| 316 | QOwnNotes | [Current link](https://www.qownnotes.org/) | Download/release navigation detected | Windows 11 not established · [evidence](https://www.qownnotes.org/) | Verify support / run smoke test |
| 317 | qTox | [Current link](https://github.com/qTox/qTox) | Source repository; inspect release assets | Windows 11 not established · [evidence](https://github.com/qTox/qTox) | Verify support / run smoke test |
| 318 | Quick Blackjack | [Current link](https://wesleysteiner.com) | Download route not established from retrieved page | Windows 11 not established · [evidence](https://wesleysteiner.com) | Verify support / run smoke test |
| 319 | Quick Bridge | [Current link](https://wesleysteiner.com) | Download route not established from retrieved page | Windows 11 not established · [evidence](https://wesleysteiner.com) | Verify support / run smoke test |
| 320 | Quick Cribbage | [Current link](https://wesleysteiner.com) | Download route not established from retrieved page | Windows 11 not established · [evidence](https://wesleysteiner.com) | Verify support / run smoke test |
| 321 | Quick Poker | [Current link](https://wesleysteiner.com) | Download route not established from retrieved page | Windows 11 not established · [evidence](https://wesleysteiner.com) | Verify support / run smoke test |
| 322 | Quick Solitaire | [Current link](https://wesleysteiner.com) | Download route not established from retrieved page | Packager lists Windows 11 · [evidence](https://portableapps.com/apps/games/quick_solitaire_portable) | Verify selected binary / smoke test |
| 323 | QuickMemoryTestOK | [Current link](https://www.softwareok.com/?seite=Microsoft/QuickMemoryTestOK) | Download/release navigation detected | Publisher lists Windows 11 · [evidence](https://www.softwareok.com/?seite=Microsoft/QuickMemoryTestOK) | Verify selected binary / smoke test |
| 324 | QuiteRSS | [Current link](https://quiterss.org) | Download route not established from retrieved page | Windows 11 not established · [evidence](https://quiterss.org) | Verify support / run smoke test |
| 325 | QwikMark | [Current link](https://portableapps.com/apps/utilities/qwikmark-portable) | Binary/archive link detected; payload untested | Packager lists Windows 11 · [evidence](https://portableapps.com/apps/utilities/qwikmark-portable) | Verify selected binary / smoke test |
| 326 | r3dfox | [Current link](https://eclipse.cx/projects/r3dfox) | Download/release navigation detected | Windows 11 not established · [evidence](https://eclipse.cx/projects/r3dfox) | Verify support / run smoke test |
| 327 | RAMMap | [Current link](https://learn.microsoft.com/en-us/sysinternals/downloads/rammap) | Binary/archive link detected; payload untested | Windows 11 not established · [evidence](https://learn.microsoft.com/en-us/sysinternals/downloads/rammap) | Verify support / run smoke test |
| 328 | Rapid CRC Unicode | [Current link](https://www.ov2.eu/programs/rapidcrc-unicode) | Binary/archive link detected; payload untested | Windows 11 not established · [evidence](https://www.ov2.eu/programs/rapidcrc-unicode) | Verify support / run smoke test |
| 329 | RawTherapee | [Current link](https://www.rawtherapee.com/) | Blocked/error: HTTP 466 | Windows 11 not established · [evidence](https://www.rawtherapee.com/) | Verify support / run smoke test |
| 330 | RBTray | [Current link](https://github.com/g-bortoletto/rbtray) | Source repository; inspect release assets | Windows 11 not established · [evidence](https://github.com/g-bortoletto/rbtray) | Verify support / run smoke test |
| 331 | Recuva | [Current link](https://www.ccleaner.com/recuva/download/standard) | Download route not established from retrieved page | Windows 11 not established · [evidence](https://www.ccleaner.com/recuva/download/standard) | Verify support / run smoke test |
| 332 | RedNotebook | [Current link](http://rednotebook.app) | Download/release navigation detected | Windows 11 not established · [evidence](http://rednotebook.app) | Verify support / run smoke test |
| 333 | RegAlyzer | [Current link](http://safer-networking.org/products/regalyzer/) | Download/release navigation detected | Windows 11 not established · [evidence](http://safer-networking.org/products/regalyzer/) | Verify support / run smoke test |
| 334 | Regshot | [Current link](https://github.com/Seabreg/Regshot) | Source repository; inspect release assets | Windows 11 not established · [evidence](https://github.com/Seabreg/Regshot) | Verify support / run smoke test |
| 335 | ReNamer | [Current link](https://www.den4b.com/changelogs/renamer) | Version history / changelog | Windows 11 not established · [evidence](https://www.den4b.com/changelogs/renamer) | F22 |
| 336 | Resource Hacker | [Current link](http://angusj.com/resourcehacker/) | Blocked/error: HTTP 406 | Packager lists Windows 11 · [evidence](https://portableapps.com/apps/utilities/resource-hacker-portable) | Verify selected binary / smoke test |
| 337 | RetroArch | [Current link](https://www.retroarch.com/) | Download/release navigation detected | Publisher lists Windows 11 · [evidence](https://www.retroarch.com/?page=platforms) | Verify selected binary / smoke test |
| 338 | RetroShare | [Current link](https://retroshare.cc/) | Download/release navigation detected | Packager lists Windows 11 · [evidence](https://portableapps.com/node/66914) | Verify selected binary / smoke test |
| 339 | RisohEditor | [Current link](https://katahiromz.web.fc2.com/re/en) | Binary/archive link detected; payload untested | Windows 11 not established · [evidence](https://katahiromz.web.fc2.com/re/en) | Verify support / run smoke test |
| 340 | Rocks'n'Diamonds | [Current link](http://www.artsoft.org/rocksndiamonds/) | Download/release navigation detected | Windows 11 not established · [evidence](http://www.artsoft.org/rocksndiamonds/) | Verify support / run smoke test |
| 341 | RSS Guard | [Current link](https://github.com/martinrotter/rssguard) | Source repository; inspect release assets | Windows 11 not established · [evidence](https://github.com/martinrotter/rssguard) | Verify support / run smoke test |
| 342 | Rufus | [Current link](https://rufus.ie) | Download route not established from retrieved page | Windows 11 not established · [evidence](https://rufus.ie) | Verify support / run smoke test |
| 343 | Run-Command | [Current link](https://www.softwareok.com/?seite=Freeware/Run-Command) | Download/release navigation detected | Publisher lists Windows 11 · [evidence](https://www.softwareok.com/?seite=Freeware/Run-Command) | Verify selected binary / smoke test |
| 344 | RustDesk | [Current link](https://rustdesk.com/download/) | Blocked/error: <urlopen error timed out> | Windows 11 not established · [evidence](https://rustdesk.com/download/) | F11 |
| 345 | Sandboxie Plus | [Current link](https://sandboxie-plus.com/) | Download/release navigation detected | Publisher lists Windows 11 · [evidence](https://sandboxie-plus.com/downloads/) | Verify selected binary / smoke test |
| 346 | Sauerbraten | [Current link](https://www.sauerbraten.org/) | Blocked/error: HTTP 502 | Windows 11 not established · [evidence](https://www.sauerbraten.org/) | Verify support / run smoke test |
| 347 | Scorched 3D | [Current link](http://www.scorched3d.co.uk/) | Download/release navigation detected | Windows 11 not established · [evidence](http://www.scorched3d.co.uk/) | Verify support / run smoke test |
| 348 | ScreenToGif | [Current link](https://www.screentogif.com/) | Migrated page; download unverified | Publisher lists Windows 11 · [evidence](https://github.com/NickeManarin/ScreenToGif/wiki) | F35 |
| 349 | Scribus | [Current link](https://www.scribus.net/) | Download route not established from retrieved page | Windows 11 not established · [evidence](https://www.scribus.net/) | Verify support / run smoke test |
| 350 | SeaMonkey | [Current link](https://www.seamonkey-project.org) | Binary/archive link detected; payload untested | Windows 11 not established · [evidence](https://www.seamonkey-project.org) | Verify support / run smoke test |
| 351 | Session | [Current link](https://getsession.org) | HTTP 200 placeholder; unverified | Windows 11 not established · [evidence](https://getsession.org) | Verify support / run smoke test |
| 352 | ShareX | [Current link](https://getsharex.com) | Download/release navigation detected | Windows 11 not established · [evidence](https://getsharex.com) | Verify support / run smoke test |
| 353 | Shortcuts Search And Replace | [Current link](http://jacquelin.potier.free.fr/ShortcutsSearchAndReplace/) | Binary/archive link detected; payload untested | Publisher lists Windows 11 · [evidence](http://jacquelin.potier.free.fr/ShortcutsSearchAndReplace/) | Verify selected binary / smoke test |
| 354 | Shotcut | [Current link](https://www.shotcut.org/) | Download/release navigation detected | Publisher lists Windows 11 · [evidence](https://www.shotcut.org/download/) | Verify selected binary / smoke test |
| 355 | Sigil | [Current link](https://sigil-ebook.com/) | Download route not established from retrieved page | Windows 11 not established · [evidence](https://sigil-ebook.com/) | Verify support / run smoke test |
| 356 | Signal Desktop | [Current link](https://signal.org/download/) | Download/release navigation detected | Windows 11 not established · [evidence](https://signal.org/download/) | Verify support / run smoke test |
| 357 | Simple Sudoku | [Current link](http://www.angusj.com/sudoku/) | Blocked/error: HTTP 406 | Windows 11 not established · [evidence](http://www.angusj.com/sudoku/) | Verify support / run smoke test |
| 358 | SimpleWall | [Current link](https://github.com/henrypp/simplewall) | Source repository; inspect release assets | Publisher lists Windows 11 · [evidence](https://github.com/henrypp/simplewall) | Verify selected binary / smoke test |
| 359 | Smart Deblur | [Current link](https://github.com/Y-Vladimir/SmartDeblur) | Source repository; inspect release assets | Windows 11 not established · [evidence](https://github.com/Y-Vladimir/SmartDeblur) | F34 |
| 360 | SMPlayer | [Current link](https://www.smplayer.info/) | Blocked/error: HTTP 406 | Windows 11 not established · [evidence](https://www.smplayer.info/) | Verify support / run smoke test |
| 361 | SnapTimer | [Current link](https://dan.hersam.com/software/snaptimer/index.php) | Binary/archive link detected; payload untested | Packager lists Windows 11 · [evidence](http://portableapps.com/apps/utilities/snaptimer-portable) | Verify selected binary / smoke test |
| 362 | SpeedCrunch | [Current link](http://speedcrunch.org/) | Download/release navigation detected | Windows 11 not established · [evidence](http://speedcrunch.org/) | Verify support / run smoke test |
| 363 | SpeedyFox | [Current link](https://crystalidea.com/speedyfox/) | Unavailable: HTTP 404 | Windows 11 not established · [evidence](https://crystalidea.com/speedyfox/) | F13 |
| 364 | Spybot - Search & Destroy | [Current link](https://www.safer-networking.org) | Download/release navigation detected | Windows 11 not established · [evidence](https://www.safer-networking.org) | Verify support / run smoke test |
| 365 | SSD-Z | [Current link](https://portableapps.com/news/2016-06-30--ssd-z-portable-16.06.29.b-released) | Old release announcement | Packager lists Windows 11 · [evidence](https://portableapps.com/download) | Verify selected binary / smoke test |
| 366 | StackNotes | [Current link](https://portableapps.com/node/70651) | Binary/archive link detected; payload untested | Packager lists Windows 11 · [evidence](https://portableapps.com/node/70651) | Verify selected binary / smoke test |
| 367 | Startup Sentinel | [Current link](https://www.kcsoftwares.com/?home) | Unavailable: HTTP 404 | Windows 11 not established · [evidence](https://www.kcsoftwares.com/?home) | F32 |
| 368 | Stella | [Current link](https://stella-emu.github.io) | Download/release navigation detected | Publisher lists Windows 11 · [evidence](https://stella-emu.github.io/downloads.html) | Verify selected binary / smoke test |
| 369 | Stellarium | [Current link](https://stellarium.org/) | Binary/archive link detected; payload untested | Publisher lists Windows 11 · [evidence](https://stellarium.org/) | Verify selected binary / smoke test |
| 370 | Stickies | [Current link](https://www.zhornsoftware.co.uk/stickies/versions.html) | Version history / changelog | Publisher lists Windows 11 · [evidence](https://www.zhornsoftware.co.uk/stickies/download.html) | F23 |
| 371 | Stirling PDF | [Current link](https://github.com/Stirling-Tools/Stirling-PDF) | Source repository; inspect release assets | Windows 11 not established · [evidence](https://github.com/Stirling-Tools/Stirling-PDF) | Verify support / run smoke test |
| 372 | Strawberry Music Player | [Current link](https://www.strawberrymusicplayer.org/) | Paid access to current Windows binaries | Publisher lists Windows 11 · [evidence](https://www.strawberrymusicplayer.org/) | F02 |
| 373 | StreamWriter | [Current link](https://streamwriter.org/) | Download/release navigation detected | Packager lists Windows 11 · [evidence](https://portableapps.com/apps/music_video/streamwriter-portable) | Verify selected binary / smoke test |
| 374 | StressMyPC | [Current link](https://www.softwareok.com/?Download=StressMyPC) | Binary/archive link detected; payload untested | Publisher lists Windows 11 · [evidence](https://www.softwareok.com/?Download=StressMyPC) | Verify selected binary / smoke test |
| 375 | Sudoku | [Current link](https://portableapps.com/node/58961) | Binary/archive link detected; payload untested | Packager lists Windows 11 · [evidence](https://portableapps.com/node/58961) | Verify selected binary / smoke test |
| 376 | Sumatra PDF | [Current link](https://www.sumatrapdfreader.org/) | Download/release navigation detected | Publisher lists Windows 11 · [evidence](https://www.sumatrapdfreader.org/) | Verify selected binary / smoke test |
| 377 | Supermium | [Current link](https://win32subsystem.live/supermium/) | Binary/archive link detected; payload untested | Windows 11 not established · [evidence](https://win32subsystem.live/supermium/) | Verify support / run smoke test |
| 378 | SuperTux | [Current link](https://supertux.org/) | Download/release navigation detected | Windows 11 not established · [evidence](https://supertux.org/) | Verify support / run smoke test |
| 379 | SuperTuxKart | [Current link](https://supertuxkart.net/Download) | Binary/archive link detected; payload untested | Windows 11 not established · [evidence](https://supertuxkart.net/Download) | Verify support / run smoke test |
| 380 | SWI-Prolog | [Current link](https://www.swi-prolog.org) | Download route not established from retrieved page | Windows 11 not established · [evidence](https://www.swi-prolog.org) | Verify support / run smoke test |
| 381 | Sylpheed | [Current link](https://sylpheed.sraoss.jp) | Download/release navigation detected | Windows 11 not established · [evidence](https://sylpheed.sraoss.jp) | Verify support / run smoke test |
| 382 | Syncthing | [Current link](https://syncthing.net) | Download/release navigation detected | Windows 11 not established · [evidence](https://syncthing.net) | Verify support / run smoke test |
| 383 | System Informer | [Current link](https://github.com/winsiderss/systeminformer) | Source repository; inspect release assets | Windows 11 not established · [evidence](https://github.com/winsiderss/systeminformer) | F26 |
| 384 | T^3 | [Current link](https://portableapps.com/apps/games/t-3_portable) | Binary/archive link detected; payload untested | Packager lists Windows 11 · [evidence](https://portableapps.com/apps/games/t-3_portable) | Verify selected binary / smoke test |
| 385 | Task Coach | [Current link](https://github.com/taskcoach/taskcoach) | Source repository; inspect release assets | Windows 11 not established · [evidence](https://github.com/taskcoach/taskcoach) | Verify support / run smoke test |
| 386 | TCPView | [Current link](https://learn.microsoft.com/en-us/sysinternals/downloads/tcpview) | Binary/archive link detected; payload untested | Windows 11 not established · [evidence](https://learn.microsoft.com/en-us/sysinternals/downloads/tcpview) | Verify support / run smoke test |
| 387 | TeamViewer | [Current link](https://www.teamviewer.com) | HTTP 200 placeholder; unverified | Windows 11 not established · [evidence](https://www.teamviewer.com) | Verify support / run smoke test |
| 388 | Telegram Desktop | [Current link](https://telegram.org/) | Download/release navigation detected | Windows 11 not established · [evidence](https://telegram.org/) | Verify support / run smoke test |
| 389 | Texter | [Current link](https://portableapps.com/apps/utilities/texter_portable) | Binary/archive link detected; payload untested | Packager lists Windows 11 · [evidence](https://portableapps.com/apps/utilities/texter_portable) | F37 |
| 390 | Textify | [Current link](https://ramensoftware.com/textify) | Binary/archive link detected; payload untested | Windows 11 not established · [evidence](https://ramensoftware.com/textify) | Verify support / run smoke test |
| 391 | The Legend of Edgar | [Current link](https://www.parallelrealities.co.uk/games/edgar/) | Download/release navigation detected | Windows 11 not established · [evidence](https://www.parallelrealities.co.uk/games/edgar/) | Verify support / run smoke test |
| 392 | The Powder Toy | [Current link](https://powdertoy.co.uk/Download.html) | Binary/archive link detected; payload untested | Windows 11 not established · [evidence](https://powdertoy.co.uk/Download.html) | Verify support / run smoke test |
| 393 | Tick5 | [Current link](https://portableapps.com/apps/games/tick5_portable) | Binary/archive link detected; payload untested | Packager lists Windows 11 · [evidence](https://portableapps.com/apps/games/tick5_portable) | Verify selected binary / smoke test |
| 394 | TidyTabs | [Current link](https://www.nurgo-software.com/products/tidytabs) | Download route not established from retrieved page | Windows 11 not established · [evidence](https://www.nurgo-software.com/products/tidytabs) | Verify support / run smoke test |
| 395 | Tile World | [Current link](http://www.muppetlabs.com/~breadbox/software/tworld/) | Binary/archive link detected; payload untested | Windows 11 not established · [evidence](http://www.muppetlabs.com/~breadbox/software/tworld/) | Verify support / run smoke test |
| 396 | TinyTask | [Current link](https://www.tinytask.net/) | Binary/archive link detected; payload untested | Windows 11 not established · [evidence](https://www.tinytask.net/) | Verify support / run smoke test |
| 397 | TIPP10 | [Current link](https://www.tipp10.com/) | Download/release navigation detected | Windows 11 not established · [evidence](https://www.tipp10.com/) | Verify support / run smoke test |
| 398 | Tor Browser | [Current link](https://www.torproject.org/download/) | HTTP 200 placeholder; unverified | Windows 11 not established · [evidence](https://www.torproject.org/download/) | Verify support / run smoke test |
| 399 | Toucan | [Current link](https://portableapps.com) | Generic vendor/directory destination | Publisher lists Windows 11 · [evidence](https://portableapps.com/apps/utilities/toucan) | F19 |
| 400 | Transmission | [Current link](https://transmissionbt.com/download/) | Download route not established from retrieved page | Windows 11 not established · [evidence](https://transmissionbt.com/download/) | Verify support / run smoke test |
| 401 | TreeSize Free | [Current link](https://www.jam-software.com/treesize_free) | Binary/archive link detected; payload untested | Windows 11 not established · [evidence](https://www.jam-software.com/treesize_free) | Verify support / run smoke test |
| 402 | Trelix Stinger | [Current link](https://www.trellix.com) | Generic vendor/directory destination | Windows 11 not established · [evidence](https://www.trellix.com) | F21 |
| 403 | Twin Distress | [Current link](https://portableapps.com/apps/games/twin_distress_portable) | Binary/archive link detected; payload untested | Packager lists Windows 11 · [evidence](https://portableapps.com/apps/games/twin_distress_portable) | Verify selected binary / smoke test |
| 404 | TyperTask | [Current link](https://portableapps.com/apps/utilities/typertask-portable) | Binary/archive link detected; payload untested | Packager lists Windows 11 · [evidence](https://portableapps.com/apps/utilities/typertask-portable) | Verify selected binary / smoke test |
| 405 | uGet | [Current link](https://ugetdm.com) | Blocked/error: <urlopen error timed out> | Windows 11 not established · [evidence](https://ugetdm.com) | Verify support / run smoke test |
| 406 | UNetbootin | [Current link](https://unetbootin.github.io) | Binary/archive link detected; payload untested | Windows 11 not established · [evidence](https://unetbootin.github.io) | Verify support / run smoke test |
| 407 | Unicodia | [Current link](https://mercury13.github.io/unicodia/) | Download/release navigation detected | Publisher lists Windows 11 · [evidence](https://mercury13.github.io/unicodia/) | Verify selected binary / smoke test |
| 408 | USB Sudoku | [Current link](https://portableapps.com/apps/games/usb-sudoku-portable) | Binary/archive link detected; payload untested | Packager lists Windows 11 · [evidence](https://portableapps.com/apps/games/usb-sudoku-portable) | Verify selected binary / smoke test |
| 409 | UUID-GUID Generator | [Current link](https://portableapps.com/node/66008) | Binary/archive link detected; payload untested | Packager lists Windows 11 · [evidence](https://portableapps.com/node/66008) | Verify selected binary / smoke test |
| 410 | Ventoy | [Current link](https://www.ventoy.net/en/) | Download/release navigation detected | Windows 11 not established · [evidence](https://www.ventoy.net/en/) | Verify support / run smoke test |
| 411 | VeraCrypt | [Current link](https://veracrypt.jp) | Download route not established from retrieved page | Windows 11 not established · [evidence](https://veracrypt.jp) | Verify support / run smoke test |
| 412 | Virtual Magnifying Glass | [Current link](https://portableapps.com/news/2013-09-24--virtual-magnifying-glass-portable-3.6-released) | Old release announcement | Packager lists Windows 11 · [evidence](https://portableapps.com/download) | Verify selected binary / smoke test |
| 413 | Virtual Volumes View | [Current link](https://portableapps.com/news/2021-06-16--virtual-volumes-view-portable-1.4-released) | Old release announcement | Packager lists Windows 11 · [evidence](https://portableapps.com/download) | Verify selected binary / smoke test |
| 414 | VirtuaWin | [Current link](https://virtuawin.sourceforge.io/) | Download/release navigation detected | Windows 11 not established · [evidence](https://virtuawin.sourceforge.io/) | Verify support / run smoke test |
| 415 | VLC Media Player | [Current link](https://www.videolan.org/vlc/) | Binary/archive link detected; payload untested | Windows 11 not established · [evidence](https://www.videolan.org/vlc/) | F14 |
| 416 | VMMap | [Current link](https://learn.microsoft.com/en-us/sysinternals/downloads/vmmap) | Binary/archive link detected; payload untested | Windows 11 not established · [evidence](https://learn.microsoft.com/en-us/sysinternals/downloads/vmmap) | Verify support / run smoke test |
| 417 | VS Code | [Current link](https://code.visualstudio.com) | Download/release navigation detected | Publisher lists Windows 11 · [evidence](https://code.visualstudio.com/download) | Verify selected binary / smoke test |
| 418 | VSCodium | [Current link](https://vscodium.com/) | Download/release navigation detected | Windows 11 not established · [evidence](https://vscodium.com/) | F04 |
| 419 | WackGet | [Current link](https://portableapps.com/apps/internet/wackget-portable) | Binary/archive link detected; payload untested | Packager lists Windows 11 · [evidence](https://portableapps.com/apps/internet/wackget-portable) | Verify selected binary / smoke test |
| 420 | WarMUX | [Current link](https://github.com/gbaudic/warmux2) | Source repository; inspect release assets | Windows 11 not established · [evidence](https://github.com/gbaudic/warmux2) | Verify support / run smoke test |
| 421 | Warzone 2100 | [Current link](https://wz2100.net/) | Binary/archive link detected; payload untested | Windows 11 not established · [evidence](https://wz2100.net/) | Verify support / run smoke test |
| 422 | WAtomic | [Current link](http://portableapps.com/apps/games/watomic_portable) | Binary/archive link detected; payload untested | Packager lists Windows 11 · [evidence](http://portableapps.com/apps/games/watomic_portable) | Verify selected binary / smoke test |
| 423 | WaveShop | [Current link](https://waveshop.sourceforge.net/) | Download/release navigation detected | Windows 11 not established · [evidence](https://waveshop.sourceforge.net/) | Verify support / run smoke test |
| 424 | Whalebird | [Current link](https://whalebird.social) | Download/release navigation detected | Windows 11 not established · [evidence](https://whalebird.social) | Verify support / run smoke test |
| 425 | WhatChanged | [Current link](https://portableapps.com/apps/utilities/whatchanged-portable) | Binary/archive link detected; payload untested | Packager lists Windows 11 · [evidence](https://portableapps.com/apps/utilities/whatchanged-portable) | Verify selected binary / smoke test |
| 426 | WhoDat | [Current link](https://portableapps.com/news/2013-01-25--whodat-portable-0.9-released) | Old release announcement | Packager lists Windows 11 · [evidence](https://portableapps.com/download) | Verify selected binary / smoke test |
| 427 | WhyNotWin11 | [Current link](https://github.com/rcmaehl/WhyNotWin11/) | Source repository; inspect release assets | Windows 11 not established · [evidence](https://github.com/rcmaehl/WhyNotWin11/) | Verify support / run smoke test |
| 428 | Winaero Tweaker | [Current link](https://winaero.com/winaero-tweaker/) | Binary/archive link detected; payload untested | Publisher lists Windows 11 · [evidence](https://winaero.com/winaero-tweaker/) | Verify selected binary / smoke test |
| 429 | WinBoard Chess | [Current link](https://www.gnu.org/software/xboard/) | Blocked/error: HTTP 403 | Windows 11 not established · [evidence](https://www.gnu.org/software/xboard/) | Verify support / run smoke test |
| 430 | WinCDEmu | [Current link](https://wincdemu.sysprogs.org/portable/) | Binary/archive link detected; payload untested | Windows 11 not established · [evidence](https://wincdemu.sysprogs.org/portable/) | Verify support / run smoke test |
| 431 | WinCompose | [Current link](https://github.com/samhocevar/wincompose) | Source repository; inspect release assets | Windows 11 not established · [evidence](https://github.com/samhocevar/wincompose) | Verify support / run smoke test |
| 432 | WinContig | [Current link](https://www.mdtzone.it/sw/wincontig/en/index.html) | Binary/archive link detected; payload untested | Publisher lists Windows 11 · [evidence](https://www.mdtzone.it/sw/wincontig/en/index.html) | Verify selected binary / smoke test |
| 433 | WinDirStat | [Current link](https://windirstat.net/) | Download/release navigation detected | Windows 11 not established · [evidence](https://windirstat.net/) | Verify support / run smoke test |
| 434 | Windows Error Lookup Tool | [Current link](https://github.com/henrypp/errorlookup) | Source repository; inspect release assets | Publisher lists Windows 11 · [evidence](https://github.com/henrypp/errorlookup) | Verify selected binary / smoke test |
| 435 | WinFile | [Current link](https://github.com/microsoft/winfile) | Source repository; inspect release assets | Publisher lists Windows 11 · [evidence](https://github.com/microsoft/winfile) | Verify selected binary / smoke test |
| 436 | winLAME | [Current link](https://winlame.sourceforge.io/) | Download/release navigation detected | Windows 11 not established · [evidence](https://winlame.sourceforge.io/) | F06 |
| 437 | winMd5Sum | [Current link](https://portableapps.com/apps/utilities/winmd5sum_portable) | Binary/archive link detected; payload untested | Packager lists Windows 11 · [evidence](https://portableapps.com/apps/utilities/winmd5sum_portable) | Verify selected binary / smoke test |
| 438 | WinMerge | [Current link](https://winmerge.org/) | Download/release navigation detected | Packager lists Windows 11 · [evidence](https://portableapps.com/apps/utilities/winmerge_portable) | Verify selected binary / smoke test |
| 439 | WinMTR | [Current link](https://github.com/WinMTR/WinMTR-Official) | Source repository; inspect release assets | Windows 11 not established · [evidence](https://github.com/WinMTR/WinMTR-Official) | Verify support / run smoke test |
| 440 | WinObj | [Current link](https://learn.microsoft.com/en-us/sysinternals/downloads/winobj) | Binary/archive link detected; payload untested | Windows 11 not established · [evidence](https://learn.microsoft.com/en-us/sysinternals/downloads/winobj) | Verify support / run smoke test |
| 441 | WinPenguins | [Current link](https://github.com/ricky65/WinPenguins) | Source repository; inspect release assets | Publisher lists Windows 11 · [evidence](https://github.com/ricky65/WinPenguins) | Verify selected binary / smoke test |
| 442 | WinSCP | [Current link](https://winscp.net) | Download/release navigation detected | Windows 11 not established · [evidence](https://winscp.net) | Verify support / run smoke test |
| 443 | WinWGet | [Current link](https://winwget.sourceforge.io/) | Download/release navigation detected | Windows 11 not established · [evidence](https://winwget.sourceforge.io/) | Verify support / run smoke test |
| 444 | WireGuard | [Current link](https://www.wireguard.com/install) | Windows downloads seen via web retrieval | Publisher lists Windows 11 · [evidence](https://www.wireguard.com/install/) | Verify selected binary / smoke test |
| 445 | Wise Disk Cleaner | [Current link](http://www.wisecleaner.com/wise-disk-cleaner.html) | Download/release navigation detected | Windows 11 not established · [evidence](http://www.wisecleaner.com/wise-disk-cleaner.html) | Verify support / run smoke test |
| 446 | Wise Duplicate Finder | [Current link](https://www.wisecleaner.com/wise-duplicate-finder.html) | Download/release navigation detected | Windows 11 not established · [evidence](https://www.wisecleaner.com/wise-duplicate-finder.html) | Verify support / run smoke test |
| 447 | Wise Force Deleter | [Current link](http://www.wisecleaner.com/wise-force-deleter.html) | Download/release navigation detected | Windows 11 not established · [evidence](http://www.wisecleaner.com/wise-force-deleter.html) | Verify support / run smoke test |
| 448 | Wise JetSearch | [Current link](https://www.wisecleaner.com/wise-jetsearch.html) | Download/release navigation detected | Windows 11 not established · [evidence](https://www.wisecleaner.com/wise-jetsearch.html) | Verify support / run smoke test |
| 449 | Wise Program Uninstaller | [Current link](https://www.wisecleaner.com/wise-program-uninstaller.html) | Download/release navigation detected | Windows 11 not established · [evidence](https://www.wisecleaner.com/wise-program-uninstaller.html) | Verify support / run smoke test |
| 450 | Wise Registry Cleaner | [Current link](https://www.wisecleaner.com/) | Generic vendor/directory destination | Windows 11 not established · [evidence](https://www.wisecleaner.com/) | Verify support / run smoke test |
| 451 | WizFile | [Current link](https://antibody-software.com/wizfile/download/) | Unavailable: HTTP 404 | Windows 11 not established · [evidence](https://antibody-software.com/wizfile/download/) | F12 |
| 452 | WizTree | [Current link](https://diskanalyzer.com/download) | Binary/archive link detected; payload untested | Windows 11 not established · [evidence](https://diskanalyzer.com/download) | Verify support / run smoke test |
| 453 | Wizznic | [Current link](https://portableapps.com/node/65402) | Download/release navigation detected | Packager lists Windows 11 · [evidence](https://portableapps.com/download) | Verify selected binary / smoke test |
| 454 | Workrave | [Current link](https://workrave.org/) | Download/release navigation detected | Windows 11 not established · [evidence](https://workrave.org/) | Verify support / run smoke test |
| 455 | wxMP3gain | [Current link](https://github.com/cfgnunes/wxmp3gain) | Source repository; inspect release assets | Publisher lists Windows 11 · [evidence](https://github.com/cfgnunes/wxmp3gain) | Verify selected binary / smoke test |
| 456 | X-Moto | [Current link](http://xmoto.tuxfamily.org) | Binary/archive link detected; payload untested | Windows 11 not established · [evidence](http://xmoto.tuxfamily.org) | Verify support / run smoke test |
| 457 | XAMPP | [Current link](https://www.apachefriends.org) | Binary/archive link detected; payload untested | Windows 11 not established · [evidence](https://www.apachefriends.org) | Verify support / run smoke test |
| 458 | XMPlay | [Current link](https://www.un4seen.com/xmplay.html) | Binary/archive link detected; payload untested | Windows 11 not established · [evidence](https://www.un4seen.com/xmplay.html) | Verify support / run smoke test |
| 459 | XN Resource Editor | [Current link](https://stefansundin.github.io/xn_resource_editor/) | Binary/archive link detected; payload untested | Windows 11 not established · [evidence](https://stefansundin.github.io/xn_resource_editor/) | Verify support / run smoke test |
| 460 | XnConvert | [Current link](https://www.xnview.com/en/xnconvert/) | Binary/archive link detected; payload untested | Publisher lists Windows 11 · [evidence](https://www.xnview.com/en/xnconvert/) | Verify selected binary / smoke test |
| 461 | XnView | [Current link](https://www.xnview.com/en/xnview-classic/) | Binary/archive link detected; payload untested | Windows 11 not established · [evidence](https://www.xnview.com/en/xnview-classic/) | Verify support / run smoke test |
| 462 | XnView MP | [Current link](https://www.xnview.com/en/xnview-mp/) | Binary/archive link detected; payload untested | Publisher lists Windows 11 · [evidence](https://www.xnview.com/en/xnview-mp/) | Verify selected binary / smoke test |
| 463 | Xonotic | [Current link](https://xonotic.org) | Download/release navigation detected | Windows 11 not established · [evidence](https://xonotic.org) | Verify support / run smoke test |
| 464 | Xye | [Current link](https://xye.sourceforge.net/download.php) | Download/release navigation detected | Windows 11 not established · [evidence](https://xye.sourceforge.net/download.php) | Verify support / run smoke test |
| 465 | Yubico Authenticator | [Current link](http://www.yubico.com/products/yubico-authenticator/) | Binary/archive link detected; payload untested | Windows 11 not established · [evidence](http://www.yubico.com/products/yubico-authenticator/) | Verify support / run smoke test |
| 466 | YUMI exFAT | [Current link](https://pendrivelinux.com/yumi-multiboot-usb-creator/) | Binary/archive link detected; payload untested | Publisher lists Windows 11 · [evidence](https://pendrivelinux.com/yumi-multiboot-usb-creator/) | Verify selected binary / smoke test |
| 467 | YUMI Legacy | [Current link](https://pendrivelinux.com/yumi-multiboot-usb-creator/) | Binary/archive link detected; payload untested | Archived / unsupported edition · [evidence](https://pendrivelinux.com/yumi-multiboot-usb-creator/) | F15 |
| 468 | YUMI UEFI | [Current link](https://pendrivelinux.com/yumi-multiboot-usb-creator/) | Binary/archive link detected; payload untested | Archived / unsupported edition · [evidence](https://pendrivelinux.com/yumi-multiboot-usb-creator/) | F15 |
| 469 | Zaz | [Current link](https://zaz.sourceforge.net/) | Download/release navigation detected | Packager lists Windows 11 · [evidence](http://portableapps.com/apps/games/zaz_portable) | Verify selected binary / smoke test |
| 470 | Zettlr | [Current link](https://www.zettlr.com/download/) | Download/release navigation detected | Windows 11 not established · [evidence](https://www.zettlr.com/download/) | Verify support / run smoke test |
| 471 | Zim | [Current link](https://zim-wiki.org/) | Download/release navigation detected | Publisher lists Windows 11 · [evidence](https://zim-wiki.org/downloads.html) | Verify selected binary / smoke test |
| 472 | Zint Barcode Studio | [Current link](https://zint.org.uk) | Download route not established from retrieved page | Windows 11 not established · [evidence](https://zint.org.uk) | Verify support / run smoke test |
| 473 | Zoom | [Current link](https://zoom.us) | Download/release navigation detected | Windows 11 not established · [evidence](https://zoom.us) | Verify support / run smoke test |
| 474 | ZoomIt | [Current link](https://learn.microsoft.com/en-us/sysinternals/downloads/zoomit) | Binary/archive link detected; payload untested | Windows 11 not established · [evidence](https://learn.microsoft.com/en-us/sysinternals/downloads/zoomit) | Verify support / run smoke test |
| 475 | Zotero | [Current link](https://www.zotero.org/) | Download/release navigation detected | Windows 11 not established · [evidence](https://www.zotero.org/) | Verify support / run smoke test |
| 476 | Zulip | [Current link](https://zulip.com) | Download/release navigation detected | Windows 11 not established · [evidence](https://zulip.com) | Verify support / run smoke test |

## Configured URL failures and access limitations

This includes primary and alternative URLs. Each row preserves the exact configured URL, initial result and recheck. A 404/410 observed twice is stronger evidence than a single failed request. Unavailable pages require a replacement or a manual recheck; access-protected pages require browser verification before declaring them broken.

| Apps | Role | Configured URL | Initial | Recheck | Recommendation |
|---|---|---|---|---|---|
| VSCodium | Alternative: winget | `VSCodium.VSCodium` | Not an HTTP(S) URL | Not repeated | Replace URL field with a valid URL or render as a package command. |
| Resource Hacker | Primary | [http://angusj.com/resourcehacker/](http://angusj.com/resourcehacker/) | HTTP 406 | HTTP 406 | Verify in a normal browser; do not mark permanently broken from this result alone. |
| Texter | Alternative: Lifehacker Code announcement (archived) | [http://lifehacker.com/238306/lifehacker-code-texter-windows](http://lifehacker.com/238306/lifehacker-code-texter-windows) | HTTP 404 | HTTP 404 | Repair/remove destination; see app finding where supplied. |
| Simple Sudoku | Primary | [http://www.angusj.com/sudoku/](http://www.angusj.com/sudoku/) | HTTP 406 | HTTP 406 | Verify in a normal browser; do not mark permanently broken from this result alone. |
| Converber | Primary | [http://www.xyntec.com/unit-converter-download.htm](http://www.xyntec.com/unit-converter-download.htm) | HTTP 404 | HTTP 404 | Repair/remove destination; see app finding where supplied. |
| WizFile | Primary | [https://antibody-software.com/wizfile/download/](https://antibody-software.com/wizfile/download/) | HTTP 404 | HTTP 404 | Repair/remove destination; see app finding where supplied. |
| Krita | Alternative: Microsoft Store | [https://apps.microsoft.com/detail/9n8w29w2czq5](https://apps.microsoft.com/detail/9n8w29w2czq5) | HTTP 410 | HTTP 410 | Repair/remove destination; see app finding where supplied. |
| VLC Media Player | Alternative: Microsoft Store | [https://apps.microsoft.com/detail/9nblggh4vzwk](https://apps.microsoft.com/detail/9nblggh4vzwk) | HTTP 410 | HTTP 410 | Repair/remove destination; see app finding where supplied. |
| IrfanView | Alternative: Microsoft Store | [https://apps.microsoft.com/detail/9nblggh4wfpz](https://apps.microsoft.com/detail/9nblggh4wfpz) | HTTP 410 | <urlopen error timed out> | Repair/remove destination; see app finding where supplied. |
| SpeedyFox | Primary | [https://crystalidea.com/speedyfox/](https://crystalidea.com/speedyfox/) | HTTP 404 | HTTP 404 | Repair/remove destination; see app finding where supplied. |
| Cube | Primary | [https://cubeengine.com/](https://cubeengine.com/) | HTTP 502 | HTTP 502 | Verify in a normal browser; do not mark permanently broken from this result alone. |
| DSynchronize | Primary | [https://dimio.altervista.org/eng/](https://dimio.altervista.org/eng/) | HTTP 502 | HTTP 502 | Verify in a normal browser; do not mark permanently broken from this result alone. |
| WarMUX | Alternative: FSF Free Software Directory | [https://directory.fsf.org/wiki/WarMUX](https://directory.fsf.org/wiki/WarMUX) | HTTP 403 | HTTP 403 | Verify in a normal browser; do not mark permanently broken from this result alone. |
| Disk Cleaner | Primary | [https://diskcleaner.nl/](https://diskcleaner.nl/) | HTTP 502 | HTTP 502 | Verify in a normal browser; do not mark permanently broken from this result alone. |
| Dolphin | Primary | [https://dolphin-emu.org/](https://dolphin-emu.org/) | HTTP 403 | HTTP 403 | Verify in a normal browser; do not mark permanently broken from this result alone. |
| Eraser .Net; Eraser Classic | Primary | [https://eraser.heidi.ie](https://eraser.heidi.ie) | HTTP 403 | HTTP 403 | Verify in a normal browser; do not mark permanently broken from this result alone. |
| FileZilla | Primary | [https://filezilla-project.org](https://filezilla-project.org) | HTTP 403 | <urlopen error timed out> | Verify in a normal browser; do not mark permanently broken from this result alone. |
| Session | Primary | [https://getsession.org](https://getsession.org) | HTTP 200 / placeholder | Not repeated | HTTP 200 returned an unavailable placeholder; retry with browser/publisher source. |
| Celestia | Alternative: GitHub | [https://github.com/Anthony-B/Celestia-Project](https://github.com/Anthony-B/Celestia-Project) | HTTP 404 | HTTP 404 | Repair/remove destination; see app finding where supplied. |
| winLAME | Alternative: GitHub | [https://github.com/hypercubemc/winlame](https://github.com/hypercubemc/winlame) | HTTP 404 | HTTP 404 | Repair/remove destination; see app finding where supplied. |
| FUPX | Primary | [https://gurupia.wordpress.com/fupx/](https://gurupia.wordpress.com/fupx/) | HTTP 404 | <urlopen error timed out> | Repair/remove destination; see app finding where supplied. |
| ImageGlass | Primary | [https://imageglass.org/](https://imageglass.org/) | HTTP 403 | HTTP 403 | Verify in a normal browser; do not mark permanently broken from this result alone. |
| Inkscape | Primary | [https://inkscape.org](https://inkscape.org) | The read operation timed out | The read operation timed out | Verify in a normal browser; do not mark permanently broken from this result alone. |
| Kdenlive | Alternative: GitLab | [https://invent.kde.org/multimedia/kdenlive](https://invent.kde.org/multimedia/kdenlive) | HTTP 403 | HTTP 403 | Verify in a normal browser; do not mark permanently broken from this result alone. |
| MusicBrainz Picard | Primary | [https://picard.musicbrainz.org/downloads/](https://picard.musicbrainz.org/downloads/) | HTTP 200 / placeholder | Not repeated | Publisher page was independently readable through web retrieval; client limitation. |
| JPEGView | Alternative: PortableApps | [https://portableapps.com/apps/graphics_pictures/jpegview-portable](https://portableapps.com/apps/graphics_pictures/jpegview-portable) | HTTP 404 | HTTP 404 | Repair/remove destination; see app finding where supplied. |
| Smart Deblur | Alternative: PortableApps | [https://portableapps.com/apps/graphics_pictures/smartdeblur-portable](https://portableapps.com/apps/graphics_pictures/smartdeblur-portable) | HTTP 404 | HTTP 404 | Repair/remove destination; see app finding where supplied. |
| fre:ac | Alternative: PortableApps | [https://portableapps.com/apps/music_video/freac-portable](https://portableapps.com/apps/music_video/freac-portable) | HTTP 404 | HTTP 404 | Repair/remove destination; see app finding where supplied. |
| Converber | Alternative: PortableApps release | [https://portableapps.com/news/2019-08-05--converber-portable-2.3.1-released](https://portableapps.com/news/2019-08-05--converber-portable-2.3.1-released) | HTTP 404 | HTTP 404 | Repair/remove destination; see app finding where supplied. |
| PotPlayer | Primary | [https://potplayer.daum.net/](https://potplayer.daum.net/) | HTTP 502 | <urlopen error timed out> | Verify in a normal browser; do not mark permanently broken from this result alone. |
| RustDesk | Primary | [https://rustdesk.com/download/](https://rustdesk.com/download/) | HTTP 404 | <urlopen error timed out> | Repair/remove destination; see app finding where supplied. |
| PhotoFilmStrip | Alternative: SourceForge | [https://sourceforge.net/projects/photofilmstrip/](https://sourceforge.net/projects/photofilmstrip/) | HTTP 404 | HTTP 404 | Repair/remove destination; see app finding where supplied. |
| uGet | Primary | [https://ugetdm.com](https://ugetdm.com) | HTTP 502 | <urlopen error timed out> | Verify in a normal browser; do not mark permanently broken from this result alone. |
| AutoHotkey | Primary | [https://www.autohotkey.com/](https://www.autohotkey.com/) | HTTP 403 / placeholder | HTTP 403 | HTTP 200 returned an unavailable placeholder; retry with browser/publisher source. |
| BYOND | Primary | [https://www.byond.com](https://www.byond.com) | HTTP 403 / placeholder | HTTP 403 | HTTP 200 returned an unavailable placeholder; retry with browser/publisher source. |
| DOSBox | Primary | [https://www.dosbox.com/](https://www.dosbox.com/) | HTTP 403 | HTTP 403 | Verify in a normal browser; do not mark permanently broken from this result alone. |
| Paint.NET | Primary | [https://www.getpaint.net/](https://www.getpaint.net/) | HTTP 406 | HTTP 406 | Verify in a normal browser; do not mark permanently broken from this result alone. |
| WinBoard Chess | Primary | [https://www.gnu.org/software/xboard/](https://www.gnu.org/software/xboard/) | HTTP 403 | HTTP 403 | Verify in a normal browser; do not mark permanently broken from this result alone. |
| PortExpert | Primary | [https://www.kcsoftwares.com](https://www.kcsoftwares.com) | HTTP 404 | HTTP 404 | Repair/remove destination; see app finding where supplied. |
| Startup Sentinel | Primary | [https://www.kcsoftwares.com/?home](https://www.kcsoftwares.com/?home) | HTTP 404 | HTTP 404 | Repair/remove destination; see app finding where supplied. |
| WinPenguins | Alternative: Microsoft Store | [https://www.microsoft.com/store/apps/9P5Z59BMZZ5G](https://www.microsoft.com/store/apps/9P5Z59BMZZ5G) | HTTP 403 | HTTP 403 | Verify in a normal browser; do not mark permanently broken from this result alone. |
| WinFile | Alternative: Microsoft Store | [https://www.microsoft.com/store/apps/9p7vbbbc49rb?ocid=badge](https://www.microsoft.com/store/apps/9p7vbbbc49rb?ocid=badge) | HTTP 403 | HTTP 403 | Verify in a normal browser; do not mark permanently broken from this result alone. |
| Duplicate Files Finder | Primary | [https://www.mindgems.com/products/Duplicate-Files-Finder/Duplicate-Files-Finder-Download.htm](https://www.mindgems.com/products/Duplicate-Files-Finder/Duplicate-Files-Finder-Download.htm) | HTTP 404 | HTTP 404 | Repair/remove destination; see app finding where supplied. |
| Nemp | Primary | [https://www.nemp-online.de/](https://www.nemp-online.de/) | HTTP 502 | <urlopen error timed out> | Verify in a normal browser; do not mark permanently broken from this result alone. |
| Zim | Alternative: Portable Freeware Collection | [https://www.portablefreeware.com/?id=3044&ts=1612711802](https://www.portablefreeware.com/?id=3044&ts=1612711802) | HTTP 403 / placeholder | HTTP 403 | HTTP 200 returned an unavailable placeholder; retry with browser/publisher source. |
| PChat; PChat | Alternative: Portable Freeware; Primary | [https://www.portablefreeware.com/index.php?id=1731](https://www.portablefreeware.com/index.php?id=1731) | HTTP 403 / placeholder | HTTP 403 | HTTP 200 returned an unavailable placeholder; retry with browser/publisher source. |
| Database Browser | Alternative: Portable Freeware Collection listing | [https://www.portablefreeware.com/index.php?id=1915](https://www.portablefreeware.com/index.php?id=1915) | HTTP 403 / placeholder | HTTP 403 | HTTP 200 returned an unavailable placeholder; retry with browser/publisher source. |
| Checksum Control | Alternative: Portable Freeware Collection listing | [https://www.portablefreeware.com/index.php?sc=28](https://www.portablefreeware.com/index.php?sc=28) | HTTP 403 / placeholder | HTTP 403 | HTTP 200 returned an unavailable placeholder; retry with browser/publisher source. |
| Diffpdf | Primary | [https://www.qtrac.eu/diffpdf.html](https://www.qtrac.eu/diffpdf.html) | HTTP 502 | HTTP 502 | Verify in a normal browser; do not mark permanently broken from this result alone. |
| RawTherapee | Primary | [https://www.rawtherapee.com/](https://www.rawtherapee.com/) | HTTP 466 | HTTP 466 | Verify in a normal browser; do not mark permanently broken from this result alone. |
| Sauerbraten | Primary | [https://www.sauerbraten.org/](https://www.sauerbraten.org/) | HTTP 502 | HTTP 502 | Verify in a normal browser; do not mark permanently broken from this result alone. |
| SMPlayer | Primary | [https://www.smplayer.info/](https://www.smplayer.info/) | HTTP 406 | HTTP 406 | Verify in a normal browser; do not mark permanently broken from this result alone. |
| TeamViewer | Primary | [https://www.teamviewer.com](https://www.teamviewer.com) | HTTP 200 / placeholder | Not repeated | HTTP 200 returned an unavailable placeholder; retry with browser/publisher source. |
| Tor Browser | Primary | [https://www.torproject.org/download/](https://www.torproject.org/download/) | HTTP 200 / placeholder | Not repeated | HTTP 200 returned an unavailable placeholder; retry with browser/publisher source. |
| WireGuard | Primary | [https://www.wireguard.com/install](https://www.wireguard.com/install) | HTTP 200 / placeholder | Not repeated | Publisher page was independently readable through web retrieval; client limitation. |

## Old announcement pages used as primary download destinations

These are navigation/maintenance issues rather than automatically broken links. Follow the product link in the announcement, verify that its current Windows download matches the app, and then replace the primary destination.

| App | Configured primary |
|---|---|
| ADR | [https://portableapps.com/news/2017-06-08--a-dark-room-portable-1.4-released](https://portableapps.com/news/2017-06-08--a-dark-room-portable-1.4-released) |
| Checksum Control | [https://portableapps.com/news/2016-05-19--checksum-control-portable-2.4.1-released](https://portableapps.com/news/2016-05-19--checksum-control-portable-2.4.1-released) |
| DiffImg | [https://portableapps.com/news/2014-09-11--diffimg-portable-2.2.0-released](https://portableapps.com/news/2014-09-11--diffimg-portable-2.2.0-released) |
| Finance Explorer | [https://portableapps.com/news/2018-11-21--finance-explorer-portable-8.2.0-released](https://portableapps.com/news/2018-11-21--finance-explorer-portable-8.2.0-released) |
| Gopherus | [https://portableapps.com/news/2023-02-14--gopherus-portable-1.2.2-released](https://portableapps.com/news/2023-02-14--gopherus-portable-1.2.2-released) |
| Project Invincible | [https://portableapps.com/news/2013-01-06--project-invincible-portable-2.02-released](https://portableapps.com/news/2013-01-06--project-invincible-portable-2.02-released) |
| SSD-Z | [https://portableapps.com/news/2016-06-30--ssd-z-portable-16.06.29.b-released](https://portableapps.com/news/2016-06-30--ssd-z-portable-16.06.29.b-released) |
| Virtual Magnifying Glass | [https://portableapps.com/news/2013-09-24--virtual-magnifying-glass-portable-3.6-released](https://portableapps.com/news/2013-09-24--virtual-magnifying-glass-portable-3.6-released) |
| Virtual Volumes View | [https://portableapps.com/news/2021-06-16--virtual-volumes-view-portable-1.4-released](https://portableapps.com/news/2021-06-16--virtual-volumes-view-portable-1.4-released) |
| WhoDat | [https://portableapps.com/news/2013-01-25--whodat-portable-0.9-released](https://portableapps.com/news/2013-01-25--whodat-portable-0.9-released) |

## Complete alternative-link register

All configured alternatives are recorded here, including working responses. Source-code mirrors, package-index pages and archived announcements should not be presented as equivalent one-click Windows downloads.

| App | Label | Configured destination | Initial response |
|---|---|---|---|
| 4st Attack | SourceForge project (original files) | [https://sourceforge.net/projects/forcedattack/](https://sourceforge.net/projects/forcedattack/) | HTTP 200 |
| 4st Attack | Community-maintained source (GitHub) | [https://github.com/3D1T0R/4st-attack](https://github.com/3D1T0R/4st-attack) | HTTP 200 |
| Aegisub | GitHub | [https://github.com/TypesettingTools/Aegisub](https://github.com/TypesettingTools/Aegisub) | HTTP 200 |
| Ant Renamer | SourceForge (mirror) | [https://sourceforge.net/projects/ant-renamer/](https://sourceforge.net/projects/ant-renamer/) | HTTP 200 |
| Armagetron Advanced | SourceForge | [https://sourceforge.Net/projects/armagetronad/](https://sourceforge.Net/projects/armagetronad/) | HTTP 200 |
| Artha | SourceForge (mirror) | [https://sourceforge.net/projects/artha/](https://sourceforge.net/projects/artha/) | HTTP 200 |
| Atomic Tanks | PortableApps | [https://portableapps.com/apps/games/atomic_tanks_portable](https://portableapps.com/apps/games/atomic_tanks_portable) | HTTP 200 |
| Audacity | GitHub | [https://github.com/audacity/audacity](https://github.com/audacity/audacity) | HTTP 200 |
| AutoDrum | PortableApps | [https://portableapps.com/apps/music_video/autodrum-portable](https://portableapps.com/apps/music_video/autodrum-portable) | HTTP 200 |
| Avidemux | Official nightly builds | [https://avidemux.org/nightly/](https://avidemux.org/nightly/) | HTTP 200 |
| BabelMap | PortableApps release | [https://portableapps.com/news/2024-09-29--babelmap-portable-16.0.0.3-released](https://portableapps.com/news/2024-09-29--babelmap-portable-16.0.0.3-released) | HTTP 200 |
| Battle for Wesnoth | GitHub releases | [https://github.com/wesnoth/wesnoth/releases](https://github.com/wesnoth/wesnoth/releases) | HTTP 200 |
| Big Solitaires 3D | PortableApps | [https://portableapps.com/news/2012-06-18--big-solitaires-3d-portable-1.4-rev-2-released](https://portableapps.com/news/2012-06-18--big-solitaires-3d-portable-1.4-rev-2-released) | HTTP 200 |
| Big Solitaires 3D | SourceForge (mirror) | [https://sourceforge.net/projects/big3dsol/](https://sourceforge.net/projects/big3dsol/) | HTTP 200 |
| Brutal Chess | PortableApps release news | [https://portableapps.com/news/2018-08-20--brutal-chess-portable-0.5.2.2-released](https://portableapps.com/news/2018-08-20--brutal-chess-portable-0.5.2.2-released) | HTTP 200 |
| Brutal Chess | winget | [https://winget.run/pkg/BrutalChess/BrutalChess](https://winget.run/pkg/BrutalChess/BrutalChess) | HTTP 200 |
| Caesium | GitHub | [https://github.com/Lymphatus/caesium-image-compressor](https://github.com/Lymphatus/caesium-image-compressor) | HTTP 200 |
| calibre | GitHub | [https://github.com/kovidgoyal/calibre](https://github.com/kovidgoyal/calibre) | HTTP 200 |
| Canabalt | itch.io (Classic) | [https://finji.itch.io/canabalt-classic](https://finji.itch.io/canabalt-classic) | HTTP 200 |
| Capture2Text | SourceForge (mirror) | [https://sourceforge.net/projects/capture2text/](https://sourceforge.net/projects/capture2text/) | HTTP 200 |
| cdrtfe | SourceForge project files (official, demoted per policy) | [https://sourceforge.net/projects/cdrtfe/](https://sourceforge.net/projects/cdrtfe/) | HTTP 200 |
| Celestia | GitHub | [https://github.com/Anthony-B/Celestia-Project](https://github.com/Anthony-B/Celestia-Project) | HTTP 404 |
| Checksum Control | Portable Freeware Collection listing | [https://www.portablefreeware.com/index.php?sc=28](https://www.portablefreeware.com/index.php?sc=28) | HTTP 403 |
| Chromium B.S.U. | SourceForge project files (official, demoted per policy) | [https://sourceforge.net/projects/chromium-bsu/](https://sourceforge.net/projects/chromium-bsu/) | HTTP 200 |
| Clicky Gone | SourceForge project files (official, demoted per policy) | [https://sourceforge.net/projects/clickygone/](https://sourceforge.net/projects/clickygone/) | HTTP 200 |
| Colour Contrast Analyser | GitHub | [https://github.com/soluciones-inclusivas/ccae](https://github.com/soluciones-inclusivas/ccae) | HTTP 200 |
| Converber | PortableApps release | [https://portableapps.com/news/2019-08-05--converber-portable-2.3.1-released](https://portableapps.com/news/2019-08-05--converber-portable-2.3.1-released) | HTTP 404 |
| ConvertAll | SourceForge | [https://sourceforge.net/projects/convertall/](https://sourceforge.net/projects/convertall/) | HTTP 200 |
| CopyQ | GitHub | [https://github.com/git-cgallagher/copyq](https://github.com/git-cgallagher/copyq) | HTTP 200 |
| Cppcheck | GitHub | [https://github.com/cppcheck-opensource/cppcheck](https://github.com/cppcheck-opensource/cppcheck) | HTTP 200 |
| Cppcheck | cppcheck.sourceforge.io (official project site, demoted per policy) | [https://cppcheck.sourceforge.io](https://cppcheck.sourceforge.io) | HTTP 200 |
| CrystalMark Retro | PortableApps | [https://portableapps.com/apps/utilities/crystalmark-retro-portable](https://portableapps.com/apps/utilities/crystalmark-retro-portable) | HTTP 200 |
| darktable | GitHub | [https://github.com/darktable-org/darktable](https://github.com/darktable-org/darktable) | HTTP 200 |
| Database Browser | Portable Freeware Collection listing | [https://www.portablefreeware.com/index.php?id=1915](https://www.portablefreeware.com/index.php?id=1915) | HTTP 403 |
| Dave Gnukem | winget | [http://winget.run/pkg/DavidJoffe/DaveGnukem](http://winget.run/pkg/DavidJoffe/DaveGnukem) | HTTP 200 |
| DB Browser for SQLite | GitHub | [https://github.com/sqlitebrowser/sqlitebrowser](https://github.com/sqlitebrowser/sqlitebrowser) | HTTP 200 |
| Delta Chat Desktop | GitHub | [https://github.com/deltachat/deltachat-desktop](https://github.com/deltachat/deltachat-desktop) | HTTP 200 |
| Ditto | PortableApps | [https://portableapps.com/apps/utilities/ditto_portable](https://portableapps.com/apps/utilities/ditto_portable) | HTTP 200 |
| DM2 | SourceForge project page (migrated to GitHub, demoted per policy) | [https://sourceforge.net/projects/dm2/](https://sourceforge.net/projects/dm2/) | HTTP 200 |
| Domino-Chain | PortableApps release | [https://portableapps.com/news/2024-05-06--domino-chain-portable-1.1-released](https://portableapps.com/news/2024-05-06--domino-chain-portable-1.1-released) | HTTP 200 |
| Don't Panic! | PortableApps release | [https://portableapps.com/news/2012-10-03--dont-panic-portable-2.0.1-released](https://portableapps.com/news/2012-10-03--dont-panic-portable-2.0.1-released) | HTTP 200 |
| DTaskManager | PortableApps | [https://portableapps.com/apps/utilities/dtaskmanager_portable](https://portableapps.com/apps/utilities/dtaskmanager_portable) | HTTP 200 |
| DVDStyler | GitHub (official repo) | [https://github.com/ntxalex/DVDStyler](https://github.com/ntxalex/DVDStyler) | HTTP 200 |
| DVDStyler | FossHub (official mirror, demoted per policy) | [https://www.fosshub.com/DVDStyler.html](https://www.fosshub.com/DVDStyler.html) | HTTP 200 |
| EarTrumpet | GitHub | [https://github.com/File-New-Project/EarTrumpet](https://github.com/File-New-Project/EarTrumpet) | HTTP 200 |
| EraserDrop | PortableApps | [https://portableapps.com/apps/security/eraserdrop-portable](https://portableapps.com/apps/security/eraserdrop-portable) | HTTP 200 |
| FeedRoller | TechSpot | [https://www.techspot.com/downloads/downloadnow/5767/?evp=e767cd2d8c7a9c58801c64c57abb5692&file=6731](https://www.techspot.com/downloads/downloadnow/5767/?evp=e767cd2d8c7a9c58801c64c57abb5692&file=6731) | HTTP 200 |
| Ferdium | PortableApps | [https://portableapps.com/news/2025-05-26--ferdium-portable-7.1.0-released](https://portableapps.com/news/2025-05-26--ferdium-portable-7.1.0-released) | HTTP 200 |
| FileAlyzer | PortableApps (2012 release announcement) | [https://portableapps.com/news/2012-10-22--filealyzer-portable-2.0.5.57-released](https://portableapps.com/news/2012-10-22--filealyzer-portable-2.0.5.57-released) | HTTP 200 |
| FileOptimizer | SourceForge (developer page) | [https://nikkhokkho.sourceforge.io/static.php?page=FileOptimizer](https://nikkhokkho.sourceforge.io/static.php?page=FileOptimizer) | HTTP 200 |
| Flow Launcher | GitHub | [https://github.com/Flow-Launcher/Flow.Launcher](https://github.com/Flow-Launcher/Flow.Launcher) | HTTP 200 |
| FontForge | GitHub Releases | [https://github.com/fontforge/fontforge/releases](https://github.com/fontforge/fontforge/releases) | HTTP 200 |
| FontForge | PortableApps | [http://portableapps.com/apps/utilities/fontforge-portable](http://portableapps.com/apps/utilities/fontforge-portable) | HTTP 200 |
| Fotografix | GitHub | [https://github.com/lmadhavan/fotografix](https://github.com/lmadhavan/fotografix) | HTTP 200 |
| fre:ac | PortableApps | [https://portableapps.com/apps/music_video/freac-portable](https://portableapps.com/apps/music_video/freac-portable) | HTTP 404 |
| Frhed | SourceForge (developer page) | [https://sourceforge.net/projects/frhed/](https://sourceforge.net/projects/frhed/) | HTTP 200 |
| Geany | GitHub Releases | [https://github.com/geany/geany/releases](https://github.com/geany/geany/releases) | HTTP 200 |
| GIMP | GitHub | [https://github.com/GNOME/gimp](https://github.com/GNOME/gimp) | HTTP 200 |
| GoldenDict | GoldenDict-ng (active fork) on GitHub | [https://github.com/xiaoyifang/goldendict-ng](https://github.com/xiaoyifang/goldendict-ng) | HTTP 200 |
| Golly | SourceForge (developer page) | [https://golly.sourceforge.net/](https://golly.sourceforge.net/) | HTTP 200 |
| Gopherus | SourceForge (developer page) | [https://gopherus.sourceforge.io](https://gopherus.sourceforge.io) | HTTP 200 |
| GPG Plugin | GnuPG (upstream) | [https://www.gnupg.org/](https://www.gnupg.org/) | HTTP 200 |
| gPodder | GitHub | [https://github.com/gpodder/gpodder](https://github.com/gpodder/gpodder) | HTTP 200 |
| Greenshot | GitHub | [https://github.com/greenshot](https://github.com/greenshot) | HTTP 200 |
| grepWin | GitHub | [https://github.com/stefankueng/grepWin](https://github.com/stefankueng/grepWin) | HTTP 200 |
| Gridy | AfterDawn | [https://www.afterdawn.com/software/desktop/misc_desktop_tools/gridy.cfm](https://www.afterdawn.com/software/desktop/misc_desktop_tools/gridy.cfm) | HTTP 200 |
| gVim | Vim Windows installer releases (GitHub) | [https://github.com/vim/vim-win32-installer/releases](https://github.com/vim/vim-win32-installer/releases) | HTTP 200 |
| HandBrake | GitHub | [https://github.com/HandBrake/HandBrake](https://github.com/HandBrake/HandBrake) | HTTP 200 |
| Hex-a-Hop | Hex-a-Hop project page (SourceForge, demoted) | [https://sourceforge.net/projects/hexahop/](https://sourceforge.net/projects/hexahop/) | HTTP 200 |
| I Have No Tomatoes | Developer site (SourceForge, demoted) | [http://tomatoes.sourceforge.net](http://tomatoes.sourceforge.net) | HTTP 200 |
| IceBreaker | PortableApps release news | [https://portableapps.com/news/2021-05-02--icebreaker-portable-2.2.0-released](https://portableapps.com/news/2021-05-02--icebreaker-portable-2.2.0-released) | HTTP 200 |
| IDPhotoStudio | PortableApps | [https://portableapps.com/apps/graphics_pictures/idphotostudio-portable](https://portableapps.com/apps/graphics_pictures/idphotostudio-portable) | HTTP 200 |
| ImageGlass | GitHub | [https://github.com/d2phap/ImageGlass](https://github.com/d2phap/ImageGlass) | HTTP 200 |
| ImageGlass | Microsoft Store | [https://apps.microsoft.com/detail/9N33VZK3C7TH](https://apps.microsoft.com/detail/9N33VZK3C7TH) | HTTP 200 |
| IniTranslator | Developer site (SourceForge, demoted) | [http://initranslator.sourceforge.net](http://initranslator.sourceforge.net) | HTTP 200 |
| InnoUnpacker | PortableApps release | [https://portableapps.com/news/2026-05-05--innounpacker-portable-2.2.9-released](https://portableapps.com/news/2026-05-05--innounpacker-portable-2.2.9-released) | HTTP 200 |
| InnoUnpacker | InnoUnpacker GitHub project | [https://github.com/jrathlev/innounpacker-windows-gui](https://github.com/jrathlev/innounpacker-windows-gui) | HTTP 200 |
| IrfanView | PortableApps | [https://portableapps.com/apps/graphics_pictures/irfanview_portable](https://portableapps.com/apps/graphics_pictures/irfanview_portable) | HTTP 200 |
| IrfanView | Microsoft Store | [https://apps.microsoft.com/detail/9nblggh4wfpz](https://apps.microsoft.com/detail/9nblggh4wfpz) | HTTP 410 |
| Jooleem | Developer site (SourceForge, demoted) | [http://jooleem.sourceforge.net/](http://jooleem.sourceforge.net/) | HTTP 200 |
| Joplin | GitHub releases | [https://github.com/laurent22/joplin/releases](https://github.com/laurent22/joplin/releases) | HTTP 200 |
| JPEGView | PortableApps | [https://portableapps.com/apps/graphics_pictures/jpegview-portable](https://portableapps.com/apps/graphics_pictures/jpegview-portable) | HTTP 404 |
| JPEGView | Chocolatey | [https://community.chocolatey.org/packages/jpegview](https://community.chocolatey.org/packages/jpegview) | HTTP 200 |
| Kdenlive | GitLab | [https://invent.kde.org/multimedia/kdenlive](https://invent.kde.org/multimedia/kdenlive) | HTTP 403 |
| Krita | Microsoft Store | [https://apps.microsoft.com/detail/9n8w29w2czq5](https://apps.microsoft.com/detail/9n8w29w2czq5) | HTTP 410 |
| KVIrc | KVIrc GitHub project | [https://github.com/kvirc/KVIrc](https://github.com/kvirc/KVIrc) | HTTP 200 |
| LameXP | GitHub | [https://github.com/lordmulder/LameXP](https://github.com/lordmulder/LameXP) | HTTP 200 |
| LameXP | PortableApps | [https://portableapps.com/apps/music_video/lamexp-portable](https://portableapps.com/apps/music_video/lamexp-portable) | HTTP 200 |
| LAN Messenger | Developer site (SourceForge, demoted) | [https://lanmsngr.sourceforge.net/](https://lanmsngr.sourceforge.net/) | HTTP 200 |
| LazPaint | GitHub | [https://github.com/bgrabitmap/lazpaint](https://github.com/bgrabitmap/lazpaint) | HTTP 200 |
| LBreakout2 | LGames project page (SourceForge, demoted) | [https://lgames.sourceforge.net/index.php?project=LBreakout2](https://lgames.sourceforge.net/index.php?project=LBreakout2) | HTTP 200 |
| LMarbles | PortableApps release news | [https://portableapps.com/news/2010-12-28_-_lmarbles_portable_1.0.6](https://portableapps.com/news/2010-12-28_-_lmarbles_portable_1.0.6) | HTTP 200 |
| LMMS | GitHub | [https://github.com/LMMS/lmms](https://github.com/LMMS/lmms) | HTTP 200 |
| LocalSend | Source code (GitHub) | [https://github.com/localsend/localsend](https://github.com/localsend/localsend) | HTTP 200 |
| Lossless Cut | GitHub | [https://github.com/mifi/lossless-cut](https://github.com/mifi/lossless-cut) | HTTP 200 |
| Lucas Chess | SourceForge | [http://sourceforge.net/projects/lucaschessr/](http://sourceforge.net/projects/lucaschessr/) | HTTP 200 |
| MahJongg Solitaire 3D | PortableApps release | [https://portableapps.com/apps/games/mahjongg-solitaire-3d-portable](https://portableapps.com/apps/games/mahjongg-solitaire-3d-portable) | HTTP 200 |
| MahJongg Solitaire 3D | Old developer page | [http://www.reto-schoelly.de/mahjongg3d/](http://www.reto-schoelly.de/mahjongg3d/) | HTTP 200 |
| ManiaDrive | SourceForge project | [https://sourceforge.net/projects/maniadrive/](https://sourceforge.net/projects/maniadrive/) | HTTP 200 |
| MBox Viewer | GitHub | [https://github.com/eneam/mboxviewer](https://github.com/eneam/mboxviewer) | HTTP 200 |
| MBox Viewer | PortableApps | [https://portableapps.com/apps/utilities/mbox-viewer-portable](https://portableapps.com/apps/utilities/mbox-viewer-portable) | HTTP 200 |
| MBox Viewer | SourceForge | [https://sourceforge.net/projects/mbox-viewer/](https://sourceforge.net/projects/mbox-viewer/) | HTTP 200 |
| MilkyTracker | GitHub | [https://github.com/milkytracker/MilkyTracker](https://github.com/milkytracker/MilkyTracker) | HTTP 200 |
| Miranda NG | GitHub | [https://github.com/miranda-ng/miranda-ng](https://github.com/miranda-ng/miranda-ng) | HTTP 200 |
| Mixxx | GitHub | [https://github.com/mixxxdj/mixxx](https://github.com/mixxxdj/mixxx) | HTTP 200 |
| MKVToolNix | GitLab | [https://gitlab.com/mbunkus/mkvtoolnix](https://gitlab.com/mbunkus/mkvtoolnix) | HTTP 200 |
| MPV | GitHub | [https://github.com/mpv-player/mpv](https://github.com/mpv-player/mpv) | HTTP 200 |
| MuseScore | GitHub | [https://github.com/MuseScore/MuseScore](https://github.com/MuseScore/MuseScore) | HTTP 200 |
| MusicBrainz Picard | GitHub | [https://github.com/metabrainz/picard](https://github.com/metabrainz/picard) | HTTP 200 |
| MyPaint | GitHub | [https://github.com/mypaint/mypaint](https://github.com/mypaint/mypaint) | HTTP 200 |
| Nemp | GitHub | [https://github.com/DanielGausi/Nemp](https://github.com/DanielGausi/Nemp) | HTTP 200 |
| netPanzer | Official site | [https://netpanzer.io](https://netpanzer.io) | HTTP 200 |
| Neverball | PortableApps | [https://portableapps.com/apps/games/neverball_portable](https://portableapps.com/apps/games/neverball_portable) | HTTP 200 |
| Notepad++ | GitHub releases | [https://github.com/notepad-plus-plus/notepad-plus-plus/releases](https://github.com/notepad-plus-plus/notepad-plus-plus/releases) | HTTP 200 |
| Notepad2-mod | GitHub | [https://github.com/XhmikosR/notepad2-mod](https://github.com/XhmikosR/notepad2-mod) | HTTP 200 |
| Notes | GitHub | [https://github.com/nuttyartist/notes](https://github.com/nuttyartist/notes) | HTTP 200 |
| OBS Studio | GitHub | [https://github.com/obsproject/obs-studio](https://github.com/obsproject/obs-studio) | HTTP 200 |
| OpenShot | GitHub | [https://github.com/OpenShot/openshot-qt](https://github.com/OpenShot/openshot-qt) | HTTP 200 |
| OpenTTD | GitHub releases | [https://github.com/OpenTTD/OpenTTD/releases](https://github.com/OpenTTD/OpenTTD/releases) | HTTP 200 |
| Paint.NET | Microsoft Store | [https://apps.microsoft.com/detail/9nbhcs1lx4r0](https://apps.microsoft.com/detail/9nbhcs1lx4r0) | HTTP 200 |
| Password Safe | Source and releases (GitHub) | [https://github.com/pwsafe/pwsafe](https://github.com/pwsafe/pwsafe) | HTTP 200 |
| PChat | Portable Freeware | [https://www.portablefreeware.com/index.php?id=1731](https://www.portablefreeware.com/index.php?id=1731) | HTTP 403 |
| PhotoDemon | GitHub | [https://github.com/tannerhelland/PhotoDemon](https://github.com/tannerhelland/PhotoDemon) | HTTP 200 |
| PhotoFilmStrip | SourceForge | [https://sourceforge.net/projects/photofilmstrip/](https://sourceforge.net/projects/photofilmstrip/) | HTTP 404 |
| Pingus | GitHub | [https://github.com/Pingus/](https://github.com/Pingus/) | HTTP 200 |
| Pinta | GitHub | [https://github.com/PintaProject/Pinta](https://github.com/PintaProject/Pinta) | HTTP 200 |
| PNotes | SourceForge (developer project site) | [https://pnotes.sourceforge.io/](https://pnotes.sourceforge.io/) | HTTP 200 |
| PokerTH | GitHub | [https://github.com/pokerth/pokerth](https://github.com/pokerth/pokerth) | HTTP 200 |
| PortableApps.com Platform | SourceForge | [https://sourceforge.net/projects/portableapps/?source=sfspproj](https://sourceforge.net/projects/portableapps/?source=sfspproj) | HTTP 200 |
| Project Invincible | SourceForge (developer project site) | [https://sourceforge.net/projects/project-invincible/](https://sourceforge.net/projects/project-invincible/) | HTTP 200 |
| Puzzle Collection | PortableApps | [https://portableapps.com/apps/games/puzzle_collection_portable](https://portableapps.com/apps/games/puzzle_collection_portable) | HTTP 200 |
| Qalculate | Official site | [http://qalculate.github.io/](http://qalculate.github.io/) | HTTP 200 |
| Quick Solitaire | PortableApps | [https://portableapps.com/apps/games/quick_solitaire_portable](https://portableapps.com/apps/games/quick_solitaire_portable) | HTTP 200 |
| r3dfox | PortableApps | [https://portableapps.com/news/2025-07-31--r3dfox-portable-140.0.4-released](https://portableapps.com/news/2025-07-31--r3dfox-portable-140.0.4-released) | HTTP 200 |
| Rapid CRC Unicode | PortableApps | [https://portableapps.com/news/2024-05-11--rapid-crc-unicode-portable-0.3.40-released](https://portableapps.com/news/2024-05-11--rapid-crc-unicode-portable-0.3.40-released) | HTTP 200 |
| RawTherapee | GitHub | [https://github.com/Beep6581/RawTherapee](https://github.com/Beep6581/RawTherapee) | HTTP 200 |
| RBTray | SourceForge (original) | [https://sourceforge.net/projects/rbtray/files/](https://sourceforge.net/projects/rbtray/files/) | HTTP 200 |
| Resource Hacker | PortableApps | [https://portableapps.com/apps/utilities/resource-hacker-portable](https://portableapps.com/apps/utilities/resource-hacker-portable) | HTTP 200 |
| RetroShare | PortableApps | [https://portableapps.com/node/66914](https://portableapps.com/node/66914) | HTTP 200 |
| RisohEditor | GitHub | [https://github.com/katahiromz/RisohEditor](https://github.com/katahiromz/RisohEditor) | HTTP 200 |
| ScreenToGif | GitHub | [https://github.com/NickeManarin/ScreenToGif/](https://github.com/NickeManarin/ScreenToGif/) | HTTP 200 |
| ShareX | GitHub | [https://github.com/ShareX/ShareX](https://github.com/ShareX/ShareX) | HTTP 200 |
| Shortcuts Search And Replace | PortableApps | [https://portableapps.com/news/2024-05-11--shortcuts-search-and-replace-portable-1.14.0--released](https://portableapps.com/news/2024-05-11--shortcuts-search-and-replace-portable-1.14.0--released) | HTTP 200 |
| Shotcut | GitHub | [https://github.com/mltframework/shotcut](https://github.com/mltframework/shotcut) | HTTP 200 |
| Sigil | GitHub | [https://github.com/Sigil-Ebook/Sigil](https://github.com/Sigil-Ebook/Sigil) | HTTP 200 |
| Sigil | Chocolatey | [https://community.chocolatey.org/packages/Sigil](https://community.chocolatey.org/packages/Sigil) | HTTP 200 |
| Sigil | winget | [https://winstall.app/apps/Sigil-Ebook.Sigil](https://winstall.app/apps/Sigil-Ebook.Sigil) | HTTP 200 |
| Simple Sudoku | PortableApps | [https://portableapps.com/news/2017-12-11--simple-sudoku-portable-4.2n-released](https://portableapps.com/news/2017-12-11--simple-sudoku-portable-4.2n-released) | HTTP 200 |
| Smart Deblur | PortableApps | [https://portableapps.com/apps/graphics_pictures/smartdeblur-portable](https://portableapps.com/apps/graphics_pictures/smartdeblur-portable) | HTTP 404 |
| SnapTimer | PortableApps | [http://portableapps.com/apps/utilities/snaptimer-portable](http://portableapps.com/apps/utilities/snaptimer-portable) | HTTP 200 |
| SpeedyFox | PortableApps release | [https://portableapps.com/news/2020-10-12--speedyfox-portable-2.0.30-released](https://portableapps.com/news/2020-10-12--speedyfox-portable-2.0.30-released) | HTTP 200 |
| SSD-Z | Guru3D | [https://www.guru3d.com/download/ssd-z-download/?print](https://www.guru3d.com/download/ssd-z-download/?print) | HTTP 200 |
| StackNotes | SourceForge (developer project site) | [https://sourceforge.net/p/stacknotes/](https://sourceforge.net/p/stacknotes/) | HTTP 200 |
| Startup Sentinel | PortableApps | [https://portableapps.com/node/64610](https://portableapps.com/node/64610) | HTTP 200 |
| Stellarium | GitHub | [https://github.com/Stellarium/stellarium](https://github.com/Stellarium/stellarium) | HTTP 200 |
| Strawberry Music Player | GitHub | [https://github.com/strawberrymusicplayer/strawberry](https://github.com/strawberrymusicplayer/strawberry) | HTTP 200 |
| StreamWriter | PortableApps | [https://portableapps.com/apps/music_video/streamwriter-portable](https://portableapps.com/apps/music_video/streamwriter-portable) | HTTP 200 |
| Sumatra PDF | GitHub | [https://github.com/sumatrapdfreader/sumatrapdf](https://github.com/sumatrapdfreader/sumatrapdf) | HTTP 200 |
| Sumatra PDF | PortableApps | [https://portableapps.com/apps/office/sumatra_pdf_portable](https://portableapps.com/apps/office/sumatra_pdf_portable) | HTTP 200 |
| Supermium | PortableApps | [https://portableapps.com/node/70710](https://portableapps.com/node/70710) | HTTP 200 |
| SuperTuxKart | GitHub Releases | [https://github.com/supertuxkart/stk-code/releases/latest](https://github.com/supertuxkart/stk-code/releases/latest) | HTTP 200 |
| SWI-Prolog | GitHub | [https://github.com/SWI-Prolog](https://github.com/SWI-Prolog) | HTTP 200 |
| T^3 | SourceForge project | [http://sourceforge.net/projects/t-3/](http://sourceforge.net/projects/t-3/) | HTTP 200 |
| TCPView | winget | [https://winstall.app/apps/Microsoft.Sysinternals.TCPView](https://winstall.app/apps/Microsoft.Sysinternals.TCPView) | HTTP 200 |
| Texter | Lifehacker Code announcement (archived) | [http://lifehacker.com/238306/lifehacker-code-texter-windows](http://lifehacker.com/238306/lifehacker-code-texter-windows) | HTTP 404 |
| Textify | PortableApps release | [https://portableapps.com/news/2022-05-30--textify-portable-1.10.1-released](https://portableapps.com/news/2022-05-30--textify-portable-1.10.1-released) | HTTP 200 |
| Tick5 | PortableApps release | [https://portableapps.com/news/2015-06-07--tick5-portable-1.0-rev-2-released](https://portableapps.com/news/2015-06-07--tick5-portable-1.0-rev-2-released) | HTTP 200 |
| TidyTabs | Official MSI download | [https://www.nurgo-software.com/download/TidyTabs.msi](https://www.nurgo-software.com/download/TidyTabs.msi) | HTTP 200 |
| Tile World | GitHub fork (mjfwalsh) | [https://github.com/mjfwalsh/tworld](https://github.com/mjfwalsh/tworld) | HTTP 200 |
| Twin Distress | SourceForge project | [https://sourceforge.net/p/twind/news/2004/07/twin-distress-110-released/history](https://sourceforge.net/p/twind/news/2004/07/twin-distress-110-released/history) | HTTP 200 |
| TyperTask | PortableApps release | [https://portableapps.com/news/2019-08-05--typertask-portable-1.20-rev-3-released](https://portableapps.com/news/2019-08-05--typertask-portable-1.20-rev-3-released) | HTTP 200 |
| Unicodia | GitHub Releases | [https://github.com/Mercury13/unicodia/releases](https://github.com/Mercury13/unicodia/releases) | HTTP 200 |
| Unicodia | PortableApps release | [https://portableapps.com/news/2024-05-20--unicodia-portable-2.7.1-released](https://portableapps.com/news/2024-05-20--unicodia-portable-2.7.1-released) | HTTP 200 |
| UUID-GUID Generator | PortableApps release | [https://portableapps.com/news/2023-11-06--uuid-guid-generator-portable-3.0-released](https://portableapps.com/news/2023-11-06--uuid-guid-generator-portable-3.0-released) | HTTP 200 |
| Virtual Magnifying Glass | SourceForge project site | [http://magnifier.sourceforge.net/](http://magnifier.sourceforge.net/) | HTTP 200 |
| Virtual Volumes View | SourceForge project | [https://sourceforge.net/projects/vvvapp/](https://sourceforge.net/projects/vvvapp/) | HTTP 200 |
| VirtuaWin | SourceForge project page | [http://sourceforge.net/projects/virtuawin/](http://sourceforge.net/projects/virtuawin/) | HTTP 200 |
| VLC Media Player | Microsoft Store | [https://apps.microsoft.com/detail/9nblggh4vzwk](https://apps.microsoft.com/detail/9nblggh4vzwk) | HTTP 410 |
| VSCodium | winget | `VSCodium.VSCodium` | Not an HTTP(S) URL |
| WackGet | GitHub (fabianod/wackget) modified source | [https://github.com/fabianod/wackget](https://github.com/fabianod/wackget) | HTTP 200 |
| WarMUX | FSF Free Software Directory | [https://directory.fsf.org/wiki/WarMUX](https://directory.fsf.org/wiki/WarMUX) | HTTP 403 |
| WarMUX | GitHub (former author's code) | [https://github.com/yekcim/warmux](https://github.com/yekcim/warmux) | HTTP 200 |
| Warzone 2100 | GitHub Releases | [https://github.com/Warzone2100/warzone2100/releases](https://github.com/Warzone2100/warzone2100/releases) | HTTP 200 |
| WAtomic | SourceForge project page | [https://sourceforge.net/projects/watomic/](https://sourceforge.net/projects/watomic/) | HTTP 200 |
| Winaero Tweaker | Official direct download (zip) | [https://winaerotweaker.com/download/winaerotweaker.zip](https://winaerotweaker.com/download/winaerotweaker.zip) | HTTP 200 |
| WinFile | Chocolatey | [https://chocolatey.org/packages/winfile](https://chocolatey.org/packages/winfile) | HTTP 200 |
| WinFile | Microsoft Store | [https://www.microsoft.com/store/apps/9p7vbbbc49rb?ocid=badge](https://www.microsoft.com/store/apps/9p7vbbbc49rb?ocid=badge) | HTTP 403 |
| winLAME | GitHub | [https://github.com/hypercubemc/winlame](https://github.com/hypercubemc/winlame) | HTTP 404 |
| winMd5Sum | NullRiver (original developer) | [http://www.nullriver.com/products/winmd5sum](http://www.nullriver.com/products/winmd5sum) | HTTP 200 |
| WinMerge | WinMerge Portable | [https://portableapps.com/apps/utilities/winmerge_portable](https://portableapps.com/apps/utilities/winmerge_portable) | HTTP 200 |
| WinMerge | GitHub Releases | [https://github.com/WinMerge/winmerge/releases/latest](https://github.com/WinMerge/winmerge/releases/latest) | HTTP 200 |
| WinPenguins | Microsoft Store | [https://www.microsoft.com/store/apps/9P5Z59BMZZ5G](https://www.microsoft.com/store/apps/9P5Z59BMZZ5G) | HTTP 403 |
| Wizznic | SourceForge project files | [https://sourceforge.net/projects/wizznic/files/](https://sourceforge.net/projects/wizznic/files/) | HTTP 200 |
| X-Moto | PortableApps | [https://portableapps.com/news/2023-03-23--x-moto-portable-0.6.2-released](https://portableapps.com/news/2023-03-23--x-moto-portable-0.6.2-released) | HTTP 200 |
| XN Resource Editor | SourceForge mirror | [https://sourceforge.net/projects/xn-resource-editor/support](https://sourceforge.net/projects/xn-resource-editor/support) | HTTP 200 |
| Xye | SourceForge project page | [https://sourceforge.net/projects/xye/](https://sourceforge.net/projects/xye/) | HTTP 200 |
| Zaz | Zaz Portable | [http://portableapps.com/apps/games/zaz_portable](http://portableapps.com/apps/games/zaz_portable) | HTTP 200 |
| Zettlr | Chocolatey | [https://community.chocolatey.org/packages/zettlr/](https://community.chocolatey.org/packages/zettlr/) | HTTP 200 |
| Zim | Portable Freeware Collection | [https://www.portablefreeware.com/?id=3044&ts=1612711802](https://www.portablefreeware.com/?id=3044&ts=1612711802) | HTTP 403 |
| Zint Barcode Studio | GitHub | [https://github.com/zint/zint](https://github.com/zint/zint) | HTTP 200 |
| ZoomIt | Microsoft PowerToys on GitHub (ZoomIt module) | [https://github.com/microsoft/PowerToys](https://github.com/microsoft/PowerToys) | HTTP 200 |

## Reproducibility and completion criteria

- Catalogue snapshot SHA-256: `b8e5de175165efe385912e7a637528ea25b4a13b66e6c89d896afd7ccd645811`.
- Windows entries: 476. Primary link occurrences: 476. Alternative link occurrences: 201. Unique configured destinations: 661.
- Additional automatically selected download/navigation destinations retrieved: 232. These were discovery candidates; unrelated links or OS-topic pages were excluded from compatibility claims.
- The primary register provides all 476 configured primary URLs; the alternative register supplies every configured alternative. The failures register preserves initial and repeated errors.
- This audit is complete as a catalogue-wide URL/evidence review, but **Windows 11 execution verification remains outstanding**. Before declaring every app verified, close each unresolved download route, obtain app-specific support evidence or a documented smoke test for every “not established” entry, and resolve the known incompatible/archived/paid-source cases.
