#!/usr/bin/env bash
# Build + publish an RC round to npm under the `rc` dist-tag (does NOT move `latest`).
#
# THIS ROUND = 0.2.0. Three changes, all of them inside the font files:
#
#   1. Line metrics normalised to hhea/usWin 1100/-340 (per 1000 upem), so every
#      family shares one vertical central baseline (0.380em). Fixes the sideways
#      jog when two families meet in a vertical column. CSS `ascent-override`
#      cannot do this — Safari ignores it on that path.
#   2. Identity `vert`/`vrt2` substitution for U+FF1A / U+FF1B, so Firefox stops
#      rotating `：；` in vertical text (UTR50 class Tr).
#   3. `name` table rewritten to `Ziano <family>`, so the files stop presenting
#      themselves as an unmodified upstream release. INTERNAL ONLY — the CSS
#      family names are unchanged from the roster (`Shanggu Serif`, …).
#
# Plus the family rename: `-tc` (which pointed opposite ways between Shanggu and
# Genki) is gone, both cuts now carry `-dan` / `-yue`, and Genki's Min/Gothic
# became Serif/Sans. Eight package names changed; the old ones are NOT
# deprecated here (0.1.0 stays where it is).
#
# ⚠️ NOT a CSS-only round. Every woff2 is re-sliced, so `recss_dist` (which keeps
# the woff2 byte-identical) is the wrong tool — that was the 0.1.0 emoji-prune
# round. Run the full build first:
#
#     uv run python -c 'from ziano.build import build_family; from ziano.roster \
#       import load_roster; [build_family(f.id, roster_path="roster.toml", \
#       dest="dist", version="0.2.0") for f in load_roster("roster.toml")]'
#
#   …then this script, which only bumps the version and publishes what is in
#   dist/. It refuses to publish a package whose woff2 predate the last roster
#   change, so a forgotten rebuild fails loudly instead of shipping stale files.
#
# Versioning: each package bumps to one past its highest published 0.2.0 rc (no
# version burning, see memory/publish-workflow).
#
# Auth (hard-won, see memory/publish-workflow): account ethantw enforces 2FA on
# writes. A plain token hits EOTP. Use a classic *Automation* token, or set 2FA
# to "Authorization only" while publishing. `npm publish` will also prompt for an
# OTP interactively.
#
# Run from repo root:   bash scripts/publish-rc.sh                    # every family
#                       bash scripts/publish-rc.sh shanggu-serif  # a subset
set -uo pipefail
cd "$(dirname "$0")/.."
export PYTHONPATH="src${PYTHONPATH:+:$PYTHONPATH}"
PY=${PYTHON:-python3}

# The round is whatever the roster says — hardcoding ids is how the last round's
# list ended up naming eight directories that no longer exist.
# (`mapfile` is bash 4; macOS ships 3.2, so read the list the portable way.)
ids=()
while IFS= read -r line; do ids+=("$line"); done < <("$PY" -c "
from ziano.roster import load_roster
for f in load_roster('roster.toml'):
    print(f.id)
")
[ "$#" -gt 0 ] && ids=("$@")   # allow an explicit subset

who=$(npm whoami 2>/dev/null) || { echo "✗ not logged in to npm"; exit 1; }
[ "$who" = "ethantw" ] || { echo "✗ npm whoami=$who (expected ethantw)"; exit 1; }
echo "✓ npm whoami=$who · round: ${ids[*]}"

# next 0.2.0-rc.N for a package = one past the highest rc already on the registry.
next_rc() {
  local pkg=$1 cur
  cur=$(npm view "$pkg" versions --json 2>/dev/null \
        | grep -oE '0\.2\.0-rc\.[0-9]+' | sed 's/.*rc\.//' | sort -n | tail -1)
  echo "0.2.0-rc.$(( ${cur:--1} + 1 ))"
}

# A woff2 older than roster.toml means the rebuild never ran (or ran before the
# last roster edit) — the name table and metrics live in those files, so
# publishing them would ship the previous round's fonts under a new version.
stale() {
  local dir=$1 newest
  newest=$(find "$dir/files" -name '*.woff2' -newer roster.toml -print -quit 2>/dev/null)
  [ -z "$newest" ]
}

fail=0
for id in "${ids[@]}"; do
  pkg="@hanzi.pro/webfonts-$id"
  dir="dist/$id"
  [ -d "$dir/files" ] || { echo "✗ $pkg — no $dir/files (run the full build)"; fail=1; continue; }
  stale "$dir" && { echo "✗ $pkg — woff2 older than roster.toml (rebuild first)"; fail=1; continue; }
  ver=$(next_rc "$pkg")
  echo "→ $pkg@$ver"
  "$PY" -c "
import json, pathlib
p = pathlib.Path('$dir/package.json')
pkg = json.loads(p.read_text())
pkg['version'] = '$ver'
p.write_text(json.dumps(pkg, indent=2, ensure_ascii=False) + '\n')
" || { echo "  ✗ version bump failed — skip"; fail=1; continue; }
  ( cd "$dir" && npm publish --tag rc --access public ) \
    && echo "  ✓ $pkg@$ver" \
    || { echo "  ✗ $pkg@$ver (a 403 may still have succeeded — verify the version-doc)"; fail=1; }
done

echo
[ "$fail" = 0 ] || echo "⚠️  some packages did not publish — see above"
echo "Verify:  npm view @hanzi.pro/webfonts-shanggu-serif dist-tags"
echo "Purge jsDelivr @rc (the mutable tag caches ~7d — see memory/shanggu-variant):"
for id in "${ids[@]}"; do
  echo "  curl -s https://purge.jsdelivr.net/npm/@hanzi.pro/webfonts-$id@rc/swap.css >/dev/null"
done
echo "Then bump the demo's pinned @rc.N versions in demo/index.html."
