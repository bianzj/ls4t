import os
import glob
import numpy as np
import pandas as pd
from base.util_data import *
from base.util_lsct import *
from base.util_file import *
from scipy.ndimage import uniform_filter

# ================= 常量定义 =================
planck_c1 = 1.191042972e-16
planck_c2 = 1.438776877e-2
temperature_zero = 273.15
temperature_threshold = 150.0


# ================= 核心物理函数 =================
def hotspot_layer(lai, hspot, vza, sza, vsa, CIs=1.0, CIv=1.0, G=0.5):
    """计算双向透过率(w:光照土壤比例)和单向透过率(b:总土壤比例)"""
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
    return gapvs, gapv


def planck(wavelength, Ts):
    """基于普朗克公式从温度计算辐射"""
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
    """普朗克逆函数：从辐射计算温度"""
    c1 = planck_c1 * 10000
    c2 = planck_c2
    with np.errstate(invalid='ignore', divide='ignore'):
        temp = c1 / (rad * np.power(wavelength, 5)) + 1
        Ts = np.where(temp > 1, c2 / (wavelength * np.log(temp)), np.nan)
    return Ts


def gap_probability_hom_analytical(lai, sza):
    """计算间隙概率"""
    sza_rad = np.radians(sza)
    return np.exp(-0.5 * lai / np.cos(sza_rad))

def solve_3x3_three_components(rad_euro, rad_iodc, w):
    """
    求解三组分模型 (3x3 窗口最小二乘法):
    w1*bs1 + w2*bs2 + w3*bv = rad_e
    w4*bs1 + w5*bs2 + w6*bv = rad_i
    w shape: (H, W, 6)
    """
    # 1. 提取 6 个系数
    # w1, w2, w3 对应 Euro 的 bs1, bs2, bv
    # w4, w5, w6 对应 IODC 的 bs1, bs2, bv
    w1, w2, w3 = w[..., 0], w[..., 1], w[..., 2]
    w4, w5, w6 = w[..., 3], w[..., 4], w[..., 5]

    # --- 2. 处理 NaN (防止扩散) ---
    # 只要辐射值或第一个系数是 NaN，则视为无效像素
    invalid_mask = np.isnan(rad_euro) | np.isnan(rad_iodc) | np.isnan(w1)

    def clean_nan(img):
        return np.nan_to_num(img, nan=0.0)

    # --- 3. 计算 A^T * A (3x3 对称矩阵的 6 个独立元素) ---
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

    # 有效像素计数
    valid_count = clean_nan(np.where(invalid_mask, 0.0, 1.0))

    # --- 5. 3x3 窗口空间累加 ---
    def box_sum_3x3(img):
        # size=3, 均值乘 9 得到窗口总和
        return uniform_filter(img, size=3, mode='nearest') * 9.0

    M11, M12, M13 = box_sum_3x3(m11_p), box_sum_3x3(m12_p), box_sum_3x3(m13_p)
    M22, M23, M33 = box_sum_3x3(m22_p), box_sum_3x3(m23_p), box_sum_3x3(m33_p)
    V1, V2, V3 = box_sum_3x3(v1_p), box_sum_3x3(v2_p), box_sum_3x3(v3_p)

    # 关键点：3x3 窗口内有效像素最大值为 9
    n_valid = box_sum_3x3(valid_count)

    # --- 6. 逐像素构建矩阵并求解 ---
    H, W = rad_euro.shape
    A_stack = np.zeros((H, W, 3, 3))
    A_stack[..., 0, 0], A_stack[..., 0, 1], A_stack[..., 0, 2] = M11, M12, M13
    A_stack[..., 1, 0], A_stack[..., 1, 1], A_stack[..., 1, 2] = M12, M22, M23
    A_stack[..., 2, 0], A_stack[..., 2, 1], A_stack[..., 2, 2] = M13, M23, M33

    B_stack = np.zeros((H, W, 3))
    B_stack[..., 0], B_stack[..., 1], B_stack[..., 2] = V1, V2, V3

    # 计算 3x3 矩阵的行列式用于判别
    det = (M11 * (M22 * M33 - M23 ** 2) -
           M12 * (M12 * M33 - M13 * M23) +
           M13 * (M12 * M23 - M13 * M22))

    # --- 7. 求解门槛设置 ---
    # 1. 行列式不能太小（防止奇异矩阵）
    # 2. n_valid 必须大于等于 4 (3x3窗口共9个点，要求近一半有效，保证稳定性)
    # 3. 原始像素不能是无效的
    solve_mask = (np.abs(det) > 1e-7) & (n_valid >= 4) & (~invalid_mask)

    bs1 = np.full((H, W), np.nan)
    bs2 = np.full((H, W), np.nan)
    bv = np.full((H, W), np.nan)

    if np.any(solve_mask):
        # 批量执行 3x3 矩阵求逆/求解
        results = np.linalg.solve(A_stack[solve_mask], B_stack[solve_mask])
        bs1[solve_mask] = results[:, 0]
        bs2[solve_mask] = results[:, 1]
        bv[solve_mask] = results[:, 2]

    # --- 8. 物理约束清理 ---
    # 辐射值必须大于 0 且不能是天文数字（根据 planck 范围判断，比如上限 20.0）
    limit_mask = (bs1 <= 0) | (bs2 <= 0) | (bv <= 0) | (bs1 > 30) | (bs2 > 30) | (bv > 30)
    bs1[limit_mask], bs2[limit_mask], bv[limit_mask] = np.nan, np.nan, np.nan

    return bs1, bs2, bv
