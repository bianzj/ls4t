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
# import pyresample as pr
# from satpy import Scene
# import satpy

import numpy as np


def hotspot_layer(lai, hspot, vza, sza, vsa, CIs=1.0, CIv=1.0, G=0.5):
    """
    计算双向透过率(w:光照土壤比例)和单向透过率(b:总土壤比例)
    """
    rvza, rsza, rvsa = np.radians(vza), np.radians(sza), np.radians(vsa)
    cv, cs = np.cos(rvza), np.cos(rsza)
    tv, ts = np.tan(rvza), np.tan(rsza)

    kv, ks = G / cv, G / cs

    # 计算投影距离
    dist = np.sqrt(np.maximum(tv ** 2 + ts ** 2 - 2 * tv * ts * np.cos(rvsa), 0))
    d_prime = hspot / (2.0 / (kv + ks))

    with np.errstate(divide='ignore', invalid='ignore'):
        alpha = dist / d_prime
        w_factor = np.where(alpha < 1e-5, 1.0, (1.0 - np.exp(-alpha)) / alpha)

    pls, plv = CIs * ks, CIv * kv
    overlap = np.sqrt(pls * plv) * w_factor

    gapvs = np.exp(-(pls + plv - overlap) * lai)  # w: 光照土壤
    gapv = np.exp(-plv * lai)  # b: 总土壤
    return gapvs,gapv

def calculate_scattering_angle(sza, saa, vza, vaa):
    """
    计算太阳方向与观测方向的夹角 (散射角/相位角)
    输入参数均为角度 (Degrees)
    """
    # 1. 将角度转换为弧度
    sza_r = np.radians(sza)
    vza_r = np.radians(vza)
    saa_r = np.radians(saa)
    vaa_r = np.radians(vaa)

    # 2. 计算相对方位角 (Relative Azimuth Angle)
    # cos(delta_phi) 在公式中不限制减法顺序
    rel_azimuth_r = saa_r - vaa_r

    # 3. 应用球面三角公式
    cos_xi = (np.cos(sza_r) * np.cos(vza_r) +
              np.sin(sza_r) * np.sin(vza_r) * np.cos(rel_azimuth_r))

    # 4. 限制余弦值范围在 [-1, 1] 之间，防止数值计算误差导致 nan
    cos_xi = np.clip(cos_xi, -1.0, 1.0)

    # 5. 反余弦得到夹角 (弧度)，再转回角度
    scattering_angle = np.degrees(np.arccos(cos_xi))

    return scattering_angle

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


