import pytest

from cheritage.roster import FamilyConfig, load_roster


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
    assert serif.member == "ShangguSerifTC-VF.ttf"
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
