.gitignore lines

Add these so state/logs don’t clutter PRs:

# FCP runtime
Codex/System/fcp_state.yaml
Codex/System/logs/

Quick usage

# Activate FCP for 7 days with a reason
./scripts/enable_fcp.sh "regulatory_audit" 7

# Check (exit 10 when active, 12 if active+blocked)
python3 scripts/fcp_guard.py check && echo "OK to proceed" || echo "FCP gating"

# Deactivate
./scripts/disable_fcp.sh "audit_complete"

# Human-readable status (YAML)
./scripts/fcp_status.sh

These are intentionally minimalist and safe-by-default:
	•	If the activation window expires, fcp_guard.py will auto-deactivate and append an audit record.
	•	If policy.hard_block_on_active is set in your Codex/System/fcp.yaml, check exits with code 12 to allow upstream tools/CI to gate actions while FCP is active.
	•	Everything is file-based; no external services required.

 
