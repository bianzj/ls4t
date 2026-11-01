# 活动案例中的算法、重复实现与能力边界

核查日期：2026-10-24。依据 `C:/work/ls4t` 当前 Python 源码；排除 `_archive`、结果目录、日志、原始数据和缓存。本文不运行区域反演、不修改算法，不把脚本存在解释为已通过实际科学验证。表中“案例专有”指实现/组合保存在案例或示例中，**不表示数学方法是新方法**；共享库已有 LS、Ridge、约束窗口和二次曲面等基础方法。

## 1. MSG 窗口、约束和两阶段实验

记双视角辐射为 `y`，有效发射率/几何权重为 `A`，组分辐射为 `x`。大部分方法求解辐射后才反普朗克为温度；`delta/dif` 若作用于 `x`，单位是辐射，不能直接写成 K。窗口模型假设窗口内各组分辐射一致；二次曲面方法是例外。

| 函数及源码 | 输入 → 输出 | 数学方法、默认值与实际边界 | 定位 |
|---|---|---|---|
| [solve_3x3_least_squares](/C:/work/ls4t/cases/msg/experiments/msg_lsct_2c_window.py:44)；[solve_5x5_least_squares_robust](/C:/work/ls4t/cases/msg/experiments/msg_lsct_2c_window.py:106) | 两张辐射图、四通道权重 → 两组分辐射图 | `uniform_filter(mode='nearest')` 求正规方程窗口和，2×2 克莱姆法；3×3 至少3点，5×5至少5点；`abs(det)>=1e-8`。后者再去除非正辐射。“robust”没有 Huber、RANSAC 或迭代重加权，仅缺测/病态/正值过滤。3×3返回变量名为 `bv_rad, bs_rad`，5×5为 `bs_rad, bv_rad`，必须按权重列解释，不能依赖矛盾注释。 | 案例专有向量化实现；不是新的鲁棒估计族。 |
| [solve_5x5_three_components](/C:/work/ls4t/cases/msg/experiments/msg_lsct_3c_window.py:51)；[solve_3x3_three_components](/C:/work/ls4t/cases/msg/experiments/msg_lsct_3c_window.py:130) | 双视角辐射、六通道权重 → 阳照土壤、阴影土壤、植被辐射 | 无先验三元窗口 LS，批量 `np.linalg.solve`。5×5要求 `n_valid>10`、`abs(det)>1e-6`、全部辐射正；3×3要求至少4点、`abs(det)>1e-7`，并限制辐射 `(0,30]`。清洗逐项 NaN，计数只检查两辐射和第一权重，不能据此宣称所有项使用严格共同掩膜。 | 多脚本复制；3×3/5×5是窗口/门槛变体。 |
| [solve_2x2_system_5x5](/C:/work/ls4t/cases/msg/msg_lsct_iter.py:160) | 双辐射、四权重、`size=5` → X、Y辐射 | 通用 `size×size` 二元窗口 LS；名称不是固定5×5。至少 `0.4*size²` 点、`abs(det)>=1e-8`、非负；`size=3`实际至少4点。逐项清零和不完整权重掩膜是历史实现特征。 | `msg_lsct_iter` 与 experiments 多份完全重复。 |
| [solve_constrained_vectorized](/C:/work/ls4t/cases/msg/experiments/msg_lsct_3c_constrained.py:14) | 扣除阳照项的双视角残差、阴影/植被权重、固定阳照辐射 → 阴影、植被辐射 | 窗口无约束解加三条边界候选；要求 `shade<=sun` 与 `abs(shade-veg)<=dif`，默认 `.5`；候选按中心双视角 SSE 比较。不是对整个窗口严格统一求解的通用 QP：初始解来自窗口，边界 SSE 来自中心；代码未穷举所有边界交点。 | 组合约束试验；不能以函数名替代最优性证明。 |
| [solve_constrained_vectorized1](/C:/work/ls4t/cases/msg/msg_lsct_iter.py:225)；[solve_constrained_vectorized2](/C:/work/ls4t/cases/msg/msg_lsct_iter.py:247) | 同上 → 阴影、植被辐射 | `1`仅在阴影超过阳照时替换为 `shade=sun` 的中心解析解；`2`仅比较 `shade=veg±dif` 两边界，默认`.5`，其 `bs1_fixed` 参数未用于约束。主流程在外部再次 `min(shade,sun)`。 | 约束消融变体；不是两个独立反演原理。 |
| [solve_joint_vectorized_with_prior](/C:/work/ls4t/cases/msg/msg_lsct_iter.py:290)；[矩阵版](/C:/work/ls4t/cases/msg/experiments/msg_lsct_3c_constrained.py:395) | 中心双观测、六权重、三分量先验、`lmbda=.5` → 三组分辐射 | 最小化 `||Ax-y||²+λ||x-x_prior||²`；一个用3×3伴随矩阵公式，一个用批量 `solve`；最后 `shade=min(shade,sun)`。该裁剪是后处理，不等于联合约束 MAP。 | 相同目标的不同数值实现。 |
| [msg_lsct_iter 顶层组合](/C:/work/ls4t/cases/msg/msg_lsct_iter.py:576) | 同时双视角 LST、LAI、视角/太阳角、组分发射率 → 组分图 | 先3×3解阳照与合并项；再由逐像元阳照场扣残差，在5×5分阴影和植被；温差边界后联合先验解。实际主流程 `hotspot=.2, λ=100, dif=3`，见[参数](/C:/work/ls4t/cases/msg/msg_lsct_iter.py:370)，不是函数签名默认值。 | 案例内完整组合，无统一共享API；导入会触发顶层参数/I/O。 |
| [msg_lsct_3c_two_stage 顶层计算](/C:/work/ls4t/cases/msg/experiments/msg_lsct_3c_two_stage.py:359) | 双视角输入 → 阳照、合并温度、总土壤、植被 | 实际先解“阳照 vs 阴影+植被”，又独立解“总土壤 vs 植被”，两次 `size=3`。注释称残差第二阶段，但执行段没有据此解阴影分量。 | 命名不能当能力证据；不是已完成的三组分残差反演。 |
| [hotspot_layer](/C:/work/ls4t/cases/msg/msg_lsct_iter.py:26)；[calculate_scattering_angle](/C:/work/ls4t/cases/msg/msg_lsct_iter.py:51) | LAI、热点参数、太阳/观测角 → 阳照土壤概率与观测间隙；或散射角 | `G=.5`、可指定 `CIs/CIv` 的指数冠层间隙与热点重叠；散射角为球面方向余弦。不是独立温度求解器。 | 同 `constrained/diagnostics` 复制；与 `base.rt` 属同物理模型族，返回接口须区分。 |

