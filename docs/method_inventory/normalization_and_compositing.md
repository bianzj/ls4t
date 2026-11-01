# 归一化、降尺度、融合、合成与公共空间方法：函数级盘点

盘点对象为 2026-10-24 的 `C:/work/ls4t` 当前工作区，包含尚未提交的新归一化实现。以下公式直接按代码解释，不把函数名或文献方法名当作已经实现的证据。测试通过只能证明被测试路径的行为，不能代替真实精度评估。

## 1. 角度归一化：三项经验核及匹配样本标定

源码：[angle.py](C:/work/ls4t/base/normalization/angle.py)。这是独立于 `base/kernel.py` 中旧核模型的一套明确三参数归一化接口，两者不能按“都是角度核”视作同一个实现。

### `angular_basis(view_zenith_deg, solar_zenith_deg, relative_azimuth_deg)`

[定义](C:/work/ls4t/base/normalization/angle.py:28)。三个输入允许标量或 NumPy 可广播数组，单位均为度。令 `q=sec(vza)-1`，输出最后一维长度为 3 的核：

```text
K = [q, q*cos(raa), q*cos(sza)]
```

视天顶角要求 `0≤vza<90`，太阳天顶角 `0≤sza≤180`；相对方位角只要求有限，按余弦周期使用。非法几何输出 NaN。该函数只形成设计矩阵，不拟合温度，也不是完整 BRDF/热辐射传输模型。天底 `q=0`，因此该模型不能在天底独立表现太阳角或方位角造成的温度差异。

### `normalize_directional(temperature_k, view_zenith_deg, solar_zenith_deg, relative_azimuth_deg, coefficients_k, *, reference_view_zenith_deg=None, reference_solar_zenith_deg=None, reference_relative_azimuth_deg=None)`

[定义](C:/work/ls4t/base/normalization/angle.py:48)。输入为观测 LST（K）、观测几何和三项系数（K），系数末维必须为 3，可每像元不同。参考默认 `(0°,30°,0°)`。

```text
T_reference = T_observed + Σ[(K_reference - K_observed) * coefficient]
```

输出温度数组；观测或结果不在 150–400 K、几何不合法时为 NaN。非法参考几何直接报错。它不生成系数、不计算系数误差、不传播不确定度，也不读取云标志；数组调用者需自行传入筛选后的温度。新栅格封装承担质量掩膜。

### `fit_directional_coefficients(temperature_k, reference_temperature_k, view_zenith_deg, solar_zenith_deg, relative_azimuth_deg, *, reference_view_zenith_deg=0., reference_solar_zenith_deg=30., reference_relative_azimuth_deg=0., weights=1., quality_flag=0)`

[定义](C:/work/ls4t/base/normalization/angle.py:91)。拟合对象为**匹配、同状态参考温度与观测温度的差值**：

```text
X = K_observed - K_reference
y = T_observed - T_reference
c = argmin Σ weight * (Xc-y)^2
```

过滤温度非有限/越界、非法几何、无效质量、非正或非有限权重。三参数要求有效样本数大于 3，并通过满秩与条件数检查。没有截距项，所以未知传感器常偏差不应无条件混入角度系数。

返回 `DirectionalFit(coefficients_k, rmse_k, sample_count)`。`rmse_k` 是加权训练残差，不是独立角度校正精度；输入多个空间像元会合并拟合一套系数，不能自动理解为每像元拟合。若输入来自不同日期/地类，必须自行控制实际温度变化造成的混淆。

### `angle_normalize_years(indir_temperature=None, outdir_angle=None, years=None, overwrite=None)`

[定义](C:/work/ls4t/base/normalization/angle.py:119)。旧 NPZ 年份批处理包装，读取 `temperature_k`、三角度和 `directional_coefficients_k`，只替换温度字段。没有自动系数拟合，也没有新 GeoTIFF 接口的完整质量更新、阶段历史与重复处理保护；保留的原不确定度并未加入角度模型误差。

## 2. 时间归一化：单谐波日变化基线

源码：[time.py](C:/work/ls4t/base/normalization/time.py)。小时必须是同一约定下的地方太阳时，函数不负责 UTC→地方太阳时转换。

### `diurnal_anomaly(local_solar_time_hour, amplitude_k, peak_hour)`

