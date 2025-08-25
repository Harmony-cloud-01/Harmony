#!/bin/bash

# harmony-backup.sh — lightweight wrapper to call full backup
# Safe for crontab execution

cd "$(dirname "$0")" || exit 1

# Timestamp for logging
echo "[Backup] Started at $(date)"

# Execute full backup
./harmony-backup-full.sh

echo "[Backup] Finished at $(date)"
