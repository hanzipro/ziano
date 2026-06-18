from fontTools.ttLib import TTFont


def cmap_codepoints(font_path: str) -> set[int]:
    # getBestCmap() returns None for a glyphless font (e.g. an empty emoji-slice woff2)
    return set((TTFont(font_path).getBestCmap() or {}).keys())


def coverage_report(cmap: set[int], target_chars: str) -> dict:
    targets = list(dict.fromkeys(target_chars))  # dedupe, keep order
    missing = [c for c in targets if ord(c) not in cmap]
    return {
        "total_glyphs": len(cmap),
        "target_total": len(targets),
        "target_covered": len(targets) - len(missing),
        "missing": missing,
    }
