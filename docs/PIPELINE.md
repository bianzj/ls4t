# 产品处理关系

## 传感器产品

```text
AATSR-DATA → AATSR-LST / AATSR-LSCT
SLSTR-DATA → SLSTR-LST / SLSTR-LSCT
MSG-DATA   → MSG-LST   / MSG-LSCT
MODIS-DATA → MODIS-LST
VIIRS-DATA → VIIRS-LST
AHI-DATA   → AHI-LST
ASTER-DATA → ASTER-LST
```

SLSTR 原始产品内部是 NetCDF；MSG 原始产品是 SEVIRI native（`.nat`）。两者从读取阶段开始，
数据、辅助数据和 LST 结果统一使用 GeoTIFF。数据模块负责原始读取和数据产品保存；温度模块
负责补齐辅助数据并反演产品。其他传感器流程暂不受本次格式调整影响。

SLSTR 的通用单景流程为：

1. `slstr/slstr_unzip.py` 的 `slstr_unzip()`：压缩包到 SEN3。
2. `slstr/slstr_extract.py` 的 `slstr_extract()`：读取原生 `.nc`，输出 `SLSTR-EXTRACT` GeoTIFF 文件组：
   `bt8.tif`、`bt9.tif`、`vza.tif`、`lat.tif`、`lon.tif` 和 `cloud.tif`。
3. `slstr/slstr_reconstruct.py` 的 `slstr_reconstruct()`：读取 `SLSTR-EXTRACT`，输出完整的
   `SLSTR-DATA` GeoTIFF，将坐标、云和 tie-point 角度对齐到热红外网格。
4. `slstr/slstr_data.py` 的 `add_lst_auxiliary()`：只接收 `SLSTR-DATA`，读取辅助 GeoTIFF，
   添加发射率、LAI、TCWV。
5. `slstr/slstr_lst.py` 的 `produce_slstr_lst()`：读取带辅助数据的 `SLSTR-DATA`，输出 `L2LST` GeoTIFF。
6. `slstr/slstr_project.py` 是可选的观测投影阶段，输入和输出仍然都是 `SLSTR-DATA` GeoTIFF，可插入
   重建之后、LST 之前。

MSG 使用固定网格，不需要 SLSTR 的几何重建：

1. `msg/msg_data.py` 的 `msg_extract()`：Satpy 读取 `.nat`，结合静态经纬度、观测角和云数据，
   输出 `MSG-DATA` GeoTIFF。
2. `msg/msg_data.py` 的 `add_lst_auxiliary()`：读取辅助 GeoTIFF，添加发射率、LAI 和 TCWV。
3. `msg/msg_lst.py` 的 `msg_lst()`：读取 `MSG-DATA`，输出 LST GeoTIFF。
4. `msg/msg_project.py` 是可选投影阶段，输入和输出都是 `MSG-DATA` GeoTIFF，必须在 LST 之前。
5. `msg/msg_region.py` 只在需要研究区拼接或裁剪时调用；结果阶段读取 LST GeoTIFF。

MSG 主数据的 TIFF 波段名称为 `bt8`、`bt9`、`vza`、`lat`、`lon` 和 `cloud`，内部热通道字段为
`bt8`、`bt9`，与已有处理数据保持一致。MSG LSCT 的多时相输入仍是独立的数值输入，不属于
上述单景 MSG-DATA 主链。

AHI、MODIS、VIIRS 和 ASTER 共用 `base/dual_thermal.py` 的双通道结构：案例负责把已经定标的
原生数组准备成 GeoTIFF，`*_extract()` 形成 `*-DATA.tif`，之后可选投影、区域处理和 `*_lst()`
输出 LST GeoTIFF。历史 prepared NPZ 仍可读取，但新阶段输出使用 GeoTIFF。

这些函数互不调用，可分别重跑。

## 两种空间路线

### 当前路线：单景先反演

```text
一个 SEN3
  → 解压
  → 原生提取
  → 几何重建（SLSTR-EXTRACT → SLSTR-DATA）
  → 添加 LST 辅助数据
  → LST 反演
```

SLSTR 单景处理必须先完成几何重建，但不要求先投影。需要统一分析网格、跨景拼接或与其他
栅格严格配准时，在重建后的 `SLSTR-DATA` 上显式调用 `slstr_project.py`。

### 多景扩展路线

```text
原始影像
  → 解压/提取
  → 几何重建
  → 可选投影
  → 每景 LST 或 LSCT
  → 统一网格后再拼接（按研究需要）
  → *_result_region() 按质量和不确定度选择重叠像元并裁剪
```

只有同一网格的 LST 输出才能进入 `*_result_region()`。LST 输出携带经纬度，可以用于
后续结果投影或裁剪。LSCT 的准备文件应同时保存
`latitude_deg`、`longitude_deg`，反演结果才可进入结果阶段。

每次 `*_data_region()` 或 `*_result_region()` 只接收一个逻辑影像组。相邻影像
必须同次获取、同视角、同目标网格；不同时间和不同视角分别处理。

## 产品级别

| 级别 | 内容 |
|---|---|
| L1O | 解码、定位和质量控制后的传感器观测 |
| L2LST | 地表温度、误差和质量标识 |
| L2LSCT | 组分温度、残差、条件数和质量标识 |
| L3N | 角度、时间、空间和传感器归一化结果；可选融合 |
| L3C | 时间合成及观测数量 |
| L4A | TVDI 等应用 |

## 归一化

归一化不包装成一个统一调用。case 脚本依次按需要调用：

- `normalization/angle.py`
- `normalization/time.py`
- `normalization/space.py`
- `normalization/sensor.py`
- `normalization/fusion.py`

每一步都有自己的输入目录、输出目录、年份和物理参数。