### 源码去重结论

使用 Python AST 去掉函数首层文档字符串、忽略位置信息后比较，以下函数完全一致：

- `solve_5x5_three_components`：`msg_lsct_iter`、`3c_constrained`、`3c_diagnostics`、`3c_two_stage`、`3c_window` 共5份。
- `solve_2x2_system_5x5`：`msg_lsct_iter`、`3c_constrained`、`3c_diagnostics`、`3c_two_stage` 共4份。
- `solve_constrained_vectorized1/2`：`msg_lsct_iter`、`3c_constrained`、`3c_diagnostics` 各3份。
- `hotspot_layer`：上述3份；`solve_joint_vectorized_with_prior` 的伴随矩阵版在 `msg_lsct_iter` 与 `3c_diagnostics` 重复。`3c_constrained`矩阵版目标相同，但 AST 不同。
- experiments 中4份 `planck/inv_planck` 完全一致，沿用当前 `base.radiometry` 常量和历史 `*10000` 写法。数值量纲需与物理 `planck_radiance` 及各代码版本同时核查，不能把不同辐射尺度上的 `λ/delta` 直接互换。

## 2. MSG compatible / declared / hybrid：一套反演，三套观测几何策略

[compatible.retrieve](/C:/work/ls4t/cases/msg/assessment/msg_compatible/produce_msg_ls4t.py:133)、[declared.retrieve](/C:/work/ls4t/cases/msg/assessment/msg_declared/produce_msg_ls4t.py:133)、[hybrid.retrieve](/C:/work/ls4t/cases/msg/assessment/msg_hybrid/produce_msg_ls4t.py:136) 的 AST **完全相同**；三套 `planck`、`hotspot` 也一致。因此不应计作三种温度反演算法。

