import os

import matplotlib.pyplot as plt
import numpy as np
from scipy.ndimage import uniform_filter
from base.util_data import *
from base.util_lsct import *
from base.util_file import *
from base.util_plot import *
import pvlib
from pvlib.location import Location
from osgeo import gdal
from osgeo import osr
import os
import pyresample as pr
from satpy import Scene
import satpy

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



import numpy as np
from scipy.ndimage import uniform_filter


def solve_5x5_three_components(rad_euro, rad_iodc, w):
    """
    求解三组分模型: w1*bs1 + w2*bs2 + w3*bv = rad_e
                  w4*bs1 + w5*bs2 + w6*bv = rad_i
    w shape: (H, W, 6)
    """
    # 1. 提取 6 个系数
    w1, w2, w3 = w[..., 0], w[..., 1], w[..., 2]
    w4, w5, w6 = w[..., 3], w[..., 4], w[..., 5]

    # --- 2. 处理 NaN (防止扩散) ---
    invalid_mask = np.isnan(rad_euro) | np.isnan(rad_iodc) | np.isnan(w1)

    def clean_nan(img):
        return np.nan_to_num(img, nan=0.0)

    # --- 3. 计算 A^T * A (3x3 对称矩阵的 6 个独立元素) ---
    # M11 = sum(w1^2 + w4^2), M12 = sum(w1*w2 + w4*w5) ...
    m11_p = clean_nan(w1 ** 2 + w4 ** 2)
    m12_p = clean_nan(w1 * w2 + w4 * w5)
    m13_p = clean_nan(w1 * w3 + w4 * w6)
    m22_p = clean_nan(w2 ** 2 + w5 ** 2)
    m23_p = clean_nan(w2 * w3 + w5 * w6)
    m33_p = clean_nan(w3 ** 2 + w6 ** 2)

    # --- 4. 计算 A^T * b (3x1 向量的 3 个元素) ---
    v1_p = clean_nan(w1 * rad_euro + w4 * rad_iodc)
    v2_p = clean_nan(w2 * rad_euro + w5 * rad_iodc)
    v3_p = clean_nan(w3 * rad_euro + w6 * rad_iodc)

    valid_count = clean_nan(np.where(invalid_mask, 0.0, 1.0))

    # --- 5. 5x5 窗口空间累加 ---
    def box_sum(img):
        return uniform_filter(img, size=5, mode='nearest') * 25.0

    M11, M12, M13 = box_sum(m11_p), box_sum(m12_p), box_sum(m13_p)
    M22, M23, M33 = box_sum(m22_p), box_sum(m23_p), box_sum(m33_p)
    V1, V2, V3 = box_sum(v1_p), box_sum(v2_p), box_sum(v3_p)
    n_valid = box_sum(valid_count)

    # --- 6. 逐像素求解 3x3 方程组 ---
    # 为了速度，我们构造大矩阵进行批量求解
    # 矩阵形状 (H, W, 3, 3)
    H, W = rad_euro.shape
    A_stack = np.zeros((H, W, 3, 3))
    A_stack[..., 0, 0], A_stack[..., 0, 1], A_stack[..., 0, 2] = M11, M12, M13
    A_stack[..., 1, 0], A_stack[..., 1, 1], A_stack[..., 1, 2] = M12, M22, M23
    A_stack[..., 2, 0], A_stack[..., 2, 1], A_stack[..., 2, 2] = M13, M23, M33

    B_stack = np.zeros((H, W, 3))
    B_stack[..., 0], B_stack[..., 1], B_stack[..., 2] = V1, V2, V3

    # 计算行列式以排除不可解区域
    det = (M11 * (M22 * M33 - M23 ** 2) -
           M12 * (M12 * M33 - M13 * M23) +
           M13 * (M12 * M23 - M13 * M22))

    # 只对有效且矩阵满秩的区域求解
    solve_mask = (np.abs(det) > 1e-6) & (n_valid > 10) & (~invalid_mask)

    bs1 = np.full((H, W), np.nan)
    bs2 = np.full((H, W), np.nan)
    bv = np.full((H, W), np.nan)

    if np.any(solve_mask):
        # 批量求解 (numpy.linalg.solve 支持堆栈操作)
        results = np.linalg.solve(A_stack[solve_mask], B_stack[solve_mask])
        bs1[solve_mask] = results[:, 0]
        bs2[solve_mask] = results[:, 1]
        bv[solve_mask] = results[:, 2]

    # 物理约束清理
    final_mask = (bs1 <= 0) | (bs2 <= 0) | (bv <= 0)
    bs1[final_mask], bs2[final_mask], bv[final_mask] = np.nan, np.nan, np.nan

    return bs1, bs2, bv

