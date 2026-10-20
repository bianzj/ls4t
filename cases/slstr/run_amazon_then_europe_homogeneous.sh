#!/usr/bin/env bash
set -u -o pipefail

cd /home/hero/work/ls4t || exit 2
export OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 MKL_NUM_THREADS=1
export PROJ_LIB=/usr/share/proj PROJ_DATA=/usr/share/proj
PY=/home/hero/anaconda3/envs/env_311/bin/python
LOG_DIR=/home/hero/work/ls4t/cases/slstr/logs/amazon_then_europe_homogeneous
PREVIOUS=/home/hero/work/ls4t/cases/slstr/logs/amazon_europe_bayes3
LST_ONLY=/home/hero/work/ls4t/cases/slstr/logs/amazon_europe_lst_only
ADAPTIVE=/home/hero/work/ls4t/cases/slstr/adaptive_year_run.py
ADAPTIVE_LOG="$LOG_DIR/adaptive_workers.jsonl"
EXCLUSION_2023=/home/hero/work/ls4t/cases/slstr/amazon_2023_unreadable_inputs.json
mkdir -p "$LOG_DIR"
exec 9>"$LOG_DIR/run.lock"
if ! flock -n 9; then
    echo "Another phased Amazon/Europe run is active" >&2
    exit 2
fi
printf 'region\tyear\tstage\texit_code\treport\n' > "$LOG_DIR/status.tsv"

report_ok() {
    "$PY" - "$1" "$2" "$3" "$4" "$5" "$6" "$7" "$8" "${9:-}" <<'PY'
import json,sys
from pathlib import Path
stage,path,root,year,*rest=sys.argv[1:]
bounds=rest[:4]
exclusion_file=rest[4]
try:
    d=json.loads(Path(path).read_text())
    ok=(d.get('year')==int(year) and Path(d.get('root','')).resolve()==Path(root).resolve()
        and d.get('bounds_wsen')==[float(v) for v in bounds])
    if stage=='lst':
        expected=(json.loads(Path(exclusion_file).read_text())['scenes'] if exclusion_file else [])
        ok &= (d.get('scenes',0)>0 and len(d.get('updated_scenes',[]))==d.get('scenes')
            and d.get('skipped')==0
            and d.get('excluded_scenes',[])==sorted(set(expected))
            and all(day.get('error') is None for day in d.get('days_report',[])))
    else:
        ok &= (d.get('method')=='homogeneous_3component_bayes_map_5x5_lai_only_v5'
            and d.get('complete') is True and d.get('done')==d.get('queued')
            and not d.get('errors') and d.get('counts',{}).get('missing_input',0)==0)
except (OSError,ValueError,KeyError,TypeError):
    ok=False
sys.exit(0 if ok else 1)
PY
}

run_region_lst() {
    local region="$1" root="$2" year report rc disk exclusion_file
    local -a exclude_scenes=()
    shift 2
    if [[ "$region" == amazon ]]; then disk=sda; else disk=sdb; fi
    local -a bounds=("$@")
    for year in {2017..2025}; do
        exclusion_file=""
        exclude_scenes=()
        if [[ "$region:$year" == amazon:2023 ]]; then
            exclusion_file="$EXCLUSION_2023"
            mapfile -t exclude_scenes < <("$PY" -c 'import json,sys;print(*json.load(open(sys.argv[1]))["scenes"],sep="\n")' "$exclusion_file")
        fi
        report="$LOG_DIR/${region}_${year}_lst.json"
        if [[ "$region:$year" == amazon:2017 ]]; then
            report="$PREVIOUS/amazon_2017_lst.json"
        elif [[ "$region:$year" == europe:2017 ]]; then
            report="$LST_ONLY/europe_2017_lst.json"
        fi
        if report_ok lst "$report" "$root" "$year" "${bounds[@]}" "$exclusion_file"; then
            echo "[$(date -Is)] VERIFIED LST $region $year report=$report"
            printf '%s\t%s\tlst_verified\t0\t%s\n' "$region" "$year" "$report" >> "$LOG_DIR/status.tsv"
            continue
        fi
        report="$LOG_DIR/${region}_${year}_lst.json"
        echo "[$(date -Is)] START LST $region $year bounds=${bounds[*]} adaptive_workers"
        "$PY" "$ADAPTIVE" --region "$region" --stage lst --year "$year" \
            --disk "$disk" --report "$report" --history "$ADAPTIVE_LOG" -- \
            "$PY" -m cases.slstr.slstr_lst_scene_parallel \
            --root "$root" --year "$year" --bounds "${bounds[@]}" \
            --workers '{workers}' --all-scenes --overwrite --exclude-scenes "${exclude_scenes[@]}" --report "$report"
        rc=$?
        if (( rc==0 )) && ! report_ok lst "$report" "$root" "$year" "${bounds[@]}" "$exclusion_file"; then rc=3; fi
        printf '%s\t%s\tlst\t%s\t%s\n' "$region" "$year" "$rc" "$report" >> "$LOG_DIR/status.tsv"
        echo "[$(date -Is)] END LST $region $year exit=$rc report=$report"
        if (( rc!=0 )); then return "$rc"; fi
    done
}