| 函数/策略 | 实际算法及输入输出 | 与其他变体的区别 |
|---|---|---|
| `retrieve(d)`，见上方三个入口 | 字典含双视角 LST、LAI、组分发射率、太阳/观测角，可含地类 → `[background_soil,canopy,sunlit_soil,shaded_soil]` K数组、邻域计数、QA位。共同有效双辐射及全部六权重；两阶段均5×5，至少10点、`det>=1e-8`。第一阶段阳照辐射**对该中心整窗视为常量**；第二阶段先验加 `delta=3` 辐射边界，`λ=1000`的中心联合解，再限 `shade<=sun`。输出全部四分量共同满足250–350 K，LAI≥.05。总土壤由太阳方向间隙权重混合两土壤辐射。 | 与旧 `msg_lsct_iter` 的3×3/5×5、`.2/100`和局部阳照场扣残差不同；这是相同家族但真实不同配置/残差定义，不能仅改文件名后视为数值等价。 |
| `planck/inverse/hotspot`，如[compatible](/C:/work/ls4t/cases/msg/assessment/msg_compatible/produce_msg_ls4t.py:113) | SI常量、10.5 μm，辐射 `W m-2 sr-1 um-1`；热点`.25`，输出阳照土壤与总间隙。 | 有明确辐射单位；`inverse`有形式不同但数学相同的版本，不据 AST 差异计新方法。 |
| [compatible.read_position / geometry_metadata / view_geometry](/C:/work/ls4t/cases/msg/assessment/msg_compatible/msg_view_geometry.py:40) | 从原始HDF读取每景 `MEAN_SSLAT/MEAN_SSLON`，核验时刻/轨道范围/投影时期；生成逐像元 VZA/VAA。 | 缺失、0/0占位、轨道与输入网格冲突均拒绝；不回退 nominal。 |
| [declared.geometry_metadata / view_geometry](/C:/work/ls4t/cases/msg/assessment/msg_declared/msg_view_geometry.py:49) | 冻结声明轨位，经度取对应投影时期的声明，纬度明确设0；返回角度及证据。 | 明示名义几何近似；仍排除计划中原始投影冲突月份，不称实际星下点轨道。 |
| [hybrid._select_position](/C:/work/ls4t/cases/msg/assessment/msg_hybrid/msg_view_geometry.py:72)；[view_geometry](/C:/work/ls4t/cases/msg/assessment/msg_hybrid/msg_view_geometry.py:177) | 有可信动态元数据则动态；缺文件/缺字段/非有限/0,0占位才回退声明静态轨位，记录原因。 | 有限但超范围或与投影时期冲突的动态位置仍抛错，不以静态回退掩盖冲突。 |
| `look_angles`：[compatible](/C:/work/ls4t/cases/msg/assessment/msg_compatible/msg_view_geometry.py:60)、[declared](/C:/work/ls4t/cases/msg/assessment/msg_declared/msg_view_geometry.py:26)、[hybrid](/C:/work/ls4t/cases/msg/assessment/msg_hybrid/msg_view_geometry.py:154) | WGS84地面大地坐标→ECEF→站点ENU；卫星地心半径42164000 m、地面高度0；输出天顶角和北0东90方位角。 | 同一几何方程，输入位置策略有别；不是新增温度算法。 |
| `monthly`，如[compatible](/C:/work/ls4t/cases/msg/assessment/msg_compatible/produce_msg_ls4t.py:576) | 编码后的瞬时四组分在共同掩膜上按月份、固定UTC小时算术平均；返回月产品/支持计数。至少1次保留，1–2次标低支持。 | 观测合成，无时间插值、无全天候补全。文件哈希、续跑、提交、lineage属于工程控制。 |

上述三套仍位于 `cases/msg/assessment`，各自硬编码产品协议、路径和生产身份；不能当作已统一的共享库公开接口。此次仅核对源码，不借计划文件中的 `approved` 字段推断当前所有输入和产物已通过验收。

## 3. MSG 参数实验、日变化拟合和验证程序

| 入口 | 方法、输入输出及边界 |
|---|---|
| [search_evo_parameters.solve / prepare / retrieve](/C:/work/ls4t/cases/msg/assessment/search_evo_parameters.py:38) | 批量5×5缓存输入；提供物理/历史辐射分支、第一窗3或5、`center`或`local_vector`残差模式；最终同先验正则三组分族。`prepare`控制空间假设，`retrieve`控制λ/辐射差约束、可选350 K植被替换；输出4分量或阳照/冠层对及有效/约束标记。 |
| [search_evo_parameters.metrics / main](/C:/work/ls4t/cases/msg/assessment/search_evo_parameters.py:155) | 8–10月开发、11–12月保留验证；遍历热点8值×λ6值×delta5值×窗2值×残差2值。目标为等月/等分量惩罚RMSE，失败预测按20 K；覆盖门槛 `max(.8,baseline-.01)`。脚本承认后期日期曾被早前总体分析查看，不能称从未见过的外部测试。 |
| [select_joint_station_parameters.score_specs / evaluate / normalized / qualified](/C:/work/ls4t/cases/msg/assessment/select_joint_station_parameters.py:83) | 直接与间接参考分域、站点/年/月等权；每月至少3记录；缺失按20 K误差；基线归一化平方RMSE，单指标退化不超过10%，站点覆盖下降阈值直接.01/间接.02。是参数选择与评价规则，不新增反演模型。参考层把直接土壤配阳照土壤、间接土壤配总土壤。 |
| [msg_site_fit.fitting_DTC / fitting_DTCRL / fitting_DTCLSFRL](/C:/work/ls4t/cases/msg/msg_site_fit.py:17) | 将观测温度、时间和方向核传入 `base.kernel` 的代价函数，用 `scipy.optimize.fmin`（Nelder–Mead）拟合4/6/7参数；不传参数边界。物理/经验模型在共享库，案例函数仅优化包装。是真实日变化曲线拟合能力，但这里没有独立云下温度补全或深度学习训练流水线。 |
| [msg_lst_fit.retrieve_lst](/C:/work/ls4t/cases/msg/msg_lst_fit.py:213) | 10.8/12.0 μm亮温、TCWV、VZA、LAI、土壤/植被双波段发射率、昼夜标记、系数表 → LST K。FVC→混合发射率加散射；八特征广义分裂窗、TCWV分箱、视角相邻节点系数线性插值、昼夜系数切换。是应用已有系数的分裂窗，不在该函数训练系数，不属于缺测重建。 |
| [msg_monthly_composites.Accumulator / process_job](/C:/work/ls4t/cases/msg/assessment/msg_monthly_composites.py:157) | 独立集合有效掩膜累计；组分与两原始LST的配对集合取交集。固定UTC小时月均、有效计数、1–2次低支持标记；不插值。 |
| [analyze_station_full_2018_2024.match / aggregate / metrics / paired](/C:/work/ls4t/cases/msg/assessment/analyze_station_full_2018_2024.py:42) | 站点时间配对、瞬时/月/月-小时聚合、RMSE/Bias和共同支持比较；`legacy_pairs`另复现历史筛选。评价尺度与筛选是协议差异，不能把月平均误差叫瞬时精度。 |

