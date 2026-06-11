import sys
from pathlib import Path

from .acquire import download, download_raw, extract_member
from .cssgen import generate_css, generate_index_css, weight_css_name, woff2_name
from .package import write_package_skeleton
from .roster import FamilyConfig, load_roster, slice_table_name
from .slices import Slice, load_slices
from .subset import subset_to_woff2

_EXTRACT_DIR = Path(".cache/extracted")


def _acquire(fam: FamilyConfig, work: Path, member: str, sha256: str = "") -> Path:
    """Resolve one font/license file to a local path, for either source kind."""
    if fam.source == "raw":
        return download_raw(fam.repo, fam.release_tag, member, expected_sha256=sha256 or None)
    archive = download(fam.repo, fam.release_tag, fam.asset, expected_sha256=fam.asset_sha256 or None)
    return extract_member(archive, member, work)


def _build_vf(fam: FamilyConfig, work: Path, slices: list[Slice],
              *, dest: str, version: str, license_text: str) -> Path:
    font_path = _acquire(fam, work, fam.member)
    root = write_package_skeleton(
        fam, dest=dest, version=version,
        css=generate_css(fam, slices), license_text=license_text,
    )
    for s in slices:
        out = root / "files" / woff2_name(fam, s.index)
        subset_to_woff2(str(font_path), s, str(out), keep_variations=True)
    return root


def _build_static(fam: FamilyConfig, work: Path, slices: list[Slice],
                  *, dest: str, version: str, license_text: str,
                  only_weights: list[int] | None) -> Path:
    weights = [w for w in fam.weights if only_weights is None or w.weight in only_weights]
    extra_css = {weight_css_name(w.weight): generate_css(fam, slices, weight=w.weight)
                 for w in weights}
    root = write_package_skeleton(
        fam, dest=dest, version=version,
        css=generate_index_css(fam), extra_css=extra_css, license_text=license_text,
    )
    for w in weights:
        font_path = _acquire(fam, work, w.member, w.sha256)
        for s in slices:
            out = root / "files" / woff2_name(fam, s.index, w.weight)
            subset_to_woff2(str(font_path), s, str(out), keep_variations=False)
    return root


def build_family(family_id: str, *, roster_path: str, dest: str, version: str,
                 only_weights: list[int] | None = None) -> Path:
    fam = next(f for f in load_roster(roster_path) if f.id == family_id)
    work = _EXTRACT_DIR / fam.id
    license_text = Path(_acquire(fam, work, fam.license_member)).read_text(
        encoding="utf-8", errors="replace")
    slices = load_slices(f"data/slices.{slice_table_name(fam.style)}.json")

    if fam.format == "vf":
        return _build_vf(fam, work, slices,
                         dest=dest, version=version, license_text=license_text)
    return _build_static(fam, work, slices,
                         dest=dest, version=version, license_text=license_text,
                         only_weights=only_weights)


if __name__ == "__main__":  # python -m cheritage.build <family_id>
    fam_id = sys.argv[1]
    out = build_family(fam_id, roster_path="roster.toml", dest="dist", version="0.1.0")
    n = len(list((out / "files").glob("*.woff2")))
    print(f"built {out} ({n} woff2 files)")
