# cheritage Core Pipeline Implementation Plan (Plan 1 of N)

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build the font-agnostic slicing pipeline and use it to produce two installable, `npm pack`-able packages — `@cheritage/shanggu-serif` and `@cheritage/shanggu-sans` — that serve heritage-glyph (傳承字形) Traditional-Chinese webfonts as `unicode-range` woff2 subsets.

**Architecture:** A Python (fonttools) build tool reads a `roster.toml`, downloads a pinned upstream OFL font release, subsets it into ~100 `unicode-range` woff2 slices using a snapshot of Google Fonts' partition table, generates the `@font-face` CSS, and assembles a static npm package directory (CSS + `files/*.woff2` + OFL + package.json). The published packages contain **no JavaScript** — they are pure CSS+woff2, served free via jsDelivr.

**Tech Stack:** Python 3.12, `uv` (env/deps), `fonttools[woff]` (subsetting + brotli/woff2 + cmap), `pytest`. Output packages are plain npm packages (no build-time JS). Rationale for Python over TS: the entire core is fonttools (subsetting, variable-axis retention, cmap coverage analysis) which is a Python library; a Node tool would only shell out to it. The user's han.css is TS, but cheritage is a separate font-build repo and its *products* need no JS runtime.

**Spec:** `docs/superpowers/specs/2026-06-12-cheritage-design.md`

---

## File Structure

```
cheritage/
  pyproject.toml                 # uv project + deps + pytest config
  roster.toml                    # roster config (data, not code)
  src/cheritage/
    __init__.py
    roster.py                    # load+validate roster.toml → FamilyConfig dataclass
    slices.py                    # snapshot Google css2 → list[Slice]; load/refresh
    acquire.py                   # download + sha256-verify pinned release asset; unzip
    subset.py                    # FamilyConfig + Slice → woff2 bytes (fontTools.subset)
    cssgen.py                    # FamilyConfig + [Slice] → @font-face CSS string
    package.py                   # assemble npm package dir (css, files/, LICENSE, package.json, README)
    build.py                     # orchestrate one family end-to-end; CLI `python -m cheritage.build <id>`
    coverage.py                  # cmap diff vs common-hard TC charset (spec §8 / task #6)
  data/
    slices.sans.json             # snapshot of Noto Sans TC unicode-ranges
    slices.serif.json            # snapshot of Noto Serif TC unicode-ranges
    common-hard-tc.txt           # curated common-but-hard TC chars for coverage test
  tests/
    fixtures/
      noto-sans-tc.css2.txt      # captured Google css2 response (for slices parser test)
    test_roster.py
    test_slices.py
    test_cssgen.py
    test_package.py
    test_acquire.py              # integration (network, cached)
    test_subset.py               # integration (uses cached Shanggu VF)
    test_build.py                # integration (end-to-end)
    test_coverage.py
  .cache/                        # gitignored: downloaded fonts
  dist/                          # gitignored: built packages
```

Pure-data transforms (`roster`, `slices`, `cssgen`, `package`) are unit-tested with fast TDD. Binary/network steps (`acquire`, `subset`, `build`) are integration tests gated on a session-cached real font download.

---

## Task 1: Project scaffold

**Files:**
- Create: `pyproject.toml`
- Create: `src/cheritage/__init__.py`
- Create: `tests/__init__.py`
- Modify: `.gitignore`

- [ ] **Step 1: Write `pyproject.toml`**

```toml
[project]
name = "cheritage"
version = "0.0.0"
description = "傳承字形 webfont CDN build pipeline"
requires-python = ">=3.12"
dependencies = ["fonttools[woff]>=4.50"]

[dependency-groups]
dev = ["pytest>=8"]

[build-system]
requires = ["hatchling"]
build-backend = "hatchling.build"

[tool.hatch.build.targets.wheel]
packages = ["src/cheritage"]

[tool.pytest.ini_options]
pythonpath = ["src"]
markers = ["integration: needs network / real fonts (deselect with -m 'not integration')"]
```

- [ ] **Step 2: Create empty package files**

```bash
mkdir -p src/cheritage tests data
touch src/cheritage/__init__.py tests/__init__.py
```

- [ ] **Step 3: Extend `.gitignore`**

Append to `.gitignore`:

```
.cache/
dist/
.venv/
__pycache__/
*.pyc
.pytest_cache/
```

- [ ] **Step 4: Verify the env builds and pytest runs**

Run: `uv sync && uv run pytest -q`
Expected: `no tests ran` (exit 0/5) — environment resolves, fonttools installed.

- [ ] **Step 5: Commit**

```bash
git add pyproject.toml src/cheritage/__init__.py tests/__init__.py .gitignore
git commit -m "chore: scaffold cheritage python build tool (uv + fonttools + pytest)"
```

---

## Task 2: Roster config + loader

**Files:**
- Create: `roster.toml`
- Create: `src/cheritage/roster.py`
- Test: `tests/test_roster.py`

- [ ] **Step 1: Write `roster.toml`** (Shanggu only for Plan 1)

