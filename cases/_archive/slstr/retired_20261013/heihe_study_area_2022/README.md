# 已归档：历史 SLSTR 快照

2026-10-13 退出当前案例登记。以下保留历史说明；脚本依赖已移除的 `base.util_*`，不能直接作为当前入口运行。重复文件已按 `cases/_archive/DEDUPLICATED_FILES.json` 去重，恢复完整历史目录请使用清理前备份。

# SLSTR Heihe 2022

黑河研究区优先案例：先把相邻影像准备为完整研究区，再进行 LST/LSCT。现有脚本位于
`study_area/`，机器路径记录在 `machines/hero.toml`。

当前状态为 `migrated`：它是可追溯的实际实现，但仍使用旧 GeoTIFF/HDF5 工具和脚本内
绝对路径。下一次运行时按 `base/templates/case/` 补充分阶段脚本并逐步调用 `base/` 中的标准模块。
