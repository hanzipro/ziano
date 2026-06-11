# cheritage Demo — modern redesign plan

**Why:** the current "ink on paper" theme (warm ochre, 朱紅 vermilion, soft
editorial) is beautiful but **codes 古風**. That visually argues the *opposite* of
our thesis. The page must prove **傳承字形 are timeless and fully at home in
contemporary design** — so the frame should read aggressively *modern*, and the
heritage forms should look excellent inside it. **Medium is the message.**

## What currently reads "古風" (diagnosis)

1. **Warm ochre paper** (`#f7f4ee`) → scroll / 古籍 / 茶館.
2. **朱紅 vermilion accent** → 印泥 / 朱批 — culturally "ancient".
3. **Serif-led, gentle, centered-editorial** rhythm → literary/classical.
4. Soft borders, low contrast → quiet, antique.

None of these are *bad* — they're just arguing the wrong case.

## Direction — "modern type-foundry"

Think Klim / Grilli / Pangram-Pangram / Dinamo / Linear-era brand sites: **stark,
high-contrast, huge confident type, tight modern grid, lots of negative space,
near-monochrome with one disciplined accent, subtle snappy motion.** Let the
heritage 字 carry all the warmth; the *frame* stays cool and contemporary.

### Concrete moves
- **Palette → crisp neutral, high contrast.**
  - Light: near-white/bone background (`#f6f6f4`→`#fff`), near-black ink (`#0b0b0c`).
  - Drop the warm ochre as the default ground.
- **Accent → modern, not 朱.** Either (a) **monochrome** with accent only on
  interaction/focus, or (b) a single **sharp digital red** used minimally (red can
  be very modern — but treat it as a brand mark, not seal-ink). Lean (a)+(b): mostly
  mono, one decisive red moment.
- **Type → bold and large.** Oversized display set in Shanggu Serif; UI/labels in
  Shanggu Sans, tight tracking, modern type scale, real grid. Uppercase mono
  micro-labels (the eyebrow style) lean technical/modern.
- **Layout → grid + asymmetry + space.** 12-col feel, big left-aligned headers,
  generous whitespace, hairline rules, intentional sharp radii (or none).
- **Motion → subtle, precise.** Snappy transitions, scroll-reveal, the slice-loader
  cells animating (already data-viz-modern — lean into that "technical" energy as a
  signature).
- **A true dark mode** (OLED near-black + warm-white ink) as the "wow" — dark +
  heritage type reads very 2026.

## The key idea (recommended): **a theme switcher, default = Modern**

Turn your own tension ("the ochre is beautiful, but I want modern") into the
*proof itself*: ship **2–3 themes** and let the user flip:

- **Modern** (default) — stark, mono, contemporary. The argument.
- **Warm** — the current ochre/vermilion (keep the beauty you like).
- **Dark** — OLED modern.

The same heritage fonts holding up across a stark-modern, a warm-classical, and a
dark frame **is** the demonstration that 傳承字形 adapt to any contemporary
aesthetic — not just nostalgic ones. One toggle, maximum thesis.

## Tasks

1. **Token layer** — refactor `:root` into theme tokens driven by a
   `[data-theme]` attribute (modern / warm / dark). Move every color to a token.
2. **Modern theme** — design the default: neutral ground, mono+red accent, type
   scale, grid, hairlines, radii. Make it genuinely sharp.
3. **Type & layout pass** — bigger/bolder display, tighter tracking, real grid,
   more whitespace, modern micro-labels; restructure hero for impact.
4. **Motion** — scroll-reveal + transitions; animate slice-loader cells.
5. **Theme switcher** — control in the top bar; persist to `localStorage`; keep
   Warm = today's look, add Dark.
6. **Re-shoot + verify** each theme.

## Open decisions (⚑ for you)
- ⚑ **How stark?** Pure mono (most modern, safest argument) vs. mono + one sharp
  red moment (my lean). Keep red at all, or retire 朱 entirely for the modern theme?
- ⚑ **Theme switcher yes/no?** (My strong rec: yes — it *is* the thesis. If no,
  we commit to Modern-only and drop the warm default.)
- ⚑ Default ground: clean **white** (boldest/most modern) vs. a **whisper-warm
  bone** (keeps a little soul). My lean: bone, very low saturation.

## My recommendation (TL;DR)
**Default to a stark modern type-foundry aesthetic** (bone/near-white, near-black,
mostly mono with one sharp red moment, big type, tight grid, subtle motion),
**add a theme switcher** keeping today's Warm + a new Dark. That proves the point
*and* keeps the ochre you love — as a choice, not the default.
