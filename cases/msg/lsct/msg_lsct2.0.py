import os

import matplotlib.pyplot as plt
import numpy as np
from scipy.ndimage import uniform_filter
from base.util_data import *
from base.util_lsct import *
from base.util_file import *
from base.util_plot import *


def planck(wavelength, Ts):
    '''
    基于planck公式，计算某个波长时候，从温度到辐射的转换
    :param wavelength: 波长，10.5
    :param Ts: 温度，可以是亮温，也可以是摄氏度
    :return: 辐射
    '''
    c1 = planck_c1
    c2 = planck_c2
    if np.isscalar(Ts):
        if Ts < temperature_threshold:
            Ts = Ts + temperature_zero
        wavelength = np.float64(wavelength)
        Ts = float(Ts)
        rad = c1 / (np.power(wavelength, 5) * (np.exp(c2 / Ts / wavelength) - 1)) * 10000
    else:
        Ts = np.array(Ts, dtype=np.float64)
        Ts[Ts < temperature_threshold] = Ts[Ts < temperature_threshold] + temperature_zero
        wavelength = float(wavelength)
        rad = c1 / (np.power(wavelength, 5) * (np.exp(c2 / Ts / wavelength) - 1)) * 10000
    return rad

def inv_planck(wavelength, rad):
    c1 = planck_c1 * 10000
    c2 = planck_c2
    # 过滤掉非正值辐射
    with np.errstate(invalid='ignore', divide='ignore'):
        temp = c1 / (rad * np.power(wavelength, 5)) + 1
        # 只有在 temp > 1 时 log 才有意义
        Ts = np.where(temp > 1, c2 / (wavelength * np.log(temp)), np.nan)
    return Ts

# --- 求解函数：3x3 最小二乘法 ---
def solve_3x3_least_squares(rad_euro, rad_iodc, w):
    # w shape: (H, W, 4)
    w0, w1, w2, w3 = w[..., 0], w[..., 1], w[..., 2], w[..., 3]

    # --- 1. 处理 NaN 值 ---
    # 记录原始无效位置（LST为空或权重为空的地方）
    invalid_mask = np.isnan(rad_euro) | np.isnan(rad_iodc) | np.isnan(w0)

    # 为了防止 uniform_filter 扩散 NaN，先将所有变量的 NaN 替换为 0
    # 但我们稍后需要除以“有效像素个数”来修正总和
    def clean_nan(img):
        return np.nan_to_num(img, nan=0.0)

    # --- 2. 计算点对点乘积 (清理后的) ---
    term_A = clean_nan(w0 ** 2 + w2 ** 2)
    term_B = clean_nan(w0 * w1 + w2 * w3)
    term_C = clean_nan(w1 ** 2 + w3 ** 2)
    term_D1 = clean_nan(w0 * rad_euro + w2 * rad_iodc)
    term_D2 = clean_nan(w1 * rad_euro + w3 * rad_iodc)

    # 构造一个权重计数器：有效像素记为 1，无效记为 0
    valid_count = clean_nan(np.where(invalid_mask, 0.0, 1.0))

    # --- 3. 窗口求和 (解决 NaN 扩散) ---
    def box_sum(img):
        # 使用 'nearest' 避免边缘补0干扰。
        # uniform_filter 计算的是均值，所以乘 9 得到总和。
        # 如果窗口内有无效值，这种方法计算的是“窗口内有效值的总和”。
        return uniform_filter(img, size=3, mode='nearest') * 9.0

    # 这里的 sum 实际上是窗口内所有有效像素的累加
    sum_A = box_sum(term_A)
    sum_B = box_sum(term_B)
    sum_C = box_sum(term_C)
    sum_D1 = box_sum(term_D1)
    sum_D2 = box_sum(term_D2)

    # 计算每个窗口实际包含的有效像素个数
    n_valid = box_sum(valid_count)

    # --- 4. 求解 ---
    # 行列式
    det = sum_A * sum_C - sum_B ** 2

    with np.errstate(divide='ignore', invalid='ignore'):
        bv_rad = (sum_D1 * sum_C - sum_D2 * sum_B) / det
        bs_rad = (sum_D2 * sum_A - sum_D1 * sum_B) / det

    # --- 5. 结果清理 ---
    # 条件 A: 行列式太小（奇异矩阵）
    # 条件 B: 窗口内有效像素太少（例如少于 3 个，不足以支撑最小二乘）
    # 条件 C: 原始像素本身就是无效的
    final_mask = (np.abs(det) < 1e-8) | (n_valid < 3) | invalid_mask

    bv_rad[final_mask] = np.nan
    bs_rad[final_mask] = np.nan

    return bv_rad, bs_rad


