import tomllib
from dataclasses import dataclass

_STYLES = {"serif", "sans", "cursive"}
_FORMATS = {"vf", "static"}
_SOURCES = {"release", "raw"}

# Which slice table a style uses by default. We use Google Fonts' canonical
# slicing strategies (Apache-2.0, googlefonts/nam-files) — the partitions are
# font-agnostic frequency-ordered Unicode buckets. Print/handwriting TC styles
# default to the Traditional-Chinese partition; a family whose default script is
# SC or JP overrides this via `slice_table` in roster.toml (e.g. LXGW WenKai SC →
# "simplified-chinese", Klee One → "japanese"), so SC/JP-only codepoints (鹜, ゐ…)
# land in a slice instead of being dropped.
_SLICE_TABLE = {
    "serif": "traditional-chinese",
    "sans": "traditional-chinese",
    "cursive": "traditional-chinese",
}
_SLICE_TABLES = {"traditional-chinese", "simplified-chinese", "japanese"}


def slice_table_name(style: str, override: str = "") -> str:
    if override:
        if override not in _SLICE_TABLES:
            raise ValueError(f"unknown slice_table {override!r}")
        return override
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
    # Chinese family name for the zh-* name-table slots; the English one fills
    # every other slot. Empty for JP-only faces that never had one.
    font_family_zh: str = ""
    # Simplified form for the zh-CN / zh-SG slots, when it differs (體→体,
    # 鶩→鹜). Empty means "same as font_family_zh".
    font_family_zh_hans: str = ""
    # Which cut this family is, when its own name doesn't say. Only the
    # unsuffixed families carry it: on npm, no suffix always means 丹 (Dan), so
    # `Shanggu Serif` IS the 丹 cut and never says so. The value gives them a
    # second, qualified CSS name (`Shanggu Serif Dan`) shipped as its own
    # stylesheet under `dan/`, and it is the name written into the font files.
    # One font, two labels; `-yue` families need none, their name carries it.
    cut: str = ""
    asset: str = ""  # release: the downloadable archive; unused for raw
    asset_sha256: str = ""
    source: str = "release"  # "release" (GitHub release asset) | "raw" (repo file)
    # override the style→slice-table default (see _SLICE_TABLE). Used by SC/JP-default
    # families so their script-specific codepoints get sliced instead of dropped.
    slice_table: str = ""
    # TC glyph form: heritage/orthodox 傳承字形 (the project's core) vs the MOE
    # 國字標準字體 standard form. Only meaningful for TC families; iansui is the
    # lone standard-form one. Drives the npm keyword/branding, not the slicing.
    heritage: bool = True
    license_member: str = "LICENSE.txt"
    member: str = ""  # vf: the single font file inside the archive
    weights: tuple[Weight, ...] = ()  # static: one entry per weight
    weight_min: int = 400  # vf: fvar axis bounds → CSS "font-weight: min max"
    weight_max: int = 400
    # local() names tried before the webfont url in @font-face src, so a browser
    # with the system font (e.g. macOS "Klee One") downloads nothing.
    local_names: tuple[str, ...] = ()

    @property
    def qualified_family(self) -> str:
        """The family name that states the cut — `Shanggu Serif Dan`. Falls back
        to the plain name for families whose own name already says it."""
        return f"{self.font_family} {self.cut}" if self.cut else self.font_family

    @property
    def cut_dir(self) -> str:
        """Subfolder holding the qualified-name stylesheets, e.g. `dan`."""
        return self.cut.lower()


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
