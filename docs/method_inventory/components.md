# 组分温度反演、均质冠层物理与角度核：函数级清单

本清单读取 2026-10-24 工作树现有源码，包括未提交修改；只说明实际实现，不改变算法。`H,W` 为行列，`n` 为观测数，`m` 为组分数，`s` 为窗口边长。`A` 是有效发射率矩阵，`y` 是观测辐射，`x` 是待求组分黑体辐射；通常 `y=A x`，最后才用逆 Planck 得到 K。物理权重并非一般意义上和为 1 的面积比例。除最后另列的执行验证外，本文“异常/风险/会导致”的证据等级均为**源码可见风险**，不是在真实生产数据上复现的失败。

## 1. 方法边界与实际调用路径

|现有实现|实际估计问题|边界/先验的性质|
|---|---|---|
|`retrieve_components`|观测标准差加权 OLS，或固定 λ 的零中心 ridge|无界求解；正辐射、200–380 K 是求解后剔除，非 bounded least squares|
|`retrieve_components_window`|窗口内所有像元/角度共享同一 `m` 维辐射|常数窗口，不是温度二次曲面，也不自动使用距离权重|
|`lsct_window.fitting_Nangle_Mcomponent_window`|距离加权 SSE，SLSQP|辐射上下界、辐射差近似温差、观测包络不等式；没有检查优化成功|
|`fitting_Nangle_Mcomponent_window_quadratic`|每组分 6 个二维二次系数的线性 LS|实际拟合辐射二次曲面，输出中心常数项；当前存在调用关键字不兼容问题|
|`fitting_unknown_linear_sklearn`|RidgeCV/Lasso/BayesianRidge|只有 BayesianRidge 估计 Gaussian 权重/噪声精度；不等于区域三组分 MAP|
|MSG `solve_joint_vectorized_with_prior`|`||Ax-y||²+λ||x-x_prior||²`|外部先验中心的 Tikhonov；求解后裁剪阴影土壤，不是完整不等式优化|
|SLSTR `slstr_lsct3_bayes_scene.scene`|Gaussian 辐射似然+相关温度先验线性化+土壤/植被温差软先验|两步 Gauss–Newton MAP 近似与局部二次顺序约束投影；无 MCMC/后验样本输出|

在本次检索的非归档 `base/`、`cases/`、`tests/` Python 中未找到 `scipy.optimize.lsq_linear` 调用。不能把上述 OLS 的事后范围过滤描述成有界线性最小二乘。

可复用接口路径是 `sensor.retrieve_*_lsct → retrieve_components[_window] → inverse_planck → TemperatureProduct`。旧区域路径是 `LAI/角度/发射率 → effective_weights、εB(LST) → 常数/二次窗口/分阶段/MAP → inverse Planck → 产品文件`。二者需要分别保留名称和统计含义。

## 2. 通用反演接口

### 2.1 `ComponentRetrievalResult`

[定义](C:/work/ls4t/base/lsct.py:18)：冻结 dataclass，字段 `temperature_k`、`radiance` 为 `(...,m)`，`residual_rms`、`condition_number`、`quality_flag` 为空间形状 `(...)`。冻结的是字段绑定，不保证数组元素不可变。没有组分后验协方差/温度标准差字段。

### 2.2 `retrieve_components(observed_radiance, effective_weights, wavelength_um, *, observation_uncertainty=None, ridge=0, max_condition_number=1e6, valid_temperature_range_k=(200,380))`

[实现](C:/work/ls4t/base/lsct.py:26)。输入 `y:(...,n)`、`A:(...,n,m)`；两者空间及观测维必须相同，全局 `n>=m`，λ 不可负。σ 可广播到 `y`，缺省全 1，表示**辐射标准差**，不是 K 标准差。

逐像元删除 `y` 非有限、任一组分权重非有限、σ 非有限或 σ≤0 的观测；有效数 `<m` 标 `INPUT_INVALID|RETRIEVAL_FAILED`。令 `Ã=A/σ`、`ỹ=y/σ`，先算 `cond(Ã)`；非有限或 `>1e6` 标 `ILL_CONDITIONED|RETRIEVAL_FAILED`。这一检查在 ridge 之前，因此 ridge 不会救回已判奇异的矩阵。

λ=0 调 `np.linalg.lstsq(Ã,ỹ,rcond=None)`；λ>0 解 `(ÃᵀÃ+λI)x=Ãᵀỹ`，目标 `Σ((Ax-y)/σ)²+λΣx²`。`LinAlgError` 标失败；任一 `x<=0` 标 `OUT_OF_RANGE|RETRIEVAL_FAILED`。成功后记录的是**未加权、原辐射单位** `sqrt(mean((Ax-y)²))`，不是求解目标值或 K-RMSE。

逆 Planck 后任一组分非有限或超温区，整像元温度、辐射置 NaN，另加 `OUT_OF_RANGE`；该步骤本身不加 `RETRIEVAL_FAILED`，且已计算的残差/条件数可保留。没有非负权重、发射率总和、同地物同时间、太阳天顶角或组分顺序验证；这些由输入构造者保证。

### 2.3 `retrieve_components_window(..., *, window_size=5, observation_uncertainty=None, ridge=0, max_condition_number=1e6, valid_temperature_range_k=(200,380))`

[实现](C:/work/ls4t/base/lsct.py:115)。严格接收 `y:(H,W,n)`、`A:(H,W,n,m)`；s 必须正奇数。边界以 NaN 补齐，逐中心把 `s×s×n` 行展平后交给上述函数；结果仍为 `H×W×m`。因此 `n<m` 可由空间上变化的权重补足秩，前提是窗口中组分辐射局部常量。边缘可以用不完整窗口反演；中心观测本身无效也可由邻域给出结果。没有最少有效像元比例、中心必须有效、空间相似性判断；只有内层有效观测数和条件数门槛。条件数、残差针对整个窗口。

### 2.4 传感器准备文件适配

三个 `retrieve_*_lsct(input_path, output_path, wavelength_um=None, component_names=None, window_size=None, ridge=None, max_condition_number=None, grid_id=None, algorithm_version=None)` 都返回 `None`，写 L2LSCT 产品。默认 λ=0、10.8 μm、s=5、`('soil','vegetation')`、最大条件数 1e6。只有输入为三维 y、四维 A 且 `n<m` 时才走窗口；否则逐像元解，**不会因为设置 s=5 就对二组分两角度进行窗口反演**。组分名长度必须匹配 m；纬经度必须成对出现。它们不自行把 LST 转辐射，不估计 LAI，也不构造权重。

|函数|读取、写出与批处理|
|---|---|
|[`retrieve_slstr_lsct`](C:/work/ls4t/base/slstr/slstr_lsct.py:35)|`read_lsct_input` 读取准备好的输入；`write_lst_product` 写各组分温度、残差、条件数、可选经纬度与 QA；时间 metadata 用 `.get`|
|[`slstr_lsct(indir_lsct_input=None,outdir_lsct=None,years=None,overwrite=None)`](C:/work/ls4t/base/slstr/slstr_lsct.py:119)|必须提供 roots/years；遍历 `{year}/lsct_input/**/*.tif`，写 `{year}/lsct/..._lsct.tif`；存在且不 overwrite 则跳过|
|[`retrieve_aatsr_lsct`](C:/work/ls4t/base/aatsr/aatsr_lsct.py:36)|`np.load(...allow_pickle=False)` 读 NPZ、JSON metadata；`write_product` 写；metadata 的 start/end 必须存在|
|[`aatsr_lsct(indir_lsct_input=None,outdir_lsct=None,years=None,months=None,days=None,overwrite=None)`](C:/work/ls4t/base/aatsr/aatsr_lsct.py:115)|按年/月/日目录递归 NPZ，默认月 1–12、日 1–31，缺目录跳过，输出 `_lsct.npz`|
|[`retrieve_msg_lsct`](C:/work/ls4t/base/msg/msg_lsct.py:36)|NPZ 读准备的时空观测，`write_temperature_product` 写 GeoTIFF；通用求解仍假设同一 x，未在接口内引入 DTC|
|[`msg_lsct(indir_lsct_input=None,outdir_lsct=None,years=None,months=None,days=None,overwrite=None)`](C:/work/ls4t/base/msg/msg_lsct.py:118)|与 AATSR 相同日期遍历，写 `_lsct.tif`；无各场景异常收集、自动回退或重试|

## 3. 旧线性与约束窗口函数

### 3.1 点拟合及回归器

- [`fitting_Nangle_Mcomponent_point(w,b,n,m,method='ridge')`](C:/work/ls4t/base/lsct.py:504)：`w:(n,m)`、`b:(n,)`，返回 `m` 维组分辐射；文档把 b 称“亮温”但函数没有 Planck 转换，物理反演调用必须传辐射。形状不符打印并返回整数 -1，未做 NaN/秩/温区/正值检查。支持 `ls/ridge/lasso/bayesianridge`，其他字符串会导致 p 未赋值。
- [`fitting_unknown_linear_ls(y,A)`](C:/work/ls4t/base/fitting.py:12)：直接 `scipy.linalg.lstsq(A,y)[0]`，返回系数，不返回 rank/singular values/residual。
- [`fitting_unknown_linear_sklearn(y,A,method='ridge')`](C:/work/ls4t/base/fitting.py:23)：`RidgeCV(alphas=[0.01],fit_intercept=False)` 实际只有一个候选 λ，不能宣传为广泛超参数搜索；目标 `||Ax-y||²+0.01||x||²`。Lasso 是 `Lasso(alpha=.01,fit_intercept=False)`，目标 `||Ax-y||²/(2N)+.01||x||₁`。`BayesianRidge(fit_intercept=False)` 由 sklearn 估计噪声/权重精度，但只返回 `.coef_`，没有返回 `.sigma_` 或预测不确定性。没有标准化、物理边界或成功状态；未知 method 返回初值标量 1.0。

### 3.2 空间权重与初值/边界

