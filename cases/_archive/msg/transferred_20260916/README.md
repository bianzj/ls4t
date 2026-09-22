# 2026-09-16 MSG 生产流程收敛时归档的内容

MSG 只保留两条真实流程：LST 拟合/反演（`cases/msg/msg_lst_fit.py`）和 LSCT 反演
（`cases/msg/msg_lsct_iter.py`）。这里保存收敛前 `cases/msg/europe_africa/dual_disk/`
的完整快照。

```text
nested_snapshots/europe_africa/dual_disk/
├── lsct/        LSCT 反演各版本（2.0/2.1/3.0/3.1/3.2-cons/3.2-iter-show/site 系列）与月合成
├── preprocess/  MSG 提取、投影、站点取值
├── field/       站点 LAI/LST/静态参数提取
├── auxiliary/   ERA5 TCWV、MODIS LAI
├── download/    Landsat 等外部数据下载
└── machines/    hero、bianzj-macos 机器配置
```

这些脚本导入的是已被删除的 `base.util_*`，当前不能直接运行。恢复方式是成对放回运行
项目 `/home/hero/work/ls4t-msg-lsct/cases/`（那里仍有完整的 `support/`），或按
`cases/msg/case.toml` 的依赖清单改写后放回 `cases/msg/`。

注：盘点反演链数据后又从本归档里取回两个生产者，放进 `cases/msg/`：
`implementation/msg_proj_hdf5-euro-lai.py` → `msg_project_euro_lai.py`（欧盘 LAI
HDF5→GeoTIFF，LSCT 直接读），
`implementation/msg-download.py` → `msg_download.py`（下载 MDLAI HDF5，投影后作为
LSCT 的 LAI 输入）。ERA5 GRIB→TCWV 转换经确认不再需要，`auxiliary/era5_tcw.py`
（`auxiliary_scripts/msg_era5_tcw.py`）留在归档。

另按“站点测试（组分温度 + 角度拟合）”的重点，取回了
`validation/extract_point_{lst,lai,static,csv}.py`、`msg-fit/msg_fit-site.py`、
`implementation/msg_val_f2025.py`、`validation/statistical-data.py`，角度拟合内核
`support/util_kernel.py` 逐字进入 `base/kernel.py`。归档里仍保留的同线脚本：
`msg_fit_dtcrl-site.py`（DTCRL 专用旧版）、`msg-val-evo.py`、`msg-val-kal.py`、
`msg_val-kal-all.py`、`msg_val_f2025_month*.py`、`display-dtc-*.py`、`msg_monthly_averaging.py`。

此外，运行项目里当天新写、当时尚未提交的站点验证复现套件 `cases/validation/repro/`
也搬进了 `cases/msg/`：`extract_site_series.py` → `msg_site_extract_series.py`、
`repro_evora_lst.py` → `msg_site_repro_lst.py`、`repro_evora_lsct.py` →
`msg_site_repro_lsct.py`、`validate_multisite.py` → `msg_site_validate_multisite.py`；
该套件自带的 `radiometry.py` 由 `base.radiometry` 取代（数值逐位相同），参考统计
`Validation_Stats_Nadir_vs_Obs.csv` 一并带入 `cases/msg/`。
