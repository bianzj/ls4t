# SLSTR Huailai scene processing

The 2024 source scenes are under
`/media/hero/slstr_heihe/huailai/2024/raw`. The pipeline preserves the raw
data and writes the standard `raw/tif/lst/lsct` hierarchy. The two-component
temperature file remains named `lsct2.tif` inside the `lsct` layer.

Exact scene products already available in the Heihe tree are reused through
directory symlinks. Coverage classification uses the Huailai County window
`115.26–115.98°E, 40.06–40.60°N`; cloud, water and no-coverage outcomes are
reported separately from processing failures.

Run with:

```bash
cases/slstr-huailai/stages/run_scene_pipeline.sh
```
