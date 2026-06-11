from fontTools.subset import Options, Subsetter
from fontTools.ttLib import TTFont

from .slices import Slice


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
    opts.layout_features = ["*"]  # keep GSUB/GPOS (ligatures, locl, kerning)
    if not keep_variations:
        opts.drop_tables += ["fvar", "gvar", "avar", "STAT"]
    subs = Subsetter(options=opts)
    subs.populate(unicodes=sorted(sl.codepoints()))
    subs.subset(font)
    # opts.flavor is only honored by fontTools' own save_font(); since we call
    # font.save() directly we must set the flavor on the font object ourselves.
    font.flavor = opts.flavor
    font.save(out_path)
    font.close()
