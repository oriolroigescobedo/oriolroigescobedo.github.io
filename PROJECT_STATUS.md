# Portfolio CMS — Project Status

Updated: 2026-11-14
Repository: `oriolroigescobedo/oriolroigescobedo.github.io`
Working branch: `feature/portfolio-cms-phase-1`
Production branch: `main` (**DO NOT CHANGE without explicit approval**)

## Objective
Keep the existing public portfolio's exact visual design and features while preparing direct, authenticated editing in-page, adding/reordering sections and translations, and publishing to GitHub Pages.

## Verified repository baseline
- `main` points to `8a51574bd49bb8a28b5a2e8815cc48e491fd0f26` at inspection.
- Only `index.html` was present on `main`.
- File blob SHA: `cf6387bb1df3051f4a467236d82c50afaba6dfa7`; size: 3,546,480 bytes.
- The feature branch was created from this same baseline, and `index.html` has **not** been modified.
- GitHub connector returned empty content when requesting `index.html` (including line-range requests). Its HTML/JS/CSS could not be reliably analyzed. **Do not claim otherwise.**

## Phase 1 progress
- [x] Inspect repository metadata and file inventory.
- [x] Work on an isolated feature branch; protect `main` by not writing to it.
- [x] Create a proposed versioned multilingual content schema (`cms/content.schema.json`).
- [x] Document architecture, security assumptions and migration checks (`cms/README.md`).
- [x] Document progress and handoff (`PROJECT_STATUS.md`).
- [ ] Read and analyze the full actual HTML, script behavior, embedded assets and locale strings — **blocked by connector returning empty content**.
- [ ] Extract real current content, preserve exact markup, and wire renderer without regressions — **not started**.
- [ ] Verify visual/function parity — **not tested**.

## Key decisions
- Do not fabricate actual page content from prior chat, screenshots or assumptions.
- Avoid a blind rewrite of a 3.5 MB single HTML file.
- Use stable IDs for sections and entries; navigation derives from ordered sections.
- Keep locale-specific strings explicit (en/es/ca/fr) to avoid changes being lost when switching languages.
- Phase 1 schema is a proposal, not yet a faithful extraction of the existing document.
- Never store GitHub credentials in source or persistent browser storage.

## Next action
Obtain readable HTML source, for example by supplying a local copy of `index.html` as a chat attachment or using a reliable GitHub file reader. Analyze it, inventory CSS/JS/i18n/sections, then extract to a real `cms/content.json` and adapt `index.html` **only on the feature branch**. Test desktop/mobile, languages, dark mode and links before merging.

## Overall roadmap
1. Phase 1: architecture/content migration and parity — **scaffold in place, migration blocked**.
2. Phase 2: in-page click-to-edit.
3. Phase 3: editable/reorderable sections, links, assets and all four locales.
4. Phase 4: authorized publishing to GitHub.
5. Phase 5: regression testing, security review and production release.

## Resume instruction for a new conversation
Read this file, check branch/current commit, read the full original `index.html`, and complete outstanding Phase 1 items without touching `main`.
