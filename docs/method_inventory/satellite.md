# 卫星产品层：LST、观测解码与反射相关功能清单

盘点日期：2026-10-24；对象：`C:/work/ls4t` 当前工作树。本文依据函数体及测试体阅读，不依据函数名推定能力；下面的“测试证据”解释测试定义及其实际断言。本轮全库测试执行结果见总报告的验证记录；未重新运行区域科学实验或独立地面精度评价。

## 1. 层级与计数边界

- 已存在一个公共 **八特征广义分裂窗 LST 核心**，AATSR、SLSTR、MSG、MODIS、VIIRS、AHI、ASTER 的公共 `retrieve_*_lst` 是传感器数据映射入口，不能计为七个独立反演算法。
- AATSR 的 EPR N1、SLSTR 的 SEN3 NetCDF、MSG 的 Satpy native 读取在公共层有实现。MODIS、VIIRS、AHI、ASTER 公共 `read_native_product` 实际读取预处理好的 NPZ/GeoTIFF，不等于已经实现原始任务 HDF/NetCDF/HSD 的解析和定标。
- `slstr_reconstruct` 是几何、云与热红外网格对齐，保留原亮温；它属于卫星观测准备，不能放进“DL 温度重建”方法清单。
- 已读代码中可确认红光/近红外读取、辐亮度到反射因子换算、NDVI；未确认独立的地表反射率大气校正反演公共 API。不能把这些功能标成完整 Surface Reflectance 产品生产链。
- `cases` 内还保留实际公式、系数选择和编码；公共入口存在不代表所有案例已经调用它，也不代表公共默认参数与案例数值等价。

状态用语：**公共核心**＝无文件遍历的计算；**公共入口**＝可调用的读写/任务接口；**包装器**＝委托公共实现；**案例实现**＝公式或流程仍由案例持有；**兼容/历史**＝保留旧接口或旧单位语义。上述状态描述代码归属，不代替观测验证等级。

## 2. LST 计算核心及校准参数

| 函数/类与源码 | 输入、输出 | 实际计算及边界 | 状态与证据 |
|---|---|---|---|
| [`SplitWindowModel(view_zenith_nodes_deg, water_vapour_edges, coefficients, valid_temperature_range_k=(220,365))`](C:/work/ls4t/base/lst.py:23)；`retrieve(bt1_k, bt2_k, emissivity1, emissivity2, water_vapour, view_zenith_deg, *, cloud_mask=None)` | 输入可广播标量/数组；BT 为 K，角度为度，发射率无量纲；水汽单位必须与系数分箱一致，传感器入口为 cm。系数形状 `(Nv, Nw-1, 8)`。输出 `SplitWindowResult(temperature_k, quality_flag)`，形状为广播结果 | 水汽分箱；相邻 VZA 节点线性插值系数，再与八特征点乘。非有限/非正 BT、发射率不在 `(0,1]`、云、校准域外变 NaN 并置位；结果超温度范围变 NaN。VZA 最末节点允许，水汽最末边界不允许；不外推 | 公共核心。[八特征合成测试](C:/work/ls4t/tests/test_retrieval.py:10)只设置均温系数为 1；[校准域测试](C:/work/ls4t/tests/test_retrieval.py:26)、[网格约束](C:/work/ls4t/tests/test_retrieval.py:34) |
| [`vegetation_fraction_from_lai(lai, view_zenith_deg, projection_g=0.5)`](C:/work/ls4t/base/lst.py:127) | LAI 无量纲，度；可广播；输出方向植被覆盖比例 `[0,1]` | `f=1-exp(-G*LAI/cos(vza))`；要求 LAI≥0、`abs(vza)<89`、cos>0；否则 NaN | 公共核心；供 `retrieve_dual_channel_lst` 调用，未在上述测试文件发现单独覆盖全部边界的直接测试 |
| [`effective_emissivity(soil_emissivity, vegetation_emissivity, vegetation_fraction, *, scattering_factor=0.75, maximum=0.995)`](C:/work/ls4t/base/lst.py:145) | 三组可广播无量纲量；输出混合发射率 | `e=es*(1-f)+ev*f+(1-es)*ev*F*(1-f)`，限制最大 0.995；es、ev 必须在 `(0,1]`，f 在 `[0,1]` | 公共核心；F 是输入常数，不从卫星反演；不是地表反射率计算 |
| [`DualChannelObservation(...)`](C:/work/ls4t/base/lst.py:174) | BT1/2、土壤和植被各两通道发射率、LAI、水汽、VZA、可选云 | 统一内存字段载体；不负责原始产品缩放、空间配准或自动估算辅助参数 | 公共数据契约 |
| [`retrieve_dual_channel_lst(observation, model, *, scattering_factor=0.75)`](C:/work/ls4t/base/lst.py:189) | 统一观测与 `SplitWindowModel` → `SplitWindowResult` | 顺序调用方向 FVC、两个有效发射率、分裂窗；没有训练或系数拟合 | 公共核心组合；七传感器公共入口共同调用 |
| [`legacy_split_window_model(coefficient_table, view_zenith_nodes_deg, water_vapour_edges, *, coefficient_columns=slice(-8,None), valid_temperature_range_k=(220,365))`](C:/work/ls4t/base/calibration.py:13) | 二维旧系数表；要求截取后形状 `(Nv*(Nw-1),8)` → 模型 | 按 VZA-major 顺序 reshape；只转换既有系数，不估计系数 | 兼容适配；[round-trip](C:/work/ls4t/tests/test_calibration.py:8) |
| [`save_split_window_model(path, model, *, sensor, version)`](C:/work/ls4t/base/calibration.py:39)；[`load_split_window_model(path)`](C:/work/ls4t/base/calibration.py:71) | 模型↔非 pickle NPZ；schema、sensor、version、温度范围 | 原子写入；加载检查 schema、恢复模型。加载结果不保留 sensor/version 字段到 `SplitWindowModel`，调用链未核对系数文件的 sensor 与输入 sensor 是否一致 | 公共参数 IO；版本化存储不等于系数科学有效性验证 |
| [`import_legacy_coefficients(table_path, output_path, *, version)`](C:/work/ls4t/base/slstr/slstr_lst.py:42) | SLSTR 文本表→版本化 NPZ | 取列 `2:10`；VZA `[0,3,14.9,38.6,44.5,51.2,58,65,70,75,80]`；水汽边界 cm `[0,1.25,2.25,3.25,4.25,5.25,100]` | SLSTR 参数转换包装器，不是新增 LST 算法 |