# --- 辅助函数：通用的 2x2 最小二乘求解器 ---
def solve_2x2_system(rad1, rad2, w_a1, w_b1, w_a2, w_b2, size=3):
    """
    求解方程组: w_a1*X + w_b1*Y = rad1
               w_a2*X + w_b2*Y = rad2
    """
    invalid_mask = np.isnan(rad1) | np.isnan(rad2) | np.isnan(w_a1)
    def clean(img): return np.nan_to_num(img, nan=0.0)

    # 构造正规方程各项
    term_AA = clean(w_a1**2 + w_a2**2)
    term_AB = clean(w_a1*w_b1 + w_a2*w_b2)
    term_BB = clean(w_b1**2 + w_b2**2)
    term_D1 = clean(w_a1*rad1 + w_a2*rad2)
    term_D2 = clean(w_b1*rad1 + w_b2*rad2)
    valid_count = clean(np.where(invalid_mask, 0.0, 1.0))

    def box_sum(img):
        return uniform_filter(img, size=size, mode='nearest') * float(size**2)

    sAA, sAB, sBB = box_sum(term_AA), box_sum(term_AB), box_sum(term_BB)
    sD1, sD2 = box_sum(term_D1), box_sum(term_D2)
    n_v = box_sum(valid_count)

    det = sAA * sBB - sAB**2
    with np.errstate(divide='ignore', invalid='ignore'):
        X = (sD1 * sBB - sD2 * sAB) / det
        Y = (sD2 * sAA - sD1 * sAB) / det

    mask = (np.abs(det) < 1e-10) | (n_v < (size**2)/2) | invalid_mask
    X[mask], Y[mask] = np.nan, np.nan
    return X, Y
# ================= 配置路径 =================
indir = "/Users/bianzj/Downloads/data/"
indir0_euro = indir + '/PRODUCTS/MSG/MLST/GEOTIFF'
indir0_iodc = indir + '/PRODUCTS/MSG-IODC/MLST/GEOTIFF'
indir0_lai = indir + '/lai/'
outdir_root = indir + '/PRODUCTS/LSCT/MLST_COMPONENT/'
altitude = 0

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
vaa_euro = (360 + vaa_euro) % 360
vaa_iodc = (360 + vaa_iodc) % 360

# 坐标转换映射 (用于提取土地利用类型和发射率)
ns, nl = nss, nll
nsi, nli = np.meshgrid(np.arange(ns), np.arange(nl))
nli_flat, nsi_flat = nli.flatten(), nsi.flatten()

