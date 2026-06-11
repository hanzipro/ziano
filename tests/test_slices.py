from pathlib import Path

from cheritage.slices import Slice, parse_css2_unicode_ranges


def test_parse_css2_yields_one_slice_per_font_face():
    css = Path("tests/fixtures/noto-sans-tc.css2.txt").read_text()
    slices = parse_css2_unicode_ranges(css)
    assert 100 <= len(slices) <= 130  # ~105 blocks
    assert all(isinstance(s, Slice) for s in slices)
    assert slices[0].index == 0
    assert "U+" in slices[0].unicode_range
    for s in slices:
        for tok in s.unicode_range.split(","):
            assert tok.strip().startswith("U+")


def test_slice_codepoints_expands_ranges():
    s = Slice(index=0, unicode_range="U+41-43, U+4e00")
    assert s.codepoints() == {0x41, 0x42, 0x43, 0x4E00}


def test_save_then_load_roundtrips(tmp_path):
    from cheritage.slices import load_slices, save_slices

    original = [Slice(0, "U+41-43"), Slice(1, "U+4e00, U+4e01")]
    path = tmp_path / "slices.json"
    save_slices(original, str(path))
    assert load_slices(str(path)) == original