八特征精确定义：令 `M=(BT1+BT2)/2`、`D=(BT1-BT2)/2`、`e=(e1+e2)/2`、`de=e1-e2`，则

```text
x = [1, M, (1-e)/e*M, de/e²*M, D, (1-e)/e*D, de/e²*D, (BT1-BT2)²]
LST = sum(c_i(VZA, water_bin) * x_i)
```

这条链需要已提供的土壤/植被发射率、LAI、水汽和有效系数；不能声称由双通道 BT 单独同时反演温度、发射率和大气状态。

## 3. 辐射与温度单位工具

| 函数与源码 | 输入→输出 | 公式、限制与状态 |
|---|---|---|
| [`planck_radiance(wavelength_um, temperature_k)`](C:/work/ls4t/base/radiometry.py:15) | 正波长 μm；K 标量/数组 → 光谱辐亮度 `W m⁻² sr⁻¹ μm⁻¹` | `C1/[λ⁵*expm1(C2/(λT))]`，C1=1.191042972e8、C2=1.438776877e4；T≤0→NaN；公共核心 |
| [`inverse_planck(wavelength_um, radiance)`](C:/work/ls4t/base/radiometry.py:27) | μm、上述光谱辐亮度→K | `C2/[λ*log1p(C1/(Lλ⁵))]`；L≤0→NaN；公共核心；[互逆测试](C:/work/ls4t/tests/test_physics.py:6) |
| [`decode_temperature(raw, *, scale, offset=0, fill_value=None, source_unit='K')`](C:/work/ls4t/base/radiometry.py:39) | 编码数组→float64 K 数组 | `raw*scale+offset`；显式摄氏度加273.15；原始 fill→NaN；不猜单位；[测试](C:/work/ls4t/tests/test_physics.py:12)。这是解码，不是 LST 反演或时空归一化 |
| [`planck(wavelength, Ts)`](C:/work/ls4t/base/radiometry.py:77)；[`inv_planck(wavelength, rad)`](C:/work/ls4t/base/radiometry.py:100) | 旧温度/辐射接口 | `planck` 自动把数值<100解释成摄氏度并加273.15，常数也与新接口略不同；`inv_planck`返回 K。兼容/历史，不能与显式单位接口混写而不记录差异 |

上述 Planck 是单波长转换，没有实现传感器光谱响应函数积分；亮温、地表温度和反射率是不同物理量。

## 4. AATSR：原始 N1 到公共 LST

公共数据 `AatsrDataProduct` 包含二维同形 `bt11_k/bt12_k`、VZA、经纬度、云；`view∈{nadir,forward}`；六辅助字段须全部有或全部无。来源见 [类定义](C:/work/ls4t/base/aatsr/aatsr_data.py:52)。