[`set_weights(window_size)`](C:/work/ls4t/base/lsct.py:432) 及 [同名副本](C:/work/ls4t/base/lsct_window.py:104)：中心 `s//2`，距离 d≤s 时 `q=(1-(d/s)²)²`，否则 0；返回 `(s,s)`，未归一化。s 是**完整窗口边长**而不是半径，所以一般角点仍有正权重。

[`set_x0_bnds_Nangle_Mcomponent(lst,n,m,ws=None,wl=10.8)`](C:/work/ls4t/base/lsct.py:446) 用中心（若 ws 给出）或点的各角 LST：`T̄=nanmean(LST)`、`b=Bλ(LST)`。n 未实际参与计算。下表 bounds 是 K 偏移先经 Planck 转换；初值中的 +5/+10 等则直接加在**辐射**上，不能读成温度差。未 clip 初值。

|实现/组分数|辐射初值 x0|各组分 bounds 对 T̄ 的 K 偏移|
|---|---|---|
|base.lsct，m=2|`[max(b)+5,min(b)-3]`|`[-10,+40]；[-10,+10]`|
|base.lsct，m=3|`[max(b)+10,min(b)-5,mean(b)]`|`[-10,+40]；[-30,+30]；[-10,+20]`|
|base.lsct，m=4|`[max(b)+10,min(b)-5,mean(b),min(b)-5]`|`[-10,+40]；[-30,+30]；[-20,+20]；[-30,+30]`|
|[base.lsct_window 同名函数](C:/work/ls4t/base/lsct_window.py:118)，m=2|同上 m=2|第二组分改 `[-30,+30]`|
|base.lsct_window，m=3|第一初值 `max(b)+15`，其他同上|第三组分改 `[-20,+20]`|
|base.lsct_window，m=4|同上 m=4|同上 m=4|

[`set_x0_bnds_Nangle_Mcomponent_night`](C:/work/ls4t/base/lsct.py:475) 签名相同：m=2 初值 `[max(b),min(b)]`，m=3 加 `mean(b)`，所有 bounds 都 `T̄±10 K`；m=4 初值无加减偏移，但 bounds 仍与日间 m=4 相同，并非四组分统一夜间 ±10 K。所有这些函数只处理 m=2/3/4，其他 m 未定义返回量。

### 3.3 温差与观测包络约束

[`constraint_func_Nangle_2component(x,lst,d,ws=None,wl=10.8)`](C:/work/ls4t/base/lsct.py:377)、[`constraint_func_Nangle_3component(x,lst,d12,d23,ws=None,wl=10.8)`](C:/work/ls4t/base/lsct.py:402) 在 [lsct_window:49](C:/work/ls4t/base/lsct_window.py:49)、[lsct_window:74](C:/work/ls4t/base/lsct_window.py:74) 各有副本。

返回长度 4/6 的 SLSQP `g(x)>=0` 向量：`max(x)-max(B(LST))`、`min(B(LST))-min(x)` 保证组分辐射包住中心观测黑体辐射；随后对相邻组分差 `x0-x1`、三组分再加 `x1-x2` 设置上下限。差限实际为 `B_wl(T̄+d/2)-B_10.8(T̄-d/2)`：两项波长不一致的硬编码会影响 wl≠10.8；这是以 T̄ 为参考的辐射差近似，不是精确 `B⁻¹(x_i)-B⁻¹(x_j)` 约束。max/min 包络构成非光滑且可能多分支的可行域。

### 3.4 优化包装、常数窗口与二次窗口

- [`fitting_unknown_nonlinear_min(fun,y,A,xn,x0,bnds,method='Powell',constraints=None,**kwargs)`](C:/work/ls4t/base/lsct_window.py:145)：调用 `minimize(fun,x0,args=(y,A,xn,*kwargs.values()),method=method,bounds=bnds,constraints=constraints)`。kwargs 按插入顺序变为位置参数，并非按名传给目标。只返回 `res.x`，不检查 `success/status/message`，不返回目标值、迭代数或约束残差。改 method 为不支持约束的方法会改变能力，接口没有防护。
- [`fitting_Nangle_Mcomponent_window(w,b,n,m,mask,weight,constraints,x0,bounds,window_size=5,method='SLSQP')`](C:/work/ls4t/base/lsct_window.py:174)：`w:(s,s,n,m)`、`b/mask:(s,s,n)`、`weight:(s,s)`。展平并重复每像元空间权重 n 次，按 bool mask 取行，少于 `2m` 条观测返回全 NaN。求 `Σq_i(A_i x-y_i)²`，返回 `(m,)` 辐射。形状错误返回 -1；mask 外 NaN 不参与，mask 内 NaN 不另筛除。虽然调用非线性优化器，其观测前向模型仍是线性的；非线性来自约束表达式。
- [`inv_lsct2_window(n,m,ws,wl,w,b,mask,lst)`](C:/work/ls4t/base/lsct_window.py:230)：只扫描距边界 `ws//2` 以内中心，中心全部 n 个 mask 必须有效，采用上项求解、空间权重和差范围 `[-5,30] K`。输出 `(H,W,m)` K。初值/边界调用没有传 wl，故使用 10.8 μm 默认，约束与最后逆 Planck 才传 wl。
- [`inv_lsct3_window(...)`](C:/work/ls4t/base/lsct_window.py:261)：同流程，`T_sun-T_shade` 范围 `[5,40]`、`T_shade-T_veg` 范围 `[-15,15] K` 的辐射近似。二者结果辐射数组初始零，未扫描边缘经旧 inverse Planck 得到 0 K（伴随除零），不是 NaN。没有 QA/条件数；未强制 m 必须等于函数名中的 2/3。二函数在 base.lsct:14 重导出。
- [`fitting_Nangle_Mcomponent_window_quadratic(w,b,n,m,mask,weight,window_size=5)`](C:/work/ls4t/base/lsct.py:528)：空间基 `z=[1,u,v,uv,u²,v²]`，设计列 `A_(j,k)=w_j z_k`，共 `6m` 未知数；至少 `6m` 有效观测，每像元基重复 n 次匹配角度展平次序。拟合后取各组分第 0 项 `(m,)` 作为中心辐射，**weight 参数没有实际使用**。当前 `lstsq` 来自 scipy.linalg，调用却传 `rcond=None`（NumPy 的参数名），被宽泛 except 捕获并返回 NaN；这是源码可定位的兼容性风险，不是已验证可运行的二次解。s 未检查奇数，偶数会与 `[-radius,+radius]` 网格长度不匹配。

## 4. LAI—组分权重—辐射构造

|函数、输入/输出|实际公式/用途/限制|
|---|---|
|[`cal_fvc_from_lai(thetav,lai)`](C:/work/ls4t/base/lsct.py:247)|`fvc=1-exp(-0.5 LAI/cos(vza))`，角度 degree，clip 到 [0,1]；通过下标赋值 clip，标量输入兼容性弱；无日夜/无效角度处理|
|[`cal_rad_from_lst(lst,wl,lai,vza,emisS,emisV)`](C:/work/ls4t/base/lsct.py:227)|`f=1-gap(lai,vza)`，`y=Bλ(LST)[f εv+(1-f)εs+C]`，`C=(1-εs)εv·0.75·(1-f)`。是地表有效辐射构造，不是 TOA 大气正演；F=.75 与区域案例 F=.05 不同|
|[`cal_rad_from_lst_fvc(lst,wl,fvc,emisS,emisV)`](C:/work/ls4t/base/lsct.py:340)|同式但直接用 fvc；未 clip fvc/ε 或检查范围；返回广播形状辐射|
|[`cal_psoil_hom(lai,sza)`](C:/work/ls4t/base/lsct.py:358)|返回 `exp(-.5 LAI/cos(sza))`，作为光照土壤占总土壤比例；一维 sza 强行 reshape(1,1)，仅长度 1 能成功，不是任意一维矢量接口；单点 squeeze|
|[`sample_hom_Emis(lai,hspot,wavelength,emissivity_soil,emissivity_leaf,vza,sza,raa)`](C:/work/ls4t/base/lsct.py:201)|创建 Hom、设结构/光学/角度、`run_emis()`；输出顺序光照土壤、阴影土壤、光照叶、阴影叶；执行后会把 `raa==180` 的传入 vza 原地乘 -1，调用者数组可被改写|
|[`sample_hom_Emis2(...)`](C:/work/ls4t/base/lsct.py:214)|同样流程，但调用 `Hom.run_emis2()`；当前 Hom 没定义该方法，因此此路径会 AttributeError，不能算可用二组分权重实现|
|[`cal_effective_emissivity_hom(lai,hspot,wl,emisS,emisV,vza,sza,vaa,saa,n,m,CI=1)`](C:/work/ls4t/base/lsct.py:257)|点输入输出 `(n,m)`，区域 LAI `(H,W)` 输出 `(H,W,n,m)`；先计算四组分，m=2 合并两土壤/两叶，m=3 保留光照/阴影土壤并合并叶，m=4 保留全部。sza≥90 被原地设 89.9；CI 参数从未传入物理模型。区域 m=2 使用前述缺失 run_emis2 路径；区域 emissivity 的二维数组与 `emissivity_direct` 展平广播约定也需单独验证。m 非 2/3/4 返回初始化全零；缺少显式参数验证|

### 4.1 均质冠层基础物理函数

角度默认为 degree，LAI/CI/G/发射率均无量纲；没有通用输入域校验。四组分顺序固定为 `[soil_sunlit,soil_shaded,leaf_sunlit,leaf_shaded]`。

