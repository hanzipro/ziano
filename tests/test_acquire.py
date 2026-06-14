import hashlib

import pytest

from ziano.acquire import release_asset_url, sha256_file


def test_release_asset_url_is_github_releases_download():
    url = release_asset_url("GuiWonder/Shanggu", "1.028", "ShangguSerifVF_TTFs.7z")
    assert url == (
        "https://github.com/GuiWonder/Shanggu/releases/download/"
        "1.028/ShangguSerifVF_TTFs.7z"
    )


def test_sha256_file(tmp_path):
    p = tmp_path / "f.bin"
    p.write_bytes(b"hello")
    assert sha256_file(str(p)) == hashlib.sha256(b"hello").hexdigest()


def test_raw_file_url():
    from ziano.acquire import raw_file_url
    assert raw_file_url("fontworks-fonts/Klee", "Version1.000", "fonts/ttf/KleeOne-Regular.ttf") == (
        "https://raw.githubusercontent.com/fontworks-fonts/Klee/Version1.000/"
        "fonts/ttf/KleeOne-Regular.ttf"
    )


@pytest.mark.integration
def test_download_raw_klee_is_a_real_font():
    from fontTools.ttLib import TTFont
    from ziano.acquire import download_raw
    p = download_raw(
        "fontworks-fonts/Klee", "Version1.000", "fonts/ttf/KleeOne-Regular.ttf",
        expected_sha256="74cb0a6523cc22b221ceaa7b78b56cea66512ec14b4145fd0102ffe27c30d084",
    )
    assert TTFont(str(p))["name"].getDebugName(1) == "Klee One"


def test_download_rejects_sha256_mismatch(tmp_path, monkeypatch):
    import ziano.acquire as acq

    monkeypatch.setattr(acq, "CACHE", tmp_path)
    # pre-seed the cache so no network is hit, with wrong-hash content
    dest = tmp_path / "GuiWonder__Shanggu__1.028__x.7z"
    dest.write_bytes(b"not the real font")
    with pytest.raises(ValueError, match="sha256 mismatch"):
        acq.download("GuiWonder/Shanggu", "1.028", "x.7z", expected_sha256="deadbeef")
    assert not dest.exists()  # corrupt file removed


@pytest.mark.integration
def test_download_shanggu_serif_archive_is_real():
    from ziano.acquire import download

    p = download(
        "GuiWonder/Shanggu", "1.028", "ShangguSerifVF_TTFs.7z",
        expected_sha256="36c26a19f159d4e388de115e222fd663dd7d0629d0dba48b289f85a7cd85c399",
    )
    assert p.stat().st_size > 1_000_000
    assert p.read_bytes()[:2] == b"7z"  # 7z signature 0x37 0x7A


@pytest.mark.integration
def test_extract_member_pulls_tc_vf_from_7z(tmp_path):
    from fontTools.ttLib import TTFont

    from ziano.acquire import download, extract_member

    archive = download("GuiWonder/Shanggu", "1.028", "ShangguSerifVF_TTFs.7z")
    ttf = extract_member(archive, "ShangguSerifTC-VF.ttf", tmp_path)
    assert ttf.exists()
    font = TTFont(str(ttf))
    assert "fvar" in font  # it is a variable font


def test_extract_member_missing_raises(tmp_path):
    from ziano.acquire import extract_member

    # reuse the seeded cache copy if present, else skip the body via passthrough
    real = __import__("pathlib").Path(
        ".cache/GuiWonder__Shanggu__1.028__ShangguSerifVF_TTFs.7z"
    )
    if not real.exists():
        pytest.skip("archive not cached")
    with pytest.raises(FileNotFoundError, match="not in"):
        extract_member(real, "DoesNotExist.ttf", tmp_path)
