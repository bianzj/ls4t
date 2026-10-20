# AATSR cases

AATSR 生产和实验代码已从独立运行项目 `ls4t-aatsr` 转入本目录并扁平化：一个文件一个环节，
放在本目录根部，项目代码只从 `base/`（含 `base/aatsr/`）导入；没有 `support/` 夹层、没有
`import *`、没有 `sys.path` 技巧。

| 环节 | 脚本 | 来源 |
| --- | --- | --- |
| 解压 | `aatsr_unzip.py` | `cases/implementation/aatsr_unzip.py` |
| 提取 | `aatsr_data.py` | `cases/implementation/aatsr_data.py` |
| LST | `aatsr_lst.py` | `cases/implementation/aatsr_lst.py` |
| **LSCT（2 组分，正式）** | `aatsr_lsct.py` | `cases/implementation/aatsr_lsct.py` |
| LSCT（2 组分，经纬度版） | `aatsr_lsct_latlon.py` | `cases/implementation/aatsr_lsct-ll.py` |
| LSCT（全图 2 组分 v3.1） | `aatsr_lsct_v31.py` | `cases/_archive/product_history/inv_lstC_global/inv_lsct2_v3.1.py` |
| LSCT（NDVI 版） | `aatsr_lsct_ndvi.py` | `.../inv_lsct2_NDVI.py` |
| 日/月 0.01° 统计 | `aatsr_001deg_stats.py` | `cases/implementation/aatsr_001deg_stats.py` |
| 月分析堆栈 | `aatsr_monthly_3files.py` | `cases/implementation/aatsr_monthly_3files.py` |
| ERA5 TCWV 输入 | `aatsr_era5_tcw.py` | `cases/implementation/era5_tcw_data.py` |
| 站点 LSCT 反演 | `aatsr_site_inv.py` | `cases/_archive/product_history/inv_lstC_sites/inv_lsct_sites.py` |
| 站点 LSCT（贝叶斯） | `aatsr_site_inv_bayes.py` | `.../inv_lsct_sites_bayesian.py` |
| 站点验证 | `aatsr_site_validate.py` | `cases/_archive/product_history/val_sites/val_sites.py` |
| 站点时间序列 | `aatsr_site_series.py` | `.../val_sites_time_series.py` |

## 全图 LSCT 方法

`aatsr_lsct.py` 是正式生产版（`number_component = 2`，两组分：土壤 + 植被），
`aatsr_lsct_latlon.py` 是同一算法的经纬度读取版，`aatsr_lsct_v31.py` 是全图 2 组分的
v3.1 历史版，`aatsr_lsct_ndvi.py` 用 NDVI 求植被覆盖度，并采用带组分温差约束的
窗口 SLSQP。正式版使用窗口 Ridge；v3.1 比较单像元、窗口常量、空间二次曲面及
空间先验与中心角度观测的贝叶斯融合，不能把这些分支统一称为约束拟合。

结构权重、空间温度差异、组分温差约束、贝叶斯融合及当前实现限制，见
[AATSR 方法整理](../../docs/AATSR_METHODS.md)。

## 依赖来源

| 依赖 | 位置 | 内容 |
| --- | --- | --- |
| 文件与栅格 | `base/files.py` | `read_image_gdal`、`read_image_Nc`、`read_h5py_item(s)`、`write_h5py_item/file`、`un_gz`、`search_file(_rej)`、`mkdir_if_not_exist`、`read_txt_array/str` |
| AATSR 专用读取 | `cases/aatsr/util_aatsr.py` | `aatsr_read_NDVI/angle/lai/loc/obs/lst/clo/clo_optimized`、`aatsr_read_sites_*`、`aatsr_read_crown_data`（含机器路径，按仓库规则放在 case 内） |
| 几何/日期/统计 | `base/spatial.py`、`base/dates.py`、`base/metrics.py` | `loc2map`、`date2DOY`、`doy2date`、`cal_rmse_r2` |
| 辐射/组分温度 | `base/radiometry.py`、`base/lsct.py`、`base/lsct_window.py`、`base/rt/` | `planck`、`cal_fvc_from_lai`、`cal_psoil_hom`、`fit*`、`constraint_func_*`、`Hom` 等 |
| 角度拟合核 | `base/kernel.py` | `kernel_*`、`model_*`、`cost_*` |

## 运行

```bash
cd /home/hero/work/ls4t
PYTHONPATH=. python cases/aatsr/aatsr_001deg_stats.py --help
PYTHONPATH=. python cases/aatsr/aatsr_monthly_3files.py
```

生产解释器 `/home/hero/anaconda3/envs/env_311/bin/python3.11`（需要 GDAL、h5py、pyepr、
netCDF4、scikit-learn）。脚本顶部的 `/media/hero/...` 路径、年份区间运行前请与
`machines/hero.toml` 核对。

## 已知问题

- `aatsr/util_aatsr.py` 的 `aatsr_read_obs(...)` 末尾 `return resultT` 引用了未定义变量，
  这是来源项目里就有的 bug，迁移时保持原样。

早期 AATSR 产品、参数实验和备份仍在 `cases/_archive/aatsr/product_history/`；本次迁移前的
旧快照在 `cases/_archive/aatsr/transferred_20260916/`。
