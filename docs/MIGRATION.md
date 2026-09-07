# 旧代码迁移对应关系

| 现有代码 | 新位置 |
|---|---|
| AATSR 解压、读取和存放 | `aatsr/aatsr_data.py` |
| AATSR 投影、研究区拼接/裁剪 | `aatsr/aatsr_project.py`、`aatsr/aatsr_region.py` |
| AATSR 分裂窗温度 | `aatsr/aatsr_lst.py` |
| AATSR 组分温度 | `aatsr/aatsr_lsct.py` |
| SLSTR 数据模型和单景读写 | `slstr/slstr_data.py` |
| SLSTR 解压 | `slstr/slstr_unzip.py` |
| SLSTR 提取 | `slstr/slstr_extract.py` |
| SLSTR 重建 | `slstr/slstr_reconstruct.py` |
| SLSTR 投影 | `slstr/slstr_project.py` |
| SLSTR 合并 | `slstr/slstr_merge.py` |
| SLSTR 两种空间处理方式 | `slstr/slstr_region.py` |
| SLSTR 分裂窗温度 | `slstr/slstr_lst.py` |
| SLSTR 组分温度 | `slstr/slstr_lsct.py` |
| MSG SEVIRI 读取 | `msg/msg_data.py` |
| MSG 投影、研究区拼接/裁剪 | `msg/msg_project.py`、`msg/msg_region.py` |
| MSG 温度和组分温度 | `msg/msg_lst.py`、`msg/msg_lsct.py` |
| MODIS 数据、投影、拼接和温度 | `modis/modis_data.py`、`modis/modis_project.py`、`modis/modis_merge.py`、`modis/modis_lst.py` |
| VIIRS 数据、投影、拼接和温度 | `viirs/viirs_data.py`、`viirs/viirs_project.py`、`viirs/viirs_merge.py`、`viirs/viirs_lst.py` |
| AHI 数据、投影、拼接和温度 | `ahi/ahi_data.py`、`ahi/ahi_project.py`、`ahi/ahi_merge.py`、`ahi/ahi_lst.py` |
| ASTER 数据、投影、拼接和温度 | `aster/aster_data.py`、`aster/aster_project.py`、`aster/aster_merge.py`、`aster/aster_lst.py` |
| 角度归一化 | `normalization/angle.py` |
| 地方太阳时归一化 | `normalization/time.py` |
| 网格和空间归一化 | `normalization/space.py` |
| 传感器标定 | `normalization/sensor.py` |
| 数据融合 | `normalization/fusion.py` |
| 月平均和时间合成 | `composite/temporal.py` |
| TVDI 等应用 | `applications/tvdi.py` |

旧工作区不覆盖，继续用于逐传感器实际数据回归。新源码不再依赖个人目录、`production/`、`retrieval/` 或统一 CLI。
