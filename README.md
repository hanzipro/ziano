# cheritage · 傳承字形 webfont CDN

Free, CDN-hosted, drop-in **傳承字形 / 舊字形** (heritage / orthodox glyph form)
Traditional-Chinese webfonts. cheritage does for heritage CJK what
[Fontsource](https://github.com/fontsource/fontsource) does for Latin: it slices
OFL fonts into `unicode-range` woff2 subsets and publishes per-family npm
packages, so jsDelivr/unpkg serve them for free and a page downloads only the
glyphs it actually uses.

> Why: almost every TC webfont on the open web renders Taiwan's MOE national
> standard forms (國字標準字體). cheritage serves the orthodox heritage forms
> instead. JP/SC/KR runs deliberately fall through to system fonts.

See `docs/superpowers/specs/` for the full design.

## Roster

黑 (sans) · 明 (serif) · 楷 (cursive) — all three styles covered.

| Package | Family | Style | Format | Weights | Glyph forms |
|---|---|---|---|---|---|
| `@cheritage/shanggu-serif` | 尚古宋 Shanggu Serif | 明 serif | **VF** | 250–900 | **full 舊字形** (flagship) |
| `@cheritage/shanggu-sans` | 尚古黑 Shanggu Sans | 黑 sans | **VF** | 250–900 | **full 舊字形** (flagship) |
| `@cheritage/genyo-min` | 源樣明體 GenYo Min | 明 serif | static | 7 | neutral · 月版/TW (milder) |
| `@cheritage/genyo-gothic` | 源樣黑體 GenYo Gothic | 黑 sans | static | 7 | neutral · 月版/TW (milder) |
| `@cheritage/genyo-min-tc` | 源樣明體 GenYo Min TC | 明 serif | static | 7 | 丹版/TC (傳承印刷體) |
| `@cheritage/genyo-gothic-tc` | 源樣黑體 GenYo Gothic TC | 黑 sans | static | 7 | 丹版/TC (傳承印刷體) |
| `@cheritage/lxgw-wenkai-tc` | LXGW WenKai TC 霞鶩文楷 | 楷 cursive | static | 3 | 傳承字形 |
| `@cheritage/iansui` | Iansui 芫荽 | 楷 cursive | static | 1 | 國字標準字體 (MOE) |

GenYo weights: serif `250 300 400 500 600 700 900`, sans `250 300 350 400 500 700 900`.
LXGW weights: `300 400 500`.

## Printed vs. handwriting: where MOE standard forms are (dis)allowed

cheritage's correction target is the **printed** styles. The ban on the MOE
national standard (國字標準字體) applies to **明 (serif) and 黑 (sans)** only — the
faces where heritage vs. standard forms are a real typographic choice.

**楷 (style `cursive`) is a handwriting style**, and in handwriting the MOE
standard forms are legitimate (they are, after all, modelled on handwriting). So
cheritage admits a 楷 font that follows the MOE standard:

- **`@cheritage/iansui`** (Iansui 芫荽) — a **國字標準字體** 楷. Allowed because it
  is handwriting, not print.
- **`@cheritage/lxgw-wenkai-tc`** (LXGW WenKai TC) — a **傳承字形** 楷 (Klee-based).

Both ship side by side so users **freely choose** the kai orthography they want.
The print faces (Shanggu, GenYo) remain heritage-only.

## Usage

```css
/* flagship: Shanggu, variable, full 舊字形 */
@import url("https://cdn.jsdelivr.net/npm/@cheritage/shanggu-serif/variable.css");
@import url("https://cdn.jsdelivr.net/npm/@cheritage/shanggu-sans/variable.css");

/* static families import index.css (all weights) or a single weight, e.g. ./400.css */
@import url("https://cdn.jsdelivr.net/npm/@cheritage/lxgw-wenkai-tc/400.css");

:root {
  --han-heritage-serif: "Shanggu Serif";
  --han-heritage-sans:  "Shanggu Sans";
}
```

The browser downloads only the slices your page hits. Uncovered codepoints fall
through to the next font in your stack (by design — no tofu, and the mechanism by
which JP/KR/SC stay on system fonts).

> Tip: for static families, importing `index.css` pulls every weight's CSS via
> `@import`. If you only need one or two weights, import those `<weight>.css`
> files directly to cut requests.

## Build

```bash
uv sync
uv run python -m cheritage.build <family-id>   # e.g. shanggu-serif
uv run pytest -q                                # add -m "not integration" to skip downloads
```

All fonts are OFL 1.1; each package bundles its upstream license. Sources are
pinned by release tag + sha256 in `roster.toml`.
