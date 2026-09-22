#!/usr/bin/env bash
set -u

SOURCE_ROOT="/media/hero/slstr-southA-lst"
REGION_FILE="/home/hero/work/ls4t/cases/slstr/regions/south_america_tropical_amazon.geojson"
SCRIPT="/home/hero/work/ls4t/cases/slstr/regions/south_america_daily_nadir_lsct_time.py"
OUTPUT_ROOT="/media/hero/slstr-southA-lst/south_america_tropical_nadir_lsct_time"
PYTHON="/home/hero/anaconda3/envs/env_311/bin/python3.11"
LOG_ROOT="/home/hero/work/ls4t/cases/slstr/regions/nadir_lsct_time_logs"
CHECK_SECONDS=3600

run_year() {
    local year="$1"
    local manifest="$OUTPUT_ROOT/$year/manifest.json"
    local latest="$LOG_ROOT/${year}_restart_latest.log"
    local watch="$LOG_ROOT/${year}_hourly_watch.log"

    while [ ! -f "$manifest" ]; do
        local started
        started="$(date -Is)"
        echo "start year=$year time=$started" >>"$watch"
        "$PYTHON" "$SCRIPT" \
            --source-root "$SOURCE_ROOT" \
            --region-file "$REGION_FILE" \
            --output-root "$OUTPUT_ROOT" \
            --start-date "${year}-01-01" \
            --end-date "${year}-12-31" \
            --target-crs EPSG:6933 \
            --resolution-m 1000 \
            --overwrite >"$latest" 2>&1 &
        local pid=$!
        local elapsed=0
        while kill -0 "$pid" 2>/dev/null; do
            sleep 60
            elapsed=$((elapsed + 60))
            if [ "$elapsed" -ge "$CHECK_SECONDS" ]; then
                echo "hourly_check year=$year time=$(date -Is) pid=$pid" >>"$watch"
                if rg -n "Traceback|RuntimeError|Cannot create|Warp failed|No usable" "$latest" >>"$watch" 2>&1; then
                    echo "error_pattern_found year=$year time=$(date -Is)" >>"$watch"
                else
                    echo "no_error_pattern year=$year time=$(date -Is)" >>"$watch"
                fi
                elapsed=0
            fi
        done
        wait "$pid"
        local status=$?
        echo "exit year=$year status=$status time=$(date -Is)" >>"$watch"
        if [ "$status" -eq 0 ] && [ -f "$manifest" ]; then
            echo "complete year=$year time=$(date -Is)" >>"$watch"
            break
        fi
        echo "restart_after_failure year=$year next_check=$(date -Is -d '+1 hour')" >>"$watch"
        sleep "$CHECK_SECONDS"
    done
}

mkdir -p "$LOG_ROOT"
export -f run_year
export SOURCE_ROOT REGION_FILE SCRIPT OUTPUT_ROOT PYTHON LOG_ROOT CHECK_SECONDS

run_year 2019 & pid_2019=$!
run_year 2023 & pid_2023=$!
wait "$pid_2019"
status_2019=$?
wait "$pid_2023"
status_2023=$?
echo "all_restarted_years_complete time=$(date -Is) status_2019=$status_2019 status_2023=$status_2023"
exit $((status_2019 != 0 || status_2023 != 0))
