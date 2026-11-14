# Portfolio CMS — Project Status

Updated: 2026-11-14
Repository: `oriolroigescobedo/oriolroigescobedo.github.io`
Working branch: `feature/portfolio-cms-phase-1`
Production branch: `main` — **DO NOT MODIFY**

## Objective
Preserve the original public portfolio while gradually enabling on-page direct visual edits, dynamic navigation/sections, four locales and secure GitHub-based publication.

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