| 函数与源码 | 关键输入→输出与真实职责 | 限制/状态 |
|---|---|---|
| [`unzip_gzip(input_path, output_path, overwrite=False)`](C:/work/ls4t/base/aatsr/aatsr_data.py:117) | gzip→原始文件 Path | 文件准备，无反演 |
| [`read_native_product(input_path, view='nadir')`](C:/work/ls4t/base/aatsr/aatsr_data.py:130) | EPR N1→`AatsrDataProduct`；读 `btemp_*_1100/1200`、`view_elev_*`、经纬度、云旗标 | VZA=`90-elevation`；云=`flag!=0`，不是逐位精选云分类；经纬度必须已和 BT 同形，不自动重建。时间从文件名取第一个时间，start=end。需要 EPR；公共原始读取实现 |
| [`add_lst_auxiliary(item, auxiliary_file)`](C:/work/ls4t/base/aatsr/aatsr_data.py:170) | NPZ 中 `soil_emissivity_11/12`、`vegetation_emissivity_11/12`、`lai`、`tcwv_cm`广播到观测二维形状 | 附加现成辅助场；不包含辅助数据反演或重投影 |
| [`write_data_product(path,item)`](C:/work/ls4t/base/aatsr/aatsr_data.py:184)、[`read_data_product(path)`](C:/work/ls4t/base/aatsr/aatsr_data.py:208) | `ls4t.aatsr-data/v1` NPZ 与对象互转 | 保留源、角度、时间与可选辅助字段；读取校验 schema |
| [`aatsr_unzip(indir_zip,outdir_raw,years,months,days,overwrite)`](C:/work/ls4t/base/aatsr/aatsr_data.py:231)、[`aatsr_extract(indir_raw,outdir_extract,years,months,days,views,overwrite)`](C:/work/ls4t/base/aatsr/aatsr_data.py:267) | 以上全部参数默认 None；按年月日处理；提取产出每景/每视角 NPZ | 公共批处理入口；cases 负责执行路径 |
| [`retrieve_aatsr_lst(item, coefficient_file=None)`](C:/work/ls4t/base/aatsr/aatsr_lst.py:37) | 完整 AATSR 观测→公共 `SplitWindowResult` | 仅字段映射与公共核心调用；nadir/forward 不构成新分裂窗公式 |
| [`produce_aatsr_lst(input_path,output_path,coefficient_file=None,auxiliary_file=None,grid_id=None,algorithm_version=None,uncertainty_k=None)`](C:/work/ls4t/base/aatsr/aatsr_lst.py:57) | DATA+系数+辅助→L2LST 温度产品 NPZ；变量 lst、经纬度、QC、uncertainty | 必须有时间；默认不确定度1 K为用户参数填满，未从残差传播估计 |
| [`aatsr_lst(indir_data,outdir_lst,coefficient_file,auxiliary_file,years,months,days,overwrite)`](C:/work/ls4t/base/aatsr/aatsr_lst.py:111) | 参数均默认 None；按年月日、递归 NPZ 调用 `produce_aatsr_lst` | 批处理包装器 |

案例仍有 [cases/aatsr/aatsr_lst.py](C:/work/ls4t/cases/aatsr/aatsr_lst.py:15)：`cal_fvc_from_lai(thetav,lai)`实现方向 FVC；后续顶层脚本重复八特征分裂窗，输出 `lstN/lstO` 的 uint16、比例0.01。读取了 day/night 两张表，已读 nadir/forward 计算段取 `coeffs_day`，不能仅凭存在 night 文件认定两条昼夜路由均运行。案例读取函数 [`aatsr_read_obs(infile_obs)`](C:/work/ls4t/cases/aatsr/util_aatsr.py:174) 实际返回四组 BT/100，虽 docstring 写“红、近红外”，也不能据该注释认定为光学读取。

## 5. SLSTR：提取、几何对齐、LST 与产品 IO

