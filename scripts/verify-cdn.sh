#!/usr/bin/env bash
# Verify a published package is live + correctly served on jsDelivr and unpkg.
#
# Usage:
#   scripts/verify-cdn.sh <pkg@version> <css-entry> <sample-woff2>
# Example:
#   scripts/verify-cdn.sh @hanzi.pro/webfonts-shanggu-serif@0.1.0-rc.1 \
#       variable.css files/shanggu-serif.0.woff2
#
# Always test a PINNED version (…@x.y.z) — @latest/unversioned is cached for days
# on jsDelivr and will not reflect a fresh publish.
set -euo pipefail

PKG="${1:?need <pkg@version>}"
CSS="${2:?need css entry, e.g. variable.css}"
WOFF2="${3:?need sample woff2, e.g. files/shanggu-serif.0.woff2}"

fail=0

check() {  # check <url> <expect-content-type-substr>
  local url="$1" want="$2" code ct acao cc ok
  ct=$(curl -sIL "$url" | grep -i '^content-type:'  | tail -1 | tr -d '\r' | cut -d' ' -f2-)
  acao=$(curl -sIL "$url" | grep -i '^access-control-allow-origin:' | tail -1 | tr -d '\r')
  cc=$(curl -sIL "$url" | grep -i '^cache-control:' | tail -1 | tr -d '\r')
  code=$(curl -sIL -o /dev/null -w '%{http_code}' "$url")
  ok="OK"
  [ "$code" = 200 ]        || { ok="FAIL(http=$code)"; fail=1; }
  case "$ct" in *"$want"*) ;; *) ok="FAIL(ctype=$ct want=$want)"; fail=1 ;; esac
  case "$acao" in *"*"*) ;; *) [ "$ok" = OK ] && ok="WARN(no CORS *)" ;; esac
  printf "    %-26s %s\n" "$ok" "$url"
  printf "      content-type=%s | %s | %s\n" "${ct:-?}" "${acao:-no-cors}" "${cc:-no-cache-header}"
}

verify_on() {  # verify_on <name> <base-url>
  echo "== $1 =="
  check "$2/${CSS}"   "css"
  check "$2/${WOFF2}" "font/woff2"
}

verify_on jsdelivr "https://cdn.jsdelivr.net/npm/${PKG}"
verify_on unpkg    "https://unpkg.com/${PKG}"

if [ "$fail" = 0 ]; then echo "✅ all CDN checks passed"; else echo "❌ some checks failed"; exit 1; fi
