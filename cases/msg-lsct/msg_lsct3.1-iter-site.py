import os
import glob
import numpy as np
import pandas as pd
from base.util_data import *
from base.util_lsct import *
from base.util_file import *
import numpy as np
from scipy.ndimage import uniform_filter

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
indir0_euro = indir + '/PRODUCTS/MSG/MLST/GEOTIFF'
indir0_euro_lai = indir + '/PRODUCTS/MSG/MDLAI/GEOTIFF'
indir0_iodc = indir + '/PRODUCTS/MSG-IODC/MLST/GEOTIFF'
indir0_lai = indir + '/lai/'
infile_sites = indir + "/field/sites.txt"
outdir_root = indir + '/PRODUCTS/LSCT/MLST_COMPONENT/'
indir_root = indir + "/PRODUCTS/SITE/"
outfile_csv = indir + "/PRODUCTS/LSCT_Site_Results.csv"

# ================= 核心反演参数 =================
wavelength = 10.5
hspot_val = 0.1
lmbda_val = 0.1  # 联合平差的先验权重

# 读取站点列表
site_info = read_txt_str(infile_sites, r",")
site_names = [_[0] for _ in site_info]

results_list = []

print(f"开始处理站点反演，共 {len(site_names)} 个站点...")

for site in site_names:
    site_path = os.path.join(indir_root, site)
    static_path = os.path.join(site_path, "static")

    if not os.path.exists(static_path):
        continue

    # --- 1. 读取站点静态数据 (5x5) ---
    vza_e, _, _, _, _, _ = read_image_gdal(os.path.join(static_path, "vza_e.tif"))
    vaa_e, _, _, _, _, _ = read_image_gdal(os.path.join(static_path, "vaa_e.tif"))
    vza_i, _, _, _, _, _ = read_image_gdal(os.path.join(static_path, "vza_i.tif"))
    vaa_i, _, _, _, _, _ = read_image_gdal(os.path.join(static_path, "vaa_i.tif"))
    emis_s, _, _, _, _, _ = read_image_gdal(os.path.join(static_path, "emis_s.tif"))
    emis_v, _, _, _, _, _ = read_image_gdal(os.path.join(static_path, "emis_v.tif"))
    land_type, _, _, _, _, _ = read_image_gdal(os.path.join(static_path, "lc.tif"))

    # --- 2. 遍历时间 (年/月/日) ---
    # 搜索该站点下所有的日期文件夹
    date_folders = glob.glob(os.path.join(site_path, "2017/*/*"))

    for date_dir in sorted(date_folders):
        # 提取日期信息
        parts = date_dir.replace("\\", "/").split("/")
        year, month, day = parts[-3], parts[-2], parts[-1]
        date_str = f"{year}{month}{day}"

        # 读取该日 LAI
        lai_file = os.path.join(date_dir, f"LAI_{date_str}.tif")
        if not os.path.exists(lai_file): continue
        lai, _, _, _, _, _ = read_image_gdal(lai_file)

        # --- 3. 遍历小时 (寻找对齐的 LST_e 和 LST_i) ---
        lst_e_files = glob.glob(os.path.join(date_dir, "LST_*_e.tif"))

        for f_e in lst_e_files:
            file_id = os.path.basename(f_e).split("_")[1]  # 提取 201708101200
            f_i = f_e.replace("_e.tif", "_i.tif")
            f_sza = os.path.join(date_dir, f"SZA_{file_id}.tif")
            f_saa = os.path.join(date_dir, f"SAA_{file_id}.tif")

            if not (os.path.exists(f_i) and os.path.exists(f_sza)):
                continue

            # 读取动态切片
            lst_e, _, _, _, _, _ = read_image_gdal(f_e)
            lst_i, _, _, _, _, _ = read_image_gdal(f_i)
            sza, _, _, _, _, _ = read_image_gdal(f_sza)
            saa, _, _, _, _, _ = read_image_gdal(f_saa)
            lst_e = lst_e/100.0+273.15
            lst_i = lst_i/100.0+273.15

            # --- 4. 准备反演权重 ---
            vsa_e = np.abs(saa - vaa_e)
            vsa_e[vsa_e > 180] = 360 - vsa_e[vsa_e > 180]
            vsa_i = np.abs(saa - vaa_i)
            vsa_i[vsa_i > 180] = 360 - vsa_i[vsa_i > 180]

            w1, b1 = hotspot_layer(lai, hspot_val, vza_e, sza, vsa_e)
            w2, b2 = hotspot_layer(lai, hspot_val, vza_i, sza, vsa_i)

            # 构造 6 分量权重矩阵 (用于 5x5 窗口)
            w_mat = np.zeros([5, 5, 6])
            w_mat[:, :, 0] = emis_s * w1  # Sunlit Soil Euro
            w_mat[:, :, 1] = emis_s * (b1 - w1)  # Shaded Soil Euro
            w_mat[:, :, 2] = emis_v * (1.0 - b1)  # Veg Euro
            w_mat[:, :, 3] = emis_s * w2  # Sunlit Soil IODC
            w_mat[:, :, 4] = emis_s * (b2 - w2)  # Shaded Soil IODC
            w_mat[:, :, 5] = emis_v * (1.0 - b2)  # Veg IODC

            # 辐射计算 (假设存储的是摄氏度或开尔文，统一转为开尔文)
            if np.nanmean(lst_e) < 150: lst_e += 273.15  # 自动纠正
            if np.nanmean(lst_i) < 150: lst_i += 273.15

            rad_e = planck(wavelength, lst_e) * (w_mat[:, :, 0] + w_mat[:, :, 1] + w_mat[:, :, 2])
            rad_i = planck(wavelength, lst_i) * (w_mat[:, :, 3] + w_mat[:, :, 4] + w_mat[:, :, 5])

            # --- 5. 执行反演算法 ---
            # 阶段 1: 分步求解 (Stepwise)
            # A: 土壤 vs 其余
            w_soil_e = w_mat[:, :, 0] + w_mat[:, :, 1]
            w_veg_e = w_mat[:, :, 2]
            w_soil_i = w_mat[:, :, 3] + w_mat[:, :, 4]
            w_veg_i = w_mat[:, :, 5]

            # 求解整体土壤辐射 (bs_total_rad) 和 植被辐射 (bv_rad)
            bs_s1, bv_s1= solve_2x2_system_5x5(rad_e, rad_i,
                                                        w_soil_e, w_veg_e,
                                                        w_soil_i, w_veg_i, size=3)

            # ---------------------------------------------------------
            # 步骤 B: 第二阶段求解 - 拆分土壤组分 (光照土壤 vs 阴影土壤)
            # ---------------------------------------------------------
            # 在已知 bv_rad 的情况下，减去植被贡献，得到纯土壤的残差辐射响应
            with np.errstate(invalid='ignore'):
                rad_soil_only_e = rad_e - w_veg_e * bv_s1
                rad_soil_only_i = rad_i - w_veg_i * bv_s1

            # 利用光照土壤(w1, w4)和阴影土壤(w2, w5)的权重关系求解 bs1 和 bs2
            # 方程: w1*bs1 + w2*bs2 = rad_soil_only_e
            #      w4*bs1 + w5*bs2 = rad_soil_only_i
            bs1_s2, bs2_s2 = solve_2x2_system_5x5(rad_soil_only_e, rad_soil_only_i,
                                                    w_mat[:, :, 0], w_mat[:, :, 1],
                                                    w_mat[:, :, 3], w_mat[:, :, 4], size=5)
            # 物理边界初步修正
            bs2_s2 = np.where(bs2_s2 > bs1_s2, bs1_s2, bs2_s2)

            # 阶段 2: 联合平差 (Joint Inversion)
            x_prior = np.stack([bs1_s2, bs2_s2, bv_s1], axis=-1)
            bs1_f, bs2_f, bv_f = solve_joint_vectorized_with_prior(rad_e, rad_i, w_mat, x_prior, lmbda=lmbda_val)

            # bs1_f, bs2_f, bv_f = bs_s1, bs_s1, bv_s1

            # --- 6. 提取结果 ---
            # 提取 5x5 窗口的中心像素 (索引 2,2)
            with np.errstate(invalid='ignore'):
                ts1_pix = inv_planck(wavelength, bs1_f[2, 2])
                ts2_pix = inv_planck(wavelength, bs2_f[2, 2])
                tv_pix = inv_planck(wavelength, bv_f[2, 2])
                lst_e_pix = lst_e[2, 2]
                lst_i_pix = lst_i[2, 2]
                sza_pix = sza[2, 2]

            # 保存记录
            results_list.append({
                'Site': site,
                'DateTime': file_id,
                'SZA': np.round(sza_pix, 2),
                'LST_Euro': np.round(lst_e_pix, 2),
                'LST_IODC': np.round(lst_i_pix, 2),
                'T_Sunlit_Soil': np.round(ts1_pix, 2),
                'T_Shaded_Soil': np.round(ts2_pix, 2),
                'T_Vegetation': np.round(tv_pix, 2),
                'LAI': np.round(lai[2, 2], 3)
            })

# --- 7. 输出到 CSV ---
df = pd.DataFrame(results_list)
df.to_csv(outfile_csv, index=False)
print(f"反演完成！结果已保存至: {outfile_csv}")