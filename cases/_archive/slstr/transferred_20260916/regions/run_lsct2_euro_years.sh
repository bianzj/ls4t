#!/usr/bin/env bash
# Complete the missing scene-first LSCT2 products of the slstr-euro-lst disk.
#
#   bash cases/slstr/regions/run_lsct2_euro_years.sh 2017 2025
#
# Years are processed one after another (the data disk is the bottleneck, so
# running them in parallel does not help).  The driver skips scenes that
# already have an lsct2.tif, so re-running a year is safe and resumes.
set -u

ROOT="/home/hero/work/ls4t"
PYTHON="${PYTHON:-/home/hero/anaconda3/envs/env_311/bin/python3}"
WORKERS="${WORKERS:-48}"

cd "$ROOT" || exit 1
for year in "$@"; do
    echo "=== ${year} start $(date -Is)"
    PYTHONPATH=. PROJ_LIB=/usr/share/proj "$PYTHON" -u \
        cases/slstr/implementation/one_by_one/slstr_lsct2_parallel.py \
        --year "$year" --workers "$WORKERS" \
        --report "cases/slstr/regions/lsct2_${year}_completion.json" \
        > "/tmp/lsct2_${year}_run.log" 2>&1
    status=$?
    echo "=== ${year} exit=${status} $(date -Is)"
    [ "$status" -eq 0 ] || exit "$status"
done
echo "=== all years finished $(date -Is)"
