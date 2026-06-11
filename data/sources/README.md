# Slice-table source & attribution

`../slices.traditional-chinese.json` is **generated** from
`traditional-chinese_default.txt` in this directory by
`cheritage.slices.parse_slicing_strategy`.

## Provenance

`traditional-chinese_default.txt` is Google Fonts' canonical Traditional-Chinese
**slicing strategy** — the `unicode-range` partition the Google Fonts CSS API uses
to split CJK fonts into ~120 frequency-based subsets.

- **Source:** [`googlefonts/nam-files`](https://github.com/googlefonts/nam-files),
  file `slices/traditional-chinese_default.txt`.
- **License:** **Apache License 2.0** — https://www.apache.org/licenses/LICENSE-2.0
- **Pinned copy:** committed here verbatim (unmodified) for reproducible builds.
  `sha256 = 7fed53a1c91c1852d1cb43211d03d5001ad288ab86396b2fc1552ffd026c8f8e`
- **Methodology:** "How Google Fonts slices CJK" (Sheeter), Unicode Conf. #42 —
  referenced inside the file header. The header documents the algorithm: ~20
  `FreqRange` slices of ~213 high-frequency codepoints each, then the remaining
  ~13,453 codepoints split into 100 codepoint-ordered bins.

## Why we use this rather than scraping the CSS API

The `css2` API response is the *rendered* form of this same data but carries no
explicit license. Deriving directly from the Apache-2.0 `nam-files` source gives a
clean, attributable licensing chain. cheritage does **not** redistribute any Google
font — only this openly-licensed codepoint partition, applied to our own OFL fonts.

## Updating

The strategy is versioned by Google. To refresh: replace the `.txt` from the
pinned source, re-run the generator, and bump package versions (slice indices may
shift — see spec §9.5). Do **not** hand-edit the partition.
