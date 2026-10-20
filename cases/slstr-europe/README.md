# SLSTR Europe daily mosaic

欧洲 + 北非逐景优先案例。反演沿用 `cases/slstr/slstr_lst_scene_parallel.py`
（**保留云**）与 `cases/slstr/slstr_lsct2_scene_parallel.py`（反演内剔云，LAI 下限 0.05），
拼接把逐景结果按 UTC 日、昼/夜合成到统一网格。

| 项 | 值 |
|---|---|
| 网格 | EPSG:4326，0.01°，5400 × 4150（-12–42°E，30–71.5°N） |
| 昼夜 | 景内中位太阳天顶角 < 90° 为 day |
| 产品 | `lst_nadir`、`lsct`（文件 `lsct2.tif`，2 波段）、`time`（HHMMSS）；`lst_obliq` 暂不输出 |
| 叠置 | 按获取时间，后景覆盖前景 |
| 云 | 反演保留云；拼接默认按 `cloud_{view}.tif` 剔云 |

现有 `euro_daily_0p01` 是旧口径产物（未剔云、LSCT2 为 float32、LAI 0.25）。
本案例状态 `draft`：先用 2020 年与旧产物逐值比对，确认差异只来自这三处口径变化后
再重跑全量。

```bash
cd /home/hero/work/ls4t
PYTHONPATH=. python cases/slstr-europe/run_standard_stage.py --list
```
