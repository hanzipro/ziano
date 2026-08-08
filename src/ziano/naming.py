"""Rewrite a prepared font's `name` table so it stops claiming to be upstream.

None of ziano's upstreams actually declare a Reserved Font Name for the families
we ship — Shanggu's `LICENSE.txt` carries no copyright line at all, LXGW WenKai
and Iansui name only their project authors, and the Source Han derivatives
(GenKi / GenYo) reserve Adobe's `Source`, which we never use. So this is not an
OFL compliance requirement; it is honesty.

What we ship is a derived work: subset into `unicode-range` slices, line metrics
normalised (`metrics.py`), a sentinel `vert` rule added (`upright.py`). A file
that still calls itself `Shanggu Serif VF` misrepresents all three, and it also
disagrees with the `font-family` our own stylesheets declare — which shows up
the moment someone installs the woff2 or reaches for `local()`.

The scheme is `Ziano <roster family>` — publisher first, source and cut intact.
`Ziano` marks who changed it; `Shanggu Serif Dan` says what it came from, so
anyone looking for the original can still find it.

The prefix lives **here and nowhere else**. Stylesheets, docs and demos all say
`Shanggu Serif` — a `@font-face` family is a label the author picks, and
making everyone type `Ziano` into their CSS would be branding, not honesty. The
file identifies itself; the CSS names it.

Localised names are kept localised: the English name fills most slots, the
Chinese ones take `font_family_zh`. Dropping the Chinese name — the one a
Chinese font is actually known by — to gain uniformity would be a bad trade.

zh-TW/HK/MO and zh-CN/SG are separate slots because upstream treats them as
separate: Shanggu ships `尙古明體 VF` to the first and `尙古明体 VF` to the
second, LXGW WenKai `霞鶩文楷` and `霞鹜文楷`. Writing one form into both would
put traditional glyphs in a simplified reader's font menu — the same
orthographic carelessness these fonts exist to undo. `font_family_zh_hans`
carries the simplified form; families whose name is script-neutral (芫荽) or
that never had a zh-CN slot (源起 / 源樣) leave it empty.
"""

from fontTools.ttLib import TTFont

# Windows language IDs, split by which orthography the slot expects.
_HANT_LANG_IDS = frozenset({0x0404, 0x0C04, 0x1404})  # TW HK MO
_HANS_LANG_IDS = frozenset({0x0804, 0x1004})          # CN SG

_FAMILY_IDS = (1, 16, 21)  # family / typographic family / WWS family

PREFIX = "Ziano "


def _records(font: TTFont, name_id: int) -> list:
    return [rec for rec in font["name"].names if rec.nameID == name_id]


def _subfamily(font: TTFont) -> str:
    """The style this file represents — `Regular`, `Bold`, `ExtraLight`…

    Prefer the typographic subfamily (17): a static family split across more
    than four weights puts the real style there and leaves 2 saying `Regular`.
    """
    for name_id in (17, 2):
        for rec in _records(font, name_id):
            if rec.langID == 0x0409 and (value := rec.toUnicode()):
                return value
    return "Regular"


def rename(font: TTFont, family: str, family_zh: str = "",
           family_zh_hans: str = "") -> None:
    """Rewrite family / full / PostScript / unique-ID names in place.

    Takes the roster family names — the ones the stylesheets declare — and
    writes them prefixed. Only slots the source already populated are written:
    a font that never targeted Macintosh doesn't gain Macintosh records here
    (and `subset.py` would drop them again anyway).
    """
    family = PREFIX + family
    family_zh = PREFIX + family_zh if family_zh else ""
    # A family with no simplified form of its own reuses the traditional one;
    # 芫荽 reads the same either way, and 源起 / 源樣 have no zh-CN slot at all.
    family_hans = PREFIX + family_zh_hans if family_zh_hans else family_zh
    table = font["name"]
    subfamily = _subfamily(font)
    postscript = f"{family}-{subfamily}".replace(" ", "")

    for rec in list(table.names):
        # Only Windows (platformID 3) records are Unicode here; a legacy
        # Macintosh record is mac_roman and would fail to encode Han.
        localised = family
        if family_zh and rec.platformID == 3:
            if rec.langID in _HANT_LANG_IDS:
                localised = family_zh
            elif rec.langID in _HANS_LANG_IDS:
                localised = family_hans
        if rec.nameID in _FAMILY_IDS:
            rec.string = localised
        elif rec.nameID == 4:  # full name
            rec.string = f"{localised} {subfamily}"
        elif rec.nameID == 6:  # PostScript name — ASCII, one per font
            rec.string = postscript
        elif rec.nameID == 3:  # unique ID
            rec.string = f"{postscript} (ziano)"

    # Style-name slots (2 / 17 / 22) are left exactly as upstream wrote them:
    # they describe the weight, not the family, and this file still *is*
    # upstream's ExtraLight.
