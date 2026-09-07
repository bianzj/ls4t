# Shared cases

这里只放确实服务多个传感器的实际执行材料：

- `download/laads/`：MODIS 与 VIIRS 共用的 LAADS 下载脚本；
- `cross_sensor/slstr_ahi/`：SLSTR-AHI 时空匹配和联合 LSCT 实验；
- `cross_sensor/stream_msg/`：STREAM 与 MSG 的数据融合实验。

可复用算法仍应放在根目录模块，不能因多个案例都复制了一份而长期留在这里。