- [`gap_probability_hom_analytical(lai,xza,CI=1,G=.5)`](C:/work/ls4t/base/rt/gap.py:10)：`Pgap=exp(-LAI·G·CI/cos(xza))`，返回广播形状。负 LAI、越过 90° 或余弦近零可能造成非物理/溢出。
- [`gap_probability_hom_hemisphere_analytical(lai,CI=1)`](C:/work/ls4t/base/rt/gap.py:23)：`exp(-.825 LAI·CI)`；半球透过率经验参数化，不是数值半球积分。
- [`hotspot_layer(lai,hspot,vza,sza,vsa,CIs=1,CIv=1,G=.5)`](C:/work/ls4t/base/rt/hotspot.py:11)：`kv=G/cos(v)`、`ks=G/cos(s)`，几何距离平方 `δ=sec²s+sec²v-2 cosξ/(cos s cos v)`；`d=hspot/(2/(kv+ks))`，`α=sqrt(δ)/d`，重叠因子 `w=(1-exp(-α))/α`，`Pss=exp[-LAI(CIs ks+CIv kv-sqrt(CIs ks CIv kv)w)]`。数组 δ<1e-4 用 w=1；标量恰好热点没有 α=0 极限保护。δ 只在该函数中先截到非负。返回光照且可见土壤比例。
- [`hotspot_analytical(lai,hspot,vza,sza,vsa,CIi=1,CIv=1,G=.5)`](C:/work/ls4t/base/rt/hotspot.py:64)：两层经验近似光照且可见叶比例。由 gap_v/gap_s 和 `index=.83-.04 floor(LAI/.5)` 求上层高度：`bv_u=1-(1-bv)index`、`hv=-log(bv_u)cos(v)/(G LAI)`，太阳方向类似，`h_u=sqrt(hv hi)`。最终 `1-exp(-G LAI h_u CIv/cos v)+[1-exp(-G sqrt(CIv CIi/(cos v cos s))w LAI(1-h_u))]·Pgap_upper`。上下层热点 w 都用完整高度 H=1；不是显式逐叶追踪。未保护 LAI=0、超大 LAI index 变负、δ 微负平方根。
- [`hotspot_vegetation_volume(lai,sza,CI=1,G=.5)`](C:/work/ls4t/base/rt/hotspot.py:162)：整体光照叶比例 `V=(1-exp(-G LAI CI/cos s)) cos s/(G LAI CI)`，无 LAI→0 极限处理。
- [`proportion_bidirectional_hom_one(lai,hspot,vza,sza,vsa)`](C:/work/ls4t/base/rt/proportion.py:11)：`Ps=gap(v)`、`Pv=1-Ps`、Pss/Pvs 调上述两个 hotspot，返回 `Pss, Ps-Pss, Pvs, Pv-Pvs` 元组；未自行截负值或归一化。
- [`multiple_scattering_analytical_sunlit(lai,vza,sza,refl_soil,refl_leaf)`](C:/work/ls4t/base/rt/scatter.py:12)：令 `b=gap(v)`、`M=exp(-.825 LAI)`、V 为光照叶体比例。总叶散射贡献 `S=[b(1-M)ρs+(1-α)(1-bM)(1-b)ρl](1-ρl)`，输出 `(S·V,S·(1-V))`。α 按 `int(vza/10)` 查十元素表 `[.2885375,.2885375,.2964427,.3003953,.3083004,.3201581,.3399209,.3715415,.4189723,1]`，没有插值或 index clip，负 vza 会用负下标，≥100°可越界。
- [`emissivity_direct(Pcom,Ecom)`](C:/work/ls4t/base/rt/emissivity.py:11)：各组分 `P_j ε_j`，返回组分贡献与总和。`np.size(Pcom)==4` 分支迭代，其余分支先把负 P 设零、NaN 转零，随后 `Pcom.reshape(4,-1)*Ecom.reshape(-1,1)`；该形状假设适合四个标量发射率，不保证空间变化 ε 数组广播正确，且把缺测改为零可能掩盖无效输入。
- [`emissivity_scatter_analytical(lai,emis_l,emis_s,vza,sza)`](C:/work/ls4t/base/rt/emissivity.py:38)：ρ=1-ε，调用散射函数，只给光照/阴影叶添加 S；土壤两项为零；返回四组分数组 `(4,... )` 和总和，仅处理 vza.ndim=1/2。
- [`radiance_direct(Ecom,Rcom)`](C:/work/ls4t/base/rt/radiance.py:10)、[`radiance_scatter(Ecom,Rcom)`](C:/work/ls4t/base/rt/radiance.py:30)：相同实现 `Σ_j Ecom[j,:]Rcom[j]`，按 `np.size(Rcom)` 作为组分数。适合四个标量辐射加角度轴；不是任意 `(4,H,W)` 组分辐射张量的通用 einsum。

### 4.2 `Hom` 前向类与 Planck 兼容函数

[`Hom`](C:/work/ls4t/base/rt/hom.py:15) 默认 LAI=1、hspot=.2、G=.5、波长 10.5、叶/土壤 ε=.985/.955、光照土壤/叶 303 K、阴影土壤/叶 300 K；这些是类属性。`clumping_index`、叶倾角等属性未实际传至上述函数。

|方法|输入、计算和返回|
|---|---|
|[`set_structure(leaf_area_index,hspot)`](C:/work/ls4t/base/rt/hom.py:41)|只赋 LAI/hspot，无检验，返回 None|
|[`set_thermal(temperature_soil_sunlit,temperature_soil_shaded,temperature_leaf_sunlit,temperature_leaf_shaded)`](C:/work/ls4t/base/rt/hom.py:45)|把四温度转 ndarray 存储，返回 None|
|[`set_optical(wavelength,emissivity_soil,emissivity_leaf)`](C:/work/ls4t/base/rt/hom.py:51)|存波长及发射率，无一致性验证|
|[`set_angle(view_zenith_angle,solar_zenith_angle,relative_azimuth_angle)`](C:/work/ls4t/base/rt/hom.py:57)|按 ndarray.size 更新 number_angle，标量通过 resize 扩展；不自动 broadcast 不同长度 ndarray；number_angle 只增不减|
|[`run_emis(ifradiance=0)`](C:/work/ls4t/base/rt/hom.py:77)|四组分比例→direct ε→scatter ε→相加，再 `nan_to_num`；ifradiance 未用，输出有效发射率而非温度|
|[`run(ifradiance=0)`](C:/work/ls4t/base/rt/hom.py:101)|四温度→黑体辐射→direct/scatter 相加存 self.radiance；ifradiance=1 返回辐射，其他返回逆 Planck 温度。**正向调用 `planck(Tcom)` 使用 physicsF 默认 10.8，逆向却用 self.wavelength 默认 10.5**，设其它波长也未修正正向；需记作现有不一致|

[`physicsF.planck(Ts,wavelength=10.8)`](C:/work/ls4t/base/rt/physicsF.py:10) 与 [`physicsF.inv_planck(rad,wavelength=10.8)`](C:/work/ls4t/base/rt/physicsF.py:25) 参数顺序和 `base.radiometry.planck(wavelength,Ts)` 相反。常数 `c1=11910.439340652`、`c2=14388.291040407`，`B=c1·10000/[λ⁵(exp(c2/(λT))-1)]`；λ μm、T K、辐射数值对应 W m⁻² sr⁻¹ μm⁻¹。正向把 T<100 猜作摄氏度并加 273.15，ndarray 会被原地改写；负/零辐射逆向不安全。

[`lsct_window.planck(wavelength,Ts)`](C:/work/ls4t/base/lsct_window.py:16) 和 [`inv_planck(wavelength,rad)`](C:/work/ls4t/base/lsct_window.py:35) 使用同一旧常数但**没有摄氏度自动转换**，尽管 docstring 声称可摄氏度。新 `radiometry.planck_radiance`/`inverse_planck` 用 `C1=1.191042972e8`、`C2=1.438776877e4`、严格 K、expm1/log1p；[来源](C:/work/ls4t/base/radiometry.py:11)。不同常数体系和自动摄氏度逻辑不能混用作精确 round-trip 标准。

## 5. 活跃案例中的额外反演方法

### 5.1 SLSTR 双角度常数窗口与三组分 ridge

[`lsct2_scene(scene,year,lat,lon,lai0,out_file)`](C:/work/ls4t/cases/slstr/slstr_lsct2_scene_parallel.py:287) 是区域批处理实际数值入口，返回 written/skipped/no_valid 等状态字符串。LAI÷1000，角度/LST÷100，fvc 使用 `1-exp(-.825 LAI·.5)` 形成像元发射率；定向 fvc 用 `1-exp(-.5 LAI/cos v)`。散射近似 F=.05 加到植被权重，像元 ε 上限 .995；y=`εBλ(LST)`。5×5 两视角共最多 50 行，中心及邻域 cloud/land/LAI/thermal 掩码后，只保留 `.1<soil effective ε<.9` 且超过 5 条观测，直接 scipy lstsq 两个常数辐射，再逆 Planck。没有 cond、非负约束或 200–380 K 过滤，未计算位置保持零。输出 band 顺序 soil、vegetation；[求解行](C:/work/ls4t/cases/slstr/slstr_lsct2_scene_parallel.py:425)。它与 sensor API 自动分支策略不同。

[`fitting_with_ridge(bb,ww)`](C:/work/ls4t/cases/slstr/slstr_lsct3_scene.py:28) 使用 `Ridge(alpha=.01,fit_intercept=False).fit(ww.T,bb.T)`，返回 coef，ww 按 `(3,N)` 存储。没有 Bayesian 后验或边界。

### 5.2 SLSTR 三组分区域 MAP

[`scene(year,scene_name)`](C:/work/ls4t/cases/slstr/slstr_lsct3_bayes_scene.py:210) 是主数值/文件函数；辅助 [`derivative(T)`](C:/work/ls4t/cases/slstr/slstr_lsct3_bayes_scene.py:79) 用 Planck 中心差分，[`box_sum(a)`](C:/work/ls4t/cases/slstr/slstr_lsct3_bayes_scene.py:83) 做 5×5 uniform_filter 累加。输出四张图 soil mixture、vegetation、sunlit soil、shaded soil；并写方法、输入签名、有效像元/顺序约束激活计数。

设 x 顺序光照土壤、阴影土壤、植被。权重为 `A=[εs·Pss, εs·(Psoil-Pss), εv·fvc_directional]`，hspot=.25；y 仍乘含 F=.05 的像元 ε，但 A 没有把该 C 显式加到叶权重，不能默认严格 RT 闭合。通过 day/solar、cloud=0、0≤vza<80、.05<LAI≤10、200≤LST≤360、ε>0、A≥-1e-6 筛行。中心两视角均有效且各视角 5×5 至少 8 个有效样本，去掉两像元边框。

