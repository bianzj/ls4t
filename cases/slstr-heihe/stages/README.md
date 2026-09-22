# Case-specific stages

这里只放标准模块无法替案例决定的内容，例如：

- 下载清单和认证后的下载命令；
- 相邻轨道、时次和视角的明确分组；
- `study-area-first` 的数据拼接/裁剪清单；
- `scene-first` 的结果拼接/裁剪清单；
- LSCT `observed_radiance`、`effective_weights` 和不确定度的准备；
- 研究区验证、图表和批处理/服务配置。

建议按 `01_download.py`、`02_group_scenes.py`、`03_prepare_lsct.py`、
`04_validate.py` 命名。阶段之间只通过已保存的文件传递，不在 import 时自动运行。