# ================= 配置路径 =================

# ================= 窗口求解函数 (仅中心像素) =================
def solve_2x2_system_center(rad1, rad2, w_a1, w_b1, w_a2, w_b2, center=2, size=5):
    """
    使用5x5窗口最小二乘法求解2x2方程组，只返回中心像素结果

    方程组:
        w_a1*X + w_b1*Y = rad1
        w_a2*X + w_b2*Y = rad2

    Args:
        rad1, rad2: 观测辐射 (5x5矩阵)
        w_a1, w_b1: 第一行权重 (5x5矩阵)
        w_a2, w_b2: 第二行权重 (5x5矩阵)
        center: 中心像素索引 (默认2)
        size: 窗口大小 (默认5)

    Returns:
        X, Y: 中心像素的求解结果 (标量)
    """
    # 提取中心像素所在的5x5邻域
    # 注意：如果输入已经是5x5，直接使用
    h, w = rad1.shape

    # 定义窗口范围
    half = size // 2
    r_start = max(0, center - half)
    r_end = min(h, center + half + 1)
    c_start = max(0, center - half)
    c_end = min(w, center + half + 1)

    # 提取邻域数据
    rad1_win = rad1[r_start:r_end, c_start:c_end].flatten()
    rad2_win = rad2[r_start:r_end, c_start:c_end].flatten()
    w_a1_win = w_a1[r_start:r_end, c_start:c_end].flatten()
    w_b1_win = w_b1[r_start:r_end, c_start:c_end].flatten()
    w_a2_win = w_a2[r_start:r_end, c_start:c_end].flatten()
    w_b2_win = w_b2[r_start:r_end, c_start:c_end].flatten()

    # 创建有效像素掩码
    valid_mask = ~(np.isnan(rad1_win) | np.isnan(rad2_win) |
                   np.isnan(w_a1_win) | np.isnan(w_b1_win) |
                   np.isnan(w_a2_win) | np.isnan(w_b2_win))

    # 如果有效像素太少，返回NaN
    threshold_nv = size ** 2 * 0.4
    if np.sum(valid_mask) < threshold_nv:
        return np.nan, np.nan

    # 过滤有效像素
    rad1_valid = rad1_win[valid_mask]
    rad2_valid = rad2_win[valid_mask]
    w_a1_valid = w_a1_win[valid_mask]
    w_b1_valid = w_b1_win[valid_mask]
    w_a2_valid = w_a2_win[valid_mask]
    w_b2_valid = w_b2_win[valid_mask]

    # 构造正规方程
    n = len(rad1_valid)

    # A^T * A
    sAA = np.sum(w_a1_valid ** 2 + w_a2_valid ** 2)
    sAB = np.sum(w_a1_valid * w_b1_valid + w_a2_valid * w_b2_valid)
    sBB = np.sum(w_b1_valid ** 2 + w_b2_valid ** 2)

    # A^T * b
    sD1 = np.sum(w_a1_valid * rad1_valid + w_a2_valid * rad2_valid)
    sD2 = np.sum(w_b1_valid * rad1_valid + w_b2_valid * rad2_valid)

    # 克莱姆法则求解
    det = sAA * sBB - sAB ** 2

    if np.abs(det) < 1e-8:
        return np.nan, np.nan

    X = (sD1 * sBB - sD2 * sAB) / det
    Y = (sD2 * sAA - sD1 * sAB) / det

    # 物理约束：辐射值不能为负
    if X < 0 or Y < 0:
        return np.nan, np.nan

    return X, Y


