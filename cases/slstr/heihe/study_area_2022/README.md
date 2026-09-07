# SLSTR Heihe 2022

黑河研究区优先案例：先把相邻影像准备为完整研究区，再进行 LST/LSCT。现有脚本位于
`study_area/`，机器路径记录在 `machines/hero.toml`。

当前状态为 `migrated`：它是可追溯的实际实现，但仍使用旧 GeoTIFF/HDF5 工具和脚本内
绝对路径。下一次运行时按 `_templates/case/` 补充分阶段脚本并逐步调用根目录标准模块。
