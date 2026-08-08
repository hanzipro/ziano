import pytest

from ziano.roster import FamilyConfig, load_roster


def test_load_roster_returns_typed_families():
    families = load_roster("roster.toml")
    by_id = {f.id: f for f in families}
    assert {"shanggu-serif", "shanggu-sans", "genyo-min", "genyo-gothic"} <= set(by_id)
    serif = by_id["shanggu-serif"]
    assert isinstance(serif, FamilyConfig)
    assert serif.font_family == "Shanggu Serif"
    assert serif.style == "serif"
    assert serif.format == "vf"
    assert serif.weight_min == 250 and serif.weight_max == 900
    assert serif.repo == "GuiWonder/Shanggu"
    assert serif.release_tag == "1.028"
    assert serif.asset == "ShangguSerifVF_TTFs.7z"
    assert serif.member == "ShangguSerif-VF.ttf"  # base 無附加名 cut, not TC (see shanggu-variant)
    assert serif.license_member == "LICENSE.txt"
    assert serif.weights == ()  # vf carries no per-weight table


def test_load_roster_static_families_have_per_weight_members():
    by_id = {f.id: f for f in load_roster("roster.toml")}

    min_ = by_id["genyo-min"]
    assert min_.format == "static"
    assert min_.font_family == "GenYo Min"
    assert min_.license_member == "SIL_Open_Font_License_1.1.txt"
    weights = {w.weight: w.member for w in min_.weights}
    assert set(weights) == {250, 300, 400, 500, 600, 700, 900}  # serif: has SB(600)
    assert weights[600] == "GenYoMin2TW-SB.otf"
    assert weights[250] == "GenYoMin2TW-EL.otf"

    gothic = by_id["genyo-gothic"]
    gweights = {w.weight: w.member for w in gothic.weights}
    assert set(gweights) == {250, 300, 350, 400, 500, 700, 900}  # sans: has N(350)
    assert gweights[350] == "GenYoGothic2TW-N.otf"


def test_load_roster_cursive_families():
    by_id = {f.id: f for f in load_roster("roster.toml")}
    lxgw = by_id["lxgw-wenkai-tc"]
    assert lxgw.style == "cursive" and lxgw.format == "static"
    assert {w.weight for w in lxgw.weights} == {300, 400, 500}
    assert lxgw.license_member == "lxgw-wenkai-tc-v1.522/OFL.txt"
    iansui = by_id["iansui"]
    assert {w.weight for w in iansui.weights} == {400}  # single weight
    assert iansui.weights[0].member == "Iansui-Regular.ttf"


def test_styles_use_canonical_tc_slice_table():
    from ziano.roster import slice_table_name
    assert slice_table_name("cursive") == "traditional-chinese"
    assert slice_table_name("serif") == "traditional-chinese"
    assert slice_table_name("sans") == "traditional-chinese"


def test_slice_table_override_wins_over_style():
    from ziano.roster import slice_table_name
    assert slice_table_name("cursive", "simplified-chinese") == "simplified-chinese"
    assert slice_table_name("cursive", "japanese") == "japanese"
    # empty override falls back to the style default
    assert slice_table_name("serif", "") == "traditional-chinese"


def test_unknown_slice_table_override_rejected():
    import pytest
    from ziano.roster import slice_table_name
    with pytest.raises(ValueError):
        slice_table_name("serif", "klingon")


def test_sc_and_jp_families_declare_overrides():
    fams = {f.id: f for f in load_roster("roster.toml")}
    assert fams["lxgw-wenkai"].slice_table == "simplified-chinese"
    assert fams["klee-one"].slice_table == "japanese"
    # the TC sibling must NOT override (stays on the TC partition)
    assert fams["lxgw-wenkai-tc"].slice_table == ""


def test_load_roster_raw_source_and_local_names():
    by_id = {f.id: f for f in load_roster("roster.toml")}
    klee = by_id["klee-one"]
    assert klee.source == "raw"
    assert klee.local_names == ("Klee One", "Klee")
    assert {w.weight for w in klee.weights} == {400, 600}
    # raw weights carry their own sha256
    assert all(w.sha256 for w in klee.weights)
    # release families default to source=release with empty local_names
    assert by_id["shanggu-serif"].source == "release"
    assert by_id["shanggu-serif"].local_names == ()
    assert by_id["lxgw-wenkai"].local_names == ("LXGW WenKai",)


