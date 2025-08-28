#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."

REASON="${1:-'operator_request'}"
DAYS="${2:-7}"

python3 scripts/fcp_guard.py activate "$REASON" --days "$DAYS"
# Helpful status echo
python3 scripts/fcp_guard.py status
