#!/bin/bash
# set-checkout-url.sh — Gemmer Lemon Squeezy checkout-URL i KV
#
# Brug efter at have kørt node lemon-setup.js:
#   ./tools/set-checkout-url.sh "https://checkout.lemonsqueezy.com/..."        # Clean Copy Pro (standard)
#   ./tools/set-checkout-url.sh pp "https://checkout.lemonsqueezy.com/..."     # Page Profile Pro
#   ./tools/set-checkout-url.sh du "https://checkout.lemonsqueezy.com/..."     # DeskUptime Pro
#
# BEMÆRK: Kræver at wrangler er logget ind (npx wrangler whoami).

set -euo pipefail

KV_NS="215f8a921ac34dbcad9eb204e06baf2f"

if [ $# -eq 1 ]; then
  PRODUCT="cc"; URL="$1"
elif [ $# -eq 2 ] && [ "$1" = "pp" ]; then
  PRODUCT="pp"; URL="$2"
elif [ $# -eq 2 ] && [ "$1" = "du" ]; then
  PRODUCT="du"; URL="$2"
else
  echo "Brug: $0 [pp|du] <checkout-url>"
  echo "  (uden flag gemmes URL'en som Clean Copy Pro; 'pp' = Page Profile Pro; 'du' = DeskUptime Pro)"
  exit 1
fi

if [[ "$URL" != https://*lemonsqueezy.com/* ]]; then
  echo "FEJL: URL ligner ikke et Lemon Squeezy checkout-link: $URL"
  exit 1
fi

case "$PRODUCT" in
  pp) KEY="pp-pro-checkout" ;;
  du) KEY="du-pro-checkout" ;;
  *)  KEY="cc-pro-checkout" ;;
esac

echo "Gemmer checkout-URL i KV under '$KEY'..."
npx wrangler kv key put "$KEY" "$URL" --namespace-id "$KV_NS" --remote

echo ""
echo "URL gemt. Verificér: curl 'https://hermes-passiv.pages.dev/api/checkout?product=$PRODUCT'"