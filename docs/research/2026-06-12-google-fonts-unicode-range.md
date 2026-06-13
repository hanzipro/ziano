# How Google Fonts slices CJK with `unicode-range` — research report

**Date:** 2026-06-12・**Scope:** the partition logic cheritage uses in
`data/slices.traditional-chinese.json`. Combines (a) Google's official slicing
strategy — the Apache-2.0 text-proto pinned at
`data/sources/traditional-chinese_default.txt` (from `googlefonts/nam-files`) —
and (b) our empirical analysis of it.

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
- That is the whole trick: **common text → a few small files; a rare character →
  one extra tiny file, only if you use it.** (Note: modern browsers *partition* the
  HTTP cache per top-level site — Chrome 86+, Firefox 85+, Safari since 2013 — so
  these files are **not** reused across different sites; each site downloads them
  itself once, then reuses within that site.)

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

The actual strategy is open, not proprietary: Google publishes it in
[`googlefonts/nam-files`](https://github.com/googlefonts/nam-files) under
`slices/traditional-chinese_default.txt` — a text-proto whose header documents the
exact construction (**Apache-2.0**; cheritage pins it at
`data/sources/traditional-chinese_default.txt`):

> `17704 codepoints in 120 subsets … From highest to lowest priority:`
> `1–20: FreqRange target_len 213 … 21: Remaining 13453 in 100 bins, sorted by codepoint`

So the algorithm is concretely:

1. **FreqRange slices (~20):** the highest-frequency codepoints packed into
   uniform **~213-codepoint** slices, in frequency-priority order.
2. **Remaining (~13,453 codepoints):** the long tail split into **100 bins ordered
   by codepoint** (not frequency — order is irrelevant once a glyph is rare).

cheritage parses this proto directly (`cheritage.slices.parse_slicing_strategy`)
into `data/slices.traditional-chinese.json` — one canonical TC partition reused for
every style.

## 3. What the data actually shows (empirical)

Measured on the canonical table (`data/slices.traditional-chinese.json`).

| metric | value |
|---|---|
| slices | 120 |
| codepoints covered | 17,704 |
| …of which CJK Unified (U+4E00–9FFF) | 12,548 |
| codepoints per slice | min 134・**mean 147**・max 214 |

### 3a. Slices are frequency-ordered (rarest → commonest), ASCII last

Block order runs from rarest to commonest:

- **slice 0 (rarest):** emoji (U+1F921 🤡); the early slices are the "Remaining"
  codepoint-ordered bins — CJK Ext-A, compatibility ideographs, half-width kana.
- **middle slices:** the long tail of CJK Unified.
- **last ~20 slices (~100–119):** the `FreqRange` blocks — the highest-frequency
  Han, uniform ~213 codepoints each.
- **final slice (119):** Basic Latin / ASCII (`U+20…`) — universal, effectively
  always fetched.

Within a slice the codepoints are **scattered across the whole code space** —
direct evidence the grouping is by *frequency*, not by code point.

### 3b. Common characters are guaranteed to hit few slices

| test | result |
|---|---|
| Common TC paragraph (53 distinct chars) | **7 slices** (idx 113–119) |
| Top ~89 most-frequent characters | **4 slices** (idx 115, 117–119) |
| FreqRange slice size | uniform **~213 codepoints** each |

So a typical CJK page downloads the ASCII slice + ~5–8 common-Han slices =
**~6–9 woff2 (≈0.5–1 MB total for a VF serif; less for sans/static)**, fetched once
per site and then reused across that site's pages. This is *the* mechanism that
"ensures common characters are hit cheaply." (Per-site, not cross-site — see §4 on
cache partitioning.)

### 3c. Rare characters are isolated

| test | result |
|---|---|
| 10 assorted rare chars (鬱靈鑑釁衞夔饕餮龘鱻) | land in **10 different slices** |

Each uncommon character sits in its own bin, so using one rare glyph pulls in
exactly **one** extra tiny file — and only if the page actually contains it. Pages
that never use 鬱 never download 鬱's slice.

## 4. Why this shape is optimal

- **Frequency grouping** ⇒ the 80/20 of text is satisfied by a few always-cached
  slices → minimal requests for the common case.
- **Isolation of rare glyphs** ⇒ the long tail costs nothing unless used, and one
  rare glyph never drags in a big bucket of unrelated rare glyphs.
- **Co-occurrence modelling** ⇒ characters that appear together (same slice)
  reduce the *number* of requests vs. naive frequency bucketing (the 20× win).
- **Stable ids + immutable URLs** ⇒ within-site cache reuse (across a site's pages
  and repeat visits) + CDN edge caching. **Not** cross-site: modern browsers
  partition the HTTP cache by top-level site (Chrome 86+, Firefox 85+, Safari since
  2013), so the old "shared CDN cache across sites" benefit is gone — each site
  downloads the slices itself once. The win is now CDN-edge speed + within-site
  reuse, not cross-site sharing.
- Cost paid: **CSS is verbose** (codepoints scatter into many range fragments →
  ~100 KB of CSS), but it gzip/brotli-compresses to ~20–33 KB and is fetched once.

## 5. Implications for cheritage

- We **derive the partition from the Apache-2.0 `nam-files` strategy**
  (`data/slices.traditional-chinese.json`, generated from
  `data/sources/traditional-chinese_default.txt`), so we **inherit Google's
  frequency tuning for free** — Shanggu/GenYo/LXGW get the same "common text → few
  files" behaviour without re-deriving a partition, on a clean licensed lineage
  (no scraped CSS).
- We slice the **whole font** against this table; with `unicode-range` a TC page
  only ever pulls the common-Han + ASCII slices regardless of what else the font
  covers (the rationale already in spec §4).
- **Caveat for narrow fonts (already in `docs/TODO.md`):** the table targets
  full-coverage CJK. A small font like **Klee One (~10k glyphs)** leaves many
  slices empty/near-empty — those should be skipped (no woff2, no `@font-face`),
  exactly as Google omits ranges a font doesn't cover.
- **Refresh discipline:** the strategy is versioned by Google. If we re-pin
  `data/sources/traditional-chinese_default.txt` and regenerate, slice ids shift
  and break cross-version cache reuse — so treat it as a pinned, deliberately-bumped
  asset (spec §9.5).

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
- `googlefonts/nam-files` — slicing strategies + subset definitions (Apache-2.0): https://github.com/googlefonts/nam-files
- W3C — *Incremental Font Transfer*: https://w3c.github.io/IFT/Overview.html
- Primary data: `data/sources/traditional-chinese_default.txt` (pinned from nam-files), parsed via `cheritage.slices.parse_slicing_strategy`. Attribution: `data/sources/README.md`.
