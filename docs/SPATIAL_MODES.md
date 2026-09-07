# 两种空间处理方式

LS4T 同时保留“研究区优先”和“逐景优先”，二者没有自动总调度器。运行人员按
研究目的选择一条路线，并在 `cases/` 的执行脚本中配置参数。

## 方式一：研究区优先

适用于先下载覆盖研究区的相邻影像，再把研究区作为一个整体计算。

```text
raw
  → extract
  → project each scene
  → data_region (mosaic + optional crop)
  → attach LST auxiliary data when needed
  → LST / prepared LSCT input → LSCT
```

运行入口：

| 传感器 | 投影 | 形成研究区数据 |
|---|---|---|
| AATSR | `aatsr/aatsr_project.py` | `aatsr_data_region()` |
| SLSTR | `slstr/slstr_project.py` | `slstr_data_region()` |
| MSG | `msg/msg_project.py`（可选） | `msg_data_region()` |

研究区拼接在重叠位置优先选择无云且观测天顶角较小的像元。输入可以是一个目录，
也可以是明确的 NPZ 文件列表。一个输入组只能包含同一次获取和同一视角的数据。
进入 LST 时，如果数据产品尚无发射率、LAI 和水汽，case 必须向三个 `*_lst.py`
显式传入 `auxiliary_file`；该 NPZ 必须是标量或与当前研究网格形状一致。

## 方式二：逐景优先

适用于先独立处理每景影像、保留逐景结果，最后再拼接或裁剪。

```text
raw
  → extract
  → project each scene
  → LST / LSCT for each scene
  → result_region (mosaic + optional crop)
```

运行入口：

| 传感器 | 逐景结果后处理 |
|---|---|
| AATSR | `aatsr_result_region()` |
| SLSTR | `slstr_result_region()` |
| MSG | `msg_result_region()` |

结果拼接先排除质量标识不可用的像元；多个有效结果重叠时，LST 优先采用不确定度
较小的结果，LSCT 按输入文件顺序选择。这样不会在拼接阶段重新执行反演。

## 参数约定

三个 `*_region.py` 函数由 case 显式接收：

- `DATA_INPUT` / `DATA_OUTPUT`：方式一的输入组和输出文件。
- `RESULT_INPUT` / `RESULT_OUTPUT`：方式二的输入组和输出文件。
- `STUDY_BOUNDS`：`(west, south, east, north)`；设为 `None` 时只拼接不裁剪。
- `INPUT_PATTERN`：目录输入时使用的文件匹配模式。

空间阶段不负责判断哪些轨道或时次属于同一组。分组是科学处理条件，应由运行人员
根据过境时间、轨道和视角明确选择。
