#!/usr/bin/env bash
set -euo pipefail
count=0
# Walk files safely; skip .git and common binaries
find . -type f \
  -not -path "*/.git/*" \
  -not -name "*.png" -not -name "*.jpg" -not -name "*.jpeg" -not -name "*.gif" -not -name "*.pdf" \
  -not -name "*.woff*" -not -name "*.ttf" -not -name "*.otf" \
  -print0 | while IFS= read -r -d '' f; do
    if grep -Iq "Usage" "$f"; then
      sed -i '' -e 's/Usage/Usage/g' "$f"
      count=$((count+1))
      echo "fixed: $f"
    fi
  done
echo "Done. Files touched: $count"
