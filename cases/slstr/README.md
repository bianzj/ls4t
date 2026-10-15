# SLSTR cases

SLSTR 生产代码从独立运行项目 `ls4t-slstr` 转入后已扁平化：一个文件一个环节，全部
直接放在本目录，只从 `base/`（含 `base/slstr/`）导入，没有 `support/` 夹层、没有
`sys.path` 技巧、没有 `import *`。后续直接在 ls4t 仓库根目录运行。

## 五个环节

| 环节 | 研究区优先 | 逐景优先 | 批处理 |
| --- | --- | --- | --- |
| 解压 | —— | `slstr_unzip_scene.py` | `slstr_unzip_batch.py` |
| 重整 | `slstr_data_area.py` | `slstr_data_scene.py`、`slstr_data_scene_origin.py`、`slstr_data_scene_latlon.py`、`slstr_data_scene_years.py` | `slstr_data_batch.py` |
| 投影 | 含在重整脚本内 | `slstr_proj_scene.py` | 含在 `slstr_data_batch.py` 内 |
| LST 反演 | `slstr_lst_area.py` | `slstr_lst_scene.py`、`slstr_lst_scene_parallel.py` | `slstr_lst_batch.py` |
| LSCT 反演 | `slstr_lsct2_area.py`、`slstr_lsct3_area.py` | `slstr_lsct2_scene.py`、`slstr_lsct2_scene_parallel.py`、`slstr_lsct3_scene.py` | —— |

```text
cases/slstr/
├── production.toml                  环节登记、依赖策略、来源版本
├── machines/hero.toml               本机数据盘、Python 和并行设置
├── slstr_unzip_scene.py             解压
├── slstr_data_area.py               重整（研究区优先）
├── slstr_lst_scene.py               LST 反演（逐景）
├── slstr_lsct3_scene.py             LSCT 三组分（逐景）
└── ...                              共 18 个扁平脚本
```

## 运行

在 ls4t 根目录执行，一次只跑一个文件；输入输出目录、年份和研究区参数在脚本顶部。

```bash
cd /home/hero/work/ls4t
PYTHONPATH=. python cases/slstr/slstr_data_batch.py
PYTHONPATH=. python cases/slstr/slstr_lst_scene_parallel.py \
  --root /media/hero/slstr_heihe/heihe --year 2025 --workers 24
PYTHONPATH=. python cases/slstr/slstr_lsct2_scene_parallel.py --year 2020 --workers 24
```

并行脚本的运行报告写到 `cases/slstr/logs/`（Git 忽略）。生产解释器是
`/home/hero/anaconda3/envs/env_311/bin/python3.11`，需要 GDAL、cv2、netCDF4、h5py、
scipy、scikit-learn；`tests/test_slstr_case_dependencies.py` 可以在没有这些库的解释器
下运行（相关用例自动跳过）。

## 依赖来源

case 脚本用到的每个函数都来自 `base/`，迁移时逐字搬运、行为保持一致（数值已用
golden 测试锁定）：

| 依赖 | 位置 | 内容 |
| --- | --- | --- |
| 文件与栅格读写 | `base/files.py` | GeoTIFF 读写、VRT、目录/文件名搜索、解压、NetCDF、HDF5 |
| 栅格写出与坐标系 | `base/raster.py` | `write_vrt`、`writevrt_nadir/obliq`、`getSRSPair` |
| 几何与重采样 | `base/spatial.py` | `loc2map`、`geo2imagexy`、`imagexy2geo`、`geo2lonlat`、`lonlat2geo`、`resize_data` |
| 日期 | `base/dates.py` | `date2DOY` |
| 辐射 | `base.radiometry.py` | `planck`、`inv_planck`（沿用原运行项目常数） |
| 组分温度内核 | `base/lsct.py` | `cal_fvc_from_lai`、`cal_effective_emissivity_hom`、`cal_rad_from_lst`、`sample_hom_Emis*` |
| 窗口反演 | `base/lsct_window.py` | `inv_lsct2_window`、`inv_lsct3_window` 及约束/权重/求解依赖（由 `base/lsct.py` 转出） |
| 冠层辐射传输 | `base/rt/` | `Hom` 模型与 gap/hotspot/散射/发射率/辐亮度 |
| SLSTR 网格常量 | `base/slstr/slstr_grid.py` | `nl_*`、`ns_*`、`adjust_*` |

## 已知问题与已修复

- 已修复：`slstr_lsct2_area.py`、`slstr_lsct3_area.py` 调用的 `inv_lsct2_window` /
  `inv_lsct3_window` 在 2026-09-07 的目录扁平化（提交 `c1389a0`）里被删掉，导致两个
  研究区脚本「能编译、一跑就报 NameError」。现已从 AATSR 产品历史
  `cases/_archive/aatsr/product_history/util/util_ls4t.py` 逐字恢复到
  `base/lsct_window.py` 并由 `base/lsct.py` 转出，与原实现逐值相同（golden 值在
  `tests/test_slstr_case_dependencies.py`）；
- `Hom.run`、`cal_effective_emissivity_hom` 的部分分支依赖特定输入形状，迁移前后行为
  一致，改动时用同一组测试对照。

## 归档

五个环节之外的 ERA5/TCWV 预处理、区域拼接出图、覆盖率报告、shell 驱动、文件检查、
未被依赖的 support 模块，以及迁移前的嵌套脚本和整个 support 夹层，都在
`cases/_archive/slstr/transferred_20260916/`。两个旧区域快照已移到
`cases/_archive/slstr/retired_20261013/`，并退出 catalog 登记。它们导入的
`base.util_*` 已不存在，仅作历史参考。
