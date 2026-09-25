#!/bin/bash
set -euo pipefail
DIR="$(cd "$(dirname "$0")" && pwd)"
LOG_FILE="$DIR/passiv.log"
TIMESTAMP=$(date '+%Y-%m-%d %H:%M:%S')

run_check() {
  local name="$1"
  shift
  local output
  if output=$("$@" 2>&1); then
    printf '[%s] OK %s\n' "$TIMESTAMP" "$name" >> "$LOG_FILE"
    return
  fi
  printf '[%s] FAIL %s\n%s\n' "$TIMESTAMP" "$name" "$output" >> "$LOG_FILE"
  printf 'CHECK_FAIL: %s\n' "$name"
  exit 1
}

cd "$DIR"
run_check sitemap-tests python3 tools/test_check_sitemaps.py
run_check build python3 build_sites.py
run_check sitemap python3 tools/check_sitemaps.py
run_check seo python3 tools/seo_check.py
run_check live-sitemaps python3 tools/check_live_sitemaps.py --attempts 1 --delay 0
run_check stripe-worker node tests/stripe-worker.test.mjs
run_check inline-js python3 tools/check_inline_js.py
run_check versions python3 version_sweep.py
