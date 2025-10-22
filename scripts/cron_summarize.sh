#!/bin/bash
set -euo pipefail
cd /opt/digestor
/opt/digestor/venv/bin/python cli.py summarize --limit 6 >> logs/cron_summarize.log 2>&1
