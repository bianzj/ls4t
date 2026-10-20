# MSG EVO 真实数据反演样例

样例数据位于 `tests/data/msg_evo_201710_10x10/`，来自已有 LSASAF MSG 产品，
不是合成数据。EVO 坐标为 38.5411°N、8.0033°W，取 MSG 区域网格零起始
行 881、列 333 周围 **10×10** 个像元。偶数窗口明确从行 876、列 328 开始；
站点像元在样例内为行 5、列 5。地理位置使用网格像元中心。

## 数据

样例采用 `cases/msg/msg_project_hdf5.py` 输出的真实 **投影 GeoTIFF 格式**：
保留产品目录、原文件名、单波段、整数编码、NoData、投影和像元大小，
只将空间范围裁剪为 10×10。它对应区域投影阶段，不是原生全圆盘 HDF5 文件。

```text
msg_evo_201710_10x10/
├── PRODUCTS/
│   ├── MSG/MLST/GEOTIFF/2017/10/01/
│   │   ├── HDF5_LSASAF_MSG_LST_MSG-Disk_201710010000.tif
│   │   └── ...                              # 每小时一个文件，整月 744 个
│   ├── MSG-IODC/MLST/GEOTIFF/2017/10/01/
│   │   ├── HDF5_LSASAF_MSG-IODC_LST_IODC-Disk_201710010000.tif
│   │   └── ...                              # 每小时一个文件，整月 744 个
│   └── MSG/MDLAI/GEOTIFF/2017/10/01/
│       └── HDF5_LSASAF_MSG_LAI_MSG-Disk_201710010000.tif
│                                            # 每天一个文件，整月 31 个
├── Static/                                  # 原始 Int16 角度裁剪，度 × 100
│   ├── combined_euro_vza.tif
│   ├── combined_euro_vaa.tif
│   ├── combined_iodc_vza.tif
│   └── combined_iodc_vaa.tif
├── AUXILIARY/                               # 样例派生辅助量，非 MSG 原产品
│   ├── static.tif
│   ├── solar_zenith_deg.tif
│   └── solar_azimuth_deg.tif
├── manifest.json
└── sources.json
```

上例展示 10 月 1 日的文件名；实际目录包含 `01/` 至 `31/`。

| 文件 | 内容 | 编码与单位 |
|---|---|---|
| `PRODUCTS/MSG/MLST/GEOTIFF/.../*.tif` | EURO 逐小时 LST | 744 个单波段 UInt16 文件；摄氏度 × 100 的有符号位模式；NoData=0 |
| `PRODUCTS/MSG-IODC/MLST/GEOTIFF/.../*.tif` | 同时次 IODC 逐小时 LST | 同上，共 744 个文件 |
| `PRODUCTS/MSG/MDLAI/GEOTIFF/.../*.tif` | MSG 每日 LAI | 31 个单波段 UInt16 文件；LAI × 1000；NoData=0 |
| `Static/combined_*.tif` | 两视角 VZA/VAA | 单波段 Int16，度 × 100，NoData=-32768 |
| `AUXILIARY/static.tif` | 经纬度、土地类型、土壤和植被发射率 | 字段名称写入波段描述 |
| `AUXILIARY/solar_zenith_deg.tif` | 逐像元、逐小时几何太阳天顶角 | 744 波段，与 LST 同时次，degree |
| `AUXILIARY/solar_azimuth_deg.tif` | 逐像元、逐小时太阳方位角 | 744 波段，与 LST 同时次，degree |
| `manifest.json` | 时间轴、站点、网格、单位、文件 SHA-256、限制 | 全部路径相对于样例目录运行 |
| `sources.json` | 原始文件路径、裁剪窗口原始字节 SHA-256、HDF5 定标属性 | 提取来源记录；运行样例不依赖来源盘 |

三类动态产品覆盖整个日历月。文件存在不代表每个像元都无云；磁盘中保留原始
缺测编码，读取时才转换为 NaN，不插值、不补零。原始 LST 是摄氏度×100 的
Int16，经投影保存为 UInt16，需先恢复有符号位模式，再换算成 K。LAI 依 HDF5
定标属性除以 1000。源投影 TIFF 本身没有 GDAL Scale/Offset；相应 HDF5 的
`SCALING_FACTOR`、`OFFSET`、`MISSING_VALUE`、`UNITS` 逐文件记录于
`sources.json`，由读取器应用。样例 TIFF 保持源文件编码，不提前转为浮点 K。
投影产品的零值被声明为 NoData，无法再区分真实 0°C 或真实零 LAI，保守排除。
太阳角是 pvlib `nrel_numpy` 根据 UTC、像元中心经纬度和 0 m 高度计算的辅助量。

## 运行

```powershell
cd C:\work\ls4t
& C:\work\miniconda\Scripts\conda.exe run -n python311 --no-capture-output python tests/examples/msg_evo_sample.py run
& C:\work\miniconda\Scripts\conda.exe run -n python311 --no-capture-output python -m pytest tests/test_msg_evo_sample.py -q
```

默认反演土壤和植被两个组分。每个时次独立使用 EURO/IODC 双视角，按
`exp(-0.5×LAI/cos(VZA))` 和组分发射率构造有效权重；用 10.5 μm Planck
公式将 LST 换成与有效发射率相乘的辐射。调用
`base.lsct.retrieve_components_window()`，采用 5×5 局部常量窗口最小二乘。
只输出中心输入有效、昼间、LAI≥0.05、两视角 LST 及结果在 250–350 K 的像元。
不同时间的观测不会放进同一个反演方程；夜间数据保留在样例中，但不反演。

