# Portfolio CMS — architecture scaffold

This folder is deliberately **not linked** from `index.html` yet. Phase 1 prioritizes zero regressions.

## Intended data flow
- Current published `index.html` remains the single source of truth until a complete content extraction and browser parity check can be performed.
- `content.schema.json` proposes a versioned, ordered section collection with stable IDs and four translated locale values (en/es/ca/fr).
- In the next implementation step, extract the actual source content into a validated `cms/content.json` (do **not** populate it from guesses).
- A rendering adapter should preserve existing markup and CSS classes, navigation anchors, responsive behavior, locale switching and dark-mode behavior.
- Preview edits in local memory; publish to GitHub only after explicit authentication, validation, and a SHA-aware write.
- Section order controls navigation order. Content and layout should remain separate.

## Security
GitHub Pages is public static hosting. Hiding an admin icon or storing a password in JavaScript is **not** authorization. Never commit PATs, credentials, client secrets or session tokens. Prefer a secure OAuth/backend authorization flow in production; a short-lived, fine-grained PAT entered into the browser only when publishing can be an interim option, with clear risk warnings.

## Migration acceptance checks
1. Compare the old and new portfolio at desktop and mobile sizes in all four languages and themes.
2. Check navigation links, external buttons, animations, image assets and accessibility controls.
3. Check that text rendered after locale changes remains unchanged until the CMS is activated.
4. Check all sections and linked anchors against the actual source page.
5. Confirm that no data loss or new console errors occur.
6. Do not merge into `main` until checks have been completed.
