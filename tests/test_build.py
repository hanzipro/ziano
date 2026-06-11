import json

import pytest

from cheritage.build import build_family


@pytest.mark.integration
def test_build_shanggu_serif_produces_installable_package(tmp_path):
    root = build_family(
        "shanggu-serif", roster_path="roster.toml", dest=str(tmp_path), version="0.1.0"
    )
    pj = json.loads((root / "package.json").read_text())
    assert pj["name"] == "@cheritage/shanggu-serif"

    css = (root / "variable.css").read_text()
    assert "font-weight: 250 900;" in css
    n_faces = css.count("@font-face")

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
    assert pj["name"] == "@cheritage/genyo-gothic"

    index = (root / "index.css").read_text()
    for w in (250, 300, 350, 400, 500, 700, 900):
        assert f'@import url("./{w}.css");' in index

    css400 = (root / "400.css").read_text()
    assert "font-weight: 400;" in css400
    n_faces = css400.count("@font-face")

    woff2 = list((root / "files").glob("genyo-gothic.400.*.woff2"))
    assert len(woff2) == n_faces > 50
    assert all(p.read_bytes()[:4] == b"wOF2" for p in woff2)
    for p in woff2:
        assert f"src: url(./files/{p.name})" in css400
    # only the requested weight was subset
    assert not list((root / "files").glob("genyo-gothic.700.*.woff2"))
    assert "SIL Open Font License" in (root / "LICENSE").read_text()
