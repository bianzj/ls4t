# 3×3窗口：两个SLSTR方向 + 一个AHI联合核拟合

已保存的真实数据案例：2019-05-12，S3B + AHI，大满DM、阿柔AR、四道桥SDQ。
`data/2019-05-12-s3b/` 是随代码保存的小规模固定样本和参考基准；新结果仍写到外部目录。
优先使用离线入口，无需原始卫星盘：

```powershell
& 'C:/work/ls4t/cases/ahi-slstr/heihe/three-site-kernel-3x3/replay.ps1'
# 可指定 Python 和仓库外结果目录（路径允许包含空格）：
# .\replay.ps1 -Python 'C:/work/miniconda/python.exe' -OutputParent 'D:/cases/ls4t/my replay'
```

跨平台入口（在本案例目录执行；输出目录替换为自己的仓库外路径）：

```bash
python run.py --replay data/2019-05-12-s3b --output-parent /absolute/external/result-directory
```

复现会校验冻结输入 SHA-256，重新拟合并核对参考系数、预测和质量标记；
输入CSV按 round-trip 浮点精度读取。不同科学库版本可能造成优化器差异，参考运行环境见
`data/2019-05-12-s3b/provenance.json`。该离线案例复现配对提取后的核拟合，
不重新运行原始栅格筛选或日期搜索；原栅格路径、SHA-256及选日记录一并保存用于追溯。

|站点|完整配对|留一法原始RMSE/K|归一化诊断RMSE/K|通过质量门槛|
|---|---:|---:|---:|---:|
|大满|9|3.343|1.104|9/9|
|阿柔|9|1.169|0.905|0/9|
|四道桥|9|2.138|1.141|9/9|

**阿柔全部修正超过10 K门槛，其数值仅作诊断。AHI参与拟合，以上不是独立传感器或地面精度验证。**
完整参考结果见 [报告](data/2019-05-12-s3b/report.md)，案例登记见 [case.json](case.json)。

需要从原始归档重新提取时使用原入口：

```powershell
& 'C:/work/ls4t/cases/ahi-slstr/heihe/three-site-kernel-3x3/run.ps1'
# 冻结输入重放，无需原始卫星盘：
& 'C:/work/ls4t/cases/ahi-slstr/heihe/three-site-kernel-3x3/run.ps1' -Replay 'D:/cases/ls4t/ahi-slstr-three-site-kernel-3x3/run_时间戳'
```

独立Python入口：`python run.py --config config.json`。数据/输出路径显式配置，代码可整体复制到仓库外运行；不会导入其他案例或base。需要requirements.txt中的科学库。

窗口按AHI的2 km投影归档格网定义，3×3约6×6 km；每个AHI足迹对应4个1 km SLSTR子像元/方向。最多9组完整配对、27个粗尺度方向温度。没有把1个AHI反复计为4个独立样本。并非逐像元用3个观测恰好解3参数。

每站窗口共用LSF系数a和RL系数b，热点宽度k=1固定；不同像元背景允许不同。SLSTR先在1 km层施加修正，再进行辐亮度聚合。优化两个差分对比 `(o-n)/sqrt(2)` 和 `(a-(n+o)/2)/sqrt(1.5)`；对应每个方向1 K等误差假设。光谱/反演偏差不单独拟合，但它们可能混入角度系数。

日期固定2019-05-12 S3B；大满DM、阿柔AR、四道桥SDQ分别拟合；阿柔坐标来自站点表（100.4643°E，38.0473°N）。不沿用30 km范围的参数。3×3内不按NDVI筛相似地表。所有输入必须满足已有温区、云代理、角度、同UTC日≤5分钟及格网嵌套规则。花寨子历史结果保留在原运行目录，当前配置已替换为阿柔。

替换站点后，原2019-10-30阿柔AHI云量代理约0.80，超过0.20阈值，无完整质量合格三方向配对。因此按2019-05-01至10-31日期升序、同日S3A再S3B检查，采用首个三站均有9组完整合格配对的2019-05-12 S3B；未按模型效果选日。逐候选质量记录保存在输出父目录的`site_replacement_AR_selection_20261028.json`。

`all_window_fit`用全部有效足迹拟合，误差只能叫拟合残差。
`leave_one_footprint_out`每轮同时留出一个像元的SLSTR-nadir、SLSTR-oblique和AHI，用其余像元拟合；站点中心使用周围最多8组。AHI已加入训练，不再宣称独立AHI验证。相邻像元及各折有关联，不能当作9次独立实验或地面精度。

输出：observations.csv、diagnostics.json、models.json、predictions.csv、metrics.csv、station_results.csv、report.md、3×3温差图、源文件SHA256、验证记录与独立代码快照。`norm_*`保存全部模型提议；只有通过10 K子像元修正及220–365 K温区门槛的值进入`usable_norm_*`。

LSF/RL数学公式来自前一案例中已核验的LS4T副本；Reader/归档解码也复制为本案例独立代码。继承的实际数据限制包括：AHI tcc是云量代理、140.7°E名义轨道几何、已投影格网不等价于原生PSF、归档双视角时间未独立追溯、波段差异未消除。
