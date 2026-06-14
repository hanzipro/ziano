import json
from pathlib import Path

from .cssgen import DEFAULT_MODE, DISPLAY_MODES, mode_css_name
from .roster import FamilyConfig

# npm publishing identity. Packages publish as @hanzi.pro/webfonts-<id>.
# The GitHub repo (ziano) deliberately does NOT appear in the package name.
PKG_SCOPE = "@hanzi.pro"
PKG_PREFIX = "webfonts-"
REPO_URL = "https://github.com/hanzipro/ziano"
HOMEPAGE = "https://hanzi.pro"

# Chinese classification keywords per roster style. serif (明朝體) is searched as
# both 明體 (TW) and 宋體 (CN); sans → 黑體; cursive (handwriting) → 楷體.
STYLE_KEYWORDS: dict[str, list[str]] = {
    "serif": ["明體", "宋體"],
    "sans": ["黑體"],
    "cursive": ["楷體"],
}


def package_name(fam: FamilyConfig) -> str:
    return f"{PKG_SCOPE}/{PKG_PREFIX}{fam.id}"


def css_entry_name(fam: FamilyConfig) -> str:
    # Default entry for every family: swap.css. No semantically-vague index.css —
    # the "default" role is carried by package.json main/exports below, not a name.
    return mode_css_name(DEFAULT_MODE)


def package_json(fam: FamilyConfig, *, version: str) -> dict:
    entry = css_entry_name(fam)  # swap.css
    # exports: bare specifier → swap; subpath per mode (./block, ./optional).
    exports: dict[str, str] = {".": f"./{entry}"}
    for mode in DISPLAY_MODES:
        exports[f"./{mode}"] = f"./{mode_css_name(mode)}"
    exports["./files/*"] = "./files/*"
    # files whitelist: the three top-level mode css, plus (static) their per-weight
    # subdirs; woff2 are mode-independent and shared from files/.
    mode_css = [mode_css_name(m) for m in DISPLAY_MODES]
    mode_dirs = [f"{m}/" for m in DISPLAY_MODES] if fam.format == "static" else []
    if fam.format == "static":
        for mode in DISPLAY_MODES:
            exports[f"./{mode}/*"] = f"./{mode}/*"
    return {
        "name": package_name(fam),
        "version": version,
        "description": (
            f"{fam.font_family} — 傳承字形 webfont subset of {fam.repo} "
            f"({fam.release_tag}), sliced by ziano."
        ),
        "license": "OFL-1.1",
        "homepage": HOMEPAGE,
        "repository": {"type": "git", "url": f"git+{REPO_URL}.git"},
        # main/style so bundlers and jsDelivr's bare-package URL resolve to swap.
        "main": entry,
        "style": entry,
        "sideEffects": ["*.css"],
        "exports": exports,
        "files": [*mode_css, *mode_dirs, "files/", "LICENSE", "README.md"],
        "keywords": [
            "webfont", "cjk", "traditional-chinese", "傳承字形", fam.style,
            *STYLE_KEYWORDS.get(fam.style, []),
        ],
        # scoped packages are private by default — must opt into public publish
        "publishConfig": {"access": "public"},
    }


def render_readme(fam: FamilyConfig, *, version: str) -> str:
    entry = css_entry_name(fam)
    pkg = package_name(fam)
    base = f"https://cdn.jsdelivr.net/npm/{pkg}@{version}"
    css_url = f"{base}/{entry}"
    fallback = "sans-serif" if fam.style == "sans" else "serif"
    # static families also expose one css per weight under <mode>/<weight>.css —
    # spell that out so consumers can load just the weights they use.
    weights = sorted(w.weight for w in fam.weights)
    per_weight = ""
    if fam.format == "static" and weights:
        eg = 400 if 400 in weights else weights[0]
        weight_list = " ".join(f"`{w}`" for w in weights)
        per_weight = (
            "\n### Single weight\n\n"
            f"`{entry}` (and `block.css` / `optional.css`) declares **every** weight; "
            "the browser still only downloads the slices and weights your page uses. "
            "But if you want a smaller stylesheet, each mode also ships one file per "
            "weight under a matching subfolder — `swap/<weight>.css`, "
            "`block/<weight>.css`, `optional/<weight>.css`:\n\n"
            "```html\n"
            f'<link rel="stylesheet" href="{base}/swap/{eg}.css" />\n'
            "```\n\n"
            f"Available weights: {weight_list}\n"
        )
    return (
        f"# {pkg}\n\n"
        f"**{fam.font_family}** — 傳承字形 (heritage-glyph) Traditional-Chinese webfont, "
        f"sliced into `unicode-range` woff2 subsets from "
        f"[{fam.repo}](https://github.com/{fam.repo}) `{fam.release_tag}`.\n\n"
        "## Usage\n\n"
        "Drop these in your `<head>` — `preconnect` warms the CDN connection so the "
        "stylesheet (and the woff2 slices it pulls) arrive sooner:\n\n"
        "```html\n"
        '<link rel="preconnect" href="https://cdn.jsdelivr.net" crossorigin />\n'
        f'<link rel="stylesheet" href="{css_url}" />\n'
        "```\n\n"
        "Then use the family in CSS:\n\n"
        "```css\n"
        f'body {{ font-family: "{fam.font_family}", {fallback}; }}\n'
        "```\n\n"
        "The browser downloads only the slices your page actually uses; "
        "codepoints outside the subset fall through to the next font in your stack.\n\n"
        "## font-display\n\n"
        f"`{entry}` is the default (`font-display: swap` — show text immediately, "
        "swap the glyph in when it arrives). Two alternates ship alongside it; just "
        "point the stylesheet at a different file:\n\n"
        "```html\n"
        f'<!-- headlines / logotypes: never flash the wrong fallback glyph -->\n'
        f'<link rel="stylesheet" href="{base}/block.css" />\n\n'
        f'<!-- Core-Web-Vitals pages: zero layout shift (may skip the first visit) -->\n'
        f'<link rel="stylesheet" href="{base}/optional.css" />\n'
        "```\n\n"
        "| file | `font-display` | use when |\n"
        "| --- | --- | --- |\n"
        f"| `{entry}` | `swap` | body / content — show text now, swap glyph in (FOUT) |\n"
        "| `block.css` | `block` | headlines / logotypes — brief invisible text, "
        "never the wrong glyph |\n"
        "| `optional.css` | `optional` | perf-critical — no layout shift; slice may "
        "sit out the first visit |\n"
        f"{per_weight}\n"
        "## License\n\n"
        "SIL Open Font License 1.1 — see `LICENSE`. Font copyright remains with the "
        f"upstream authors of {fam.repo}.\n"
    )


def write_package_skeleton(
    fam: FamilyConfig, *, dest: str, version: str,
    css_files: dict[str, str], license_text: str, readme: str | None = None,
) -> Path:
    root = Path(dest) / fam.id
    (root / "files").mkdir(parents=True, exist_ok=True)
    # css_files maps relative path → content; keys may be nested (swap/300.css).
    for rel, text in css_files.items():
        path = root / rel
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text)
    (root / "LICENSE").write_text(license_text)
    (root / "README.md").write_text(readme if readme is not None else render_readme(fam, version=version))
    (root / "package.json").write_text(
        json.dumps(package_json(fam, version=version), indent=2, ensure_ascii=False)
    )
    return root