def test_load_roster_rejects_bad_source(tmp_path):
    bad = tmp_path / "bad.toml"
    bad.write_text(
        '[[family]]\nid="x"\nfont_family="X"\nstyle="serif"\nformat="vf"\n'
        'source="ftp"\nrepo="a/b"\nrelease_tag="v1"\nmember="x.ttf"\n'
    )
    with pytest.raises(ValueError, match="source"):
        load_roster(str(bad))


def test_load_roster_tc_dan_families():
    by_id = {f.id: f for f in load_roster("roster.toml")}
    min_tc = by_id["genyo-min-tc"]
    assert min_tc.format == "static"
    assert min_tc.font_family == "GenYo Min TC"
    assert min_tc.asset == "GenYoMin2TC-otf.zip"
    assert {w.member for w in min_tc.weights} >= {"GenYoMin2TC-SB.otf", "GenYoMin2TC-EL.otf"}
    gothic_tc = by_id["genyo-gothic-tc"]
    assert {w.weight for w in gothic_tc.weights} == {250, 300, 350, 400, 500, 700, 900}


def test_load_roster_rejects_static_without_weights(tmp_path):
    bad = tmp_path / "bad.toml"
    bad.write_text(
        '[[family]]\nid="x"\nfont_family="X"\nstyle="serif"\n'
        'format="static"\nrepo="a/b"\nrelease_tag="v1"\nasset="x.zip"\n'
        'asset_sha256="0"\n'
    )
    with pytest.raises(ValueError, match="weights"):
        load_roster(str(bad))


def test_load_roster_rejects_vf_without_member(tmp_path):
    bad = tmp_path / "bad.toml"
    bad.write_text(
        '[[family]]\nid="x"\nfont_family="X"\nstyle="serif"\n'
        'format="vf"\nrepo="a/b"\nrelease_tag="v1"\nasset="x.7z"\n'
        'asset_sha256="0"\n'
    )
    with pytest.raises(ValueError, match="member"):
        load_roster(str(bad))


def test_load_roster_rejects_unknown_style(tmp_path):
    bad = tmp_path / "bad.toml"
    bad.write_text(
        '[[family]]\nid="x"\nfont_family="X"\nstyle="script"\n'
        'format="vf"\nrepo="a/b"\nrelease_tag="v1"\nasset="x.7z"\n'
        'member="x.ttf"\nasset_sha256="0"\n'
    )
    with pytest.raises(ValueError, match="style"):
        load_roster(str(bad))


def test_load_roster_rejects_unknown_format(tmp_path):
    bad = tmp_path / "bad.toml"
    bad.write_text(
        '[[family]]\nid="x"\nfont_family="X"\nstyle="serif"\n'
        'format="bitmap"\nrepo="a/b"\nrelease_tag="v1"\nasset="x.7z"\n'
        'member="x.ttf"\nasset_sha256="0"\n'
    )
    with pytest.raises(ValueError, match="format"):
        load_roster(str(bad))


# --- 丹／月 naming ------------------------------------------------------------


def test_cut_suffix_matches_family_name():
    """The npm id and the CSS family name must agree about which cut you get —
    `-dan`/`-yue` in the id, `Dan`/`Yue` in the family. `-tc` now means one
    thing only (a region variant) and is left to LXGW WenKai."""
    for fam in load_roster("roster.toml"):
        for suffix, word in (("-dan", "Dan"), ("-yue", "Yue")):
            if fam.id.endswith(suffix):
                assert fam.font_family.endswith(word), fam.id
            if fam.font_family.endswith(word):
                assert fam.id.endswith(suffix), fam.id


def test_no_min_or_gothic_left_in_shipped_names():
    """Serif/Sans across the whole roster — Source Han's own Latin naming, and
    what `--font-serif` / `--font-sans-serif` are called in CSS. GenYo is the
    exception: it is a wind-down package and keeps its published name."""
    for fam in load_roster("roster.toml"):
        if fam.id.startswith("genyo-"):
            continue
        assert " Min" not in fam.font_family, fam.id
        assert " Gothic" not in fam.font_family, fam.id