[定义](C:/work/ls4t/base/normalization/time.py:24)。返回 `A*cos(2π*(t-peak)/24)`，单位 K。时刻和峰值要求 `[0,24)`，振幅必须非负，非法样本为 NaN。它输出相对均值的日变化项，不是完整绝对温度。

### `normalize_local_solar_time(temperature_k, local_solar_time_hour, amplitude_k, peak_hour, *, reference_hour=None)`

[定义](C:/work/ls4t/base/normalization/time.py:40)。默认目标 13.5 地方太阳时：

```text
T_reference = T_observed + D(reference_hour) - D(observed_hour)
```

保持观测中的绝对温度水平，只转移模型所预测的时刻差异。输入和输出均按 150–400 K 筛选；非法参考时刻报错。允许振幅/峰值逐像元变化，不负责估算参数或质量标志。该函数不是温度缺测填补：原温度 NaN 仍为 NaN。

### `fit_diurnal_cycle(temperature_k, local_solar_time_hour, *, weights=1., quality_flag=0, minimum_span_hours=6.)`

[定义](C:/work/ls4t/base/normalization/time.py:69)。使用线性参数化拟合：

```text
T(t) = mean + c*cos(2πt/24) + s*sin(2πt/24)
amplitude = hypot(c,s)
peak = atan2(s,c)*24/(2π) mod 24
```

有效样本不少于 4；圆周覆盖为 `24 - 相邻排序时刻的最大间隔（含跨午夜间隔）`，默认至少 6 h；同时执行满秩和病态检查。振幅接近零时峰值设置为 0，不能将该峰值解释为可识别的真实峰值时间。

返回 `DiurnalFit(mean_k, amplitude_k, peak_hour, rmse_k, sample_count)`。每次调用只拟合一套参数，广播后的有效样本会合并。适用于一个像元或合理均一区域的一日/明确时间窗；跨天输入需先控制天气与季节变化。单谐波不实现昼夜不对称、日落后的指数冷却、云下热过程，也没有神经网络。

### `time_normalize_years(indir_angle=None, outdir_time=None, years=None, overwrite=None)`

[定义](C:/work/ls4t/base/normalization/time.py:99)。NPZ 包装，读取地方太阳时、`diurnal_amplitude_k` 和 `diurnal_peak_hour`，调用已给参数的归一化；不从时序自动拟合参数。默认字段名暗示前一阶段是 angle，但不会主动验证来源或执行角度归一化。

## 3. 降尺度：辅助变量线性回归、TsHARP与逐粗像元温度残差闭合

### `downscale_temperature(coarse_temperature_k, fine_predictors, *, coarse_quality_flag=0, fine_quality_flag=0, fine_weights=None, minimum_coverage=1., method="linear")`

[定义](C:/work/ls4t/base/normalization/downscale.py:43)。这是实际的辅助变量降尺度，不是双线性插值。以下步骤描述默认linear；新增TsHARP的转换顺序另列于本节末。

输入约定：

- 粗温度为二维 `(rows,cols)`，K；辅助变量为 `(fine_rows,fine_cols)` 或末维为特征的三维数组。
- 细网格必须是粗网格的整数细分，且不能与粗网格完全相同；数组接口不携带坐标，地理一致性由调用者负责。
- 粗/细质量为 LS4T 标志，可广播。`fine_weights` 是有限正面积权重；未给时等权。覆盖率分母包含无效辅助像元的面积。
- `minimum_coverage` 默认为 1，只有完整覆盖的粗像元参与训练和输出；显式降低后才接受部分覆盖。

实际计算步骤：

1. 同时要求全部特征有效、细质量可用，计算每个粗像元的面积加权特征均值和覆盖率。
2. 选择温度 150–400 K、质量可用且覆盖足够的粗像元。
3. 对粗特征中心化/标准化，拟合 `T_coarse = intercept + Σ slope_j*X_coarse,j`。训练样本等权；细面积权重不等于粗样本回归权重。
4. 有效粗像元数必须大于 `特征数+1`，各特征需有粗尺度变化，设计矩阵须满秩且条件数合格。
5. 在细网格预测温度，并计算每个粗像元下细预测的面积加权均值。
6. `residual_coarse = observed_coarse - mean(predicted_fine)`；同一粗像元内所有有效子像元加相同残差。
7. 无效粗像元不填补；缺失细特征不预测。任一输出子像元超过 150–400 K，拒绝其整个粗像元，防止局部裁剪破坏均值闭合。