```toml
# Each [[family]] is one packaged face. Data only — no code.
# format: "vf" (variable, one file spans all weights) | "static" (per-weight)
# style:  "serif" | "sans"  → selects the slice table (data/slices.<style>.json)

[[family]]
id            = "shanggu-serif"
font_family   = "Shanggu Serif"          # keep upstream name (spec §7); RFN-checked
style         = "serif"
format        = "vf"
weight_min    = 100
weight_max    = 900
repo          = "GuiWonder/Shanggu"
release_tag   = "v1.028"
# asset + sha256 + the path of the TTF inside the asset are filled in Task 5/8
asset         = "ShangguSerifTC.ttf"
asset_sha256  = "PLACEHOLDER_FILLED_IN_TASK_8"
license_path  = "OFL.txt"

[[family]]
id            = "shanggu-sans"
font_family   = "Shanggu Sans"
style         = "sans"
format        = "vf"
weight_min    = 100
weight_max    = 900
repo          = "GuiWonder/Shanggu"
release_tag   = "v1.028"
asset         = "ShangguSansTC.ttf"
asset_sha256  = "PLACEHOLDER_FILLED_IN_TASK_8"
license_path  = "OFL.txt"
```

> Note: exact upstream asset filenames + sha256 are confirmed during Task 8 (first real download). Treat the values above as placeholders to be corrected against the actual `v1.028` release.

- [ ] **Step 2: Write the failing test**

```python
# tests/test_roster.py
from cheritage.roster import load_roster, FamilyConfig

def test_load_roster_returns_typed_families():
    families = load_roster("roster.toml")
    by_id = {f.id: f for f in families}
    assert set(by_id) == {"shanggu-serif", "shanggu-sans"}
    serif = by_id["shanggu-serif"]
    assert isinstance(serif, FamilyConfig)
    assert serif.font_family == "Shanggu Serif"
    assert serif.style == "serif"
    assert serif.format == "vf"
    assert serif.weight_min == 100 and serif.weight_max == 900
    assert serif.repo == "GuiWonder/Shanggu"

def test_load_roster_rejects_unknown_style(tmp_path):
    bad = tmp_path / "bad.toml"
    bad.write_text('[[family]]\nid="x"\nfont_family="X"\nstyle="script"\n'
                   'format="vf"\nrepo="a/b"\nrelease_tag="v1"\nasset="x.ttf"\n'
                   'asset_sha256="0"\nlicense_path="OFL.txt"\n')
    import pytest
    with pytest.raises(ValueError, match="style"):
        load_roster(str(bad))
```

- [ ] **Step 3: Run test to verify it fails**

Run: `uv run pytest tests/test_roster.py -q`
Expected: FAIL — `ModuleNotFoundError: cheritage.roster`.

- [ ] **Step 4: Implement `src/cheritage/roster.py`**

```python
import tomllib
from dataclasses import dataclass

_STYLES = {"serif", "sans"}
_FORMATS = {"vf", "static"}

@dataclass(frozen=True)
class FamilyConfig:
    id: str
    font_family: str
    style: str
    format: str
    repo: str
    release_tag: str
    asset: str
    asset_sha256: str
    license_path: str
    weight_min: int = 400
    weight_max: int = 400

def load_roster(path: str) -> list[FamilyConfig]:
    with open(path, "rb") as fh:
        data = tomllib.load(fh)
    families = []
    for raw in data.get("family", []):
        if raw.get("style") not in _STYLES:
            raise ValueError(f"invalid style {raw.get('style')!r} in {raw.get('id')!r}")
        if raw.get("format") not in _FORMATS:
            raise ValueError(f"invalid format {raw.get('format')!r} in {raw.get('id')!r}")
        families.append(FamilyConfig(**raw))
    return families
```

- [ ] **Step 5: Run test to verify it passes**

Run: `uv run pytest tests/test_roster.py -q`
Expected: PASS (2 passed).

- [ ] **Step 6: Commit**

```bash
git add roster.toml src/cheritage/roster.py tests/test_roster.py
git commit -m "feat(roster): typed roster.toml loader with style/format validation"
```

---

## Task 3: Slice table — snapshot Google's unicode-ranges

Resolves spec §9.5 as **snapshot** (committed data file, refreshable). One table per style, captured from the matching Noto family.

**Files:**
- Create: `tests/fixtures/noto-sans-tc.css2.txt`
- Create: `src/cheritage/slices.py`
- Create: `data/slices.sans.json`, `data/slices.serif.json` (generated in Step 6)
- Test: `tests/test_slices.py`

- [ ] **Step 1: Capture the css2 fixture**

Run:
```bash
UA='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120 Safari/537.36'
curl -s -H "User-Agent: $UA" \
  'https://fonts.googleapis.com/css2?family=Noto+Sans+TC:wght@100..900&display=swap' \
  -o tests/fixtures/noto-sans-tc.css2.txt
grep -c font-face tests/fixtures/noto-sans-tc.css2.txt   # expect ~105
```

