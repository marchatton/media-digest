#!/bin/bash
set -euo pipefail

echo "== Media Digest Hetzner rollout =="

cd /opt/digestor

echo "[1/3] Pulling latest code..."
git pull --ff-only

echo "[2/3] Backing up current crontab..."
if crontab -l > /root/crontab.backup.$(date -u +%F_%H%M%S) 2>/dev/null; then
  echo "Saved crontab backup to /root/crontab.backup.*"
else
  echo "No existing crontab found (ok)"
fi

echo "[3/3] Applying new cron jobs..."
crontab /opt/digestor/scripts/cron_jobs.txt

echo "Cron installed. Current entries:"
crontab -l

echo "Done."

