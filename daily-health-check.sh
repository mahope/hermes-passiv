#!/bin/zsh
set -u
DIR="${0:A:h}"
LOG="$DIR/health-cron.log"
FAILURE_MARKER="$DIR/.health-failure"
cd "$DIR" || exit 1

output=$(
  python3 build_sites.py &&
  python3 tools/check_live_sitemaps.py --attempts 1 --delay 0 &&
  python3 -c 'import json, urllib.request; response=urllib.request.urlopen("https://mahope.tools/api/health", timeout=15); data=json.loads(response.read()); raise SystemExit(0 if response.status == 200 and data.get("status") == "healthy" else 1)' 2>&1
)
exit_code=$?
result=$(print -r -- "$output" | tr '\n' ' ' | cut -c1-1000)
printf '%s exit=%s %s\n' "$(date -Iseconds)" "$exit_code" "$result" >> "$LOG"

if [ "$exit_code" -eq 0 ]; then
  rm -f "$FAILURE_MARKER"
else
  count=0
  [ -f "$FAILURE_MARKER" ] && count=$(<"$FAILURE_MARKER")
  count=$((count + 1))
  print -r -- "$count" > "$FAILURE_MARKER"
fi
