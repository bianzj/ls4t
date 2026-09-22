# LS4T cases

这里就是**执行案例区**：`cases/<sensor>/<region>/<case-id>/` 下的脚本用真实数据、真实
机器路径跑生产。参考实现不在这里——参考是根目录的传感器包（`slstr/`、`msg/`、`aatsr/`、
`base/` 等），`cases/` 下不再分"参考"和"案例"。

```text
cases/
├── _templates/                    新建案例的脚手架（工具，不是参考实现）
│   ├── README.md                  案例结构、运行方式和模板说明
│   ├── new_case.py                从模板生成 cases/<sensor>/<region>/<case-id>/
│   ├── audit_cases.py             结构审计，不执行科学代码
│   └── case/                      案例骨架（case.toml、machines、stages）
├── _archive/                      归档区
│   ├── aatsr/、msg/、slstr/       逐次迁移留下的历史归档
│   └── legacy/、shared/、compatibility/  更早的旧实现与兼容层
├── aatsr/  msg/  slstr/  aster/   执行案例
├── catalog.toml                   案例登记
└── projects.toml                  独立运行项目的来源索引
```

执行案例目前有：`aatsr/`（全球 0.01° 日/月生产 + 全图 LSCT 变体 + 站点）、
`msg/`（下载/提取/投影/LST/LSCT + 站点测试与复现）、
`slstr/`（解压/重整/投影/LST/LSCT 五环节 + 两个旧区域快照）、`aster/`（待导入说明）。
每个案例里有什么见各自的 `README.md`、`case.toml`，以及 `catalog.toml`、`projects.toml`。

## 三层边界仍然有效

```text
根目录模块（base/、aatsr/、msg/、slstr/、…）   标准、可复用的参考实现
tests/                                          合成数据自动化测试
cases/_templates/                               新建案例的模板与审计工具
```

参考侧（根目录模块）保存解压、投影、提取、LST/LSCT 反演、角度拟合核等的标准实现；
`base/` 里为执行案例补的 `kernel.py`、`lsct_window.py`、`metrics.py`、`fitting.py`、
`rt/` 等也属于参考侧，案例脚本只从这些模块导入。

## 新建案例

```bash
python cases/_templates/new_case.py slstr heihe summer-2022 --mode study-area-first
python cases/_templates/audit_cases.py
```

审计只会检查带 `case.toml` 的登记案例；`_archive/` 下的目录会被跳过，所以当前
4 个在用案例会输出 `OK: 4 registered cases`。
