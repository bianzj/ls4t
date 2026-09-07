# LS4T cases

`cases/` 保存针对具体传感器、研究区、年份和数据盘目录的实际运行案例。它与根目录
的通用产品代码分工如下：

- 根目录 `base/`、`aatsr/`、`msg/`、`slstr/`、`normalization/`：可复用算法；
- `cases/`：一次研究或产品生产所需的参数、路径、验证和批处理脚本；
- 原始数据、LST、LSCT、图像和日志：保存在外部数据盘，不进入 Git。

## 独立运行项目

三个当前使用的 case 已独立发布，并保留各自的历史算法和机器运行参数：

| 传感器 | 本地目录 | 私有 GitHub 项目 | 主要内容 |
|---|---|---|---|
| AATSR | `/home/hero/work/ls4t-aatsr-lsct` | `bianzj/ls4t-aatsr` | 逐景 LSCT、0.01° 日/月统计和月分析文件 |
| MSG | `/home/hero/work/ls4t-msg-lsct` | `bianzj/ls4t-msg` | 投影、LSCT、月合成、站点提取和验证 |
| SLSTR | `/home/hero/work/ls4t-slstr-lsct` | `bianzj/ls4t-slstr` | 研究区优先和逐景优先两种处理路线 |

这些项目是独立 Git 仓库，不是 worktree，也不作为 Python 包依赖嵌入主项目。这样可
避免主项目整理影响正在运行的案例。可复用的改进应整理到主项目；案例采用某次主项目
实现时，应在对应 README 或提交信息中记录来源提交。

## 仓库内案例

当前目录还保留 `AATSR_product/`、`MSG/`、`msg-fit/`、`msg-lsct/`、`slstr-lsct/`
以及早期 `case1/`、`case2/`。原根目录中的 `aatsr_lst/`、`msg_lst/`、`slstr_lst/`
和旧数据整理脚本已集中到 `legacy/`；它们使用的旧 `base/util_*` 模块位于
`_legacy_support/base/`。这些内容用于历史结果复现和迁移检查，不是新的公共 API。

必须运行仓库内旧案例时，从项目根目录显式加入兼容路径，例如：

```bash
PYTHONPATH=cases/_legacy_support:. python cases/legacy/aatsr_lst/aatsr_lst.py
```

旧文件中可能仍有未解决的历史分支冲突或过期绝对路径；实际生产优先使用上面的三个
独立 case 项目。

新增案例时应放在明确命名的子目录中，并做到：

1. 参数集中在脚本顶部，不引入统一 CLI；
2. 数据、LST、LSCT 分阶段运行；
3. 明确采用“先形成研究区再反演”或“逐景反演后再拼接/裁剪”；
4. 不提交认证信息、数据产品、缓存、日志和本机生成图；
5. 通用算法放回根目录模块，案例脚本只保留数据选择和运行参数。
