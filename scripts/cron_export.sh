#!/bin/bash
set -euo pipefail
cd /opt/digestor
/opt/digestor/venv/bin/python cli.py export >> logs/cron_export.log 2>&1
