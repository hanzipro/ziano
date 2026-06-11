# cheritage — deferred TODO

## Skip empty/near-empty slices for narrow-coverage fonts

**Context:** the slice table has ~108 `unicode-range` buckets (snapshot of Noto's
partition). Wide fonts (Shanggu, GenYo, LXGW) fill almost all of them, but a
narrow font like **Klee One** (~10k glyphs, JP-flavoured) covers nothing in many
slices. We still emit a `@font-face` + a woff2 for those — the woff2 is a valid
but near-empty file (.notdef only), and the `@font-face`'s `unicode-range` can
never match a glyph the font has.

**Do:** in `build.py` (and/or `cssgen.py`), when a slice's codepoints have **zero
intersection** with the font's cmap for a given weight, skip generating both the
woff2 and the `@font-face` block for that (weight, slice). Mirrors what Google
Fonts does (it omits ranges the font doesn't cover).

**Where:** `cheritage.coverage.cmap_codepoints` already gives the font's cmap;
intersect with `Slice.codepoints()`. Guard inside the per-slice loops of
`_build_vf` / `_build_static`, and filter the slice list passed to `generate_css`
per weight so CSS and files stay in sync.

**Payoff:** smaller Klee package, fewer dead `@font-face` rules. Mainly benefits
narrow-coverage fonts; wide fonts are barely affected.

**Test:** build `klee-one` and assert no `klee-one.*.woff2` exists for a slice
that is purely in a block Klee lacks (e.g. a CJK Ext-B-only slice), and that
`400.css` has fewer `@font-face` than the full 108.
