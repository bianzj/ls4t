# LS4T 当前案例

案例保存具体任务的代码、配置和说明。完整输入与运行结果在仓库外；少量固定样本用于离线复现。

| 当前目录 | 定位 | 状态与边界 |
|---|---|---|
| [黑河三站 3×3](ahi-slstr/heihe/three-site-kernel-3x3/README.md) | 2019-05-12 大满、阿柔、四道桥 AHI+SLSTR 联合角度核拟合 | 含固定 27 组输入、参考结果及离线重放；AHI 参与拟合，阿柔质量拒绝 |
| [黑河原窗口](ahi-slstr/heihe/three-site-kernel/README.md) | 较早窗口实验 | 保留原实现；不与 3×3 固定样本混为同一批次 |
| [Amazon 三组分试验](slstr/amazon-3component-feasibility/README.md) | SLSTR 三组分可行性与低温筛选 | 使用外部现存 LST、LAI；不是独立精度验证，结果位于 E 盘显式配置目录 |
| [非洲下载](slstr-africa/README.md) | Earthdata 数据获取 | 需要账号与联网；本轮不执行下载，不随对外案例分发认证信息 |
| [_archive](_archive/README.md) | 历史脚本 | 不作为当前生产或对外推广入口 |

对外推广以 `D:\发布\ls4t\推广案例` 的说明、固定数据和验证回执为准。
历史 MSG 完整结果仍在 `D:\cases\ls4t\msg\official-results`；不把其精度直接归给当前代码。

新案例从 [通用参考脚本](../base/templates/references/README.md) 复制所需方法，按区域和时间组织，
显式写入数据与输出路径。见 [新建工具说明](../base/templates/README.md) 和
[案例工作流程](../docs/CASE_WORKFLOW.md)。

旧 `catalog.toml`、`projects.toml` 及 AATSR/MSG 等旧执行根目录已不在当前活动工作树。
现存 `base/aatsr`、`base/msg` 等算法仍保留；不恢复已移除的任务目录，不把归档当作已验收生产入口。
