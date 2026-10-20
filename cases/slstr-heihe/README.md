# SLSTR Heihe daily mosaic

黑河（黑河流域：祁连山—额济纳）逐景优先案例。反演阶段沿用
`cases/slstr/slstr_lst_scene_parallel.py`（**保留云**）与
`cases/slstr/slstr_lsct2_scene_parallel.py`（反演内剔云，LAI 下限 0.05），
拼接阶段把逐景结果按 UTC 日、昼/夜合成到统一网格。

| 项 | 值 |
|---|---|
| 网格 | EPSG:4326，0.01°，625 × 575（96.60–102.85°E，37.34–43.09°N） |
| 昼夜 | 景内中位太阳天顶角 < 90° 为 day |
| 产品 | `lst_nadir`、`lsct`（文件 `lsct2.tif`，2 波段）、`time`（HHMMSS）；`lst_obliq` 暂不输出 |
| 叠置 | 按获取时间，后景覆盖前景 |
| 云 | 反演保留云；拼接默认按 `cloud_{view}.tif` 剔云 |

当前状态 `draft`：配置已定，`stages/` 与共享拼接模块尚未接入，等实现并完成
2020 年逐值比对后升为 `active`。

```bash
cd /home/hero/work/ls4t
PYTHONPATH=. python cases/slstr-heihe/run_standard_stage.py --list
```
