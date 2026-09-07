# LS4T cases

`cases/` 保存真实生产、研究区实验和历史复现实例。根目录保存通用算法，`tests/`
保存自动化测试；机器路径、年份、区域参数、批处理入口和阶段性脚本只放在这里。

## 目录

| 目录 | 状态 | 内容 |
|---|---|---|
| `aatsr/` | active | AATSR 0.01° 日/月统计、LST/LSCT 与历史产品实验 |
| `msg/` | active | MSG 投影、LSCT、月合成、站点提取和验证 |
| `slstr/` | active | SLSTR 研究区优先、逐景优先和批处理流程 |
| `modis/` | legacy | MODIS 数据准备、LST 和辅助数据脚本 |
| `viirs/` | legacy | VIIRS 数据准备、LST 和辅助数据脚本 |
| `ahi/` | legacy | AHI 数据、LST、角度/时间归一化和不确定性实验 |
| `shared/` | mixed | LAADS 下载及 SLSTR-AHI 等跨传感器案例 |
| `examples/` | example | 最小的手工运行示例，不代替 `tests/` |
| `legacy/` | archive | 尚未按传感器归类的早期快照和兼容代码 |

机器生成的数据、缓存、日志和结果图不应继续加入 Git。已经存在的结果材料保留在相应
`archive/` 或历史目录中，仅用于追溯。

## 当前生产案例与来源

AATSR、MSG、SLSTR 的实际执行脚本已收录到本仓库。三个独立私有仓库继续作为运行
项目和上游来源；这里保存可审查的脚本快照，不使用 submodule。来源提交和入口见
`projects.toml`，传感器状态和处理方式见 `catalog.toml`。同步时应以独立仓库的一个明确
提交更新整个对应目录，并同时修改来源提交，避免两个版本含义不明。

| 传感器 | 本仓库执行目录 | 独立私有项目 |
|---|---|---|
| AATSR | `aatsr/production/global_001deg/` | `bianzj/ls4t-aatsr` |
| MSG | `msg/lsct/`、`msg/preprocess/`、`msg/field/` | `bianzj/ls4t-msg` |
| SLSTR | `slstr/study_area/`、`slstr/scene_first/`、`slstr/batch/` | `bianzj/ls4t-slstr` |

## 两种空间处理方式

每个实际案例必须明确选择一种方式，不在同一批次中隐式混合：

1. `study-area-first`：下载相邻影像 → 提取/投影 → 拼接或裁剪成完整研究区 →
   对研究区整体运行 LST/LSCT。
2. `scene-first`：逐景提取/投影 → 逐景运行 LST/LSCT → 完成后拼接或裁剪结果。

SLSTR 已按这两个名称分目录。MSG 固定网格通常接近第一种方式；AATSR 全球 0.01°
统计属于逐景处理后再做日/月聚合。

## 新增和整理规则

1. 按 `cases/<sensor>/<case-name>/` 放置，不能再直接堆到 `cases/` 最外层。
2. 在 `catalog.toml` 登记传感器、状态、入口、空间处理方式和外部依赖。
3. 参数可集中在脚本顶部；通用计算函数应移回根目录模块。
4. 不提交凭据、原始影像、产品、缓存和日志。
5. 从 `old/` 迁入但尚未验证的脚本标为 `legacy`，不能直接标为生产入口。

历史脚本可能仍有旧绝对路径。需要运行时，从项目根目录显式加入兼容路径：

```bash
PYTHONPATH=cases/_legacy_support:. python cases/legacy/aatsr_lst/aatsr_lst.py
```
