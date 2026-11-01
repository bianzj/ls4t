# TsHARP 温度降尺度

2026-10-24新增。`method="linear"`继续作为默认多变量线性降尺度；`method="tsharp"`使用单个细尺度NDVI预测变量。两者共用网格检查、QA、面积权重、有效覆盖率、残差回补和温区检查。

## 算法约定

使用简化植被覆盖率`f(N)=1-(1-N)**0.625`，固定NDVI端元为0和1。先将细尺度NDVI按面积聚合成粗尺度`N_c`，再拟合`T_c=a+b*f(N_c)`；不是先算细尺度覆盖率再聚合。相关公式和尺度顺序见[Agam等，2007](https://agupubs.onlinelibrary.wiley.com/doi/full/10.1029/2007JD008407)。

将粗尺度拟合系数用于细尺度`P_f=a+b*f(N_f)`，再重新聚合细尺度预测，计算`R_c=T_c-mean_area(P_f)`，输出`T_f=P_f+expand(R_c)`。采用这种回补定义可使细尺度温度面积均值回到原粗尺度温度；该运行顺序也见[Agam等，2008](https://agupubs.onlinelibrary.wiley.com/doi/full/10.1029/2007GL032195)。由于f是非线性的，`f(mean(N_f))`与`mean(f(N_f))`不相等，不能直接把粗尺度回归残差当作这里的均值闭合修正。

此实现是全场景单一TsHARP关系，不含分地类/局部回归、场景端元自动估计、残差插值或树模型。粗尺度回归为带截距普通最小二乘，各有效粗像元等权；细尺度聚合使用像元面积权重。保持的是K单位温度均值，不是Planck辐射或能量守恒。

## 数组接口

```python
from base.normalization import downscale_tsharp, downscale_temperature

# coarse_lst_k: (coarse_rows, coarse_cols)，单位K
# fine_ndvi: (fine_rows, fine_cols)，已经解码的无量纲NDVI
result = downscale_tsharp(coarse_lst_k, fine_ndvi)

# 相同计算的统一入口
result = downscale_temperature(coarse_lst_k, fine_ndvi, method="tsharp")

fine_lst_k = result.temperature_k
qa = result.quality_flag
intercept_k, slope_k_per_cover = result.coefficients
```

`downscale_tsharp`另接收`coarse_quality_flag`、`fine_quality_flag`、`fine_weights`、`minimum_coverage`。统一入口TsHARP允许2D NDVI或最后一维为1的3D数组，拒绝多个预测波段。`tsharp_cover_fraction(ndvi)`可独立计算覆盖率变换。

结果包含：细尺度温度、QA、粗像元有效覆盖比例、实际回补残差、回归系数、粗尺度训练RMSE、训练数以及`method`。训练RMSE指`T_c`与`a+b*f(N_c)`的残差；`coarse_residual_k`指细尺度预测重新聚合后需要回补的修正，两者定义不同。

## GeoTIFF与配置

```python
from base.normalization import downscale_raster

downscale_raster(
    "coarse_lst_k.tif", "fine_lst_tsharp.tif",
    method="tsharp",
    predictors=[{"path": "fine_ndvi.tif", "band": 1}],
)
```

若NDVI以整数存储且波段没有定标元数据，可在描述符中明确`"scale": 0.0001`；若已有GDAL Scale则不重复指定。NoData在定标前屏蔽。温度输入也必须正确解码为K。

已有case入口直接支持配置中的`method`：

```powershell
python cases/multisource-normalization/run.py downscale --config cases/multisource-normalization/config.tsharp.example.json
```

示例配置中的路径相对JSON目录解析，真实数据需替换路径。输出记录方法名、覆盖率公式、先聚合NDVI的顺序、残差定义、系数、训练诊断及输入路径。

## 缺测与使用边界

- 细、粗网格须同投影、同范围且整数嵌套；数组接口由调用者保证地理对齐，GeoTIFF入口验证实际网格。
- 本实现仅接受[0,1]的NDVI，域外变NaN，不强行截断；粗温度要求150–400 K。
- 水体、雪冰等不适合该植被关系的像元，应通过QA或输入NoData屏蔽；NDVI为正也不代表一定不是水体。QA必须使用LS4T标志语义，不能直接传入未经映射的外部产品QA位。
- 默认`minimum_coverage=1`，辅助数据缺一部分则整个父像元不输出。主动降低阈值时，闭合仅针对存活子像元，不代表完整粗像元面积；应记录这种支持域变化。
- 粗温度有云/缺测时不填洞。有效粗样本须超过2个，且NDVI覆盖率有足够变化、设计矩阵可辨识，否则报错。
- 温度异常子像元会使整个父像元被拒绝，避免逐像元截断破坏闭合。
- 结果假设温度—植被关系可跨尺度使用。土壤湿度、灌溉、城市材质等未由NDVI解释的细节不会自动恢复；常数残差回补也可能产生块状边界。

## 离线示例

在仓库根目录，用包含GDAL/NumPy/SciPy的环境运行：

```powershell
python cases/multisource-normalization/run.py --demo D:/your-input-location/multisource-normalization/tsharp-demo --products D:/your-result-location/multisource-normalization/tsharp-demo --demo-method tsharp
python cases/multisource-normalization/run.py angle --config D:/your-input-location/multisource-normalization/tsharp-demo/config.json
python cases/multisource-normalization/run.py time --config D:/your-input-location/multisource-normalization/tsharp-demo/config.json
python cases/multisource-normalization/run.py downscale --config D:/your-input-location/multisource-normalization/tsharp-demo/config.json
```

生成两套有已知角度/时间偏差的合成温度和细尺度NDVI；逐阶段执行后输出两套一致的TsHARP结果。示例是功能验证，不是实际卫星产品或独立地面精度评估。目录已有内容时拒绝重建；原线性示例不受影响。

## 本次验证

- 新增11项测试：标准覆盖率转换、先聚合NDVI的顺序、非线性聚合差异下的闭合、面积权重、无效NDVI/云/部分覆盖、非法方法/多波段/秩亏拒绝、线性默认不变、GeoTIFF定标/来源记录、多源示例。
- 全库最终结果：**218 passed，3 skipped，14.54s**。跳过来自缺少shapely的非洲下载测试和缺少pyproj的北京建筑/LAI测试。
- 上述两源TsHARP离线示例曾实际运行完成；临时产物现已清理，可指定外部路径重新生成。
- 独立代码审阅未发现P1/P2问题；旧文档中“尚无TsHARP”的表述已同步更正。