返回 `DownscaleResult`：

| 字段 | 含义 |
|---|---|
| `temperature_k` | 细网格温度 |
| `quality_flag` | 继承粗/细标志，并添加 INPUT_INVALID、LOW_SUPPORT、OUT_OF_RANGE |
| `coarse_coverage` | 粗网格有效辅助面积比例 |
| `coarse_residual_k` | 加回细预测的粗网格残差；不可用父像元为 NaN |
| `coefficients` | 截距及原始辅助变量单位下的斜率 |
| `training_rmse_k` | 粗网格拟合残差 RMS |
| `training_count` | 参与拟合的粗像元数量 |
| `method` | `linear`或`tsharp`；后者系数为截距K及K/覆盖率斜率 |

这实现的是温度均值闭合，不是 Planck 辐亮度/能量守恒；没有 RF、深度超分辨率或 DMS 回归树。细纹理来自输入辅助变量；粗训练拟合良好不能证明细尺度真实温度准确。新模型没有像元预测不确定度输出，也未做特征外推范围标志。

嵌套 `sum_blocks(values)` 和 `expand(values)` 分别完成按整数嵌套网格聚合、将粗值复制到细网格；它们是该方法内部数组操作，不是额外科学算法。

### 新增 `tsharp_cover_fraction` 与 `downscale_tsharp`

[`tsharp_cover_fraction(ndvi)`](C:/work/ls4t/base/normalization/downscale.py:29)计算`1-(1-NDVI)**0.625`，NDVI须已解码、在[0,1]内，域外/缺测返回NaN，不截断。采用固定0/1端元，非场景自适应端元。

[`downscale_tsharp(...)`](C:/work/ls4t/base/normalization/downscale.py:144)是统一入口`method="tsharp"`的便捷封装。要求恰好一个NDVI预测变量；先聚合原NDVI，再对粗NDVI进行覆盖率转换拟合OLS；对细NDVI转换后预测。回补量仍为`T_coarse-mean(predicted_fine)`，不能用转换前后不一致的粗回归残差替代。其余QA、覆盖率、网格和整父像元温区过滤均复用上述流程。[完整约定、参考论文及运行示例](C:/work/ls4t/docs/TSHARP.md)。

## 4. 空间归一化：加权格网聚合

### `aggregate_to_grid(values, row_index, column_index, target_shape, *, weights=None)`

[定义](C:/work/ls4t/base/normalization/space.py:51)。按调用方给定的目标行列索引，将散点/重复观测聚合到同一网格：`mean=Σ(w*x)/Σw`。默认等权，忽略非有限值和非正权重。任一有限温度落在网格外即报错，不静默丢弃。输出 `(mean, support)`；`support` 为权重和，只有等权时才等于样本数。不是降尺度，也不负责经纬度投影或计算面积交叠。

### `_aggregate_flags(flags, row_index, column_index, target_shape, valid_mask)`

[定义](C:/work/ls4t/base/normalization/space.py:21)。只对有效输入按目标像元执行 bitwise OR；质量聚合内部工具，不估算误差。

### `space_normalize_years(indir_time=None, outdir_space=None, years=None, target_shape=None, overwrite=None)`

[定义](C:/work/ls4t/base/normalization/space.py:90)。NPZ 年批处理；要求温度、不确定度、质量数组同形，质量可用、温度/误差有限且误差>0才参与。温度和不确定度都用等权算术平均；输出支持数，空像元标 LOW_SUPPORT，删除原始目标行列索引。

需要注意：此处“不确定度平均”不是独立观测误差传播 `sqrt(Σσ²)/n`，也不是逆方差融合；不能把该输出误差的含义与 `fuse_l3n` 混同。若改造标准产品契约，应明确是平均单次观测不确定度还是合成均值的不确定度。

## 5. 传感器间偏差校准：仿射模型

### `SensorHarmonization(sensor, reference_sensor, slope=1., offset_k=0., calibration_uncertainty_k=0.)`

[类型](C:/work/ls4t/base/normalization/sensor.py:26)，[apply](C:/work/ls4t/base/normalization/sensor.py:33)：

