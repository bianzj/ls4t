# Case 工作方法

新案例优先采用独立源码副本：

```powershell
python base/templates/new_case.py slstr africa 2026-dry-season --reference components
python cases/slstr/africa/2026-dry-season/run.py
```

也可直接复制 `base/templates/references/` 下某个目录。科学函数放在案例自己的 `run.py`
或本地 `functions.py`，参数、路径、循环、并行和阶段顺序直接写在执行脚本中。
新案例无需导入 base 或其他案例。默认运行合成演示，真实任务须改 `USE_DEMO=False`、
输入路径与 `main()`。`SOURCE_SNAPSHOT.json` 记录来源，不参与执行。
正式实验另存实际环境、输入清单和验证记录；最低依赖清单不等于冻结环境。
案例目录只存代码、配置和说明；数据、产品在仓库外分别存放，不在案例内建输出目录。
参考脚本要求显式填写 `DATA_ROOT`、`OUTPUT_DIR` 或设置 `LS4T_DATA_ROOT`、`LS4T_PRODUCT_ROOT`，
并拒绝代码内输出或两类存储根互相嵌套。少量测试夹具和固定对照表是保留例外。

升级算法时手动比较、复制并验证；base 更新不会自动改变既有副本。
通用改进可整理回 base，案例继续保留自己的代码。

以下保留旧配置式案例的工作方式；新建时必须显式加 `--legacy-template`。
base 内已有批次包装仍属于兼容入口，见 [执行边界](CASE_EXECUTION_BOUNDARY.md)。

## 1. 责任边界

| 内容 | 位置 | 修改影响 |
|---|---|---|
| 传感器读取、投影、LST/LSCT、拼接、归一化、合成 | `base/` | 只有采用该 LS4T 提交的案例受影响 |
| 研究区、时期、轨道分组、算法选择 | `case.toml` 和 `stages/` | 只影响当前案例 |
| 数据盘路径、并行数、临时盘、调度方式 | `machines/*.toml` | 只影响当前机器 |
| 旧实验、重复代码版本 | `cases/_archive/` | 不属于当前运行入口；结果图存外部产品目录 |

`ls4t` 与三个独立 case 仓库不会自动同步。生产案例必须在 `case.toml` 记录经过验证的
`ls4t_revision`；准备升级时先在小范围运行，验证后再更新该值。

## 2. 建立案例

```bash
python base/templates/new_case.py slstr africa 2026-dry-season \
  --legacy-template --mode scene-first
cp cases/slstr/africa/2026-dry-season/machines/example.toml \
   cases/slstr/africa/2026-dry-season/machines/local.toml
```

编辑 `case.toml` 的科学设置，再填写 `local.toml` 的本机路径。机器变化只增加 profile，
研究区或科学方案变化才建立新 case。

## 3. 分阶段运行

旧案例可以继续按阶段运行或直接调用 `base/` 中的函数。
标准批处理能力可通过案例内的 `run_standard_stage.py` 每次运行一个阶段：

```bash
python cases/slstr/africa/2026-dry-season/run_standard_stage.py \
  extract --machine local
```

轨道分组、研究区拼接清单、LSCT 权重准备、验证和服务器调度写入该案例的 `stages/`。
阶段必须落盘，不能依赖前一个脚本仍在内存中的状态。

## 4. 验证和状态

状态只使用：

- `draft`：只有计划和配置；
- `migrated`：历史实际代码已归入案例，但尚未完成标准化；
- `active`：入口、机器配置和 LS4T 提交已验证；
- `paused`：可恢复但当前不运行；
- `complete`：结果和完整性检查均完成。

提交前运行：

```bash
python base/templates/audit_cases.py
python -m pytest -q
```

## 5. 代码回流和归档

一个计算函数经验证后可连同测试整理回 `base/`，案例保留自己的副本与执行代码。
停止使用的实现先整体移入 `_archive/`，记录原因；确认已有替代、
无需复现后再单独决定是否删除。
