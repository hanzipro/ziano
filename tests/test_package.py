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
    assert pj["name"] == "@hanzi.pro/webfonts-shanggu-serif"
    assert pj["version"] == "0.1.0"
    assert pj["license"] == "OFL-1.1"
    assert pj["sideEffects"] == ["*.css"]
    # bare specifier + jsDelivr bare URL resolve to swap (the default mode)
    assert pj["main"] == "swap.css"
    assert pj["style"] == "swap.css"
    assert pj["exports"]["."] == "./swap.css"
    assert pj["exports"]["./block"] == "./block.css"
    assert pj["exports"]["./optional"] == "./optional.css"
    assert "GuiWonder/Shanggu" in pj["description"]


def test_vf_files_lists_three_modes_no_subdirs():
    pj = package_json(VF, version="0.1.0")
    assert "swap.css" in pj["files"] and "block.css" in pj["files"] and "optional.css" in pj["files"]
    # vf has no per-weight subdirs
    assert "swap/" not in pj["files"]
    assert "./swap/*" not in pj["exports"]


def test_write_package_skeleton_creates_layout(tmp_path):
    root = write_package_skeleton(
        VF, dest=str(tmp_path), version="0.1.0",
        css_files={"swap.css": "@font-face{}"}, license_text="OFL TEXT", readme="# hi",
    )
    assert (root / "package.json").exists()
    assert (root / "swap.css").read_text() == "@font-face{}"
    assert (root / "LICENSE").read_text() == "OFL TEXT"
    assert (root / "README.md").read_text() == "# hi"
    assert (root / "files").is_dir()
    assert json.loads((root / "package.json").read_text())["name"] == "@hanzi.pro/webfonts-shanggu-serif"


def test_static_package_json_lists_mode_subdirs():
    pj = package_json(STATIC, version="0.1.0")
    assert pj["name"] == "@hanzi.pro/webfonts-genyo-min"
    assert pj["exports"]["."] == "./swap.css"
    # static ships per-weight subdirs for each mode
    for mode in ("swap", "block", "optional"):
        assert f"{mode}/" in pj["files"]
        assert pj["exports"][f"./{mode}/*"] == f"./{mode}/*"


def test_write_static_skeleton_writes_nested_per_weight_css(tmp_path):
    root = write_package_skeleton(
        STATIC, dest=str(tmp_path), version="0.1.0",
        css_files={
            "swap.css": "/*all weights*/",
            "swap/400.css": "/*400*/",
            "swap/700.css": "/*700*/",
        },
        license_text="OFL", readme="# r",
    )
    assert (root / "swap.css").read_text() == "/*all weights*/"
    assert (root / "swap" / "400.css").read_text() == "/*400*/"
    assert (root / "swap" / "700.css").read_text() == "/*700*/"
