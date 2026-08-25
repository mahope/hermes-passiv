#!/bin/bash
# indexnow_ping.sh — ping IndexNow (Bing, Yandex, Seznam, Naver) with all site URLs.
# Key file is served dynamically by _worker.js: /indexnow-<key> returns the key.
# Usage: ./indexnow_ping.sh
set -u
KEY="0b3a0d81bfa64f1f9ec064cd6e292874"
HOST="hermes-passiv.pages.dev"

# Verify key endpoint is live first (self-check)
got=$(curl -s "https://$HOST/indexnow-$KEY")
if [ "$got" != "$KEY" ]; then
  echo "FAIL: key endpoint returned '$got' — deploy first"
  exit 1
fi

# Collect URLs from sitemap
urls=$(curl -s "https://$HOST/sitemap.xml" | grep -o '<loc>[^<]*</loc>' | sed 's/<[^>]*>//g')
count=$(echo "$urls" | wc -l)
echo "Pinging $count URLs to IndexNow..."

json='{"host":"'$HOST'","key":"'$KEY'","keyLocation":"https://'$HOST'/indexnow-'$KEY'","urlList":['
first=1
for u in $urls; do
  [ $first -eq 1 ] || json="$json,"
  json="$json\"$u\""
  first=0
done
json="$json]}"

resp=$(curl -s -o /dev/null -w "%{http_code}" -X POST \
  -H "Content-Type: application/json; charset=utf-8" \
  -d "$json" "https://api.indexnow.org/indexnow")
# 200/202 = accepted. Note: repeated identical pings may return 429 — that's fine.
echo "IndexNow response: $resp"
