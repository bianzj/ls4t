#!/usr/bin/env bash
set -u -o pipefail

# Overwrite in-place only after a two-view LST report confirms fresh results.
# Per-year reports and scene markers make an interrupted run auditable.
cd /home/hero/work/ls4t || exit 2
export OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 MKL_NUM_THREADS=1
export PROJ_LIB=/usr/share/proj PROJ_DATA=/usr/share/proj
PY=/home/hero/anaconda3/envs/env_311/bin/python
LOG_DIR=/home/hero/work/ls4t/cases/slstr/logs/amazon_europe_bayes3
mkdir -p "$LOG_DIR"
exec 9>"$LOG_DIR/run.lock"
if ! flock -n 9; then
    echo "Another Amazon/Europe Bayesian run holds $LOG_DIR/run.lock" >&2
    exit 2
fi
printf 'region\tyear\tstage\texit_code\treport\n' > "$LOG_DIR/status.tsv"
failed=0

for year in {2017..2025}; do
    for region in amazon europe; do
        if [[ "$region" == amazon ]]; then
            root=/media/hero/slstr-southA-lst
            bounds=(-80 -18 -44 12)
        else
            root=/media/hero/slstr-euro-lst
            bounds=(-12 30 42 71.5)
        fi
        lst_report="$LOG_DIR/${region}_${year}_lst.json"
        component_report="$LOG_DIR/${region}_${year}_components.json"
        echo "[$(date -Is)] START $region $year LST bounds=${bounds[*]}"
        "$PY" -m cases.slstr.slstr_lst_scene_parallel \
            --root "$root" --year "$year" --bounds "${bounds[@]}" \
            --workers 12 --all-scenes --overwrite --report "$lst_report"
        rc=$?
        printf '%s\t%s\tlst\t%s\t%s\n' "$region" "$year" "$rc" "$lst_report" >> "$LOG_DIR/status.tsv"
        if (( rc != 0 )) || [[ ! -s "$lst_report" ]]; then
            echo "[$(date -Is)] FAILED $region $year LST; component stage skipped"
            failed=$((failed+1))
            continue
        fi
        echo "[$(date -Is)] START $region $year three-component homogeneous Bayesian"
        "$PY" -m cases.slstr.slstr_lsct3_bayes_scene \
            --root "$root" --year "$year" --bounds "${bounds[@]}" \
            --lst-report "$lst_report" --workers 12 --report "$component_report"
        rc=$?
        printf '%s\t%s\tcomponents\t%s\t%s\n' "$region" "$year" "$rc" "$component_report" >> "$LOG_DIR/status.tsv"
        if (( rc != 0 )); then failed=$((failed+1)); fi
        echo "[$(date -Is)] END $region $year component_exit=$rc"
    done
done
echo "[$(date -Is)] FINISHED incomplete_stages=$failed status=$LOG_DIR/status.tsv"
if (( failed )); then exit 3; fi
