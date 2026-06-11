import tomllib
from dataclasses import dataclass

_STYLES = {"serif", "sans", "cursive"}
_FORMATS = {"vf", "static"}
_SOURCES = {"release", "raw"}

# Which slice table a style uses. We use Google Fonts' single canonical
# Traditional-Chinese slicing strategy (Apache-2.0, googlefonts/nam-files) for
# every print/handwriting style — the partition is font-agnostic Unicode buckets.
# (A simplified-chinese table could be added later for SC-default fonts.)
_SLICE_TABLE = {
    "serif": "traditional-chinese",
    "sans": "traditional-chinese",
    "cursive": "traditional-chinese",
}


def slice_table_name(style: str) -> str:
    return _SLICE_TABLE[style]


@dataclass(frozen=True)
class Weight:
    weight: int  # CSS font-weight (from the font's usWeightClass)
    member: str  # per-weight font file (archive member, or raw repo path)
    sha256: str = ""  # raw source: per-file checksum (release uses asset_sha256)


@dataclass(frozen=True)
class FamilyConfig:
    id: str
    font_family: str
    style: str
    format: str
    repo: str
    release_tag: str  # release tag (source=release) or git ref/tag (source=raw)
    asset: str = ""  # release: the downloadable archive; unused for raw
    asset_sha256: str = ""
    source: str = "release"  # "release" (GitHub release asset) | "raw" (repo file)
    license_member: str = "LICENSE.txt"
    member: str = ""  # vf: the single font file inside the archive
    weights: tuple[Weight, ...] = ()  # static: one entry per weight
    weight_min: int = 400  # vf: fvar axis bounds → CSS "font-weight: min max"
    weight_max: int = 400
    # local() names tried before the webfont url in @font-face src, so a browser
    # with the system font (e.g. macOS "Klee One") downloads nothing.
    local_names: tuple[str, ...] = ()


def load_roster(path: str) -> list[FamilyConfig]:
    with open(path, "rb") as fh:
        data = tomllib.load(fh)
    families = []
    for raw in data.get("family", []):
        raw = dict(raw)
        fam_id = raw.get("id")
        if raw.get("style") not in _STYLES:
            raise ValueError(f"invalid style {raw.get('style')!r} in {fam_id!r}")
        fmt = raw.get("format")
        if fmt not in _FORMATS:
            raise ValueError(f"invalid format {fmt!r} in {fam_id!r}")
        if raw.get("source", "release") not in _SOURCES:
            raise ValueError(f"invalid source {raw.get('source')!r} in {fam_id!r}")
        weights = tuple(Weight(**w) for w in raw.pop("weights", []))
        raw["local_names"] = tuple(raw.get("local_names", []))
        if fmt == "vf" and not raw.get("member"):
            raise ValueError(f"vf family {fam_id!r} needs a member")
        if fmt == "static" and not weights:
            raise ValueError(f"static family {fam_id!r} needs weights")
        families.append(FamilyConfig(weights=weights, **raw))
    return families
