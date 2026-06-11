from .roster import FamilyConfig
from .slices import Slice


def woff2_name(fam: FamilyConfig, slice_index: int, weight: int | None = None) -> str:
    if fam.format == "vf" or weight is None:
        return f"{fam.id}.{slice_index}.woff2"
    return f"{fam.id}.{weight}.{slice_index}.woff2"


def _src(fam: FamilyConfig, slice_index: int, weight: int | None) -> str:
    # local() names first → a browser with the system font downloads nothing.
    parts = [f'local("{n}")' for n in fam.local_names]
    parts.append(f"url(./files/{woff2_name(fam, slice_index, weight)}) format('woff2')")
    return "src: " + ", ".join(parts) + ";"


def _face(fam: FamilyConfig, s: Slice, weight: int | None) -> str:
    if fam.format == "vf":
        weight_decl = f"font-weight: {fam.weight_min} {fam.weight_max};"
    else:
        weight_decl = f"font-weight: {weight};"
    return (
        "@font-face {\n"
        f"  font-family: '{fam.font_family}';\n"
        "  font-style: normal;\n"
        f"  {weight_decl}\n"
        "  font-display: swap;\n"
        f"  {_src(fam, s.index, weight)}\n"
        f"  unicode-range: {s.unicode_range};\n"
        "}\n"
    )


def generate_css(fam: FamilyConfig, slices: list[Slice], weight: int | None = None) -> str:
    return "\n".join(_face(fam, s, weight) for s in slices)


def weight_css_name(weight: int) -> str:
    return f"{weight}.css"


def generate_index_css(fam: FamilyConfig) -> str:
    """For static families: an index.css that @imports every per-weight css."""
    weights = sorted(w.weight for w in fam.weights)
    return "".join(f'@import url("./{weight_css_name(w)}");\n' for w in weights)
