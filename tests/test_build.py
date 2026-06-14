import json

import pytest

from ziano.build import build_family


@pytest.mark.integration
def test_build_shanggu_serif_produces_installable_package(tmp_path):
    root = build_family(
        "shanggu-serif", roster_path="roster.toml", dest=str(tmp_path), version="0.1.0"
    )
    pj = json.loads((root / "package.json").read_text())
    assert pj["name"] == "@hanzi.pro/webfonts-shanggu-serif"

    css = (root / "swap.css").read_text()
    assert "font-weight: 250 900;" in css
    assert "font-display: swap;" in css
    n_faces = css.count("@font-face")
    # the two alternate modes ship the same faces at a different font-display
    assert "font-display: block;" in (root / "block.css").read_text()
    assert "font-display: optional;" in (root / "optional.css").read_text()

    woff2 = list((root / "files").glob("*.woff2"))
    # one woff2 per @font-face, all real woff2, every src resolves
    assert len(woff2) == n_faces > 50
    assert all(p.read_bytes()[:4] == b"wOF2" for p in woff2)
    for p in woff2:
        assert f"src: url(./files/{p.name})" in css

    # OFL bundled from inside the archive
    assert "SIL Open Font License" in (root / "LICENSE").read_text()


@pytest.mark.integration
def test_build_genyo_gothic_static_one_weight(tmp_path):
    # only_weights keeps the test fast; index.css still lists all 7 weights
    root = build_family(
        "genyo-gothic", roster_path="roster.toml", dest=str(tmp_path),
        version="0.1.0", only_weights=[400],
    )
    pj = json.loads((root / "package.json").read_text())
    assert pj["name"] == "@hanzi.pro/webfonts-genyo-gothic"

    # swap.css inlines every weight (no @import waterfall), even though only 400
    # was subset to woff2 — the published entry stays complete.
    swap = (root / "swap.css").read_text()
    assert "@import" not in swap
    for w in (250, 300, 350, 400, 500, 700, 900):
        assert f"font-weight: {w};" in swap

    css400 = (root / "swap" / "400.css").read_text()
    assert "font-weight: 400;" in css400
    # per-weight file is one dir deep → url() climbs back with ../files
    assert "url(../files/genyo-gothic.400." in css400
    n_faces = css400.count("@font-face")

    woff2 = list((root / "files").glob("genyo-gothic.400.*.woff2"))
    assert len(woff2) == n_faces > 50
    assert all(p.read_bytes()[:4] == b"wOF2" for p in woff2)
    for p in woff2:
        assert f"src: url(../files/{p.name})" in css400
    # only the requested weight was subset
    assert not list((root / "files").glob("genyo-gothic.700.*.woff2"))
    assert "SIL Open Font License" in (root / "LICENSE").read_text()


@pytest.mark.integration
def test_build_iansui_cursive_single_weight(tmp_path):
    # cursive style → serif slice table (108 ranges); single-weight static font
    root = build_family(
        "iansui", roster_path="roster.toml", dest=str(tmp_path), version="0.1.0"
    )
    assert json.loads((root / "package.json").read_text())["name"] == "@hanzi.pro/webfonts-iansui"
    swap = (root / "swap.css").read_text()  # single weight, inlined
    assert "@import" not in swap
    assert "font-weight: 400;" in swap
    css = (root / "swap" / "400.css").read_text()
    woff2 = list((root / "files").glob("iansui.400.*.woff2"))
    assert len(woff2) == css.count("@font-face") > 50
    assert all(p.read_bytes()[:4] == b"wOF2" for p in woff2)
    assert "Open Font License" in (root / "LICENSE").read_text()


@pytest.mark.integration
def test_build_klee_raw_source_with_local(tmp_path):
    # raw source (no GitHub release) + local() priority for the macOS system font
    root = build_family(
        "klee-one", roster_path="roster.toml", dest=str(tmp_path), version="0.1.0",
        only_weights=[400],
    )
    assert json.loads((root / "package.json").read_text())["name"] == "@hanzi.pro/webfonts-klee-one"
    css = (root / "swap" / "400.css").read_text()
    assert 'src: local("Klee One"), local("Klee"), url(../files/klee-one.400.' in css
    woff2 = list((root / "files").glob("klee-one.400.*.woff2"))
    assert len(woff2) == css.count("@font-face") > 50
    assert all(p.read_bytes()[:4] == b"wOF2" for p in woff2)
    assert "Open Font License" in (root / "LICENSE").read_text()
