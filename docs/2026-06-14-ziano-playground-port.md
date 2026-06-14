# ziano playground port — summary & TODO

**Date:** 2026-06-14 · **Scope:** porting the `demo/index.html` playground into
`demo/new.html` (ziano), and the follow-up cleanup. (Not committed — working note.)

## What landed

The index.html playground was ported into new.html, split into FP / declarative /
semicolonless modules under `demo/src/` (single-quote convention):

| Module | Responsibility |
|---|---|
| `cdn.ts` | pure CDN URL / snippet builders (no DOM, no state) |
| `fonts.ts` | read the `<dl>` roster → `Font[]` (the old inline `$$fonts`, declarative) |
| `fontLink.ts` | idempotent CDN `<link>` injection |
| `fontSelect.ts` | populate the customizable `<select>` + Safari/FF degrade |
| `piano.ts` | the 120-key `<kbd>` slice piano (refactored) |
| `playground.ts` | controls + immutable-ish state orchestration |
| `new-main.ts` | entry — imports & wires the above |

`new.html` now loads only `new-main.ts` (the `main2.ts` / `piano.ts` / inline
scripts are gone) and is a vite build input. Body structure unchanged.

**Ported features:** font picker (with Safari fallback), weight slider (range
adapts per font: VF span / static min–max, label synced), size slider (body +
title ×1.5), 橫/直排, CDN switch (jsDelivr / unpkg / esm.sh), Copy snippet
(link+preconnect, ✓ feedback), specimen font-family, slice piano (hit glow /
命中 X/120 status / per-keystroke flash / TC·SC·JP partition switching).

## Not ported (backlog)

1. **Scroll interception / full-page panel scroller** — dropped on purpose.
2. **Per-script sample texts** (tc/sc/jp swap) — kept new.html's authored
   specimen; the piano still switches partition, but the sample text doesn't.
3. **localStorage persistence** (config + edited text) — dropped to stay
   stateless; easy to re-add.
4. **Live 首載 KB** (measureBytes via Performance API) — `.status` has no KB slot
   and it needs source+woff2 coupling; status still shows 命中 X/120.
5. **Specimen meta line** (family・style・format・weight・size・source) — no element
   in new.html; skipped to avoid adding structure.
6. **Static-weight chips** (「全部」+ discrete) — replaced by adapting the single
   slider's min/max per font (no chip UI added).
7. **Dark mode** — the `黑暗模式` checkbox exists but `main.css` has no
   `[data-theme=dark]` styles, so it's left unwired.

## Caveats

- **CDN switch** injects the chosen source's CSS + updates the snippet, but does
  NOT prune the head's preloaded jsdelivr links (they serve the roster previews).
  So the snippet always reflects the choice; already-loaded families' woff2 may
  still come from jsdelivr. Fine for a demo.
- **Script (tc/sc/jp) is derived from the font id** in `fonts.ts`
  (`lxgw-wenkai→sc`, `klee-one→jp`, else `tc`) to avoid touching HTML — the
  fragile coupling the TODO below removes. `family` is still read from the
  positional first `<dd>`.

## TODO — 2026-06-15: harden ziano data binding

Make new.html robust by removing the structure/position coupling:

- Add explicit `data-name` / `data-font-family` to each `<dl>` card; rewrite
  `fonts.ts` (and `main2.ts` if/when built) to read `data-*` only — never
  `dd:first-of-type` positions or id-based script guesses. The `<dd>`s stay for
  humans; machines read attributes.
- Where JS toggles state, add class hooks instead of relying on `nth-child`.

**Why:** insert/reorder a `<dd>` and the model silently breaks. We agreed ziano's
philosophy (semantic HTML + progressive enhancement + logical properties, good for
直排) is right for this content page, but it should borrow index.html's robustness.

## Conventions noted

- TS/JS: single quotes first, double only when the string contains a `'`
  (attribute selectors keep single-outside / double-inside). Semicolonless.
- No formatter installed; **don't add prettier** (it would force semicolons and
  reflow the older double-quote+semicolon index stack).
