# AHI–SLSTR 三核心站点单日核驱动归一化

站点来自 `H:/data/field/heihe_site.txt`：大满 DM（100.3722, 38.8556）、花寨子 HZZ（100.3201, 38.7659）、四道桥 SDQ（101.1374, 42.0012）。配置可以显式替换站点与路径。

```powershell
& 'C:/work/ls4t/cases/ahi-slstr/heihe/three-site-kernel/run.ps1'
# 对已生成结果目录重放：无需访问原始卫星影像
& 'C:/work/ls4t/cases/ahi-slstr/heihe/three-site-kernel/run.ps1' -Replay 'D:/cases/ls4t/ahi-slstr-three-site-kernel/run_时间戳'
```

独立 Python：`python run.py --config config.json`。案例仅导入同目录模块和第三方库，复制整个目录后也能运行。修改配置中的显式数据及输出路径；不会覆盖原始数据或已有结果。

## 方法

- 使用已有方向性 LST，不再执行大气校正或组分温度反演。
- 从 LS4T `base/kernel.py::kernel_LSF/kernel_RLf` 和 `base/normalization/kernels.py::evaluate_kernel` 复制核公式；测试验证现有公式一致。
- `T_oblique - T_nadir = a*(K_lsf,o-K_lsf,n) + b*(K_rl,o-K_rl,n)`。每个像元的背景温度通过作差消去。每站独立系数，训练块总权重相同。
- 主方法 RL 宽度固定为 1；单 LSF 为对照，宽度 .5/2 仅作敏感性分析。拒绝秩亏或列归一化条件数超过 100 的拟合，不用正则化掩盖不可辨识。
- 方向修正 `T_nadir = T_observed - a*(K_lsf-K_lsf,nadir) - b*K_rl`；太阳几何保持观测时刻状态。
- 半径 30 km、SLSTR NDVI 与站点中心差≤.10。在1 km原生配对层拟合和归一化，再将校正后的温度按2×2辐亮度均值聚合到AHI 2 km格网，避免非线性温度聚合破坏背景相消。四个子像元始终继承同一个2 km足迹及10 km空间块的划分。
- 10 km 空间块划分，中心块只做测试、邻近块作为缓冲区；其他块按固定空间哈希划分。训练与验证块不混用；AHI 全部留出。

## 选日和质量

按日期升序、S3A/S3B固定顺序扫描2019年5–10月，选首个三个站点都满足输入质量、相似地表样本和训练/留出块数要求的日子。全程不访问地面数据，不运行核拟合来选日。无符合条件日期则保存审计并明确失败。

SLSTR双视角需4个子像元均有220–365K LST、cloud=0、有效几何和时刻。角度解码/100，time按HHMM UTC。AHI用有效LST和tcc/1000≤.20代理质量，配对≤5分钟。原生L1 QA/时间、AHI逐扫描导航未核实，保留为限制，不能把代理掩膜称为原生晴空检测。

## 输出与解释

`paired_observations.csv`：所有SLSTR输入质量合格的训练/测试/缓冲像元、AHI QA和几何核值。
`predictions.csv`：原始和归一化温度、修正量、块bootstrap标准差、几何leverage、接受标志。`norm_*`保留模型提议；`usable_norm_*`仅保留通过幅度/范围门槛的结果。子像元修正也必须≤10K。
`models.json`：训练行ID、参数、条件数、95%块bootstrap区间、被拒模型原因。
`metrics.csv`：全部输入质量合格留出样本，以及修正≤10K等规则接受后的同样本原始/修正比较；不按温差残差删点。
`station_results.csv`：站点所在2km像元，单对观测不伪装成统计精度。
`selection.json` / `candidate_audit.json` / `source_manifest.json` / `checksums.json`：选日、输入文件元数据与SHA256、结果校验。
`report.md`、两幅PNG、`verification.json` 和 `code/`：报告、图、AHI/留出温度扰动不影响拟合的证据、独立代码快照。

bootstrap只反映空间块抽样敏感性。跨传感器光谱差异、同一UTC日最多5分钟时间差、上游LST/云误差与区域异质性仍存在。结果是单日方向一致性研究，不是独立地面精度结论。

`--selection-from <已有结果目录>` 仅用于修复采样实现后重新摘取此前按输入质量选定的日期：要求配置完全相同，保留完整选日审计并重查输入质量，不重新择优日期。`--replay`校验冻结输入哈希、模型键/状态/系数和所有归一化预测；运行中若代码发生变化会明确失败。
