import os
import numpy as np
from datetime import datetime, timedelta
from base.util_data import *
from base.util_lsct import *
from base.util_file import *
from base.util_fitting import *
from scipy.optimize import fmin


def fitting_DTCRL(obs, pst, fhs, fn, x0=np.asarray([6, 16, 14, 6, 1, 0.5])):
    res = fmin(cost_DTCRL, x0, args=(obs, pst, fhs, fn), disp=0)
    return res
def fitting_DTC( obs,pst, x0):
    res = fmin(cost_DTC, x0,args=(obs,pst), disp = 0)
    return res
def fitting_DTCLSFRL(obs,pst,kLSF,fhs,fn,x0 = np.asarray([6,16,14,6,0.5,1,0.5])):
    res = fmin(cost_DTCLSFRL, x0,args=(obs,pst,kLSF,fhs,fn), disp = 0)
    return res

# ================= 配置路径 =================
indir_root = "/Users/bianzj/Downloads/data/PRODUCTS/SITE/"
infile_sites = "/Users/bianzj/Downloads/data/msg/sites.txt"

site_info = read_txt_str(infile_sites, r",")
site_geo = {row[0]: float(row[1]) for row in site_info}
site_names = list(site_geo.keys())
site_names = ['Faidherbia']

years = ["2017"]
months = [f"{m:02d}" for m in range(8, 9)]
days = [f"{d:02d}" for d in range(10, 11)]
deg2rad = np.pi / 180.0