temp1, temp2 = imagexy2geo(dataset_ref, nli_flat, nsi_flat)
lon, lat = geo2lonlat(dataset_ref, temp1, temp2)
lon, lat = lon.reshape(nl, ns), lat.reshape(nl, ns)
lonn = resize_data(lon,int(nl/10),int(ns/10))
latt = resize_data(lat,int(nl/10),int(ns/10))

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
            for khour in range(15, 16):
                for kmin in range(0, 1):
                    file_id = "%04d%02d%02d%02d00" % (kyear, kmonth, kday, khour)
                    date_str = "%04d%02d%02d" % (kyear, kmonth, kday)
                    infile_e = os.path.join(indir_euro, f"HDF5_LSASAF_MSG_LST_MSG-Disk_{file_id}.tif")
                    infile_i = os.path.join(indir_iodc, f"HDF5_LSASAF_MSG-IODC_LST_IODC-Disk_{file_id}.tif")

                    if not (os.path.exists(infile_e) and os.path.exists(infile_i)):
                        continue

                    print(f"正在处理: {file_id}")
                    lst_e, _, _, _, _, _ = read_image_gdal(infile_e)
                    lst_i, _, _, _, _, _ = read_image_gdal(infile_i)

                    time_val = pd.to_datetime(f"{date_str} {khour:02d}:{kmin:02d}:00").tz_localize('UTC')
                    site_temp = Location(latt.flatten(), lonn.flatten(), 'Etc/GMT', altitude, 'None')
                    nloc = len(latt.flatten())
                    solpos_temp = pvlib.solarposition.get_solarposition(np.repeat(time_val, nloc), site_temp.latitude,
                                                                        site_temp.longitude, site_temp.altitude,
                                                                        method='nrel_numpy')
                    sza_temp = solpos_temp['zenith'].to_numpy().reshape(latt.shape).astype(np.float32)
                    saa_temp = solpos_temp['azimuth'].to_numpy().reshape(latt.shape).astype(np.float32)
                    sza = resize_data(sza_temp, nll, nss)
                    saa = resize_data(saa_temp, nll, nss)

                    vsa_euro = np.asarray(np.abs(vaa_euro - saa))
                    vsa_iodc = np.asarray(np.abs(vaa_iodc - saa))
                    w1 = hotspot_layer(lai, 0.1, vza_euro, sza, vsa_euro)
                    w2 = hotspot_layer(lai, 0.1, vza_iodc, sza, vsa_iodc)

                    w = np.zeros([nll, nss, 6])
                    w[:, :, 0] = emis_s * (w1)  # Soil Euro
                    w[:, :, 1] = emis_s * (1.0 - fvc_euro - w1)  # Veg Euro
                    w[:, :, 2] = emis_v * fvc_euro  # Soil IODC
                    w[:, :, 3] = emis_s * (w2)  # Veg IODC
                    w[:, :, 4] = emis_s * (1.0 - fvc_iodc - w2)  # Veg IODC
                    w[:, :, 5] = emis_v * fvc_iodc  # Veg IODC

                    # 数据清洗：处理无效值 (0, NaN, 水体类型等)
                    # 修正屏蔽逻辑：这里建议根据各产品自身的 fillvalue 处理
                    bad_mask = (lst_e <= 0) | (lst_i <= 0) | np.isnan(lst_e) | np.isnan(lst_i) | (land_type == 0) | (
                            land_type > 17)

                    lst_e = lst_e / 100.0 + 273.15
                    lst_i = lst_i / 100.0 + 273.15
                    lst_e[bad_mask] = np.nan
                    lst_i[bad_mask] = np.nan
                    # 计算总辐射
                    rad_e = planck(10.5, lst_e) * (w[:, :, 0] + w[:, :, 1] + w[:, :, 2])
                    rad_i = planck(10.5, lst_i) * (w[:, :, 3] + w[:, :, 4] + w[:, :, 5])

                    # ---------------------------------------------------------
                    # 步骤 A: 第一阶段求解 - 二组分模型 (土壤整体 vs 植被)
                    # ---------------------------------------------------------
                    # 合并土壤权重: W_soil = W_sunlit + W_shaded
                    w_soil_e = w[:, :, 0] + w[:, :, 1]
                    w_veg_e = w[:, :, 2]
                    w_soil_i = w[:, :, 3] + w[:, :, 4]
                    w_veg_i = w[:, :, 5]

                    # 求解整体土壤辐射 (bs_total_rad) 和 植被辐射 (bv_rad)
                    bs_total_rad, bv_rad = solve_2x2_system(rad_e, rad_i,
                                                            w_soil_e, w_veg_e,
                                                            w_soil_i, w_veg_i, size=3)

                    # ---------------------------------------------------------
                    # 步骤 B: 第二阶段求解 - 拆分土壤组分 (光照土壤 vs 阴影土壤)
                    # ---------------------------------------------------------
                    # 在已知 bv_rad 的情况下，减去植被贡献，得到纯土壤的残差辐射响应
                    with np.errstate(invalid='ignore'):
                        rad_soil_only_e = rad_e - w_veg_e * bv_rad
                        rad_soil_only_i = rad_i - w_veg_i * bv_rad

                    # 利用光照土壤(w1, w4)和阴影土壤(w2, w5)的权重关系求解 bs1 和 bs2
                    # 方程: w1*bs1 + w2*bs2 = rad_soil_only_e
                    #      w4*bs1 + w5*bs2 = rad_soil_only_i
                    bs1_rad, bs2_rad = solve_2x2_system(rad_soil_only_e, rad_soil_only_i,
                                                        w[:, :, 0], w[:, :, 1],
                                                        w[:, :, 3], w[:, :, 4], size=3)

                    # ---------------------------------------------------------
                    # 步骤 C: 反演温度
                    # ---------------------------------------------------------
                    with np.errstate(invalid='ignore'):
                        tv = inv_planck(10.5, bv_rad)
                        ts1 = inv_planck(10.5, bs1_rad)  # 阳照土壤 TSS
                        ts2 = inv_planck(10.5, bs2_rad)  # 阴影土壤 TSH

                    # --- 6. 保存结果及绘图 ---
                    # 绘图逻辑 (注意修正 vmin/vmax)
                    fig, axs = plt.subplots(1, 3, figsize=(15, 5))
                    im0 = axs[0].imshow(ts1 - ts2, vmin=-25, vmax=25, cmap='RdBu_r')
                    axs[0].set_title("T_sunlit - T_shaded")
                    plt.colorbar(im0, ax=axs[0])

                    im1 = axs[1].imshow(tv, vmin=275, vmax=320, cmap='jet')
                    axs[1].set_title("T_vegetation")
                    plt.colorbar(im1, ax=axs[1])

                    im2 = axs[2].imshow(ts1, vmin=275, vmax=320, cmap='jet')
                    axs[2].set_title("T_sunlit_soil")
                    plt.colorbar(im2, ax=axs[2])
                    plt.show()



                    # --- 6. 保存结果 ---
                    out_file_v = os.path.join(outdir, f"TV_{file_id}.tif")
                    out_file_s1 = os.path.join(outdir, f"TSS_{file_id}.tif")
                    out_file_s2 = os.path.join(outdir, f"TSH_{file_id}.tif")

                    trans = dataset_ref.GetGeoTransform()
                    proj = dataset_ref.GetProjection()
                    # 将结果限制在合理范围并处理异常
                    tv[(tv < 200) | (tv > 350)] = np.nan
                    ts1[(ts1 < 200) | (ts1 > 380)] = np.nan
                    ts2[(ts2 < 200) | (ts2 > 380)] = np.nan

                    write_image_gdal(tv.astype(np.float32), nss, nll, 1, trans, proj, out_file_v)
                    write_image_gdal(ts1.astype(np.float32), nss, nll, 1, trans, proj, out_file_s1)
                    write_image_gdal(ts2.astype(np.float32), nss, nll, 1, trans, proj, out_file_s2)

print("批量处理任务全部完成。")