- [ ] **Step 2: Write the failing test**

```python
# tests/test_slices.py
from pathlib import Path
from cheritage.slices import parse_css2_unicode_ranges, Slice

def test_parse_css2_yields_one_slice_per_font_face():
    css = Path("tests/fixtures/noto-sans-tc.css2.txt").read_text()
    slices = parse_css2_unicode_ranges(css)
    assert 100 <= len(slices) <= 130          # ~105 blocks
    assert all(isinstance(s, Slice) for s in slices)
    # each slice has an index and a non-empty unicode-range string
    assert slices[0].index == 0
    assert "U+" in slices[0].unicode_range
    # ranges must be valid CSS unicode-range tokens
    for s in slices:
        for tok in s.unicode_range.split(","):
            assert tok.strip().startswith("U+")

def test_slice_codepoints_expands_ranges():
    s = Slice(index=0, unicode_range="U+41-43, U+4e00")
    assert s.codepoints() == {0x41, 0x42, 0x43, 0x4e00}
```

- [ ] **Step 3: Run test to verify it fails**

Run: `uv run pytest tests/test_slices.py -q`
Expected: FAIL — `ModuleNotFoundError: cheritage.slices`.

- [ ] **Step 4: Implement `src/cheritage/slices.py`**

```python
import json
import re
from dataclasses import dataclass

_UR_RE = re.compile(r"unicode-range:\s*([^;]+);", re.IGNORECASE)

@dataclass(frozen=True)
class Slice:
    index: int
    unicode_range: str   # raw CSS token list, e.g. "U+41-43, U+4e00"

    def codepoints(self) -> set[int]:
        cps: set[int] = set()
        for tok in self.unicode_range.split(","):
            tok = tok.strip().removeprefix("U+").removeprefix("u+")
            if "-" in tok:
                lo, hi = tok.split("-")
                cps.update(range(int(lo, 16), int(hi, 16) + 1))
            elif tok:
                cps.add(int(tok, 16))
        return cps

def parse_css2_unicode_ranges(css: str) -> list[Slice]:
    return [Slice(index=i, unicode_range=m.group(1).strip())
            for i, m in enumerate(_UR_RE.finditer(css))]

def save_slices(slices: list[Slice], path: str) -> None:
    with open(path, "w") as fh:
        json.dump([{"index": s.index, "unicode_range": s.unicode_range}
                   for s in slices], fh, ensure_ascii=False, indent=0)

def load_slices(path: str) -> list[Slice]:
    with open(path) as fh:
        return [Slice(**row) for row in json.load(fh)]
```

- [ ] **Step 5: Run test to verify it passes**

Run: `uv run pytest tests/test_slices.py -q`
Expected: PASS (2 passed).

- [ ] **Step 6: Generate the committed data tables**

Run:
```bash
UA='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120 Safari/537.36'
curl -s -H "User-Agent: $UA" 'https://fonts.googleapis.com/css2?family=Noto+Serif+TC:wght@200..900&display=swap' -o /tmp/noto-serif-tc.css2.txt
uv run python -c "from cheritage.slices import parse_css2_unicode_ranges,save_slices; from pathlib import Path; save_slices(parse_css2_unicode_ranges(Path('tests/fixtures/noto-sans-tc.css2.txt').read_text()),'data/slices.sans.json'); save_slices(parse_css2_unicode_ranges(Path('/tmp/noto-serif-tc.css2.txt').read_text()),'data/slices.serif.json')"
wc -l data/slices.sans.json data/slices.serif.json
```

- [ ] **Step 7: Commit**

```bash
git add tests/fixtures/noto-sans-tc.css2.txt src/cheritage/slices.py tests/test_slices.py data/slices.sans.json data/slices.serif.json
git commit -m "feat(slices): snapshot Google Fonts unicode-range tables (sans+serif)"
```

---

## Task 4: CSS generator

**Files:**
- Create: `src/cheritage/cssgen.py`
- Test: `tests/test_cssgen.py`

- [ ] **Step 1: Write the failing test**

```python
# tests/test_cssgen.py
from cheritage.roster import FamilyConfig
from cheritage.slices import Slice
from cheritage.cssgen import generate_css

VF = FamilyConfig(id="shanggu-serif", font_family="Shanggu Serif", style="serif",
                  format="vf", repo="GuiWonder/Shanggu", release_tag="v1.028",
                  asset="x.ttf", asset_sha256="0", license_path="OFL.txt",
                  weight_min=100, weight_max=900)

def test_vf_font_face_has_weight_range_and_relative_src():
    slices = [Slice(0, "U+4e00-4e10"), Slice(1, "U+20")]
    css = generate_css(VF, slices)
    assert css.count("@font-face") == 2
    assert "font-weight: 100 900;" in css
    assert "font-display: swap;" in css
    assert "font-family: 'Shanggu Serif';" in css
    assert "src: url(./files/shanggu-serif.0.woff2) format('woff2');" in css
    assert "unicode-range: U+4e00-4e10;" in css

def test_static_font_face_uses_single_weight_and_weight_suffix():
    static = FamilyConfig(id="genyo-min", font_family="GenYoMin", style="serif",
                          format="static", repo="ButTaiwan/genyo-font", release_tag="v2.100",
                          asset="x.ttf", asset_sha256="0", license_path="OFL.txt",
                          weight_min=400, weight_max=400)
    css = generate_css(static, [Slice(0, "U+20")], weight=700)
    assert "font-weight: 700;" in css
    assert "src: url(./files/genyo-min.700.0.woff2) format('woff2');" in css
```

