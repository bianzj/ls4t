# 旧代码迁移对应关系

| 现有代码 | 新位置 |
|---|---|
| AATSR 解压、读取和存放 | `base/aatsr/aatsr_data.py` |
| AATSR 投影、研究区拼接/裁剪 | `base/aatsr/aatsr_project.py`、`base/aatsr/aatsr_region.py` |
| AATSR 分裂窗温度 | `base/aatsr/aatsr_lst.py` |
| AATSR 组分温度 | `base/aatsr/aatsr_lsct.py` |
| SLSTR 数据模型和单景读写 | `base/slstr/slstr_data.py` |
| SLSTR 解压 | `base/slstr/slstr_unzip.py` |
| SLSTR 提取 | `base/slstr/slstr_extract.py` |
| SLSTR 重建 | `base/slstr/slstr_reconstruct.py` |
| SLSTR 投影 | `base/slstr/slstr_project.py` |
| SLSTR 合并 | `base/slstr/slstr_merge.py` |
| SLSTR 两种空间处理方式 | `base/slstr/slstr_region.py` |
| SLSTR 分裂窗温度 | `base/slstr/slstr_lst.py` |
| SLSTR 组分温度 | `base/slstr/slstr_lsct.py` |
| MSG SEVIRI 读取 | `base/msg/msg_data.py` |
| MSG 投影、研究区拼接/裁剪 | `base/msg/msg_project.py`、`base/msg/msg_region.py` |
| MSG 温度和组分温度 | `base/msg/msg_lst.py`、`base/msg/msg_lsct.py` |
| MODIS 数据、投影、拼接和温度 | `base/modis/modis_data.py`、`base/modis/modis_project.py`、`base/modis/modis_merge.py`、`base/modis/modis_lst.py` |
| VIIRS 数据、投影、拼接和温度 | `base/viirs/viirs_data.py`、`base/viirs/viirs_project.py`、`base/viirs/viirs_merge.py`、`base/viirs/viirs_lst.py` |
| AHI 数据、投影、拼接和温度 | `base/ahi/ahi_data.py`、`base/ahi/ahi_project.py`、`base/ahi/ahi_merge.py`、`base/ahi/ahi_lst.py` |
| ASTER 数据、投影、拼接和温度 | `base/aster/aster_data.py`、`base/aster/aster_project.py`、`base/aster/aster_merge.py`、`base/aster/aster_lst.py` |
| 角度归一化 | `base/normalization/angle.py` |
| 地方太阳时归一化 | `base/normalization/time.py` |
| 网格和空间归一化 | `base/normalization/space.py` |
| 传感器标定 | `base/normalization/sensor.py` |
| 数据融合 | `base/normalization/fusion.py` |
| 月平均和时间合成 | `base/composite/temporal.py` |
| TVDI 等应用 | `base/applications/tvdi.py` |

旧工作区不覆盖，继续用于逐传感器实际数据回归。新源码不再依赖个人目录、`production/`、`retrieval/` 或统一 CLI。
