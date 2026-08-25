#!/bin/bash
# smoke_test_desktop.sh — hovedløs build-test af desktop-src zippen.
# Verificerer: unzip OK, npm install OK, scanner-core loader, electron-binær findes.
# Brug: ./tools/smoke_test_desktop.sh
set -e
ZIP="$(dirname "$0")/../site/downloads/eaa-scanner-desktop-src-1.2.0.zip"
TMP="$(mktemp -d)"
trap 'rm -rf "$TMP"' EXIT

echo "== 1. unzip =="
unzip -q "$ZIP" -d "$TMP"
test -f "$TMP/eaa-scanner-desktop/package.json" || { echo "FEJL: package.json mangler i zippens rod/desktop"; exit 1; }
echo "OK"

echo "== 2. npm install (ignorerer scripts; electron-binær tjekkes separat) =="
cd "$TMP/eaa-scanner-desktop"
npm install --ignore-scripts --no-audit --no-fund >/dev/null 2>&1
echo "OK"

echo "== 3. scanner-core.js kan loade i ren Node =="
node -e "require('./scanner-core.js'); console.log('OK')"

echo "== 4. electron-binær downloades korrekt =="
node node_modules/electron/install.js
test -x node_modules/electron/dist/Electron.app/Contents/MacOS/Electron && echo "OK (macOS)" \
  || test -x node_modules/electron/dist/electron && echo "OK (linux)"

echo "ALLE TJEK BESTÅET"
