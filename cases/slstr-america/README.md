# SLSTR America daily mosaic

南美（亚马逊focus）逐景优先案例。反演沿用 `cases/slstr/slstr_lst_scene_parallel.py`
（**保留云**）与 `cases/slstr/slstr_lsct2_scene_parallel.py`（反演内剔云，LAI 下限 0.05）。
现状是早期独立实现留下的 EPSG:6933 / 1 km 产物，本案例把它统一到与欧洲、黑河相同的
0.01° 网格后重跑拼接。

| 项 | 值 |
|---|---|
| 网格 | EPSG:4326，0.01°，4800 × 4500（-82–-34°E，-25–20°N） |
| 昼夜 | 景内中位太阳天顶角 < 90° 为 day（旧产物用 85°，本案例统一到 90°） |
| 产品 | `lst_nadir`、`lsct`（文件 `lsct2.tif`，2 波段）、`time`（HHMMSS）；`lst_obliq` 暂不输出 |
| 叠置 | 按获取时间，后景覆盖前景 |
| 云 | 反演保留云；拼接默认按 `cloud_{view}.tif` 剔云 |

当前状态 `draft`：先跑 2020 年与 `legacy_output_root` 做重投影后的对比，
确认除网格、昼夜阈值、剔云三处差异外一致，再决定是否全量重跑。

```bash
cd /home/hero/work/ls4t
PYTHONPATH=. python cases/slstr-america/run_standard_stage.py --list
```
