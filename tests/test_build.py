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
