import pytest

from ziano.coverage import cmap_codepoints, coverage_report


def test_coverage_report_counts_and_missing():
    cmap = {0x6236, 0x9AA8}  # 戶 骨
    rep = coverage_report(cmap, "戶骨直")  # 直 (U+76F4) missing
    assert rep["total_glyphs"] == 2
    assert rep["target_total"] == 3
    assert rep["target_covered"] == 2
    assert rep["missing"] == ["直"]


@pytest.mark.integration
def test_real_families_cover_common_hard_set(tmp_path):
    from ziano.acquire import download, extract_member

    archive = download("GuiWonder/Shanggu", "1.028", "ShangguSerifVF_TTFs.7z")
    ttf = extract_member(archive, "ShangguSerifTC-VF.ttf", tmp_path)
    target = open("data/common-hard-tc.txt").read().strip()
    rep = coverage_report(cmap_codepoints(str(ttf)), target)
    # the chosen default MUST cover the entire common-hard set
    assert rep["target_covered"] == rep["target_total"], rep["missing"]
