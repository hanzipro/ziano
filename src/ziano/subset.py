from fontTools.subset import Options, Subsetter
from fontTools.ttLib import TTFont, newTable

from .slices import Slice

# All four gasp behaviours on, one range covering every size — the same value
# Noto CJK ships (0x000F). Our glyf builds carry no per-glyph hinting, so this is
# what tells Windows GDI/DirectWrite to grayscale/ClearType-smooth at all sizes
# instead of falling back to aliased B&W; macOS/Chrome ignore it. glyf-only —
# CFF families (genki, lxgw) already carry their own CFF hints.
_GASP_SMOOTH_ALL = 0x000F


def _ensure_gasp(font: TTFont) -> None:
    if "glyf" not in font or "gasp" in font:
        return
    gasp = newTable("gasp")
    gasp.version = 1
    gasp.gaspRange = {0xFFFF: _GASP_SMOOTH_ALL}
    font["gasp"] = gasp


def subset_to_woff2(src_path: str, sl: Slice, out_path: str, *, keep_variations: bool) -> None:
    font = TTFont(src_path)
    opts = Options()
    opts.flavor = "woff2"
    opts.retain_gids = False
    opts.desubroutinize = True  # smaller CFF, harmless for glyf
    opts.recalc_bounds = True
    opts.notdef_outline = True  # keep .notdef shape
    opts.name_IDs = ["*"]  # keep name table (family/RFN notices)
    opts.name_legacy = True
    # Default is English-only, which would drop `尙古明體丹` — the name these
    # fonts are actually known by, and the one `naming.py` writes into the zh
    # slots. Costs ~96 bytes/slice (0.9%) on Shanggu; worth it for a file that
    # is supposed to identify itself correctly.
    opts.name_languages = ["*"]
    opts.layout_features = ["*"]  # keep GSUB/GPOS (ligatures, locl, kerning)
    if not keep_variations:
        opts.drop_tables += ["fvar", "gvar", "avar", "STAT"]
    subs = Subsetter(options=opts)
    subs.populate(unicodes=sorted(sl.codepoints()))
    subs.subset(font)
    _ensure_gasp(font)  # glyf-only Windows smoothing safety net (per-slice file)
    # opts.flavor is only honored by fontTools' own save_font(); since we call
    # font.save() directly we must set the flavor on the font object ourselves.
    font.flavor = opts.flavor
    font.save(out_path)
    font.close()
