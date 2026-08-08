#!/usr/bin/env bash
# Mark the six 0.1.0 package names that 0.2.0 retires, each pointing at the
# name that now carries the same font.
#
# The mapping is NOT mechanical: `-tc` meant opposite cuts in the two families.
# 尚古's unsuffixed package was 丹 and its `-tc` was 月; 源起's `-tc` was 丹 and
# its unsuffixed was 月. Reading the old names as if one rule applied sends
# people to the wrong glyphs, which is exactly what these messages exist to
# prevent — so they are written out one by one rather than generated.
#
# Deprecating is not unpublishing: 0.1.0 keeps installing and keeps working.
# It adds a warning on install and a badge on npm.
#
# Auth: `npm whoami` = ethantw, 2FA OTP at the prompt.
# Run:  bash scripts/deprecate-retired.sh          # do it
#       DRY_RUN=1 bash scripts/deprecate-retired.sh  # print only
set -uo pipefail
cd "$(dirname "$0")/.."

who=$(npm whoami 2>/dev/null) || { echo "✗ not logged in to npm"; exit 1; }
[ "$who" = "ethantw" ] || { echo "✗ npm whoami=$who (expected ethantw)"; exit 1; }
echo "✓ npm whoami=$who"

# old package                    → message
declare -a RETIRED=(
  "shanggu-serif-tc|0.2.0 起改用 @hanzi.pro/webfonts-shanggu-serif-yue（月）。無後綴的 webfonts-shanggu-serif 是丹，不是這個包的字。"
  "shanggu-sans-tc|0.2.0 起改用 @hanzi.pro/webfonts-shanggu-sans-yue（月）。無後綴的 webfonts-shanggu-sans 是丹，不是這個包的字。"
  "genki-min|0.2.0 起改用 @hanzi.pro/webfonts-genki-serif-yue（月）。注意：源起的 -tc 才是丹，與尚古相反。"
  "genki-gothic|0.2.0 起改用 @hanzi.pro/webfonts-genki-sans-yue（月）。注意：源起的 -tc 才是丹，與尚古相反。"
  "genki-min-tc|0.2.0 起改用 @hanzi.pro/webfonts-genki-serif（丹）。Min→Serif，且無後綴＝丹。"
  "genki-gothic-tc|0.2.0 起改用 @hanzi.pro/webfonts-genki-sans（丹）。Gothic→Sans，且無後綴＝丹。"
)

failed=()
for row in "${RETIRED[@]}"; do
  id=${row%%|*}
  msg=${row#*|}
  pkg="@hanzi.pro/webfonts-$id"
  echo "→ $pkg"
  echo "   $msg"
  if [ "${DRY_RUN:-}" = "1" ]; then continue; fi
  if npm deprecate "$pkg" "$msg"; then
    echo "  ✓"
  else
    echo "  ✗"; failed+=("$pkg")
  fi
done

if [ ${#failed[@]} -gt 0 ]; then
  echo "failed: ${failed[*]}"; exit 1
fi
echo "Done. Verify: npm view @hanzi.pro/webfonts-genki-min-tc deprecated"
