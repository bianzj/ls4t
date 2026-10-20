# MSG 方法对照

本目录保留独立科学方法和诊断入口。正式产品仍由上一级的
`msg_lsct_iter.py` 生成；这些脚本未改变数值实现。

| 当前文件 | 旧文件名 | 用途 |
|---|---|---|
| `msg_lsct_2c_window.py` | `msg_lsct_2c_full.py` | 土壤/植被两组分窗口最小二乘 |
| `msg_lsct_3c_window.py` | `msg_lsct_3c_full.py` | 三组分窗口最小二乘基线 |
| `msg_lsct_3c_two_stage.py` | `msg_lsct_3c_2stage_full.py` | 无约束两阶段三组分对照 |
| `msg_lsct_3c_constrained.py` | `msg_lsct_3c_constrained_full.py` | 全向量化约束解对照 |
| `msg_lsct_3c_diagnostics.py` | `msg_lsct_3c_show_full.py` | 组分反演及逐景诊断出图 |

在仓库根目录执行。运行前按目标案例核对脚本中的数据路径、时间和输出目录；
这些历史全区域脚本不等同于 `tests/examples/msg_evo_sample.py` 的小窗口离线测试。

旧路径已撤销，`cases/catalog.toml`、`cases/msg/case.toml` 和依赖测试均使用新路径。
