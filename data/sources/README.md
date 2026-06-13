# Slice-table source & attribution

The `../slices.<script>.json` tables are **generated** from the `*_default.txt`
slicing strategies in this directory by `cheritage.slices.parse_slicing_strategy`:

| Generated table | Source strategy file | Used by (default) |
|---|---|---|
| `slices.traditional-chinese.json` | `traditional-chinese_default.txt` | all TC print/handwriting families |
| `slices.simplified-chinese.json` | `simplified-chinese_default.txt` | `lxgw-wenkai` (SC) — `slice_table` override |
| `slices.japanese.json` | `japanese_default.txt` | `klee-one` (JP) — `slice_table` override |

A family slices with its **default script's** partition so script-specific
codepoints (鹜 in SC, ゐ/々/凜 in JP) land in a subset instead of being dropped
when sliced against the TC partition. The override is set per family in
`roster.toml` via `slice_table = "simplified-chinese" | "japanese"`.

## Provenance

All three are Google Fonts' canonical per-script **slicing strategies** — the
`unicode-range` partitions the Google Fonts CSS API uses to split CJK fonts into
~120 frequency-based subsets.

- **Source:** [`googlefonts/nam-files`](https://github.com/googlefonts/nam-files),
  files `slices/{traditional-chinese,simplified-chinese,japanese}_default.txt`.
- **License:** **Apache License 2.0** — https://www.apache.org/licenses/LICENSE-2.0
- **Pinned commit:** `1d38a7d77ce11452ccbfe8fa9a0cb728ee6d7cd3` (the SC + JP files
  were fetched from this commit; copies committed here verbatim).
- **sha256:**
  - `traditional-chinese_default.txt`: `87c207802e3de930f7ee65cfe8564ebb25f244ee986cf50310ef7c6e8722e0ca`
  - `simplified-chinese_default.txt`: `cd022036048744a478b2d261131a90400bacbb9098b83efd0360f1e44122c2c1`
  - `japanese_default.txt`: `3032f27de94485ab2885c14b927b35d12e31a281ad4eb287b9ec28fe45b8509d`
- **Methodology:** "How Google Fonts slices CJK" (Sheeter), Unicode Conf. #42 —
  referenced inside each file header. The header documents the algorithm: ~20
  `FreqRange` slices of high-frequency codepoints each, then the remaining
  codepoints split into codepoint-ordered bins (120 subsets total per script).

## Why we use this rather than scraping the CSS API

The `css2` API response is the *rendered* form of this same data but carries no
explicit license. Deriving directly from the Apache-2.0 `nam-files` source gives a
clean, attributable licensing chain. cheritage does **not** redistribute any Google
font — only this openly-licensed codepoint partition, applied to our own OFL fonts.

## Updating

The strategy is versioned by Google. To refresh: replace the `.txt` from the
pinned source, re-run the generator, and bump package versions (slice indices may
shift — see spec §9.5). Do **not** hand-edit the partition.