run_region_components() {
    local region="$1" root="$2" year lst_report report rc disk exclusion_file
    shift 2
    if [[ "$region" == amazon ]]; then disk=sda; else disk=sdb; fi
    local -a bounds=("$@")
    for year in {2017..2025}; do
        exclusion_file=""
        if [[ "$region:$year" == amazon:2023 ]]; then exclusion_file="$EXCLUSION_2023"; fi
        lst_report="$LOG_DIR/${region}_${year}_lst.json"
        if [[ "$region:$year" == amazon:2017 ]]; then
            lst_report="$PREVIOUS/amazon_2017_lst.json"
        elif [[ "$region:$year" == europe:2017 ]]; then
            lst_report="$LST_ONLY/europe_2017_lst.json"
        fi
        if ! report_ok lst "$lst_report" "$root" "$year" "${bounds[@]}" "$exclusion_file"; then
            echo "[$(date -Is)] STOP: LST not complete for $region $year"
            return 3
        fi
        report="$LOG_DIR/${region}_${year}_components.json"
        if [[ "$region:$year" == amazon:2017 ]]; then
            report="$PREVIOUS/amazon_2017_components.json"
        fi
        if report_ok components "$report" "$root" "$year" "${bounds[@]}"; then
            echo "[$(date -Is)] VERIFIED COMPONENTS $region $year report=$report"
            printf '%s\t%s\tcomponents_verified\t0\t%s\n' "$region" "$year" "$report" >> "$LOG_DIR/status.tsv"
            continue
        fi
        report="$LOG_DIR/${region}_${year}_components.json"
        echo "[$(date -Is)] START HOMOGENEOUS COMPONENTS $region $year adaptive_workers"
        "$PY" "$ADAPTIVE" --region "$region" --stage components --year "$year" \
            --disk "$disk" --report "$report" --history "$ADAPTIVE_LOG" -- \
            "$PY" -m cases.slstr.slstr_lsct3_bayes_scene \
            --root "$root" --year "$year" --bounds "${bounds[@]}" \
            --lst-report "$lst_report" --workers '{workers}' --report "$report"
        rc=$?
        if (( rc==0 )) && ! report_ok components "$report" "$root" "$year" "${bounds[@]}"; then rc=3; fi
        printf '%s\t%s\tcomponents\t%s\t%s\n' "$region" "$year" "$rc" "$report" >> "$LOG_DIR/status.tsv"
        echo "[$(date -Is)] END COMPONENTS $region $year exit=$rc report=$report"
        if (( rc!=0 )); then return "$rc"; fi
    done
}

run_region_lst amazon /media/hero/slstr-southA-lst -80 -18 -44 12 || exit $?
run_region_components amazon /media/hero/slstr-southA-lst -80 -18 -44 12 || exit $?
run_region_lst europe /media/hero/slstr-euro-lst -12 30 42 71.5 || exit $?
run_region_components europe /media/hero/slstr-euro-lst -12 30 42 71.5 || exit $?
echo "[$(date -Is)] ALL FOUR PHASES COMPLETE"