def solve_constrained_vectorized2_center(rad_e, rad_i, w2, w3, w5, w6, bs1_fixed, dif=3.0):
    """
    带约束的求解 (约束: |bs2 - bv| <= dif)，只返回中心像素
    """
    # 计算无约束解
    bs2_fast, bv_fast = solve_2x2_system_center(rad_e, rad_i, w2, w3, w5, w6)

    # 如果无约束解无效，尝试边界解
    if np.isnan(bs2_fast) or np.isnan(bv_fast):
        return bs2_fast, bv_fast

    # 检查是否违反约束
    if np.abs(bs2_fast - bv_fast) <= dif:
        return bs2_fast, bv_fast

    # 计算两种边界解
    # 情况C: bs2 = bv + dif
    # 从中心提取权重和辐射值
    # 注意：这里我们需要重新计算，但使用中心像素作为初始估计
    # 简单方法：使用最小二乘估计
    center = 2
    w2_c = w2[center, center] if w2.ndim == 2 else w2
    w3_c = w3[center, center] if w3.ndim == 2 else w3
    w5_c = w5[center, center] if w5.ndim == 2 else w5
    w6_c = w6[center, center] if w6.ndim == 2 else w6
    rad_e_c = rad_e[center, center] if rad_e.ndim == 2 else rad_e
    rad_i_c = rad_i[center, center] if rad_i.ndim == 2 else rad_i

    # 情况C: bs2 = bv + dif
    w_sum_e = w2_c + w3_c
    w_sum_i = w5_c + w6_c
    bv_C = (w_sum_e * (rad_e_c - w2_c * dif) + w_sum_i * (rad_i_c - w5_c * dif)) / (w_sum_e ** 2 + w_sum_i ** 2 + 1e-9)
    bs2_C = bv_C + dif
    sse_C = (rad_e_c - (w2_c * bs2_C + w3_c * bv_C)) ** 2 + (rad_i_c - (w5_c * bs2_C + w6_c * bv_C)) ** 2

    # 情况D: bs2 = bv - dif
    bv_D = (w_sum_e * (rad_e_c + w2_c * dif) + w_sum_i * (rad_i_c + w5_c * dif)) / (w_sum_e ** 2 + w_sum_i ** 2 + 1e-9)
    bs2_D = bv_D - dif
    sse_D = (rad_e_c - (w2_c * bs2_D + w3_c * bv_D)) ** 2 + (rad_i_c - (w5_c * bs2_D + w6_c * bv_D)) ** 2

    # 选择残差更小的解
    if sse_C <= sse_D:
        return bs2_C, bv_C
    else:
        return bs2_D, bv_D


def solve_joint_center(rad_e, rad_i, w, x_prior, lmbda=100):
    """
    联合反演，只返回中心像素
    """
    center = 2

    # 提取中心像素
    if rad_e.ndim == 2:
        rad_e_c = rad_e[center, center]
        rad_i_c = rad_i[center, center]
    else:
        rad_e_c = rad_e
        rad_i_c = rad_i

    # 提取权重
    if w.ndim == 3:
        w_c = w[center, center, :]
    else:
        w_c = w

    w1, w2, w3, w4, w5, w6 = w_c

    # 提取先验
    if x_prior.ndim == 3:
        x_prior_c = x_prior[center, center, :]
    else:
        x_prior_c = x_prior

    # 构建 A^T * A + lambda * I
    m11 = w1 ** 2 + w4 ** 2 + lmbda
    m12 = w1 * w2 + w4 * w5
    m13 = w1 * w3 + w4 * w6
    m22 = w2 ** 2 + w5 ** 2 + lmbda
    m23 = w2 * w3 + w5 * w6
    m33 = w3 ** 2 + w6 ** 2 + lmbda

    # 构建 A^T * b + lambda * x_prior
    v1 = (w1 * rad_e_c + w4 * rad_i_c) + lmbda * x_prior_c[0]
    v2 = (w2 * rad_e_c + w5 * rad_i_c) + lmbda * x_prior_c[1]
    v3 = (w3 * rad_e_c + w6 * rad_i_c) + lmbda * x_prior_c[2]

    # 求解3x3方程组
    A = np.array([[m11, m12, m13],
                  [m12, m22, m23],
                  [m13, m23, m33]])
    B = np.array([v1, v2, v3])

    try:
        result = np.linalg.solve(A, B)
    except np.linalg.LinAlgError:
        # 如果矩阵奇异，使用伪逆
        result = np.linalg.lstsq(A, B, rcond=None)[0]

    bs1, bs2, bv = result

    # 物理约束
    if bs2 > bs1:
        bs2 = bs1

    return bs1, bs2, bv


