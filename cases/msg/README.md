# MSG cases

MSG 只保留真实在跑、并且反演链真正用到的环节，各自一个脚本，扁平放在本目录，项目代码
只从根目录 `base/` 导入；没有 `support/` 夹层、没有 `import *`、没有 `sys.path` 技巧。
月合成、站点验证、绘图和旧版本反演脚本都移到
`cases/_archive/msg/transferred_20260916/`。

| 环节 | 脚本 | 来源 |
| --- | --- | --- |
| LAI/MDLAI 下载 | `msg_download.py` | 运行项目 `cases/implementation/msg-download.py` |
| 提取（欧洲盘） | `msg_extract_euro.py` | 运行项目 `cases/ingest/msg_data_euro.py` |
| 提取（IODC 盘） | `msg_extract_iodc.py` | 运行项目 `cases/ingest/msg_data_iodc.py` |
| 投影（欧洲盘） | `msg_project_euro.py` | 运行项目 `cases/implementation/msg_proj_hdf5-euro.py` |
| 投影（欧洲盘 LAI） | `msg_project_euro_lai.py` | 运行项目 `cases/implementation/msg_proj_hdf5-euro-lai.py` |
| 投影（IODC 盘） | `msg_project_iodc.py` | 运行项目 `cases/implementation/msg_proj_hdf5-iodc.py` |
| LST 拟合/反演 | `msg_lst_fit.py` | 运行项目 `cases/ingest/msg_data_lst_euro.py` |
| LSCT 反演（在用版） | `msg_lsct_iter.py` | 运行项目 `cases/implementation/msg_lsct3.2-iter.py` |
| 站点抽取（LST/角度） | `msg_site_extract_lst.py` | 运行项目 `cases/validation/extract_point_lst_from_msg.py` |
| 站点抽取（LAI） | `msg_site_extract_lai.py` | 运行项目 `cases/validation/extract_point_lai_from_msg.py` |
| 站点抽取（静态） | `msg_site_extract_static.py` | 运行项目 `cases/validation/extract_point_static_from_msg.py` |
| 站点抽取（CSV，读 `MLST_COMPONENT2`） | `msg_site_extract_csv.py` | 运行项目 `cases/validation/extract_point_csv_from_msg.py` |
| **站点角度拟合** | `msg_site_fit.py` | 运行项目 `cases/msg-fit/msg_fit-site.py` |
| 站点组分温度验证 | `msg_site_validate.py` | 运行项目 `cases/implementation/msg_val_f2025.py` |
| 站点统计 | `msg_site_stats.py` | 运行项目 `cases/validation/statistical-data.py` |
| 站点序列重抽 | `msg_site_extract_series.py` | 运行项目 `cases/validation/repro/extract_site_series.py` |
| 站点 LST 验证复现 | `msg_site_repro_lst.py` | 运行项目 `cases/validation/repro/repro_evora_lst.py` |
| 站点组分温度复现 | `msg_site_repro_lsct.py` | 运行项目 `cases/validation/repro/repro_evora_lsct.py` |
| 多站点验证 | `msg_site_validate_multisite.py` | 运行项目 `cases/validation/repro/validate_multisite.py` |

## 站点测试与角度拟合（重点）

```text
MLST/MDLAI/LSCT 产品 ─┬─ msg_site_extract_lst/lai/static.py ─→ MSG/PRODUCTS/SITE/<站点>/<年>/<月>/<日>/
                      │                                          每站另有 static/（emis_s, emis_v, lat, lon, lc, vaa）
                      └─ msg_site_extract_csv.py ─→ /results2/*.csv（读 MLST_COMPONENT2）

MSG/field/ 观测 + PRODUCTS/SITE/ ─→ msg_site_fit.py（角度拟合 DTC/DTCRL/DTCLSFRL）
                                       └─→ PRODUCTS/SITE/ALL_SITES_LST_FITTING_RESULTS.csv（6,100 行）

LSCT_Site_Results_*.csv + field/ 观测 ─→ msg_site_validate.py / msg_site_validate_multisite.py
                                            └─→ PRODUCTS/VALIDATION/*.csv（58 站 × 8 类）
```

