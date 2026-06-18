import sys
from pathlib import Path

from .acquire import download, download_raw, extract_member
from .coverage import cmap_codepoints
from .cssgen import (
    DISPLAY_MODES,
    generate_aggregate_css,
    generate_css,
    mode_css_name,
    weight_css_path,
    woff2_name,
)
from .package import write_package_skeleton
from .roster import FamilyConfig, load_roster, slice_table_name
from .slices import Slice, load_slices, prune_slices
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
    # one top-level entry per display mode; the woff2 are shared (mode-independent).
    css_files = {mode_css_name(m): generate_css(fam, slices, display=m)
                 for m in DISPLAY_MODES}
    root = write_package_skeleton(
        fam, dest=dest, version=version,
        css_files=css_files, license_text=license_text,
    )
    for s in slices:
        out = root / "files" / woff2_name(fam, s.index)
        subset_to_woff2(str(font_path), s, str(out), keep_variations=True)
    return root


def _build_static(fam: FamilyConfig, work: Path, slices: list[Slice],
                  *, dest: str, version: str, license_text: str,
                  only_weights: list[int] | None) -> Path:
    weights = [w for w in fam.weights if only_weights is None or w.weight in only_weights]
    # index.css lists every weight regardless of only_weights, so the published
    # entry is complete; only_weights only limits which woff2 we actually subset.
    all_weights = [w.weight for w in fam.weights]
    css_files: dict[str, str] = {}
    for mode in DISPLAY_MODES:
        css_files[mode_css_name(mode)] = generate_aggregate_css(
            fam, slices, all_weights, display=mode)
        for w in fam.weights:
            css_files[weight_css_path(mode, w.weight)] = generate_css(
                fam, slices, weight=w.weight, display=mode, files_base="../files")
    root = write_package_skeleton(
        fam, dest=dest, version=version,
        css_files=css_files, license_text=license_text,
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
    slices = load_slices(f"data/slices.{slice_table_name(fam.style, fam.slice_table)}.json")

    # Prune each slice's unicode-range to the font's real cmap so no @font-face claims a
    # codepoint its woff2 lacks. Safari honours the bare unicode-range and renders .notdef
    # instead of falling through — so the all-emoji slices (a CJK font has zero glyphs
    # there) would otherwise swallow 🌞 etc. rather than letting the system emoji font
    # render them. Empty slices are dropped entirely. (See slices.prune_slices.)
    repr_member = fam.member if fam.format == "vf" else fam.weights[0].member
    repr_sha = "" if fam.format == "vf" else fam.weights[0].sha256
    cmap = cmap_codepoints(str(_acquire(fam, work, repr_member, repr_sha)))
    slices = prune_slices(slices, cmap)

    if fam.format == "vf":
        return _build_vf(fam, work, slices,
                         dest=dest, version=version, license_text=license_text)
    return _build_static(fam, work, slices,
                         dest=dest, version=version, license_text=license_text,
                         only_weights=only_weights)


if __name__ == "__main__":  # python -m ziano.build <family_id>
    fam_id = sys.argv[1]
    out = build_family(fam_id, roster_path="roster.toml", dest="dist", version="0.1.0")
    n = len(list((out / "files").glob("*.woff2")))
    print(f"built {out} ({n} woff2 files)")