- [ ] **Step 2: Run test to verify it fails**

Run: `uv run pytest tests/test_cssgen.py -q`
Expected: FAIL — `ModuleNotFoundError: cheritage.cssgen`.

- [ ] **Step 3: Implement `src/cheritage/cssgen.py`**

```python
from .roster import FamilyConfig
from .slices import Slice

def woff2_name(fam: FamilyConfig, slice_index: int, weight: int | None = None) -> str:
    if fam.format == "vf" or weight is None:
        return f"{fam.id}.{slice_index}.woff2"
    return f"{fam.id}.{weight}.{slice_index}.woff2"

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
        f"  src: url(./files/{woff2_name(fam, s.index, weight)}) format('woff2');\n"
        f"  unicode-range: {s.unicode_range};\n"
        "}\n"
    )

def generate_css(fam: FamilyConfig, slices: list[Slice], weight: int | None = None) -> str:
    return "\n".join(_face(fam, s, weight) for s in slices)
```

- [ ] **Step 4: Run test to verify it passes**

Run: `uv run pytest tests/test_cssgen.py -q`
Expected: PASS (2 passed).

- [ ] **Step 5: Commit**

```bash
git add src/cheritage/cssgen.py tests/test_cssgen.py
git commit -m "feat(cssgen): @font-face generator for vf and static slices"
```

---

## Task 5: Acquire — download + verify pinned release asset

**Files:**
- Create: `src/cheritage/acquire.py`
- Test: `tests/test_acquire.py`

- [ ] **Step 1: Write the failing test (unit part — checksum)**

```python
# tests/test_acquire.py
import hashlib, pytest
from cheritage.acquire import sha256_file, release_asset_url

def test_release_asset_url_is_github_releases_download():
    url = release_asset_url("GuiWonder/Shanggu", "v1.028", "ShangguSerifTC.ttf")
    assert url == ("https://github.com/GuiWonder/Shanggu/releases/download/"
                   "v1.028/ShangguSerifTC.ttf")

def test_sha256_file(tmp_path):
    p = tmp_path / "f.bin"
    p.write_bytes(b"hello")
    assert sha256_file(str(p)) == hashlib.sha256(b"hello").hexdigest()
```

- [ ] **Step 2: Run test to verify it fails**

Run: `uv run pytest tests/test_acquire.py -q`
Expected: FAIL — `ModuleNotFoundError: cheritage.acquire`.

- [ ] **Step 3: Implement `src/cheritage/acquire.py`**

```python
import hashlib
import os
import urllib.request
from pathlib import Path

CACHE = Path(".cache")

def release_asset_url(repo: str, tag: str, asset: str) -> str:
    return f"https://github.com/{repo}/releases/download/{tag}/{asset}"

def sha256_file(path: str) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()

def download(repo: str, tag: str, asset: str, *, expected_sha256: str | None = None) -> Path:
    CACHE.mkdir(exist_ok=True)
    dest = CACHE / f"{repo.replace('/', '__')}__{tag}__{asset}"
    if not dest.exists():
        url = release_asset_url(repo, tag, asset)
        req = urllib.request.Request(url, headers={"User-Agent": "cheritage-build"})
        with urllib.request.urlopen(req) as resp, open(dest, "wb") as out:
            while chunk := resp.read(1 << 20):
                out.write(chunk)
    if expected_sha256 and expected_sha256 not in ("0", "", "PLACEHOLDER_FILLED_IN_TASK_8"):
        actual = sha256_file(str(dest))
        if actual != expected_sha256:
            os.remove(dest)
            raise ValueError(f"sha256 mismatch for {asset}: got {actual}")
    return dest
```

- [ ] **Step 4: Run test to verify it passes**

Run: `uv run pytest tests/test_acquire.py -q`
Expected: PASS (2 passed).

- [ ] **Step 5: Add an integration smoke test (network, cached)**

Append to `tests/test_acquire.py`:

```python
@pytest.mark.integration
def test_download_shanggu_serif_is_a_real_font():
    from fontTools.ttLib import TTFont
    from cheritage.acquire import download
    # NOTE: correct asset name confirmed in Task 8; update if release differs.
    p = download("GuiWonder/Shanggu", "v1.028", "ShangguSerifTC.ttf")
    assert p.stat().st_size > 1_000_000
    font = TTFont(str(p))
    assert "fvar" in font  # it is a variable font
```

- [ ] **Step 6: Run integration test (and discover the real asset name if it 404s)**