import numpy as np
from scipy.ndimage import uniform_filter


def solve_5x5_least_squares_robust(rad_euro, rad_iodc, w):
    # w0, w2 -> 土壤系数; w1, w3 -> 植被系数
    w0, w1, w2, w3 = w[..., 0], w[..., 1], w[..., 2], w[..., 3]

    invalid_mask = np.isnan(rad_euro) | np.isnan(rad_iodc) | np.isnan(w0)

    def clean_nan(img):
        return np.nan_to_num(img, nan=0.0)

    # A11: 土壤相关项, A22: 植被相关项, A12: 耦合项
    term_A11 = clean_nan(w0 ** 2 + w2 ** 2)
    term_A12 = clean_nan(w0 * w1 + w2 * w3)
    term_A22 = clean_nan(w1 ** 2 + w3 ** 2)

    # B1: 土壤观测向量项, B2: 植被观测向量项
    term_B1 = clean_nan(w0 * rad_euro + w2 * rad_iodc)
    term_B2 = clean_nan(w1 * rad_euro + w3 * rad_iodc)

    valid_count = clean_nan(np.where(invalid_mask, 0.0, 1.0))

    def box_sum_5x5(img):
        return uniform_filter(img, size=5, mode='nearest') * 25.0

    sum_A11 = box_sum_5x5(term_A11)
    sum_A12 = box_sum_5x5(term_A12)
    sum_A22 = box_sum_5x5(term_A22)
    sum_B1 = box_sum_5x5(term_B1)
    sum_B2 = box_sum_5x5(term_B2)

    n_valid = box_sum_5x5(valid_count)
    det = sum_A11 * sum_A22 - sum_A12 ** 2

    with np.errstate(divide='ignore', invalid='ignore'):
        # 根据克莱姆法则：
        # x1 (土壤) = (B1 * A22 - B2 * A12) / det
        # x2 (植被) = (B2 * A11 - B1 * A12) / det
        bs_rad = (sum_B1 * sum_A22 - sum_B2 * sum_A12) / det
        bv_rad = (sum_B2 * sum_A11 - sum_B1 * sum_A12) / det

    final_mask = (np.abs(det) < 1e-8) | (n_valid < 5) | invalid_mask

    bs_rad[final_mask] = np.nan
    bv_rad[final_mask] = np.nan

    # 物理合理性检查：辐射必须大于0
    bs_rad[bs_rad <= 0] = np.nan
    bv_rad[bv_rad <= 0] = np.nan

    return bs_rad, bv_rad  # 这样返回：第一个是植被，第二个是土壤

# ================= 配置路径 =================
indir = "/Users/bianzj/Downloads/data/"
indir0_euro = indir + '/PRODUCTS/MSG/MLST/GEOTIFF'
indir0_iodc = indir + '/PRODUCTS/MSG-IODC/MLST/GEOTIFF'
indir0_lai = indir + '/lai/'
outdir_root = indir + '/PRODUCTS/LSCT/MLST_COMPONENT/'

# ================= 读取静态数据 =================
print("正在读取静态数据及坐标映射...")
infile_source = indir + "/map/MCD12C1_2011_0.01.tif"
infile_vza_e = indir + "/msg/static/combined_euro_vza.tif"
infile_vaa_e = indir + "/msg/static/combined_euro_vaa.tif"
infile_vza_i = indir + "/msg/static/combined_iodc_vza.tif"
infile_vaa_i = indir + "/msg/static/combined_iodc_vaa.tif"