Gaussian 部分：`μ=[B(300)]×3`，温度先验标准差 `[50,50,10] K`、任意两个分量相关系数 .25；以 `d300=dB/dT|300` 把温度协方差换为辐射 `C0=d300² C_T`。似然 σ²=`max((10·dB/dT|center mean LST)²,1e-10)`，同一中心窗口共享。先解 `Q=AᵀA/σ²+C0⁻¹`、`h=Aᵀy/σ²+C0⁻¹μ`、`x=Q⁻¹h`。

再令 oblique 光照土壤占比 `p=clip(Pss/Psoil,0,1)`，`g(x)=B⁻¹(px0+(1-p)x1)-B⁻¹(x2)`，添加 `[(g(x)-9)/10]²` 软先验。固定做两次线性化：`J=[p/B'(Tsoil),(1-p)/B'(Tsoil),-1/B'(Tveg)]`，`Q'=Q+JᵀJ/100`、`h'=h+Jᵀ(9-g+Jx)/100`。仅计算 g/J 时把 x clip 到 B(200)–B(400)，并非每轮有界最优化。

若最后 x0<x1，把参数限制为 x=Cz，C 两个土壤行相同，解 `(CᵀQ'C)z=Cᵀh'`，是**当前局部二次目标**的等温土壤边界投影。最后全组分有限且 200–400 K 才保留。批量 solve 异常可使整批跳过；投影求解异常被 pass，不提供单像元收敛证明；两次迭代没有收敛阈值或实际目标下降检查。没有输出后验协方差、credible interval 或采样；“Bayes”应准确称相关 Gaussian 先验的 MAP/Laplace 风格近似。

土壤产品是 `B⁻¹(p x0+(1-p)x1)`，不是两温度算术平均，也不是光照土壤温度；[核心](C:/work/ls4t/cases/slstr/slstr_lsct3_bayes_scene.py:298)。

### 5.3 MSG 向量化常数窗口、两阶段和先验平差

主文件 [msg_lsct_iter.py](C:/work/ls4t/cases/msg/msg_lsct_iter.py:81) 保有以下函数；`experiments/` 中有数值近似或重复版本，列出差异而不把重名当不同科学方法。以下输出都为 `(H,W)` 分量辐射 tuple，不是 K。

|函数/来源|实际方法、门槛及限制|
|---|---|
|[`solve_5x5_three_components(rad_euro,rad_iodc,w)`](C:/work/ls4t/cases/msg/msg_lsct_iter.py:81)|w `(H,W,6)`，每视角三个权重。构造正规方程六个独立 Gram 元与三 RHS，用 `uniform_filter(size=5,mode='nearest')×25` 求和，`abs(det)>1e-6` 且有效像元>10、中心不缺测时批量 solve；任一分量≤0，三者置 NaN|
|[`solve_2x2_system_5x5(rad1,rad2,w_a1,w_b1,w_a2,w_b2,size=5)`](C:/work/ls4t/cases/msg/msg_lsct_iter.py:160)|同样窗口 Gram，2×2 用 Cramer 显式解；`abs(det)<1e-8`、有效像元 `<.4 size²`、中心无效剔除；负辐射分别置 NaN。size 可变，函数名不代表总是 5×5|
|[`solve_constrained_vectorized1(rad_e,rad_i,w2,w3,w5,w6,bs1_fixed,dif=.5)`](C:/work/ls4t/cases/msg/msg_lsct_iter.py:225)|先解 5×5 阴影土壤/植被；若 bs2>固定光照土壤，把 bs2 固定并按**中心双视角**单未知 LS 重算 bv。dif 未用；窗口目标和边界中心目标不一致|
|[`solve_constrained_vectorized2(...,dif=.5)`](C:/work/ls4t/cases/msg/msg_lsct_iter.py:247)|只限制 `abs(bs2-bv)<=dif`，dif 为辐射差，不是 K。违约时枚举 bs2=bv±dif 两条边界中心 LS，选中心 SSE 较小者；bs1_fixed 未参与这一约束。边界公式 `bv=Σ(w_s+w_v)(rad∓w_s dif)/[Σ(w_s+w_v)²+1e-9]`|
|[`solve_joint_vectorized_with_prior(rad_e,rad_i,w,x_prior,lmbda=.5)`](C:/work/ls4t/cases/msg/msg_lsct_iter.py:290)|逐像元 2 行、3 个分量，解 `(AᵀA+λI)x=Aᵀy+λx_prior`，手工伴随矩阵/行列式；返回前 `bs2=min(bs2,bs1)`。没有奇异/λ 正值/有限输入/温区检查；裁剪后不重新拟合 bv，也不保证约束目标最优|
|[`solve_constrained_vectorized(...)`](C:/work/ls4t/cases/msg/experiments/msg_lsct_3c_constrained.py:14)|额外同时限制 bs2≤bs1_fixed 与 abs(bs2-bv)≤dif。候选包含无约束解及三条边界解，按中心 SSE/可行性比较；未显式枚举边界交点，若全部候选不合格仍可能保留原违约解，不能视为一般精确 QP|
|[`solve_3x3_least_squares(rad_euro,rad_iodc,w)`](C:/work/ls4t/cases/msg/experiments/msg_lsct_2c_window.py:44)|w `(H,W,4)`，2×2 Gram 显式解，3×3 nearest 求和、有效数≥3、abs(det)≥1e-8；返回变量名 `(bv_rad,bs_rad)` 实际分别对应第 0/1 系数列，必须以输入列顺序定物理含义|
|[`solve_5x5_least_squares_robust(...)`](C:/work/ls4t/cases/msg/experiments/msg_lsct_2c_window.py:106)|5×5、有效数≥5、abs(det)≥1e-8、非正辐射置 NaN；实际返回 `(bs_rad,bv_rad)`，源码尾部注释反称植被/土壤，需以运算为准。robust 只指过滤，不是 Huber/M估计|
|[`solve_3x3_three_components(...)`](C:/work/ls4t/cases/msg/experiments/msg_lsct_3c_window.py:130)|3×3、有效数≥4、abs(det)>1e-7，辐射各组分要求 0<x≤30；没有正值约束优化，属于事后拒绝|

`solve_5x5_three_components` 的重复位置：[3c_window:51](C:/work/ls4t/cases/msg/experiments/msg_lsct_3c_window.py:51)、[two_stage:51](C:/work/ls4t/cases/msg/experiments/msg_lsct_3c_two_stage.py:51)、[diagnostics:69](C:/work/ls4t/cases/msg/experiments/msg_lsct_3c_diagnostics.py:69)、[constrained:250](C:/work/ls4t/cases/msg/experiments/msg_lsct_3c_constrained.py:250)。`solve_2x2_system_5x5` 对应 [two_stage:132](C:/work/ls4t/cases/msg/experiments/msg_lsct_3c_two_stage.py:132)、[diagnostics:148](C:/work/ls4t/cases/msg/experiments/msg_lsct_3c_diagnostics.py:148)、[constrained:329](C:/work/ls4t/cases/msg/experiments/msg_lsct_3c_constrained.py:329)。`solve_constrained_vectorized1/2` 对应 [diagnostics:213](C:/work/ls4t/cases/msg/experiments/msg_lsct_3c_diagnostics.py:213)、[diagnostics:235](C:/work/ls4t/cases/msg/experiments/msg_lsct_3c_diagnostics.py:235)、[constrained:97](C:/work/ls4t/cases/msg/experiments/msg_lsct_3c_constrained.py:97)、[constrained:119](C:/work/ls4t/cases/msg/experiments/msg_lsct_3c_constrained.py:119)。先验平差还有 [diagnostics:278](C:/work/ls4t/cases/msg/experiments/msg_lsct_3c_diagnostics.py:278) 和 [constrained:395](C:/work/ls4t/cases/msg/experiments/msg_lsct_3c_constrained.py:395)，后者批量 solve/输入 mask 与主文件手工解不是逐行等同。

上述旧窗口代码的 NaN 策略不是严格整行屏蔽：先分别把乘积 NaN 转零，有效计数常只检查部分权重，Gram 中可能仍保留缺辐射观测的贡献；nearest 边界会重复边缘像元。正常方程还会平方条件数；行列式绝对阈值不等于 condition number 门槛。旧堆栈 `np.linalg.solve(A_stack[mask],B_stack[mask])` 的 RHS 形状需要关注 NumPy 2 批处理语义。

MSG 主调用 [570 行起](C:/work/ls4t/cases/msg/msg_lsct_iter.py:570)：先在 size=3 窗口分离光照土壤与“阴影土壤+植被”；固定光照土壤、对残差用 `vectorized2`，再裁剪阴影≤光照、过热植被退为阴影值；以三者为先验做联合 λ 平差。土壤混合权重使用太阳方向 gap，而 SLSTR MAP 用 oblique 可见土壤光照占比，两种 soil mixture 定义不同。最后联合筛 250–350 K 与 LAI≥.05。该路线不是一次联合三组分无约束解，也不是显式物理能量平衡模型。

MSG 本地 [`hotspot_layer`](C:/work/ls4t/cases/msg/msg_lsct_iter.py:26) 返回 `(双向gap,单向gap)`，与 base 同名只返回单个值不同；采用距离平方 clip 非负和 α<1e-5 极限。[`calculate_scattering_angle(sza,saa,vza,vaa)`](C:/work/ls4t/cases/msg/msg_lsct_iter.py:51) 用球面余弦及 clip[-1,1] 返回 degree；是几何夹角辅助，不执行反演。实验 constrained/diagnostics 中有同样本地辅助函数及 Planck 副本，应避免仅按同名替换。

### 5.4 受控 MSG/AATSR 方法对照辅助函数

[tests/examples/msg_aatsr_comparison.py](C:/work/ls4t/tests/examples/msg_aatsr_comparison.py:34) 中 `planck(t)` 固定现代 10.5 μm；`least_squares(a,b,ridge=0)` 要求行数足、满秩、cond≤1e6 后 OLS/ridge。`quadratic(w,y,good)` 建 12 列二组分辐射二次曲面，返回中心 `(2,)` 和 `(5,5,2)` 面。`posterior(a,b,prior)` 解 `(AᵀA/.05+diag(.5,1))x=Aᵀb/.05+diag(.5,1)prior`，是给定辐射噪声方差/先验精度的点 MAP。

