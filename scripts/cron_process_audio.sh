#!/bin/bash
set -euo pipefail
cd /opt/digestor
/opt/digestor/venv/bin/python cli.py process-audio --limit 4 >> logs/cron_process_audio.log 2>&1
