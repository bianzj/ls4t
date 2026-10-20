#!/usr/bin/env bash
set -euo pipefail

LOG_DIR=/home/hero/work/ls4t/cases/slstr/logs/amazon_then_europe_homogeneous
OLD=ls4t-amazon-then-europe-homogeneous-20261011.service
NEW=ls4t-amazon-then-europe-homogeneous-adaptive-20261011.service
STATUS="$LOG_DIR/status.tsv"

echo "[$(date -Is)] Waiting for Amazon 2018 LST to finish before adaptive handoff"
while ! awk -F '\t' '$1=="amazon" && $2=="2018" && $3=="lst" && $4=="0" {ok=1} END {exit !ok}' "$STATUS"; do
    if ! systemctl --user is-active --quiet "$OLD"; then
        echo "[$(date -Is)] Old service stopped before Amazon 2018 LST completed" >&2
        exit 3
    fi
    sleep 3
done
echo "[$(date -Is)] Amazon 2018 LST verified; stopping old launcher"
systemctl --user stop "$OLD"
if systemctl --user is-active --quiet "$OLD"; then
    echo "[$(date -Is)] Old launcher remains active" >&2
    exit 4
fi
echo "[$(date -Is)] Starting adaptive launcher"
systemd-run --user --unit="$NEW" --working-directory=/home/hero/work/ls4t \
    /bin/bash -c 'exec bash /home/hero/work/ls4t/cases/slstr/run_amazon_then_europe_homogeneous.sh >> /home/hero/work/ls4t/cases/slstr/logs/amazon_then_europe_homogeneous/run.log 2>&1'
