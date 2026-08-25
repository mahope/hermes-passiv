#!/bin/bash
# self-check.sh — Automated health check for ComplianceDocs
# Runs silently. Exits 0 on OK, 1 on failure.
# Logs to passiv.log for review.
# Designed to be run by cron or passiv-loop.sh.

set -e

SITE_URL="https://hermes-passiv.pages.dev"
LOG_FILE="$(dirname "$0")/passiv.log"
TIMESTAMP=$(date '+%Y-%m-%d %H:%M:%S')

log() {
  echo "[$TIMESTAMP] $1" >> "$LOG_FILE"
}

# --- Check 1: Site is up and returns 200 ---
HTTP_CODE=$(curl -s -o /dev/null -w "%{http_code}" --max-time 10 "$SITE_URL" 2>/dev/null || echo "000")

if [ "$HTTP_CODE" != "200" ]; then
  log "SITE_DOWN — HTTP $HTTP_CODE — $SITE_URL"
  echo "CHECK_FAIL: Site returned HTTP $HTTP_CODE"
  exit 1
fi

# --- Check 2: Page contains expected content ---
CONTENT=$(curl -s --max-time 10 "$SITE_URL" 2>/dev/null || echo "")

if ! echo "$CONTENT" | grep -q "ComplianceDocs"; then
  log "CONTENT_MISMATCH — Expected 'ComplianceDocs' not found on $SITE_URL"
  echo "CHECK_FAIL: Content mismatch on $SITE_URL"
  exit 1
fi

# --- Check 3: Product count >= 4 (we have 5 products listed) ---
PRODUCT_COUNT=$(echo "$CONTENT" | grep -c "product-card" || echo "0")
if [ "$PRODUCT_COUNT" -lt 4 ]; then
  log "PRODUCT_COUNT_LOW — Found only $PRODUCT_COUNT products (expected 4+)"
  echo "CHECK_FAIL: Only $PRODUCT_COUNT products rendered"
  exit 1
fi

# --- Check 4: Version sweep — all Clean Copy surfaces in sync ---
SWEEP=$(python3 "$(dirname "$0")/version_sweep.py" 2>&1) || true
if ! echo "$SWEEP" | grep -q "ALL SURFACES IN SYNC"; then
  log "VERSION_SWEEP_FAIL — $SWEEP"
  echo "CHECK_FAIL: version mismatch across Clean Copy surfaces"
  exit 1
fi

# --- Check 5: Inline JS syntax on all site HTML (catches broken <script> blocks) ---
JS_CHECK=$(python3 "$(dirname "$0")/tools/check_inline_js.py" 2>&1) || true
if ! echo "$JS_CHECK" | grep -q "problems: 0"; then
  log "INLINE_JS_SYNTAX_FAIL — $JS_CHECK"
  echo "CHECK_FAIL: inline JS syntax errors found"
  exit 1
fi
exit 0
