# MSG cases

当前只展示 `europe_africa/dual_disk/`，包含 MSG 欧洲盘与 IODC 非洲区域的投影、LSCT、
月合成和站点分析。根目录标准 MSG 主链为 `.nat → MSG-DATA.tif → 可选投影.tif → LST.tif`；
静态定位和 LST 辅助数据均使用 GeoTIFF。原脚本仍含 Hero 与 macOS 路径，已建立两个 machine
profile；完成路径读取改造前状态为 `migrated`。

显示实验、旧验证和整理前快照已放到 `_archive/msg/`。
