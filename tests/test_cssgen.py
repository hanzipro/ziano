from cheritage.cssgen import generate_css
from cheritage.roster import FamilyConfig
from cheritage.slices import Slice

VF = FamilyConfig(
    id="shanggu-serif", font_family="Shanggu Serif", style="serif", format="vf",
    repo="GuiWonder/Shanggu", release_tag="1.028", asset="x.7z",
    member="x.ttf", asset_sha256="0", weight_min=250, weight_max=900,
)


def test_vf_font_face_has_weight_range_and_relative_src():
    slices = [Slice(0, "U+4e00-4e10"), Slice(1, "U+20")]
    css = generate_css(VF, slices)
    assert css.count("@font-face") == 2
    assert "font-weight: 250 900;" in css
    assert "font-display: swap;" in css
    assert "font-family: 'Shanggu Serif';" in css
    assert "src: url(./files/shanggu-serif.0.woff2) format('woff2');" in css
    assert "unicode-range: U+4e00-4e10;" in css


def test_static_font_face_uses_single_weight_and_weight_suffix():
    static = FamilyConfig(
        id="genyo-min", font_family="GenYoMin", style="serif", format="static",
        repo="ButTaiwan/genyo-font", release_tag="v2.100", asset="x.7z",
        member="x.ttf", asset_sha256="0", weight_min=400, weight_max=400,
    )
    css = generate_css(static, [Slice(0, "U+20")], weight=700)
    assert "font-weight: 700;" in css
    assert "src: url(./files/genyo-min.700.0.woff2) format('woff2');" in css
