"""Shipped files must not claim to be their upstream — see src/ziano/naming.py."""

import glob
import os

import pytest
from fontTools.ttLib import TTFont

from ziano.naming import PREFIX, rename
from ziano.roster import load_roster

DIST = "dist"
WINDOWS, ENGLISH = 3, 0x0409
TAIWAN, CHINA = 0x0404, 0x0804


def _name(font: TTFont, name_id: int, lang_id: int = ENGLISH) -> str:
    for rec in font["name"].names:
        if rec.nameID == name_id and rec.platformID == WINDOWS and rec.langID == lang_id:
            return rec.toUnicode()
    return ""


def _rostered() -> list:
    return [f for f in load_roster("roster.toml") if os.path.isdir(f"{DIST}/{f.id}")]


@pytest.mark.integration
def test_shipped_slices_carry_the_ziano_family_name():
    """The name table and the `@font-face` family must agree — otherwise
    `local()`, a desktop install, and any font manager see a different font
    from the one the stylesheet asked for."""
    if not os.path.isdir(DIST):
        pytest.skip("no dist/ — run the build first")
    checked = 0
    for fam in _rostered():
        for path in sorted(glob.glob(f"{DIST}/{fam.id}/files/*.woff2"))[:2]:
            font = TTFont(path, lazy=True)
            where = f"{fam.id}/{os.path.basename(path)}"
            assert _name(font, 1) == PREFIX + fam.qualified_family, where
            assert _name(font, 6).startswith(
                (PREFIX + fam.qualified_family).replace(" ", "")), where
            # zh-TW and zh-CN are separate slots with separate orthography;
            # a font only has the slots upstream gave it (LXGW WenKai SC has
            # zh-CN only), so check each one that exists.
            if fam.font_family_zh and _name(font, 1, TAIWAN):
                assert _name(font, 1, TAIWAN) == PREFIX + fam.font_family_zh, where
            if fam.font_family_zh and _name(font, 1, CHINA):
                hans = fam.font_family_zh_hans or fam.font_family_zh
                assert _name(font, 1, CHINA) == PREFIX + hans, where
            checked += 1
    assert checked, "no shipped slices found"


@pytest.mark.integration
def test_no_shipped_slice_still_answers_to_its_upstream_name():
    if not os.path.isdir(DIST):
        pytest.skip("no dist/ — run the build first")
    for fam in _rostered():
        for path in sorted(glob.glob(f"{DIST}/{fam.id}/files/*.woff2"))[:2]:
            font = TTFont(path, lazy=True)
            for rec in font["name"].names:
                if rec.nameID in (1, 3, 4, 6, 16, 21):
                    assert rec.toUnicode().startswith("Ziano"), (
                        f"{fam.id}: nameID {rec.nameID} is {rec.toUnicode()!r}")


def test_rename_keeps_the_style_name_and_the_upstream_notices():
    """Only the family identifies the publisher. The weight name still
    describes upstream's design, and the copyright/licence records are the
    upstream authors' — rewriting either would be a lie in the other direction.
    """
    src = ".cache/extracted/shanggu-serif/ShangguSerif-VF.ttf"
    if not os.path.exists(src):
        pytest.skip("source font not fetched")
    font = TTFont(src, lazy=True)
    before = {r.nameID: r.toUnicode() for r in font["name"].names
              if r.nameID in (0, 2, 13, 14, 17) and r.platformID == WINDOWS}
    # the build passes the QUALIFIED name — the file always states its cut,
    # even though the default stylesheet declares the plain `Shanggu Serif`.
    rename(font, "Shanggu Serif Dan", "尙古明體丹")
    after = {r.nameID: r.toUnicode() for r in font["name"].names
             if r.nameID in (0, 2, 13, 14, 17) and r.platformID == WINDOWS}
    assert before == after
    assert _name(font, 1) == "Ziano Shanggu Serif Dan"
    assert _name(font, 1, TAIWAN) == "Ziano 尙古明體丹"
    assert _name(font, 6) == "ZianoShangguSerifDan-ExtraLight"
