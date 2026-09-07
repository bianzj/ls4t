# AATSR cases

- `production/global_001deg/`：来自私有项目 `bianzj/ls4t-aatsr@f95acc7` 的当前
  执行快照，包括逐景 LST/LSCT、0.01° 日/月统计、云筛选统计和三变量月产品。
- `product/`：较早的 AATSR 产品、站点验证和参数实验，保留用于复现。

生产入口及同步版本记录在 `../projects.toml` 和 `../catalog.toml`。数据盘路径和运行
年份属于案例配置，不应迁入根目录通用模块。
