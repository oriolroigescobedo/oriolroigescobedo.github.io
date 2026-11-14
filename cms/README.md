# Portfolio CMS — architecture and Phase 1 migration

## Source of truth
The original production portfolio lives in `main:index.html` (commit `8a51574bd49bb8a28b5a2e8815cc48e491fd0f26`). Its exact 3,546,480 bytes were supplied as `index (14).html` and analyzed. It contains 6 page sections, 4 locales, 20 embedded images, and one inline style/script block.

## Phase 1 implementation
A reproducible migration is implemented at `tools/migrate_phase1.py`. The GitHub Actions workflow `.github/workflows/phase1-migration.yml` runs it **only on the feature branch**, verifies exact data parity via `tests/validate_phase1.py`, and commits the result to that feature branch. The production branch remains untouched.

The migrated layout:
- `index.html`: unchanged DOM structure, replacing embedded image data with local file paths and inline style/script with external assets.
- `assets/site.css`: the exact original CSS (plus ending newline).
- `assets/site.js`: original interactive behavior, except the embedded translation dictionary is replaced with `window.PortfolioTranslations`.
- `assets/images/`: 20 extracted files with identical decoded bytes.
- `cms/content/translations.json`: exact EN/ES/CA/FR translations (100 keys per language, including spread fallback strings from the original).
- `cms/content/translations.js`: synchronous browser-loadable data generated from the JSON; loaded before site.js to preserve initialization order.
- `cms/assets-manifest.json`: ordered filenames, digests and sizes of embedded assets.
- `cms/content.schema.json`: **draft future schema** for dynamic user-created sections, NOT currently used by the original layout.

## Current content model boundary
This phase separates translations but **does not** pretend every text is editable yet. Some fixed headings, link labels/URLs, metrics, images and section markup remain in `index.html`. A subsequent editor/data migration must cover all of them. Section creation/reordering and auto-navigation do not work yet. No login or publishing UI exists.

## Existing behavior that must remain intact
- Sidebar navigation, anchor scrolling and compact mobile menu
- English/Spanish/Catalan/French locale switching
- Dark/light theme and 4 custom accent colors
- Brand-color spans, reading time, education story expand/collapse
- Automatic scrolling character and its pause/stop controls
- All existing buttons/links/images; fixed 6-section structure
- Responsive layout and accessible control state

## Checks and limitations
- Local validation passed: CSS and script preservation, exact HTML reversible transformation, all 20 image bytes, all 400 translations equal to the original.
- Node.js syntax check passed.
- Chromium was blocked in the initial container, so the checks were moved to GitHub Actions. **Run 43537774230 passed:** 16/16 original-vs-migrated screenshot comparisons had 0.000000 pixel difference, matching text/DOM/computed styles, and no JavaScript page errors. Desktop/mobile (1440px/390px), all 4 locales and both themes tested.
- GitHub Actions verified the migration and full-page browser rendering. Additional manual exploration of accent selection, sidebar menu, automatic scrolling and other controls before production merge is still recommended.

## Security
Static GitHub Pages cannot protect an in-browser hard-coded password. Never commit PATs, passwords, secrets or client tokens. Admin publication must require GitHub authorization (prefer an OAuth intermediary; an explicitly entered, session-only fine-grained token may be an interim prototype).

## Recommended next action
1. Inspect workflow status on the feature branch.
2. Read `PROJECT_STATUS.md`; verify migration files exist and CI checks passed.
3. Run original-vs-refactored visual snapshots in a working browser environment (desktop/mobile, 4 locales, light/dark).
4. Compare all links and interactions. Address regressions on the feature branch only.
5. Continue to Phase 2 (visual editor) without merging `main` until approved.

## Phase 2 — Visual editing (development only)

The editor is loaded through `cms/editor.js` and `cms/editor.css` and **only activates** at `index.html?cms=edit` (the public page remains visually unchanged when this parameter is absent). This URL option is **not authentication**; it must not be treated as a private/admin lock. GitHub-based authentication and remote publication remain Phase 4.

Features in this phase:
- On-page click-to-edit for the 100 existing translation keys, retaining the original HTML structure, and additional eligible static text targets.
- Floating toolbar with Edit/Preview, Save Draft, Cancel Changes and Exit.
- 4-locale draft overrides. Editing one language leaves other languages untouched.
- Local `localStorage` save as `oriol-cms-draft-v1`, with drafts rehydrated on edit-mode reload; nothing is committed or published from the website.
- HTML sanitization for saved rich text: only basic paragraph, line break, emphasis, span and safe link markup are retained; no scripts or event-handler attributes.
- Responsive controls, keyboard focus styles, dark theme compatibility, and passive CSS unless editor mode is active.

**Limitations / next phases**: Saved drafts are device/browser-local, not authenticated or synchronized with GitHub. Static labels with complex nested SVG/image controls, URL editing, images, adding/removing/reordering sections, and dynamic navigation are intentionally outside this milestone; to be addressed in Phases 3–4. Editing markup can change formatting on edited targets; no guarantee of pixel-identical screenshots while edit mode is active. No public editing mode should be enabled as an access-controlled feature without server-side GitHub OAuth.

CI: `.github/workflows/phase2-editor.yml` runs exact baseline migration assertions, original-vs-current browser parity on the default URL, and multilingual interactive editor smoke tests. Details and pending acceptance are recorded in `PROJECT_STATUS.md`.
