from ziano.cssgen import (
    METRICS_OVERRIDE,
    generate_aggregate_css,
    generate_css,
    mode_css_name,
    weight_css_path,
)
from ziano.roster import FamilyConfig, Weight
from ziano.slices import Slice

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


def test_local_names_emitted_before_url():
    fam = FamilyConfig(
        id="klee-one", font_family="Klee One", style="cursive", format="static",
        repo="fontworks-fonts/Klee", release_tag="Version1.000", source="raw",
        local_names=("Klee One", "Klee"),
        weights=(Weight(400, "fonts/ttf/KleeOne-Regular.ttf"),),
    )
    css = generate_css(fam, [Slice(0, "U+4e00")], weight=400)
    assert 'src: local("Klee One"), local("Klee"), ' \
           "url(./files/klee-one.400.0.woff2) format('woff2');" in css


def test_no_local_names_keeps_plain_url():
    css = generate_css(VF, [Slice(0, "U+4e00-4e10")])
    assert "src: url(./files/shanggu-serif.0.woff2) format('woff2');" in css


STATIC = FamilyConfig(
    id="genyo-min", font_family="GenYo Min", style="serif", format="static",
    repo="ButTaiwan/genyo-font", release_tag="v2.100", asset="x.zip",
    asset_sha256="0",
    weights=(Weight(900, "H.otf"), Weight(250, "EL.otf"), Weight(400, "R.otf")),
)


def test_display_mode_is_emitted():
    css = generate_css(VF, [Slice(0, "U+20")], display="optional")
    assert "font-display: optional;" in css
    assert "font-display: swap;" not in css


def test_aggregate_inlines_every_weight_sorted_no_import():
    css = generate_aggregate_css(STATIC, [Slice(0, "U+20")], [900, 250, 400], display="block")
    # no @import — all @font-face inlined to avoid a request waterfall
    assert "@import" not in css
    assert css.count("@font-face") == 3
    assert "font-display: block;" in css
    # weights inlined in sorted order
    assert css.index("font-weight: 250;") < css.index("font-weight: 400;") < css.index("font-weight: 900;")
    # top-level entry → ./files
    assert "url(./files/genyo-min.250.0.woff2)" in css


def test_per_weight_file_climbs_to_files_dir():
    # swap/300.css sits one dir deep, so url() must reach back up with ../files
    css = generate_css(STATIC, [Slice(0, "U+20")], weight=400, files_base="../files")
    assert "url(../files/genyo-min.400.0.woff2)" in css


def test_path_helpers():
    assert mode_css_name("swap") == "swap.css"
    assert weight_css_path("optional", 700) == "optional/700.css"


# --- normalised line metrics ------------------------------------------------
#
# Every family must carry the SAME ascent/descent, or Chromium lands them on
# different central baselines in vertical text (up to 0.0965em apart between
# Shanggu and LXGW WenKai). See docs/vertical-baseline-offset.md.


def test_every_face_carries_the_metrics_override():
    css = generate_css(VF, [Slice(0, "U+4e00"), Slice(1, "U+20")])
    for line in METRICS_OVERRIDE:
        assert css.count(line) == 2, f"{line} missing from a face"


def test_metrics_override_difference_is_the_em_box():
    """asc − desc = 0.76em is the number that fixes the offset: it is the em box
    centre (sTypo 880/−120), shared with Hiragino / YuMincho / 源起 / 芫荽."""
    values = {k: float(v.rstrip("%;")) for k, v in
              (line.split(": ") for line in METRICS_OVERRIDE)}
    assert values["ascent-override"] - values["descent-override"] == 76.0
    assert values["line-gap-override"] == 0.0


def test_cut_stylesheet_declares_the_qualified_name_against_the_same_files():
    """One font, two labels. `dan/swap.css` names the cut out loud and points at
    the very same woff2 — one directory up, since it sits in dan/."""
    fam = FamilyConfig(
        id="shanggu-serif", font_family="Shanggu Serif", cut="Dan",
        style="serif", format="vf",
        repo="GuiWonder/Shanggu", release_tag="1.028", asset="x.7z",
        member="x.ttf", asset_sha256="0", weight_min=250, weight_max=900,
    )
    assert fam.qualified_family == "Shanggu Serif Dan" and fam.cut_dir == "dan"
    slices = [Slice(0, "U+4E00-9FFF")]
    plain = generate_css(fam, slices)
    qualified = generate_css(
        fam, slices, files_base="../files", family=fam.qualified_family)

    assert "font-family: 'Shanggu Serif';" in plain
    assert "font-family: 'Shanggu Serif Dan';" in qualified
    assert "font-family: 'Shanggu Serif';" not in qualified
    # same file, one level deeper
    assert "url(./files/shanggu-serif.0.woff2)" in plain
    assert "url(../files/shanggu-serif.0.woff2)" in qualified
    # nothing else differs — a label, not a different build
    assert qualified.replace("'Shanggu Serif Dan'", "'Shanggu Serif'").replace(
        "url(../files/", "url(./files/") == plain


def test_families_whose_name_states_the_cut_ship_no_extra_stylesheet():
    from ziano.build import _css_files
    plain = FamilyConfig(
        id="iansui", font_family="Iansui", style="cursive", format="static",
        repo="ButTaiwan/iansui", release_tag="v1", asset="x.zip", asset_sha256="0",
        weights=(Weight(400, "R.ttf"),),
    )
    paths = _css_files(plain, [Slice(0, "U+4E00")])
    assert plain.cut == "" and not any(p.startswith(("dan/", "yue/")) for p in paths)