```text
T' = slope*T + offset
σ' = sqrt((slope*σ)^2 + calibration_uncertainty^2)
```

`apply(temperature_k, uncertainty_k)` 返回温度及误差数组。要求斜率>0、校准误差≥0；系数由外部提供，没有实现自动匹配卫星、回归求系数或交叉验证。该公式未包含 slope/offset 的参数协方差，也未建模共同系统误差。sensor/reference_sensor 为来源标签，不会据名称选择物理波段响应。

### `sensor_normalize_years(...)`

[定义](C:/work/ls4t/base/normalization/sensor.py:46)。参数包含输入/输出、年份、两传感器名称、斜率、偏差、校准误差和覆盖开关；建立上述模型并更新每个 NPZ 温度与误差。属于包装函数，不是新增标定算法。

## 6. 多源融合：带创新筛选的逆方差加权

### 数据对象

`NormalizedField(sensor, temperature_k, uncertainty_k, quality_flag, profile)` 描述一个已经满足归一化基准的源；`FusionResult` 输出温度、不确定度、质量、贡献传感器数量及 profile。[类型定义](C:/work/ls4t/base/normalization/fusion.py:27)。

### `fuse_l3n(inputs, *, innovation_threshold_sigma=None, minimum_sensors=None)`

[定义](C:/work/ls4t/base/normalization/fusion.py:46)。默认创新阈值 4σ，最少传感器数 1。所有输入须相同 profile_id、温度数组形状；同一传感器名称（忽略大小写）只能出现一次。

1. 有效输入为有限温度、有限正误差、质量可用。
2. 用 `w=1/σ²` 计算初始均值。
3. 每个来源仅当 `abs(T_i-preliminary)≤threshold*σ_i` 才接受；只有一个有效来源时直接保留。
4. 如果所有有效来源都被拒绝，保留误差最小的一个，并标记来源分歧 FUSION_REJECTED。
5. 接受项重新做逆方差加权，`σ_fused=sqrt(1/Σw)`；贡献来源不足时输出 NaN 并标 LOW_SUPPORT。

这不是学习型融合、卡尔曼滤波、时空融合或自动传感器标定。误差公式以输入误差可比较、没有显式交叉协方差为前提；同源相关性或共同标定偏差不会自动计入。形状/profile 是契约检查，不会读取或比较输入数组的实际地理坐标。

### `fusion_years(input_roots=None, output_root=None, years=None, innovation_threshold_sigma=None, minimum_sensors=None, overwrite=None)`

[定义](C:/work/ls4t/base/normalization/fusion.py:110)。取各目录下同年份、相同相对文件名的 NPZ 为一组，缺源时仍可按最少来源门槛运行；没有实际时间戳配对器。

源码边界：该包装只从文件恢复 profile 的 name/version/grid_id/temporal_interval，角度和时间基准使用 dataclass 默认值；写出也不保存完整参考角度/时刻。因此，非默认参考基准不能通过该旧批处理路径被完整往返保存。这是产品衔接待整理项，不能因底层 `assert_compatible` 存在就认为批处理已经验证全部参考参数。

## 7. 归一化契约与公共标定数值工具

| 函数/方法 | 实际职责与边界 |
|---|---|
| [`NormalizationProfile.__post_init__`](C:/work/ls4t/base/normalization/profile.py:22) | 检查名称、版本、网格、时段非空，单位 K，参考视角 `[0,90)`、地方太阳时 `[0,24)`；并非对全部几何量做完整验证。 |
| [`NormalizationProfile.profile_id`](C:/work/ls4t/base/normalization/profile.py:33) | 将所有 dataclass 字段排序 JSON 后 SHA256 截取 10 位，生成包含名称版本的基准标识；并非文件内容哈希。 |
| [`NormalizationProfile.assert_compatible(other)`](C:/work/ls4t/base/normalization/profile.py:38) | 比较 profile_id，不同即报错；不执行重投影、单位转换或补充标定。 |
| [`fit_linear(design,target,weights)`](C:/work/ls4t/base/normalization/_fit.py:7) | 加权最小二乘公共数值核心。以最大权重归一化，列范数缩放，调用 NumPy lstsq；要求样本数>参数数、满秩、缩放后条件数≤1e10；返回原单位系数和加权训练 RMSE。不是 ridge。 |
| [`quality_flags(values)`](C:/work/ls4t/base/normalization/_validation.py:7) | 无穷/NaN、非整数、超出 uint16 范围的 QA 都映射为 INPUT_INVALID，避免转型后变为 GOOD；不负责原生卫星 QC 的位定义转换。 |

