# Case 工作方法

## 1. 责任边界

| 内容 | 位置 | 修改影响 |
|---|---|---|
| 传感器读取、投影、LST/LSCT、拼接、归一化、合成 | 根目录模块 | 只有采用该 LS4T 提交的案例受影响 |
| 研究区、时期、轨道分组、算法选择 | `case.toml` 和 `stages/` | 只影响当前案例 |
| 数据盘路径、并行数、临时盘、调度方式 | `machines/*.toml` | 只影响当前机器 |
| 旧实验、重复版本、结果图 | `cases/_archive/` | 不属于当前运行入口 |

`ls4t` 与三个独立 case 仓库不会自动同步。生产案例必须在 `case.toml` 记录经过验证的
`ls4t_revision`；准备升级时先在小范围运行，验证后再更新该值。

## 2. 建立案例

```bash
python cases/_templates/new_case.py slstr africa 2026-dry-season \
  --mode scene-first
cp cases/slstr/africa/2026-dry-season/machines/example.toml \
   cases/slstr/africa/2026-dry-season/machines/local.toml
```

编辑 `case.toml` 的科学设置，再填写 `local.toml` 的本机路径。机器变化只增加 profile，
研究区或科学方案变化才建立新 case。

## 3. 分阶段运行

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
python cases/_templates/audit_cases.py
python -m pytest -q
```

## 5. 代码回流和归档

一个计算函数在两个以上案例重复，或不再依赖具体路径/区域时，连同测试移到根目录。
案例只保留参数和调用。停止使用的实现先整体移入 `_archive/`，记录原因；确认已有替代、
无需复现后再单独决定是否删除。
