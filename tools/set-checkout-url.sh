#!/bin/bash
# set-checkout-url.sh — Gemmer Lemon Squeezy checkout-URL i KV
#
# Brug efter at have kørt node lemon-setup.js:
#   ./tools/set-checkout-url.sh "https://checkout.lemonsqueezy.com/..."        # Clean Copy Pro (standard)
#   ./tools/set-checkout-url.sh pp "https://checkout.lemonsqueezy.com/..."     # Page Profile Pro
#
# BEMÆRK: Kræver at wrangler er logget ind (npx wrangler whoami).

set -euo pipefail

KV_NS="215f8a921ac34dbcad9eb204e06baf2f"

if [ $# -eq 1 ]; then
  PRODUCT="cc"; URL="$1"
elif [ $# -eq 2 ] && [ "$1" = "pp" ]; then
  PRODUCT="pp"; URL="$2"
else
  echo "Brug: $0 [pp] <checkout-url>"
  echo "  (uden 'pp' gemmes URL'en som Clean Copy Pro; med 'pp' som Page Profile Pro)"
  exit 1
fi

if [[ "$URL" != https://*lemonsqueezy.com/* ]]; then
  echo "FEJL: URL ligner ikke et Lemon Squeezy checkout-link: $URL"
  exit 1
fi

KEY="$([ "$PRODUCT" = pp ] && echo pp-pro-checkout || echo cc-pro-checkout)"

echo "Gemmer checkout-URL i KV under '$KEY'..."
npx wrangler kv key put "$KEY" "$URL" --namespace-id "$KV_NS" --remote

echo ""
echo "URL gemt. $([ "$PRODUCT" = pp ] && echo '/page-profile og /da/page-profile viser nu Køb Pro.' || echo '/clean-copy viser nu Buy Pro.')"
echo ""
echo "Verificér: curl 'https://hermes-passiv.pages.dev/api/checkout$([ "$PRODUCT" = pp ] && echo '?product=pp' || echo '')'"