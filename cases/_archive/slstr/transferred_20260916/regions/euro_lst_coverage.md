# SLSTR euro-LST 覆盖底图

`/media/hero/slstr-euro-lst` 的盘面抽查与拼接底图，由
[`euro_lst_coverage.py`](euro_lst_coverage.py) 生成（只读扫描，不写数据盘）。

## 选定窗口

| | 主窗口 | 近每日变体 |
|---|---|---|
| 经纬度 | `-12 ~ 42 E` / `30 ~ 71.5 N` | `-12 ~ 42 E` / `31.5 ~ 71.5 N` |
| 0.01° 网格 | 5400 × 4150 px | 5400 × 4000 px |
| 面积 | 17.2 M km² | 16.3 M km² |
| 每格最少观测天数（52 天采样） | 11 | 24 |

主窗口覆盖欧洲大陆主体、英国爱尔兰与北非沿海带（摩洛哥—埃及，下至 30°N）。
南界由成像范围决定：9 年抽样中成像南界都是 28.7°N，但 30°N 处每格仍只有
约 1/5 的天数有轨道经过，再往南不足以支撑拼接，故截在 30°N。

## 产物

| 文件 | 说明 |
|---|---|
| `euro_lst_window.json` | 窗口设置（机器可读，拼接流程的输入） |
| `euro_lst_window.geojson` | 主窗口 + 近每日变体 + 数据外沿轮廓 |
| `euro_lst_mosaic_base_0p01.tif` | 0.01° 拼接底图网格（4326，4150 × 5400） |
| `euro_lst_coverage_0p05.tif` | 每格被多少景 footprint 覆盖 |
| `euro_lst_revisit_0p05.tif` | 每格被多少个观测日扫到（0~52） |
| `euro_lst_coverage_preview.png` | 覆盖底图 |
| `euro_lst_revisit_profile.png` | 南界再访率剖面 |
| `euro_lst_year_overlap.png` | 各年 ROI 覆盖一致性 |
| `euro_lst_disk_audit.png` | 盘面体检（逐年数量、每日景数、非欧洲轨道段） |
| `euro_lst_coverage_summary.json` | 全部统计量 |
| `euro_lst_coverage_cache/` | 各年 footprint 抽样缓存，重跑无需再读数据盘 |

## 盘面要点

- 2016 年空盘；2017—2025 共 91142 景、3172 个观测日，全部为 S3A。
- 每年用一套 ROI 挑选下载，各年 swath 外沿一致（西 -57.7°E、北 73.4°N、
  南 28.7°N），盘内约 30% 的景是南极夜轨与北极段，做欧洲拼接时用不到。
- 数据完整性（按环节实际文件核对）见
  [`euro_lst_data_status.md`](euro_lst_data_status.md)：2020 年 LSCT2 已补齐
  （2026-09-16，7030 景），目前真正的大缺口是 2017 与 2025 年的 LSCT2，
  以及 2020-11/12 的提取。

## 重跑

```bash
PYTHONPATH=. python cases/slstr/regions/euro_lst_coverage.py
```

缓存缺失时会重新抽样（约 2 分钟/年）；改窗口只改脚本顶部的 `EUROPE` 常量。
