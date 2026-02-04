import os
import csv
import numpy as np
from datetime import timedelta
import datetime as dt
from scipy.optimize import fmin

# 假设这些工具函数已正确定义在你的 base 包中
from base.util_data import *
from base.util_lsct import *
from base.util_file import *
from base.util_fitting import *
from scipy.optimize import fmin  # 确保是从这里导入

MINIMIZE_METHODS = ['nelder-mead', 'powell', 'cg', 'bfgs', 'newton-cg',
                    'l-bfgs-b', 'tnc', 'cobyla', 'slsqp', 'trust-constr',
                    'dogleg', 'trust-ncg', 'trust-exact', 'trust-krylov']
method = 'nelder-mead'

# ================= 拟合封装 =================
def fitting_DTCRL(obs, pst, fhs, fn, x0):
    return fmin(cost_DTCRL, x0, args=(obs, pst, fhs, fn), disp=0)
    # return minimize(cost_DTCRL,x0,args=(obs, pst, fhs, fn),
    #                method=method).x


def fitting_DTC(obs, pst, x0):
    return fmin(cost_DTC, x0, args=(obs, pst), disp=0)


def fitting_DTCLSFRL(obs, pst, klsf, fhs, fn, x0):
    return fmin(cost_DTCLSFRL, x0, args=(obs, pst, klsf, fhs, fn), disp=0)


# ================= 路径配置 =================
indir_root = "/Users/bianzj/Downloads/data/PRODUCTS/SITE/"
infile_sites = "/Users/bianzj/Downloads/data/msg/sites.txt"

years = ["2017"]
months = [f"{m:02d}" for m in range(8, 12)]
days = [f"{d:02d}" for d in range(1, 32)]
deg2rad = np.pi / 180.0

# ================= 站点信息 =================
site_info = read_txt_str(infile_sites, r",")
site_geo = {row[0]: float(row[1]) for row in site_info}
site_names = list(site_geo.keys())

# ================= CSV 初始化 =================
out_csv = "/Users/bianzj/Downloads/data/PRODUCTS/SITE/ALL_SITES_LST_FITTING_RESULTS.csv"
csv_f = open(out_csv, "w", newline="")
writer = csv.writer(csv_f)

writer.writerow([
    "site", "date", "sensor", "local_time", "LAI",
    "VZA", "VAA", "SZA", "SAA", "LST_obs",
    "LST_fit_DTC", "LST_fit_DTCRL", "LST_fit_DTCLSFRL",
    "LST_nadir_DTC", "LST_nadir_DTCRL", "LST_nadir_DTCLSFRL"
])

