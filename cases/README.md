# LS4T cases

这里是**执行案例区**：每个子目录是一个单独的执行案例，用真实数据、真实机器路径运行。
函数和模板都在 `base/`，案例只从 `base` 导入；怎么用不做限制——可以从
`base/templates/` 复制模板改配置运行，也可以直接写脚本调用 `base/` 中的函数。

```text
cases/
├── aatsr/  msg/  slstr/  aster/   各传感器的执行案例
├── slstr-heihe/ slstr-europe/ slstr-america/  由模板生成的 SLSTR 日拼接案例
├── msg/experiments/               MSG 方法对照，独立于正式反演
├── _archive/                      归档区
│   ├── aatsr/、msg/、slstr/       逐次迁移留下的历史归档
│   └── legacy/、shared/、compatibility/  更早的旧实现与兼容层
├── catalog.toml                   案例登记
└── projects.toml                  独立运行项目的来源索引
```

执行案例目前有：`aatsr/`（全球 0.01° 日/月生产 + 全图 LSCT 变体 + 站点）、
`msg/`（下载/提取/投影/LST/LSCT + 站点测试与复现）、
`slstr/`（解压/重整/投影/LST/LSCT 五环节；旧区域快照已归档）、`aster/`（待导入说明），
以及 `slstr-heihe/`、`slstr-europe/`、`slstr-america/` 三个模板案例。
每个案例里有什么见各自的 `README.md`、`case.toml`，以及 `catalog.toml`、`projects.toml`。

## 边界

```text
base/             函数库：标准、可复用的实现（解压、投影、提取、LST/LSCT、角度核、rt/ 等）
base/templates/   案例模板与审计工具
tests/            合成与真实输入自动化测试
cases/            执行案例：路径、年份、研究区、并行和调度
```

案例中写的计算如果被两个以上案例用到、且不再依赖具体路径/区域，就整理进 `base/` 并补测试。

## 新建案例

```bash
python base/templates/new_case.py slstr heihe summer-2022 --mode study-area-first
python base/templates/audit_cases.py
```

审计只检查 `catalog.toml` 中登记、带 `case.toml` 的案例；`_archive/` 下的目录会被跳过。
