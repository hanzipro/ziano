# How Google Fonts slices CJK with `unicode-range` — research report

**Date:** 2026-06-12 · **Scope:** the partition logic cheritage snapshots into
`data/slices.{sans,serif}.json`. Combines (a) Google's official statements and
(b) empirical analysis of the live `css2` responses we captured in
`tests/fixtures/noto-{sans,serif}-tc.css2.txt` (Noto TC, `v39`).

---

## TL;DR

- A CJK font is split into **~105–110 `unicode-range` subsets** ("slices"), each a
  separate woff2. Every slice is declared as one `@font-face` with a
  `unicode-range`; the **browser downloads only the slices whose range intersects
  the text actually on the page**.
- The split is **frequency / co-occurrence based, not codepoint-based**. Google
  built **topic models from real web text** ("which characters appear together on
  the same page") so that the few high-frequency characters cluster into a handful
  of slices and each rare character is isolated.
- **Empirically (Noto TC v39):** a normal paragraph of Traditional Chinese hits
  **~7 slices**; the ~90 most frequent characters live in **5 slices** (and ~78 of
  them in just **2**); **10 random rare characters land in 10 different slices**.
  Basic Latin/ASCII sits in the final slice and is effectively always loaded.
- That is the whole trick: **common text → a few cache-shared files; a rare
  character → one extra tiny file, only if you use it.**

---

## 1. The delivery mechanism

The `css2` response is a list of `@font-face` blocks that share a `font-family`
but differ in `src` (one woff2 per slice) and `unicode-range`:

```css
@font-face {
  font-family: 'Noto Sans TC';
  font-weight: 100 900;
  src: url(https://fonts.gstatic.com/s/notosanstc/v39/…<hash>.99.woff2) format('woff2');
  unicode-range: U+4e00-4e0f, U+4e11, U+4e3d, … ;   /* ~200 scattered codepoints */
}
```

Per the CSS spec, the browser **lazily fetches a `unicode-range` font only when a
glyph it covers is needed**. So all ~108 rules are parsed, but only the woff2 for
ranges present on the page are requested — fetched in parallel over one HTTP/2
connection.

The `.<n>.woff2` number is Google's **stable slice id**; `v39` is the partition
version. Stability matters: identical slice URLs across sites = shared browser
cache.

## 2. How Google builds the partition (official)

From Google's own write-up of the launch
([Developers Blog](https://developers.googleblog.com/en/google-fonts-launches-korean-support/))
and the web-fonts API article
([web.dev](https://web.developers.google.cn/articles/api-for-fast-beautiful-web-fonts)):

- They analysed **text on the live web** to "extract patterns of Unicode
  characters, **building topic models of which ones tend to appear together on the
  same page**."
- The objective is to **minimise the number of subsets *and* the number of HTTP
  requests a real page triggers** — explicitly *not* equal-sized chunks. Their
  measured result: the best strategy had **"20× fewer connection requests than the
  worst, which simply divides the font into equal parts."**
- They validated strategies against **real-world traffic** via the Early Access
  system before shipping.
- The exact clustering algorithm and frequency cut-offs are **kept proprietary**.

The actual codepoint sets are open, though: Google publishes them as **"nam
files"** in
[`googlefonts/nam-files`](https://github.com/googlefonts/nam-files) — one codepoint
(`0x….`) per line, machine-readable under `Lib/gfsubsets/data`, and they are what
the CSS API uses to subset before serving. (cheritage doesn't parse nam files; it
snapshots the *resolved* ranges straight from the `css2` response, which already
reflects them.)

## 3. What the data actually shows (empirical)

Measured on the captured Noto **Sans** TC (`105` slices) and **Serif** TC (`108`
slices); both behave identically.

| metric | Noto Sans TC |
|---|---|
| slices | 105 |
| codepoints covered | 16,254 |
| …of which CJK Unified (U+4E00–9FFF) | 12,564 |
| codepoints per slice | min 102 · **mean 161** · max 1,162 |
| `unicode-range` fragments per slice | min 5 · **mean 93** · max 212 |

### 3a. Slices are frequency-ordered (rarest → commonest), Latin last

Walking the slice index from 0 upward:

- **index 0–~9 (rarest):** CJK Ext-A (U+3400+), compatibility ideographs
  (U+FA0A), half-width kana (U+FF78), emoji (U+1F9xx). e.g. slice 0 = `㐁㑁㓾…`.
- **index ~10–~95:** the bulk of CJK Unified, **frequency-graded** — density of
  common characters rises with the index (CJK-Unified chars per 10-slice band:
  752 → ~1,350 → **1,765 (80s) → 1,922 (90s)**).
- **index ~95–~103 (commonest Han):** where ordinary text lands.
- **final 2–4 slices:** Latin Extended, then **Basic Latin / ASCII / Latin-1**
  (slice 104, `U+0000…`). ASCII is universal, so it is effectively always fetched.

Within a slice the codepoints are **scattered across the whole code space** (mean
93 disjoint ranges per slice) — direct evidence the grouping is by *frequency /
co-occurrence*, not by code point.

### 3b. Common characters are guaranteed to hit few slices

| test (Noto Sans TC) | result |
|---|---|
| Common TC paragraph (~65 distinct chars) | **7 slices** (idx 93–103) |
| Top ~89 most-frequent characters | **5 slices** (idx 96–100) |
| …concentration | **78 of 89** chars fall in just **2 slices** (99 & 100) |
| Those common slices' size | uniform **213 codepoints** each |

So a typical CJK page downloads the ASCII slice + ~5–8 common-Han slices =
**~6–9 small woff2 (~30–100 KB each)**, almost all shared with every other site
using the same font. This is *the* mechanism that "ensures common characters are
hit cheaply."

### 3c. Rare characters are isolated

| test | result |
|---|---|
| 10 assorted rare chars (鬱靈鑑釁衞夔饕餮龘鱻) | land in **10 different slices** (idx 4, 6, 9, 15, 22, 60, 81, 88, 92, 96) |

Each uncommon character sits in its own low-index slice, so using one rare glyph
pulls in exactly **one** extra tiny file — and only if the page actually contains
it. Pages that never use 鬱 never download 鬱's slice.

## 4. Why this shape is optimal

- **Frequency grouping** ⇒ the 80/20 of text is satisfied by a few always-cached
  slices → minimal requests for the common case.
- **Isolation of rare glyphs** ⇒ the long tail costs nothing unless used, and one
  rare glyph never drags in a big bucket of unrelated rare glyphs.
- **Co-occurrence modelling** ⇒ characters that appear together (same slice)
  reduce the *number* of requests vs. naive frequency bucketing (the 20× win).
- **Stable ids + immutable URLs** ⇒ cross-site browser-cache sharing.
- Cost paid: **CSS is verbose** (mean 93 range fragments/slice → ~100 KB of CSS),
  but it gzip/brotli-compresses to ~20–33 KB and is fetched once.

## 5. Implications for cheritage

- We **snapshot the resolved Noto TC ranges** (`data/slices.{sans,serif}.json`),
  so we **inherit Google's frequency tuning for free** — our Shanggu/GenYo/LXGW
  packages get the same "common text → few files" behaviour without re-deriving a
  partition.
- We slice the **whole font** against this table; with `unicode-range` a TC page
  only ever pulls the common-Han + ASCII slices regardless of what else the font
  covers (the rationale already in spec §4).
- **Caveat for narrow fonts (already in `docs/TODO.md`):** the table assumes
  Noto-level coverage. A small font like **Klee One (~10k glyphs)** leaves many
  slices empty/near-empty — those should be skipped (no woff2, no `@font-face`),
  exactly as Google omits ranges a font doesn't cover.
- **Refresh discipline:** the partition is versioned (`v39`). If we ever
  regenerate `data/slices.*.json`, slice ids shift and break cross-version cache
  reuse — so treat the snapshot as a pinned, deliberately-bumped asset (spec §9.5).

## 6. The successor: Incremental Font Transfer (IFT)

`unicode-range` is the current best; the **W3C
[Incremental Font Transfer](https://w3c.github.io/IFT/Overview.html)** spec is its
replacement. IFT streams only the exact glyphs a page uses (and patches in more on
demand) from a single font URL, "surpassing the performance of unicode-range" and
eliminating the ~100-rule CSS and empty-slice waste. Chrome has shipped early
support. **Not actionable for cheritage now** (needs server-side IFT + broad
browser support), but it's the direction the whole approach is heading — worth a
revisit before any large-scale production push.

## Sources

- Google Developers Blog — *Google Fonts launches Korean support*: https://developers.googleblog.com/en/google-fonts-launches-korean-support/
- web.dev — *An API for fast, beautiful web fonts*: https://web.developers.google.cn/articles/api-for-fast-beautiful-web-fonts
- `googlefonts/nam-files` — the subset codepoint definitions: https://github.com/googlefonts/nam-files
- W3C — *Incremental Font Transfer*: https://w3c.github.io/IFT/Overview.html
- Primary data: `tests/fixtures/noto-{sans,serif}-tc.css2.txt` (Noto TC `v39`), analysed via `cheritage.slices`.
