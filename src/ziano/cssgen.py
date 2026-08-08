from . import metrics
from .roster import FamilyConfig
from .slices import Slice

# font-display modes we publish per family. swap is the default entry; block is
# for headline/logotype use (never flash the wrong fallback glyph); optional is
# for CWV/CLS-sensitive pages (huge CJK slices may arrive late → no layout shift).
DISPLAY_MODES = ("swap", "block", "optional")
DEFAULT_MODE = "swap"


def woff2_name(fam: FamilyConfig, slice_index: int, weight: int | None = None) -> str:
    if fam.format == "vf" or weight is None:
        return f"{fam.id}.{slice_index}.woff2"
    return f"{fam.id}.{weight}.{slice_index}.woff2"


def mode_css_name(mode: str) -> str:
    """Top-level entry for a display mode, e.g. swap.css (all weights inlined)."""
    return f"{mode}.css"


def weight_css_path(mode: str, weight: int) -> str:
    """Per-weight entry for a display mode, e.g. swap/300.css (one weight only)."""
    return f"{mode}/{weight}.css"


def _src(fam: FamilyConfig, slice_index: int, weight: int | None, files_base: str) -> str:
    # local() names first → a browser with the system font downloads nothing.
    parts = [f'local("{n}")' for n in fam.local_names]
    parts.append(f"url({files_base}/{woff2_name(fam, slice_index, weight)}) format('woff2')")
    return "src: " + ", ".join(parts) + ";"


# The same normalised line metrics the fonts themselves now carry (metrics.py),
# restated as @font-face descriptors so the stylesheet says out loud what we did
# — and so the pairing demo can A/B it by dropping these three lines.
#
# They are NOT the fix on their own: Safari reads `hhea` for the vertical central
# baseline and ignores these descriptors there, which is why the numbers are
# written into the files. See docs/vertical-baseline-offset.md.
METRICS_OVERRIDE = (
    f"ascent-override: {metrics.ASCENT / 10:g}%;",
    f"descent-override: {-metrics.DESCENT / 10:g}%;",
    "line-gap-override: 0%;",
)


def _face(fam: FamilyConfig, s: Slice, weight: int | None, display: str, files_base: str,
          family: str = "") -> str:
    # readable, NOT minified: this CSS is ~all unicode-range payload, so stripping
    # whitespace saves ~2.7% raw and 0% after gzip/brotli (which the CDN serves) —
    # not worth the loss of diff/inspect-ability. Let the transport compress it.
    if fam.format == "vf":
        weight_decl = f"font-weight: {fam.weight_min} {fam.weight_max};"
    else:
        weight_decl = f"font-weight: {weight};"
    metric_lines = "".join(f"  {line}\n" for line in METRICS_OVERRIDE)
    return (
        "@font-face {\n"
        f"  font-family: '{family or fam.font_family}';\n"
        "  font-style: normal;\n"
        f"  {weight_decl}\n"
        f"  font-display: {display};\n"
        f"{metric_lines}"
        f"  {_src(fam, s.index, weight, files_base)}\n"
        f"  unicode-range: {s.unicode_range};\n"
        "}\n"
    )


def generate_css(
    fam: FamilyConfig, slices: list[Slice],
    weight: int | None = None, display: str = DEFAULT_MODE,
    files_base: str = "./files", family: str = "",
) -> str:
    """@font-face rules for one weight (or the vf range) at one display mode.
    files_base is the url() prefix to the woff2 dir — '../files' for per-weight
    files that sit one directory deep (swap/300.css). `family` overrides the
    declared font-family (the `dan/` stylesheets)."""
    return "\n".join(_face(fam, s, weight, display, files_base, family) for s in slices)


def generate_aggregate_css(
    fam: FamilyConfig, slices: list[Slice],
    weights: list[int], display: str = DEFAULT_MODE,
    files_base: str = "./files", family: str = "",
) -> str:
    """Static top-level entry: every weight's @font-face inlined (no @import, so
    no serialised request waterfall). woff2 stays lazy via unicode-range."""
    return "\n".join(
        _face(fam, s, w, display, files_base, family)
        for w in sorted(weights) for s in slices
    )
