#!/usr/bin/env bash
set -euo pipefail

LOG=/home/hero/work/ls4t/cases/slstr/logs/amazon_then_europe_homogeneous
OLD=ls4t-amazon-europe-lai-only-cachetrim-20261012.service
NEW=ls4t-amazon-europe-annual-batch-20261013.service
REPORT="$LOG/europe_2023_lst.json"

echo "[$(date -Is)] Waiting for verified Europe 2023 LST before annual batch handoff"
while true; do
    if awk -F '\t' '$1=="europe" && $2=="2023" && $3=="lst" && $4=="0" {ok=1} END {exit !ok}' "$LOG/status.tsv"; then
        /home/hero/anaconda3/envs/env_311/bin/python - "$REPORT" <<'PY'
import json,sys
from pathlib import Path
d=json.loads(Path(sys.argv[1]).read_text())
assert d['year']==2023 and d['scenes']>0
assert d['skipped']==0 and len(d['updated_scenes'])==d['scenes']
assert all(not day.get('error') for day in d['days_report'])
PY
        break
    fi
    if ! systemctl --user is-active --quiet "$OLD"; then
        echo "[$(date -Is)] Old service stopped before Europe 2023 LST completed" >&2
        exit 3
    fi
    sleep 2
done

echo "[$(date -Is)] Europe 2023 LST verified; stopping old launcher"
systemctl --user stop "$OLD"
if systemctl --user is-active --quiet "$OLD"; then
    echo "[$(date -Is)] Old launcher remains active" >&2
    exit 4
fi
echo "[$(date -Is)] Starting annual LST-then-components batch"
systemd-run --user --unit="$NEW" --working-directory=/home/hero/work/ls4t \
    /bin/bash -c 'exec /home/hero/anaconda3/envs/env_311/bin/python /home/hero/work/ls4t/cases/slstr/run_amazon_europe_annual.py >> /home/hero/work/ls4t/cases/slstr/logs/amazon_then_europe_homogeneous/annual_run.log 2>&1'