[`constrained(a,b,center_lst,spatial_weights,delta_constraint=True)`](C:/work/ls4t/tests/examples/msg_aatsr_comparison.py:60) 复现 legacy 辐射包络与近似温差，但两个 Planck 都用 10.5 μm，bounds 采用 base.lsct 的较窄版本；warm-soil 和 LS 两初值，经 clip 后 SLSQP（解析 SSE 梯度、ftol=1e-9、maxiter=150），要求 `success` 且所有 g≥-1e-6，取可行解最小 SSE，否则 NaN。`delta_constraint=False` 仍保留 box 和包络，不是无约束 LS。

[`solve_window(y,w,center_lst,method,exclude_center=False)`](C:/work/ls4t/tests/examples/msg_aatsr_comparison.py:106) 要求至少 10 个双视角完整像元，分发 ls2/ls3/ridge2、SLSQP、二次曲面与点后验。`map_constant2` 用邻域常数解为 prior；`map_quadratic2` 用曲面中 4.5<辐射<20 的双视角完整位置经固定 5×5 权重加权平均；`map_exclude_center2` 去掉中心求 prior，最终仍使用中心观测形成 posterior。这里“exclude center”不表示最终估计不含中心。它们是受控对照实现，不能自动代替生产算法。

## 6. 角度核与核模型

这些函数输出无量纲核，或者随系数单位变化的模拟量；不自行做 Planck 转换、不识别 K 与辐射。`vza/sza/raa` 采用 degree；多数 Li/Ross/Solar/RPV 函数对 raa>180 原地折返，标量与 ndarray 的兼容性不同。无统一 finite/domain 检查；组合函数的 isotropic 项是 `ones(np.size(vza))`，通常按一维角度数组使用，不是保持任意二维输入形状。

### 6.1 单核

|函数|公式与实现特征|
|---|---|
|[`kernel_Vin(vza)`](C:/work/ls4t/base/kernel.py:12)|`1-cos(v)`|
|[`kernel_RLf(vza,sza,raa)`](C:/work/ls4t/base/kernel.py:129)|`sqrt(tan²v+tan²s-2 tanv tans cosraa)`；不 clip 根号，传入 radian 会被再次当 degree 转换|
|[`kernel_Solar(vza,sza,raa)`](C:/work/ls4t/base/kernel.py:105)|`sin(abs(v)) sin(s) cos(s) cos(raa) cos(s-abs(v))`|
|[`kernel_LSF_analytical(vza)`](C:/work/ls4t/base/kernel.py:144)|令 c=cosv，`.069c²-.215c+1.176`|
|[`kernel_LSF(vza)`](C:/work/ls4t/base/kernel.py:156)|`(1+2c)/(sqrt(.96)+2·.96c)-.25c/(1+2c)+.15(1-exp(-.75/c))`；`.96c` 不是 `sqrt(.96)c`|
|[`kernel_TLSF(vza,w=.10)`](C:/work/ls4t/base/kernel.py:169)|`(1+2c)/(sqrt(1-w)+2sqrt(1-w)c)-.25c/(1+2c)`|
|[`kernel_VLSF(vza,w=.15)`](C:/work/ls4t/base/kernel.py:182)|公式与 TLSF 相同，仅默认 w 不同；不是另一个求解器|
|[`kernel_Thapke(vza,w=.10,K=1)`](C:/work/ls4t/base/kernel.py:195)|令 r=sqrt(1-w)、f=2cosv/K，返回 `r(1+f)/(1+fr)`|
|[`kernel_LiDense(vza,sza,raa,h=2,r=1,b=1)`](C:/work/ls4t/base/kernel.py:22)|先 `v'=atan((b/r)tanv)`，s 同理；令 ξ 为夹角、D²=tan²v'+tan²s'-2tanv'tans'cosraa，`cos t=(h/b)sqrt(D²+(tanv'tans'sinraa)²)/(secv'+secs')`，`O=(t-sint cost)(secv'+secs')/π`；返回 `(1+cosξ)secv'secs'/(secv'+secs'-O)-2`。D²截非负，cos t 超 ±1 才改到 ±.999|
|[`kernel_LiSparse(...)`](C:/work/ls4t/base/kernel.py:63)|同变换/重叠 O，返回 `O-secv'-secs'+.5(1+cosξ)secv'secs'`|
|[`kernel_RossThick(vza,sza,raa)`](C:/work/ls4t/base/kernel.py:209)|`[(π/2-ξ)cosξ+sinξ]/(cosv+coss)-π/4`；arccos 输入未 clip|
|[`kernel_RossThin(...)`](C:/work/ls4t/base/kernel.py:233)|同分子除 `(cosv coss)`，再减 π/2|

### 6.2 组合核及显式预测函数

下列组合签名均 `(vza,sza,raa)`，输出 tuple 而非自动堆叠设计矩阵：

|组合函数|输出顺序|
|---|---|
|[`kernel_LSFLiDense`](C:/work/ls4t/base/kernel.py:257)|LSF、LiDense、1|
|[`kernel_LSFLiDenseRossThick`](C:/work/ls4t/base/kernel.py:272)|LSF、LiDense、RossThick、1|
|[`kernel_LSFLiSparse`](C:/work/ls4t/base/kernel.py:288)|LSF、LiSparse、1|
|[`kernel_RossThickLiSparse`](C:/work/ls4t/base/kernel.py:303)|RossThick、LiSparse、1|
|[`kernel_RossThickLiDense`](C:/work/ls4t/base/kernel.py:319)|RossThick、LiDense、1|
|[`kernel_VinLiDense`](C:/work/ls4t/base/kernel.py:335)|Vin、LiDense、1|
|[`kernel_VinLiSparse`](C:/work/ls4t/base/kernel.py:351)|Vin、LiSparse、1|
|[`kernel_LSFRL`](C:/work/ls4t/base/kernel.py:367)|**1、LSF、RLf**；顺序与其它组合不同|
|[`kernel_VinSolar`](C:/work/ls4t/base/kernel.py:382)|Vin、Solar、1|

预测函数签名通常 `(coeffs,vza,sza,raa)`，输出逐角模拟量。`model_VinSolar` [927](C:/work/ls4t/base/kernel.py:927)、`model_VinLiSparse` [936](C:/work/ls4t/base/kernel.py:936)、`model_LSFLiDense` [945](C:/work/ls4t/base/kernel.py:945)、`model_LSFLiSparse` [964](C:/work/ls4t/base/kernel.py:964)、`model_RossThickLiSparse` [1001](C:/work/ls4t/base/kernel.py:1001)、`model_RossThickLiDense` [1010](C:/work/ls4t/base/kernel.py:1010) 均按对应三核 `aK1+bK2+c`。例外：[`model_VinLiDense`](C:/work/ls4t/base/kernel.py:918) 取 `c=coeffs[3]`，跳过下标 2，三元素输入会越界。

[`model_LSFLiDenseRossThick`](C:/work/ls4t/base/kernel.py:954) 是 `aLSF+bLiDense+c+dRossThick`，系数顺序与四核 tuple 不直接一致。[`model_LSFR`](C:/work/ls4t/base/kernel.py:973)、[`model_RossThickR`](C:/work/ls4t/base/kernel.py:987)、[`model_VinR`](C:/work/ls4t/base/kernel.py:1019) 为 `aKvol+b exp(-k RLf)+c`，coeffs=`[a,b,c,k]`，各自 Kvol 为 LSF/RossThick/Vin。[`model_Vin(x,vza,coeffa)`](C:/work/ls4t/base/kernel.py:910) 则直接 `x·(1+coeffa·Vin)`，x 是参考量，非参数数组。

[`model_RPV(coeffs,sza,vza,raa)`](C:/work/ls4t/base/kernel.py:1033) 与 [`cost_RPV(x,obs,sza,vza,raa)`](C:/work/ls4t/base/kernel.py:838) 用 `[obs0,k,phi]` 构造 `obs0·M·F·R`：`M=cos(v)^(k-1) cos(s)^(k-1)/(cos(v)+cos(s))^(1-k)`；`F=(1-phi²)/(1+phi²-2phi cos(π-g))`；`R=1+(1-obs0)/(1+G)`。**实际** `g=acos(cosv coss+sin(raa) sins cosraa)`、`G=tan²v+tan²s-2tanv tans`，前者使用 sinraa 而非 sinv，后者没有 cosraa；这是按现有代码记录，不能默认等于标准 RPV。cost 返回 SSE，且还把负 raa 加 360；model 不做这一负角处理。

### 6.3 核优化包装器与所有目标函数

[`fitting_kernel_R_min(fun,y,kvol,fhs,x0,bnds,method='Powell')`](C:/work/ls4t/base/kernel.py:872) 以 args=`(y,kvol,fhs)` 调 minimize；[`fitting_kernel_RL_min(fun,y,kvol,fhs,fn,x0,bnds,method='Powell')`](C:/work/ls4t/base/kernel.py:891) 多传 fn。两者 bounds/x0 全由调用者决定，不提供默认物理上下界，无缺测屏蔽、权重、约束接口或 success 检查，只返回 res.x。

下面逐函数给出实际优化参数和前向/残差表达式。Python 表达式保持源运算和常数，`np` 表示 NumPy；输入数组须可广播，输出目标是标量。函数名 `dif/ab/k/EB` 不能替代公式定义；没有自行校验输入或限制参数。`fhs/f1/f2/fn` 是已准备的角度距离，`kvol/phi/lsf/ref/rad` 均来自调用者，`rad` 这个参数名不保证物理辐射单位。

#### `cost_kernel_VolR(x, y, kvol, fhs)`

[源码](C:/work/ls4t/base/kernel.py:397)；下列 x 下标映射就是被估计的系数，非 x 赋值或形参是固定输入。

```python
a = x[0]
b = x[1]
c = x[2]
k = x[3]
kR = np.exp(-k * fhs)
mea = y
mod = a * kvol + b * kR + c
res = mod - mea
return np.sum(res * res)
```