## 8. GeoTIFF 归一化入口与保护

三个入口定义在 [normalization/raster.py](C:/work/ls4t/base/normalization/raster.py)，只读取显式输入，不按传感器名称生成校准参数：

| 函数 | 输入与输出 | 实际处理 |
|---|---|---|
| [`angle_normalize_raster`](C:/work/ls4t/base/normalization/raster.py:133) | input/output；三角度、三个系数、参考角度；可选择温度与质量波段和定标覆盖值 | 读入质量、原始 NoData/mask、scale/offset；调用 normalize_directional；输出 temperature_k/quality_flag/correction_k。 |
| [`time_normalize_raster`](C:/work/ls4t/base/normalization/raster.py:162) | input/output；观测地方太阳时、振幅、峰值、参考时刻 | 调用 normalize_local_solar_time；输出与角度阶段相同三字段。 |
| [`downscale_raster`](C:/work/ls4t/base/normalization/raster.py:182) | input/output；predictors 描述符列表、细质量、可选面积、覆盖门槛 | 对粗/细地理网格做嵌套检查，读取细辅助变量并调用 downscale_temperature；输出温度/质量/复制到细网格的粗覆盖率，回归系数和训练诊断写 metadata。 |

标量可用于整景常量；像元参数使用 `{path,band,scale,offset}`。同格网辅助数据必须 CRS、形状、仿射变换一致；降尺度额外要求北向上、同范围、整数分辨率关系。经纬度细像元默认权重取 `abs(diff(sin(latitude_edges)))`；投影网格默认等权。用户显式面积可以覆盖该默认。

温度默认寻找 `temperature_k`、`variable__lst`、`lst` 波段名称，单波段亦可自动选取。默认识别名为 `quality_flag` 的 LS4T QA。默认不覆盖既有输出，禁止覆盖输入/辅助文件，禁止同一个阶段重复施加到已有阶段历史的输入上。

内部函数并非独立优化算法：

| 函数 | 职责 |
|---|---|
| `_band_number` | 解析名称/1 起始编号，拒绝多波段歧义。 |
| `_read` | 在定标前处理 NoData/GDAL mask，读取 CRS/仿射和 metadata。 |
| `_same_grid` | 检查同网格或整数嵌套网格；不自动 resample。 |
| `_field` | 读取标量或描述符辅助输入并验证网格。 |
| `_protect` | 防止输出覆盖辅助源。 |
| `_prepare` | 验证输出位置、读取温度和质量、温区检查、重复阶段检查。 |
| `_save` | 写 GeoTIFF、NaN NoData 和 LS4T_NORMALIZATION 历史。 |

输出 schema 为 `NORMALIZATION_STAGE_V1`，尚不是含完整不确定度的标准 `TemperatureProduct/L3N`。也不会自动连接旧 NPZ `fusion_years`。新 GeoTIFF 阶段没有虚构模型不确定度；要正式进入融合还需要明确的误差产品和完整基准元数据。

案例 [run.py](C:/work/ls4t/cases/multisource-normalization/run.py:30) 的 `run_stage(config_path,stage,overwrite=False)` 按配置对多源逐一执行指定阶段；`_resolve` 使所有相对路径相对配置文件；`create_demo` 生成两个合成源；`main` 处理命令行。它们是上述方法的组合，不增加新的科学求解器。

## 9. 时间合成与同样本月合成

### `temporal_composite(temperature_k, uncertainty_k, quality_flag, *, minimum_observations=1)`

[定义](C:/work/ls4t/base/composite/temporal.py:34)。输入三数组同形，第一维为时间，剩余维为像元。有效样本为温度/误差有限、误差正、质量可用，使用逆方差加权均值和 `sqrt(1/Σw)`。输出 `CompositeResult(temperature_k,uncertainty_k,quality_flag,observation_count)`；不足门槛标 LOW_SUPPORT。

它只对已有样本做时间统计，不生成缺失时刻温度，不是日变化重构，也未考虑时间相关误差。调用者必须已保证时刻/角度/网格和产品语义可合成。

