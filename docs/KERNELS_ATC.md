# 核组合与 ATC 年温度周期

2026-10-24 新增实现。旧 `base/kernel.py` 数值公式和旧案例接口保持原状；新入口位于 `base/normalization/kernels.py` 和 `annual.py`。此次没有重跑卫星生产数据或宣称新增地面精度。

## 设计与接口

采用“核注册表＋有序组合＋独立拟合器”，而非复制每个组合的cost函数。旧函数继续供历史案例使用；新适配器调用它们，对输入做广播、相对方位角周期化和防原地修改处理。源码中已有RPV整体非线性模型继续留在旧库，不强行当作一个线性可加核。

- `available_kernels()`：核名称、物理类别和默认形状参数，返回独立字典。
- `KernelTerm(name, parameters)`：单核及固定参数，参数只读。
- `KernelModel(terms)`：自定义有序组合；不暗中补截距，需显式包含`isotropic`。
- `kernel_model(preset)`：创建预设组合。
- `model.design_matrix(vza,sza,raa)`：广播空间形状，最后一维为核。角度为度，温度为K。
- `model.to_dict()` / `KernelModel.from_dict()`：JSON配置往返，保存核顺序及全部形状参数。
- `fit_kernel_model(...)`：训练一组同地点、同状态的角度样本，返回`KernelFit`。
- `fit.predict(...)` / `fit.normalize(...)`：前向预测与保留观测残差的参考几何归一化。
- `fit_annual_cycle(...)`：训练一个像元/站点的可比温度时间序列，返回`ATCFit`。

## 可组合核

| 类别 | 注册名 | 形状参数 |
|---|---|---|
| 各向同性 | `isotropic` | 无，恒1 |
| 几何光学 | `li_dense`, `li_sparse` | h=2、r=1、b=1 |
| 体散射 | `ross_thick`, `ross_thin` | 无 |
| 上下层差异及相关形式 | `lsf`, `lsf_analytical` | 无 |
| LSF变体 | `tlsf`, `vlsf` | w=.10或.15；同公式不同默认值 |
| Hapke相关形式 | `thapke` | w=.10、K=1 |
| 发射率/太阳方向项 | `vin`, `solar` | 无 |
| 方向距离 | `rl_distance` | 无；不是完整热点核 |
| 指数热点 | `r` | k=1，`exp(-k*f)` |
| 参考天底归一化热点 | `rl` | k=1，`(exp(-k*f)-exp(-k*fn))/(1.0001-exp(-k*fn))` |

`f`沿用旧`kernel_RLf`，`fn=tan(sza)`。`w`要求[0,1)，h/r/b/K/k要求>0。几何统一限于`abs(vza)<90`、`0<=sza<90`，无效样本返回NaN；该接口是日间角度模型，不能直接处理夜间太阳角。所有核参数固定时，各系数均线性可求。线性组合可以含多个物理类别，但不应无依据堆叠高度相关的核。

预设：`lsf_li_dense`、`lsf_li_sparse`、`lsf_li_dense_ross_thick`、`ross_thick_li_sparse`、`ross_thick_li_dense`、`vin_li_dense`、`vin_li_sparse`、`vin_solar`、`lsf_r`、`ross_thick_r`、`vin_r`、`lsf_rl`。预设均将`isotropic`放第一位；不要直接拷贝旧组合的系数数组，因为旧函数返回顺序不统一。

```python
from base.normalization import KernelModel, KernelTerm, kernel_model, fit_kernel_model

# 三种物理作用：各向同性 + 上下层差异 + 几何光学 + 体散射
model = kernel_model("lsf_li_dense_ross_thick")
fit = fit_kernel_model(model, temperature_k, vza, sza, raa, weights=weights)
nadir_k = fit.normalize(temperature_k, vza, sza, raa)

# 自定义组合，线性拟合时k固定
model = KernelModel(("isotropic", "lsf", KernelTerm("rl", {"k": 0.8})))

# 联合估计热点形状参数，线性系数在每个优化步中直接解出
fit = fit_kernel_model(model, temperature_k, vza, sza, raa,
                       solver="minimize", parameter_bounds={"rl.k": (0.1, 3.0)},
                       method="Powell")
```

### 求解和诊断

固定形状采用加权最小二乘：`sum(w*(T-Xb)^2)`。权重是统计权重，若输入误差σ则调用者使用`1/σ²`。归一化为`Tobs+Tmodel(ref)-Tmodel(obs)`；默认参考为同一太阳角下的天底，不默认改变太阳照明。

`solver="minimize"`采用变量投影：外层只优化指定形状参数，内层WLS解析求系数。默认Powell，支持Nelder-Mead、L-BFGS-B、SLSQP；每个待估参数必须给合法有限边界，初值来自`KernelTerm`并须位于边界内。Li核仅依赖b/r和h/b，因此不能同时估计h/r/b三个绝对尺寸，必须固定至少一个。不存在暗中自动调参。

训练先过滤QA、非有限/非正权重、温区外和无效几何；要求残差自由度，并检查缩放设计矩阵秩及条件数。非线性优化检查success，结束时检查形状参数的局部灵敏度及联合Jacobian秩。失败抛异常，不将未收敛系数包装为成功产品。局部可辨识不等于全局唯一解；非线性拟合不保证全局最优。返回训练加权RMSE、样本数、求解消息、最终模型和系数，不声称提供后验不确定性。

