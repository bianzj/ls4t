# Xizang SLSTR scene processing

The source ZIP files live directly in `<scene_root>/<year>`.  Processing keeps
the following visible hierarchy for every year:

```text
<year>/raw/<scene>.SEN3/
<year>/tif/<scene>.SEN3/
<year>/lst/<scene>.SEN3/
<year>/lsct/<scene>.SEN3/
```

The directory is consistently named `lsct`; the two-component product is
identified by its filename, `lsct2.tif`.

Run the inventory before extraction.  It records every duplicate before
deletion, checks geographic coverage, and creates read-only directory symlinks
for exact products already present in the Heihe tree.

```bash
PYTHONPATH=. /home/hero/anaconda3/envs/env_311/bin/python3.11 \
  cases/slstr-xizang/stages/inventory_and_reuse.py --delete-duplicates --apply
```

Then selectively extract only the required NetCDF members of selected local
archives:

```bash
PYTHONPATH=. /home/hero/anaconda3/envs/env_311/bin/python3.11 \
  cases/slstr-xizang/stages/stage_raw.py --workers 2
```
