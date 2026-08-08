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
from .slices import Slice, format_unicode_range, load_slices, prune_slices
from .subset import subset_to_woff2
from .upright import prepare as prepare_upright

_EXTRACT_DIR = Path(".cache/extracted")
_PREPARED_DIR = Path(".cache/prepared")


def _acquire(fam: FamilyConfig, work: Path, member: str, sha256: str = "") -> Path:
    """Resolve one font/license file to a local path, for either source kind."""
    if fam.source == "raw":
        return download_raw(fam.repo, fam.release_tag, member, expected_sha256=sha256 or None)
    archive = download(fam.repo, fam.release_tag, fam.asset, expected_sha256=fam.asset_sha256 or None)
    return extract_member(archive, member, work)


def _css_files(fam: FamilyConfig, slices: list[Slice]) -> dict[str, str]:
    """Every stylesheet a package ships, keyed by its path inside the package.

    One entry per display mode (plus one per weight for static families), and —
    for a family whose name doesn't state its cut — the same set again under
    `dan/`, declaring the qualified name against the very same woff2. Two labels
    for one font: `Shanggu Serif` is what npm has always called this cut (no
    suffix means 丹), and `Shanggu Serif Dan` is for pages that would rather say
    so out loud.

    `url()` is relative to the stylesheet, so every extra directory level costs
    another `../`.
    """
    out: dict[str, str] = {}
    variants = [("", "", "./files", "../files")]
    if fam.cut:
        variants.append(
            (f"{fam.cut_dir}/", fam.qualified_family, "../files", "../../files"))

    for prefix, family, base_top, base_weight in variants:
        for mode in DISPLAY_MODES:
            if fam.format == "vf":
                out[prefix + mode_css_name(mode)] = generate_css(
                    fam, slices, display=mode, files_base=base_top, family=family)
                continue
            out[prefix + mode_css_name(mode)] = generate_aggregate_css(
                fam, slices, [w.weight for w in fam.weights], display=mode,
                files_base=base_top, family=family)
            for w in fam.weights:
                out[prefix + weight_css_path(mode, w.weight)] = generate_css(
                    fam, slices, weight=w.weight, display=mode,
                    files_base=base_weight, family=family)
    return out


def _build_vf(fam: FamilyConfig, work: Path, slices: list[Slice],
              *, dest: str, version: str, license_text: str) -> Path:
    font_path = prepare_upright(
        _acquire(fam, work, fam.member),
        _PREPARED_DIR / fam.id,
        family=fam.qualified_family,
        family_zh=fam.font_family_zh,
        family_zh_hans=fam.font_family_zh_hans,
    )
    # one top-level entry per display mode; the woff2 are shared (mode-independent).
    css_files = _css_files(fam, slices)
    root = write_package_skeleton(
        fam, dest=dest, version=version,
        css_files=css_files, license_text=license_text,
    )
    written = set()
    for s in slices:
        name = woff2_name(fam, s.index)
        subset_to_woff2(str(font_path), s, str(root / "files" / name), keep_variations=True)
        written.add(name)
    _drop_unwritten(root, written)
    return root


def _build_static(fam: FamilyConfig, work: Path, slices: list[Slice],
                  *, dest: str, version: str, license_text: str,
                  only_weights: list[int] | None) -> Path:
    weights = [w for w in fam.weights if only_weights is None or w.weight in only_weights]
    # index.css lists every weight regardless of only_weights, so the published
    # entry is complete; only_weights only limits which woff2 we actually subset.
    css_files = _css_files(fam, slices)
    root = write_package_skeleton(
        fam, dest=dest, version=version,
        css_files=css_files, license_text=license_text,
    )
    written = set()
    for w in weights:
        font_path = prepare_upright(
            _acquire(fam, work, w.member, w.sha256),
            _PREPARED_DIR / fam.id,
            family=fam.qualified_family,
            family_zh=fam.font_family_zh,
            family_zh_hans=fam.font_family_zh_hans,
        )
        for s in slices:
            name = woff2_name(fam, s.index, w.weight)
            subset_to_woff2(str(font_path), s, str(root / "files" / name), keep_variations=False)
            written.add(name)
    # only safe when this run built every weight; a partial build would delete
    # the others' files.
    if only_weights is None:
        _drop_unwritten(root, written)
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
    cmap = cmap_codepoints(str(prepare_upright(
        _acquire(fam, work, repr_member, repr_sha),
        _PREPARED_DIR / fam.id,
        family=fam.qualified_family,
        family_zh=fam.font_family_zh,
        family_zh_hans=fam.font_family_zh_hans,
    )))
    slices = prune_slices(slices, cmap)

    if fam.format == "vf":
        return _build_vf(fam, work, slices,
                         dest=dest, version=version, license_text=license_text)
    return _build_static(fam, work, slices,
                         dest=dest, version=version, license_text=license_text,
                         only_weights=only_weights)


def _drop_unwritten(root: Path, written: set[str]) -> list[str]:
    """Delete woff2 in <root>/files that this build did not produce.

    Nothing else clears the directory, so a slice that stops being generated —
    the pruned-to-cmap list shrinks, a family is re-sliced after an upstream
    bump — leaves its file behind forever. Those orphans are unreachable (no
    @font-face references them) but they still ship, and they still carry
    whatever metrics they were built with, which is how they get noticed.
    """
    stale = [p.name for p in (root / "files").glob("*.woff2") if p.name not in written]
    for name in stale:
        (root / "files" / name).unlink()
    return stale


def prune_dist_woff2(root: Path, slices: list[Slice]) -> None:
    """Delete woff2 in <root>/files whose slice index isn't in `slices` (css-only mode
    reuses the rest as-is). Filename is <id>.<idx>.woff2 (vf) or <id>.<weight>.<idx>.woff2
    (static); the index is always the last dotted token."""
    keep = {s.index for s in slices}
    for p in (root / "files").glob("*.woff2"):
        if int(p.stem.split(".")[-1]) not in keep:
            p.unlink()


def recss_dist(family_id: str, *, roster_path: str, dest: str, version: str) -> Path:
    """Regenerate a package's CSS + bump its version WITHOUT re-subsetting. Each
    @font-face's unicode-range is read back from the existing woff2's own cmap, and woff2
    with an empty cmap are dropped. For shipping a CSS-only fix (the unicode-range prune)
    on an already-built dist: every kept woff2 stays byte-identical, so the change is just
    the CSS (+ version). Requires a prior full build to exist in dest/<id>."""
    fam = next(f for f in load_roster(roster_path) if f.id == family_id)
    root = Path(dest) / fam.id
    # one cmap per slice index (all weights of a slice share coverage); skip empties.
    by_idx: dict[int, Slice] = {}
    for p in sorted((root / "files").glob("*.woff2")):
        idx = int(p.stem.split(".")[-1])
        if idx not in by_idx and (cmap := cmap_codepoints(str(p))):
            by_idx[idx] = Slice(idx, format_unicode_range(cmap))
    slices = [by_idx[i] for i in sorted(by_idx)]
    prune_dist_woff2(root, slices)  # drop the now-unreferenced empty woff2

    license_text = (root / "LICENSE").read_text(encoding="utf-8")
    css_files = _css_files(fam, slices)
    return write_package_skeleton(
        fam, dest=dest, version=version, css_files=css_files, license_text=license_text)


if __name__ == "__main__":  # python -m ziano.build <family_id>
    fam_id = sys.argv[1]
    out = build_family(fam_id, roster_path="roster.toml", dest="dist", version="0.1.0")
    n = len(list((out / "files").glob("*.woff2")))
    print(f"built {out} ({n} woff2 files)")
