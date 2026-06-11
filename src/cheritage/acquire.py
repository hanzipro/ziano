import hashlib
import os
import urllib.request
from pathlib import Path

CACHE = Path(".cache")

_PLACEHOLDER_HASHES = {"0", "", "PLACEHOLDER_FILLED_IN_TASK_8"}


def release_asset_url(repo: str, tag: str, asset: str) -> str:
    return f"https://github.com/{repo}/releases/download/{tag}/{asset}"


def sha256_file(path: str) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def download(repo: str, tag: str, asset: str, *, expected_sha256: str | None = None) -> Path:
    CACHE.mkdir(exist_ok=True)
    dest = CACHE / f"{repo.replace('/', '__')}__{tag}__{asset}"
    if not dest.exists():
        url = release_asset_url(repo, tag, asset)
        req = urllib.request.Request(url, headers={"User-Agent": "cheritage-build"})
        with urllib.request.urlopen(req) as resp, open(dest, "wb") as out:
            while chunk := resp.read(1 << 20):
                out.write(chunk)
    if expected_sha256 and expected_sha256 not in _PLACEHOLDER_HASHES:
        actual = sha256_file(str(dest))
        if actual != expected_sha256:
            os.remove(dest)
            raise ValueError(
                f"sha256 mismatch for {asset}: got {actual}, want {expected_sha256}"
            )
    return dest
