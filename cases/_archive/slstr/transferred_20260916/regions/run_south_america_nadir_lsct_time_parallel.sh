#!/usr/bin/env bash
set -u

SOURCE_ROOT="/media/hero/slstr-southA-lst"
REGION_FILE="/home/hero/work/ls4t/cases/slstr/regions/south_america_tropical_amazon.geojson"
SCRIPT="/home/hero/work/ls4t/cases/slstr/regions/south_america_daily_nadir_lsct_time.py"
OUTPUT_ROOT="/media/hero/slstr-southA-lst/south_america_tropical_nadir_lsct_time"
PYTHON="/home/hero/anaconda3/envs/env_311/bin/python3.11"
LOG_ROOT="/home/hero/work/ls4t/cases/slstr/regions/nadir_lsct_time_logs"
PARALLEL_YEARS="${PARALLEL_YEARS:-9}"

mkdir -p "$OUTPUT_ROOT" "$LOG_ROOT"

run_year() {
    local year="$1"
    local log="$LOG_ROOT/${year}.log"
    {
        echo "start $(date -Is) year=$year"
        "$PYTHON" "$SCRIPT" \
            --source-root "$SOURCE_ROOT" \
            --region-file "$REGION_FILE" \
            --output-root "$OUTPUT_ROOT" \
            --start-date "${year}-01-01" \
            --end-date "${year}-12-31" \
            --target-crs EPSG:6933 \
            --resolution-m 1000 \
            --overwrite
        status=$?
        echo "finish $(date -Is) year=$year status=$status"
        exit "$status"
    } >"$log" 2>&1
}

export SOURCE_ROOT REGION_FILE SCRIPT OUTPUT_ROOT PYTHON LOG_ROOT
export -f run_year

printf '%s\n' 2017 2018 2019 2020 2021 2022 2023 2024 2025 \
    | xargs -r -n 1 -P "$PARALLEL_YEARS" bash -c 'run_year "$1"' _

status=$?
echo "all years dispatched/completed $(date -Is) status=$status"
exit "$status"