Run: `uv run pytest tests/test_acquire.py -q -m integration`
Expected: PASS. **If it 404s**, list the real asset names with
`gh api repos/GuiWonder/Shanggu/releases/tags/v1.028 --jq '.assets[].name'`,
fix `asset` in `roster.toml` + the test, and re-run. Record the working name.

- [ ] **Step 7: Commit**

```bash
git add src/cheritage/acquire.py tests/test_acquire.py roster.toml
git commit -m "feat(acquire): pinned GitHub-release download with sha256 verification"
```

---

## Task 6: Subset — produce woff2 slices (the core)

**Files:**
- Create: `src/cheritage/subset.py`
- Test: `tests/test_subset.py`

- [ ] **Step 1: Write the failing integration test**

```python
# tests/test_subset.py
import pytest
from fontTools.ttLib import TTFont
from cheritage.acquire import download
from cheritage.slices import Slice
from cheritage.subset import subset_to_woff2

@pytest.mark.integration
def test_subset_vf_slice_keeps_axes_and_is_woff2(tmp_path):
    src = download("GuiWonder/Shanggu", "v1.028", "ShangguSerifTC.ttf")
    s = Slice(index=0, unicode_range="U+4e00-4e2f")   # a block of common Han
    out = tmp_path / "slice0.woff2"
    subset_to_woff2(str(src), s, str(out), keep_variations=True)
    data = out.read_bytes()
    assert data[:4] == b"wOF2"                         # woff2 magic
    font = TTFont(str(out))
    assert font.flavor == "woff2"
    assert "fvar" in font                              # variable axes retained
    cmap = font.getBestCmap()
    assert 0x4e00 in cmap                              # requested codepoint present
    assert 0x0041 not in cmap                          # un-requested codepoint dropped
```

- [ ] **Step 2: Run test to verify it fails**

Run: `uv run pytest tests/test_subset.py -q -m integration`
Expected: FAIL — `ModuleNotFoundError: cheritage.subset`.

- [ ] **Step 3: Implement `src/cheritage/subset.py`**

```python
from fontTools.subset import Options, Subsetter
from fontTools.ttLib import TTFont
from .slices import Slice

def subset_to_woff2(src_path: str, sl: Slice, out_path: str, *, keep_variations: bool) -> None:
    font = TTFont(src_path)
    opts = Options()
    opts.flavor = "woff2"
    opts.retain_gids = False
    opts.desubroutinize = True            # smaller CFF, harmless for glyf
    opts.recalc_bounds = True
    opts.notdef_outline = True            # keep .notdef shape
    opts.name_IDs = ["*"]                 # keep name table (family/RFN notices)
    opts.name_legacy = True
    opts.layout_features = ["*"]          # keep GSUB/GPOS (ligatures, locl, kerning)
    if not keep_variations:
        opts.drop_tables += ["fvar", "gvar", "avar", "STAT"]
    subs = Subsetter(options=opts)
    subs.populate(unicodes=sorted(sl.codepoints()))
    subs.subset(font)
    font.save(out_path)
    font.close()
```

- [ ] **Step 4: Run test to verify it passes**

Run: `uv run pytest tests/test_subset.py -q -m integration`
Expected: PASS (1 passed). Each slice file should be small (tens of KB).

- [ ] **Step 5: Commit**

```bash
git add src/cheritage/subset.py tests/test_subset.py
git commit -m "feat(subset): fontTools woff2 slicer retaining variable axes + layout"
```

---

## Task 7: Packager — assemble the npm package directory

**Files:**
- Create: `src/cheritage/package.py`
- Test: `tests/test_package.py`

- [ ] **Step 1: Write the failing test**

```python
# tests/test_package.py
import json
from cheritage.roster import FamilyConfig
from cheritage.package import package_json, write_package_skeleton

VF = FamilyConfig(id="shanggu-serif", font_family="Shanggu Serif", style="serif",
                  format="vf", repo="GuiWonder/Shanggu", release_tag="v1.028",
                  asset="x.ttf", asset_sha256="0", license_path="OFL.txt",
                  weight_min=100, weight_max=900)

def test_package_json_fields():
    pj = package_json(VF, version="0.1.0")
    assert pj["name"] == "@cheritage/shanggu-serif"
    assert pj["version"] == "0.1.0"
    assert pj["license"] == "OFL-1.1"
    assert pj["sideEffects"] == ["*.css"]
    assert pj["exports"]["./variable.css"] == "./variable.css"
    assert "GuiWonder/Shanggu" in pj["description"]

def test_write_package_skeleton_creates_layout(tmp_path):
    root = write_package_skeleton(VF, dest=str(tmp_path), version="0.1.0",
                                  css="@font-face{}", license_text="OFL TEXT")
    assert (root / "package.json").exists()
    assert (root / "variable.css").read_text() == "@font-face{}"
    assert (root / "LICENSE").read_text() == "OFL TEXT"
    assert (root / "files").is_dir()
    assert json.loads((root / "package.json").read_text())["name"] == "@cheritage/shanggu-serif"
```