# ================= 主程序 =================
# 配置路径
indir = "/media/hero/MSG/"
indir_root = indir + "/PRODUCTS/SITE/"
infile_sites = indir + "/field/sites-2025-selected.csv"
outfile_csv = indir + "/PRODUCTS/LSCT_Site_Results_2018-2025_all.csv"


indir = "/media/hero/MSG/"
indir_root = indir + "/PRODUCTS/SITE/"
infile_sites = indir + "/field/sites.txt"
outfile_csv = indir + "/PRODUCTS/LSCT_Site_Results_old.csv"

# 核心反演参数
wavelength = 10.5
hspot_val = 0.2
lmbda_val = 1
dif = 3


# ===================== 【观测时段配置，按需修改】 =====================
TARGET_HOURS = list(range(9, 17))  # 12,13,14,15,16
# TARGET_HOURS = list(range(9,17))   # 如需9~16点启用这一行
# ===================================================================

# 读取站点列表
site_info = read_txt_str(infile_sites, r",")
site_names = [row[0] for row in site_info]
n_site = len(site_names)
results_list = []

print(f"开始处理站点反演，共 {len(site_names)} 个站点...")
print("注意：现在只处理5x5窗口的中心像素 (索引2,2)")

# 主循环
for ksite in range(n_site):
    # if ksite != 53: continue  # 取消注释可测试特定站点

    site = site_names[ksite]
    site_path = os.path.join(indir_root, site)
    static_path = os.path.join(site_path, "static")

    print(f"\n处理站点 {ksite + 1}/{n_site}: {site}")

    if not os.path.exists(static_path):
        print(f"  警告: 静态数据不存在，跳过")
        continue

    # --- 1. 读取站点静态数据 ---
    vza_e, _, _, _, _, _ = read_image_gdal(os.path.join(static_path, "vza_e.tif"))
    vaa_e, _, _, _, _, _ = read_image_gdal(os.path.join(static_path, "vaa_e.tif"))
    vza_i, _, _, _, _, _ = read_image_gdal(os.path.join(static_path, "vza_i.tif"))
    vaa_i, _, _, _, _, _ = read_image_gdal(os.path.join(static_path, "vaa_i.tif"))
    emis_s, _, _, _, _, _ = read_image_gdal(os.path.join(static_path, "emis_s.tif"))
    emis_v, _, _, _, _, _ = read_image_gdal(os.path.join(static_path, "emis_v.tif"))

    # --- 2. 遍历日期 ---
    for kyear in range(2017,2018):
        date_folders = glob.glob(os.path.join(site_path, "%04d/*/*"%kyear))

        for date_dir in sorted(date_folders):
            parts = date_dir.replace("\\", "/").split("/")
            year, month, day = parts[-3], parts[-2], parts[-1]
            date_str = f"{year}{month}{day}"

            # 读取LAI
            lai_file = os.path.join(date_dir, f"LAI_{date_str}.tif")
            if not os.path.exists(lai_file):
                continue
            lai, _, _, _, _, _ = read_image_gdal(lai_file)

            # --- 3. 遍历时间 ---
            lst_e_files = glob.glob(os.path.join(date_dir, "LST_*_e.tif"))

            for f_e in lst_e_files:


                file_id = os.path.basename(f_e).split("_")[1]
                f_i = f_e.replace("_e.tif", "_i.tif")
                f_sza = os.path.join(date_dir, f"SZA_{file_id}.tif")
                f_saa = os.path.join(date_dir, f"SAA_{file_id}.tif")


                # ===================== 小时过滤 =====================
                if len(file_id) >= 12 and file_id.isdigit():
                    hour = int(file_id[8:10])
                    if hour not in TARGET_HOURS:
                        continue
                else:
                    continue
                # ====================================================

                if not (os.path.exists(f_i) and os.path.exists(f_sza)):
                    continue

                # 读取数据
                lst_e, _, _, _, _, _ = read_image_gdal(f_e)
                lst_i, _, _, _, _, _ = read_image_gdal(f_i)
                sza, _, _, _, _, _ = read_image_gdal(f_sza)
                saa, _, _, _, _, _ = read_image_gdal(f_saa)

                # 数据预处理
                lst_e = lst_e.astype(np.float64)
                lst_i = lst_i.astype(np.float64)
                lst_e[lst_e == 0] = np.nan
                lst_i[lst_i == 0] = np.nan
                lst_e = lst_e / 100.0 + temperature_zero
                lst_i = lst_i / 100.0 + temperature_zero



                # 检查中心像素是否有效
                center = 2
                if np.isnan(lst_e[center, center]) or np.isnan(lst_i[center, center]):
                    continue

                # --- 4. 计算角度和权重 ---
                vsa_e = np.abs(saa - vaa_e)
                vsa_e[vsa_e > 180] = 360 - vsa_e[vsa_e > 180]
                vsa_i = np.abs(saa - vaa_i)
                vsa_i[vsa_i > 180] = 360 - vsa_i[vsa_i > 180]

                # 计算透过率
                w1, b1 = hotspot_layer(lai, hspot_val, vza_e, sza, vsa_e)
                w2, b2 = hotspot_layer(lai, hspot_val, vza_i, sza, vsa_i)

                # 构造权重矩阵
                w_mat = np.zeros([5, 5, 6])
                w_mat[:, :, 0] = emis_s * w1
                w_mat[:, :, 1] = emis_s * (b1 - w1)
                w_mat[:, :, 2] = emis_v * (1.0 - b1)
                w_mat[:, :, 3] = emis_s * w2
                w_mat[:, :, 4] = emis_s * (b2 - w2)
                w_mat[:, :, 5] = emis_v * (1.0 - b2)

                # 计算辐射
                rad_e = planck(wavelength, lst_e) * (w_mat[:, :, 0] + w_mat[:, :, 1] + w_mat[:, :, 2])
                rad_i = planck(wavelength, lst_i) * (w_mat[:, :, 3] + w_mat[:, :, 4] + w_mat[:, :, 5])

                # 检查中心像素的有效性
                if np.isnan(rad_e[center, center]) or np.isnan(rad_i[center, center]):
                    continue

                # --- 5. 执行反演 (只针对中心像素) ---


                bs1_f, bs2_f, bv_f = solve_3x3_three_components(rad_e, rad_i, w_mat)

                bs1_f = bs1_f[2,2]
                bs2_f = bs2_f[2,2]
                bv_f = bv_f[2,2]

                if np.isnan(bs1_f) or np.isnan(bs2_f) or np.isnan(bv_f):
                    continue

                # 计算土壤温度
                bs = gap_probability_hom_analytical(lai[center, center], sza[center, center])
                bs_f = bs1_f * bs + bs2_f * (1 - bs)



                # --- 6. 提取结果 ---
                with np.errstate(invalid='ignore'):
                    ts1_pix = inv_planck(wavelength, bs1_f)
                    ts2_pix = inv_planck(wavelength, bs2_f)
                    tv_pix = inv_planck(wavelength, bv_f)
                    ts_pix = inv_planck(wavelength, bs_f)
                    lst_e_pix = lst_e[center, center]
                    lst_i_pix = lst_i[center, center]
                    sza_pix = sza[center, center]
                    lai_pix = lai[center, center]

                # 有效性检查
                if np.isnan(tv_pix) or np.isnan(ts1_pix) or np.isnan(ts2_pix):
                    continue

                # 保存记录
                results_list.append({
                    'Site': site,
                    'DateTime': file_id,
                    'SZA': np.round(sza_pix, 2),
                    'LST_Euro': np.round(lst_e_pix - temperature_zero, 2),
                    'LST_IODC': np.round(lst_i_pix - temperature_zero, 2),
                    'T_Sunlit_Soil': np.round(ts1_pix - temperature_zero, 2),
                    'T_Shaded_Soil': np.round(ts2_pix - temperature_zero, 2),
                    'T_Vegetation': np.round(tv_pix - temperature_zero, 2),
                    'T_Soil': np.round(ts_pix - temperature_zero, 2),
                    'LAI': np.round(lai_pix, 3)
                })

# --- 7. 输出结果 ---
if results_list:
    df = pd.DataFrame(results_list)
    df.to_csv(outfile_csv, index=False)
    print(f"\n反演完成！共 {len(results_list)} 条记录，保存至: {outfile_csv}")

    # 输出统计信息
    print("\n=== 结果统计 ===")
    print(f"总记录数: {len(df)}")
    print(f"站点数: {df['Site'].nunique()}")
    print(f"时间范围: {df['DateTime'].min()} - {df['DateTime'].max()}")
    print(f"SZA范围: {df['SZA'].min():.1f} - {df['SZA'].max():.1f}°")
    print(f"T_Soil范围: {df['T_Soil'].min():.1f} - {df['T_Soil'].max():.1f}°C")
    print(f"T_Vegetation范围: {df['T_Vegetation'].min():.1f} - {df['T_Vegetation'].max():.1f}°C")
else:
    print("\n警告: 没有生成任何有效结果！")