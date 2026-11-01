# 2019-05-12 黑河三站固定案例数据

真实归档提取样本：大满DM、阿柔AR、四道桥SDQ各9个AHI格网足迹，共27行。
每行包含一个AHI温度、两个SLSTR方向各4个原生子像元温度及角度核。
样本来自S3B双视角与AHI的时间配对；AHI与SLSTR最大时间差分别为4、4、3分钟。

|文件|用途|
|---|---|
|`observations.csv`|冻结输入；`t_n/t_o`为SLSTR子像元聚合温度，`t_a`为AHI；`t_n_0..3/t_o_0..3`保留子像元；`lsf_* / rl_*`为核值；温度单位K|
|`config.json`|原运行配置，保留历史外部路径；离线重放只覆盖输出路径，不访问原始盘|
|`diagnostics.json`|三站输入质量与配对数量|
|`source_manifest.json`|原栅格路径、SHA-256、格网及站点坐标来源|
|`date_selection.json`|按输入质量筛选日期的逐候选记录，不按模型效果选日|
|`models.json`|全窗口及逐足迹留一的参考系数、训练行标识|
|`predictions.csv`|参考预测及质量标记；拒绝结果的`usable_norm_*`为空|
|`metrics.csv` / `station_results.csv`|参考差异统计与中心留出结果|
|`report.md` / `window_differences.png`|参考说明与图，图中叉号表示修正未通过质量门槛|
|`verification.json`|原运行的留出扰动验证与代码哈希；对应原始代码快照，不代表之后的包装改动|
|`checksums.json`|原运行文件校验和，重放前校验必要输入与参考输出|
|`provenance.json`|复制来源、冻结文件收据及打包时科学计算环境|

在案例根目录运行`replay.ps1`，或：

```bash
python run.py --replay data/2019-05-12-s3b --output-parent /absolute/external/result-directory
```

本目录为固定输入和参考基准，不接收新结果。复现范围为提取后的核拟合，
不包含原始栅格重新提取或日期重新搜索。旧HZZ和2019-10-30试验留在外部历史运行目录。
阿柔9组输入均有效，但9组修正均超过10 K门槛，归一化值只作诊断。
AHI参与标定，不能把本案例结果表述为独立AHI验证或地面精度验证。
