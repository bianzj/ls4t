#!/usr/bin/env bash
set -u -o pipefail

cd /home/hero/work/ls4t || exit 2
export OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 MKL_NUM_THREADS=1
export PROJ_LIB=/usr/share/proj PROJ_DATA=/usr/share/proj
PY=/home/hero/anaconda3/envs/env_311/bin/python
LOG_DIR=/home/hero/work/ls4t/cases/slstr/logs/amazon_europe_lst_only
PREVIOUS=/home/hero/work/ls4t/cases/slstr/logs/amazon_europe_bayes3
mkdir -p "$LOG_DIR"
exec 9>"$LOG_DIR/run.lock"
if ! flock -n 9; then
    echo "LST-only run already active" >&2
    exit 2
fi
printf 'region\tyear\tstage\texit_code\treport\n' > "$LOG_DIR/status.tsv"
failed=0

report_complete() {
    "$PY" - "$1" "$2" "$3" "$4" "$5" "$6" "$7" <<'PY'
import json,sys
from pathlib import Path
try:
    p=Path(sys.argv[1]);d=json.loads(p.read_text())
    root=Path(sys.argv[2]).resolve();year=int(sys.argv[3])
    bounds=[float(x) for x in sys.argv[4:8]]
    ok=(d.get('year')==year and Path(d.get('root','')).resolve()==root
        and d.get('bounds_wsen')==bounds
        and len(d.get('updated_scenes',[]))==d.get('scenes')
        and d.get('skipped')==0
        and all(day.get('error') is None for day in d.get('days_report',[])))
except (OSError,ValueError,KeyError):
    ok=False
sys.exit(0 if ok else 1)
PY
}

for year in {2017..2025}; do
    for region in amazon europe; do
        if [[ "$region" == amazon ]]; then
            root=/media/hero/slstr-southA-lst
            bounds=(-80 -18 -44 12)
        else
            root=/media/hero/slstr-euro-lst
            bounds=(-12 30 42 71.5)
        fi
        report="$LOG_DIR/${region}_${year}_lst.json"
        if [[ "$region" == amazon && "$year" == 2017 && ! -s "$report" ]]; then
            report="$PREVIOUS/amazon_2017_lst.json"
        fi
        if report_complete "$report" "$root" "$year" "${bounds[@]}"; then
            echo "[$(date -Is)] VERIFIED PRIOR LST $region $year report=$report"
            printf '%s\t%s\tlst_verified\t0\t%s\n' "$region" "$year" "$report" >> "$LOG_DIR/status.tsv"
            continue
        fi
        report="$LOG_DIR/${region}_${year}_lst.json"
        echo "[$(date -Is)] START LST $region $year bounds=${bounds[*]}"
        "$PY" -m cases.slstr.slstr_lst_scene_parallel \
            --root "$root" --year "$year" --bounds "${bounds[@]}" \
            --workers 12 --all-scenes --overwrite --report "$report"
        rc=$?
        if (( rc == 0 )) && ! report_complete "$report" "$root" "$year" "${bounds[@]}"; then
            rc=3
        fi
        printf '%s\t%s\tlst\t%s\t%s\n' "$region" "$year" "$rc" "$report" >> "$LOG_DIR/status.tsv"
        echo "[$(date -Is)] END LST $region $year exit=$rc report=$report"
        if (( rc != 0 )); then failed=$((failed+1)); fi
    done
done
echo "[$(date -Is)] LST-ONLY FINISHED incomplete_years=$failed"
if (( failed )); then exit 3; fi
