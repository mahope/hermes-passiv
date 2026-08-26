#!/bin/zsh
# reconcile-waitlist.sh — daily cron: make wl-count honest.
# Counts actual wl:<hash> keys in KV and overwrites wl-count with that number.
# Guards against the counter drifting from reality (found 2026-08-26: count=10, real=0).
set -e
set -a; source "$HOME/.hermes/.env"; set +a

ACC="$CLOUDFLARE_ACCOUNT_ID"
NS="$CF_KV_NAMESPACE_ID"

REAL=$(python3 - <<EOF
import os, json, urllib.request
acc=os.environ['CLOUDFLARE_ACCOUNT_ID']; ns=os.environ['CF_KV_NAMESPACE_ID']; tok=os.environ['CLOUDFLARE_API_TOKEN']
n=0; cursor=''
while True:
    url=f"https://api.cloudflare.com/client/v4/accounts/{acc}/storage/kv/namespaces/{ns}/keys?limit=1000&prefix=wl:{cursor}"
    r=urllib.request.Request(url, headers={'Authorization':f'Bearer {tok}'})
    d=json.load(urllib.request.urlopen(r))
    n+=len(d.get('result',[]))
    cd=d.get('result_info',{}).get('cursor','')
    if not cd: break
    cursor=f"&cursor={cd}"
print(n)
EOF
)

CUR=$(curl -s "https://api.cloudflare.com/client/v4/accounts/$ACC/storage/kv/namespaces/$NS/values/wl-count" \
  -H "Authorization: Bearer $CLOUDFLARE_API_TOKEN")

echo "$(date +%FT%T%z) real=$REAL stored=$CUR" >> "$HOME/hermes-passiv/reconcile.log"

if [ "$REAL" != "$CUR" ]; then
  curl -s -X PUT "https://api.cloudflare.com/client/v4/accounts/$ACC/storage/kv/namespaces/$NS/values/wl-count" \
    -H "Authorization: Bearer $CLOUDFLARE_API_TOKEN" --data "$REAL" > /dev/null
  echo "$(date +%FT%T%z) FIXED wl-count $CUR -> $REAL" >> "$HOME/hermes-passiv/reconcile.log"
fi
