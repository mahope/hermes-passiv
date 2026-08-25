#!/bin/zsh
# deploy.sh — udgiver denne agents site til Cloudflare Pages.
# Laast til ÉT projekt: du kan ikke komme til at deploye til et andet.
# Brug:  ./deploy.sh            (udgiver mappen "site")
#        ./deploy.sh public     (udgiver en anden mappe)
set -e
PROJEKT="hermes-passiv"
MAPPE="${1:-site}"
DIR="$(cd "$(dirname "$0")" && pwd)"
cd "$DIR"

if [ ! -d "$MAPPE" ]; then
  echo "FEJL: mappen '$MAPPE' findes ikke i $DIR"; exit 1
fi
if [ ! -f "$MAPPE/index.html" ]; then
  echo "ADVARSEL: der er ingen index.html i '$MAPPE' - sitet faar ingen forside"
fi

# credentials laeses fra ~/.hermes/.env (de staar ikke i dette script)
set -a; source "$HOME/.hermes/.env" 2>/dev/null; set +a
if [ -z "$CLOUDFLARE_API_TOKEN" ]; then
  echo "FEJL: CLOUDFLARE_API_TOKEN mangler i ~/.hermes/.env"; exit 1
fi

export PATH="$HOME/.local/bin:/opt/homebrew/bin:$PATH"
echo "Udgiver $MAPPE -> https://$PROJEKT.pages.dev"
npx --yes wrangler pages deploy "$MAPPE" \
  --project-name "$PROJEKT" --branch main --commit-dirty=true

echo ""
echo "Kontrollér selv bagefter - HTTP 200 er ikke bevis nok:"
echo "  curl -s https://$PROJEKT.pages.dev/ | head -40"
echo "Tjek at indholdet faktisk er det nye, og at undersider svarer."
