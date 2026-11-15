# Portfolio CMS

## Fase 5 · Guia d’administració

1. Obre `https://EL-TEU-SERVIDOR/?cms=edit`. Per restaurar un esborrany d’un altre navegador o domini, selecciona **Importar JSON**.
2. Clica el text de la pàgina per editar-lo. Al **Gestor de contingut**, aplica els canvis de format, URL, imatge o text alternatiu. Des de **Contingut** pots afegir, eliminar i ordenar seccions i entrades. El menú lateral segueix l’ordre de les seccions.
3. Canvia d’idioma amb EN, ES, CA i FR. Completa els textos pendents i comprova la pàgina amb **Previsualitzar**. **Desar esborrany** desa al navegador del dispositiu. **Cancel·lar canvis** restaura la còpia desada o el contingut inicial. **Exportar JSON** et permet fer una còpia independent.
4. Tria **Publica l’esborrany**, **Connecta GitHub**, **Autoritza a GitHub** i, quan tornis a l’editor, **Comprova la connexió**. Revisa el resum, els idiomes pendents i el JSON amb **Revisa l’esborrany**. Pots tancar el diàleg per comprovar la previsualització.
5. Quan vulguis guardar aquesta versió a GitHub, tria **Confirma la publicació a desenvolupament**. El commit només escriu `cms/content/published.v3.json` a `feature/portfolio-cms-phase-5`. El fitxer és visible a GitHub tan bon punt es publica. Si la branca ha canviat o la connexió s’ha perdut, conserva l’esborrany i torna a revisar-lo. Si el primer intent ja havia escrit el mateix contingut, la revisió següent l’identifica com a coincident.

La pàgina normal llegeix el JSON disponible al mateix lloc des d’on se serveix el portfolio. Sense un fitxer compatible, es mostra el contingut original. Els esborranys desats al navegador són exclusius de l’editor. Actualitza el checkout del servidor de desenvolupament al commit revisat per veure el nou JSON des d’aquell servidor.

### Configurar i verificar el servidor de desenvolupament

- Segueix els passos de la GitHub App i les variables de configuració de **One-time setup**. A la fase 5, fes servir un host HTTPS dedicat i el checkout de `feature/portfolio-cms-phase-5`. Configura el callback exacte `https://EL-TEU-SERVIDOR/auth/callback` i instal·la l’app només al repositori del portfolio.
- A **Settings → Pages**, comprova que la font sigui `main` o que el workflow de producció només desplegui des de `main`. A **Settings → Rules → Rulesets**, requereix pull request per a `main` i verifica que l’app i el compte d’administració no tinguin bypass. Aquestes opcions s’han de verificar al repositori.
- Prova el login real amb el teu compte. En una finestra privada, comprova que la UI demani connectar GitHub abans de revisar o publicar. Amb el compte correcte, fes una publicació de prova amb contingut no sensible després de revisar-lo i comprova el fitxer, el commit i la branca. Desconnecta al final.

### Còpia, desplegament i reversió

- Abans de cada publicació, exporta el JSON i guarda el SHA de la versió aprovada i, si existeix, una còpia de `published.v3.json`. Fes servir una ubicació privada per a aquestes còpies.
- Abans d’aprovar un desplegament, verifica els workflows del commit exacte, el resultat de l’OAuth real, les regles de `main`, la font de Pages i l’acceptació en els quatre idiomes. Revisa el JSON que anirà al públic. Promou només la versió aprovada mitjançant una pull request revisada.
- Per revertir contingut a desenvolupament, importa la còpia bona i passa de nou per la revisió i la confirmació. Per revertir una publicació de producció després de l’aprovació, crea una pull request que reverteixi el commit de publicació o recuperi el JSON de l’últim SHA aprovat. Comprova el nou resultat de Pages i la pàgina pública. Si cal recuperar el contingut original, retira el fitxer de publicació mitjançant aquest mateix flux.

### Acceptació abans de producció

