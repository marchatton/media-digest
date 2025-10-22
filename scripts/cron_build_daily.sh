#!/bin/bash
set -euo pipefail
cd /opt/digestor
/opt/digestor/venv/bin/python cli.py build-daily --date today >> logs/cron_daily.log 2>&1
