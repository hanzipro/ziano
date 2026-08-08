# ziano・傳承字形 webfont CDN

Free, CDN-hosted, drop-in **傳承字形 / 舊字形** (heritage / orthodox glyph form)
Traditional-Chinese webfonts. ziano does for heritage CJK what
[Fontsource](https://github.com/fontsource/fontsource) does for Latin: it slices
OFL fonts into `unicode-range` woff2 subsets and publishes per-family npm
packages, so jsDelivr/unpkg serve them for free and a page downloads only the
glyphs it actually uses.

> Why: almost every TC webfont on the open web renders Taiwan's MOE national
> standard forms (國字標準字體). ziano serves the orthodox heritage forms
> instead. JP/SC/KR runs deliberately fall through to system fonts.

See `docs/superpowers/specs/` for the full design.

## Roster

黑 (sans)・明 (serif)・楷 (cursive) — all three styles covered.

| Package | Family | Style | Format | Weights | Glyph forms |
|---|---|---|---|---|---|
| `@hanzi.pro/webfonts-shanggu-serif` | 尚古宋 Shanggu Serif | 明 serif | **VF** | 250–900 | **full 舊字形**・丹 (異體字增強, flagship) |
| `@hanzi.pro/webfonts-shanggu-sans` | 尚古黑 Shanggu Sans | 黑 sans | **VF** | 250–900 | **full 舊字形**・丹 (異體字增強, flagship) |
| `@hanzi.pro/webfonts-shanggu-serif-yue` | 尚古宋 Shanggu Serif Yue | 明 serif | **VF** | 250–900 | **full 舊字形**・月 (Unicode 忠實) |
| `@hanzi.pro/webfonts-shanggu-sans-yue` | 尚古黑 Shanggu Sans Yue | 黑 sans | **VF** | 250–900 | **full 舊字形**・月 (Unicode 忠實) |
| `@hanzi.pro/webfonts-genki-serif-yue` | 源起明體 Genki Serif Yue | 明 serif | static | 7 | neutral・月 (milder, default-alt) |
| `@hanzi.pro/webfonts-genki-sans-yue` | 源起黑體 Genki Sans Yue | 黑 sans | static | 6 | neutral・月 (milder, default-alt) |
| `@hanzi.pro/webfonts-genki-serif` | 源起明體 Genki Serif | 明 serif | static | 7 | 丹 (傳承印刷體) |
| `@hanzi.pro/webfonts-genki-sans` | 源起黑體 Genki Sans | 黑 sans | static | 6 | 丹 (傳承印刷體) |
| `@hanzi.pro/webfonts-lxgw-wenkai-tc` | LXGW WenKai TC 霞鶩文楷 | 楷 cursive | static | 3 | 傳承字形 (TC) |
| `@hanzi.pro/webfonts-lxgw-wenkai` | LXGW WenKai 霞鶩文楷 | 楷 cursive | static | 3 | 傳承字形 (SC) |
| `@hanzi.pro/webfonts-iansui` | Iansui 芫荽 | 楷 cursive | static | 1 | 國字標準字體 (MOE) |
| `@hanzi.pro/webfonts-klee-one` | Klee One | 楷 cursive | static | 2 | JP 楷 (Klee) |

Genki weights: serif `250 300 400 500 600 700 900`, sans
`250 300 400 500 700 900` (no 350). LXGW weights: `300 400 500`. Klee One weights: `400 600`.

**丹 vs 月:** 丹 is the more-heritage 傳承印刷體 cut, 月 the milder / Unicode-faithful
one. **No suffix always means 丹** — one rule, both families. Before 0.2.0 the suffix
was `-tc`, which pointed opposite ways between them (Shanggu's base was 丹, Genki's
was 月) and had to be explained every time; now `-yue` marks 月 explicitly and `-tc`
means only what it says — a region variant, which is left to LXGW WenKai alone.
The 丹 packages also ship their faces under the qualified `… Dan` name — see
*Saying the cut out loud*.

Shanggu (VF) covers the full 舊字形 in both cuts — 丹 異體字-merges (内→內 even when you
typed 内), 月 stays codepoint-faithful. Genki is the smaller, neutral default-alt.

Genki's Latin names changed with the same release: **Min／Gothic → Serif／Sans**, to
match Shanggu and Source Han's own naming (思源宋體/黑體 = Source Han **Serif/Sans**),
and the `--font-serif` / `--font-sans-serif` generics you plug them into. Upstream
still calls them GenKi **Min** / GenKi **Gothic** — that is ButTaiwan's series
convention (源流 GenRyuMin, 源雲 GenWanMin), not a mistake, so look for those names
when you go back to the source.

> 源樣 GenYo (`@hanzi.pro/webfonts-genyo-*`) — Genki's visually-identical but
> 17–24 % larger predecessor — stays published but is no longer promoted; reach for
> Genki instead.

楷 (cursive) is offered widest because system 楷 fonts are scarce on mobile and
restricted in macOS Safari — webfonts are often the only option. LXGW = 傳承字形
(TC + SC); Iansui = 國字標準字體; Klee One = the JP cut.

## What the build changes about the fonts

Subsetting is not the only edit. Two normalisations are applied to every family
**before slicing**, because both are file-level properties that CSS cannot reach:

**Line metrics → `hhea 1100/−340`, `usWin 1100/340`.** In vertical writing mode
Chromium *and Safari* synthesise a glyph's central baseline as
`(ascent − |descent|) / 2`, taken from whichever font drew the glyph — and a
`unicode-range`-segmented `@font-face` is never the line's first available font, so
these faces always take that path. Upstream disagrees wildly (Source Han lineage
`1151/−286` → 0.4325em, ButTaiwan `880/−120` → 0.380em, LXGW WenKai `928/−256` →
0.336em), which lands two families **up to 0.0965em apart across the column** — a
visible sideways jog wherever a 楷 quotation or a punctuation face sits inside body
text. Every family now carries the same 0.380em centre (the em box, and what
Hiragino / YuMincho / 源起 / 芫荽 already use, so the position holds when the webfont
fails and a system font takes over). The sum, 1.44em, only sets `line-height: normal`
and is kept close to Shanggu's own 1.437em.

The stylesheets restate the same numbers as `ascent-override` / `descent-override`,
derived from one constant so they cannot drift — but the CSS is *not* the fix:
Safari ignores those descriptors for this path, which is why the numbers are written
into the files. Full derivation and measurements: `docs/vertical-baseline-offset.md`.

**`：` and `；` stay upright.** UTR50 classes U+FF1A and U+FF1B as **Tr** — rotate by
default unless the font's `vert` feature substitutes them. Firefox implements that
faithfully, so on a font with no rule for them the colons lie on their side in
vertical text (Chrome and Safari are lax and leave them upright either way). The
build registers an identity (sentinel) substitution — the glyph maps to itself — which
costs nothing visually and flips Firefox out of the rotate branch. Fonts that already
map them are left alone: Klee One sends `：` to a genuinely rotated JP form and LXGW
WenKai SC to a re-centred one, and that is the designer's convention, not an oversight.

**The files say who changed them.** The shipped `name` table reads
`Ziano Shanggu Serif` / `Ziano 尙古明體丹`, not `Shanggu Serif VF` — so a
font manager, a desktop install, or anyone poking at the woff2 sees a file that
admits it is a derivative. This is not an OFL requirement: none of the upstreams
reserves the names we ship (Shanggu declares no copyright line at all; LXGW
WenKai and Iansui name only their project authors; the Source Han derivatives
reserve Adobe's `Source`, which we never use). It is honesty — the three edits
above are invisible in a glyph diff. Weight names, copyright and licence records
stay exactly as upstream wrote them.

**The prefix is internal only.** Your CSS says `Shanggu Serif`, and so do
these stylesheets, the docs and the demos. A `@font-face` family is a label the
author picks; making everyone type a publisher name into their font stacks would
be branding, not honesty.

All three edits are listed in each package's `LICENSE`, under a MODIFICATIONS
section after the OFL text.

## Printed vs. handwriting: where MOE standard forms are (dis)allowed

ziano's correction target is the **printed** styles. The ban on the MOE
national standard (國字標準字體) applies to **明 (serif) and 黑 (sans)** only — the
faces where heritage vs. standard forms are a real typographic choice.

**楷 (style `cursive`) is a handwriting style**, and in handwriting the MOE
standard forms are legitimate (they are, after all, modelled on handwriting). So
ziano admits a 楷 font that follows the MOE standard:

- **`@hanzi.pro/webfonts-iansui`** (Iansui 芫荽) — a **國字標準字體** 楷. Allowed because it
  is handwriting, not print.
- **`@hanzi.pro/webfonts-lxgw-wenkai-tc`** (LXGW WenKai TC) — a **傳承字形** 楷 (Klee-based).

Both ship side by side so users **freely choose** the kai orthography they want.
The print faces (Shanggu, Genki) remain heritage-only.

## Usage

```css
/* flagship: Shanggu 丹, variable, full 舊字形 */
@import url("https://cdn.jsdelivr.net/npm/@hanzi.pro/webfonts-shanggu-serif/swap.css");
@import url("https://cdn.jsdelivr.net/npm/@hanzi.pro/webfonts-shanggu-sans/swap.css");

/* every package ships swap.css (default), block.css and optional.css.
   static families also expose one file per weight, e.g. swap/400.css */
@import url("https://cdn.jsdelivr.net/npm/@hanzi.pro/webfonts-lxgw-wenkai-tc/swap/400.css");

:root {
  --han-heritage-serif: "Shanggu Serif";
  --han-heritage-sans:  "Shanggu Sans";
}
```

The browser downloads only the slices your page hits. Uncovered codepoints fall
through to the next font in your stack (by design — no tofu, and the mechanism by
which JP/KR/SC stay on system fonts).

### Saying the cut out loud

On npm **no suffix always means 丹**: `webfonts-shanggu-serif` is the 丹 cut, as
it was in 0.1.0, and `webfonts-shanggu-serif-yue` is the 月 one. So the default
stylesheet declares the plain name — nothing to migrate, and one rule to
remember.

For a stack that would rather name the cut, every unsuffixed package also ships
the same faces under the qualified name:

```css
/* one font, two labels — import ONE of them */
@import url(".../webfonts-shanggu-serif/swap.css");      /* 'Shanggu Serif'     */
@import url(".../webfonts-shanggu-serif/dan/swap.css");  /* 'Shanggu Serif Dan' */
```

`block.css` and `optional.css` have the same twin under `dan/` (static families
also get `dan/swap/<weight>.css`), and the package exports it as
`@hanzi.pro/webfonts-shanggu-serif/dan`. Importing both is harmless but
pointless: identical URLs, every face declared twice under two names.

The font files themselves always carry the qualified name — a `name` table has
no room for ambiguity. See *What the build changes about the fonts*.

### Which CDN

The packages are plain npm packages, so **any npm CDN serves them** — switching
host is just editing the `@import` URL, no republish. Recommended:

- **jsDelivr (default).** Multi-CDN with automatic failover, purpose-built for
  static npm assets, immutable caching on versioned paths, widest global reach.
  Use it unless you have a reason not to.
  ```css
  @import url("https://cdn.jsdelivr.net/npm/@hanzi.pro/webfonts-shanggu-serif/swap.css");
  ```
- **unpkg (Asia fallback).** Cloudflare-fronted; from a Taipei POP it measured
  noticeably faster than jsDelivr (which routed via Singapore/Frankfurt). Good
  primary if your audience is overwhelmingly Taiwan/Asia — trading jsDelivr's
  multi-CDN resilience for lower regional latency.
  ```css
  @import url("https://unpkg.com/@hanzi.pro/webfonts-shanggu-serif/swap.css");
  ```

Pin a version for production (`@hanzi.pro/webfonts-shanggu-serif@0.2.0/...`); jsDelivr and
unpkg serve versioned paths immutably, so the npm version is your cache-buster.

### System font first (`local()`)

Where a font commonly ships on the OS, its `@font-face src` lists `local()`
before the webfont url, so a browser that already has it downloads **nothing**:

```css
src: local("Klee One"), local("Klee"), url(./files/klee-one.400.0.woff2) format('woff2');
```

`@hanzi.pro/webfonts-klee-one` (macOS often has Klee) and `@hanzi.pro/webfonts-lxgw-wenkai` prefer
the local copy and only fetch slices when it is absent.

> Tip: for static families, `swap.css` inlines every weight's `@font-face`. If you
> only need one or two weights, import those `swap/<weight>.css` files directly to
> cut bytes.

## Build

```bash
uv sync
uv run python -m ziano.build <family-id>   # e.g. shanggu-serif
uv run pytest -q                                # add -m "not integration" to skip downloads
```

All fonts are OFL 1.1; each package bundles its upstream license. Sources are
pinned by release tag + sha256 in `roster.toml`.
