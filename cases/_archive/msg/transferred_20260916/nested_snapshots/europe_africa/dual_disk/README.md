# MSG Europe + Africa dual disk

该案例联合 MSG 欧洲盘和 IODC 观测，包含：

- `preprocess/`：原始数据和静态网格准备；
- `lsct/`：双视角/双星盘 LSCT、月平均及显示；
- `field/`：站点提取；
- `auxiliary/`、`download/`：辅助数据步骤。

目前是从实际运行仓库迁入的快照，科学脚本尚未统一读取 `machines/*.toml`，因此状态为
`migrated`。下一次正式运行前，应先选定 Hero 或 macOS profile，并把该次使用的脚本
路径改为读取 profile；无需一次性重写所有历史版本。
