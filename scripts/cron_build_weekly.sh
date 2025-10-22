#!/bin/bash
set -euo pipefail
cd /opt/digestor
/opt/digestor/venv/bin/python cli.py build-weekly --ending today >> logs/cron_weekly.log 2>&1
