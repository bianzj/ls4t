import os
import glob
import numpy as np
import pandas as pd
from base.util_data import *
from base.util_lsct import *
from base.util_file import *

# ================= 常量定义 =================
planck_c1 = 1.191042972e-16
planck_c2 = 1.438776877e-2
temperature_zero = 273.15
temperature_threshold = 150.0
EPS_MAT = 1e-8
# 自然梯度迭代参数（信息几何新增）
MAX_ITER = 12
STEP_INIT = 0.2
CONV_TOL = 0.01
FIM_COND_THRESH = 1e5
# 物理温度约束区间 K
T_MIN_K = 243.15
T_MAX_K = 353.15

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


def dplanck_dT(wavelength, Ts):
    """普朗克函数解析导数 dB/dT，信息几何雅可比使用"""
    c1 = planck_c1
    c2 = planck_c2
    if Ts < temperature_threshold:
        Ts = Ts + temperature_zero
    exp_term = np.exp(c2 / (Ts * wavelength))
    denom = (exp_term - 1.0) ** 2
    deriv = (c1 * 10000 * c2 * exp_term) / (wavelength ** 6 * Ts ** 2 * denom)
    return deriv


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

# =====================【信息几何新增：自然梯度联合反演】=====================
def solve_joint_natural_gradient(rad_e, rad_i, w, x_prior, wavelength, lmbda=1.0):
    """
    【中等改造：信息几何 自然梯度下降NGD】
    替代原有solve_joint_center闭式求解
    参数:
        rad_e,rad_i: 双角度观测辐射场
        w: 权重矩阵 w_mat (5,5,6)
        x_prior: [bs1,bs2,bv] 两阶段得到的辐射初值
        wavelength: 波段波长
        lmbda: 先验正则权重
    返回: bs1,bs2,bv
    """
    center = 2
    # 提取中心单点
    rad_e_c = rad_e[center, center]
    rad_i_c = rad_i[center, center]
    w_c = w[center, center, :]
    w1, w2, w3, w4, w5, w6 = w_c

    # 初始辐射值（普朗克辐射量纲）
    theta = np.array(x_prior, dtype=np.float64)
    obs = np.array([rad_e_c, rad_i_c])

    def forward_model(x):
        bs1, bs2, bv = x
        r_e = w1*bs1 + w2*bs2 + w3*bv
        r_i = w4*bs1 + w5*bs2 + w6*bv
        return np.array([r_e, r_i])

    def jacobian(x):
        """雅可比矩阵 dR/dθ"""
        J = np.array([
            [w1, w2, w3],
            [w4, w5, w6]
        ])
        return J

    # 1. 在初始点计算Fisher信息矩阵 F = J^T J
    J0 = jacobian(theta)
    F = J0.T @ J0 + lmbda * np.eye(3)
    # 条件数质控
    cond_F = np.linalg.cond(F)
    if cond_F > FIM_COND_THRESH:
        return np.nan, np.nan, np.nan

    # 自然梯度迭代
    step = STEP_INIT
    for it in range(MAX_ITER):
        r_mod = forward_model(theta)
        resid = obs - r_mod
        loss = np.sum(resid**2)
        J = jacobian(theta)
        grad = -2 * J.T @ resid

        # 自然梯度更新 theta = theta - eta * F^{-1} grad
        try:
            nat_grad = np.linalg.solve(F, grad)
        except np.linalg.LinAlgError:
            return np.nan, np.nan, np.nan

        theta_new = theta - step * nat_grad

        # =========物理约束投影=========
        bs1, bs2, bv = theta_new
        # 辐射非负
        bs1 = np.clip(bs1, 0.0, None)
        bs2 = np.clip(bs2, 0.0, None)
        bv = np.clip(bv, 0.0, None)
        # 阴影土壤温度 ≤光照土壤温度
        if bs2 > bs1:
            bs2 = bs1
        theta_new = np.array([bs1, bs2, bv])

        # 收敛判断
        delta = np.linalg.norm(theta_new - theta)
        theta = theta_new
        if delta < CONV_TOL:
            break

    bs1_f, bs2_f, bv_f = theta
    return bs1_f, bs2_f, bv_f

# ================= 主程序 =================
# 配置路径
indir = "/media/hero/MSG/"
indir_root = indir + "/PRODUCTS/SITE/"
infile_sites = indir + "/field/sites-2025-selected.csv"
outfile_csv = indir + "/PRODUCTS/LSCT_Site_Results_2018-2025_all_direct.csv"


indir = "/media/hero/MSG/"
indir_root = indir + "/PRODUCTS/SITE/"
infile_sites = indir + "/field/sites.txt"
outfile_csv = indir + "/PRODUCTS/LSCT_Site_Results.csv"

# 核心反演参数
wavelength = 10.5
hspot_val = 0.1
lmbda_val = 1000
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
print("【已启用：信息几何自然梯度NGD联合反演】")

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
    for kyear in range(2018,2026):
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
                # 阶段1: 光照土壤 vs 其余
                bs1_s1, _ = solve_2x2_system_center(
                    rad_e, rad_i,
                    w_mat[:, :, 0], (w_mat[:, :, 1] + w_mat[:, :, 2]),
                    w_mat[:, :, 3], (w_mat[:, :, 4] + w_mat[:, :, 5])
                )

                if np.isnan(bs1_s1):
                    continue

                # 阶段2: 阴影土壤 vs 植被
                rad_res_e = rad_e - w_mat[:, :, 0] * bs1_s1
                rad_res_i = rad_i - w_mat[:, :, 3] * bs1_s1

                bs2_s2, bv_s2 = solve_constrained_vectorized2_center(
                    rad_res_e, rad_res_i,
                    w_mat[:, :, 1], w_mat[:, :, 2],
                    w_mat[:, :, 4], w_mat[:, :, 5],
                    bs1_s1, dif=dif
                )

                if np.isnan(bs2_s2) or np.isnan(bv_s2):
                    continue

                # 物理修正
                if bs2_s2 > bs1_s1:
                    bs2_s2 = bs1_s1

                # 阶段3:【重点修改：替换为信息几何自然梯度】
                x_prior = np.stack([bs1_s1, bs2_s2, bv_s2], axis=-1)
                bs1_f, bs2_f, bv_f = solve_joint_natural_gradient(
                    rad_e, rad_i, w_mat, x_prior, wavelength, lmbda=lmbda_val
                )

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