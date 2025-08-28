# QSecure – Dev Notes

## Commands

- **Status**
  ```bash
  python3 scripts/qsecure_status.py          # human line
  python3 scripts/qsecure_status.py --json   # machine JSON

  Rotate (local)

  python3 scripts/rotate_qkeys.py --reason "weekly" --commit

  Enforce in CI

  python3 scripts/enforce_qpolicies.py && echo "OK to proceed"

  CI wiring (GitHub Actions)

  # .github/workflows/qsecure.yml
name: QSecure Gate
on: [push, workflow_dispatch]
jobs:
  guard:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with: { python-version: '3.11' }
      - run: pip install pyyaml
      - run: python3 scripts/enforce_qpolicies.py

Notes
	•	Real QKD integration should update qsecure.endpoints.qkd.status and last_rotation_ts from the KMS API.
	•	If policies.require_quantum_ok is true, WARN (grace) still passes; FAIL blocks.
	•	Rotation cadence is governed by policies.rotation_days + grace_hours.

 ---

### Quick add/commit helper (optional)
Make executable with `chmod +x scripts/qsecure_quickcheck.sh`.

```bash
#!/usr/bin/env bash
# scripts/qsecure_quickcheck.sh
set -euo pipefail
python3 scripts/qsecure_status.py || true

Drop-in steps (one time)

# from your repo root
mkdir -p scripts reports Codex/System
# save the three .py files and the DEV_NOTES.md as shown above

chmod +x scripts/qsecure_status.py scripts/rotate_qkeys.py scripts/enforce_qpolicies.py

# try it
python3 scripts/qsecure_status.py --verbose
python3 scripts/rotate_qkeys.py --reason "initialization" --commit
python3 scripts/enforce_qpolicies.py

# GitHub Actions workflow that runs a weekly rotation and commits the bumped key id.
#GitHub Actions workflow that rotates the QSecure key weekly, updates Codex/System/QSecure.yaml, and commits the bumped active_key_id back to main if anything changed.

Save this as: .github/workflows/qsecure-rotate.yml

name: QSecure Weekly Rotation

on:
  schedule:
    # Every Monday at 03:00 UTC — adjust as you like
    - cron: "0 3 * * 1"
  workflow_dispatch: {}

permissions:
  contents: write  # required to push changes

concurrency:
  group: qsecure-rotate
  cancel-in-progress: false

jobs:
  rotate:
    runs-on: ubuntu-latest

    steps:
      - name: Checkout
        uses: actions/checkout@v4
        with:
          persist-credentials: true
          fetch-depth: 0

      - name: Set up Python
        uses: actions/setup-python@v5
        with:
          python-version: "3.11"

      - name: Install deps
        run: |
          python -m pip install --upgrade pip
          pip install pyyaml

      - name: Rotate QSecure key
        run: |
          python scripts/qsecure_rotate.py --config Codex/System/QSecure.yaml --bump

      - name: Configure Git user
        run: |
          git config user.name "github-actions[bot]"
          git config user.email "41898282+github-actions[bot]@users.noreply.github.com"

      - name: Commit changes (if any)
        run: |
          if ! git diff --quiet -- Codex/System/QSecure.yaml; then
            git add Codex/System/QSecure.yaml
            ts="$(date -u +"%Y-%m-%dT%H:%M:%SZ")"
            git commit -m "QSecure: weekly key rotation (${ts})"
          else
            echo "No changes to QSecure.yaml — nothing to commit."
          fi

      - name: Push
        if: success()
        run: |
          if git log -1 --pretty=%B | grep -q "QSecure: weekly key rotation"; then
            git push origin HEAD:main
          else
            echo "No commit created; skipping push."
          fi

#Quick checklist:
	•	Ensure the rotation script exists at scripts/qsecure_rotate.py and supports:
	•	--config Codex/System/QSecure.yaml
	•	--bump (rotates to the next key and updates active_key_id, rotated_at, optional next_rotation_at)
	•	Confirm Codex/System/QSecure.yaml is in the repo (and on main).
	•	No extra secrets are required; the default GITHUB_TOKEN with contents: write is enough.

If you prefer a different day/time, tweak the cron line. Want a different branch (e.g., dev)? Change git push origin HEAD:main to your target branch.



