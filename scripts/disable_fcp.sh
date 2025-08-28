#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."

REASON="${1:-'operator_request'}"

python3 scripts/fcp_guard.py deactivate "$REASON"
python3 scripts/fcp_guard.py status
