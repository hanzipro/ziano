import json

from cheritage.package import package_json, write_package_skeleton
from cheritage.roster import FamilyConfig, Weight

STATIC = FamilyConfig(
    id="genyo-min", font_family="GenYo Min", style="serif", format="static",
    repo="ButTaiwan/genyo-font", release_tag="v2.100", asset="x.zip",
    asset_sha256="0", weights=(Weight(400, "R.otf"), Weight(700, "B.otf")),
)

VF = FamilyConfig(
    id="shanggu-serif", font_family="Shanggu Serif", style="serif", format="vf",
    repo="GuiWonder/Shanggu", release_tag="1.028", asset="x.7z",
    member="x.ttf", asset_sha256="0", weight_min=250, weight_max=900,
)


def test_package_json_fields():
    pj = package_json(VF, version="0.1.0")
    assert pj["name"] == "@cheritage/shanggu-serif"
    assert pj["version"] == "0.1.0"
    assert pj["license"] == "OFL-1.1"
    assert pj["sideEffects"] == ["*.css"]
    assert pj["exports"]["./variable.css"] == "./variable.css"
    assert "GuiWonder/Shanggu" in pj["description"]


def test_write_package_skeleton_creates_layout(tmp_path):
    root = write_package_skeleton(
        VF, dest=str(tmp_path), version="0.1.0",
        css="@font-face{}", license_text="OFL TEXT", readme="# hi",
    )
    assert (root / "package.json").exists()
    assert (root / "variable.css").read_text() == "@font-face{}"
    assert (root / "LICENSE").read_text() == "OFL TEXT"
    assert (root / "README.md").read_text() == "# hi"
    assert (root / "files").is_dir()
    assert json.loads((root / "package.json").read_text())["name"] == "@cheritage/shanggu-serif"


def test_static_package_json_uses_index_and_css_glob():
    pj = package_json(STATIC, version="0.1.0")
    assert pj["name"] == "@cheritage/genyo-min"
    assert pj["exports"]["./index.css"] == "./index.css"
    assert "*.css" in pj["files"]


def test_write_static_skeleton_writes_index_and_per_weight_css(tmp_path):
    root = write_package_skeleton(
        STATIC, dest=str(tmp_path), version="0.1.0",
        css='@import url("./400.css");\n@import url("./700.css");\n',
        extra_css={"400.css": "/*400*/", "700.css": "/*700*/"},
        license_text="OFL", readme="# r",
    )
    assert (root / "index.css").read_text().startswith('@import url("./400.css");')
    assert (root / "400.css").read_text() == "/*400*/"
    assert (root / "700.css").read_text() == "/*700*/"
