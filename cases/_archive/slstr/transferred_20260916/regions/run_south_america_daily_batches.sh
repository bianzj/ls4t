#!/usr/bin/env bash
set -euo pipefail

python_bin="/home/hero/anaconda3/envs/env_311/bin/python3.11"
script="/home/hero/work/ls4t/cases/slstr/regions/south_america_daily_mosaic.py"
source_root="/media/hero/slstr-southA-lst"
region_file="/home/hero/work/ls4t/cases/slstr/regions/south_america_tropical_amazon.geojson"
output_root="/media/hero/slstr-southA-lst/south_america_tropical_daily_0p01"

for date_range in "2017-01-01 2021-12-31" "2022-01-01 2025-12-31"; do
    read -r start_date end_date <<< "$date_range"
    "$python_bin" -u "$script" \
        --source-root "$source_root" \
        --region-file "$region_file" \
        --output-root "$output_root" \
        --start-date "$start_date" \
        --end-date "$end_date"
done
