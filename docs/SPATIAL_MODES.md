# SLSTR 空间处理方式

当前以逐景处理为主，不自动调度多景拼接。多景处理在后续需要时再显式增加统一网格步骤。

## 当前方式：单景优先

适用于当前零散下载、逐景处理的场景。

```text
raw
  → extract
  → reconstruct to SLSTR-DATA
  → attach LST auxiliary data
  → LST
```

运行入口：

| 传感器 | 投影（可选） | 形成研究区数据 |
|---|---|---|
| AATSR | `base/aatsr/aatsr_project.py` | `aatsr_data_region()` |
| SLSTR | `base/slstr/slstr_project.py` | `slstr_data_region()` |
| MSG | `base/msg/msg_project.py`（可选） | `msg_data_region()` |
| MODIS | `base/modis/modis_project.py` | `modis_data_region()` |
| VIIRS | `base/viirs/viirs_project.py` | `viirs_data_region()` |
| AHI | `base/ahi/ahi_project.py`（可选） | `ahi_data_region()` |
| ASTER | `base/aster/aster_project.py` | `aster_data_region()` |

当前 SLSTR 单景流程必须先执行 `slstr_reconstruct.py`，生成 `SLSTR-DATA` 后才能添加
辅助数据和执行 LST。`slstr_project.py` 和 `slstr_data_region()` 仍是可选的空间处理阶段。
进入 LST 时，`auxiliary_file` 必须包含发射率、LAI 和水汽，并且数组必须是标量或与
当前热红外网格形状一致。

## 多景扩展

适用于先独立处理每景影像、保留逐景结果，最后再拼接或裁剪。

```text
raw
  → extract
  → reconstruct to SLSTR-DATA
  → optional project
  → LST / LSCT for each scene
  → common-grid result
  → result_region (mosaic + optional crop)
```

运行入口：

| 传感器 | 逐景结果后处理 |
|---|---|
| AATSR | `aatsr_result_region()` |
| SLSTR | `slstr_result_region()` |
| MSG | `msg_result_region()` |
| MODIS | `modis_result_region()` |
| VIIRS | `viirs_result_region()` |
| AHI | `ahi_result_region()` |
| ASTER | `aster_result_region()` |

结果拼接先排除质量标识不可用的像元；多个有效结果重叠时，LST 优先采用不确定度
较小的结果，LSCT 按输入文件顺序选择。这样不会在拼接阶段重新执行反演。

## 参数约定

各传感器的 `*_region.py` 函数由 case 显式接收：

- `DATA_INPUT` / `DATA_OUTPUT`：方式一的输入组和输出文件。
- `RESULT_INPUT` / `RESULT_OUTPUT`：方式二的输入组和输出文件。
- `STUDY_BOUNDS`：`(west, south, east, north)`；设为 `None` 时只拼接不裁剪。
- `INPUT_PATTERN`：目录输入时使用的文件匹配模式。

空间阶段不负责判断哪些轨道或时次属于同一组。分组是科学处理条件，应由运行人员
根据过境时间、轨道和视角明确选择。