#### `cost_kernel_VolRB(x, y, kvol, fhs, fn)`

[源码](C:/work/ls4t/base/kernel.py:409)；下列 x 下标映射就是被估计的系数，非 x 赋值或形参是固定输入。

```python
a = x[0]
b = x[1]
c = x[2]
k = x[3]
kR = np.exp(-k * fhs) - np.exp(-k * fn)
mea = y
mod = a * kvol + b * kR + c
res = mod - mea
return np.sum(res * res)
```

#### `cost_kernel_VolRL(x, y, kvol, fhs, fn)`

[源码](C:/work/ls4t/base/kernel.py:421)；下列 x 下标映射就是被估计的系数，非 x 赋值或形参是固定输入。

```python
a = x[0]
b = x[1]
c = x[2]
k = x[3]
kRL = (np.exp(-k * fhs) - np.exp(-k * fn)) / (1.0001 - np.exp(-k * fn))
mea = y
mod = a * kvol + b * kRL + c
res = mod - mea
return np.sum(res * res)
```

#### `cost_kernel_RL(x, y, fhs, fn)`

[源码](C:/work/ls4t/base/kernel.py:433)；下列 x 下标映射就是被估计的系数，非 x 赋值或形参是固定输入。

```python
b = x[0]
c = x[1]
k = x[2]
kRL = (np.exp(-k * fhs) - np.exp(-k * fn)) / (1.0001 - np.exp(-k * fn))
mea = y
mod = b * kRL + c
res = mod - mea
return np.sum(res * res)
```

#### `cost_kernel_RL_dif(x, y, fhs, fn)`

[源码](C:/work/ls4t/base/kernel.py:444)；下列 x 下标映射就是被估计的系数，非 x 赋值或形参是固定输入。

```python
b = x[0]
k = x[1]
kRL = (np.exp(-k * fhs) - np.exp(-k * fn)) / (1.0001 - np.exp(-k * fn))
mea = y
mod = b * kRL
res = mod - mea
return np.sum(res * res)
```

#### `cost_kernel_VolRL_ab(x, k, y, kvol, fhs, fn)`

[源码](C:/work/ls4t/base/kernel.py:454)；下列 x 下标映射就是被估计的系数，非 x 赋值或形参是固定输入。

```python
a = x[0]
b = x[1]
c = x[2]
kRL = (np.exp(-k * fhs) - np.exp(-k * fn)) / (1.0001 - np.exp(-k * fn))
mea = y
mod = a * kvol + b * kRL + c
res = mod - mea
return np.sum(res * res)
```

#### `cost_kernel_VolR_ab(x, k, y, kvol, fhs, fn)`

[源码](C:/work/ls4t/base/kernel.py:465)；下列 x 下标映射就是被估计的系数，非 x 赋值或形参是固定输入。

```python
a = x[0]
b = x[1]
c = x[2]
kRL = np.exp(-k * fhs)
mea = y
mod = a * kvol + b * kRL + c
res = mod - mea
return np.sum(res * res)
```

#### `cost_kernel_VolR_ab_k(x, a, b, c, y, kvol, fhs, fn)`

[源码](C:/work/ls4t/base/kernel.py:476)；下列 x 下标映射就是被估计的系数，非 x 赋值或形参是固定输入。

```python
k = x[0]
kRL = np.exp(-k * fhs)
mea = y
mod = a * kvol + b * kRL + c
res = mod - mea
return np.sum(res * res)
```

#### `cost_kernel_VolRL_ab_k(x, a, b, c, y, kvol, fhs, fn)`

[源码](C:/work/ls4t/base/kernel.py:486)；下列 x 下标映射就是被估计的系数，非 x 赋值或形参是固定输入。

```python
k = x[0]
kRL = (np.exp(-k * fhs) - np.exp(-k * fn)) / (1.0001 - np.exp(-k * fn))
mea = y
mod = a * kvol + b * kRL + c
res = mod - mea
return np.sum(res * res)
```

#### `cost_kernel_VolRLEB(x, y, kvol, fhs, fn, ref, refplus)`

[源码](C:/work/ls4t/base/kernel.py:496)；下列 x 下标映射就是被估计的系数，非 x 赋值或形参是固定输入。

```python
a = x[0]
b = x[1]
c = x[2]
k = x[3]
kRL = (np.exp(-k * fhs) - np.exp(-k * fn)) / (1.0001 - np.exp(-k * fn))
mea = y
mod = a * ref * kvol + b * refplus * kRL + c
res = mod - mea
return np.sum(res * res)
```

#### `cost_kernel_VolRLEB_dif(x, y, kvol, fhs, fn, ref, refplus)`

[源码](C:/work/ls4t/base/kernel.py:508)；下列 x 下标映射就是被估计的系数，非 x 赋值或形参是固定输入。

```python
a = x[0]
b = x[1]
k = x[2]
kRL = (np.exp(-k * fhs) - np.exp(-k * fn)) / (1.0001 - np.exp(-k * fn))
mea = y
mod = a * ref * kvol + b * refplus * kRL
res = mod - mea
return np.sum(res * res)
```

#### `cost_kernel_RLEB_dif(x, y, fhs, fn, ref, refplus)`

[源码](C:/work/ls4t/base/kernel.py:519)；下列 x 下标映射就是被估计的系数，非 x 赋值或形参是固定输入。

```python
b = x[0]
k = x[1]
kRL = (np.exp(-k * fhs) - np.exp(-k * fn)) / (1.0001 - np.exp(-k * fn))
mea = y
mod = b * refplus * kRL
res = mod - mea
return np.sum(res * res)
```

#### `cost_kernel_VolRLEB_dif_ab(x, k, y, kvol, fhs, fn, ref, refplus)`

[源码](C:/work/ls4t/base/kernel.py:529)；下列 x 下标映射就是被估计的系数，非 x 赋值或形参是固定输入。

```python
a = x[0]
b = x[1]
kRL = (np.exp(-k * fhs) - np.exp(-k * fn)) / (1.0001 - np.exp(-k * fn))
mea = y
mod = a * ref * kvol + b * refplus * kRL
res = mod - mea
return np.sum(res * res)
```

#### `cost_kernel_VolRLEB_dif_ab_k(x, a, b, y, kvol, fhs, fn, ref, refplus)`

[源码](C:/work/ls4t/base/kernel.py:539)；下列 x 下标映射就是被估计的系数，非 x 赋值或形参是固定输入。

```python
k = x[0]
kRL = (np.exp(-k * fhs) - np.exp(-k * fn)) / (1.0001 - np.exp(-k * fn))
mea = y
mod = a * ref * kvol + b * refplus * kRL
res = mod - mea
return np.sum(res * res)
```

#### `cost_kernel_VolREB_dif(x, y, kvol, fhs, fn, ref, refplus)`

[源码](C:/work/ls4t/base/kernel.py:548)；下列 x 下标映射就是被估计的系数，非 x 赋值或形参是固定输入。

```python
a = x[0]
b = x[1]
k = x[2]
kRL = np.exp(-k * fhs)
mea = y
mod = a * ref * kvol + b * refplus * kRL
res = mod - mea
return np.sum(res * res)
```

#### `cost_kernel_VolR_dif(x, y, kvol, fhs, fn)`

[源码](C:/work/ls4t/base/kernel.py:559)；下列 x 下标映射就是被估计的系数，非 x 赋值或形参是固定输入。

```python
a = x[0]
b = x[1]
k = x[2]
kRL = np.exp(-k * fhs) - np.exp(-k * fn)
mea = y
mod = a * kvol + b * kRL
res = mod - mea
return np.sum(res * res)
```

#### `cost_kernel_VolREBB_dif(x, y, kvol, fhs, fn, ref, refplus)`

[源码](C:/work/ls4t/base/kernel.py:570)；下列 x 下标映射就是被估计的系数，非 x 赋值或形参是固定输入。

```python
a = x[0]
b = x[1]
k = x[2]
kRL = np.exp(-k * fhs) - np.exp(-k * fn)
mea = y
mod = a * ref * kvol + b * refplus * kRL
res = mod - mea
return np.sum(res * res)
```

#### `cost_kernel_VolREB_dif_ab(x, k, y, kvol, fhs, fn, ref, refplus)`

[源码](C:/work/ls4t/base/kernel.py:581)；下列 x 下标映射就是被估计的系数，非 x 赋值或形参是固定输入。

```python
a = x[0]
b = x[1]
kRL = np.exp(-k * fhs)
mea = y
mod = a * ref * kvol + b * refplus * kRL
res = mod - mea
return np.sum(res * res)
```

#### `cost_kernel_VolREB_dif_ab_k(x, a, b, y, kvol, fhs, fn, ref, refplus)`

[源码](C:/work/ls4t/base/kernel.py:591)；下列 x 下标映射就是被估计的系数，非 x 赋值或形参是固定输入。

```python
k = x[0]
kRL = np.exp(-k * fhs)
mea = y
mod = a * ref * kvol + b * refplus * kRL
res = mod - mea
return np.sum(res * res)
```

#### `cost_kernel_VolRLE_dif(x, lst1, lst2, phi1, phi2, f1, f2, fn, rad)`

[源码](C:/work/ls4t/base/kernel.py:600)；下列 x 下标映射就是被估计的系数，非 x 赋值或形参是固定输入。

```python
a = x[0]
b = x[1]
k = x[2]
mea = lst1 - lst2
mod = a * (phi1 * lst2 - phi2 * lst1) + b * rad * (np.exp(-k * f1) - np.exp(-k * f2)) / (1.0001 - np.exp(-k * fn))
res = mod - mea
return np.sum(res * res)
```

#### `cost_kernel_VolVRLE_dif(x, lst1, lst2, phi1, phi2, f1, f2, fn, ref, rad)`

[源码](C:/work/ls4t/base/kernel.py:611)；下列 x 下标映射就是被估计的系数，非 x 赋值或形参是固定输入。