结果默认写到 `tests/outputs/msg_evo_201710_10x10/`：组分温度 GeoTIFF、质量标志、
辐射残差、站点中心时间序列 CSV 和运行汇总 JSON。结果 GeoTIFF 保留裁剪后的
地理坐标、时间轴和 K 单位；诊断结果按月多波段保存，生成结果目录被 Git 忽略。

可选的三组分参考解使用 hotspot=0.25，把土壤进一步分成光照土壤和阴影土壤：

```powershell
& C:\work\miniconda\Scripts\conda.exe run -n python311 --no-capture-output python tests/examples/msg_evo_sample.py run --components 3 --output tests/outputs/msg_evo_201710_3c
```

两视角三组分依赖窗口内组分辐射恒定的假设，解的稳定性受 LAI、云和矩阵条件数
影响。这是主 LS4T 函数库的参考求解路径，**不是 MSG 区域产品的两阶段硬约束
与先验平差算法，也不构成 EVO 地面精度验证**。2017 静态观测角的轨道来源限制、
土地类型数据的未知 Clarke 1866 基准及缺测限制记录在 `manifest.json` 中。

本样例在 Conda `python311`、Python 3.11.15、GDAL 3.12.3 中实际运行：

| 解法 | 有结果的时次 | 有效像元时次 | EVO 中心有效时次 |
|---|---:|---:|---:|
| 土壤与植被两组分 | 263 / 744 | 12351 | 31 |
| 光照土壤、阴影土壤与植被三组分 | 253 / 744 | 10567 | 28 |

这是运行覆盖率，不是反演精度。自动检查涵盖完整月时间轴、样例 SHA-256、
原产品目录与文件名、单波段整数编码、裁剪原始字节一致性、网格和单位、实际
GeoTIFF 结果、缺测不填补，以及两种解法与独立邻域最小二乘
和物理 Planck 反算的一致性。

## AATSR 方法迁移与温差约束对照

`msg_aatsr_comparison.py` 使用同一真实月份，比较两组分 LS、Ridge、SLSQP、
空间二次曲面和贝叶斯融合，以及三组分 LS、SLSQP 与当前仓库 MSG 两阶段算法。
两/三组分均设置 SLSQP 温差约束开关，保持相同权重、边界和初值策略。
另外记录 MSG 第二阶段共同缺测掩膜修正的控制结果，保留原算法结果作为基准。

```powershell
& C:\work\miniconda\Scripts\conda.exe run -n python311 --no-capture-output python -B tests/examples/msg_aatsr_comparison.py
& C:\work\miniconda\Scripts\conda.exe run -n python311 --no-capture-output python -B -m pytest tests/test_msg_aatsr_comparison.py -q
```

结果位于 `tests/outputs/msg_aatsr_201710/`：`REPORT.md`、`summary.json`、
`method_metrics.csv`、`ground_paired_metrics.csv`、`constraint_ablation.csv`、
`heldout_metrics.csv`、`center_predictions.csv`，以及逐方法组分温度 GeoTIFF。
只评价内部 4×4 像元，保证两阶段算法的 7×7 支持完整，不跨时次拟合。

地面参考通过可选 `--reference-panel` 传入，默认探测本机以前保存的 EVO 参考缓存；
文件不存在时仍执行反演诊断，但不生成地面精度结论。参考缓存不包含在本样例内。
两组分平均土壤与 EVO 阳照土壤不是同一变量；单站单月、少量匹配日期的结论不代表全区域。

## 重新提取原始样例

只有重新提取才需要原始 E 盘与 pvlib。安装依赖可使用项目的 `msg-sample` 扩展。

```powershell
& C:\work\miniconda\Scripts\conda.exe run -n python311 --no-capture-output python -m pip install -e '.[msg-sample]'
& C:\work\miniconda\Scripts\conda.exe run -n python311 --no-capture-output python tests/examples/msg_evo_sample.py extract --source-root E:\
```

提取器只读取源产品，不修改 MSG 原始文件；逐文件核验时间、网格和 HDF5
定标属性，输出的小样例与来源记录一起保存到 `tests/data/`。

# SLSTR EVO 真实窗口测试样例

`tests/data/slstr_evo_20170517_10x10/` 保存一景 2017-05-17 的真实 EVO
双视角 10×10 窗口和 IGBP 发射率表，附有 SHA-256 来源清单。样例从窗口内已有的
双视角 LST 开始，调用当前欧洲年度批次使用的
`homogeneous_3component_bayes_map_5x5_lai_only_v5` 逐景求解函数；不依赖数据盘挂载。
天底窗口依已保存的最近地理位置映射到斜视窗口，最大映射距离 1.12 km。
局部 LAI、土地类型及发射率替代生产程序索引的全球辅助网格，求解器本身不改动。

```bash
cd /home/hero/work/ls4t
/home/hero/anaconda3/envs/env_311/bin/python -B tests/examples/slstr_evo_sample.py run
/home/hero/anaconda3/envs/env_311/bin/python -B -m unittest discover -s tests -p test_slstr_evo_sample.py -v
```

结果写入被 Git 忽略的 `tests/outputs/slstr_evo_20170517_10x10/`：四个组分温度
GeoTIFF 和 `summary.json`。当前样例运行写出 36 个有效像元，站点锚点有结果。
另可执行 `--force-night --output tests/outputs/slstr_evo_20170517_night_gate`，
将样例太阳天顶角替换为 100°，检查白天筛选返回 `no_valid`；这是受控检查，
并非另一景真实夜间观测。

本样例检验三组分求解和白天筛选，不重算分裂窗 LST，也不代表完整场景运行。
窗口内虽保留旧方法组分结果，程序不会把它们当输入或真值。未附站点地面温度，
因此有效像元数和物理范围检查不构成 EVO 精度验证；源 TIFF 未提供真实地图
投影，生成的温度 TIFF 也仅表示本地 10×10 数组坐标。