for site in site_names:
    site_path = os.path.join(indir_root, site)
    static_path = os.path.join(site_path, "static")
    if not os.path.exists(static_path): continue

    lon = site_geo[site]

    # --- 2. 读取静态数据 ---
    vza_e, _, _, _, _, _ = read_image_gdal(os.path.join(static_path, "vza_e.tif"))
    vaa_e, _, _, _, _, _ = read_image_gdal(os.path.join(static_path, "vaa_e.tif"))
    vza_i, _, _, _, _, _ = read_image_gdal(os.path.join(static_path, "vza_i.tif"))
    vaa_i, _, _, _, _, _ = read_image_gdal(os.path.join(static_path, "vaa_i.tif"))

    for yr in years:
        for mn in months:
            for dy in days:
                date_dir = os.path.join(site_path, yr, mn, dy)
                if not os.path.exists(date_dir): continue

                # --- 修复点 1: 用 strptime 创建基准时间，避免 callable 错误 ---
                base_dt = datetime.datetime.strptime(f"{yr}{mn}{dy}", "%Y%m%d")

                lai_file = os.path.join(date_dir, f"LAI_{yr}{mn}{dy}.tif")
                if not os.path.exists(lai_file): continue
                lai, _, _, _, _, _ = read_image_gdal(lai_file)

                day_lst_e, day_lst_i = [], []
                day_sza, day_saa = [], []
                day_ltimes = []

                files_in_day = os.listdir(date_dir)

                for hr in range(5,20):
                    hour_str = f"{yr}{mn}{dy}{hr:02d}"
                    target_e = [f for f in files_in_day if f.startswith(f"LST_{hour_str}") and f.endswith("_e.tif")]
                    if not target_e: continue

                    f_e_name = target_e[0]
                    time_id = f_e_name.split("_")[1]

                    f_e = os.path.join(date_dir, f_e_name)
                    f_i = os.path.join(date_dir, f"LST_{time_id}_i.tif")
                    f_sza = os.path.join(date_dir, f"SZA_{time_id}.tif")
                    f_saa = os.path.join(date_dir, f"SAA_{time_id}.tif")

                    # 读取 LST
                    l_e, _, _, _, _, _ = read_image_gdal(f_e)
                    if not os.path.exists(f_i): continue
                    l_i, _, _, _, _, _ = read_image_gdal(f_i)

                    # --- 修复点 2: 完善夜晚时间与角度逻辑 ---
                    utc_dt = datetime.datetime.strptime(time_id, "%Y%m%d%H%M")
                    local_dt = utc_dt + timedelta(hours=lon / 15.0)

                    # 计算相对于当天 00:00 的小时数（支持跨天，解决拟合时的单调性问题）
                    ltime = (local_dt - base_dt).total_seconds() / 3600.0

                    if os.path.exists(f_sza) and os.path.exists(f_saa):
                        sz, _, _, _, _, _ = read_image_gdal(f_sza)
                        sa, _, _, _, _, _ = read_image_gdal(f_saa)
                        # 夜晚角度强制设为 85
                        sz[sz > 85] = 85.0
                    else:
                        sz = np.full_like(l_e, 85.0)
                        sa = np.zeros_like(l_e)

                    day_lst_e.append(l_e / 100.0 + 273.15)
                    day_lst_i.append(l_i / 100.0 + 273.15)
                    day_sza.append(sz)
                    day_saa.append(sa)
                    day_ltimes.append(ltime)

                n = len(day_ltimes)
                if n > 0:
                    stack_lst_e = np.stack(day_lst_e)  # (N, 5, 5)
                    stack_lst_i = np.stack(day_lst_i)
                    stack_sza = np.stack(day_sza)
                    stack_saa = np.stack(day_saa)
                    stack_times = np.array(day_ltimes)

                    # --- 修复点：利用广播机制代替 repeat，并修正方位角减法 ---
                    # stack_saa 是 (N, 5, 5)，vaa_e 是 (5, 5)
                    # NumPy 会自动将 (5, 5) 匹配到 (N, 5, 5) 的后两个维度

                    # 计算轨道 e 的角度核
                    stack_vsa_e = np.abs(stack_saa - vaa_e)
                    stack_vsa_e[stack_vsa_e > 180] = 360 - stack_vsa_e[stack_vsa_e > 180]
                    # kernel_RLf 的输入：vza_e (5,5), stack_sza (N,5,5), stack_vsa_e (N,5,5)
                    fhs_e = kernel_RLf(vza_e, stack_sza, stack_vsa_e)
                    klsf_e = kernel_LSF(vza_e)

                    # 计算轨道 i 的角度核
                    stack_vsa_i = np.abs(stack_saa - vaa_i)
                    stack_vsa_i[stack_vsa_i > 180] = 360 - stack_vsa_i[stack_vsa_i > 180]
                    fhs_i = kernel_RLf(vza_i, stack_sza, stack_vsa_i)

                    klsf_i = kernel_LSF(vza_i)
                    fn = np.tan(stack_sza * deg2rad)
                    # --- 提取中心点序列进行拟合 ---
                    idx_r, idx_c = 2, 2
                    fn_temp = np.hstack([fn[:, idx_r, idx_c], fn[:, idx_r, idx_c]])
                    fhs_temp = np.hstack([fhs_e[:, idx_r, idx_c], fhs_i[:, idx_r, idx_c]])
                    lst_temp = np.hstack([stack_lst_e[:, idx_r, idx_c], stack_lst_i[:, idx_r, idx_c]])
                    pst_temp = np.hstack([stack_times, stack_times])
                    klsf_temp = np.hstack([klsf_e,klsf_i])

                    x0_fit = np.asarray([273.15, 25, 14, 6, 3, 0.5])
                    result_dtcrl = fitting_DTCRL(lst_temp, pst_temp, fhs_temp, fn_temp, x0=x0_fit)
                    fitted_dtcrl = model_DTCRL(result_dtcrl, pst_temp, fhs_temp, fn_temp)
                    rmse_dtcrl = np.sqrt(np.mean((lst_temp - fitted_dtcrl) ** 2))


                    # --- 6. 绘图部分 ---
                    plt.figure(figsize=(10, 6))

                    # 提取 e 卫星数据 (前 n 个点)
                    obs_e = lst_temp[:n]
                    fit_e = fitted_dtcrl[:n]
                    # 提取 i 卫星数据 (后 n 个点)
                    obs_i = lst_temp[n:]
                    fit_i = fitted_dtcrl[n:]

                    # 绘制观测点 (散点)
                    plt.scatter(stack_times, obs_e, color='blue', label='Obs LST (e)', alpha=0.6, marker='o')
                    plt.scatter(stack_times, obs_i, color='red', label='Obs LST (i)', alpha=0.6, marker='x')

                    # 绘制拟合线 (直线)
                    # 注意：如果时间不是排序的，画线会乱。这里按照时间正向排序绘图
                    sort_idx = np.argsort(stack_times)
                    plt.plot(stack_times[sort_idx], fit_e[sort_idx], color='blue', linestyle='--',
                             label='Fitted DTC-RL (e)')
                    plt.plot(stack_times[sort_idx], fit_i[sort_idx], color='red', linestyle='-',
                             label='Fitted DTC-RL (i)')

                    # 图表修饰
                    plt.title(f"Site: {site} | Date: {yr}-{mn}-{dy} | RMSE: {rmse_dtcrl:.3f}")
                    plt.xlabel("Local Time (Hours)")
                    plt.ylabel("Temperature (K)")
                    plt.legend()
                    plt.grid(True, linestyle=':', alpha=0.7)
                    plt.show() # 如果在本地运行可以打开这个



                    print(f"站点 {site} {yr}-{mn}-{dy} 处理完成: 样本数 {n}, RMSE {rmse_dtcrl:.4f}")