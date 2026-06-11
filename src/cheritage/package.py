import json
from pathlib import Path

from .roster import FamilyConfig

# npm publishing identity. Packages publish as @hanzi.pro/webfonts-<id>.
# The GitHub repo (cheritage) deliberately does NOT appear in the package name.
PKG_SCOPE = "@hanzi.pro"
PKG_PREFIX = "webfonts-"
REPO_URL = "https://github.com/hanzi-pro/cheritage"  # TODO: confirm GitHub org slug
HOMEPAGE = "https://hanzi.pro"


def package_name(fam: FamilyConfig) -> str:
    return f"{PKG_SCOPE}/{PKG_PREFIX}{fam.id}"


def css_entry_name(fam: FamilyConfig) -> str:
    return "variable.css" if fam.format == "vf" else "index.css"


def package_json(fam: FamilyConfig, *, version: str) -> dict:
    entry = css_entry_name(fam)
    # static ships one css per weight (caught by the *.css glob) alongside index.css
    files = ["*.css", "files/", "LICENSE", "README.md"] if fam.format == "static" \
        else [entry, "files/", "LICENSE", "README.md"]
    return {
        "name": package_name(fam),
        "version": version,
        "description": (
            f"{fam.font_family} — 傳承字形 webfont subset of {fam.repo} "
            f"({fam.release_tag}), sliced by cheritage."
        ),
        "license": "OFL-1.1",
        "homepage": HOMEPAGE,
        "repository": {"type": "git", "url": f"git+{REPO_URL}.git"},
        "sideEffects": ["*.css"],
        "exports": {f"./{entry}": f"./{entry}", "./files/*": "./files/*"},
        "files": files,
        "keywords": ["webfont", "cjk", "traditional-chinese", "傳承字形", fam.style],
        # scoped packages are private by default — must opt into public publish
        "publishConfig": {"access": "public"},
    }


def render_readme(fam: FamilyConfig, *, version: str) -> str:
    entry = css_entry_name(fam)
    pkg = package_name(fam)
    return (
        f"# {pkg}\n\n"
        f"**{fam.font_family}** — 傳承字形 (heritage-glyph) Traditional-Chinese webfont, "
        f"sliced into `unicode-range` woff2 subsets from "
        f"[{fam.repo}](https://github.com/{fam.repo}) `{fam.release_tag}`.\n\n"
        "## Usage\n\n"
        "```css\n"
        f'@import url("https://cdn.jsdelivr.net/npm/{pkg}@{version}/{entry}");\n\n'
        f"body {{ font-family: \"{fam.font_family}\", serif; }}\n"
        "```\n\n"
        "The browser downloads only the slices your page actually uses. "
        "Uncovered codepoints fall through to the next font in your stack "
        "(by design — JP/KR/SC stay on system fonts, no tofu).\n\n"
        "## License\n\n"
        "SIL Open Font License 1.1 — see `LICENSE`. Font copyright remains with the "
        f"upstream authors of {fam.repo}.\n"
    )


def write_package_skeleton(
    fam: FamilyConfig, *, dest: str, version: str,
    css: str, license_text: str, readme: str | None = None,
    extra_css: dict[str, str] | None = None,
) -> Path:
    root = Path(dest) / fam.id
    (root / "files").mkdir(parents=True, exist_ok=True)
    (root / css_entry_name(fam)).write_text(css)
    for name, text in (extra_css or {}).items():
        (root / name).write_text(text)
    (root / "LICENSE").write_text(license_text)
    (root / "README.md").write_text(readme if readme is not None else render_readme(fam, version=version))
    (root / "package.json").write_text(
        json.dumps(package_json(fam, version=version), indent=2, ensure_ascii=False)
    )
    return root
