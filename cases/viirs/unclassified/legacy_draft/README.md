# VIIRS legacy draft case

这些脚本从 `old/` 迁入，当前登记状态为 `draft`：`data/`、`lst/`、`auxiliary/` 和
`tools/` 分别保存数据准备、LST、VNP 辅助数据和修补工具。旧 LAADS 下载脚本位于
`cases/_archive/shared/legacy_cross_sensor/download/laads/`。

代码仍含 Windows 盘符、旧 `util` 依赖和直接执行逻辑。入口仅标记处理方法；在确定区域、
产品版本和机器配置并完成结果验证前，不能作为生产入口。
