import hashlib
import os
import urllib.request
import zipfile
from pathlib import Path

CACHE = Path(".cache")

_PLACEHOLDER_HASHES = {"0", "", "PLACEHOLDER_FILLED_IN_TASK_8"}


def release_asset_url(repo: str, tag: str, asset: str) -> str:
    return f"https://github.com/{repo}/releases/download/{tag}/{asset}"


def raw_file_url(repo: str, ref: str, path: str) -> str:
    return f"https://raw.githubusercontent.com/{repo}/{ref}/{path}"


def _fetch(url: str, dest: Path) -> None:
    req = urllib.request.Request(url, headers={"User-Agent": "ziano-build"})
    with urllib.request.urlopen(req) as resp, open(dest, "wb") as out:
        while chunk := resp.read(1 << 20):
            out.write(chunk)


def _verify(dest: Path, expected_sha256: str | None, what: str) -> Path:
    if expected_sha256 and expected_sha256 not in _PLACEHOLDER_HASHES:
        actual = sha256_file(str(dest))
        if actual != expected_sha256:
            os.remove(dest)
            raise ValueError(f"sha256 mismatch for {what}: got {actual}, want {expected_sha256}")
    return dest


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
        _fetch(release_asset_url(repo, tag, asset), dest)
    return _verify(dest, expected_sha256, asset)


def download_raw(repo: str, ref: str, path: str, *, expected_sha256: str | None = None) -> Path:
    """Download a single file from a repo tree at a pinned ref (no GitHub release)."""
    CACHE.mkdir(exist_ok=True)
    flat = path.replace("/", "_")
    dest = CACHE / f"{repo.replace('/', '__')}__{ref}__{flat}"
    if not dest.exists():
        _fetch(raw_file_url(repo, ref, path), dest)
    return _verify(dest, expected_sha256, path)


def extract_member(archive: Path, member: str, dest_dir: Path) -> Path:
    """Extract one font file from a release asset into dest_dir, return its path.

    Handles .7z (Shanggu) and .zip archives, plus bare .ttf/.otf passthrough.
    """
    archive = Path(archive)
    dest_dir = Path(dest_dir)
    dest_dir.mkdir(parents=True, exist_ok=True)
    suffix = archive.suffix.lower()

    if suffix in (".ttf", ".otf"):
        return archive

    if suffix == ".7z":
        import py7zr

        with py7zr.SevenZipFile(archive) as z:
            names = set(z.getnames())
            if member not in names:
                raise FileNotFoundError(f"{member!r} not in {archive.name}: {sorted(names)}")
            z.extract(path=str(dest_dir), targets=[member])
        return dest_dir / member

    if zipfile.is_zipfile(archive):
        with zipfile.ZipFile(archive) as z:
            if member not in z.namelist():
                raise FileNotFoundError(f"{member!r} not in {archive.name}: {z.namelist()}")
            z.extract(member, dest_dir)
        return dest_dir / member

    raise ValueError(f"unsupported asset type: {archive.name}")
