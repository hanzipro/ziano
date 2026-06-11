import tomllib
from dataclasses import dataclass, field

_STYLES = {"serif", "sans", "cursive"}
_FORMATS = {"vf", "static"}

# Which snapshot slice table a style uses. The partition is just Unicode
# buckets (cache-friendly boundaries), so it is script-agnostic; cursive (楷書,
# a handwriting/brush style) reuses the serif table.
_SLICE_TABLE = {"serif": "serif", "sans": "sans", "cursive": "serif"}


def slice_table_name(style: str) -> str:
    return _SLICE_TABLE[style]


@dataclass(frozen=True)
class Weight:
    weight: int  # CSS font-weight (from the font's usWeightClass)
    member: str  # the per-weight font file inside the asset archive


@dataclass(frozen=True)
class FamilyConfig:
    id: str
    font_family: str
    style: str
    format: str
    repo: str
    release_tag: str
    asset: str
    asset_sha256: str
    license_member: str = "LICENSE.txt"
    member: str = ""  # vf: the single font file inside the archive
    weights: tuple[Weight, ...] = ()  # static: one entry per weight
    weight_min: int = 400  # vf: fvar axis bounds → CSS "font-weight: min max"
    weight_max: int = 400


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
        weights = tuple(Weight(**w) for w in raw.pop("weights", []))
        if fmt == "vf" and not raw.get("member"):
            raise ValueError(f"vf family {fam_id!r} needs a member")
        if fmt == "static" and not weights:
            raise ValueError(f"static family {fam_id!r} needs weights")
        families.append(FamilyConfig(weights=weights, **raw))
    return families
