#!/bin/bash

# harmony-backup.sh — lightweight wrapper to call full backup
cd "$(dirname "$0")" || exit 1

echo "[Backup] Started at $(date)"

./harmony-backup-full.sh

echo "[Backup] Finished at $(date)"
