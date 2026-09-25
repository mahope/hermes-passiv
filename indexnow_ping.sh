#!/bin/bash
# indexnow_ping.sh — ping IndexNow (Bing, Yandex, Seznam, Naver) med alle sider.
# Nøglefilen serveres dynamisk af _worker.js: /indexnow-<key> returnerer nøglen,
# og den ligger på alle tre domæner, så der kan pinges per domæne.
# Brug: ./indexnow_ping.sh
set -u
KEY="0b3a0d81bfa64f1f9ec064cd6e292874"
HOSTS="mahope.tools cleancopy.tools deskuptime.com"

for HOST in $HOSTS; do
  # Verify key endpoint is live first (self-check)
  got=$(curl -s "https://$HOST/indexnow-$KEY")
  if [ "$got" != "$KEY" ]; then
    echo "FAIL $HOST: key endpoint returned '$got' — deploy first"
    continue
  fi

  # Collect URLs from that host's own sitemap
  urls=$(curl -s "https://$HOST/sitemap.xml" | grep -o '<loc>[^<]*</loc>' | sed 's/<[^>]*>//g')
  count=$(echo "$urls" | wc -l | tr -d ' ')
  if [ "$count" -eq 0 ]; then
    echo "FAIL $HOST: sitemap.xml gav ingen URLs"
    continue
  fi
  echo "Pinging $count URLs from $HOST to IndexNow..."

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
  echo "$HOST: IndexNow response $resp"
done
