#!/usr/bin/env bash
set -euo pipefail

python_bin="/home/hero/anaconda3/envs/env_311/bin/python3.11"
script="/home/hero/work/ls4t/cases/slstr/regions/south_america_daily_mosaic_gdalwarp.py"
source_root="/media/hero/slstr-southA-lst"
region_file="/home/hero/work/ls4t/cases/slstr/regions/south_america_tropical_amazon.geojson"
output_root="/media/hero/slstr-southA-lst/south_america_tropical_daily_projected_daynight"

for year in "$@"; do
    "$python_bin" -u "$script" \
        --source-root "$source_root" \
        --region-file "$region_file" \
        --output-root "$output_root" \
        --start-date "${year}-01-01" \
        --end-date "${year}-12-31"
done
