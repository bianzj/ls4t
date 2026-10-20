#!/usr/bin/env bash
set -euo pipefail

REPO="/home/hero/work/ls4t"
ROOT="/media/hero/slstr_heihe/xizang"
PYTHON="/home/hero/anaconda3/envs/env_311/bin/python3.11"
CASE="cases/slstr-xizang"
LOG_DIR="$ROOT/_inventory"
STATE="$LOG_DIR/pipeline.state"
# LSCT workers touch a large, scene-derived auxiliary window.  Eight workers
# repeatedly triggered systemd-oomd on this machine.  Four workers provide
# moderate parallelism below that failed setting; the pipeline is resumable.
WORKERS="${WORKERS:-4}"
RAW_WORKERS="${RAW_WORKERS:-2}"

mkdir -p "$LOG_DIR"
exec >>"$LOG_DIR/pipeline.log" 2>&1
cd "$REPO"
export PYTHONPATH=.
export PROJ_LIB=/usr/share/proj
export PYTHONUNBUFFERED=1
export OMP_NUM_THREADS=1
export OPENBLAS_NUM_THREADS=1
export MKL_NUM_THREADS=1
export NUMEXPR_NUM_THREADS=1

stage() {
    printf '%s %s\n' "$1" "$(date -Is)" >"$STATE"
    echo "=== $1 $(date -Is) ==="
}

stage raw
"$PYTHON" -u "$CASE/stages/stage_raw.py" --workers "$RAW_WORKERS" \
    --report "$LOG_DIR/raw_stage_report.json"

stage tif_2017
LS4T_YEAR=2017 LS4T_DATA_ROOT="$ROOT" "$PYTHON" -u cases/slstr/slstr_data_scene_origin.py
stage tif_2018
LS4T_YEAR=2018 LS4T_DATA_ROOT="$ROOT" "$PYTHON" -u cases/slstr/slstr_data_scene_origin.py

for year in 2017 2018; do
    stage "coverage_${year}"
    "$PYTHON" -u cases/slstr/slstr_scene_coverage.py \
        --case "$CASE" --machine hero --year "$year" --write

    stage "lst_${year}"
    "$PYTHON" -u cases/slstr/slstr_lst_scene_parallel.py \
        --root "$ROOT" --year "$year" --workers "$WORKERS" \
        --report "$LOG_DIR/lst_${year}_report.json"

    stage "lsct_${year}"
    "$PYTHON" -u cases/slstr/slstr_lsct2_scene_parallel.py \
        --root "$ROOT" --out-layer lsct --year "$year" --workers "$WORKERS" \
        --emis-dir /home/hero/data/rs/emissivity \
        --type-ref /home/hero/data/rs/land-cover/type/type_world_1000.tif \
        --report "$LOG_DIR/lsct_${year}_report.json"
done

stage audit
"$PYTHON" -u "$CASE/stages/audit_outputs.py" --report "$LOG_DIR/final_audit.json"
stage done
echo "=== Xizang scene pipeline complete $(date -Is) ==="
