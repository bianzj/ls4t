# LS4T 项目关系

## 主项目

`/home/hero/work/ls4t` 是通用算法、产品结构、测试和文档的主项目，对应私有仓库
`bianzj/ls4t`。源码直接位于项目根目录：

- `aatsr/`、`slstr/`、`msg/`：传感器数据、投影、LST 和 LSCT；
- `modis/`、`viirs/`、`ahi/`、`aster/`：双热通道数据、投影、拼接和 LST；
- `base/`：公共反演、质量控制、产品读写和空间算法；
- `normalization/`：角度、时间、空间和传感器归一化；
- `composite/`、`applications/`：时间合成和 L4 应用；
- `cases/`：按传感器组织的实际执行快照、历史实验和独立项目索引。

## 独立 case 项目

| 本地目录 | GitHub 项目 | 定位 |
|---|---|---|
| `/home/hero/work/ls4t-aatsr-lsct` | `bianzj/ls4t-aatsr` | AATSR 逐景处理、0.01° 日/月统计和分析文件 |
| `/home/hero/work/ls4t-msg-lsct` | `bianzj/ls4t-msg` | MSG 投影、LSCT、月合成和验证 |
| `/home/hero/work/ls4t-slstr-lsct` | `bianzj/ls4t-slstr` | SLSTR 研究区优先与逐景优先流程 |

这三个目录是独立 Git 仓库，不共享主项目的 `.git`，也不再由 `git worktree` 管理。
每个独立仓库都以 `cases/official/` 作为正式生产入口，包含阶段登记、机器配置和当前
生产实现；旧目录名仅作为兼容符号链接。AATSR 的历史产品开发脚本已移到其独立仓库的
`cases/_archive/product_history/`。

主仓库同时在 `cases/aatsr/`、`cases/msg/`、`cases/slstr/` 保存指定提交的执行脚本快照，
因此单独克隆主仓库也能查看和复现流程。它们不是 submodule；同步关系由
`cases/projects.toml` 中的 `source_revision` 和 `official_path` 明确记录。修改主 LS4T
算法不会自动修改三个独立仓库；独立仓库升级所用框架版本后，应更新各自
`cases/official/case.toml` 的框架提交号，再同步本索引。

MODIS、VIIRS、AHI 尚无独立 case 仓库。已有脚本已经放入各自的
`cases/<sensor>/unclassified/legacy_draft/` 并登记为 `draft`；完成区域、机器路径、
依赖和结果验证后才可标记 `migrated` 或 `active`。四类传感器的机器无关处理接口已在
根目录建立；ASTER 当前没有可迁移的真实案例，`cases/aster/` 只保留待导入说明。

## 代码流动原则

1. 在 case 中经过实际数据验证的通用改进，整理后移入主项目根目录的传感器模块。
2. 独立项目更新主仓库快照时，整体同步对应 case，并更新 `source_revision`，不做无版本
   记录的零散双向复制。
3. case 可以保留本机绝对路径，但必须集中在脚本顶部；认证信息不能写入源码。
4. 数据、LST、LSCT 分开保存和执行，不增加统一总调度器。
5. 两种空间模式都保留：先形成完整研究区再反演，以及逐景反演后再拼接或裁剪。
6. 当前使用的多传感器流程按研究目标建立独立 case；尚未验证的旧联合脚本先放在
   `cases/_archive/shared/`，不能为了文件名方便重复归入两个传感器。

## 日常检查

```bash
git -C /home/hero/work/ls4t status --short --branch
git -C /home/hero/work/ls4t-aatsr-lsct status --short --branch
git -C /home/hero/work/ls4t-msg-lsct status --short --branch
git -C /home/hero/work/ls4t-slstr-lsct status --short --branch
```

项目状态、主仓库快照路径和入口见 `cases/README.md`、`cases/catalog.toml`、
`cases/projects.toml` 以及各自独立仓库的 README。