| 函数与源码 | 输入→输出/计算 | 边界与状态 |
|---|---|---|
| [`unpack_archive(archive, output_directory)`](C:/work/ls4t/base/slstr/slstr_data.py:172) | ZIP→SEN3 Path | 带 archive 路径安全检查；[父路径测试](C:/work/ls4t/tests/test_slstr_products.py:38)、[盘符相对路径测试](C:/work/ls4t/tests/test_slstr_products.py:46)；文件准备 |
| [`extract_native_product(product_directory, *, view='nadir')`](C:/work/ls4t/base/slstr/slstr_data.py:241) | SEN3 目录→`SlstrExtractedProduct`；view nadir/oblique；S8/S9 BT(K)、原经纬度、tie-point VZA(度)、原 cloud | 从 `in/io` 热红外、`tn/to` 几何读取；保持各原始网格，BT8/9要求同形；公共原生提取 |
| [`reconstruct_product(item)`](C:/work/ls4t/base/slstr/slstr_data.py:289) | extracted→`SlstrDataProduct` | 把 VZA、经纬度、cloud最近邻resize到BT8形状；cloud非零为云；BT8/9保留。没有时序输入、学习权重或缺测温度估计；[4×4合成形状测试](C:/work/ls4t/tests/test_flat_structure.py:188) |
| [`read_native_product(product_directory, *, view='nadir')`](C:/work/ls4t/base/slstr/slstr_data.py:310) | `reconstruct_product(extract_native_product(...))` | 单景兼容组合包装器 |
| [`write_extracted_product(path,item)`](C:/work/ls4t/base/slstr/slstr_data.py:564)、[`read_extracted_product(path)`](C:/work/ls4t/base/slstr/slstr_data.py:589) | 每视角目录，各原生字段单独 GeoTIFF | 使不同分辨率网格暂不混为一个多波段文件；读取无规范 metadata 时从目录/景名推导 view/time |
| [`write_auxiliary_product(path,fields)`](C:/work/ls4t/base/slstr/slstr_data.py:437)、[`read_auxiliary_product(path,shape=None)`](C:/work/ls4t/base/slstr/slstr_data.py:450)、[`add_lst_auxiliary(item,auxiliary_file)`](C:/work/ls4t/base/slstr/slstr_data.py:316) | 六字段 `soil_emissivity_s8/s9`、`vegetation_emissivity_s8/s9`、lai、tcwv_cm；命名波段 TIFF或逐字段目录→dict/完整DATA | 读辅助时校验 shape；只附加现成已配准场，记录 auxiliary_source |
| [`write_data_product(path,item,*,reference_path=None)`](C:/work/ls4t/base/slstr/slstr_data.py:639)、[`read_data_product(path)`](C:/work/ls4t/base/slstr/slstr_data.py:680) | 统一二维 DATA↔命名波段 GeoTIFF | schema检查，保留单位、源、视角、时间、辅助来源；DATA是观测产品，不是LST |
| [`write_lst_product(path,product,*,reference_path=None)`](C:/work/ls4t/base/slstr/slstr_data.py:716)、[`read_lst_product(path)`](C:/work/ls4t/base/slstr/slstr_data.py:744) | 温度产品↔TIFF，`variable__*`、quality_flag、`uncertainty__*` | 温度产品schema与DATA分开；公共 IO |
| [`describe_data_product(item)`](C:/work/ls4t/base/slstr/slstr_data.py:777) | 对象→source/view/shape/time/辅助状态 dict | 状态查看，无新物理计算 |
| [`retrieve_slstr_lst(item,coefficient_file=None)`](C:/work/ls4t/base/slstr/slstr_lst.py:60) | 完整 DATA→公共分裂窗结果 | S8/S9及辅助字段映射；共同核心包装器 |
| [`produce_slstr_lst(input_path,output_path,coefficient_file=None,auxiliary_file=None,*,grid_id,algorithm_version,uncertainty_k,start_time=None,end_time=None)`](C:/work/ls4t/base/slstr/slstr_lst.py:83) | DATA→L2LST TIFF | 提供/补充时间、来源、QC；不确定度要求正数但为常量字段。 [合成 299 K 产品链测试](C:/work/ls4t/tests/test_slstr_products.py:54)，依赖 GDAL 时可能 skip，不是实测精度验证 |

公共批处理接口（均为文件编排，不新增方法）：

- [`slstr_unzip(indir_zip,outdir_raw,years,overwrite,start_index)`](C:/work/ls4t/base/slstr/slstr_unzip.py:28)；[`slstr_extract(indir_raw,outdir_extract,years,views,overwrite)`](C:/work/ls4t/base/slstr/slstr_extract.py:23)，默认参数均 None。
- [`slstr_reconstruct(indir_extract=None,outdir_reconstruct=None,years=None,overwrite=None)`](C:/work/ls4t/base/slstr/slstr_reconstruct.py:22)：扫描 `bt8.tif` 所在提取目录，调用前述几何对齐，输出 DATA TIFF。
- [`slstr_lst(indir_data=None,outdir_lst=None,coefficient_file=None,auxiliary_file=None,years=None,grid_id=None,algorithm_version=None,uncertainty_k=None,overwrite=None,input_year_template=None)`](C:/work/ls4t/base/slstr/slstr_lst.py:144)：默认 `{year}/reconstruct`→`{year}/lst`。
- `slstr_data.py` 末尾的同名 `slstr_unzip/extract/reconstruct/project/merge` 是转调阶段模块的兼容入口，不应重复计数。

