# Changelog

## 0.2.0 — unreleased

### Naming: no suffix always means 丹

`-tc` meant opposite cuts in the two families it was used on — 尚古's
unsuffixed package was 丹 and its `-tc` was 月, while 源起's `-tc` was 丹 and
its unsuffixed was 月. One rule now: **no suffix is 丹, `-yue` is 月**.

| 0.1.0 | upstream | cut | 0.2.0 |
|---|---|---|---|
| `webfonts-shanggu-serif` | `ShangguSerif-VF` | 丹 | unchanged |
| `webfonts-shanggu-serif-tc` | `ShangguSerifTC-VF` | 月 | `webfonts-shanggu-serif-yue` |
| `webfonts-genki-min` | `GenKiMin2TW` | 月 | `webfonts-genki-serif-yue` |
| `webfonts-genki-min-tc` | `GenKiMin2TC` | 丹 | `webfonts-genki-serif` |

**No package changed which upstream file it ships.** Every surviving id points
at the same source it always did, so nobody's install silently changes glyphs;
源起's four old names all retire, and its four new ones are all first
releases. Migrating by hand, though, means reading the table — the suffix
means the opposite of what it did.

Min / Gothic become Serif / Sans, so 源起 gains four new package names and
retires four. Each unsuffixed package also ships its faces under the
qualified name from `dan/`: `dan/swap.css` declares `'Shanggu Serif Dan'`
against the very same woff2, for stacks that would rather say the cut aloud.

### Metrics

Every shipped slice is normalised to `hhea 1100 / −340`, a central baseline of
0.380em. A `unicode-range`-segmented face is never the line's first available
font, so browsers synthesise its vertical central baseline from `hhea` —
Chromium *and* Safari, and CSS `ascent-override` does not reach it. Upstream
values ranged from 0.336 to 0.436, which is what made kai and body text drift
apart down a vertical column.

### `：；` stay upright in vertical writing

Thirteen families gained an identity `vert` substitution for U+FF1A / U+FF1B.
UTR50 class Tr rotates them unless the font says otherwise, and Firefox is
strict about it.

### Font names

Shipped files identify themselves as `Ziano <family>` — the subsetting, the
metric normalisation and the `vert` rule make them derived works, and a file
that still answers to its upstream name misrepresents all three. **The prefix
is internal to the font file**: stylesheets, docs and demos say
`'Shanggu Serif'`. Localised names are kept localised, with zh-Hant and
zh-Hans slots carrying the orthography upstream uses for each.

Each package's `LICENSE` carries the upstream text plus a MODIFICATIONS
section stating all four changes.

## 0.1.0

First release: heritage-glyph CJK webfonts as Fontsource-style
`unicode-range` woff2 subsets, one npm package per family.
