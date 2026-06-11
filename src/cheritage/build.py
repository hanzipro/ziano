import sys
from pathlib import Path

from .acquire import download, extract_member
from .cssgen import generate_css, woff2_name
from .package import write_package_skeleton
from .roster import load_roster
from .slices import load_slices
from .subset import subset_to_woff2

_EXTRACT_DIR = Path(".cache/extracted")


def build_family(family_id: str, *, roster_path: str, dest: str, version: str) -> Path:
    fam = next(f for f in load_roster(roster_path) if f.id == family_id)

    archive = download(fam.repo, fam.release_tag, fam.asset, expected_sha256=fam.asset_sha256)
    work = _EXTRACT_DIR / fam.id
    font_path = extract_member(archive, fam.member, work)
    license_path = extract_member(archive, fam.license_member, work)
    license_text = Path(license_path).read_text(encoding="utf-8", errors="replace")

    slices = load_slices(f"data/slices.{fam.style}.json")

    root = write_package_skeleton(
        fam, dest=dest, version=version,
        css=generate_css(fam, slices), license_text=license_text,
    )
    for s in slices:
        out = root / "files" / woff2_name(fam, s.index)
        subset_to_woff2(str(font_path), s, str(out), keep_variations=(fam.format == "vf"))
    return root


if __name__ == "__main__":  # python -m cheritage.build <family_id>
    fam_id = sys.argv[1]
    out = build_family(fam_id, roster_path="roster.toml", dest="dist", version="0.1.0")
    n = len(list((out / "files").glob("*.woff2")))
    print(f"built {out} ({n} slices)")
