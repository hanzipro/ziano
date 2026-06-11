import pytest
from fontTools.ttLib import TTFont

from cheritage.acquire import download, extract_member
from cheritage.slices import Slice
from cheritage.subset import subset_to_woff2


@pytest.mark.integration
def test_subset_vf_slice_keeps_axes_and_is_woff2(tmp_path):
    archive = download("GuiWonder/Shanggu", "1.028", "ShangguSerifVF_TTFs.7z")
    src = extract_member(archive, "ShangguSerifTC-VF.ttf", tmp_path)
    s = Slice(index=0, unicode_range="U+4e00-4e2f")  # a block of common Han
    out = tmp_path / "slice0.woff2"
    subset_to_woff2(str(src), s, str(out), keep_variations=True)
    data = out.read_bytes()
    assert data[:4] == b"wOF2"  # woff2 magic
    font = TTFont(str(out))
    assert font.flavor == "woff2"
    assert "fvar" in font  # variable axes retained
    cmap = font.getBestCmap()
    assert 0x4E00 in cmap  # requested codepoint present
    assert 0x0041 not in cmap  # un-requested codepoint dropped