实际 [cases/slstr/slstr_lst_scene.py](C:/work/ls4t/cases/slstr/slstr_lst_scene.py:198) 顶层场景计算使用 `f=1-exp(-0.825*LAI*0.5)`、`F=0.05`，与公共核心默认方向FVC、`F=0.75`不同。它还包含 BT/VZA/经纬度 /100 解码、土地类型掩膜、栅格抽样及 `LST*100` uint16输出；不能将公共入口存在视作该生产脚本已统一。

## 6. MSG/SEVIRI：公共入口与案例昼夜实现

| 函数与源码 | 输入→输出/实际计算 | 限制与状态 |
|---|---|---|
| [`read_native_product(input_path,static_file=None)`](C:/work/ls4t/base/msg/msg_data.py:113) | Satpy `seviri_l1b_native`、`fill_disk=True`，IR_108/120以brightness_temperature读入→`MsgDataProduct` | `bt8/bt9`名字虽无`_k`，内容是K；静态TIFF必须给经纬度和VZA。cloud从静态文件取，缺省全False；没有内建动态云检测。时间由文件名取，start=end |
| [`add_lst_auxiliary(item,auxiliary_file)`](C:/work/ls4t/base/msg/msg_data.py:150)、[`write_auxiliary_product(path,fields)`](C:/work/ls4t/base/msg/msg_data.py:166) | 六辅助字段GeoTIFF；108/120土壤和植被发射率、lai、tcwv_cm | 广播到同形；schema检查；现成辅助场 IO |
| [`write_data_product(path,item,*,reference_path=None)`](C:/work/ls4t/base/msg/msg_data.py:177)、[`read_data_product(path)`](C:/work/ls4t/base/msg/msg_data.py:213) | DATA↔命名波段TIFF | 规范化 bt108/bt120等别名；二维同形检查 |
| [`msg_extract(indir_raw,outdir_data,static_file,years,months,days,overwrite)`](C:/work/ls4t/base/msg/msg_data.py:242) | 参数均默认None；按日期从`.nat`产生`.tif` | 公共批处理 |
| [`retrieve_msg_lst(item,coefficient_file=None)`](C:/work/ls4t/base/msg/msg_lst.py:35) | 完整 DATA→公共分裂窗结果 | 单系数文件；此入口没有自动昼夜判别 |
| [`produce_msg_lst(input_path,output_path,coefficient_file=None,auxiliary_file=None,grid_id=None,algorithm_version=None,uncertainty_k=None)`](C:/work/ls4t/base/msg/msg_lst.py:55) | DATA→L2LST TIFF，lst/lat/lon/QC/常量uncertainty | 默认1 K为配置；不是由算法估计的不确定度 |
| [`msg_lst(indir_data,outdir_lst,coefficient_file,auxiliary_file,years,months,days,overwrite)`](C:/work/ls4t/base/msg/msg_lst.py:107) | 参数均默认None；年月日遍历 | 公共包装器 |

独立保留的案例函数（仍是同一八特征家族的配置变体，不能和公共入口默认为数值等价）：

| 案例函数与源码 | 输入→输出与算法 | 证据/边界 |
|---|---|---|
| [`retrieve_lst(bt108,bt120,view_zenith,tcwv_cm,soil_emissivity108,soil_emissivity120,vegetation_emissivity108,vegetation_emissivity120,lai,land_mask,day_mask,coefficients_day,coefficients_night)`](C:/work/ls4t/cases/msg/msg_lst_fit.py:213) | 同形二维观测+掩膜+两张 `(66,8)`系数表→float32 K；`f=1-exp(-0.825*LAI*0.5)`、散射0.05；逐像元由day_mask选表，水汽分箱+VZA系数插值；220–365K外NaN | 案例实现；VZA右端点80不包含，与公共模型最末节点策略不同；参数没有cloud_mask；[昼夜选择合成测试](C:/work/ls4t/tests/test_msg_case_dependencies.py:185) |
| [`load_coefficients(path)`](C:/work/ls4t/cases/msg/msg_lst_fit.py:133) | 文本8列或截取2:10→系数矩阵 | 检查形状，非拟合 |
| [`load_lai(path)`](C:/work/ls4t/cases/msg/msg_lst_fit.py:142) | HDF5 LAI→无量纲场 | 按 SCALING_FACTOR 除，MISSING_VALUE→NaN，范围0–10 |
| [`load_tcwv_slice(root,timestamp)`](C:/work/ls4t/cases/msg/msg_lst_fit.py:158) | 日HDF5的小时data→cm场 | `_FillValue`屏蔽；raw×scale_factor/10；非整点时邻小时线性插值含跨日；[缩放测试](C:/work/ls4t/tests/test_msg_case_dependencies.py:169) |
| [`solar_day_mask(timestamp,latitude,longitude)`](C:/work/ls4t/cases/msg/msg_lst_fit.py:183) | UTC时间、度制经纬度→bool日夜场 | 根据年内日、时角、赤纬估算cos太阳天顶角>0；用于系数路由，不是云判别 |
| [`read_native_brightness_temperatures(path)`](C:/work/ls4t/cases/msg/msg_lst_fit.py:317)、[`read_brightness_temperatures(path,input_format)`](C:/work/ls4t/cases/msg/msg_lst_fit.py:333) | native/既有TIFF读取通道BT | input_format为native/geotiff/auto；TIFF使用bt8/bt9配对且除100解码，非LST反演 |

