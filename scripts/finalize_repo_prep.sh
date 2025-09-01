#!/usr/bin/env bash
set -euo pipefail

echo "== Harmony / CHRS — repo prep finalizer =="

# --- 0) Ensure standard dirs exist ------------------------------------------
mkdir -p Codex/System Codex/Core Codex/SPs reports docs

# --- 1) .gitignore additions (append only if missing) -----------------------
GITIGNORE=.gitignore
touch "$GITIGNORE"

append_if_missing () {
  local line="$1"
  grep -qxF "$line" "$GITIGNORE" || echo "$line" >> "$GITIGNORE"
}

append_if_missing "harmony-venv/"
append_if_missing "__pycache__/"
append_if_missing "*.pyc"
append_if_missing "reports/.q_*.json"
append_if_missing "reports/Audit_Chain_Digests.md"
append_if_missing "reports/FCP_Audit_*.json"

echo "• .gitignore updated"

# --- 2) Seed Codex/Core/FCP_Audit.yaml if missing ---------------------------
AUDIT="Codex/Core/FCP_Audit.yaml"
if [ ! -f "$AUDIT" ]; then
  TS="$(date -u +%Y-%m-%dT%H:%M:%SZ)"
  cat > "$AUDIT" <<YAML
# FCP Audit Log (seed)
# This file is encrypted-at-rest via QSecure per policy.
events:
  - timestamp: "$TS"
    glyph: "⧉"
    virtue: "礼"
    action: "entered_fallback_review_cycle"
    justification: "Seed event to validate reporting pipeline"
    sp_ids: ["Harmonia"]
YAML
  echo "• Seeded $AUDIT"
else
  echo "• $AUDIT already exists (no changes)"
fi

# --- 3) Fix lingering 'Usage' typos in text files --------------------------
# macOS/BSD-safe in-place sed; restrict to common text extensions
MAP=$(mktemp)
# find text-like files (skip .git and binaries)
find . -type f \
  ! -path "*/.git/*" \
  ! -name "*.png" ! -name "*.jpg" ! -name "*.jpeg" ! -name "*.gif" ! -name "*.pdf" \
  ! -name "*.woff*" ! -name "*.ttf" ! -name "*.otf" \
  -print > "$MAP"

COUNT_BEFORE=$(grep -IHF "Usage" $(cat "$MAP") | wc -l | tr -d ' ')
if [ "$COUNT_BEFORE" != "0" ]; then
  # shellcheck disable=SC2046
  sed -i '' -e 's/Usage/Usage/g' $(cat "$MAP")
  echo "• Corrected 'Usage' → 'Usage' in $COUNT_BEFORE place(s)"
else
  echo "• No 'Usage' typos found"
fi
rm -f "$MAP"

# --- 4) Freeze Python deps for reproducibility ------------------------------
if command -v pip >/dev/null 2>&1; then
  pip freeze > requirements.lock.txt || true
  echo "• Wrote requirements.lock.txt"
else
  echo "• pip not found; skipped requirements.lock.txt"
fi

# --- 5) Drop a local quickstart doc -----------------------------------------
DOC=docs/Local_Usage.md
cat > "$DOC" <<'MD'
# Harmony / CHRS — Local Usage

## Common commands
```bash
make preflight   # validate FCP + QSecure
make weekly      # run sims, generate reports, merge reflections, audit digest
make audit       # FCP status + regulator-friendly audit outputs