## 4. SLSTR 案例专有三组分方法

| 入口 | 输入 → 输出 | 目标、假设与实际配置 | 状态边界 |
|---|---|---|---|
| [slstr_lsct2_scene 顶层](/C:/work/ls4t/cases/slstr/slstr_lsct2_scene.py:272)；[slstr_lsct2_scene_parallel.lsct2_scene](/C:/work/ls4t/cases/slstr/slstr_lsct2_scene_parallel.py:287) | 双视角LST、LAI、发射率、VZA、云 → 土壤与植被温度 | 5×5同温窗口；土壤权重(.1,.9)、样本>5；实际执行 `scipy.linalg.lstsq` 的无正则两元LS。LAI→FVC、混合发射率加`.05`散射项、权重组装、掩膜和反演循环都写在case中。parallel版本LAI阈值`.05`；仅一视角云图缺失时复制另一幅并标记fallback。 | 初始化了`inv_Cm`等变量不代表执行Bayes更新：求解路径没有使用它们。两脚本主要是工程/掩膜变体，不是两个独立Bayes方法。 |
| [slstr_lsct2_area](/C:/work/ls4t/cases/slstr/slstr_lsct2_area.py:78) | 已对齐栅格双视角与LAI/发射率 → 两组分温度 | case内逐像元组装`cal_effective_emissivity_hom`和辐射，`ws=5,hspot=.2,wl=10.8`，随后调用共享`inv_lsct2_window`。 | 核心约束优化已在base；case只保留输入、权重构造和运行配置。 |
| [slstr_lsct3_scene.fitting_with_ridge](/C:/work/ls4t/cases/slstr/slstr_lsct3_scene.py:28)；[顶层窗口](/C:/work/ls4t/cases/slstr/slstr_lsct3_scene.py:294) | nadir/oblique LST、LAI、发射率、角度、云掩膜 → 阳照土壤/阴影土壤/植被温度 | `sklearn.Ridge(alpha=.01,fit_intercept=False)`，辐射三元LS加L2；有效发射率来自热点和冠层间隙；顶层虽有`ws=5`，实际 `off=1`取3×3。土壤权重和需在(.1,.9)，样本>5。 | 与AATSR `fitting_with_ridge`是同一个数学方法；窗口组装不同。旧路径批处理脚本，不是通用贝叶斯算法。 |
| [slstr_lsct3_area](/C:/work/ls4t/cases/slstr/slstr_lsct3_area.py:81) | 面积输入、有效发射率 → 三组分 | 调用共享 `base.lsct`/`base.lsct_window.inv_lsct3_window`，5×5约束反演。 | 共享算法的案例入口，不重复计数。 |
| [slstr_lsct3_bayes_scene.scene](/C:/work/ls4t/cases/slstr/slstr_lsct3_bayes_scene.py:210) | 重新计算的双视角LST、云、几何、LAI、发射率 → 总土壤/植被/阳照土壤/阴影土壤四张K图 | 5×5两视角共同中心，分别至少8个邻点；先累加高斯辐射似然正规方程。先验中心均为B(300 K)，温度标准差 `[50,50,10] K`、相关`.25`，以300 K处 `dB/dT`换算协方差；观测噪声10 K按中心温度导数变换。然后对“斜视方向混合土壤温度−植被温度”施加 `9±10 K`软先验，两步 Gauss–Newton。 | **案例专有的明确 MAP/Laplace近似实现**，没有MCMC采样或后验不确定性输出。 |
| 同上[排序约束](/C:/work/ls4t/cases/slstr/slstr_lsct3_bayes_scene.py:331) | 三辐射MAP结果 → 可接受三分量 | 阳照冷于阴影时，用 `x_sun=x_shade`降维，精确解最后一次局部二次目标的边界；200–400 K输出过滤。土壤混合权重为斜视阳照占可见土壤比例，不同于MSG太阳方向土壤混合定义。 | 是最终局部二次问题上的边界投影，不能称整个非线性目标全局最优；迭代中截断仅用于线性化，最后超范围解被剔除。 |
| [solar_from_time / derivative / box_sum](/C:/work/ls4t/cases/slstr/slstr_lsct3_bayes_scene.py:56) | 文件名起止时间、经纬度 → 中点太阳角；温度→有限差分普朗克导数；数组→5×5和 | 太阳赤纬/均时差近似；`derivative`步长±.01 K；`box_sum`常量0边界。有保存太阳角时优先用保存值。 | 数值/几何辅助，非三个新的温度模型。 |
| [slstr-america.monthly_components.bin_scene / accumulate_day](/C:/work/ls4t/cases/slstr-america/monthly_components.py:87) | 4组分+像元LST、经纬度 → 0.01°格点内5层共同有效场景均值及支持 | 限温、排序和混合关系检查；原生像元中心分箱求场景均值；同日重叠按时间排序后**后景覆盖前景**，再以有效UTC日等权平均，非所有观测无差别平均。像元LST取同景oblique并除100。 | 五层共同支持的产品合成，核心分箱/日月权重计算仍写在case中；明确无空间填洞。 |

