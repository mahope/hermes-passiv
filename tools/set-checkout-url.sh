#!/bin/bash
# set-checkout-url.sh — Gemmer Lemon Squeezy checkout-URL i KV
#
# Brug efter at have kørt node lemon-setup.js:
#   ./tools/set-checkout-url.sh "https://checkout.lemonsqueezy.com/..."
#
# BEMÆRK: Kræver at wrangler er logget ind (npx wrangler whoami).

set -euo pipefail

if [ $# -lt 1 ]; then
  echo "Brug: $0 <checkout-url>"
  echo "Eksempel: $0 'https://checkout.lemonsqueezy.com/...'"
  exit 1
fi

URL="$1"
KV_NS="215f8a921ac34dbcad9eb204e06baf2f"

echo "Gemmer checkout-URL i KV (namespace $KV_NS)..."
npx wrangler kv key put cc-pro-checkout "$URL" --namespace-id "$KV_NS" --remote

echo ""
echo "URL gemt. /clean-copy vil nu vise 'Buy Pro $19/year →'."
echo ""
echo "Verificér: curl https://hermes-passiv.pages.dev/api/checkout"