## 7. MODIS、VIIRS、AHI、ASTER：四套名称、一个共用实现

| 传感器 | 数据定义/通道 | 直接LST入口 | 当前实际能力 |
|---|---|---|---|
| MODIS | [`ModisDataProduct`、SPEC](C:/work/ls4t/base/modis/modis_data.py:17)；31/32；准备键bt31_k/bt32_k | [`retrieve_modis_lst(item,coefficient_file=None)`](C:/work/ls4t/base/modis/modis_lst.py:11) | prepared数组→公共分裂窗；不等同于官方MODIS LST算法/产品读取 |
| VIIRS | [`ViirsDataProduct`、SPEC](C:/work/ls4t/base/viirs/viirs_data.py:17)；M15/M16；bt_m15_k/bt_m16_k，也接受bt15_k/bt16_k | [`retrieve_viirs_lst(item,coefficient_file=None)`](C:/work/ls4t/base/viirs/viirs_lst.py:7) | 相同核心，尚不能以此声称原始VIIRS granule链已验证 |
| AHI | [`AhiDataProduct`、SPEC](C:/work/ls4t/base/ahi/ahi_data.py:17)；14/15；bt14_k/bt15_k | [`retrieve_ahi_lst(item,coefficient_file=None)`](C:/work/ls4t/base/ahi/ahi_lst.py:7) | 相同核心；不是HSD原始解包读取器 |
| ASTER | [`AsterDataProduct`、SPEC](C:/work/ls4t/base/aster/aster_data.py:17)；13/14；bt13_k/bt14_k | [`retrieve_aster_lst(item,coefficient_file=None)`](C:/work/ls4t/base/aster/aster_lst.py:7) | 配置式双通道分裂窗；本模块没有多通道TES温度发射率分离算法 |

四个包共同提供以下函数，均转调 `base.dual_thermal`，其中 `s`依次取`modis/viirs/ahi/aster`，名称展开后即实际函数名：

| 实际接口族 | 关键参数/输出 | 共用函数体 |
|---|---|---|
| `read_native_product(path)` | 只接收已解码K的准备NPZ/TIFF→对应Product；存在键别名、传感器检查，必须带start/end；缺cloud则全False | [`read_prepared_product(path,spec,product_type)`](C:/work/ls4t/base/dual_thermal.py:144) |
| `read_data_product(path)`、`write_data_product(path,item)` | 标准DATA对象↔NPZ或命名波段TIFF；二维同形，BT有限值须在100–500K | [`read_data_product(path,spec,product_type)`](C:/work/ls4t/base/dual_thermal.py:256)、[`write_data_product(path,item,spec)`](C:/work/ls4t/base/dual_thermal.py:196)、[validate](C:/work/ls4t/base/dual_thermal.py:93) |
| `add_lst_auxiliary(item,auxiliary_file)` | soil/vegetation_emissivity_1/2、lai、tcwv_cm；标量可广播；输出完整对象 | [`add_lst_auxiliary`](C:/work/ls4t/base/dual_thermal.py:293) |
| `modis_extract/viirs_extract/ahi_extract/aster_extract(indir_raw=None,outdir_data=None,years=None,months=None,days=None,overwrite=None)` | 日期目录prepared输入→DATA | [`extract_sensor_products(spec,product_type,*,...)`](C:/work/ls4t/base/dual_thermal.py:319) |
| `produce_modis_lst/produce_viirs_lst/produce_ahi_lst/produce_aster_lst(input_path=None,output_path=None,coefficient_file=None,auxiliary_file=None,grid_id=None,algorithm_version=None,uncertainty_k=None)` | DATA→L2LST产品；默认uncertainty=1K | [`produce_sensor_lst(input_path,output_path,spec,product_type,coefficient_file,auxiliary_file,grid_id=None,algorithm_version=None,uncertainty_k=None)`](C:/work/ls4t/base/dual_thermal.py:502) |
| `modis_lst/viirs_lst/ahi_lst/aster_lst(indir_data=None,outdir_lst=None,coefficient_file=None,auxiliary_file=None,years=None,months=None,days=None,grid_id=None,algorithm_version=None,uncertainty_k=None,overwrite=None)` | 日期目录遍历、单景产出 | [`retrieve_sensor_years(spec,product_type,*,...)`](C:/work/ls4t/base/dual_thermal.py:559) |
| `retrieve_*_lst` | 检查传感器/辅助字段并映射公共观测→分裂窗 | [`retrieve_sensor_lst(item,spec,coefficient_file)`](C:/work/ls4t/base/dual_thermal.py:476) |

