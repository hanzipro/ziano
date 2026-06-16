#!/usr/bin/env bash
# Take down the two base Shanggu rc's that were mis-packaged with the *TC* font
# (TC is punctuation-only, no 青→靑 舊字形 merge — wrong glyphs for the base pkg).
#   unpublish: shanggu-serif / shanggu-sans @ rc.0 and rc.1
#   KEEP:      rc.2 (CFF2, correct base variant — kept on purpose for comparison)
#              rc.3 (glyf, the good build)
#
# Order matters:
#   1) move `latest` off rc.0 → rc.3  (default `npm install` stops serving the
#      broken build; also npm won't unpublish a version a dist-tag points at)
#   2) unpublish rc.0, rc.1
#
# Caveat: npm only allows single-version unpublish within 72h of publish. rc.0
# (published 2026-06-13) is just past that window and may be REFUSED — that's
# non-fatal here; if it refuses, deprecate it instead or contact npm support.
#
# Auth: needs `npm whoami` = ethantw + 2FA OTP (see memory/publish-workflow).
# Run:  bash scripts/unpublish-bad-rc.sh
set -uo pipefail
cd "$(dirname "$0")/.."

who=$(npm whoami 2>/dev/null) || { echo "✗ not logged in to npm"; exit 1; }
[ "$who" = "ethantw" ] || { echo "✗ npm whoami=$who (expected ethantw)"; exit 1; }
echo "✓ npm whoami=$who"

pkgs=(shanggu-serif shanggu-sans)
good=0.1.0-rc.3
bad=(0.1.0-rc.0 0.1.0-rc.1)

for id in "${pkgs[@]}"; do
  pkg="@hanzi.pro/webfonts-$id"
  echo "=== $pkg ==="

  # 1) repoint `latest` to the good glyf build
  if npm dist-tag add "$pkg@$good" latest; then
    echo "  ✓ latest → $good"
  else
    echo "  ✗ could not move latest (skipping unpublish of rc.0 to stay safe)"; continue
  fi

  # 2) unpublish the mis-packaged versions (rc.0 may refuse past 72h)
  for v in "${bad[@]}"; do
    if npm unpublish "$pkg@$v"; then
      echo "  ✓ unpublished $v"
    else
      echo "  ✗ $v not unpublished (likely >72h window) — consider: npm deprecate \"$pkg@$v\" \"mis-packaged TC font; use $good\""
    fi
  done

  echo "  now: $(npm view "$pkg" dist-tags --json 2>/dev/null)"
done

echo "Done. Verify: npm view @hanzi.pro/webfonts-shanggu-serif versions dist-tags"