def solve_2x2_system_5x5(rad1, rad2, w_a1, w_b1, w_a2, w_b2, size=5):
    """
    使用 5x5 窗口最小二乘法求解方程组:
    w_a1*X + w_b1*Y = rad1
    w_a2*X + w_b2*Y = rad2

    X, Y: 待求的两组分辐射 (如 X=光照土壤, Y=阴影土壤+植被)
    """
    # --- 1. 掩码处理 ---
    # 只要输入数据中有 NaN，该像素就不参与计算
    invalid_mask = np.isnan(rad1) | np.isnan(rad2) | np.isnan(w_a1) | np.isnan(w_b1)

    def clean(img):
        # 将 NaN 转为 0，防止 uniform_filter 扩散导致全图 NaN
        return np.nan_to_num(img, nan=0.0)

    # --- 2. 构造正规方程各项 (A^T * A 和 A^T * b) ---
    # A 矩阵元素: [[w_a1, w_b1], [w_a2, w_b2]]
    term_AA = clean(w_a1 ** 2 + w_a2 ** 2)  # A 矩阵左上角
    term_AB = clean(w_a1 * w_b1 + w_a2 * w_b2)  # A 矩阵对角线
    term_BB = clean(w_b1 ** 2 + w_b2 ** 2)  # A 矩阵右下角

    term_D1 = clean(w_a1 * rad1 + w_a2 * rad2)  # 观测向量项 1
    term_D2 = clean(w_b1 * rad1 + w_b2 * rad2)  # 观测向量项 2

    # 有效像素计数器 (1.0 代表有效, 0.0 代表无效)
    valid_count = clean(np.where(invalid_mask, 0.0, 1.0))

    # --- 3. 5x5 空间求和 ---
    def box_sum(img):
        # size=5 代表 5x5 窗口
        # uniform_filter 计算均值，乘以 25 (size**2) 得到窗口内总和
        return uniform_filter(img, size=size, mode='nearest') * float(size ** 2)

    sAA = box_sum(term_AA)
    sAB = box_sum(term_AB)
    sBB = box_sum(term_BB)
    sD1 = box_sum(term_D1)
    sD2 = box_sum(term_D2)
    n_v = box_sum(valid_count)  # 窗口内实际有效的像素个数

    # --- 4. 求解克莱姆法则 ---
    # 行列式 det = sAA * sBB - sAB^2
    det = sAA * sBB - sAB ** 2

    with np.errstate(divide='ignore', invalid='ignore'):
        # 求解 X (第一个分量) 和 Y (第二个分量)
        X = (sD1 * sBB - sD2 * sAB) / det
        Y = (sD2 * sAA - sD1 * sAB) / det

    # --- 5. 稳健性过滤 ---
    # 1. det 趋于 0 说明矩阵奇异 (角度重合且地表完全均一)
    # 2. n_v < 10: 5x5 窗口内有效像素不足 40%，解不可信
    # 3. 原始无效位置保持为 NaN
    threshold_nv = (size ** 2) * 0.4  # 5x5 窗口至少需要 10 个有效像素
    mask = (np.abs(det) < 1e-8) | (n_v < threshold_nv) | invalid_mask

    X[mask], Y[mask] = np.nan, np.nan

    # 物理约束：辐射值不能为负
    X[X < 0] = np.nan
    Y[Y < 0] = np.nan

    return X, Y


def solve_joint_vectorized_with_prior(rad_e, rad_i, w, x_prior, lmbda=0.5):
    """
    联合反演：利用分步结果作为先验知识进行全图平差
    """
    H, W = rad_e.shape
    w1, w2, w3, w4, w5, w6 = [w[..., i] for i in range(6)]

    # 构建 A^T * A + lambda * I
    m11, m12, m13 = w1 ** 2 + w4 ** 2 + lmbda, w1 * w2 + w4 * w5, w1 * w3 + w4 * w6
    m22, m23 = w2 ** 2 + w5 ** 2 + lmbda, w2 * w3 + w5 * w6
    m33 = w3 ** 2 + w6 ** 2 + lmbda

    # 构建 A^T * b + lambda * x_prior
    v1 = (w1 * rad_e + w4 * rad_i) + lmbda * x_prior[..., 0]
    v2 = (w2 * rad_e + w5 * rad_i) + lmbda * x_prior[..., 1]
    v3 = (w3 * rad_e + w6 * rad_i) + lmbda * x_prior[..., 2]

    A_stack = np.zeros((H, W, 3, 3))
    A_stack[..., 0, 0], A_stack[..., 0, 1], A_stack[..., 0, 2] = m11, m12, m13
    A_stack[..., 1, 0], A_stack[..., 1, 1], A_stack[..., 1, 2] = m12, m22, m23
    A_stack[..., 2, 0], A_stack[..., 2, 1], A_stack[..., 2, 2] = m13, m23, m33
    B_stack = np.stack([v1, v2, v3], axis=-1)

    mask = ~np.isnan(rad_e) & ~np.isnan(x_prior[..., 0])
    res = np.full((H, W, 3), np.nan)
    if np.any(mask):
        res[mask] = np.linalg.solve(A_stack[mask], B_stack[mask])

    # 基础物理约束裁剪
    bs1, bs2, bv = res[..., 0], res[..., 1], res[..., 2]
    bs2 = np.where(bs2 > bs1, bs1, bs2)
    return bs1, bs2, bv