- [ ] **Step 2: Run test to verify it fails**

Run: `uv run pytest tests/test_package.py -q`
Expected: FAIL — `ModuleNotFoundError: cheritage.package`.

- [ ] **Step 3: Implement `src/cheritage/package.py`**

```python
import json
from pathlib import Path
from .roster import FamilyConfig

def css_entry_name(fam: FamilyConfig) -> str:
    return "variable.css" if fam.format == "vf" else "index.css"

def package_json(fam: FamilyConfig, *, version: str) -> dict:
    entry = css_entry_name(fam)
    return {
        "name": f"@cheritage/{fam.id}",
        "version": version,
        "description": f"{fam.font_family} — 傳承字形 webfont subset of {fam.repo} "
                       f"({fam.release_tag}), sliced by cheritage.",
        "license": "OFL-1.1",
        "sideEffects": ["*.css"],
        "exports": {f"./{entry}": f"./{entry}", "./files/*": "./files/*"},
        "files": [entry, "files/", "LICENSE"],
        "keywords": ["webfont", "cjk", "traditional-chinese", "傳承字形", fam.style],
    }

def write_package_skeleton(fam: FamilyConfig, *, dest: str, version: str,
                           css: str, license_text: str) -> Path:
    root = Path(dest) / fam.id
    (root / "files").mkdir(parents=True, exist_ok=True)
    (root / css_entry_name(fam)).write_text(css)
    (root / "LICENSE").write_text(license_text)
    (root / "package.json").write_text(json.dumps(package_json(fam, version=version), indent=2, ensure_ascii=False))
    return root
```

- [ ] **Step 4: Run test to verify it passes**

Run: `uv run pytest tests/test_package.py -q`
Expected: PASS (2 passed).

- [ ] **Step 5: Commit**

```bash
git add src/cheritage/package.py tests/test_package.py
git commit -m "feat(package): npm package skeleton + package.json generator"
```

---

## Task 8: Build orchestrator — end-to-end for one family

**Files:**
- Create: `src/cheritage/build.py`
- Test: `tests/test_build.py`

- [ ] **Step 1: Write the failing integration test**

```python
# tests/test_build.py
import json, pytest
from pathlib import Path
from cheritage.build import build_family

@pytest.mark.integration
def test_build_shanggu_serif_produces_installable_package(tmp_path):
    root = build_family("shanggu-serif", roster_path="roster.toml",
                        dest=str(tmp_path), version="0.1.0")
    pj = json.loads((root / "package.json").read_text())
    assert pj["name"] == "@cheritage/shanggu-serif"
    css = (root / "variable.css").read_text()
    n_faces = css.count("@font-face")
    woff2 = list((root / "files").glob("*.woff2"))
    # one woff2 per @font-face, all real woff2, every src resolves
    assert len(woff2) == n_faces > 50
    assert all(p.read_bytes()[:4] == b"wOF2" for p in woff2)
    for p in woff2:
        assert f"src: url(./files/{p.name})" in css
```

- [ ] **Step 2: Run test to verify it fails**

Run: `uv run pytest tests/test_build.py -q -m integration`
Expected: FAIL — `ModuleNotFoundError: cheritage.build`.

- [ ] **Step 3: Implement `src/cheritage/build.py`**

```python
import sys
import zipfile
from pathlib import Path
from .roster import load_roster, FamilyConfig
from .acquire import download
from .slices import load_slices
from .subset import subset_to_woff2
from .cssgen import generate_css, woff2_name
from .package import write_package_skeleton, css_entry_name

def _font_path(asset: Path) -> Path:
    # Shanggu releases may ship a .ttf directly or zipped; handle both.
    if asset.suffix.lower() in (".ttf", ".otf"):
        return asset
    if zipfile.is_zipfile(asset):
        out = asset.with_suffix(".extracted")
        out.mkdir(exist_ok=True)
        with zipfile.ZipFile(asset) as z:
            ttfs = [n for n in z.namelist() if n.lower().endswith((".ttf", ".otf"))]
            z.extract(ttfs[0], out)
            return out / ttfs[0]
    return asset

def build_family(family_id: str, *, roster_path: str, dest: str, version: str) -> Path:
    fam = next(f for f in load_roster(roster_path) if f.id == family_id)
    asset = download(fam.repo, fam.release_tag, fam.asset,
                     expected_sha256=fam.asset_sha256)
    font_path = _font_path(asset)
    slices = load_slices(f"data/slices.{fam.style}.json")

    license_text = Path(fam.license_path).read_text() if Path(fam.license_path).exists() else \
        f"See {fam.repo} {fam.release_tag} OFL.txt"
    root = write_package_skeleton(fam, dest=dest, version=version,
                                  css=generate_css(fam, slices),
                                  license_text=license_text)
    for s in slices:
        out = root / "files" / woff2_name(fam, s.index)
        subset_to_woff2(str(font_path), s, str(out), keep_variations=(fam.format == "vf"))
    return root

if __name__ == "__main__":   # python -m cheritage.build <family_id>
    fam_id = sys.argv[1]
    out = build_family(fam_id, roster_path="roster.toml", dest="dist", version="0.1.0")
    print(f"built {out}")
```