# 读取并校正角度
[vza_euro, nss, nll, nb, _, _, dataset_ref] = read_image_dataset_gdal(infile_vza_e)
[vaa_euro, _, _, _, _, _, _] = read_image_dataset_gdal(infile_vaa_e)
[vza_iodc, _, _, _, _, _, _] = read_image_dataset_gdal(infile_vza_i)
[vaa_iodc, _, _, _, _, _, _] = read_image_dataset_gdal(infile_vaa_i)

vza_euro, vaa_euro = vza_euro / 100.0, vaa_euro / 100.0
vza_iodc, vaa_iodc = vza_iodc / 100.0, vaa_iodc / 100.0

# 坐标转换映射 (用于提取土地利用类型和发射率)
ns, nl = nss, nll
nsi, nli = np.meshgrid(np.arange(ns), np.arange(nl))
nli_flat, nsi_flat = nli.flatten(), nsi.flatten()

temp1, temp2 = imagexy2geo(dataset_ref, nli_flat, nsi_flat)
lon, lat = geo2lonlat(dataset_ref, temp1, temp2)
lon, lat = lon.reshape(nl, ns), lat.reshape(nl, ns)

[land_type_map, _, _, _, _, _, dataset_map] = read_image_dataset_gdal(infile_source)
indx, indy = loc2map(lat, lon, dataset_map)
indx, indy = indx.reshape(nll, nss), indy.reshape(nll, nss)
land_type = land_type_map[indx, indy].astype(np.int16)

# 读取发射率
indir_ems = indir + '/lse/'
infile_soil_emis = indir_ems + 'emis1.tif'
infile_veg_emis = indir_ems + 'IGBP_Emi.txt'
[emis_s_full, _, _, _, _, _] = read_image_gdal(infile_soil_emis)
emis_s = emis_s_full[indx, indy]
if np.nanmean(emis_s[emis_s > 0]) > 1.0:
    emis_s = emis_s / 1000.0

emis_v_table = read_txt_array(infile_veg_emis, 0, 2)
# 修正：根据 IGBP 类型索引对应的植被发射率
emis_v = emis_v_table[land_type, 0] / 1000.0