# ================= 配置路径 =================
indir = "/media/hero/MSG/"
indir_rs = '/media/hero/rs/'
indir0_euro = indir + '/PRODUCTS/MSG/MLST/GEOTIFF'
indir0_euro_lai = indir + '/PRODUCTS/MSG/MDLAI/GEOTIFF'
indir0_iodc = indir + '/PRODUCTS/MSG-IODC/MLST/GEOTIFF'
indir0_lai = indir_rs + '/veg/lai_2021-2025_0.01/'
outdir_root = indir + '/PRODUCTS/LSCT/MLST_COMPONENT2/'
altitude = 0
lambda_val = 100.0
dif = 3
hspot_val = 0.2
# ================= 读取静态数据 =================
print("正在读取静态数据及坐标映射...")
infile_source = indir + "/map/MCD12C1_2011_0.01.tif"
infile_vza_e = indir + "/Static/combined_euro_vza.tif"
infile_vaa_e = indir + "/Static/combined_euro_vaa.tif"
infile_vza_i = indir + "/Static/combined_iodc_vza.tif"
infile_vaa_i = indir + "/Static/combined_iodc_vaa.tif"
infile_lat_e = indir + "/Static/combined_euro_lat.tif"
infile_lon_e = indir + "/Static/combined_euro_lon.tif"

# 读取并校正角度
[vza_euro, nss, nll, nb, _, _, dataset_ref] = read_image_dataset_gdal(infile_vza_e)
[vaa_euro, _, _, _, _, _, _] = read_image_dataset_gdal(infile_vaa_e)
[vza_iodc, _, _, _, _, _, _] = read_image_dataset_gdal(infile_vza_i)
[vaa_iodc, _, _, _, _, _, _] = read_image_dataset_gdal(infile_vaa_i)
[lat, _, _, _, _, _, _] = read_image_dataset_gdal(infile_lat_e)
[lon, _, _, _, _, _, _] = read_image_dataset_gdal(infile_lon_e)

vza_euro, vaa_euro = vza_euro / 100.0, vaa_euro / 100.0
vza_iodc, vaa_iodc = vza_iodc / 100.0, vaa_iodc / 100.0
vaa_euro = (360 + vaa_euro) % 360
vaa_iodc = (360 + vaa_iodc) % 360
lat, lon = lat / 100.0, lon / 100.0         # 修正：使用 np.flipud
# 若经纬度存在异常值，置为 NaN
ind = (lat > 90) | (lat < -90)
lat[ind] = np.nan
lon[ind] = np.nan

# 坐标转换映射 (用于提取土地利用类型和发射率)
# ns, nl = nss, nll
# nsi, nli = np.meshgrid(np.arange(ns), np.arange(nl))
# nli_flat, nsi_flat = nli.flatten(), nsi.flatten()
# temp1, temp2 = imagexy2geo(dataset_ref, nli_flat, nsi_flat)
# lon, lat = geo2lonlat(dataset_ref, temp1, temp2)
# lon, lat = lon.reshape(nl, ns), lat.reshape(nl, ns)
# lonn = resize_data(lon,int(nl/10),int(ns/10))
# latt = resize_data(lat,int(nl/10),int(ns/10))

[land_type_map, _, _, _, _, _, dataset_map] = read_image_dataset_gdal(infile_source)
indx, indy = loc2map(lat.flatten(), lon.flatten(), dataset_map)
indx, indy = indx.reshape(nll, nss), indy.reshape(nll, nss)
land_type = land_type_map[indx, indy].astype(np.int16)

