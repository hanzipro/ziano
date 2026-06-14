# CSS clip-path scaling & icon techniques — reference

Distilled from building the ziano `::picker-icon` / `::checkmark`. Evergreen,
portable — copy into any project. (Browser-support figures: mid-2026.)

## `clip-path: path()` vs `shape()`

- **No viewBox in CSS.** `viewBox` is an SVG-only attribute. In CSS `clip-path`,
  coordinates resolve against the element's **reference box**, not a viewBox.
- **`path('M… C… Z')`** — coordinates are **fixed CSS px** relative to the box
  origin. Does **not** scale to the element → you must size the element to match
  the path's coordinate space (e.g. a 0–16 path needs a 16px box).
- **`shape(from x y, line to x y, curve to x y with c1 / c2, close)`** — the
  responsive twin. Accepts **units & `%`** (`%` = relative to the reference box),
  so it **scales to the box**. More bytes (keyword syntax vs single-letter SVG
  commands, ~2–3×) but gzip narrows that. **Baseline 2026** (Newly available):
  Chrome/Edge 135+, Safari 18.4+, Firefox 148+. "Newly available" ≠ safe to drop
  fallbacks — ~81% global reach as of mid-2026; Widely available ~2028.
- Path→shape command map: `M`→`from`, `L`→`line to`, `C c1 c2 end`→
  `curve to <end> with <c1> / <c2>`, `Z`→`close`. For `%`, divide each coord by
  the canvas size × 100.

## Fallback: `path()` → `shape()`

- **Two `clip-path` declarations WORKS** (progressive enhancement):
  ```css
  clip-path: path('…');   /* kept by browsers that don't grok shape() */
  clip-path: shape(…);    /* last valid declaration wins where supported */
  ```
  An unsupported `shape()` value is invalid-at-parse → the declaration is dropped
  → falls back to `path()`.
- **Two custom-property declarations DOES NOT work.** `--*` accept *any* tokens
  (no type-check), so `--x: shape()` always overrides `--x: path()` even where
  unsupported; then `clip-path: var(--x)` is invalid-at-computed-value-time →
  `clip-path` falls to its initial `none` (no clip), with no fallback.
- **Tokenised fallback → use `@supports`:**
  ```css
  :root { --icon: path('…') }                 /* fallback */
  @supports (clip-path: shape(from 0 0, line to 1px 1px)) {
    :root { --icon: shape(…) }                /* responsive, where supported */
  }
  ```
- **Which to use?** Two-line `clip-path` for a single inline site; `@supports`
  when the value lives in a custom property (keeps one source of truth, consumers
  stay `var(--icon)`).

## Making a path() icon scale anyway

`path()` is fixed px. Options to get scaling:

1. **`mask-image` + an SVG with a viewBox** (box in `em`): SVG scales to the box,
   box tracks font-size, and `background-color: currentColor` colours it. Easiest
   reuse of an existing `d`. Best for icons inside text/flex.
2. **`scale` + unit-division hack:** `calc()` can't divide length/length, but
   `tan(atan2(1em, 24px))` yields `1em/24px` as a **number**. So
   `scale: tan(atan2(1em, 24px))` shrinks a 24px-clipped box to 1em. Caveat:
   `transform`/`scale` **doesn't reflow** — the layout box stays the original
   size, so it can mis-align neighbours. Fine for isolated icons only.
3. **`shape()` with `em`/`%`** — see above.

## `scale` property vs `scale()` function

- **`scale: 2 0.5`** (property) — space-separated, 1–3 values (3rd = z, like
  `scale3d`), **independent** of `transform`, composes with `translate`/`rotate`
  properties, fixed order (translate→rotate→scale→transform), **independently
  animatable**. Baseline 2022-08.
- **`transform: scale(2, 0.5)`** (function) — comma args, **2D only**, one item in
  the `transform` list (rewriting `transform` replaces the whole list), order = as
  written. Baseline 2015.
- Neither accepts lengths — only `<number>` / `<percentage>`. Both share
  `transform-origin`. Prefer the **property** when you want to animate/override
  scale without touching other transforms.

## SVG path coordinates (for context)

- Numbers between `M…Z` are **user-space coordinates** (unitless), not device px;
  in an `<svg viewBox>` they map to pixels via the viewBox→viewport scale (so
  they're scalable). Origin top-left, **y axis points down**.
- Coordinates **can be negative or exceed the viewBox** — they're just clipped by
  the viewport (unless `overflow: visible`).
- Inside CSS `clip-path: path()` there is no viewBox → those same numbers are
  fixed CSS px.
