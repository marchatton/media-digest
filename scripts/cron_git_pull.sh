#!/bin/bash
set -euo pipefail
cd /opt/digestor/output
/usr/bin/git pull --ff-only >> /opt/digestor/logs/cron_git_pull.log 2>&1