### `composite_years(indir_l3n=None,outdir_l3c=None,years=None,minimum_observations=None,overwrite=None)`

[定义](C:/work/ls4t/base/composite/temporal.py:64)。读取一年目录直属 NPZ，堆叠并合为该年一个输出。不是自动月合成、8 日合成或任意时段分组器；文件名/目录决定分组，没有实际日期解析。

### `collect_month(daily_root,tag,year,month,view)`

[定义](C:/work/ls4t/base/composite/monthly_paired.py:41)。按已有 SLSTR 日拼接文件名找到同时存在的 LST 与 LSCT2 对；返回 stamp/view/lst/lsct 路径字典列表。缺失配对文件不会进入合成。

### `monthly_paired(daily_root,tag,year,month,view='day')`

[定义](C:/work/ls4t/base/composite/monthly_paired.py:61)。读取 LST UInt16/100 编码和 LSCT2 的 K 浮点；每次观测只有 LST、土壤、植被三者均有效才累计。三种温度完全使用同一支持样本集，等权算术平均，返回 4 波段数组 `[LST,Ts,Tv,count]`、Rasterio profile、统计信息。

有效规则是 LST 原始码 `0<value<65535`，两个 LSCT2 分量有限且>0。没有额外可配置质量位传播和温度物理范围过滤，依赖上游产品规则；该函数自身也没有完整的逐文件 CRS/transform 一致性验证，输入必须已对齐。和逆方差 `temporal_composite` 是不同统计口径。

### `write_monthly_paired(out_root,year,month,tag,view,array,profile,stats)`

[定义](C:/work/ls4t/base/composite/monthly_paired.py:119)。写出 4 波段 Float32、NaN NoData GeoTIFF，以及 JSON 统计。输出器，不是另一种合成算法。案例中的三组分“五温度月合成”另有实现，见案例章节。

## 10. 公共空间处理：数据选择、格网投影与裁剪

这些函数是各层可复用的空间基础，不应与角度归一化或降尺度重复计数。源文件：[spatial.py](C:/work/ls4t/base/spatial.py)。

| 函数 | 输入输出、核心规则 | 关键边界 |
|---|---|---|
| [`bounds_mask(latitude,longitude,bounds)`](C:/work/ls4t/base/spatial.py:24) | 二维经纬度和 `(west,south,east,north)`→布尔范围掩膜；支持 west>east 跨日期线。 | 不计算矢量多边形面积覆盖。 |
| [`study_area_window`](C:/work/ls4t/base/spatial.py:50) | 从范围掩膜生成最小矩形 row/col slice 和精确掩膜。 | 无相交像元时报错。 |
| [`crop_observation`](C:/work/ls4t/base/spatial.py:72) | 对观测 dataclass 的同形数组裁剪；范围外非坐标值为 NaN、cloud=True。 | 不改变像元分辨率。 |
| [`mosaic_observations(items,primary_field,angle_field='view_zenith_deg')`](C:/work/ls4t/base/spatial.py:105) | 同类型、同形、同视角产品中，选择无云、主观测有限且绝对视角最小的来源；其他变量同步取同一来源。 | 选择像元，不平均；低视角选择不是将温度校正到同一视角。地理对齐由上游保障。 |
| [`target_grid_indices`](C:/work/ls4t/base/spatial.py:178) | WGS84 经纬度经 GDAL 坐标变换到目标栅格，仿射逆变换后 floor 得 row/col，返回目标 shape。 | 默认分块 100000；只建立映射，不进行高分辨率信息恢复。 |
| [`_project_field`](C:/work/ls4t/base/spatial.py:235) | 用 bincount 按目标像元做有限样本算术平均。 | 不是双线性/三次插值，也不是面积交叠积分。 |
| [`project_observation`](C:/work/ls4t/base/spatial.py:253) | 对同形字段逐个用上述聚合；云比例超过门槛即云，默认阈值 0。 | 包括角度等字段采用普通平均，跨 0/360 方位角不做圆周平均；需关注适用区域。 |
| [`crop_temperature_product`](C:/work/ls4t/base/spatial.py:293) | 裁剪带经纬度的 TemperatureProduct，裁剪误差并补 INPUT_INVALID，写空间操作 metadata。 | 需要 latitude_deg、longitude_deg 两变量。 |
| [`mosaic_temperature_products`](C:/work/ls4t/base/spatial.py:325) | 同 sensor/level/grid_id/algorithm_version 的产品；有效重叠优先选主变量误差最小的源，否则按输入顺序。所有分量随同一来源取值。 | 没有跨源求均值；不等价于 fuse_l3n。实际获取时刻和完整归一化基准仍应由案例把关。 |
| [`resize_data`](C:/work/ls4t/base/spatial.py:452) | OpenCV 分辨率重采样旧辅助，默认最近邻。 | 缩放数组不等于物理降尺度；没有恢复真实细节。 |
| `geo2lonlat`、`lonlat2geo`、`geo2imagexy`、`imagexy2geo`、`loc2map` | 旧坐标转换工具，分别处理投影坐标、经纬度及行列号关系。 | 不属于反演算法；具体参数顺序需照源码，不能凭名称推断经纬顺序。 |

