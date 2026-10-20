#!/usr/bin/env bash
set -euo pipefail

REPO="/home/hero/work/ls4t"
ROOT="/media/hero/slstr_heihe/huailai"
PYTHON="/home/hero/anaconda3/envs/env_311/bin/python3.11"
CASE="cases/slstr-huailai"
LOG_DIR="$ROOT/_inventory"
STATE="$LOG_DIR/pipeline.state"
WORKERS="${WORKERS:-4}"

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

stage reuse
"$PYTHON" -u "$CASE/stages/prepare_reuse.py"

stage tif_2024
LS4T_YEAR=2024 LS4T_DATA_ROOT="$ROOT" \
    "$PYTHON" -u cases/slstr/slstr_data_scene_origin.py

stage coverage_2024
"$PYTHON" -u cases/slstr/slstr_scene_coverage.py \
    --case "$CASE" --machine hero --year 2024 --write

stage lst_2024
"$PYTHON" -u cases/slstr/slstr_lst_scene_parallel.py \
    --root "$ROOT" --year 2024 --workers "$WORKERS" \
    --report "$LOG_DIR/lst_2024_report.json"

stage lsct_2024
"$PYTHON" -u cases/slstr/slstr_lsct2_scene_parallel.py \
    --root "$ROOT" --year 2024 --workers "$WORKERS" \
    --emis-dir /home/hero/data/rs/emissivity \
    --type-ref /home/hero/data/rs/land-cover/type/type_world_1000.tif \
    --report "$LOG_DIR/lsct_2024_report.json"

stage audit
"$PYTHON" -u "$CASE/stages/audit_outputs.py"

stage done
echo "=== Huailai scene pipeline complete $(date -Is) ==="