## 5. AATSR 案例变体：明确可用结构与未完成函数

| 函数及源码 | 输入输出、目标和约束 | 不应混淆的点 |
|---|---|---|
| [aatsr_lsct.fitting_with_ridge](/C:/work/ls4t/cases/aatsr/aatsr_lsct.py:25)；[aatsr_lsct_latlon.fitting_with_ridge](/C:/work/ls4t/cases/aatsr/aatsr_lsct_latlon.py:29) | 辐射观测与2×N设计权重 → 两辐射系数；`Ridge(.01,fit_intercept=False)`。 | 与SLSTR三元Ridge是同目标，未知量维数不同。共享库亦已有Ridge分派。 |
| [process_column / process_column_batch / process_column_batch_new](/C:/work/ls4t/cases/aatsr/aatsr_lsct_latlon.py:75) | 指定列与窗口数据 → 土壤/植被温度列 | 都组装两视角窗口、筛选`.1<soil_weight<.9`和>5样本后调用Ridge；新函数主要改遍历非零掩膜/列批处理，不新增科学模型；异常跳过并留下0。 |
| [aatsr_lsct.inv_mpl_agl_multiple_2](/C:/work/ls4t/cases/aatsr/aatsr_lsct.py:43) | 签名看似双角两组分反演 | 函数体只有 `return resultT`，该函数内未定义结果；不能列为实现完成的算法。其他文件同名函数应按文件逐个核查。 |
| [aatsr_site_inv.inv_lsct2_window / inv_lsct3_window](/C:/work/ls4t/cases/aatsr/aatsr_site_inv.py:17)；[aatsr_lsct_ndvi.aatsr_inv_lsct2_window / aatsr_inv_lsct2_Line](/C:/work/ls4t/cases/aatsr/aatsr_lsct_ndvi.py:23) | 多角权重、辐射、掩膜、LST、窗口参数 → 组分温度 | 窗口遍历与共享 `fitting_Nangle_Mcomponent_window` 的SLSQP、`set_weights`、日夜初值/边界和组分差约束；案例拥有组装流程，约束数学在 `base`。`_Line`只是遍历范围变体。 |
| [aatsr_site_inv.optimize_LAI](/C:/work/ls4t/cases/aatsr/aatsr_site_inv.py:82) | LAI初值、双角NDVI/VZA → 每像元LAI、共用CI、土壤/植被NDVI端元及优化状态 | 拟合 `1-exp(-LAI*G*CI/cosθ)` 与归一化NDVI覆盖率，G=.5；L-BFGS-B；LAI [.01,10]、CI [.5,1]、NDVIs [0,.15]、NDVIv [.8,.99]。正则：CI偏差权重.1、端元各10、LAI平均绝对偏差平方权重.1。 | 案例专有结构/端元联合拟合，**不是温度重建**；LAI×CI耦合靠先验正则缓解，不等于独立可识别。 |
| [aatsr_site_inv_bayes.line_inv_2_s](/C:/work/ls4t/cases/aatsr/aatsr_site_inv_bayes.py:97) | 5列带状双角权重、辐射、掩膜 → 两组分温度线 | 至少12个有效像元；先用每组分6项二维二次多项式（共12参数）拟合5×5辐射场；高斯核加权有效曲面预测得到先验，不足2点退回中心；中心双观测与 `Cm=diag(2,1), Cd=.05 I`构成闭式高斯后验；辐射限制4.5–20。 | 二次空间先验+中心高斯更新的案例实现。`sensor_noise=.05`在这里直接作为协方差对角，不是再次平方；不输出后验区间。 |
| [aatsr_site_inv_bayes.line_inv_3_s](/C:/work/ls4t/cases/aatsr/aatsr_site_inv_bayes.py:235) | 名称/`number_component=3`提示三元版本 | 源码仍只构造 `ct1/ct2`及两维 `ctprior`，`Cm=diag(2,1)`，而`Cd`按3组分建3×3，中心观测仍双视角。由矩阵维数静态可见未一致改成三元。 | **不能视为已可用的三组分Bayes**；本次不运行、不修复，仅记录能力缺口。 |
| [aatsr_lsct_v31.inv_lsct2_v3_1](/C:/work/ls4t/cases/aatsr/aatsr_lsct_v31.py:30) | `w,b,mask,lst,n,m,ws` → 8通道温度，依次v0/v1/v2/v3各土壤植被 | v0共享二次曲面；v1中心LS；v2整窗同温LS；v3以v2为先验，中心观测更新 `(KᵀK/.05+diag(1/2,1))⁻¹(...)`。默认5×5、10.8 μm。 | 是4种比较输出的组合；共享二次/LS不是案例独有。方差/噪声为模块主程序赋值的全局量，单独调用需补环境；`ifcons`参数没有驱动独立约束实现。 |

