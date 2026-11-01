# LS4T 当前项目关系与目录

Windows 主代码目录为 `C:\work\ls4t`，对应 LS4T 主仓库。公共算法在 `base/`，
当前具体任务在 `cases/`，网页工作台在 `gui/`。日常修改在此目录进行。

| 位置 | 用途 |
|---|---|
| `C:\work\ls4t\base` | 公共算法、传感器处理和可复制参考脚本 |
| `C:\work\ls4t\docs` | 现有理论、实现思路、流程与发布说明 |
| `C:\work\ls4t\tests` | 自动化测试及小范围固定输入 |
| `C:\work\ls4t\cases` | 当前案例脚本、配置和三站固定小样本 |
| `D:\发布\ls4t\安装文件` | 按版本保留 Windows 安装包、源码 ZIP、依赖及校验记录 |
| `D:\发布\ls4t\推广案例` | 对外案例、固定输入、参考结果与本轮重放回执 |
| `D:\cases\ls4t` | 既有完整研究结果、历史批次与来源记录，保留原路径 |
| `C:\project\ls4t\organize-20261101` | 本轮整理备份、构建日志和验收证据 |

TIRT 和 LS4T 是 STREAM 的方法基础，各自代码独立维护。本文不将 LS4T 的理论、
案例或安装版等同于 STREAM 全系统验收。

历史曾有 `ls4t-aatsr`、`ls4t-msg`、`ls4t-slstr` 等独立项目和收编记录。
旧 Linux 路径及 `cases/projects.toml` 不作为当前 Windows 活动入口。
此前代码收编、数据迁移的具体证据保留在原 `D:\cases\ls4t` 记录中；
本轮不恢复已移除的工作副本，也不改变论文、影像或历史产品。

当前实际案例清单见 [cases/README.md](../cases/README.md)。完整原始数据继续使用各任务
显式配置的 F/H/E 等已有位置；不要为目录统一而复制整套遥感归档。
