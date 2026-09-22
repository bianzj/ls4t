#!/usr/bin/env bash
# Daily LST / LSCT2 mosaic for this case.
#
#   bash cases/slstr-heihe/stages/run_daily_mosaic.sh 2017 2018 ... 2025
#
# The window, product list, day/night rule and cloud policy come from
# case.toml; the data and output roots come from machines/<machine>.toml.
set -u

REPO="/home/hero/work/ls4t"
CASE="cases/slstr-heihe"
PYTHON="${PYTHON:-/home/hero/anaconda3/envs/env_311/bin/python3.11}"
WORKERS="${WORKERS:-16}"
MACHINE="${MACHINE:-hero}"
LOG_DIR="${LOG_DIR:-/tmp}"
EXTRA="${EXTRA:-}"
export CPL_TMPDIR="${CPL_TMPDIR:-/tmp}"

cd "$REPO" || exit 1
for year in "$@"; do
    echo "=== ${year} start $(date -Is)"
    PYTHONPATH=. PROJ_LIB=/usr/share/proj "$PYTHON" -u \
        "$CASE/../../cases/slstr/slstr_daily_mosaic_scene.py" \
        --case "$CASE" --machine "$MACHINE" --year "$year" --workers "$WORKERS" \
        $EXTRA \
        > "$LOG_DIR/heihe_daily_${year}.log" 2>&1
    status=$?
    echo "=== ${year} exit=${status} $(date -Is)"
    [ "$status" -eq 0 ] || exit "$status"
done
echo "=== all years finished $(date -Is)"
