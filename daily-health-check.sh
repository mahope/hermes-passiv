#!/bin/zsh
# daily-health-check.sh — runs daily from cron, hits /api/health, logs result
# If health check fails 3 days in a row, creates a FAILURE file as signal.
DIR="$HOME/hermes-passiv"
LOG="$DIR/health-cron.log"
FAILURE_MARKER="$DIR/.health-failure"
HEALTH_URL="https://hermes-passiv.pages.dev/api/health"

cd "$DIR" || exit 1

http_status=$(curl -sL -o /tmp/health-result.json -w "%{http_code}" "$HEALTH_URL" 2>&1)

result=$(python3 -c "
import json,sys
try:
    with open('/tmp/health-result.json') as f:
        d=json.load(f)
    s=d.get('status','unknown')
    kv=d.get('kv',False)
    v=d.get('stats',{}).get('recentVisits',0)
    wl=d.get('stats',{}).get('waitlist',0)
    http = int($http_status)
    print(f'http={http} status={s} kv={kv} visits={v} wl={wl}')
    sys.exit(0 if s=='healthy' and http==200 else 1)
except Exception as e:
    print(f'PARSE_ERROR: {e}')
    sys.exit(1)
" 2>&1)
exit_code=$?

echo "$(date -Iseconds) $result" >> "$LOG"

if [ "$exit_code" -eq 0 ]; then
    [ -f "$FAILURE_MARKER" ] && rm "$FAILURE_MARKER"
else
    count=0
    [ -f "$FAILURE_MARKER" ] && count=$(cat "$FAILURE_MARKER")
    count=$((count + 1))
    echo "$count" > "$FAILURE_MARKER"
    echo "FAILURE $count: $result" >> "$LOG"
fi

tail -200 "$LOG" > /tmp/hc-log && mv /tmp/hc-log "$LOG"