直接测试：[四传感器prepared 2×3合成往返](C:/work/ls4t/tests/test_dual_thermal_sensors.py:46)、[错sensor拒绝](C:/work/ls4t/tests/test_dual_thermal_sensors.py:87)、[MODIS日期提取](C:/work/ls4t/tests/test_dual_thermal_sensors.py:126)、[MODIS小角度拼接](C:/work/ls4t/tests/test_dual_thermal_sensors.py:161)、[MODIS合成均温299K](C:/work/ls4t/tests/test_dual_thermal_sensors.py:173)。这些测试不能证明四传感器原始定标、系数适用性或真实LST精度。

## 8. 投影、拼接、区域产品：属于准备与产品组织

| 函数与源码 | 接口/运算 | 适用边界 |
|---|---|---|
| [`project_product(item,target_grid_file,projection_chunk_size=None,cloud_fraction_threshold=None)`](C:/work/ls4t/base/slstr/slstr_project.py:90) | SLSTR经纬度→目标CRS→目标像元索引；对BT、角度、经纬度、辅助场分别聚合；cloud比例>阈值或无样本为云 | 默认chunk=100000、cloud阈值0；不是物理下推，也不是DL超分辨；目标格网需显式提供 |
| [`project_aatsr_product(...)`](C:/work/ls4t/base/aatsr/aatsr_project.py:22)、[`project_msg_product(...)`](C:/work/ls4t/base/msg/msg_project.py:22)、[`project_modis_product(...)`](C:/work/ls4t/base/modis/modis_project.py:9)、`project_viirs_product/project_ahi_product/project_aster_product` | 同签名 `(item,target_grid_file=None,projection_chunk_size=None,cloud_fraction_threshold=None)`；转调`base.spatial.project_observation` | 公共投影包装；不独立计数 |
| `aatsr_project/msg_project` | `(indir_data,outdir_project,target_grid_file,years,months,days,projection_chunk_size,cloud_fraction_threshold,overwrite)`默认None | 日期目录处理 |
| `modis_project/viirs_project/ahi_project/aster_project` | 对应参数首项为`indir_extract`；转调 [`project_sensor_products`](C:/work/ls4t/base/dual_thermal.py:360) | 输入实际上是已标准化观测，不能直接传原始任务文件 |
| [`slstr_merge(indir_project=None,outdir_merge=None,years=None,overwrite=None)`](C:/work/ls4t/base/slstr/slstr_merge.py:29) | 按日期+view分组，`_merge_products`→`mosaic_observations(primary_field='bt8_k')` | 日内同视角拼接；案例仍应控制过境分组；[低VZA选择测试](C:/work/ls4t/tests/test_slstr_products.py:100) |
| [`aatsr_data_region/aatsr_result_region`](C:/work/ls4t/base/aatsr/aatsr_region.py:42)、[`slstr_data_region/slstr_result_region`](C:/work/ls4t/base/slstr/slstr_region.py:44)、[`msg_data_region/msg_result_region`](C:/work/ls4t/base/msg/msg_region.py:41) | 均`(input_paths=None,output_path=None,bounds=None)`；DATA先拼/裁再反演，或RESULT先反演再拼/裁；bounds西南东北 | 输入必须已同格网；不能混无关视角/时段。结果路径还可容纳组件温度，但拼接本身不是LSCT算法 |
| `modis_merge/viirs_merge/ahi_merge/aster_merge`，各`*_data_region/*_result_region` | 同样三参数；分别调用[`merge_sensor_data`](C:/work/ls4t/base/dual_thermal.py:444)/[`merge_sensor_results`](C:/work/ls4t/base/dual_thermal.py:459)；`combine_data_products(input_paths,spec,product_type,bounds=None)`在[428行](C:/work/ls4t/base/dual_thermal.py:428) | 共用机械操作；结果拼接核对sensor，按需裁剪 |