## 6. `tests/examples/msg_aatsr_comparison.py`：受控迁移比较，不是生产算法目录

[METHODS](/C:/work/ls4t/tests/examples/msg_aatsr_comparison.py:25) 有13个标签，但应归并为以下方法/消融：

| 函数 | 实际数学与作用 |
|---|---|
| [least_squares](/C:/work/ls4t/tests/examples/msg_aatsr_comparison.py:38) | `ls2/ls3`为同温窗口LS，`ridge2`为λ=.01；先要求样本足够、满秩、条件数≤1e6，Ridge也执行同样门槛。 |
| [quadratic](/C:/work/ls4t/tests/examples/msg_aatsr_comparison.py:46) | 两组分各 `[1,x,y,xy,x²,y²]` 六系数；双视角5×5共12参数LS，输出中心截距及整窗曲面；与共享二次曲面属同族的独立比较实现。 |
| [posterior / solve_window](/C:/work/ls4t/tests/examples/msg_aatsr_comparison.py:54) | 中心高斯更新，观测协方差`.05 I`、先验精度`diag(.5,1)`；`map_constant2`用窗口LS先验，`map_quadratic2`用二次曲面筛选后核加权先验，`map_exclude_center2`仅在先验拟合中去中心。最终后验仍使用中心观测，不能将其解释为纯中心留出预测。 |
| [constrained](/C:/work/ls4t/tests/examples/msg_aatsr_comparison.py:60) | 空间加权SSE，SLSQP，初始经验解和LS解两起点；取成功且约束可行的最小SSE。2组分温度边界相对中心均温分别[-10,+40]、[-10,+10] K；3组分[-10,+40]、[-30,+30]、[-10,+20] K；由同一10.5 μm普朗克近似转成辐射差范围，另有min/max包络中心观测约束。`no_delta`只关差约束，不关其余约束。 |
| [msg_iter / production_functions](/C:/work/ls4t/tests/examples/msg_aatsr_comparison.py:137) | AST提取旧MSG纯数值函数，以物理辐射适配器运行3×3/5×5、λ100、delta3；`msg_iter3_commonmask`额外在第一阶段失败后同步剔除第二阶段权重。是掩膜消融，非新反演族。 |
| [three_weights](/C:/work/ls4t/tests/examples/msg_aatsr_comparison.py:171) | 所有三组分方法共用热点`.2`及相同有效发射率，以避免把几何差异错归求解器差异。 |
| [evaluate_reference / constraint_ablation](/C:/work/ls4t/tests/examples/msg_aatsr_comparison.py:197) | 对EVO 2017-10缓存参考精确UTC小时配对，共同有效支持RMSE/Bias；显式检查2017年份/201710月份和时间重复。参考是历史辐射校正缓存，原始现场CSV若不可用，不称新独立验证。两组分总土壤对阳照参考标成 `bulk_soil_cross_component`。约束消融也检查实际K温差越界；辐射差近似不保证标称K界限。 |

这里 `reconstruction_rmse_k` 指**由反演组分前向混合还原输入双视角LST的残差**，不是缺云插补精度，也不是组分真值准确率。单元测试包含已知二次辐射曲面恢复、Gaussian更新恒等式、共享LS/Ridge一致性、约束开关和恒温场检查；本轮整体测试记录见主报告。本次没有重算科学实测精度，不报告新的精度数字。