- [x] GitHub Actions de fase 5 en verd per al codi de `1c91180`. Torna a validar si el codi o el contingut que es vol promocionar canvien. [Execució 43750434974](https://github.com/oriolroigescobedo/oriolroigescobedo.github.io/actions/runs/43750434974)
- [ ] Edició, desament, importació, exportació, cancel·lació i previsualització en EN, ES, CA i FR.
- [ ] Escriptori, tauleta i mòbil amb els dos temes i els quatre accents. Completa la comprovació de contrast i lector de pantalla. Les proves de teclat i restauració del focus del diàleg han passat a Chrome.
- [ ] Login i sortida reals, revisió i publicació de prova amb l’app instal·lada, i confirmació del fitxer i la branca.
- [ ] Proteccions de `main`, font de Pages, còpia de seguretat, procediment de reversió i aprovació explícita.

## Phase 4 · GitHub publication to the development branch

Historical Phase 4 reference. For the currently supported branch and renderer, use the Phase 5 guide above. The GitHub App and HTTPS setup steps below still apply with the Phase 5 checkout.

Use the editor on the dedicated HTTPS publisher origin at `/?cms=edit`. GitHub Pages serves static files, so the publisher serves this same editor beside its authenticated API. Open **Publish draft**, select **Connect GitHub**, follow **Authorize on GitHub** in a new tab, then return and select **Check connection**. Keep the editor tab open to preserve working changes during sign-in. The editor on a static host still supports local editing.

Select the current draft by opening or importing it in the visual editor. Apply inspector changes before review. **Review current draft** switches the page to visual preview and validates a copy on the server. Close the dialog to inspect the page in each language. The dialog shows whether the snapshot creates or replaces the file, the branch and reviewed commit, and the full draft JSON. Reopen it and select **Confirm development publish**. The resulting link opens the GitHub commit.

The only file a publication can write is `cms/content/published.v3.json` on `feature/portfolio-cms-phase-4`. The snapshot includes the v3 section and entry order, four locale dictionaries and overrides, link/image attributes, added links, and any included raster uploads. The public repository exposes that file and its history immediately to anyone, including before a Pages release. The site does not load this development snapshot. A release renderer and an approved Pages release are still Phase 5 work.

Use **Save draft** or **Export JSON** for persistence. Browsers isolate local storage by origin. Export from the old editor origin and import on the publisher origin to move an existing draft. A conflict or lost response leaves the working copy untouched. Select **Review current draft** again to compare against the latest branch head. If GitHub committed an identical snapshot before a response was lost, the new review displays it as unchanged.

### Architecture and permissions

- A private GitHub App installed on the portfolio repository uses the OAuth web application flow with single-use state, PKCE S256, a fixed callback and a repository-bound, expiring user access token. The token can use only permissions shared by the installation and the signed-in user. Enable repository **Contents: Read and write** and implicit **Metadata: Read**. Keep all other permissions disabled. The server checks the numeric owner account ID, installation and repository ID. GitHub enforces the write permission. [GitHub App authentication](https://docs.github.com/en/apps/creating-github-apps/authenticating-with-a-github-app/generating-a-user-access-token-for-a-github-app)
- The GitHub token lives in a single publisher process. The browser receives an opaque, host-only, HttpOnly, Secure, SameSite=Lax session cookie. Login state expires after five minutes and the session expires after at most 30 minutes. Refresh tokens are discarded. POST endpoints require the exact configured Origin, JSON and an application header, with no cross-origin API access. Disconnect ends the local session and requests GitHub token revocation. Expired sessions and service restarts require reconnecting. Project owners can revoke the application authorization from [GitHub application settings](https://github.com/settings/apps/authorizations). [GitHub token revocation API](https://docs.github.com/en/rest/apps/oauth-applications#delete-an-app-token)
- The server applies `content.schema.json`, structural and ID checks, a rich-text and URL allowlist, image signature and size checks, and credential detection before review or publish. The scanner checks the active publisher credentials, common credential formats and credential-like assignments in text, including some encoded and split forms. It cannot detect every secret, encrypted image metadata or text visible only in pixels. The review binds the exact canonical JSON and branch head for ten minutes. GitHub's `expectedHeadOid` guards the atomic commit against a concurrent push. File, branch, repository and commit message are server constants. GitHub grants Contents permission at repository level, so protect `main` independently. [GraphQL commit mutation](https://docs.github.com/en/graphql/reference/commits#createcommitonbranch)

### One-time setup

1. In the portfolio repository, check **Settings → Pages**. Keep the existing production source on `main`, or if using Actions ensure only the production branch can deploy. Do not configure this development branch or publisher origin as the public Pages source. Under **Settings → Rules → Rulesets**, protect `main` with a pull request requirement and no bypass for the publishing app or authorizing account. [Pages source](https://docs.github.com/en/pages/getting-started-with-github-pages/configuring-a-publishing-source-for-your-github-pages-site) · [GitHub rulesets](https://docs.github.com/en/repositories/configuring-branches-and-merges-in-your-repository/managing-rulesets/creating-rulesets-for-a-repository)
2. Choose a dedicated hostname with HTTPS for the publisher. Create a [GitHub App under your account](https://github.com/settings/apps/new). Use that hostname as the homepage and `https://YOUR-PUBLISHER-HOST/auth/callback` as the callback. Disable webhook delivery and device flow, enable expiring user tokens, and set installation availability to **Only on this account**. Give it **Contents: Read and write** and leave the other optional permissions off. Install it using **Only select repositories** and select `oriolroigescobedo.github.io` only. Generate a client secret in the app settings. This flow requires no app private key. [Register a GitHub App](https://docs.github.com/en/apps/creating-github-apps/registering-a-github-app/registering-a-github-app)
3. On the publisher host, check out `feature/portfolio-cms-phase-4` and install the Python 3.12 dependencies with `python -m pip install -r publisher/requirements.txt`. Set these environment variables for the service through the host's configuration or secret manager.

   | Variable | Value |
   | --- | --- |
   | `CMS_ORIGIN` | The dedicated HTTPS origin with no trailing slash or path |
   | `CMS_CLIENT_ID` | Client ID in the GitHub App settings |
   | `CMS_CLIENT_SECRET` | Client secret entered directly in the host's secret manager |
   | `CMS_USER_ID` | Numeric `id` from [your GitHub user record](https://api.github.com/users/oriolroigescobedo) |
   | `CMS_REPO_ID` | Numeric `id` from [the GitHub repository record](https://api.github.com/repos/oriolroigescobedo/oriolroigescobedo.github.io) |
   | `CMS_INSTALLATION_ID` | Number at the end of the installed app's configuration URL in [GitHub installations](https://github.com/settings/installations) |

4. Start `python -m publisher.app` from the checkout root under a service manager. It listens on `127.0.0.1:8080`. Terminate TLS at a reverse proxy for the chosen hostname, forward requests to that loopback address, and keep one publisher process per hostname. Allow JSON bodies up to 12 MB and use an upstream response timeout of at least 75 seconds. Disable request/response body capture, inbound header capture and OAuth callback query logging at the proxy and in monitoring. Rate-limit `/api/login` at the proxy, for example 10 requests per client per minute. Never paste the secret in Git, chat, terminal history or static host settings. To revoke access immediately, uninstall/suspend the GitHub App or revoke its user authorization; when rotating the client secret, restart the service and remove the previous secret in GitHub.
5. Open the HTTPS editor and confirm a real GitHub login and installation. When ready to verify the live integration, review and explicitly confirm a non-sensitive development draft. Check that the resulting commit contains exactly the snapshot file and that Pages still serves production. Before a public release, integrate and test a release renderer and approve the specific content and release.

The Phase 4 dialog and Phase 3 advanced panel are in English. This affects usability across the four interface languages, including the comprehension of the confirmation step. The browser tests exercise the dialog and its status feedback; a manual keyboard, focus, screen-reader and responsive acceptance review remains open.

[Phase 4 GitHub Actions run 43744433351](https://github.com/oriolroigescobedo/oriolroigescobedo.github.io/actions/runs/43744433351) passed the publisher unit and browser tests, the Phase 2 and Phase 3 regressions, and the 16 visual comparisons. The publisher tests exercise the actual server and UI against a GitHub API double. The owner setup above is required to test the installed app with GitHub.

## Phase 3 usage (development branch only)

Open `index.html?cms=edit` using a local HTTP server. Click existing text to edit it directly. Selection also opens **Content manager**, where you can apply rich formatting, change link destinations, change an image URL or upload a raster image, and edit alternative text. Use **Apply** before leaving a panel field. **Save draft** persists the applied changes locally.

**Content** opens the section/entry tree. Use **+ Entry**, **+ Section**, the up/down arrows and **Delete**. Existing component designs are reused automatically. New sections receive unique stable anchors, and the sidebar follows structural order. Home cannot be deleted. Select a compatible organisation/contact link area to add a link.

Switch EN/ES/CA/FR using the original language buttons. New text is blank in untranslated locales and the inspector reports missing translations. URL/image sources and structural order are shared; text and image alt values are localized. Existing Phase 2 static overrides are copied to all four locales during migration to preserve their previous visible behavior; subsequent edits are independent.

**Preview** hides the inspector and selection outlines; use **Edit** to return. **Cancel changes** restores the last saved draft, including structure and images. **Export JSON** downloads the working draft (including unsaved applied changes); **Import JSON** validates it and stages it as an unsaved draft. Invalid versions, duplicate IDs, unknown templates and unsafe URLs are rejected. The original v1 localStorage backup is retained. Draft v3 key: `oriol-cms-draft-v3`.

`content.schema.json` now describes the live v3 envelope. `content.sections` stores stable section/entry identities and trusted template references; `content.fields` stores localized sanitized HTML overrides; `content.attributes` stores URLs and localized image alt text; `content.links` stores added component links. The existing translation-key editing model is retained rather than replaced. Original proposed schema definitions remain available for the future publishing adapter.

The normal public URL does not activate the editor or render local drafts. The Phase 4 service provides the publication endpoint on its separate HTTPS origin. Read the current limitations and verified results in `PROJECT_STATUS.md`.

Validation: `python tests/editor_phase3.py`, `python tests/editor_phase2.py`, `python tests/validate_phase1.py`, `python tests/browser_parity.py`. Install Playwright, Pillow, NumPy and jsonschema plus Chromium. An optional `CMS_BROWSER` environment variable selects an installed Chrome executable. CI uses Playwright Chromium on Linux and uploads Phase 3 screenshots.

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
Static GitHub Pages cannot protect an in-browser hard-coded password. The supported publication flow uses the separate GitHub App service described above.

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
