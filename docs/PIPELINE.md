# 产品处理关系

## 传感器产品

```text
AATSR-DATA → AATSR-LST / AATSR-LSCT
SLSTR-DATA → SLSTR-LST / SLSTR-LSCT
MSG-DATA   → MSG-LST   / MSG-LSCT
```

数据文件负责解压、原生读取、重建、投影或存放；温度文件只读取已经准备好的数据并反演产品。

SLSTR 数据阶段被明确拆开：

1. `slstr/slstr_unzip.py` 的 `slstr_unzip()`：压缩包到 SEN3。
2. `slstr/slstr_extract.py` 的 `slstr_extract()`：读取原生数组，不做网格重建。
3. `slstr/slstr_reconstruct.py` 的 `slstr_reconstruct()`：把坐标、云和 tie-point 角度对齐到热红外网格。
4. `slstr/slstr_project.py` 的 `slstr_project()`：投影到指定目标栅格。
5. `slstr/slstr_merge.py` 的 `slstr_merge()`：按日期和视角合并同网格场景。

这些函数互不调用，可分别重跑。

## 两种空间路线

### 路线 A：先研究区，后反演

```text
相邻原始影像
  → 解压/提取
  → 每景投影到同一网格
  → *_data_region() 选择清晰且观测角较小的重叠像元并裁剪
  → 研究区 LST 或 LSCT
```

SLSTR 使用 `slstr_project.py`；AATSR 和 MSG 分别使用新增的
`aatsr_project.py`、`msg_project.py`。如果 MSG 原始固定网格就是分析网格，可以
跳过投影，直接把单个数据产品交给 `msg_data_region()` 裁剪。

### 路线 B：先逐景反演，后研究区

```text
原始影像
  → 解压/提取
  → 每景投影到同一网格
  → 每景 LST 或 LSCT
  → *_result_region() 按质量和不确定度选择重叠像元并裁剪
```

LST 输出携带经纬度，可以直接进入结果阶段。LSCT 的准备文件应同时保存
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