# 读取发射率
indir_ems = indir + '/lse/'
infile_soil_emis = indir_ems + 'AG1km.v003.SoilEmi.ABI.Global.001D_LSE11.tif'
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
lai_cache = []
lai = np.zeros([nll,nss])
for kyear in range(2022, 2023):
    for kmonth in range(1, 13):
        for kday in range(1, 32):

            # --- 1. 处理 LAI 和 权重 w ---
            kdoy = date2DOY(kyear, kmonth, kday)
            kkdoy = int(kdoy / 4) * 4 + 1
            infile_lai = os.path.join(indir0_lai, f"{kyear:04d}", f"lai_{kyear:04d}{kkdoy:03d}.h5")

            if isfirst or (kkdoy == kdoy):
                if os.path.exists(infile_lai):

                    # 读取 LAI 数据（假设读取函数 read_h5py_item 可用）
                    lai_full = read_h5py_item(infile_lai, "/data")  # 或直接用 h5py
                    lai_full = lai_full / 1000.0
                    lai_full[lai_full > 10] = np.nan
                    lai = lai_full[indx, indy]
                    lai_cache.append(infile_lai)

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
            for khour in range(9, 17, 1):
                for kmin in range(0, 1):
                    file_id = "%04d%02d%02d%02d00" % (kyear, kmonth, kday, khour)
                    date_str = "%04d%02d%02d" % (kyear, kmonth, kday)
                    infile_e = os.path.join(indir_euro, f"HDF5_LSASAF_MSG_LST_MSG-Disk_{file_id}.tif")
                    infile_i = os.path.join(indir_iodc, f"HDF5_LSASAF_MSG-IODC_LST_IODC-Disk_{file_id}.tif")

                    if not (os.path.exists(infile_e) and os.path.exists(infile_i)):
                        continue

                    try:
                        print(f"正在处理: {file_id}")

                        outfile_h5 = os.path.join(outdir, f"MSG_LSCT_{file_id}.h5")
                        if os.path.exists(outfile_h5):
                            continue

                        print(f"正在处理: {file_id}")
                        lst_e, _, _, _, _, _ = read_image_gdal(infile_e)
                        lst_i, _, _, _, _, _ = read_image_gdal(infile_i)

                        time_val = pd.to_datetime(f"{date_str} {khour:02d}:{kmin:02d}:00").tz_localize('UTC')
                        site_temp = Location(lat.flatten(), lon.flatten(), 'Etc/GMT', altitude, 'None')
                        nloc = len(lat.flatten())
                        solpos_temp = pvlib.solarposition.get_solarposition(np.repeat(time_val, nloc), site_temp.latitude,
                                                                            site_temp.longitude, site_temp.altitude,
                                                                            method='nrel_numpy')
                        sza_temp = solpos_temp['zenith'].to_numpy().reshape(lat.shape).astype(np.float32)
                        saa_temp = solpos_temp['azimuth'].to_numpy().reshape(lat.shape).astype(np.float32)
                        sza = resize_data(sza_temp, nll, nss)
                        saa = resize_data(saa_temp, nll, nss)

                        vsa_euro = np.abs(saa - vaa_euro)
                        vsa_iodc = np.abs(saa - vaa_iodc)
                        vsa_euro[vsa_euro > 180] = 360 - vsa_euro[vsa_euro > 180]
                        vsa_iodc[vsa_iodc > 180] = 360 - vsa_iodc[vsa_iodc > 180]

                        b1 = gap_probability_hom_analytical(lai, vza_euro)
                        w1,b1 = hotspot_layer(lai, 0.1, vza_euro, sza, vsa_euro)
                        b2 = gap_probability_hom_analytical(lai, vza_iodc)
                        w2,b2 = hotspot_layer(lai, 0.1, vza_iodc, sza, vsa_iodc)

                        w = np.zeros([nll, nss, 6])
                        w[:, :, 0] = emis_s * (w1)  # Soil Euro
                        w[:, :, 1] = emis_s * (b1 - w1)  # Veg Euro
                        w[:, :, 2] = emis_v * (1-b1)  # Soil IODC
                        w[:, :, 3] = emis_s * (w2)  # Veg IODC
                        w[:, :, 4] = emis_s * (b2 - w2)  # Veg IODC
                        w[:, :, 5] = emis_v * (1-b2)  # Veg IODC

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
                        # 步骤 A: 第一阶段求解 - [光照土壤] vs [阴影土壤 + 植被]
                        # ---------------------------------------------------------
                        # 合并土壤权重: W_soil = W_sunlit + W_shaded
                        w_soil_e = w[:, :, 0] + w[:, :, 1]
                        w_veg_e = w[:, :, 2]
                        w_soil_i = w[:, :, 3] + w[:, :, 4]
                        w_veg_i = w[:, :, 5]

                        # 求解整体土壤辐射 (bs_total_rad) 和 植被辐射 (bv_rad)
                        bs_total_rad, bv_rad = solve_2x2_system_5x5(rad_e, rad_i,
                                                                w_soil_e, w_veg_e,
                                                                w_soil_i, w_veg_i, size=5)

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
                        bs1_rad, bs2_rad = solve_2x2_system_5x5(rad_soil_only_e, rad_soil_only_i,
                                                            w[:, :, 0], w[:, :, 1],
                                                            w[:, :, 3], w[:, :, 4], size=5)

                        # ---------------------------------------------------------
                        # 步骤 B: 第三阶段求解 - 在残差中分离 [阴影土壤] 和 [植被]
                        # ---------------------------------------------------------
                        # 构造先验矩阵堆栈
                        # --- 阶段 B: 物理边界快速修正 (Vectorized) ---
                        # 强制执行 bs2 < bs1 以及异常值压制
                        # bs2_rad = np.where(bs2_rad > bs1_rad, bs1_rad, bs2_rad)
                        # bv_rad = np.where(bv_rad > planck(10.5, 350), bs2_rad, bv_rad)  # 植被不过热

                        x_prior = np.stack([bs1_rad, bs2_rad, bv_rad], axis=-1)
                        print(f"正在进行联合平差修正...")
                        bs1_final, bs2_final, bv_final = solve_joint_vectorized_with_prior(
                            rad_e, rad_i, w, x_prior, lmbda=0.1
                        )
                        # ---------------------------------------------------------
                        # 步骤 C: 反演温度
                        # ---------------------------------------------------------
                        with np.errstate(invalid='ignore'):
                            ts1 = inv_planck(10.5, bs1_final)
                            ts2 = inv_planck(10.5, bs2_final)
                            tv = inv_planck(10.5, bv_final)
                            ts = inv_planck(10.5,bs_total_rad)
                        # with np.errstate(invalid='ignore'):
                        #     ts1 = inv_planck(10.5, bs1_rad)
                        #     ts2 = inv_planck(10.5, bs2_rad)
                        #     tv = inv_planck(10.5, bv_rad)
                        # --- 6. 保存结果及绘图 ---
                        # 绘图逻辑 (注意修正 vmin/vmax)

                        trans = dataset_ref.GetGeoTransform()
                        proj = dataset_ref.GetProjection()

                        # 统一构建掩码 (包含 NaN 和 范围外的值)
                        # 注意：np.isnan 是为了防止之前的计算步骤中已经产生了 NaN
                        invalid_mask = (np.isnan(ts)) | (ts < 250) | (ts > 350) | \
                                       (np.isnan(tv)) | (tv < 250) | (tv > 350) | \
                                       (np.isnan(ts1)) | (ts1 < 250) | (ts1 > 350) | \
                                       (np.isnan(ts2)) | (ts2 < 250) | (ts2 > 350) | (lai < 0.05)

                        # 堆叠数据 [4, H, W]
                        stack = np.stack([ts, tv, ts1, ts2], axis=0)

                        # --- 关键转换步骤 ---
                        # 1. 扩大 100 倍
                        stack_scaled = stack * 100.0

                        # 2. 将无效区域设为 0 (uint16 的填充值)
                        stack_scaled[np.broadcast_to(invalid_mask, stack_scaled.shape)] = 0

                        # 3. 转换为 uint16 (会强制截断小数位，相当于 np.floor)
                        result_u16 = stack_scaled.astype(np.uint16)

                        # --- 保存为 H5 ---
                        try:
                            with h5py.File(outfile_h5, 'w') as h5f:
                                # 创建压缩数据集 (chunks=True 对后续局部读取很有帮助)
                                dset = h5f.create_dataset(
                                    'data',
                                    data=result_u16,
                                    compression="gzip",
                                    compression_opts=4,
                                    chunks=True
                                )

                                # 保存地理参考信息（关键：将 trans 和 proj 存入属性）
                                dset.attrs['GeoTransform'] = trans
                                dset.attrs['Projection'] = proj
                                dset.attrs['Description'] = "Bands: ts, tv, tss, tsh"
                                dset.attrs['Scale_Factor'] = 100
                                dset.attrs['NoData_Value'] = 0
                        except Exception as e:
                            print(f"H5 save failed: {e}")

                    except Exception as e:
                        print(f"H5 save failed: {e}")

                print("批量处理任务全部完成。")