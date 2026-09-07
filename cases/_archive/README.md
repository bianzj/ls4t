# Archived cases

这里的文件没有删除，只是退出当前工作视图。它们可能含重复实现、旧绝对路径、历史
结果图、旧跨传感器脚本或兼容模块。

- `aatsr/product_history/`：早期 AATSR 产品与大量备份版本；
- `msg/`：整理前快照、拟合实验和旧验证；
- `slstr/mixed_batch/`：同时混入欧洲、南非和多台机器路径的批处理；
- `shared/`：旧跨传感器和下载脚本；
- `legacy/`、`compatibility/`：未分类历史代码及其旧 `base` 依赖。

归档代码不列为生产入口，也不要求通过当前依赖环境的运行测试。需要恢复时，应复制到
`cases/<sensor>/<region>/<case-id>/`，填写 `case.toml`，拆出机器配置并验证后再标记 active。
MODIS、VIIRS、AHI 的单传感器历史方法已经移到可见的 `draft` 案例，不再放在这里。
