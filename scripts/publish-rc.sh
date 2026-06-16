#!/usr/bin/env bash
# Publish this RC round to npm under the `rc` dist-tag (does NOT move `latest`).
# This round = the CFF2→glyf fix (Chrome rendered CFF2 ~1.6× too thin; glyf
# renders correctly in Chrome+Safari). See memory/cff2-renders-thin-in-browsers.
#   Shanggu base ×2 → 0.1.0-rc.3  (glyf; supersedes CFF2 rc.0–rc.2)
#   Shanggu TC   ×2 → 0.1.0-rc.1  (glyf; rc.0 was CFF2)
# Genki ×4 already published @ rc.0 (static CFF, unaffected) — not re-published.
# GenYo is intentionally NOT here — it ships 0.1.0 stable later.
#
# Auth (hard-won, see memory/publish-workflow): account ethantw enforces 2FA on
# writes. A plain token hits EOTP. Use a classic *Automation* token, or set 2FA to
# "Authorization only" while publishing. Verify `npm whoami` = ethantw first.
#
# Run from repo root:  bash scripts/publish-rc.sh
set -uo pipefail
cd "$(dirname "$0")/.."

who=$(npm whoami 2>/dev/null) || { echo "✗ not logged in to npm"; exit 1; }
[ "$who" = "ethantw" ] || { echo "✗ npm whoami=$who (expected ethantw)"; exit 1; }
echo "✓ npm whoami=$who"

ids=(shanggu-serif shanggu-sans shanggu-serif-tc shanggu-sans-tc)

for id in "${ids[@]}"; do
  pkg="@hanzi.pro/webfonts-$id"
  ver=$(node -p "require('./dist/$id/package.json').version")
  # skip if this exact version already published (version-doc 200)
  if curl -fsS "https://registry.npmjs.org/$pkg/$ver" >/dev/null 2>&1; then
    echo "• $pkg@$ver already on registry — skip"
    continue
  fi
  echo "→ publishing $pkg@$ver"
  ( cd "dist/$id" && npm publish --tag rc --access public ) \
    && echo "  ✓ $pkg@$ver" \
    || echo "  ✗ $pkg@$ver (check: a 403 may still have succeeded — verify the version-doc)"
done

echo "Done. Verify: npm view @hanzi.pro/webfonts-shanggu-serif dist-tags"