```python
a = x[0]
b = x[1]
k = x[2]
mea = lst1 - lst2
mod = a * ref * (phi1 * lst2 - phi2 * lst1) + b * rad * (np.exp(-k * f1) - np.exp(-k * f2)) / (1.0001 - np.exp(-k * fn))
res = mod - mea
return np.sum(res * res)
```

#### `cost_kernel_VolRLELSF_dif(x, lst1, lst2, phi1, phi2, f1, f2, fn, lsf1, lsf2, ref, rad)`

[源码](C:/work/ls4t/base/kernel.py:622)；下列 x 下标映射就是被估计的系数，非 x 赋值或形参是固定输入。

```python
a = x[0]
b = x[1]
c = x[2]
k = x[3]
mea = lst1 - lst2
mod = a * (phi1 * lst2 - phi2 * lst1) + b * rad * (np.exp(-k * f1) - np.exp(-k * f2)) / (1.00001 - np.exp(-k * fn)) + c * ref * (lsf1 * lst2 - lsf2 * lst1)
res = mod - mea
return np.sum(res * res)
```

#### `cost_kernel_VolRE_dif(x, lst1, lst2, phi1, phi2, f1, f2, fn, rad)`

[源码](C:/work/ls4t/base/kernel.py:634)；下列 x 下标映射就是被估计的系数，非 x 赋值或形参是固定输入。

```python
a = x[0]
b = x[1]
k = x[2]
mea = lst1 - lst2
mod = a * (phi1 * lst2 - phi2 * lst1) + b * rad * (np.exp(-k * f1) - np.exp(-k * f2))
res = mod - mea
return np.sum(res * res)
```

#### `cost_kernel_VolRE_dif_ab(x, lst1, lst2, phi1, phi2, f1, f2, fn, rad)`

[源码](C:/work/ls4t/base/kernel.py:645)；下列 x 下标映射就是被估计的系数，非 x 赋值或形参是固定输入。

```python
a = x[0]
b = x[1]
k = 1.0
mea = lst1 - lst2
mod = a * (phi1 * lst2 - phi2 * lst1) + b * rad * (np.exp(-k * f1) - np.exp(-k * f2))
res = mod - mea
return np.sum(res * res)
```

#### `cost_kernel_VolRE_dif_ab_k(x, k, lst1, lst2, phi1, phi2, f1, f2, fn, rad)`

[源码](C:/work/ls4t/base/kernel.py:656)；下列 x 下标映射就是被估计的系数，非 x 赋值或形参是固定输入。

```python
a = x[0]
b = x[1]
mea = lst1 - lst2
mod = a * (phi1 * lst2 - phi2 * lst1) + b * rad * (np.exp(-k * f1) - np.exp(-k * f2))
res = mod - mea
return np.sum(res * res)
```

#### `cost_kernel_VolRLE_dif_ab(x, lst1, lst2, phi1, phi2, f1, f2, fn, rad)`

[源码](C:/work/ls4t/base/kernel.py:666)；下列 x 下标映射就是被估计的系数，非 x 赋值或形参是固定输入。

```python
a = x[0]
b = x[1]
k = 1.0
mea = lst1 - lst2
mod = a * (phi1 * lst2 - phi2 * lst1) + b * rad * (np.exp(-k * f1) - np.exp(-k * f2)) / (1.00001 - np.exp(-k * fn))
res = mod - mea
return np.sum(res * res)
```

#### `cost_kernel_VolRLE_dif_ab_k(x, k, lst1, lst2, phi1, phi2, f1, f2, fn, rad)`

[源码](C:/work/ls4t/base/kernel.py:677)；下列 x 下标映射就是被估计的系数，非 x 赋值或形参是固定输入。

```python
a = x[0]
b = x[1]
mea = lst1 - lst2
mod = a * (phi1 * lst2 - phi2 * lst1) + b * rad * (np.exp(-k * f1) - np.exp(-k * f2)) / (1.00001 - np.exp(-k * fn))
res = mod - mea
return np.sum(res * res)
```

#### `cost_kernel_VolRE_dif_k(x, a, b, lst1, lst2, phi1, phi2, f1, f2, rad)`

[源码](C:/work/ls4t/base/kernel.py:688)；下列 x 下标映射就是被估计的系数，非 x 赋值或形参是固定输入。

```python
k = x[0]
mea = lst1 - lst2
mod = a * (phi1 * lst2 - phi2 * lst1) + b * rad * (np.exp(-k * f1) - np.exp(-k * f2))
res = mod - mea
return np.sum(res * res)
```

#### `cost_kernel_RossR_dif_k(x, a, b, lst1, lst2, kvol1, kvol2, f1, f2, da, rad)`

[源码](C:/work/ls4t/base/kernel.py:697)；下列 x 下标映射就是被估计的系数，非 x 赋值或形参是固定输入。

```python
k = x[0]
mea = lst2 - lst1
mod = a * da * (kvol2 - kvol1) + b * rad * (np.exp(-k * f2) - np.exp(-k * f1))
res = mod - mea
return np.sum(res * res)
```

#### `cost_kernel_RossRL_dif_k(x, a, b, lst1, lst2, kvol1, kvol2, f1, f2, fn, da, rad)`

[源码](C:/work/ls4t/base/kernel.py:706)；下列 x 下标映射就是被估计的系数，非 x 赋值或形参是固定输入。

```python
k = x[0]
mea = lst2 - lst1
mod = a * da * (kvol2 - kvol1) + b * rad * (np.exp(-k * f2) - np.exp(-k * f1)) / (1.0001 - np.exp(-k * fn))
res = mod - mea
return np.sum(res * res)
```

#### `cost_kernel_VolRLE_dif_k(x, a, b, lst1, lst2, phi1, phi2, f1, f2, fn, rad)`

[源码](C:/work/ls4t/base/kernel.py:715)；下列 x 下标映射就是被估计的系数，非 x 赋值或形参是固定输入。

```python
k = x[0]
mea = lst1 - lst2
mod = a * (phi1 * lst2 - phi2 * lst1) + b * rad * (np.exp(-k * f1) - np.exp(-k * f2)) / (1.00001 - np.exp(-k * fn))
res = mod - mea
return np.sum(res * res)
```

#### `cost_kernel_VolVRE_dif(x, lst1, lst2, phi1, phi2, f1, f2, ref, rad)`

[源码](C:/work/ls4t/base/kernel.py:724)；下列 x 下标映射就是被估计的系数，非 x 赋值或形参是固定输入。

```python
a = x[0]
b = x[1]
k = x[2]
mea = lst1 - lst2
mod = a * ref * (phi1 * lst2 - phi2 * lst1) + b * rad * (np.exp(-k * f1) - np.exp(-k * f2))
res = mod - mea
return np.sum(res * res)
```

#### `cost_kernel_Vin(x, lst1, lst2, phi1, phi2)`

[源码](C:/work/ls4t/base/kernel.py:735)；下列 x 下标映射就是被估计的系数，非 x 赋值或形参是固定输入。

```python
a = x[0]
mea = lst1 - lst2
mod = a * (phi1 * lst2 - phi2 * lst1)
res = mod - mea
return np.sum(res * res)
```

#### `cost_kernel_VinV(x, lst1, lst2, phi1, phi2, ref)`

[源码](C:/work/ls4t/base/kernel.py:743)；下列 x 下标映射就是被估计的系数，非 x 赋值或形参是固定输入。

```python
a = x[0]
mea = lst1 - lst2
mod = a * ref * (phi1 * lst2 - phi2 * lst1)
res = mod - mea
return np.sum(res * res)
```

#### `cost_kernel_RLE_dif(x, a, lst1, lst2, phi1, phi2, f1, f2, fn, rad)`

[源码](C:/work/ls4t/base/kernel.py:751)；下列 x 下标映射就是被估计的系数，非 x 赋值或形参是固定输入。

```python
b = x[0]
k = x[1]
mea = lst1 - lst2
mod = a * (phi1 * lst2 - phi2 * lst1) + b * rad * (np.exp(-k * f1) - np.exp(-k * f2)) / (1.00001 - np.exp(-k * fn))
res = mod - mea
return np.sum(res * res)
```

#### `cost_kernel_RLEB2_dif(x, a, b, lst1, lst2, phi1, phi2, f1, f2, fn, rad)`

[源码](C:/work/ls4t/base/kernel.py:761)；下列 x 下标映射就是被估计的系数，非 x 赋值或形参是固定输入。

```python
k = x[0]
mea = lst1 - lst2
mod = a * (phi1 * lst2 - phi2 * lst1) + b * rad * (np.exp(-k * f1) - np.exp(-k * f2)) / (1.00001 - np.exp(-k * fn))
res = mod - mea
return np.sum(res * res)
```

#### `cost_kernel_RE_dif(x, a, lst1, lst2, phi1, phi2, f1, f2, fn, rad)`

[源码](C:/work/ls4t/base/kernel.py:771)；下列 x 下标映射就是被估计的系数，非 x 赋值或形参是固定输入。

```python
b = x[0]
k = x[1]
mea = lst1 - lst2
mod = a * (phi1 * lst2 - phi2 * lst1) + b * rad * (np.exp(-k * f1) - np.exp(-k * f2))
res = mod - mea
return np.sum(np.abs(res))
```

#### `cost_DTC(x, mea, t)`

[源码](C:/work/ls4t/base/kernel.py:781)；下列 x 下标映射就是被估计的系数，非 x 赋值或形参是固定输入。

```python
T0 = x[0]
Ta = x[1]
tm = x[2]
tsr = x[3]
omg = 4 / 3.0 * (tm - tsr)
mod = T0 + Ta * np.cos(np.pi / omg * (t - tm))
res = mod - mea
return np.sum(res * res)
```

#### `cost_KDTC_RVT(x, mea, pst, vi, bf, tsr, tm, k=1.0)`

[源码](C:/work/ls4t/base/kernel.py:799)；下列 x 下标映射就是被估计的系数，非 x 赋值或形参是固定输入。

```python
T01 = x[0]
Ta1 = x[1]
T02 = x[2]
Ta2 = x[3]
omg = 4 / 3.0 * (tm - tsr)
fbf = T02 + Ta2 * np.cos(np.pi / omg * (pst - tm))
fvi = T01 + Ta1 * np.cos(np.pi / omg * (pst - tm))
mod = fvi * vi + fbf * bf
res = mod - mea + fbf * fbf * 0.0001 + fvi * fvi * 0.0001
return np.sum(res * res)
```

