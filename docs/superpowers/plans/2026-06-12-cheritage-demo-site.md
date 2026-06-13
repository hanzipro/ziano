# cheritage Demo Site — implementation plan

**Goal:** A polished, GitHub-Pages-ready showcase for cheritage, built with
**pnpm + Vite**, dev server on **port 7070**. Visual language inspired by
`han-stock/diantenjeom/demo` (clean editorial typography demo: fixed control bar,
restrained gray chrome, the fonts themselves as the hero, live weight/variant
controls). Deployed later to GitHub Pages.

**Reference studied:** `diantenjeom/demo` — static HTML, fixed `<header>` controls
(weight `range` + output, vertical toggle), nav between specimen pages, comparison
tables across glyph standards (JIS/MOE/GB/KV), system-font fallback chains, modern
CSS (nesting, logical properties, `text-spacing-trim`). We borrow the *aesthetic
and interaction*, not the static-HTML stack.

---

## Decisions — CONFIRMED 2026-06-12

- **Stack: Bun + Vite + vanilla TypeScript** (no framework). Bun as runtime +
  package manager (replaces node/pnpm); Vite for dev/build. Fast, tiny, Pages-ready.
- **Location: `demo/`** — self-contained bun project, kept entirely separate from
  `dist/` (build artifacts). `demo/public/fonts/` (local font copy) is gitignored.
- **Font source = runtime-switchable.** A control lets the user pick the font
  source: **Local** (now) and, once published, **jsDelivr** / **unpkg**. The picker
  rewrites the `@import` host live (and is reflected in the copyable snippet).
  Default Local until 0.1.0 is up.
- **Roster: ALL 10 families, as a PLAYGROUND.** The core UX: the user freely
  toggles families + weights (+ style/variant), sees them render live, and the page
  shows the **exact CSS `@import` snippet for their current selection, copy-able**.
- **Slice-loader viz: YES, scoped to the two Shanggu families** (serif+sans) for
  now — type Chinese → watch which of the 120 slices light up / get fetched.
- **Pages: not yet.** Develop + run locally (:7070) now. After 0.1.0 npm publish and
  a CDN sanity check, ship the CDN-sourced build to Pages.
- **Design:** "ink on paper" — warm off-white, near-black ink, one 朱紅 vermilion
  accent (nods to 丹版); Shanggu as the display face; system-ui only for chrome.
- **Base path:** `vite base` from env so dev (`/`) and future Pages (`/cheritage/`)
  both work.

---

## Page structure (single page, sectioned; nav scrolls)

1. **Hero** — 傳承字形 set in Shanggu Serif (big), one-line thesis (heritage vs MOE),
   subtle weight-axis animation on load.
2. **傳承 vs 國標 comparison** — the killer visual. The divergent characters
   (戶骨直過青說海角者著) shown **heritage (Shanggu/GenYo) beside the system MOE
   font**, with a toggle to flip/overlay. Annotate 1–2 glyphs (e.g. 戶 the top
   stroke) so a non-typographer sees the difference.
3. **Roster specimen** — 黑 / 明 / 楷 columns; each family rendered with a sample
   line. VF families (Shanggu) get a **weight slider (250–900)**; static families
   show their discrete weights. Family picker updates a shared specimen.
4. **Type tester** — a `contenteditable`/textarea; renders live in the selected
   family + weight (the reference's interactivity). Seeded with mixed TC/JP/SC to
   show fallthrough.
5. **How it works (slicing)** — short, visual: "you import one line, the browser
   downloads only the slices your text hits." Optional stretch: a live
   slice-loader visualization (type → light up which of the ~120 slices are
   fetched), drawing on `docs/research/2026-06-12-google-fonts-unicode-range.md`.
6. **Install** — jsDelivr `@import` snippets with copy buttons; the `index.css`
   uniform entry; `--han-heritage-serif/-sans` override note.
7. **Footer** — roster table, OFL/Apache attributions, links (repo, han.css).

---

## Tasks

### Task 1: Scaffold `demo/` (pnpm + vite + TS)
- `pnpm create vite demo --template vanilla-ts` (or hand-roll minimal).
- `demo/package.json` scripts: `dev` (vite `--port 7070 --strictPort`),
  `build`, `preview`. `demo/vite.config.ts`: `server.port=7070`,
  `base = process.env.VITE_BASE ?? '/'`.
- Add `demo/` to root `.gitignore` exceptions as needed (keep `demo/dist`,
  `demo/node_modules` ignored).
- Verify: `cd demo && pnpm i && pnpm dev` serves on 7070.

### Task 2: Font pipeline for the demo
- Script `demo/scripts/sync-fonts.mjs`: for a curated demo roster (Shanggu
  serif+sans, GenYo min/min-tc, LXGW TC, Iansui, Klee), copy each built package's
  `index.css` + `files/*.woff2` from `../dist/<id>/` into `demo/public/fonts/<id>/`,
  rewriting `@import`/paths as needed. Gate behind `VITE_FONT_SRC=local`.
- For `VITE_FONT_SRC=cdn`: generate `@import` lines pointing at jsDelivr.
- Requires the packages built (`uv run python -m cheritage.build <id>`); document
  the prerequisite. (Note: full `dist/` rebuild pending anyway — slice-table + entry
  rename changed outputs.)

### Task 3: Layout, design system, chrome
- `demo/src/styles/` — tokens (ink/paper/vermilion, type scale, spacing), reset
  (box-sizing, `text-spacing-trim`), the fixed control bar, responsive grid.
- Header controls: family picker, weight slider + numeric output, light/dark.
- Make it genuinely not-ugly: generous whitespace, real vertical rhythm, the
  heritage face doing the talking. Mobile-first.

### Task 4: Sections 1–4 (hero, comparison, roster, type tester)
- TS modules per section; a small shared store for {family, weight} driving the
  specimen + tester. CSS variables (`--han-heritage-serif` etc.) wired to the
  picker.

### Task 5: Sections 5–7 (slicing explainer, install, footer)
- Install snippets generated from the roster (single source of truth: a
  `roster.ts` mirroring the families). Copy-to-clipboard.
- Slicing explainer: static diagram first; live slice-loader as a stretch goal
  (own follow-up if it balloons).

### Task 6: GitHub Pages deploy
- `.github/workflows/pages.yml`: on push to `main`, `pnpm i`, build with
  `VITE_BASE=/cheritage/ VITE_FONT_SRC=cdn`, upload `demo/dist`, deploy via
  `actions/deploy-pages`. (Gated so it only runs after 0.1.0 publish, or use a
  manual `workflow_dispatch` until then.)
- Verify the built site locally with `pnpm preview` at the `/cheritage/` base.

---

## Open questions / risks
- **Fonts before publish:** Pages-with-CDN needs the npm packages live. Until
  0.1.0, either (a) deploy Pages with a *curated bundled subset* (Shanggu only,
  ~12 MB) or (b) hold Pages deploy until publish. Dev works locally regardless.
- **Slice-loader viz** (section 5 stretch) could eat time — keep it optional.
- Demo roster ≠ full roster: pick ~6–7 families to keep it focused and light.

---

## Deferred (not this plan)
Light/dark theme polish・i18n (中/EN copy toggle)・vertical-writing specimen ·
the live slice-loader if it grows・wiring the demo into han.css docs.
