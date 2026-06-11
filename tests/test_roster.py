import pytest

from cheritage.roster import FamilyConfig, load_roster


def test_load_roster_returns_typed_families():
    families = load_roster("roster.toml")
    by_id = {f.id: f for f in families}
    assert set(by_id) == {"shanggu-serif", "shanggu-sans"}
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
