# SLSTR cases

- `heihe/study_area_2022/`：黑河案例，采用 `study-area-first`；
- `europe_south_africa/scene_first_migrated/`：欧洲/南非逐景实现快照，采用
  `scene-first`，下次执行前应再拆成
  两个独立区域案例。

同时混有 ERA5、欧洲、南非和多台机器路径的批处理脚本已放到
`_archive/slstr/mixed_batch/`。新案例从 `_templates/` 创建，公共读取、重建、投影、
LST 和 LSCT 调用根目录 `slstr/` 模块。