角度拟合核函数（`kernel_Vin`、`kernel_LiDense/Sparse`、`kernel_RossThick/Thin`、`kernel_LSF`、
`kernel_RLf`，以及 `model_DTC/DTCRL/DTCLSFRL`、`cost_*`）已逐字搬进 `base/kernel.py`，
`msg_site_fit.py` 只从 `base.kernel` 导入。

站点验证复现套件（来自运行项目当天未提交的 `cases/validation/repro/`）已在本仓库实跑验证：

- `msg_site_repro_lst.py`：与已提交的 `Validation_Stats_Nadir_vs_Obs.csv` 逐项一致
  （偏差 ~1e-15，N=518/517/518/518/518）；
- `msg_site_repro_lsct.py`：复现缓存日变化表（最大偏差 4.8e-14），并给出四组分改进验证
  （`T_Sunlit_Soil` vs `Ts`：bias +0.27 K、RMSE 2.40 K、R 0.990；`T_Shaded_Soil` −2.33 / 3.60 / 0.985；
  `T_Soil` −1.07 / 2.46 / 0.993；`T_Vegetation` vs `Tcrown` +2.94 / 3.89 / 0.958）；
- 输出写到 `cases/msg/outputs/`（Git 忽略）；`msg_site_extract_series.py`、
  `msg_site_validate_multisite.py` 用 `--help` 验证过 CLI（需 rasterio）。

对应数据：`MSG/field/`（观测 + `sites.txt`/`sites-2025.{txt,csv}`，3.9 GB）、
`MSG/PRODUCTS/SITE/`（109 站 × 2018–2025 抽取，35,274 个文件）、
`MSG/PRODUCTS/VALIDATION/`（511 个 CSV，13.4 MB）、`MSG/PRODUCTS/LSCT_Site_Results*.csv`。

## 反演链用到的数据（2026-09-16 盘点）

| 输入 | 脚本里写的路径 | 盘上实际位置 | 谁生产 |
| --- | --- | --- | --- |
| SEVIRI 原始数据 | `msg_lst_fit.py` 顶部 `indir_raw`（macOS 路径，已失效） | 需按机器改到 `/media/hero/MSG` 对应目录 | 外部下载（`msg_download.py` 下载的是 MDLAI/MDST） |
| MLST（LST 产品） | `/media/hero/MSG/PRODUCTS/MSG{,-IODC}/MLST/GEOTIFF` | 存在，2017–2025，文件名 `HDF5_LSASAF_MSG*_LST_*Disk_*.tif` | LSASAF 官方 MLST HDF5 → `msg_project_euro.py`（欧盘）/ `msg_project_iodc.py`（IODC 盘）投影；不是 `msg_lst_fit.py` 产的 |
| MDLAI（LAI） | `/media/hero/MSG/PRODUCTS/MSG/MDLAI/GEOTIFF` | 存在，2017–2025，文件名 `HDF5_LSASAF_MSG_LAI_MSG-Disk_*.tif` | LSASAF 官方 LAI HDF5 → `msg_project_euro_lai.py` 投影 |
| 角度静态文件 | `/media/hero/MSG/Static/combined_{euro,iodc}_{vza,vaa}.tif` | 存在 | 仓库里没有生产者（历史 Windows 脚本 `old/data_satellite/MSG_data_angle*.py` 一次生成） |
| 土地覆盖 | `/media/hero/MSG/map/MCD12C1_2011_0.01.tif` | 存在 | 外部静态数据 |
| 地表发射率 | `/media/hero/MSG/lse/AG1km.v003.SoilEmi.*.tif`、`IGBP_Emi.txt` | 存在 | 外部静态数据 |
| ERA5 TCWV | `msg_lst_fit.py` 读 `ERA5_tcw_<year>_<doy>_<hh>.tif` | 不再需要 GRIB→H5 转换（脚本已归档） | —— |
| 分裂窗系数 | `Sentinel3A_SLSTR_SW_Seebor_Coef_{Day,Night}.txt` | 需与脚本同目录或改路径 | 外部静态数据 |

