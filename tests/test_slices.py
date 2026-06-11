from pathlib import Path

from cheritage.slices import (
    Slice,
    format_unicode_range,
    load_slices,
    parse_slicing_strategy,
    save_slices,
)

PROTO = """\
# a comment
subsets {
  codepoints: 65 # A
  codepoints: 66 # B
  codepoints: 67 # C
  codepoints: 19968 # 一
}
subsets {
  codepoints: 32
}
"""


def test_format_unicode_range_collapses_runs():
    assert format_unicode_range({0x41, 0x42, 0x43, 0x4E00}) == "U+41-43, U+4e00"
    assert format_unicode_range({0x20}) == "U+20"


def test_parse_slicing_strategy_yields_indexed_slices():
    slices = parse_slicing_strategy(PROTO)
    assert len(slices) == 2
    assert slices[0].index == 0 and slices[1].index == 1
    assert slices[0].unicode_range == "U+41-43, U+4e00"
    assert slices[0].codepoints() == {0x41, 0x42, 0x43, 0x4E00}
    assert slices[1].unicode_range == "U+20"


def test_real_tc_strategy_parses_to_120_slices():
    text = Path("data/sources/traditional-chinese_default.txt").read_text()
    slices = parse_slicing_strategy(text)
    assert len(slices) == 120
    total = set()
    for s in slices:
        total |= s.codepoints()
    assert len(total) == 17704


def test_save_then_load_roundtrips(tmp_path):
    original = [Slice(0, "U+41-43"), Slice(1, "U+4e00, U+4e01")]
    path = tmp_path / "slices.json"
    save_slices(original, str(path))
    assert load_slices(str(path)) == original