## 7. 北京 LAI、建筑和 Urban-G：均不属于温度重建

| 函数/入口 | 科学处理与输出 | 证据边界 |
|---|---|---|
| [landsat-beijing-lai.make_scene](/C:/work/ls4t/cases/landsat-beijing-lai/run.py:102) | Landsat反射率DN用`.0000275*DN-.2`缩放；蓝/红/近红外及QA生成EVI，`LAI=max(0,3.618*EVI-.118)`，输出经验LAI。 | 不是辐射传输反射率反演、不是LST；场景QA来自已有NDVI掩膜再追加蓝波段条件。 |
| [basis / fit_curve](/C:/work/ls4t/cases/landsat-beijing-lai/run.py:54)；[fit_curve](/C:/work/ls4t/cases/landsat-beijing-lai/run.py:148) | 年周期及二阶谐波5项设计矩阵，按实际闰年长度定相位；每年总权重相同；岭惩罚只加四谐波项，截距加1e-8；需最小观测数/年份数/季节覆盖。 | 季节经验曲线，非神经网络。 |
| [estimate_bracket / estimate / reconstruct](/C:/work/ls4t/cases/landsat-beijing-lai/run.py:177) | 8日箱有观测先保留观测平均；无观测时按短间隔线性、季节曲线+双侧残差、季节曲线+局地指数衰减残差、纯季节曲线顺序补全；输出LAI、方法码、距最近观测天数、观测计数。 | 回溯LAI补全可使用目标后侧观测；不是因果温度预报。2026扩展实际传入`.15,8,3,3,32,96,64`，即岭/支持门槛和各时间窗。 |
| [extend_2026 主流程](/C:/work/ls4t/cases/landsat-beijing-lai/extend_2026.py:145)；[validate](/C:/work/ls4t/cases/landsat-beijing-lai/run.py:400) | 扩展复用同一 `core.reconstruct`，冻结2015–2025季节训练，2026观测作当年锚点；验证按留出窗口比较经验LAI。 | 非独立地面LAI准确率；[test_beijing_lai_8day](/C:/work/ls4t/tests/test_beijing_lai_8day.py:31)是合成输入/泄漏与方法逻辑测试，不能替代绝对LAI验证。 |
| [beijing-building-structure.overlap_matrix / rectangles](/C:/work/ls4t/cases/beijing-building-structure/run.py:36) | 一维区间精确交叠构成稀疏权重矩阵；建筑连通斑块最小旋转矩形长宽和方位。 | 几何描述；不以矩形长宽冒充真实逐边尺寸。 |
| [coarse_statistics / lai_grid](/C:/work/ls4t/cases/beijing-building-structure/run.py:61) | 建筑高度栅格聚合覆盖、建筑面积、面积加权高度/高度积分及斑块密度；精确10m→30m面积交叠输出建筑密度、高度均值/标准差、已知覆盖比例。 | 建筑密度分母为已知有效面积；覆盖范围外为NoData而非0建筑。不是植被G参数反演或热辐射模拟。 |
| [beijing-buildings-urban-g.union_areas](/C:/work/ls4t/cases/beijing-buildings-urban-g/run.py:17)；[prepare_vectors / raster_products](/C:/work/ls4t/cases/beijing-buildings-urban-g/run.py:33) | 建筑修复、投影、裁剪、标准化WKB去重复；STRtree检索像元相交轮廓，求**交片并集面积**，除完整900m²得到建筑覆盖率；5/10/20%阈值分类。 | Urban-G是源数据名称，不是新冠层投影G算法。height/var原字段单位未核实、年份未知；零表示目录未记录，不证明没有建筑。 |
| [urban-g.test_methods](/C:/work/ls4t/cases/beijing-buildings-urban-g/test_methods.py:5) | 叠置轮廓只计并集、精确10%阈值、有孔面、空集和仅边界接触的人工几何测试。 | 检查算法面积逻辑，不检验源建筑目录完整性或测绘精度。 |

## 8. 真正已有与尚无源码支持的能力