因此从归档里取回了两个生产者：`msg_download.py`（下载 LSASAF HDF5 产品，供投影）和
`msg_project_euro_lai.py`（欧盘 LAI HDF5→GeoTIFF，LSCT 直接读它）。ERA5 GRIB→TCWV
转换已按实际需要去掉（`msg_era5_tcw.py` 回到归档）。`auxiliary/modis_lai.py`
没有被用到（LSCT 脚本里的 MODIS LAI 分支是注释，`/media/hero/MSG/lai/` 不存在），
`download_landsat.py` 只服务验证，都留在归档。

注意路径与配置（都能在盘上找到数据，但脚本里的配置对不上）：

- `msg_lst_fit.py` 顶部路径已换成 `/media/hero/MSG/`，但它读的 `ERA5_tcw_*.tif`
  在盘上不存在；它不在 LSCT 反演链上，是自研 LST 路线；
- `msg_project_euro.py` 的 `target_var='LST'` 却指向 MDLAI 输入，欧盘 MLST 的配置被注释掉了；
- `msg_project_iodc.py`、`msg_download.py` 指向 `/mnt/h/...`，本机实际在
  `/media/hero/MSG/PRODUCTS/...`。

## 运行

在 ls4t 根目录执行；输入输出路径、年份、分区参数在脚本顶部，运行前先与
`machines/hero.toml` 核对。

```bash
cd /home/hero/work/ls4t
PYTHONPATH=. python cases/msg/msg_lst_fit.py
PYTHONPATH=. python cases/msg/msg_lsct_iter.py
```

生产解释器是 `/home/hero/anaconda3/envs/env_311/bin/python3.11`。这两个脚本还需要
GDAL、pvlib、pandas、h5py、scipy 和 satpy（LST 拟合读取 SEVIRI 原始文件）。
投影脚本需要 rasterio、pyresample 和 GDAL。

## LSCT 反演过程（正式版 / 测试版）

两个在用版本已经合到同一个脚本 `msg_lsct_iter.py`，只靠顶部的 `METHOD` 切换：

```python
METHOD = "formal"   # 正式版（大批量产品）→ PRODUCTS/LSCT/MLST_COMPONENT/
METHOD = "test"     # 测试/对照版          → PRODUCTS/LSCT/MLST_COMPONENT2/
```

**正式版（大批量产评用的方法）**，三步：

1. **A 阶段**：先分 [光照土壤] 与 [阴影土壤 + 植被]。用两个视角（欧盘 + IODC）的
   辐亮度方程，在 3×3 窗口内闭式求解 `solve_2x2_system_5x5`，得到光照土壤亮温 `bs1`
   和混合分量 `b_comb`；
2. **B 阶段**：固定光照土壤，在残差中再分 [阴影土壤] 与 [植被]，5×5 窗口加**硬约束**
   `|bs2 − bv| ≤ dif`（`dif = 3`）；违反约束的像元取约束边界线上残差最小的解
   （`solve_constrained_vectorized2`）；
3. **C 阶段**：以 A/B 结果为先验做联合平差 `solve_joint_vectorized_with_prior(λ = 100)`
   （强先验），再做物理裁剪（bs2 ≤ bs1、植被不过热），最后逆 Planck 转温度。

输出 4 波段 `[ts, tv, tss, tsh]` = 面积加权土壤、植被、光照土壤、阴影土壤；
×100 存 uint16，nodata 0，250–350 K 或 LAI<0.05 置空。

**测试/对照版**与正式版同一套 A/B/C 流程，差别只有两处：B 阶段**不加硬约束**
（退化为普通 5×5 闭式解），C 阶段用**弱先验 λ = 0.1**。它产出的是 `MLST_COMPONENT2`，
目前被站点 CSV 抽取 `msg_site_extract_csv.py` 使用，所以保留。

需要留意的历史差异：正式版的 C 阶段用显式伴随矩阵求解，测试版原来用
`np.linalg.solve`；合并后统一为正式版实现，因此重跑 “test” 档与历史
`MLST_COMPONENT2` 会有浮点级差异（~1e-15 相对量级）。要逐位复现旧产物需使用归档脚本。

### 全图（full disk）反演方法一览（都在 `cases/msg/`）

