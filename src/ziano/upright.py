"""Prepare a base font before slicing: upright `：；`, and shared line metrics.

UTR50 classifies U+FF1A `：` and U+FF1B `；` as **Tr** — "rotate 90° by default,
*unless* the font's `vert` feature substitutes them, in which case render the
substitute upright". Firefox implements that faithfully; Chrome and Safari are
lax and leave them upright whether or not a substitution exists. TC/MOE
convention wants them upright, and most of our upstreams simply have no rule for
them — so on Firefox they lie on their side.

The fix is a **sentinel (identity) substitution**: map the glyph to *itself*
under `vert`/`vrt2`. Visually it is a no-op — the substitute is the same glyph —
but it flips Firefox out of the Tr-default rotate branch. Chrome and Safari are
unaffected (measured: identical ink before and after). Same trick as
diantenjeom's `pin_locale._add_upright_self_substs`.

Fonts that **already** map these codepoints are left alone: Klee One sends `：`
to a genuinely rotated JP form and LXGW WenKai SC to a re-centred one. That is
the type designer's convention, not an oversight.

Must run on the base font *before* slicing — `：` and `；` usually land in
different `unicode-range` slices, and every slice that contains one needs the
rule. The substitution survives `subset.py`'s options unchanged (verified).
"""

from pathlib import Path

from fontTools.ttLib import TTFont

from . import metrics, naming

UPRIGHT_CODEPOINTS = (0xFF1A, 0xFF1B)  # ：；
VERT_FEATURE_TAGS = ("vert", "vrt2")


def _lookup_indices_by_tag(gsub) -> dict[str, list[int]]:
    """Lookup indices each vertical feature points at, de-duplicated, order kept.

    A feature tag gets one FeatureRecord per script (Shanggu has seven `vert`
    records), all pointing at the same lookups — hence the de-dup.
    """
    by_tag: dict[str, list[int]] = {}
    for rec in gsub.FeatureList.FeatureRecord:
        if rec.FeatureTag not in VERT_FEATURE_TAGS:
            continue
        indices = by_tag.setdefault(rec.FeatureTag, [])
        indices.extend(i for i in rec.Feature.LookupListIndex if i not in indices)
    return by_tag


def _single_subst_subtables(gsub, lookup_indices: list[int]):
    """The SingleSubst subtables reachable from those lookups, in order.

    LookupType 7 (Extension) wraps the real subtable; unwrap it so an extension-
    packed font isn't silently skipped.
    """
    for index in lookup_indices:
        for subtable in gsub.LookupList.Lookup[index].SubTable:
            subtable = getattr(subtable, "ExtSubTable", subtable)
            if getattr(subtable, "mapping", None) is not None:
                yield subtable


def install(font: TTFont) -> list[str]:
    """Add the sentinel substitutions in place. Returns what was touched, as
    `"<tag>:<glyph>"` strings — empty when the font already handles them, lacks
    the codepoints, or has no vertical feature to hang them on."""
    if "GSUB" not in font or font["GSUB"].table.FeatureList is None:
        return []
    gsub = font["GSUB"].table
    by_tag = _lookup_indices_by_tag(gsub)
    if not by_tag:
        return []

    cmap = font.getBestCmap()
    touched: list[str] = []
    for codepoint in UPRIGHT_CODEPOINTS:
        glyph = cmap.get(codepoint)
        if glyph is None:
            continue
        for tag, indices in by_tag.items():
            subtables = list(_single_subst_subtables(gsub, indices))
            if not subtables:
                continue
            # Already mapped — by the designer, or by our own pass for a feature
            # that shares this lookup (`vrt2` usually reuses `vert`'s). Leave it.
            if any(glyph in st.mapping for st in subtables):
                continue
            subtables[0].mapping[glyph] = glyph
            # Format 2 is an explicit glyph→glyph list. Format 1 stores a delta,
            # and an identity delta of 0 is the kind of thing a tool chain feels
            # entitled to drop.
            subtables[0].Format = 2
            touched.append(f"{tag}:{glyph}")
    return touched


# Bumped whenever `prepare()` changes what it writes: the cache keys on the
# source file's mtime, which a change in *our* code doesn't touch.
_REVISION = 3


def prepare(src: str | Path, cache_dir: str | Path, *, family: str = "",
            family_zh: str = "", family_zh_hans: str = "") -> Path:
    """Path to a copy of `src` ready to slice: sentinel substitutions installed,
    line metrics normalised (`metrics.py`), `name` table rewritten
    (`naming.py`, only when `family` is given).

    All three edits ride the same read/write — the metrics change alone would
    make a copy of every base font anyway, so there is no cheaper ordering. The
    copy is cached and reused while it is newer than `src`.
    """
    src = Path(src)
    cache_dir = Path(cache_dir)
    out = cache_dir / f"{src.stem}.prepared.r{_REVISION}{src.suffix}"
    if out.exists() and out.stat().st_mtime >= src.stat().st_mtime:
        return out

    font = TTFont(src, lazy=True)
    install(font)
    metrics.normalise(font)
    if family:
        naming.rename(font, family, family_zh, family_zh_hans)
    cache_dir.mkdir(parents=True, exist_ok=True)
    font.save(out)
    font.close()
    return out