| 用户可能理解的能力 | 当前源码证据 | 盘点结论 |
|---|---|---|
| 温度时间拟合 | `base.kernel`模型和 `msg_site_fit` 的DTC/方向核拟合包装 | 有温度曲线拟合/时角归一相关能力；不能由此推断有完成的全天候温度重建产品。 |
| SLSTR“reconstruct” | [base.slstr.slstr_data.reconstruct_product](/C:/work/ls4t/base/slstr/slstr_data.py:289) | 原始BT直接保留；VZA、经纬度、云掩膜最近邻对齐到热红外网格。是几何与质量字段重构，**没有温度缺测估计**。 |
| MSG组分“重建误差” | 比较示例中 `w@rad` 再反普朗克 | 是观测闭合残差，不能替代独立地面组分验证。 |
| 深度学习重建 | 活动Python全局搜索 `torch/tensorflow/keras/neural/deep.learning`，排除归档/数据/输出/环境目录，未发现实现 | 没有源码证据支持本仓库已有深度学习训练、推断、检查点或DL温度填洞。不能从外部项目名/历史说明补造能力。 |
| 反射率相关处理 | MSG提取脚本 Satpy `calibration='reflectance'`；北京蓝红近红外计算EVI/LAI | 是反射率读取/校准与经验指数，不是光学深度学习温度重建。 |
| 干旱应用 | [base.applications.tvdi.tvdi](/C:/work/ls4t/base/applications/tvdi.py:25) | 广播温度K和植被指数，给定干/湿边两组线性系数；`(T-Twet)/(Tdry-Twet)`，要求干边高于湿边，裁剪[0,1]。没有自动边缘估计、作物胁迫校准、土壤水分反演或独立干旱验证。 |
| TVDI批处理 | [tvdi_years](/C:/work/ls4t/base/applications/tvdi.py:43) | 年目录NPZ读取 `temperature_k/vegetation_index`，写`tvdi`；默认干边(330,-10)、湿边(290,-2)，不是对研究区拟合所得。 |
| 火灾应用 | `base/applications`只有`__init__.py`和`tvdi.py`；活动Python全局`fire`搜索未见实现 | 没有火点检测、FRP、燃烧面积、火险模型或火灾验证实现证据。 |

## 9. 完成度与本次覆盖范围

### 核心计算实际归属速查

| 运行组合 | 仍写在case/示例中的计算 | 已调用共享库的部分 |
|---|---|---|
| SLSTR场景LSCT2串行/parallel | FVC/混合发射率组装、5×5样本选择、直接`lstsq`、后处理 | Planck、角度FVC、读写/网格工具 |
| SLSTR场景LSCT3 Ridge | 热点三组分权重、3×3窗口、直接Ridge拟合 | Planck、热点概率、地理工具 |
| SLSTR LSCT2/3 area | 栅格/掩膜、有效发射率输入准备 | `base.lsct_window`的约束窗口优化 |
| SLSTR三组分Bayes区域 | 高斯似然统计、温度先验转辐射、两步温差Gauss–Newton、排序边界降维解、物理筛选 | Planck、热点、LST场景数据/网格辅助 |
| MSG旧两阶段及experiments | 窗口正规方程、约束边界、先验联合解及阶段组合，另有复制热点 | 文件/地理辅助与部分物理常量 |
| MSG compatible/declared/hybrid | 相同物理两阶段`retrieve`、不同几何策略、QA、月合成 | 主要依赖NumPy/SciPy/GDAL；未复用统一`base`反演入口 |
| AATSR latlon / site Bayes / v31 | 直接Ridge窗、二次先验+中心Bayes、四版本结果组合分别在各case | 基础LS/二次曲面/约束/权重/辐射工具不同程度共享 |
| MSG/AATSR受控示例 | 约束适配、先验组合、条件数门槛、消融与参考配对 | 基础物理Planck和空间权重，另AST提取MSG旧函数 |
| SLSTR五温度月合成 | 联合有效分箱、同日后景覆盖、有效日等权月均 | 无新的温度反演；调用读取工具 |
| 北京LAI | EVI经验LAI、等年谐波岭拟合、多层次时间补全与方法码 | NumPy/Numba/rasterio通用计算 |
| 北京building/Urban-G | 面积交叠积分、矩形尺寸、轮廓并集、覆盖率/阈值分类 | Shapely/GeoPandas/SciPy通用几何 |

本次检查的是代码方法清单及静态一致性：对MSG实验核心和生产三变体做AST去重，对SLSTR MAP及AATSR先验矩阵逐段检查，并检索温度重建、DL、反射率、干旱/火灾入口。没有运行旧顶层案例、区域实验或下载，也没有打开历史结果来重新背书其精度。

真实观测验证**代码路径**确实存在，如EVO参考读取、时刻配对及多站点评价；比较示例也明确区分历史缓存参考和新独立观测。此处不把“有验证代码”“有历史报告”“合成测试通过”合并成“当前数据上已验证”。AATSR未完成函数、旧脚本全局状态/硬编码路径、不同土壤混合定义和辐射尺度，都应在后续实际运行时单独建立验证证据。

本文件集中描述科学方法和重要组装函数；下载、解包、路径迁移、制图、DOCX编辑、逐产品schema/lineage检查等工程助手不逐个重复列为科学算法。其他批处理/评价脚本的全量函数入口以同目录自动生成的函数索引为准；若其中调用上述求解器，不能再按脚本数量增加算法数量。