- [ ] **Step 4: Run test to verify it passes**

Run: `uv run pytest tests/test_build.py -q -m integration`
Expected: PASS. (Slicing ~105 ranges takes a minute or two.)

- [ ] **Step 5: Build both Shanggu faces for real and record checksums**

Run:
```bash
uv run python -m cheritage.build shanggu-serif
uv run python -m cheritage.build shanggu-sans
du -sh dist/shanggu-serif dist/shanggu-sans
# record real sha256 into roster.toml so future builds are verified:
uv run python -c "from cheritage.acquire import download,sha256_file; from cheritage.roster import load_roster; [print(f.id, sha256_file(str(download(f.repo,f.release_tag,f.asset)))) for f in load_roster('roster.toml')]"
```
Paste each printed sha256 into the matching `asset_sha256` in `roster.toml`.

- [ ] **Step 6: Verify the package is npm-packable**

Run: `cd dist/shanggu-serif && npm pack --dry-run && cd ../..`
Expected: lists `package.json`, `variable.css`, `LICENSE`, and `files/*.woff2`; no errors.

- [ ] **Step 7: Commit**

```bash
git add src/cheritage/build.py tests/test_build.py roster.toml
git commit -m "feat(build): end-to-end family build → installable @cheritage package"
```

---

## Task 9: Visual smoke test — heritage glyphs actually render (spec §8)

Confirms the slices render real heritage forms in a browser, not just that bytes are woff2.

**Files:**
- Create: `tests/visual/index.html`
- Create: `tests/visual/README.md`

- [ ] **Step 1: Write a manual visual harness**

`tests/visual/index.html`:

```html
<!doctype html><meta charset="utf-8">
<title>cheritage visual smoke</title>
<style>
  @import url("../../dist/shanggu-serif/variable.css");
  @import url("../../dist/shanggu-sans/variable.css");
  body { font-size: 48px; line-height: 2; }
  .serif { font-family: "Shanggu Serif", serif; }
  .sans  { font-family: "Shanggu Sans", sans-serif; font-weight: 300; }
  .heavy { font-weight: 900; }     /* proves the VF axis works from one file */
</style>
<!-- 戶 骨 直 過 青 are classic 傳承 vs 國標 divergence points -->
<p class="serif">傳承字形：戶骨直過青說海角</p>
<p class="sans">傳承字形：戶骨直過青說海角</p>
<p class="sans heavy">字重 900：戶骨直過青</p>
<!-- mixed-script: kana/hangul should fall through to system font, not tofu -->
<p class="serif">混排：漢字 かな 한글 简体</p>
```

`tests/visual/README.md`:

```md
# Visual smoke test
1. Build packages: `uv run python -m cheritage.build shanggu-serif && uv run python -m cheritage.build shanggu-sans`
2. Serve repo root: `python -m http.server 8000`
3. Open http://localhost:8000/tests/visual/
4. Confirm: (a) 戶/骨/直/過/青 show 傳承 (old) forms, not MOE forms;
   (b) the 字重 900 line is visibly heavier (VF axis works from one file);
   (c) かな/한글 render (from system fonts) — no tofu boxes.
```

- [ ] **Step 2: Run the visual check**

Run: `uv run python -m cheritage.build shanggu-serif && uv run python -m cheritage.build shanggu-sans && python -m http.server 8000`
Then open the URL and verify the three points above by eye.

- [ ] **Step 3: Commit**

```bash
git add tests/visual/index.html tests/visual/README.md
git commit -m "test(visual): browser smoke harness for heritage glyph + VF axis"
```

---

## Task 10: Coverage analysis (spec §8 / task #6) — confirm the default

Tests the hypothesis that raw glyph count is misleading: a family may hoard rare codepoints while missing common-but-hard 傳承 chars.

**Files:**
- Create: `data/common-hard-tc.txt`
- Create: `src/cheritage/coverage.py`
- Test: `tests/test_coverage.py`

- [ ] **Step 1: Seed the common-hard charset**

`data/common-hard-tc.txt` (one line; extend as needed — these are common chars whose 傳承 vs 國標 forms diverge or that are easy to miss):

```
戶骨直過青說海角免勉勝券卷港滑骨體髙鄉響鬱靈鑑釁衛
```

- [ ] **Step 2: Write the failing test**

```python
# tests/test_coverage.py
import pytest
from cheritage.coverage import cmap_codepoints, coverage_report

def test_coverage_report_counts_and_missing():
    cmap = {0x6236, 0x9aa8}                 # 戶 骨
    rep = coverage_report(cmap, "戶骨直")    # 直 (U+76F4) missing
    assert rep["total_glyphs"] == 2
    assert rep["target_total"] == 3
    assert rep["target_covered"] == 2
    assert rep["missing"] == ["直"]

@pytest.mark.integration
def test_real_families_cover_common_hard_set():
    from cheritage.acquire import download
    paths = {
        "shanggu-serif": download("GuiWonder/Shanggu", "v1.028", "ShangguSerifTC.ttf"),
        # genyo added in a later plan; serif vs serif is the meaningful comparison
    }
    target = open("data/common-hard-tc.txt").read().strip()
    for name, p in paths.items():
        rep = coverage_report(cmap_codepoints(str(p)), target)
        # the chosen default MUST cover the entire common-hard set
        assert rep["target_covered"] == rep["target_total"], (name, rep["missing"])
```

