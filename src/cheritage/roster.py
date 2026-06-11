import tomllib
from dataclasses import dataclass

_STYLES = {"serif", "sans"}
_FORMATS = {"vf", "static"}


@dataclass(frozen=True)
class FamilyConfig:
    id: str
    font_family: str
    style: str
    format: str
    repo: str
    release_tag: str
    asset: str
    member: str
    asset_sha256: str
    license_member: str = "LICENSE.txt"
    weight_min: int = 400
    weight_max: int = 400


def load_roster(path: str) -> list[FamilyConfig]:
    with open(path, "rb") as fh:
        data = tomllib.load(fh)
    families = []
    for raw in data.get("family", []):
        if raw.get("style") not in _STYLES:
            raise ValueError(f"invalid style {raw.get('style')!r} in {raw.get('id')!r}")
        if raw.get("format") not in _FORMATS:
            raise ValueError(f"invalid format {raw.get('format')!r} in {raw.get('id')!r}")
        families.append(FamilyConfig(**raw))
    return families
