#!/bin/bash
set -euo pipefail
cd /opt/digestor
SINCE=$(date -u -d '3 days ago' +%F)
/opt/digestor/venv/bin/python cli.py discover --since "$SINCE" >> logs/cron_discover.log 2>&1
