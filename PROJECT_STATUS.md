# Portfolio CMS — Project Status

Updated: 2026-11-15
Repository: `oriolroigescobedo/oriolroigescobedo.github.io`
Working branch: `feature/portfolio-cms-phase-4`
Production branch: `main` — **DO NOT MODIFY**

## Objective
Preserve the original public portfolio while gradually enabling on-page direct visual edits, dynamic navigation/sections, four locales and secure GitHub-based publication.

## Phase 4 — authenticated development publication

- Verified the Phase 3 branch head `91c226f9a78d3330f93deeba319437c374c9a065` against GitHub and confirmed the successful Phase 3 workflow run [43542459946](https://github.com/oriolroigescobedo/oriolroigescobedo.github.io/actions/runs/43542459946). Phase 4 was branched from that head.
- Added a separate same-origin HTTPS editor and publisher service using GitHub App OAuth, PKCE, an allowlisted account and installation, temporary server-side sessions, and GitHub repository Contents access. A reviewed v3 snapshot can be committed only to `cms/content/published.v3.json` on `feature/portfolio-cms-phase-4`. The GitHub head precondition prevents overwriting a concurrent change.
- The existing visual editing, local draft storage, v1 migration and v3 import/export are retained. The development snapshot is a publicly readable commit in the portfolio repository. The normal site does not load that snapshot. Deployment or a public release remains separate work.
- [GitHub Actions run 43744433351](https://github.com/oriolroigescobedo/oriolroigescobedo.github.io/actions/runs/43744433351) passed on `9a13904902ef03ffb027ac2c98c8eb54deee7194`. It verified exact baseline HTML reversal, CSS/JS preservation, 20 identical image files, all 400 baseline translations, seven publisher suites, Chromium publication tests at 1440 and 390 pixels, Phase 3 integration, 16 Phase 2 viewport/locale/theme cases and 16/16 visual comparisons with `pixel_diff=0` under the existing metric.
- Local Chrome on Windows passed the publisher and both editor integration suites. In its visual comparison, the DOM matched in all 16 cases and 15/16 screenshots had zero measured differences. The 1440px French light screenshot differed at 418 portrait pixels (0.0058% of pixels) despite identical source image bytes. GitHub Actions' Chromium run passed that case.
- GitHub confirmed production `main` still points to `8a51574bd49bb8a28b5a2e8815cc48e491fd0f26` after Phase 4. The development workflow runs validation only. The Pages settings were unavailable through the public API and remain an owner-side setup check.
- Local startup requires a configured HTTPS host and a GitHub App installation. Automated publisher tests use an API double. Real GitHub sign-in and real draft publication require the owner's setup and a specific confirmation. See [cms/README.md](cms/README.md) for setup, revocation and recovery.
- Localization remains pending for the English-only advanced panel and publication dialog. This can affect understanding of the confirmation step without changing server access controls. Manual keyboard, focus, screen-reader and responsive acceptance is still pending. The public renderer for committed snapshots is also pending.

## Phase 3 — implementation checkpoint (2026-11-14)
- Started from verified Phase 2 head `fe1f007755716b6ebd0421ceabe40ceba6b9b8e6`. The latest Phase 2 run is **43539708807**, successful (newer than the supplied run 43539500137).
- Added `cms/advanced.js`, integrating the existing editor with version-3 drafts and the evolved `cms/content.schema.json`. Original site JavaScript/CSS and all twenty image files remain unchanged.
- Implemented component-based entry creation, deletion and ordering; custom sections; section deletion/ordering; automatic sidebar anchors, numbering, active-section observation and mobile navigation.
- Added contextual rich-text, link destination and image/alt editors, local raster-image upload, and compatible-component link creation/removal. Existing interactive controls remain separate from editable content.
- Added independent locale fields, missing-translation indicators, shared structural order, migration of v1 drafts, JSON import/export, save/reload and cancel-to-saved-draft.
- Local Chrome: the existing Phase 2 regression passed all 16 viewport/locale/theme combinations. Exact baseline assertions passed (markup reversal, unchanged original CSS/JS, twenty image byte checks, 400 translation values).
- **GitHub Actions run [43542459946](https://github.com/oriolroigescobedo/oriolroigescobedo.github.io/actions/runs/43542459946) succeeded** against code commit `bed078238d1ccff6731d840773b31fb05f66b8aa`.
- CI passed real Chromium integration tests at 1440px and 390px: link/image edits, four-locale new entries, ordering, sidebar numbering, stable IDs, draft reload/cancel, theme/accent controls, auto-scroll, mobile navigation, JSON round-trip, rich formatting, link creation/deletion, raster upload, malformed/unsafe import rejection, section deletion/restoration and v1 migration. No JavaScript page errors were observed in these checks.
- CI passed the existing 16-case Phase 2 interaction matrix and **16/16 strict public-page screenshot comparisons with zero differing pixels**. The prior 1% visual tolerance was removed; the test now requires zero and waits for fonts/transitions to settle. Local Chrome also passed all 16 zero-difference comparisons; its measurements are saved in `tests/browser-parity-results.json`.
- Implementation commits: `46e93738c3335624b30df94ea1b721c2afdefb4e` (model/editor) and `bed078238d1ccff6731d840773b31fb05f66b8aa` (tests/documentation). The final documentation-only checkpoint does not change the tested application code.
- Rechecked the production head after implementation: `main` remains `8a51574bd49bb8a28b5a2e8815cc48e491fd0f26`. No merge or public deployment was performed.

### Phase 3 boundaries / remaining work
- This is local draft editing only. The static public page ignores draft state. No OAuth, cloud image storage, remote publication or credentials are implemented.
- Trusted components are adapted from preserved original markup; draft JSON stores template identities and field overrides, never arbitrary component HTML. A future publishing renderer must materialize these drafts server-side before release.
- Existing education/experience/interest designs are reused; custom sections use the original section heading and experience-entry style. Home is retained as the required anchor. Moving entries between different section types and arbitrary layout editing are not included.
- New content remains blank in other locales and is marked as missing; there is no generated translation. Original locale dictionaries are preserved, including their pre-existing fallback text.
- Advanced panel labels currently use English. Full panel localization and a formal accessibility audit remain follow-up work.
- Uploads accept raster images up to 2 MB. Browser storage quotas still apply; export JSON before changing devices. New blank image slots should be populated before publication.
- Authentication/publication remains Phase 4; `main` and the public domain must not be modified without explicit approval.

## Baseline and inspection
- `main` commit at baseline: `8a51574bd49bb8a28b5a2e8815cc48e491fd0f26`
- Original file: `index.html` (3,546,480 bytes, SHA `cf6387bb1df3051f4a467236d82c50afaba6dfa7`)
- Source accessed from the original uploaded `index (14).html`, confirmed byte count matches GitHub.
- Six section anchors: `home`, `about`, `education`, `experience`, `personal`, `contact`
- One inline CSS block (31,371 characters), one inline JavaScript block (~48,586 characters)
- Original translation dictionary: EN, ES with CA spread from ES and FR spread from EN; after evaluation **100 keys per locale / 400 strings total**
- Twenty embedded images, including SVG and PNG/JPEG
- Legacy functionality: navigation, responsive sidebar, 4 locale buttons, dark mode, 4 accent colors, brand highlights, reading-time estimate, education disclosure, auto-scroll thinker and scroll-position highlighting.

## Phase 1 — current status
- [x] Inspected and inventoried the full uploaded source.
- [x] Started from the original feature branch, leaving `main` untouched.
- [x] Proposed future dynamic section schema: `cms/content.schema.json`.
- [x] Added reproducible extraction code: `tools/migrate_phase1.py`.
- [x] Added exact regression assertions: `tests/validate_phase1.py`.
- [x] **Local migration completed**: extracted CSS, JS, four locales and 20 image files. Exact HTML reversal, translation equality and image hash checks passed locally; Node syntax checks passed.
- [x] Added GitHub Actions `.github/workflows/phase1-migration.yml` to perform the same extraction in the feature branch and commit ONLY there; triggered by push.
- [x] GitHub Actions run **43537558789** completed successfully, including static parity and Node syntax checks: https://github.com/oriolroigescobedo/oriolroigescobedo.github.io/actions/runs/43537558789
- [x] Verified migration-generated files exist on the feature branch (20 binary assets, separate CSS/JS, four locales, image manifest, migrated index).
- [x] GitHub Actions browser parity **43537774230 completed successfully**: 16/16 comparisons passed (desktop/mobile × 4 locales × light/dark), all DOM comparisons equal, 0.000000 pixel difference, no JS page errors. https://github.com/oriolroigescobedo/oriolroigescobedo.github.io/actions/runs/43537774230
- [ ] Additional manual interaction QA on all four accent-color buttons, auto-scroll and sidebar controls is recommended before merging; the original JavaScript and stylesheet are structurally preserved.
- [x] Phase 1 migration and automated browser parity completed. No change to `main`. Further manual acceptance is recommended before future merge.

## Implementation notes
The workflow converts `index.html` into a clean split:
- `assets/site.css`: exact CSS.
- `assets/site.js`: original JS using preloaded `window.PortfolioTranslations`.
- `assets/images/`: 20 image files with original binary data intact.
- `cms/content/translations.json`: 4 locale dictionaries.
- `cms/content/translations.js`: synchronous browser JS translation payload (generated).
- `cms/assets-manifest.json`: image list and checksums.
- `index.html`: same visible markup and ordering with references to these assets.
The dynamic sections schema is NOT yet active. This is architecture migration only, not the editing UI.

## Critical safeguards
- Never merge to or push to `main` without explicit user approval.
- Never commit GitHub PATs or usernames/passwords in site code.
- Do not claim browser checks passed unless actually tested.
- Do not rewrite translations from scratch: preserve exact content and HTML markup.
- If the GitHub Action fails, inspect logs, fix the script/workflow in the feature branch, and rerun. Keep a record.

## Next conversation
1. Open this `PROJECT_STATUS.md`, `cms/README.md`, workflow status, and feature branch file inventory.
2. CI migration succeeded (run 43537558789); avoid rerunning migration unnecessarily.
3. Automated browser parity passed in CI (run 43537774230, 16/16 identical screenshots). Additional manual interaction QA may be done before merging.
4. Phase 1 structural migration complete; keep the public site unchanged.
5. Begin Phase 2 click-to-edit development on a separate feature branch. `main` stays unchanged.

## Further roadmap
- Phase 2: on-page editing without changing public design
- Phase 3: add/remove/reorder sections, experiences, education, projects, links, images, multi-language content and generated navigation
- Phase 4: authenticated GitHub publishing without exposed secrets
- Phase 5: end-to-end QA and approved release

## Phase 2 — implementation checkpoint (2026-11-14)
- Development branch: `feature/portfolio-cms-phase-2` created from Phase 1 head `27a85907ae4cb2faaf2c6598338bd73e779a3e5b`.
- [x] Added passive `cms/editor.css` and opt-in `cms/editor.js` (`?cms=edit` only).
- [x] Added click-to-edit translation text, additional simple static targets, floating Preview/Edit, Save Draft, Cancel Changes and Exit controls.
- [x] Added per-language EN/ES/CA/FR override state, local-only browser draft persistence, and HTML sanitization.
- [x] Existing `assets/site.js`, the 20 image assets and `cms/content/translations.json` left unchanged.
- [x] Added `tests/editor_phase2.py` and branch-specific `.github/workflows/phase2-editor.yml`; adapted exact original-HTML assertion to ignore only the two added Phase 2 resource tags.
- [x] Updated `cms/README.md` with usage, limits and security boundary.
- [x] Phase 2 CI run **43539500137** passed: 16/16 original-vs-development browser snapshots had zero pixel difference, JS/migration checks succeeded, and interactive editor smoke tests passed across 2 viewport sizes × 4 languages × 2 themes, including save/reload, cancel, preview, language isolation, and HTML sanitization. https://github.com/oriolroigescobedo/oriolroigescobedo.github.io/actions/runs/43539500137
- [ ] Manual browser acceptance still needed for all fixed controls, focus/selection, existing links and complex rich formatting (automated browser tests cover the primary flows).

**Important**: `?cms=edit` is an open URL switch, NOT access control. All drafts are local to the device and are never sent to GitHub. Authentication, private mode and publishing are deferred to Phase 4; do not put credentials in this static site. The initial milestone does not include editing image assets, URLs or adding/reordering sections, which remain Phase 3.

**Phase 2 status**: implemented and **automated CI verified**. Manual interaction acceptance and Phase 3 content schema work remain separate next steps. Public release requires explicit approval; do not merge.

**Production safeguard**: rechecked `main` after Phase 2 development; its head remains `8a51574bd49bb8a28b5a2e8815cc48e491fd0f26`.