#### `cost_KDTC_DVT(x, mea, pst, vi, bf)`

[源码](C:/work/ls4t/base/kernel.py:816)；下列 x 下标映射就是被估计的系数，非 x 赋值或形参是固定输入。

```python
T01 = x[0]
Ta1 = x[1]
T02 = x[2]
Ta2 = x[3]
T03 = x[4]
Ta3 = x[5]
tm = x[6]
tsr = x[7]
omg = 4 / 3.0 * (tm - tsr)
fbf = T02 + Ta2 * np.cos(np.pi / omg * (pst - tm))
fvi = T01 + Ta1 * np.cos(np.pi / omg * (pst - tm))
fiso = T03 + Ta3 * np.cos(np.pi / omg * (pst - tm))
mod = fvi * vi + fbf * bf + fiso
res = mod - mea + fbf * fbf * 0.0001 + fvi * fvi * 0.0001
return np.sum(res * res)
```

#### `cost_DTCRL(x, y, t, fhs, fn)`

[源码](C:/work/ls4t/base/kernel.py:1062)；下列 x 下标映射就是被估计的系数，非 x 赋值或形参是固定输入。

```python
T0 = x[0]
Ta = x[1]
tm = x[2]
tsr = x[3]
a = x[4]
k = x[5]
omg = 4 / 3.0 * (tm - tsr)
kRL = (np.exp(-k * fhs) - np.exp(-k * fn)) / (1.0001 - np.exp(-k * fn))
mod = T0 + Ta * np.cos(np.pi / omg * (t - tm)) + a * kRL
res = mod - y
return np.sum(res * res)
```

#### `cost_DTCLSFRL(x, y, t, kLSF, fhs, fn)`

[源码](C:/work/ls4t/base/kernel.py:1107)；下列 x 下标映射就是被估计的系数，非 x 赋值或形参是固定输入。

```python
T0 = x[0]
Ta = x[1]
tm = x[2]
tsr = x[3]
b = x[4]
a = x[5]
k = x[6]
omg = 4 / 3.0 * (tm - tsr)
kRL = (np.exp(-k * fhs) - np.exp(-k * fn)) / (1.0001 - np.exp(-k * fn))
mod = T0 + Ta * np.cos(np.pi / omg * (t - tm)) + b * kLSF + a * kRL
res = mod - y
return np.sum(res * res) + 1e-08 * np.sum(x * x)
```

### 6.4 DTC 联合预测和目标的差异

- [`model_DTC(x,t)`](C:/work/ls4t/base/kernel.py:1095)：x=`[T0,Ta,tm,tsr]`，`ω=4/3(tm-tsr)`，`T=T0+Ta cos[π(t-tm)/ω]`。返回与 t 广播的温度；`cost_DTC` 是同一预测相对 mea 的 SSE。t/tm/tsr 必须同一时间尺度（调用者通常小时），但函数不验证、也不内置夜间指数冷却段、日出/日落分段或 tm>tsr 限制。ω=0 会除零。
- [`model_DTCRL(x,t,fhs,fn)`](C:/work/ls4t/base/kernel.py:1079)：x=`[T0,Ta,tm,tsr,a,k]`，DTC 加 `a·[exp(-k fhs)-exp(-k fn)]/[1.0001-exp(-k fn)]`；`cost_DTCRL` 采用完全相同预测的 SSE。
- [`model_DTCLSFRL(x,t,kLSF,fhs,fn)`](C:/work/ls4t/base/kernel.py:1123)：x=`[T0,Ta,tm,tsr,b,a,k]`，DTC 再加 b·kLSF 和 a·RL；`cost_DTCLSFRL` 除 SSE 外还有 `1e-8 Σx²`，连温度基线/时间/核系数都一起惩罚，单位尺度未标准化。不能将其称为与 DTCRL 完全一致的无正则目标。
- `cost_KDTC_RVT` 固定外部 tsr/tm，对两个时间余弦分量分别估计基线/幅度，以 vi/bf 线性混合；k 形参未使用。`cost_KDTC_DVT` 多一项 isotropic 时间余弦并把 tm/tsr 加入 x。二者都把 `.0001 fbf²+.0001 fvi²` **加进每个残差后再平方**，所以不是通常的 `SSE+λ||coeff||²` ridge，也不等同于普通 Tikhonov。
- `cost_kernel_RE_dif` 是 `Σabs(res)`（L1），不是本节多数函数的 SSE。`*_VolRLELSF_dif`、`*_VolRLE_dif_ab`/`*_ab_k`/`*_dif_k` 及 `RLE_dif` 家族部分分母使用 1.00001，另一些用 1.0001；这两个常数在弱太阳距离或 k≈0 时不可忽略。
- `*_dif_ab` 不统一表示“固定外部 k”：`cost_kernel_VolRE_dif_ab`/`VolRLE_dif_ab` 内置 k=1，而 `VolRLEB_dif_ab`/`VolREB_dif_ab`/`VolRL_ab` 接受外部 k；`VolRE_dif_ab_k` 虽以 `_k` 结尾，实际上估计 a,b、传入 k。上面的逐函数表达式保留了这些区别。
- `cost_kernel_RossR_dif_k` 与 `RossRL_dif_k` 观测差为 `lst2-lst1`，多数其它差分核是 `lst1-lst2`；核差同步反向，不能仅复制变量名混接。

## 7. 测试引用、证据等级与科学限制

以下是**已读到的测试定义及断言**，不是覆盖率报告。本轮全库测试结果见总报告的验证记录；此外执行了 AST 函数名称出现检查与文档源码链接存在/行号范围检查，属于清单完整性验证。未重新运行区域生产反演或独立地面精度评估。

|证据出处|能说明什么|不能说明什么|
|---|---|---|
|[test_retrieval.py:39](C:/work/ls4t/tests/test_retrieval.py:39) `test_two_component_radiance_retrieval`|用同一个现代 Planck 生成合成两组分 300/310 K，检验反演绝对温度容差 1e-9、残差<1e-10、QA=0|不验证 LAI、真实发射率、亚像元温度或地面站准确性|
|[test_retrieval.py:50](C:/work/ls4t/tests/test_retrieval.py:50) `test_component_retrieval_flags_singular_matrix`|全 1 矩阵被标 ill-conditioned，温度 NaN|不覆盖任意近奇异、各 σ、温区、ridge 超参数行为|
|[test_retrieval.py:57](C:/work/ls4t/tests/test_retrieval.py:57) `test_window_retrieval_supports_more_components_than_angles`|3×3、两角三组分、空间变化权重的合成局部常数可恢复|不证明异质温度窗口仍无偏，也不验证所有边缘|
|[SLSTR 迁移测试:74](C:/work/ls4t/tests/test_slstr_case_dependencies.py:74)、[80](C:/work/ls4t/tests/test_slstr_case_dependencies.py:80)、[87](C:/work/ls4t/tests/test_slstr_case_dependencies.py:87)、[94](C:/work/ls4t/tests/test_slstr_case_dependencies.py:94)|固定 gap/hotspot/radiance/Hom effective emissivity 旧数值回归|旧数字一致不代表物理参数/单位正确；其中 radiance 测试把 `deg2rad(30)` 传给 degree 接口，检验的是这个实际数值行为|
|[旧窗口 golden 测试:136](C:/work/ls4t/tests/test_slstr_case_dependencies.py:136)|9×9 随机输入、5×5 SLSQP 的 shape/中心历史值，容差 .01 K；源码注释提 SciPy 差异|没有 assertion `optimizer.success`；测试 b 取约 300 的随机数，与通常 10 μm 辐射量级不同，不能作为物理真实性验证|
|[AATSR 核迁移测试:96](C:/work/ls4t/tests/test_aatsr_case_dependencies.py:96)|LSF/RLf 历史数值可对照|测试同样先 deg2rad 再调用内部 deg2rad，因而不是 30°/60° 物理角度验证|
|[MSG 真数据样例:96](C:/work/ls4t/tests/test_msg_evo_sample.py:96)|744×10×10×2 输出形状、共同 valid mask、250–350 K、写回数据和地理变换|是真实输入的软件/产品验证，不是独立组分测温准确度|
|[MSG 中心独立计算:120](C:/work/ls4t/tests/test_msg_evo_sample.py:120)|在真实输入选一个有效中心，另行 NumPy lstsq 与基本 h/c/k 常数逆 Planck 比较 1e-6 K|“independent”指独立实现计算路径，不是独立观测真值；仍使用相同 y/A、相同邻域模型|
|[MSG/AATSR 对照测试:23](C:/work/ls4t/tests/test_msg_aatsr_comparison.py:23)、[35](C:/work/ls4t/tests/test_msg_aatsr_comparison.py:35)、[46](C:/work/ls4t/tests/test_msg_aatsr_comparison.py:46)、[58](C:/work/ls4t/tests/test_msg_aatsr_comparison.py:58)、[70](C:/work/ls4t/tests/test_msg_aatsr_comparison.py:70)|OLS/ridge 与基核相符；已知辐射二次面恢复；温差约束消融；同温三组分保持；Gaussian MAP 更新恒等式|不能推广为所有生产脚本已测试；尤其对照 quadratic 使用自己的 NumPy 实现，不能掩盖 base 旧 quadratic 的 scipy 参数问题|

可辨识性是本层的共同限制：观测数足够不等于矩阵满秩；即使数值满秩，LAI/ε/角度误差和局部同温假设仍会主导结果。先验使欠定问题有唯一数值解，并不使三组分拥有独立观测验证。较小的辐射残差也不能证明各组分温度唯一正确。

地面站的光照土壤、阴影土壤、叶温、混合土壤和像元 LST 是不同量；必须先匹配空间支持、观测时刻、视场/光照定义再谈准确度。本文不报告新 RMSE/Bias，不把历史迁移 golden 值、理论同温恢复、MAP 恒等式或真实数据内部重算称为独立地面精度。