# ================= 循环处理 =================
isfirst = True
for kyear in range(2017, 2018):
    for kmonth in range(8, 9):
        for kday in range(10, 11):

            # --- 1. 处理 LAI 和 权重 w ---
            kdoy = date2DOY(kyear, kmonth, kday)
            kkdoy = int(kdoy / 4) * 4 + 1
            infile_lai = os.path.join(indir0_lai, "%04d" % kyear, "lai_%04d%03d.tif" % (kyear, kkdoy))

            if isfirst or (kkdoy == kdoy):
                if os.path.exists(infile_lai):
                    lai, _, _, _, _, _ = read_image_gdal(infile_lai)
                    lai = lai[indx, indy] / 1000.0
                    lai[lai > 30] = np.nan
                    lai[lai < 0] = 0

                    # 计算 FVC 和 权重 w
                    fvc_euro = 1.0 - gap_probability_hom_analytical(lai, vza_euro)
                    fvc_iodc = 1.0 - gap_probability_hom_analytical(lai, vza_iodc)

                    w = np.zeros([nll, nss, 4])
                    w[:, :, 0] = emis_s * (1.0 - fvc_euro)  # Soil Euro
                    w[:, :, 1] = emis_v * fvc_euro  # Veg Euro
                    w[:, :, 2] = emis_s * (1.0 - fvc_iodc)  # Soil IODC
                    w[:, :, 3] = emis_v * fvc_iodc  # Veg IODC
                    isfirst = False
                else:
                    print(f"警告: 找不到 LAI 文件 {infile_lai}")
                    continue

            # --- 2. 设置目录 ---
            indir_euro = os.path.join(indir0_euro, "%04d" % kyear, "%02d" % kmonth, "%02d" % kday)
            indir_iodc = os.path.join(indir0_iodc, "%04d" % kyear, "%02d" % kmonth, "%02d" % kday)
            outdir = os.path.join(outdir_root, "%04d" % kyear, "%02d" % kmonth, "%02d" % kday)
            if not os.path.exists(outdir):
                os.makedirs(outdir)

            # --- 3. 逐小时处理 ---
            for khour in range(11, 12):
                file_id = "%04d%02d%02d%02d00" % (kyear, kmonth, kday, khour)
                infile_e = os.path.join(indir_euro, f"HDF5_LSASAF_MSG_LST_MSG-Disk_{file_id}.tif")
                infile_i = os.path.join(indir_iodc, f"HDF5_LSASAF_MSG-IODC_LST_IODC-Disk_{file_id}.tif")

                if not (os.path.exists(infile_e) and os.path.exists(infile_i)):
                    continue

                print(f"正在处理: {file_id}")
                lst_e, _, _, _, _, _ = read_image_gdal(infile_e)
                lst_i, _, _, _, _, _ = read_image_gdal(infile_i)

                # 数据清洗：处理无效值 (0, NaN, 水体类型等)
                # 修正屏蔽逻辑：这里建议根据各产品自身的 fillvalue 处理
                bad_mask = (lst_e <= 0) | (lst_i <= 0) | np.isnan(lst_e) | np.isnan(lst_i) | (land_type == 0) | (
                            land_type > 17)

                lst_e = lst_e / 100.0 + 273.15
                lst_i = lst_i / 100.0 + 273.15
                lst_e[bad_mask] = np.nan
                lst_i[bad_mask] = np.nan

                # 计算总辐射
                rad_e = planck(10.5, lst_e) * (w[:, :, 0] + w[:, :, 1])
                rad_i = planck(10.5, lst_i) * (w[:, :, 2] + w[:, :, 3])

                # --- 4. 求解组件辐射 (建议使用 3x3 最小二乘法，更稳健) ---
                bs_rad, bv_rad = solve_5x5_least_squares_robust(rad_e, rad_i, w)

                # w0 = w[:, :, 0]
                # w1 = w[:, :, 1]
                # w2 = w[:, :, 2]
                # w3 = w[:, :, 3]
                # det = w0 * w3 - w1 * w2
                # # 2. 为了防止除以 0（例如无效像素或系数全为0），可以使用 np.errstate 或加上极小值
                # # 或者直接在计算后处理 Inf/NaN
                # with np.errstate(divide='ignore', invalid='ignore'):
                #     # 3. 快速求解 bv 和 bs
                #     bv_rad = (rad_e * w3 - rad_i * w1) / det
                #     bs_rad = (rad_i * w0 - rad_e * w2) / det


                # --- 5. 反演温度 ---
                with np.errstate(invalid='ignore'):
                    tv = inv_planck(10.5, bv_rad)
                    ts = inv_planck(10.5, bs_rad)

                # --- 6. 保存结果 ---
                out_file_v = os.path.join(outdir, f"TV_{file_id}.tif")
                out_file_s = os.path.join(outdir, f"TS_{file_id}.tif")

                trans = dataset_ref.GetGeoTransform()
                proj = dataset_ref.GetProjection()

                plt.imshow(ts-tv,cmap='RdBu',vmax = 25, vmin = -25)
                plt.colorbar()
                plt.show()

                # 将结果限制在合理范围并处理异常
                tv[(tv < 200) | (tv > 350)] = np.nan
                ts[(ts < 200) | (ts > 380)] = np.nan

                write_image_gdal(tv.astype(np.float32), nss, nll, 1, trans, proj, out_file_v)
                write_image_gdal(ts.astype(np.float32), nss, nll, 1, trans, proj, out_file_s)

print("批量处理任务全部完成。")