- [ ] **Step 3: Run test to verify it fails**

Run: `uv run pytest tests/test_coverage.py -q`
Expected: FAIL — `ModuleNotFoundError: cheritage.coverage`.

- [ ] **Step 4: Implement `src/cheritage/coverage.py`**

```python
from fontTools.ttLib import TTFont

def cmap_codepoints(font_path: str) -> set[int]:
    return set(TTFont(font_path).getBestCmap().keys())

def coverage_report(cmap: set[int], target_chars: str) -> dict:
    targets = list(dict.fromkeys(target_chars))   # dedupe, keep order
    missing = [c for c in targets if ord(c) not in cmap]
    return {
        "total_glyphs": len(cmap),
        "target_total": len(targets),
        "target_covered": len(targets) - len(missing),
        "missing": missing,
    }
```

- [ ] **Step 5: Run unit + integration tests**

Run: `uv run pytest tests/test_coverage.py -q` then `uv run pytest tests/test_coverage.py -q -m integration`
Expected: PASS. If the integration assert fails, the default font is **missing common-hard chars** → record in spec §9.1 and reconsider the default (this is the whole point of the task).

- [ ] **Step 6: Generate the comparison report and record the verdict**

Run:
```bash
uv run python -c "from cheritage.coverage import *; from cheritage.acquire import download; t=open('data/common-hard-tc.txt').read().strip(); print('shanggu-serif', coverage_report(cmap_codepoints(str(download('GuiWonder/Shanggu','v1.028','ShangguSerifTC.ttf'))), t))"
```
Write a one-paragraph verdict into the spec §9.1 (Shanggu confirmed as practical default, or not).

- [ ] **Step 7: Commit**

```bash
git add data/common-hard-tc.txt src/cheritage/coverage.py tests/test_coverage.py docs/superpowers/specs/2026-06-12-cheritage-design.md
git commit -m "feat(coverage): cmap coverage analysis vs common-hard TC set; confirm default"
```

---

## Deferred to later plans (noted, not built here)

- **Plan 2 — GenYo neutral alt:** static per-weight build for all ~7 Source Han weights (`@cheritage/genyo-min`, `@cheritage/genyo-gothic`); extends roster + `build.py` static branch; per-weight CSS via `index.css` importing `<weight>.css`.
- **Plan 3 — Meta-package `cheritage`:** re-exports default serif+sans CSS + sets `--han-heritage-serif/-sans`.
- **Plan 4 — CI/publish:** GitHub Actions matrix over roster → build → version → `npm publish`; jsDelivr verification.
- **Plan 5 — Demo/docs site:** heritage-vs-MOE comparison, weight slider, install snippets.
- **Plan 6 — han.css integration:** replace the Google Fonts `@import` in `../next/src/css/fonts/webfonts/generics.css` with cheritage CDN imports.
- **Open compliance gate (spec §7):** before first `npm publish`, grep each upstream `OFL.txt` for a Reserved Font Name; keep the name only if none is declared, else rename the output family.

---

## Self-Review

**Spec coverage:** §1–2 motivation/goals → Tasks 1–10 realize the pipeline. §3 roster → Task 2. §4 architecture (6 components) → roster(T2), acquire(T5), slice engine(T3+T6), css gen(T4), packager(T7), build(T8); CI is Plan 4. §5 consumption API → CSS shape asserted in T4/T8, exercised in T9. §6 error handling: font-display swap (T4), fallthrough/no-tofu (T9 mixed-script), VF support (T6 axis retention), OFL bundling (T7 LICENSE + T8). §7 RFN gate → deferred compliance note. §8 testing → visual(T9) + coverage(T10) + determinism (woff2 magic asserts). §9 decisions baked into roster.toml + §9.5 snapshot in T3. No spec section left without a task.

**Placeholder scan:** the only literal placeholders are `asset_sha256` values, which are *intentionally* filled by the first real download (T8 Step 5) — flagged inline, not silent TODOs. All code steps contain complete, runnable code.

**Type consistency:** `FamilyConfig` fields used identically across roster/cssgen/package/build. `Slice(index, unicode_range)` consistent T3→T6. `woff2_name(fam, index, weight=None)` defined in cssgen (T4) and reused in build (T8) with matching signature. `generate_css(fam, slices, weight=None)`, `subset_to_woff2(src, slice, out, *, keep_variations)`, `write_package_skeleton(fam, *, dest, version, css, license_text)`, `build_family(id, *, roster_path, dest, version)` — all call sites match definitions.