[tests/test_spatial_modes.py](C:/work/ls4t/tests/test_spatial_modes.py:57)存在观测晴空/小VZA优选、缺VZA拒绝、结果小不确定度优选及裁剪测试。它们验证选择与空间操作，不验证分裂窗实测误差。

## 9. 反射率相关功能：真实存在的范围

| 位置/函数 | 读入与输出 | 能力归属与不得推定的内容 |
|---|---|---|
| [cases/aatsr/aatsr_data.py 可见光读取段](C:/work/ls4t/cases/aatsr/aatsr_data.py:156) | EPR `reflec_nadir_0670/0870`、`reflec_fward_0670/0870`；源码注明已是百分数反射因子 | 案例内L1波段读取；该段无气溶胶/水汽/路径辐射大气校正，不能据`reflec`认定地表反射率 |
| [`aatsr_read_sites_obs(infile,ifNDVI=1)`](C:/work/ls4t/cases/aatsr/util_aatsr.py:80) | HDF5 nirN/nirF/redN/redF；ifNDVI=1返回两视角 `(NIR-red)/(NIR+red)`；否则四光学数组 | NDVI裁到[-1,1]，任一输入0置NaN；尽管读取并计算云掩膜，该函数返回NDVI时未使用云掩膜。案例读数/指数工具 |
| [`aatsr_read_NDVI(infile_obs)`](C:/work/ls4t/cases/aatsr/util_aatsr.py:154) | 四光学数组先/10再比值；返回ndviN/ndviF | 同比例缩放在比值中抵消；NDVI不等于大气校正后的反射率产品 |
| [cases/slstr/slstr_data_scene.py](C:/work/ls4t/cases/slstr/slstr_data_scene.py:363) | S2/S3 radiance、solar_irradiance；`refl=π*radiance/solar_irradiance[0]`，resize，×10000、clip、uint16→red/nir TIFF；oblique有相应段 | 现存辐亮度归一化反射因子；已读公式没有太阳天顶角余弦项，也无地表大气校正；仅按代码公式登记，不能标为完整TOA标准校正或SR反演 |
| [cases/msg/msg_extract_euro.py](C:/work/ls4t/cases/msg/msg_extract_euro.py:150)、[msg_extract_iodc.py](C:/work/ls4t/cases/msg/msg_extract_iodc.py:151) | Satpy `calibration='reflectance'`加载VIS006/VIS008/IR_016；输出红/近红外×100 uint16；EURO段按7<hour<19运行 | 原始辐射定标/光学提取；没有后续SR大气校正函数；时段筛选不能代替逐像元日照判别 |
| [base/rt/scatter.py](C:/work/ls4t/base/rt/scatter.py:19)参数`refl_soil/refl_leaf` | 反射参数被前向辐射传输使用 | 不是由卫星观测反演地表反射率；属于前向模型依赖，不能当成卫星SR产品方法 |

对公共 `base` 及非归档 `cases` 的反射关键词检索，再读取以上命中函数体后，未确认独立 `retrieve_surface_reflectance`、可运行的大气校正参数反演或通用SR产品schema。归档中存在其他反射关键词、下载脚本不改变此判定；本清单不声称对仓库外实现做了排除。建议在既定四层分类中把SR保留为“产品方向，现有子能力为光学读取/反射因子/NDVI”，而不是填报一个已经完成的反演方法。

## 10. 跨层关联与证据强度

- 卫星层公共链：原始/准备观测→DATA→辅助发射率/LAI/水汽→公共分裂窗→L2LST；投影、裁剪、拼接可按场景/区域顺序编排。
- LSCT是细化层，`base/*/*_lsct.py`入口应在细化清单展开；不能因同属传感器目录而把组件分解记成独立的单像元LST算法。
- `tests/test_msg_evo_sample.py`的真实月样本验证是已有LST输入的组件解算与邻域最小二乘一致性，不是这里的分裂窗从L1反演LST的地面验证。同理SLSTR EVO组件案例不能自动证明所有公共读取器和系数对真实场景有效。
- 当前明确证据分为：源码实现；合成数值/IO测试；案例中实际调用/重复公式。本文未提供独立地面LST对照精度、SR地面验证、传感器系数跨场景泛化结论。
- 本轮仅盘点；没有迁移函数、统一默认散射参数、变更编码、替换案例系数或运行生产任务。

