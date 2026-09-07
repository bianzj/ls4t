# SLSTR cases

来自私有项目 `bianzj/ls4t-slstr@f4bc61b` 的当前执行快照按空间策略拆开：

- `study_area/`：先把相邻观测形成完整研究区，再进行 LST/LSCT。
- `scene_first/`：逐景完成 LST/LSCT，再拼接或裁剪研究区结果。
- `batch/`：批量解压、数据准备、ERA5 辅助数据和现有批处理入口。

新增脚本必须明确属于前两条路线之一；公共的 SLSTR 读取、投影和反演函数放在根目录
`slstr/`，不要复制回案例。
