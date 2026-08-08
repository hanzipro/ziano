"""`：；` must stay upright in vertical text — see src/ziano/upright.py."""

import glob
import os

import pytest
from fontTools.ttLib import TTFont

from ziano import metrics
from ziano.cssgen import METRICS_OVERRIDE
from ziano.roster import load_roster
from ziano.upright import UPRIGHT_CODEPOINTS, VERT_FEATURE_TAGS, install

DIST = "dist"

# Klee One sends U+FF1A to a genuinely rotated JP form and LXGW WenKai SC to a
# re-centred one. That is the designer's convention, and `install` must not
# overwrite it.
KEEPS_OWN_MAPPING = {"klee-one", "lxgw-wenkai"}


def _vert_targets(font: TTFont, codepoint: int) -> dict[str, str]:
    """What `vert`/`vrt2` substitute this codepoint's glyph with, per feature."""
    cmap = font.getBestCmap()
    glyph = cmap.get(codepoint) if cmap else None
    if glyph is None or "GSUB" not in font or font["GSUB"].table.FeatureList is None:
        return {}
    gsub = font["GSUB"].table
    out: dict[str, str] = {}
    for rec in gsub.FeatureList.FeatureRecord:
        if rec.FeatureTag not in VERT_FEATURE_TAGS:
            continue
        for index in rec.Feature.LookupListIndex:
            for subtable in gsub.LookupList.Lookup[index].SubTable:
                subtable = getattr(subtable, "ExtSubTable", subtable)
                mapping = getattr(subtable, "mapping", None)
                if mapping and glyph in mapping:
                    out[rec.FeatureTag] = mapping[glyph]
    return out


def _families() -> list[str]:
    """Roster ids, not whatever `dist/` happens to hold — a renamed family
    leaves its old directory behind until someone sweeps it."""
    return [f.id for f in load_roster("roster.toml")
            if os.path.isdir(f"{DIST}/{f.id}")]


def _slice_with(family: str, codepoint: int) -> TTFont | None:
    for path in sorted(glob.glob(f"{DIST}/{family}/files/*.woff2")):
        font = TTFont(path, lazy=True)
        cmap = font.getBestCmap()
        if cmap and codepoint in cmap:
            return font
    return None


@pytest.mark.integration
@pytest.mark.parametrize("codepoint", UPRIGHT_CODEPOINTS)
def test_shipped_slices_substitute_the_colons(codepoint):
    """Every shipped slice that carries `：` or `；` must also carry a `vert`
    rule for it, or Firefox rotates the glyph (UTR50 class Tr)."""
    if not os.path.isdir(DIST):
        pytest.skip("no dist/ — run the build first")
    checked = 0
    for family in _families():
        font = _slice_with(family, codepoint)
        if font is None:
            continue
        checked += 1
        targets = _vert_targets(font, codepoint)
        assert targets, f"{family}: U+{codepoint:04X} has no vert rule"
        if family not in KEEPS_OWN_MAPPING:
            glyph = font.getBestCmap()[codepoint]
            assert all(t == glyph for t in targets.values()), (
                f"{family}: expected an identity subst, got {targets}"
            )
    assert checked, "no family shipped this codepoint — check the slice tables"


def test_install_is_idempotent():
    """Running the pass twice must not add a second, conflicting rule."""
    font = TTFont(
        ".cache/extracted/shanggu-serif/ShangguSerif-VF.ttf", lazy=True
    ) if os.path.exists(
        ".cache/extracted/shanggu-serif/ShangguSerif-VF.ttf"
    ) else None
    if font is None:
        pytest.skip("source font not fetched")
    assert install(font), "expected the first pass to change something"
    assert install(font) == [], "second pass must be a no-op"


# --- shared line metrics ----------------------------------------------------
#
# Written into the FILE, not just the CSS: Safari reads hhea for the vertical
# central baseline and does not apply `ascent-override` there (measured on a real
# machine: 0.090em residual, matching the hhea difference). See metrics.py.


@pytest.mark.integration
def test_shipped_slices_carry_the_shared_metrics():
    if not os.path.isdir(DIST):
        pytest.skip("no dist/ — run the build first")
    checked = 0
    for family in _families():
        for path in sorted(glob.glob(f"{DIST}/{family}/files/*.woff2"))[:3]:
            font = TTFont(path, lazy=True)
            upem = font["head"].unitsPerEm
            hhea, os2 = font["hhea"], font["OS/2"]
            name = f"{family}/{os.path.basename(path)}"
            assert (hhea.ascent, hhea.descent, hhea.lineGap) == (
                metrics.ASCENT, metrics.DESCENT, 0), name
            assert (os2.usWinAscent, os2.usWinDescent) == (
                metrics.ASCENT, -metrics.DESCENT), name
            assert (hhea.ascent + hhea.descent) / 2 / upem == pytest.approx(
                metrics.CENTRE), name
            checked += 1
    assert checked, "no shipped slices found"


def test_css_descriptors_agree_with_the_font():
    """The stylesheet restates what the files carry; they must not drift."""
    values = {k: float(v.rstrip("%;")) for k, v in
              (line.split(": ") for line in METRICS_OVERRIDE)}
    assert values["ascent-override"] == metrics.ASCENT / 10
    assert values["descent-override"] == -metrics.DESCENT / 10
    assert values["line-gap-override"] == 0.0
