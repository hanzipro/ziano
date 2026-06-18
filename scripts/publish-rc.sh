#!/usr/bin/env bash
# Build + publish an RC round to npm under the `rc` dist-tag (does NOT move `latest`).
#
# THIS ROUND = emoji/PUA unicode-range prune. The slice tables (Google nam-files) put
# emoji, PUA and some foreign scripts in slices the CJK fonts have ZERO glyphs for, but
# the @font-face still advertised those ranges. Safari honours a bare unicode-range even
# when the woff2 lacks the glyph → it renders .notdef instead of falling through to the
# system emoji font (that's why 🌞 U+1F31E broke in Safari but not Chrome). build_family
# now prunes every slice's unicode-range to the font's real cmap and drops empty slices
# (see ziano/slices.py::prune_slices). So all the demo families need a rebuild + republish.
#
# Versioning: each package bumps to one past its highest published rc (no version burning,
# see memory/publish-workflow). The build is driven through build_family() directly so the
# version is set at build time (the `python -m ziano.build` CLI hardcodes 0.1.0).
#
# Auth (hard-won, see memory/publish-workflow): account ethantw enforces 2FA on writes.
# A plain token hits EOTP. Use a classic *Automation* token, or set 2FA to "Authorization
# only" while publishing. `npm publish` will also prompt for an OTP interactively.
#
# Run from repo root:   bash scripts/publish-rc.sh            # the full 12-family round
#                       bash scripts/publish-rc.sh shanggu-serif genki-min   # a subset
set -uo pipefail
cd "$(dirname "$0")/.."
export PYTHONPATH="src${PYTHONPATH:+:$PYTHONPATH}"

# the round: every family the demo ships. TC families break for 🌞; SC/JP families break
# for OTHER emoji that land in their own empty slices — so all of them get the prune.
ids=(
  shanggu-serif shanggu-sans shanggu-serif-tc shanggu-sans-tc
  genki-min genki-gothic genki-min-tc genki-gothic-tc
  lxgw-wenkai-tc lxgw-wenkai iansui klee-one
)
[ "$#" -gt 0 ] && ids=("$@")   # allow an explicit subset

who=$(npm whoami 2>/dev/null) || { echo "✗ not logged in to npm"; exit 1; }
[ "$who" = "ethantw" ] || { echo "✗ npm whoami=$who (expected ethantw)"; exit 1; }
echo "✓ npm whoami=$who · round: ${ids[*]}"

# next 0.1.0-rc.N for a package = one past the highest rc already on the registry.
next_rc() {
  local pkg=$1 cur
  cur=$(npm view "$pkg" versions --json 2>/dev/null \
        | grep -oE '0\.1\.0-rc\.[0-9]+' | sed 's/.*rc\.//' | sort -n | tail -1)
  echo "0.1.0-rc.$(( ${cur:--1} + 1 ))"
}

for id in "${ids[@]}"; do
  pkg="@hanzi.pro/webfonts-$id"
  ver=$(next_rc "$pkg")
  echo "→ build $pkg@$ver"
  python -c "from ziano.build import build_family; build_family('$id', roster_path='roster.toml', dest='dist', version='$ver')" \
    || { echo "  ✗ build failed — skip"; continue; }
  echo "  publishing…"
  ( cd "dist/$id" && npm publish --tag rc --access public ) \
    && echo "  ✓ $pkg@$ver" \
    || echo "  ✗ $pkg@$ver (a 403 may still have succeeded — verify the version-doc)"
done

echo
echo "Verify:  npm view @hanzi.pro/webfonts-shanggu-serif dist-tags"
echo "Purge jsDelivr @rc (the mutable tag caches ~7d — see memory/shanggu-variant):"
for id in "${ids[@]}"; do
  echo "  curl -s https://purge.jsdelivr.net/npm/@hanzi.pro/webfonts-$id@rc/swap.css >/dev/null"
done
echo "Then bump the demo's pinned @rc.N versions in demo/index.html."