## ATC

采用标准季节谐波形式，以1月1日为相位零点：

```text
T(p) = μ + Σ[j=1..H] {c_j cos(2πjp) + s_j sin(2πjp)}
H=1：三系数标准ATC；H=2：加半年周期的五系数模型。
A_j = hypot(c_j, s_j)
各谐波首个峰值日 = 1 + N * (atan2(s_j,c_j) mod 2π)/(2πj)
```

模型参考：[Bechtel 2015单周期ATC](https://www.mdpi.com/2072-4292/7/3/2850)、[双谐波季节模型示例](https://www.mdpi.com/2073-445X/12/2/309)。这里明确采用1月1日零相位，不能直接把输出相位当成以春分日为基准的文献参数。

```python
from base.normalization import fit_annual_cycle

# dates可用np.datetime64数组或ISO日期字符串；自动识别平年/闰年。
annual = fit_annual_cycle(temperature_k, dates, harmonics=1)
curve_k = annual.predict(target_dates)
normalized_k = annual.normalize(temperature_k, dates, reference="2024-07-15")

# 数字DOY从1开始，必须给对应年长度；默认365。
annual = fit_annual_cycle(temperature_k, doy, year_length=366, harmonics=2)
annual.mean_k
annual.amplitudes_k
annual.peak_days(366)  # 每个谐波自身首个峰；不是组合曲线的最大值日。
```

日期按各自真实公历年长度映射到[0,1)。多年的一次拟合得到共享季节气候态，不自动估计年际趋势；各年的权重不会自动均衡。数字DOY可指定365/366或可广播的长度数组。跨年、时区和当地太阳时应在上游统一；输入时间戳不推断时区。

拟合为WLS，不需要对振幅和相位再做非线性搜索。单/双谐波分别至少需要4/6个有效观测，还须满足秩检查和默认0.5的年内循环覆盖；覆盖率定义为`1-最大相位空缺`。多年的同一短季节不能因样本数多就通过。零振幅谐波的峰值日返回NaN。ATC归一化保留天气异常；预测可用于季节曲线，但不等于恢复真实云下温度或极端天气。

## 案例、比较和原入口关系

`cases/multisource-normalization/fit_models.py`负责不同组合的拟合和留出比较，`models.example.json`配置候选。角度与ATC使用独立样本集。一个领域的候选在共同有效留出掩膜上评分，输出训练加权RMSE、留出未加权RMSE/Bias及样本数；不自动按留出集选择后再宣称独立测试精度。

在已安装`ls4t`或`PYTHONPATH=.`的仓库环境中运行：

```powershell
$env:PYTHONPATH = (Get-Location).Path
python cases/multisource-normalization/fit_models.py --demo --output D:/your-result-location/multisource-normalization/kernels-atc-demo
python cases/multisource-normalization/fit_models.py --input samples.npz --config cases/multisource-normalization/models.example.json --output D:/your-result-location/multisource-normalization/new-comparison
```

输出目录必须不存在，避免覆盖。输入NPZ字段：

| 数据域 | 必需字段 | 可选字段 |
|---|---|---|
| 角度 | `angle_temperature_k`, `vza`, `sza`, `raa`, `angle_train` | `angle_weights`, `angle_quality_flag` |
| ATC | `atc_temperature_k`, `atc_dates_or_doy`, `atc_train` | `atc_weights`, `atc_quality_flag` |

每个领域必需字段是一维同形数组，train为含训练和留出点的布尔数组。日期请存datetime64或Unicode，不使用pickle/object NPZ。配置只含一个领域时，只需对应字段。输出`fit_results.json`记录模型、系数和诊断，`samples_and_predictions.npz`保存输入与预测及比较掩膜。

旧三项经验基函数`normalize_directional`、原栅格CLI及旧DTC仍保持原行为；新核组合由上述新接口/案例显式选择。尚未增加统一逐像元栅格时序拟合器或ATC-DTC联合估计。这个边界避免将站点/样本池的一个系数集误用于整幅异质影像。

## 执行验证（2026-10-24）

- 新增31项测试，覆盖12个旧核数值一致性、广播/不修改输入、自定义配置往返、加权LS、热点参数留出预测、失秩、Li共同缩放不可辨识、未收敛拒绝、单/双谐波、闰年、缺测/QA、季节覆盖、object数值DOY、时区拒绝及案例训练/留出隔离。
- 最终全库：`207 passed, 3 skipped in 16.66s`。跳过为缺少shapely的非洲下载测试、缺少pyproj的北京建筑和LAI测试；不是本次算法失败。
- `base/templates/audit_cases.py`：9个登记案例通过。
- 合成案例曾实际运行完成；临时产物现已清理，以下为当时的运行指标。已知热点宽度k=.8，估计为.785815；角度留出RMSE=.085810 K。ATC双谐波留出RMSE=.134590 K。数据本身由相应模型加噪声生成，这些数字只验证恢复和执行链，不证明其优于其它模型或真实地面精度。
- 审阅提出的Li尺度不可辨识、object数值DOY和简写时区处理问题均补充回归测试后修复。未改变旧核公式。

验证命令：

```powershell
& C:/work/miniconda/Scripts/conda.exe run -n python311 --no-capture-output python -B -m pytest -p no:cacheprovider -o addopts= -q -ra
```
