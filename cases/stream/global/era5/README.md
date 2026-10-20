# STREAM ERA5 forcing

将 `/home/hero/code/ship_stream/era5/` 中四份按年份写死的下载脚本、两份提取脚本和
文件清点脚本合并成一个**可配置执行案例**。原目录保持不变。通用转换在
`base/stream_era5.py`，真实数据路径仅在本案例的 `machines/hero.toml` 中。
本案例没有自动调度；运行任何子命令前应先确认输入月份及目标路径。

## 用法

在 LS4T 根目录执行。下载需要 `cdsapi` 与已配置的 CDS 凭据；仅做本地提取、检查
不需要网络。提取需要 `netCDF4`、`h5py` 和 `numpy`，可安装可选依赖
`pip install -e '.[stream-era5]'`（不会自动下载数据）。

```bash
python cases/stream/global/era5/run.py download --year 2024 --month 7
python cases/stream/global/era5/run.py extract --year 2024 --month 7 \
  --source /path/to/202407.nc
python cases/stream/global/era5/run.py extract --year 2024 --month 7 \
  --source /path/to/data_stream-oper_stepType-instant.nc \
  --accumulated-source /path/to/data_stream-oper_stepType-accum.nc
python cases/stream/global/era5/run.py check --year 2024 --month 7
```

默认使用 `machines/hero.toml` 的下载根目录和输出根目录；可在子命令**之前**传
`--profile <name>` 或 `--output-root /path/to/stream-input`，下载时亦可传
`download --download-root /path/to/raw`。提取已有的本地 NC 请使用 `extract`，无需
先运行 `download`。下载结果是 `<download_root>/<year>/<YYYYMM>.nc`，不会覆盖
同名文件；提取结果是 `<output_root>/force/<year>/<DOY>/`，如目标日期目录已存在
则拒绝覆盖。源 NC 必须包含完整月的逐小时记录，拆分输入的瞬时与累积时轴必须一致。

## 数据约定

- 逐小时：`t.txt`（0–1 日内比例，共 24 行）及 HDF5 `data` 数据集的
  `skt/u/ta/ea/p/rin/rli/stl/cvl/cvh.h5`（形状 `[24, lat, lon]`）。
- 每日 UTC 12:00 快照：`sm/lai/lai_hv/lai_lv.h5`（形状 `[lat, lon]`）。
  `sm` 为 ERA5 `swvl1`；`lai` 是原流程中高低植被 LAI 之和。STREAM 如使用
  自定义 LAI，可另行配置 LAI 来源，不影响这里的 ERA5 土壤水分。
- `p` 从 Pa 换算为 hPa；`rin/rli` 从逐小时累积 J/m² 换算为 W/m²；
  `ta/ea` 保留 ERA5 气温/露点温度 K（STREAM 读取露点 K 后换算水汽压）。
- 默认将 ERA5 0–360° 经度排列旋转成 −180–180°；源文件本来就是 −180–180°
  时指定 `extract --longitude-order=-180-180`。该步骤仅重排像元，不重投影。

这里仅生成历史 STREAM 驱动的逐日 `force` 文件；模型所需的静态格网、
`meteoType.tif`、参数配置以及其他辅助数据**不在此案例中生成**。
运行前应检查这些数据的坐标、分辨率与模型配置是否一致。
