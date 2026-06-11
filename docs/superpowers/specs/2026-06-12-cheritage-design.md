# cheritage — 傳承字形 webfont CDN

**Status:** Design approved 2026-06-12. Pending implementation plan.
**Repo:** `~/Workspace/hanzi.pro/cheritage` · npm: `cheritage` (meta) + `@cheritage/*` (per-family)

---

## 1. Problem & motivation

Traditional-Chinese webfonts on the open web almost universally render Taiwan's
MOE national standard character forms (國字標準字體). These forms are widely
considered aesthetically inferior, and there is no convenient, free, CDN-hosted
way to serve **傳承字形 / 舊字形** (orthodox / heritage glyph forms) the way
Google Fonts serves Noto.

Meanwhile JP / SC / KR system fonts are already good, so **only the TC layer
needs correcting**. (This mirrors han.css's own font cascade philosophy, where
`src/css/fonts/webfonts/generics.css` deliberately ranks Noto TC *last* because
it follows the MOE standard.)

cheritage fixes this by doing for heritage CJK what
[Fontsource](https://github.com/fontsource/fontsource) does for Latin webfonts:
slice OFL heritage fonts into `unicode-range` woff2 subsets, publish per-family
packages to npm, and let jsDelivr/unpkg serve them free. A page adds one
`@import` and downloads only the glyphs it actually uses.

## 2. Goals / non-goals

**Goals**
- Free, CDN-hosted, drop-in heritage-glyph TC webfonts (serif + sans).
- "Download only what's hit" via `unicode-range` slicing (the Google/Noto model).
- A font-agnostic build pipeline driven by a roster config, so adding a family
  is a config entry, not new code.
- Clean swap API via CSS variables; first-class integration with han.css.

**Non-goals**
- Not building/redesigning fonts — we only subset & repackage existing OFL fonts.
- Not "correcting" JP / SC / KR — those fall through to system fonts by design.
- No JS runtime; pure CSS + woff2 delivery.

## 3. Roster (v1)

The roster is a **config file**; everything below is data, not code.

| Slot | Family | Source repo (pinned) | Format | Heritage tier |
|---|---|---|---|---|
| **Default serif** | 尙古宋 Shanggu Serif | `GuiWonder/Shanggu` v1.028 | TrueType **VF** | full 舊字形 |
| **Default sans** | 尙古黑 Shanggu Sans | `GuiWonder/Shanggu` v1.028 | TrueType **VF** | full 舊字形 |
| Neutral alt serif | 源樣明體 GenYoMin (月版/TW) | `ButTaiwan/genyo-font` v2.100 | static per-weight | neutral |
| Neutral alt sans | 源樣黑體 GenYoGothic (月版/TW) | `ButTaiwan/genyog-font` v2.100 | static per-weight | neutral |

**Decisions behind this roster**
- **Default = Shanggu (VF, full heritage).** Variable font is the right
  architecture for the slicing model: one slice spans the whole 100–900 axis
  (smooth weight handle, no `slices × weights` file multiplication) — exactly
  what Google serves for Noto. The opinionated 舊字形 default also matches the
  project's thesis (a corrective tool should default to the strong form).
  Use Shanggu's **TrueType-flavoured VF**, not CFF2, for widest browser support.
- **Neutral alt = GenYo 月版 (Moon).** Static-only (no VF in its releases —
  confirmed: v2.100 ships `*-ttc.zip` + per-region OTF, no `VF`/`Variable`
  asset). Provides a milder cut for users who find full 舊字形 too aggressive.
  Ships **all ~7 Source Han weights** as static per-weight slices (decided).
- Chiron Hei/Sung were **rejected** — they balance standard + printed forms and
  are explicitly *not* 舊字形/傳承.
- Future drop-in roster entries (config only): I.Ming 一點明體 (the canonical
  傳承字形 standard-bearer, but Regular-weight-centric/static), 源流明體
  GenRyuMin, Shanggu Mono + Round.

## 4. Architecture

Six components, each independently testable.

1. **`roster.toml`** — per family: source repo, pinned release tag, asset
   filenames, OFL license path, style (serif/sans), heritage tier, format
   (vf/static), default weights, output family name(s).
2. **Acquire** — download the pinned GitHub-release assets; verify checksums;
   cache locally. Never floats to "latest".
3. **Slice engine** — `fonttools pyftsubset` per font × per `unicode-range`
   slice, compressed to woff2 (`--flavor=woff2`).
   - **Slice table:** extracted from Google Fonts' live `css2` response for the
     equivalent Noto family (~100 ranges) so we inherit their proven,
     cache-friendly boundaries. Stored as a versioned data file.
   - **VF fonts:** retain `fvar` axes per slice → each `@font-face` gets
     `font-weight: 100 900`.
   - **Static fonts:** one slice-set per chosen weight.
   - **Full-script scope (no TC-stripping).** We slice the *whole* font, not a
     TC-only subset. Rationale: with `unicode-range`, the end user only ever
     downloads slices their page hits, so a pure-TC page is already minimal
     whether or not kana/hangul/SC slices exist. Stripping them saves the user
     nothing (only shrinks the npm tarball nobody downloads whole) while
     breaking mixed-script documents. **TC intent is enforced by han.css's
     `:lang()` cascade** (JP/KR/SC runs prefer system fonts), not by mutilating
     the font.
4. **CSS generator** — per family emit one `@font-face` per slice
   (`unicode-range`, weight range, `font-display: swap`, relative `src`) plus a
   `:root` variable layer and `font-family` aliases.
5. **Packager** — one scoped npm package per family
   (`@cheritage/<family>`): `variable.css` (VF) or `<weight>.css` + `index.css`
   (static), `files/*.woff2`, OFL `LICENSE`, `README`, `package.json` with
   `sideEffects`/`exports`. Plus a thin meta-package **`cheritage`** that
   re-exports the default serif+sans CSS.
6. **CI / publish** — GitHub Actions: build → version → `npm publish` →
   jsDelivr serves automatically. Reproducible: pinned sources + hashed outputs.

## 5. Data flow

```
roster.toml
   │  pinned source font (GitHub release)
   ▼
acquire → slice (pyftsubset, ~100 unicode-ranges) → woff2
   ▼
CSS generator → @font-face × slices + :root vars
   ▼
per-family npm package  ──publish──▶  npm  ──▶  jsDelivr CDN
                                                  │
                              browser @import ◀───┘
                                                  │
                          downloads ONLY the slices a page hits
```

## 6. Consumption API

```css
/* default flagship (Shanggu, VF, full heritage) */
@import url("https://cdn.jsdelivr.net/npm/@cheritage/shanggu-serif/variable.css");
@import url("https://cdn.jsdelivr.net/npm/@cheritage/shanggu-sans/variable.css");

:root {
  --han-heritage-serif: "Shanggu Serif";
  --han-heritage-sans:  "Shanggu Sans";
}
```

- Works standalone, or wired into han.css `src/css/fonts/webfonts/generics.css`
  to **replace the current Google Fonts `@import`**.
- Users override `--han-heritage-serif` / `--han-heritage-sans` to switch the
  default family (e.g. to GenYo for the neutral cut).
- The meta-package `cheritage` ships a single `index.css` that imports the two
  defaults + sets the variables, for the "just give me good defaults" user.

## 7. Error handling / edge cases

- `font-display: swap` — FOUT, never invisible text.
- Uncovered codepoint → fallthrough to next font in the stack (system) — **by
  design, no tofu**, and the mechanism by which JP/KR/SC stay on system fonts.
- VF support — TrueType-flavoured woff2 VF is broadly supported in current
  Chromium/Firefox/Safari; the static GenYo packages double as the conservative
  fallback family for ancient engines.
- **OFL Reserved Font Name** — subsetting is technically a modification.
  **Decided: keep the upstream font name.** Caveat (compliance gate): OFL's RFN
  clause forbids the *reserved* name on a modified build, so per font we must
  check whether the upstream `OFL.txt` actually declares a Reserved Font Name —
  keep the name where none is declared (the common case; what Fontsource relies
  on), rename only if an RFN forces it. Each package bundles the upstream
  `OFL.txt` and preserves copyright/RFN notices regardless.
- jsDelivr 50 MB/file limit — slices are ~30–100 KB each, never an issue.

## 8. Testing / verification

- **Coverage analysis** (blocking pre-default-confirmation): download Shanggu &
  GenYo, `fonttools` cmap diff against a curated *common-but-hard* TC charset
  (難字 / 常用罕見字). Tests the hypothesis that a higher raw glyph count may
  just hoard very-rare codepoints while missing common-but-tricky 傳承 chars —
  the default is chosen on **practical** coverage, not headline count.
- **Visual regression** (Playwright — already used by han.css): render a TC
  sample + a mixed JP/KR/SC sample; assert (a) no tofu, (b) specific heritage
  glyph variants are present (e.g. 戶 / 骨 / 直 / 過 / 青 old forms vs MOE forms).
- **Build determinism** — output woff2 hashes stable across runs given pinned
  sources.
- **CSS validity** — every generated `@font-face src` URL resolves to an
  existing woff2; `unicode-range` syntax valid.

## 9. Open questions

1. ~~Coverage verdict~~ — **Decided 2026-06-12: Shanggu confirmed as practical
   default.** Coverage analysis (`cheritage.coverage` vs `data/common-hard-tc.txt`)
   on `ShangguSerifTC-VF.ttf` (1.028): **24/24 common-hard 傳承 chars covered, 0
   missing**, out of 44,791 cmap glyphs. The "high raw count hoards rare chars but
   misses common-hard" hypothesis did not materialize for the curated set; no roster
   reorder. (Re-evaluate when GenYo lands in Plan 2 for a serif-vs-serif comparison.)
2. ~~OFL naming~~ — **Decided: keep upstream names**, subject to the per-font
   Reserved-Font-Name check in §7 (rename only if an RFN is declared).
3. ~~GenYo static weight set~~ — **Decided: ship all ~7 Source Han weights.**
4. **v1 stop line** — Shanggu + GenYo only, or also ship I.Ming as a "prestige"
   entry from day one.
5. **Slice-table provenance** — snapshot Google's `css2` ranges into a static
   data file vs. regenerate at build time; pin a version either way.

## 10. References

- Fontsource (model): https://github.com/fontsource/fontsource
- 尙古 Shanggu: https://github.com/GuiWonder/Shanggu (OFL-1.1, VF)
- 源樣明體 GenYoMin: https://github.com/ButTaiwan/genyo-font (OFL-1.1)
- 源樣黑體 GenYoGothic: https://github.com/ButTaiwan/genyog-font (OFL-1.1)
- I.Ming 一點明體: https://github.com/ichitenfont/I.Ming
- han.css cascade context: `../next/src/css/fonts/webfonts/generics.css`
