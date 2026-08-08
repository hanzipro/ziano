"""One set of line metrics for every family we ship.

Two engines synthesise a glyph's **central baseline** in vertical writing mode as
`(hhea.ascent − hhea.descent) / 2`, taken from whichever font drew the glyph —
and a `unicode-range`-segmented `@font-face` is never the line's first available
font, so ziano's faces always take that path. Upstream disagrees wildly about
`hhea` (Source Han lineage `1151/−286` → 0.4325em, ButTaiwan `880/−120` →
0.380em, LXGW WenKai `928/−256` → 0.336em), which lands two families up to
0.0965em apart across the column.

**This has to be in the file, not in CSS.** `ascent-override` fixes Chromium, but
Safari reads the same `hhea` and does *not* apply the descriptor to this path —
measured on a real machine at 0.090em residual, matching the `hhea` difference.
(Don't trust Playwright's WebKit here: that build ignores the descriptor *and*
has no offset to begin with, which reads as "WebKit is fine".) The same is true
of the `text-emphasis` outset, which no CSS descriptor reaches at all.

`cssgen` still emits the equivalent `@font-face` descriptors, derived from the
constants below, so the two can't drift: the CSS makes the change visible to
anyone reading the stylesheet, and lets the demo A/B it.

Full derivation and measurements: `docs/vertical-baseline-offset.md`.
"""

from fontTools.ttLib import TTFont

# The DIFFERENCE is what fixes the vertical offset: 0.76em is the em box centre
# (sTypo 880/−120), which is also what Hiragino, YuMincho, 源起 and 芫荽 already
# use — so the position holds when the webfont fails and the JP system font takes
# over. The SUM only sets `line-height: normal` and the emphasis outset; 1.44em
# keeps it at Shanggu's own 1.437em so pages that never set line-height don't
# suddenly tighten. (diantenjeom uses the same difference with a 1.0em sum: it is
# punctuation, and must never be the font that grows someone else's line.)
ASCENT = 1100
DESCENT = -340

# (ascent − |descent|) / 2 — the quantity the engines synthesise the central
# baseline from, and the one every family has to agree on.
CENTRE = (ASCENT + DESCENT) / 2 / 1000  # 0.380em


def _scaled(value: int, upem: int) -> int:
    return round(value * upem / 1000)


def normalise(font: TTFont) -> None:
    """Point `hhea` and `OS/2.usWin*` at the shared metrics, in place.

    `sTypo*` is left alone: it is already the em box in every upstream we ship,
    and it is what the difference above is derived from.
    """
    upem = font["head"].unitsPerEm
    ascent, descent = _scaled(ASCENT, upem), _scaled(DESCENT, upem)

    hhea = font["hhea"]
    hhea.ascent, hhea.descent, hhea.lineGap = ascent, descent, 0

    os2 = font["OS/2"]
    os2.usWinAscent, os2.usWinDescent = ascent, -descent
