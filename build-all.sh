#!/bin/bash
# build-all.sh — Build all products in one command
# python3 build_ebook_all.py + make_cover_all.py + build_bundle.py
# Output: ebook/*.epub, ebook/*-cover.jpg, products/compliance-bundle.html

set -e

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
cd "$SCRIPT_DIR"

echo "=== Build all — Start === (24 Aug 2026)"

echo ""
echo "1. Building EPUBs..."
python3 build_ebook_all.py

echo ""
echo "2. Generating covers..."
python3 make_cover_all.py

echo ""
echo "3. Building ComplianceDocs bundle..."
python3 build_bundle.py

echo ""
echo "=== Output files ==="
for f in \
  ebook/nis2-for-agencies.epub \
  ebook/eaa-checklist.epub \
  ebook/cover.jpg \
  ebook/eaa-cover.jpg \
  products/compliance-bundle.html; do
    if [ -f "$f" ]; then
        SIZE=$(wc -c < "$f" | tr -d ' ')
        printf "  ✅ %-40s %10d bytes\n" "$f" "$SIZE"
    else
        echo "  ❌ $f (MISSING)"
    fi
done

echo ""
echo "=== Build complete ==="