# ================= 主循环 =================
for site in site_names:
    site_path = os.path.join(indir_root, site)
    static_path = os.path.join(site_path, "static")
    if not os.path.exists(static_path):
        continue

    lon = site_geo[site]
    idx_r, idx_c = 2, 2  # 目标行列号

    # 预读静态角度数据
    try:
        vza_e_img, *_ = read_image_gdal(os.path.join(static_path, "vza_e.tif"))
        vaa_e_img, *_ = read_image_gdal(os.path.join(static_path, "vaa_e.tif"))
        vza_i_img, *_ = read_image_gdal(os.path.join(static_path, "vza_i.tif"))
        vaa_i_img, *_ = read_image_gdal(os.path.join(static_path, "vaa_i.tif"))

        vza_e = vza_e_img[idx_r, idx_c]
        vaa_e = vaa_e_img[idx_r, idx_c]
        vza_i = vza_i_img[idx_r, idx_c]
        vaa_i = vaa_i_img[idx_r, idx_c]
    except Exception as e:
        print(f"Error reading static data for {site}: {e}")
        continue

    for yr in years:
        for mn in months:
            for dy in days:
                date_dir = os.path.join(site_path, yr, mn, dy)
                if not os.path.exists(date_dir):
                    continue

                base_dt = dt.datetime.strptime(f"{yr}{mn}{dy}", "%Y%m%d")
                lai_file = os.path.join(date_dir, f"LAI_{yr}{mn}{dy}.tif")
                if not os.path.exists(lai_file):
                    continue

                # 读取LAI
                lai_img, *_ = read_image_gdal(lai_file)
                val_lai = lai_img[idx_r, idx_c]

                records = []
                files = os.listdir(date_dir)

                # 收集日内观测序列
                for hr in range(5, 18):
                    hour_str = f"{yr}{mn}{dy}{hr:02d}"
                    targets = [f for f in files if f.startswith(f"LST_{hour_str}") and f.endswith("_e.tif")]
                    if not targets:
                        continue

                    f_e_name = targets[0]
                    time_id = f_e_name.split("_")[1]

                    f_i_path = os.path.join(date_dir, f"LST_{time_id}_i.tif")
                    f_sza_path = os.path.join(date_dir, f"SZA_{time_id}.tif")
                    f_saa_path = os.path.join(date_dir, f"SAA_{time_id}.tif")

                    if not os.path.exists(f_i_path):
                        continue

                    # 读取LST和SZA/SAA
                    l_e_img, *_ = read_image_gdal(os.path.join(date_dir, f_e_name))
                    l_i_img, *_ = read_image_gdal(f_i_path)

                    if os.path.exists(f_sza_path) and os.path.exists(f_saa_path):
                        sza_img, *_ = read_image_gdal(f_sza_path)
                        saa_img, *_ = read_image_gdal(f_saa_path)
                        val_sza = sza_img[idx_r, idx_c]
                        val_saa = saa_img[idx_r, idx_c]
                        if val_sza > 85: val_sza = 85.0
                    else:
                        val_sza, val_saa = 85.0, 0.0

                    # 计算当地时
                    utc = dt.datetime.strptime(time_id, "%Y%m%d%H%M")
                    ltime = utc.hour

                    # 添加观测 (E)
                    records.append({
                        "sensor": "E", "time": ltime, "LST": l_e_img[idx_r, idx_c] / 100.0 + 273.15,
                        "VZA": vza_e, "VAA": vaa_e, "SZA": val_sza, "SAA": val_saa, "LAI": val_lai
                    })
                    # 添加观测 (I)
                    records.append({
                        "sensor": "I", "time": ltime, "LST": l_i_img[idx_r, idx_c] / 100.0 + 273.15,
                        "VZA": vza_i, "VAA": vaa_i, "SZA": val_sza, "SAA": val_saa, "LAI": val_lai
                    })

                # 数据量检查
                if len(records) < 16:
                    continue

                # ======== 构造拟合数组并过滤无效值 ========
                obs = np.array([r["LST"] for r in records])
                pst = np.array([r["time"] for r in records])
                sza = np.array([r["SZA"] for r in records])
                vza = np.array([r["VZA"] for r in records])
                saa = np.array([r["SAA"] for r in records])
                vaa = np.array([r["VAA"] for r in records])

                # 有效性掩码 (LST 必须有限且 > 0)
                mask = np.isfinite(obs) & (obs > 0)
                if np.sum(mask) < 16:
                    continue

                obs, pst, sza, vza, saa, vaa = obs[mask], pst[mask], sza[mask], vza[mask], saa[mask], vaa[mask]

                # 更新 records 以便后续写入 CSV
                filtered_records = [r for i, r in enumerate(records) if mask[i]]

                # 计算核函数所需中间变量
                vsa = np.abs(saa - vaa)
                vsa[vsa > 180] = 360 - vsa[vsa > 180]

                fhs = kernel_RLf(vza, sza, vsa)
                fn = np.tan(sza * deg2rad)
                klsf = kernel_LSF(vza)

                # ======== 执行拟合 ========
                t0_guess = 285.15
                try:
                    p_dtc = fitting_DTC(obs, pst, [t0_guess, 20, 14, 6])
                    p_dtcrl = fitting_DTCRL(obs, pst, fhs, fn, [t0_guess, 20, 14, 6, 1, 1.5])
                    p_dtclsfrl = fitting_DTCLSFRL(obs, pst, klsf, fhs, fn, [t0_guess, 20, 14, 6, 0.5, 1, 1.5])

                    # 计算观测几何下的拟合值
                    fit_dtc = model_DTC(p_dtc, pst)
                    fit_dtcrl = model_DTCRL(p_dtcrl, pst, fhs, fn)
                    fit_dtclsfrl = model_DTCLSFRL(p_dtclsfrl, pst, klsf, fhs, fn)

                    # 计算天底 (Nadir, VZA=0) 情况下的预测值
                    fhs0 = kernel_RLf(0.0, sza, np.zeros_like(sza))
                    fn0 = fn
                    klsf0_val = kernel_LSF(0.0)
                    klsf0 = np.full_like(pst, klsf0_val)

                    nadir_dtc = model_DTC(p_dtc, pst)
                    nadir_dtcrl = model_DTCRL(p_dtcrl, pst, fhs0, fn0)
                    nadir_dtclsfrl = model_DTCLSFRL(p_dtclsfrl, pst, klsf0, fhs0, fn0)

                    # ======== 写入 CSV ========
                    for i, r in enumerate(filtered_records):
                        writer.writerow([
                            site, f"{yr}-{mn}-{dy}", r["sensor"],
                            f"{r['time']:.4f}", f"{r['LAI']:.4f}",
                            f"{r['VZA']:.2f}", f"{r['VAA']:.2f}",
                            f"{r['SZA']:.2f}", f"{r['SAA']:.2f}",
                            f"{r['LST']:.2f}",
                            f"{fit_dtc[i]:.2f}", f"{fit_dtcrl[i]:.2f}", f"{fit_dtclsfrl[i]:.2f}",
                            f"{nadir_dtc[i]:.2f}", f"{nadir_dtcrl[i]:.2f}", f"{nadir_dtclsfrl[i]:.2f}"
                        ])
                except Exception as e:
                    print(f"Fitting failed for {site} on {yr}{mn}{dy}: {e}")
                    continue

csv_f.close()
print("Processing complete.")

try:
    import subprocess
    print("正在自动执行验证脚本...")
    # 假设你的验证脚本叫 verify_kal.py
    subprocess.run(["python", "msg-val-evo.py"], check=True)
    subprocess.run(["python", "msg-val-kal.py"], check=True)
except Exception as e:
    print(f"自动验证失败: {e}")


