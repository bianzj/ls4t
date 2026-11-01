# 可直接复制的参考组装

每个子目录都是独立的源代码副本。科学函数放在 `run.py` 前部，具体执行顺序和循环放在
末尾 `main()`。直接复制后修改代码，无需安装 LS4T，无需配置阶段注册表。

| 目录 | 包含的零件与参考组装 | 外部依赖 |
|---|---|---|
| `components/` | Planck 转换、QA、逐像元/窗口组分反演；演示逐像元双组分反演 | NumPy |
| `normalization/` | 三项角度基函数归一化、24小时单谐波时间归一化、线性/TsHARP降尺度；演示角度→时间→TsHARP | NumPy |
| `kernel_atc/` | 15个角度核项、12种组合、线性/形状优化求解、单/双谐波ATC；演示两套独立样本拟合 | NumPy、SciPy |

在 PowerShell 中手动复制（目标目录应不存在）：

```powershell
Copy-Item -Recurse base/templates/references/normalization cases/slstr/heihe/normalization-2022
python cases/slstr/heihe/normalization-2022/run.py
```

也可以只用文件复制工具创建目录：

```powershell
python base/templates/new_case.py slstr heihe summer-2022 --reference normalization
python cases/slstr/heihe/summer-2022/run.py
```

默认是离线合成演示，结果在外部产品根目录下的 `<案例目录名>/`。真实任务修改 `USE_DEMO=False`、输入路径
和 `main()`，所需 NPZ 字段见 `demo_input()`。数组准备、卫星原生 QA 解码、几何校正、投影
和真实路径由具体案例处理；这些参考脚本没有隐含的卫星原始产品读取流程。

`SOURCE_SNAPSHOT.json` 记录复制时的文件和函数哈希，仅用于溯源，不参与执行。
案例副本可以修改；需要更新算法时人工比较、复制和验证，其他案例不会跟随变化。
代码目录不放原始数据或生成产品。`LS4T_DATA_ROOT` 和 `LS4T_PRODUCT_ROOT` 必须在代码目录外，
且互不包含；运行前必须指定，不自动创建默认根目录。输入相对路径以 `DATA_ROOT` 为基准。

```powershell
$env:LS4T_DATA_ROOT = 'D:/your-input-location'
$env:LS4T_PRODUCT_ROOT = 'D:/your-result-location'
python cases/slstr/heihe/summer-2022/run.py
```

已有案例保持原有执行方式；逐个迁移时可把依赖函数复制到本案例 `run.py` 或 `functions.py`，
不必把所有历史案例一次性改写。`base/` 内已有年份批处理包装属于兼容入口，见
[执行边界](../../../docs/CASE_EXECUTION_BOUNDARY.md)。