| ls4t 文件 | 来源 | 组分 | 方法 |
| --- | --- | --- | --- |
| `msg_lsct_2c_full.py` | `msg_lsct2.0.py` | **2 组分**（土壤 + 植被） | 5×5 窗口最小二乘，逐分量写 tif |
| `msg_lsct_3c_full.py` | `msg_lsct3.0.py` | 3 组分 | 3×3 窗口最小二乘（基线） |
| `msg_lsct_3c_2stage_full.py` | `msg_lsct2.1.py` | 3 组分 | 两阶段：先 [光照土壤] vs [阴影土壤+植被]，再分 [阴影土壤] vs [植被]（无约束） |
| `msg_lsct_iter.py` | `msg_lsct3.2-iter.py` / `3.1-iter.py` | 3 组分 | **正式档** `METHOD="formal"`（硬约束 + λ=100）；**测试档** `METHOD="test"`（无约束 + λ=0.1） |
| `msg_lsct_3c_constrained_full.py` | `msg_lsct3.2-cons.py` | 3 组分 | 同一硬约束的**全向量化实现**（对照，修了边界 `dif` 逻辑） |
| `msg_lsct_3c_show_full.py` | `msg_lsct3.2-iter-show.py` | 3 组分 | 正式算法 + 逐景 4 分量对比出图（对照） |

### 备选/历史方法（归档）

| 方法 | 脚本 | 特点 |
| --- | --- | --- |
| 2 组分 3×3 窗口最小二乘 | `msg_lsct2.0.py` | 最早版本，无约束 |
| 2/3 组分 5×5 窗口 LS + 物理裁剪 | `msg_lsct2.1.py` | 通用 2×2 求解器 |
| 3 组分 3×3 窗口 LS | `msg_lsct3.0.py` | 三组分基础版 |
| 全向量化约束解（候选集+可行性判定） | `msg_lsct3.2-cons.py` | 同一约束、另一种实现，修正了边界 `dif` 逻辑 |
| 约束解 + 诊断出图 | `msg_lsct3.2-iter-show.py` | 与正式版同算法，带图 |
| 站点点解 | `msg_lsct3.2-iter-site*.py` | 站点位置的直接/约束/中心解 |
| 老窗口族 | `support/util_lsct.py`：`inv_lsct2/3_winconst`、`winquad`、`winquad_constraint` | SLSQP 非线性窗口 / 贝叶斯岭回归 |
| 逐像元点解 | `inv_lsct_point`（ridge） | 单点回归 |
| 参考实现 | 根目录 `msg/msg_lsct.py` + `base/lsct.py: retrieve_components(_window)` | 读标准 NPZ 观测；与在用版输入格式不同，需先做「MLST+LAI+角度 → NPZ」准备步骤才能对拍 |

## 依赖来源

| 依赖 | 位置 | 用到的内容 |
| --- | --- | --- |
| 文件与栅格读写 | `base/files.py` | `read_image_gdal`、`read_image_dataset_gdal`、`read_txt_array`、`search_file`、`mkdir_if_not_exist` |
| 几何与重采样 | `base/spatial.py` | `loc2map`、`resize_data`、`geo2lonlat`、`imagexy2geo` |
| 日期 | `base/dates.py` | `date2DOY` |
| 辐射 | `base/radiometry.py` | `planck`、`inv_planck` |
| 冠层/组分温度 | `base/lsct.py`、`base/rt/gap.py` | `ndvi_min_g/max_g`、`gap_probability_hom_analytical` |
| **角度拟合内核** | `base/kernel.py` | `kernel_Vin/LiDense/LiSparse/RossThick/RossThin/LSF/RLf`、`model_DTC/DTCRL/DTCLSFRL`、`cost_*` |
| 站点清单读取 | `base/files.py` | `read_txt_str`（`field/sites*.txt`） |

函数逐字迁移自运行项目的 `cases/support/util_data.py`、`util_file.py`，数值由
`tests/test_msg_case_dependencies.py` 和 SLSTR 的 golden 测试共同锁定。

## 归档

`cases/_archive/msg/transferred_20260916/nested_snapshots/europe_africa/` 保存了原来的
`dual_disk` 快照（投影、LSCT 各版本、月合成、站点验证、绘图、下载、support 兼容层）。
需要复现旧流程时从那里取回，但生产只走上面两个脚本。
