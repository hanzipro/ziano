from fontTools.ttLib import TTFont


def cmap_codepoints(font_path: str) -> set[int]:
    return set(TTFont(font_path).getBestCmap().keys())


def coverage_report(cmap: set[int], target_chars: str) -> dict:
    targets = list(dict.fromkeys(target_chars))  # dedupe, keep order
    missing = [c for c in targets if ord(c) not in cmap]
    return {
        "total_glyphs": len(cmap),
        "target_total": len(targets),
        "target_covered": len(targets) - len(missing),
        "missing": missing,
    }
