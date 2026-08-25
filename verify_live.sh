#!/bin/bash
# Verify live deployment of new guides, index links, sitemap and JSON-LD
sleep 15
for u in guides/prestashop-accessibility-check guides/weebly-accessibility-check; do
  code=$(curl -sL -o /tmp/p.html -w '%{http_code}' "https://hermes-passiv.pages.dev/$u")
  echo "$u -> $code | $(grep -o '<title>[^<]*' /tmp/p.html | head -1) | $(grep -o 'canonical" href="[^"]*' /tmp/p.html | head -1)"
done
echo "--- index guide-links found:"
curl -sL https://hermes-passiv.pages.dev/ > /tmp/idx.html
grep -c 'prestashop-accessibility-check' /tmp/idx.html
grep -c 'weebly-accessibility-check' /tmp/idx.html
grep -c '9 platform' /tmp/idx.html
echo "--- sitemap URLs:"
curl -sL https://hermes-passiv.pages.dev/sitemap.xml | grep -c '<loc>'