`_array_fields` 枚举 dataclass 同形数组；`_pick` 按来源索引取值；`_first_finite` 选第一个有限坐标。这些只支撑上述方法。

## 11. 质量、产品与验证指标

`QualityFlag` 定义 GOOD=0、INPUT_INVALID=1、CLOUD=2、OUT_OF_RANGE=4、RETRIEVAL_FAILED=8、ILL_CONDITIONED=16、NORMALIZATION_FAILED=32、PROFILE_MISMATCH=64、FUSION_REJECTED=128、LOW_SUPPORT=256。[源码](C:/work/ls4t/base/quality.py:10)。

`new_flags(shape)` 分配 uint16 零标志；`set_flag(flags,mask,flag)` 原位按位 OR；`usable(flags,reject=INVALID_FLAGS)` 返回是否未命中拒绝位。默认拒绝集合不包含 ILL_CONDITIONED 和 FUSION_REJECTED，意味着这些位是可保留的告警，并非一律缺测。旧 `usable` 本身直接转 uint16；新增归一化在前面使用 `quality_flags` 防止缺失 QA 被误转为 GOOD。

`ProductMetadata.__post_init__` 检查产品标签和 UTC 时间，L3N 要求 normalization_profile；`to_dict/from_dict` 是序列化。`TemperatureProduct.validate` 检查变量与 QA 形状、LST 产品必需变量/误差及温区；`product_filename` 形成文件名。[源码](C:/work/ls4t/base/product.py)。这些是跨层契约，不是科学优化算法。

`cal_rmse_r2(data1,data2,tshred=9)` 位于 [metrics.py:11](C:/work/ls4t/base/metrics.py:11)：先按 `abs(data2-data1)<9` 默认筛选，再计算 bias/RMSE/相关平方。筛选使用待评价残差，得到的是被阈值截断后的指标，不能直接作为未筛选全样本精度；另外 `r2=coef[1]*coef[1]` 返回一行数组（通常 `[r²,1]`），不是单一标量。该问题本次只盘点，未修改代码。

## 12. 当前测试证据与适用边界

- [test_normalization.py](C:/work/ls4t/tests/test_normalization.py)：角度/时间/传感器独立调用、融合数值与基准不一致拒绝、空间重复样本和越界、质量筛选。
- [test_multisource_normalization.py](C:/work/ls4t/tests/test_multisource_normalization.py)：合成角度系数和日变化恢复、秩亏/短时窗拒绝、非法参数、QA 缺失、降尺度细纹理/面积闭合/覆盖率/缺测。
- [test_normalization_raster.py](C:/work/ls4t/tests/test_normalization_raster.py)：GeoTIFF 定标/NoData/mask、网格错位、双源三阶段示例、重复处理和覆盖源文件保护。
- [test_spatial_modes.py](C:/work/ls4t/tests/test_spatial_modes.py)：观测和结果裁剪、重叠选择等空间行为。
- 本轮重新运行全量套件为 176 passed、3 skipped；跳过的三个模块是非洲下载和北京建筑/LAI，原因是缺失 shapely/pyproj。具体见总报告。
- 没有把上述合成归一化测试认定为真实多卫星归一化精度，也没有把函数目录的同名测试引用认定为全部分支已覆盖。`temporal_composite`、`monthly_paired` 等不应仅凭函数存在被标记成已完成独立数值验证。
