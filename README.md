# cheritage・傳承字形 webfont CDN

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

黑 (sans)・明 (serif)・楷 (cursive) — all three styles covered.

| Package | Family | Style | Format | Weights | Glyph forms |
|---|---|---|---|---|---|
| `@hanzi.pro/webfonts-shanggu-serif` | 尚古宋 Shanggu Serif | 明 serif | **VF** | 250–900 | **full 舊字形** (flagship) |
| `@hanzi.pro/webfonts-shanggu-sans` | 尚古黑 Shanggu Sans | 黑 sans | **VF** | 250–900 | **full 舊字形** (flagship) |
| `@hanzi.pro/webfonts-genyo-min` | 源樣明體 GenYo Min | 明 serif | static | 7 | neutral・月版/TW (milder) |
| `@hanzi.pro/webfonts-genyo-gothic` | 源樣黑體 GenYo Gothic | 黑 sans | static | 7 | neutral・月版/TW (milder) |
| `@hanzi.pro/webfonts-genyo-min-tc` | 源樣明體 GenYo Min TC | 明 serif | static | 7 | 丹版/TC (傳承印刷體) |
| `@hanzi.pro/webfonts-genyo-gothic-tc` | 源樣黑體 GenYo Gothic TC | 黑 sans | static | 7 | 丹版/TC (傳承印刷體) |
| `@hanzi.pro/webfonts-lxgw-wenkai-tc` | LXGW WenKai TC 霞鶩文楷 | 楷 cursive | static | 3 | 傳承字形 (TC) |
| `@hanzi.pro/webfonts-lxgw-wenkai` | LXGW WenKai 霞鶩文楷 | 楷 cursive | static | 3 | 傳承字形 (SC) |
| `@hanzi.pro/webfonts-iansui` | Iansui 芫荽 | 楷 cursive | static | 1 | 國字標準字體 (MOE) |
| `@hanzi.pro/webfonts-klee-one` | Klee One | 楷 cursive | static | 2 | JP 楷 (Klee) |

GenYo weights: serif `250 300 400 500 600 700 900`, sans `250 300 350 400 500 700 900`.
LXGW weights: `300 400 500`. Klee One weights: `400 600`.

楷 (cursive) is offered widest because system 楷 fonts are scarce on mobile and
restricted in macOS Safari — webfonts are often the only option. LXGW = 傳承字形
(TC + SC); Iansui = 國字標準字體; Klee One = the JP cut.

## Printed vs. handwriting: where MOE standard forms are (dis)allowed

cheritage's correction target is the **printed** styles. The ban on the MOE
national standard (國字標準字體) applies to **明 (serif) and 黑 (sans)** only — the
faces where heritage vs. standard forms are a real typographic choice.

**楷 (style `cursive`) is a handwriting style**, and in handwriting the MOE
standard forms are legitimate (they are, after all, modelled on handwriting). So
cheritage admits a 楷 font that follows the MOE standard:

- **`@hanzi.pro/webfonts-iansui`** (Iansui 芫荽) — a **國字標準字體** 楷. Allowed because it
  is handwriting, not print.
- **`@hanzi.pro/webfonts-lxgw-wenkai-tc`** (LXGW WenKai TC) — a **傳承字形** 楷 (Klee-based).

Both ship side by side so users **freely choose** the kai orthography they want.
The print faces (Shanggu, GenYo) remain heritage-only.

## Usage

```css
/* flagship: Shanggu, variable, full 舊字形 */
@import url("https://cdn.jsdelivr.net/npm/@hanzi.pro/webfonts-shanggu-serif/index.css");
@import url("https://cdn.jsdelivr.net/npm/@hanzi.pro/webfonts-shanggu-sans/index.css");

/* static families import index.css (all weights) or a single weight, e.g. ./400.css */
@import url("https://cdn.jsdelivr.net/npm/@hanzi.pro/webfonts-lxgw-wenkai-tc/400.css");

:root {
  --han-heritage-serif: "Shanggu Serif";
  --han-heritage-sans:  "Shanggu Sans";
}
```

The browser downloads only the slices your page hits. Uncovered codepoints fall
through to the next font in your stack (by design — no tofu, and the mechanism by
which JP/KR/SC stay on system fonts).

### Which CDN

The packages are plain npm packages, so **any npm CDN serves them** — switching
host is just editing the `@import` URL, no republish. Recommended:

- **jsDelivr (default).** Multi-CDN with automatic failover, purpose-built for
  static npm assets, immutable caching on versioned paths, widest global reach.
  Use it unless you have a reason not to.
  ```css
  @import url("https://cdn.jsdelivr.net/npm/@hanzi.pro/webfonts-shanggu-serif/index.css");
  ```
- **unpkg (Asia fallback).** Cloudflare-fronted; from a Taipei POP it measured
  noticeably faster than jsDelivr (which routed via Singapore/Frankfurt). Good
  primary if your audience is overwhelmingly Taiwan/Asia — trading jsDelivr's
  multi-CDN resilience for lower regional latency.
  ```css
  @import url("https://unpkg.com/@hanzi.pro/webfonts-shanggu-serif/index.css");
  ```

Pin a version for production (`@hanzi.pro/webfonts-shanggu-serif@1.2.3/...`); jsDelivr and
unpkg serve versioned paths immutably, so the npm version is your cache-buster.

### System font first (`local()`)

Where a font commonly ships on the OS, its `@font-face src` lists `local()`
before the webfont url, so a browser that already has it downloads **nothing**:

```css
src: local("Klee One"), local("Klee"), url(./files/klee-one.400.0.woff2) format('woff2');
```

`@hanzi.pro/webfonts-klee-one` (macOS often has Klee) and `@hanzi.pro/webfonts-lxgw-wenkai` prefer
the local copy and only fetch slices when it is absent.

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
