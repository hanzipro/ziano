import hashlib

import pytest

from cheritage.acquire import release_asset_url, sha256_file


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


def test_download_rejects_sha256_mismatch(tmp_path, monkeypatch):
    import cheritage.acquire as acq

    monkeypatch.setattr(acq, "CACHE", tmp_path)
    # pre-seed the cache so no network is hit, with wrong-hash content
    dest = tmp_path / "GuiWonder__Shanggu__1.028__x.7z"
    dest.write_bytes(b"not the real font")
    with pytest.raises(ValueError, match="sha256 mismatch"):
        acq.download("GuiWonder/Shanggu", "1.028", "x.7z", expected_sha256="deadbeef")
    assert not dest.exists()  # corrupt file removed


@pytest.mark.integration
def test_download_shanggu_serif_archive_is_real():
    from cheritage.acquire import download

    p = download(
        "GuiWonder/Shanggu", "1.028", "ShangguSerifVF_TTFs.7z",
        expected_sha256="36c26a19f159d4e388de115e222fd663dd7d0629d0dba48b289f85a7cd85c399",
    )
    assert p.stat().st_size > 1_000_000
    assert p.read_bytes()[:2] == b"7z"  # 7z signature 0x37 0x7A
