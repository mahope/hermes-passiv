#!/bin/bash
set -euo pipefail
DIR="$(cd "$(dirname "$0")" && pwd)"
python3 "$DIR/build_sites.py"
python3 "$DIR/tools/check_live_sitemaps.py" "$@"
