# LS4T 项目关系

## 主项目

`/home/hero/work/ls4t` 是通用算法、产品结构、测试和文档的主项目，对应私有仓库
`bianzj/ls4t`。源码直接位于项目根目录：

- `aatsr/`、`slstr/`、`msg/`：传感器数据、投影、LST 和 LSCT；
- `base/`：公共反演、质量控制、产品读写和空间算法；
- `normalization/`：角度、时间、空间和传感器归一化；
- `composite.py`、`applications.py`：时间合成和 L4 应用；
- `cases/`：实际案例、历史实验和独立 case 项目索引。

## 独立 case 项目

| 本地目录 | GitHub 项目 | 定位 |
|---|---|---|
| `/home/hero/work/ls4t-aatsr-lsct` | `bianzj/ls4t-aatsr` | AATSR 逐景处理、0.01° 日/月统计和分析文件 |
| `/home/hero/work/ls4t-msg-lsct` | `bianzj/ls4t-msg` | MSG 投影、LSCT、月合成和验证 |
| `/home/hero/work/ls4t-slstr-lsct` | `bianzj/ls4t-slstr` | SLSTR 研究区优先与逐景优先流程 |

这三个目录是独立 Git 仓库，不共享主项目的 `.git`，也不再由 `git worktree` 管理。
独立仓库保存与数据盘、年份、区域和一次运行紧密绑定的内容，主项目保存可复用实现。

## 代码流动原则

1. 在 case 中经过实际数据验证的通用改进，整理后移入主项目对应传感器目录。
2. 主项目的新实现用于 case 时，由 case 主动更新并记录主项目提交，不自动同步。
3. case 可以保留本机绝对路径，但必须集中在脚本顶部；认证信息不能写入源码。
4. 数据、LST、LSCT 分开保存和执行，不增加统一总调度器。
5. 两种空间模式都保留：先形成完整研究区再反演，以及逐景反演后再拼接或裁剪。

## 日常检查

```bash
git -C /home/hero/work/ls4t status --short --branch
git -C /home/hero/work/ls4t-aatsr-lsct status --short --branch
git -C /home/hero/work/ls4t-msg-lsct status --short --branch
git -C /home/hero/work/ls4t-slstr-lsct status --short --branch
```

三个 case 的更详细内容见 `cases/README.md` 和各自独立仓库的 README。
