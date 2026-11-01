# 代码复制与案例执行边界

2026-10-24：组装指代码级复制、修改和串接。`base/` 保存小零件的通用原版；
`base/templates/references/` 保存少量可复制的完整参考；具体案例持有自己的执行代码和函数副本。

```text
base/                         算法原版、单产品读写和数组计算
base/templates/references/    通用参考组装，供复制选取
cases/slstr/heihe/2022/       示例：一个卫星的具体工作
cases/slstr-modis/heihe/2022/ 示例：几个卫星联合处理的具体工作
    run.py                   参数、数据路径、复制来的函数、循环与执行顺序
    functions.py             可选：函数较多时放本地文件，无跨案例依赖
D:/your-input-location/<task>/     外部数据，代码只保存路径
D:/your-result-location/<task>/ 外部产品，与数据、代码分别存放
```

同一案例可以直接把函数粘贴进执行文件，也可在自己的目录拆成几个文件。
除少量明确保留的测试输入/基准外，仓库内不存放数据或输出。案例目录同样只放代码、
配置和说明，不设产品目录；`.gitignore` 不能替代物理分离。
新案例默认不导入 `base`，不导入其他案例，也不通过 `sys.path` 找中央仓库。
第三方科学库仍正常导入。更换 base 原版不会自动改变既有案例的结果。
把案例中验证好的改进整理回 base 时，同样手动处理，不做双向自动同步。

## 本批实际调整

- 三份自包含参考组装：组分反演、角度/时间归一化与 TsHARP、核组合与 ATC。
- `new_case.py` 默认直接复制参考源代码；`--legacy-template` 保留旧配置式骨架。
- 仓库外隔离执行检查、数值闭合/已知解检查和拒绝覆盖检查。
- 合成演示不是生产任务，也不是独立地面精度验证。

## 已有兼容入口

以下代码仍在 base 中供旧案例使用，本批未删除或宣称已经完成迁移。
后续迁移某个具体任务时，把其文件遍历、年份循环、并行和阶段串接复制到该案例；
保留底层单景/数组函数即可，不需要新增通用调度框架。

| 现有位置 | 仍包含的批次行为 |
|---|---|
| `base/aatsr/aatsr_{data,project,lst,lsct}.py` | 年份/文件循环 |
| `base/msg/msg_{data,project,lst,lsct}.py` | 年份/文件循环 |
| `base/slstr/slstr_{unzip,extract,reconstruct,project,merge,lst,lsct}.py` | 场景或年份批次包装 |
| `base/dual_thermal.py` | `extract_sensor_products`、`project_sensor_products`、`retrieve_sensor_years` |
| `base/{modis,viirs,ahi,aster}/` | 调用上述通用批次包装的历史传感器入口 |
| `base/normalization/{angle,time,space,sensor,fusion}.py` | `*_years` 包装 |
| `base/composite/temporal.py`、`base/applications/tvdi.py` | `composite_years`、`tvdi_years` |
| `base/templates/case/run_standard_stage.py` | 历史动态阶段调用入口，需显式选择旧模板 |

旧 `catalog.toml` 审计只覆盖登记的配置式案例；复制式案例的独立性通过脚本执行验证。
