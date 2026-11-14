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
- [ ] GitHub Actions real-browser parity check added: `tests/browser_parity.py`, 16 combinations (desktop/mobile × 4 locales × light/dark). Run **43537774230** in progress at last inspection: https://github.com/oriolroigescobedo/oriolroigescobedo.github.io/actions/runs/43537774230. Local Chromium testing was blocked. Still verify all 4 accent colors and complex interactive controls.
- [ ] Finish browser test, fix any failures on this feature branch, and document its final outcome before claiming Phase 1 fully complete.

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
3. Perform real browser parity testing for original versus feature branch.
4. Record verified results and final Phase 1 status.
5. Only after Phase 1 is verified, begin Phase 2 click-to-edit development on another branch or this feature branch. `main` stays unchanged.

## Further roadmap
- Phase 2: on-page editing without changing public design
- Phase 3: add/remove/reorder sections, experiences, education, projects, links, images, multi-language content and generated navigation
- Phase 4: authenticated GitHub publishing without exposed secrets
- Phase 5: end-to-end QA and approved release
