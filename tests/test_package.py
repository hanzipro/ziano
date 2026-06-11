import json

from cheritage.package import package_json, write_package_skeleton
from cheritage.roster import FamilyConfig

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
