import os
import numpy as np
from datetime import datetime, timedelta
from base.util_data import *
from base.util_lsct import *
from base.util_file import *
from base.util_kernel import *
from base.util_fitting import *

# ================= 配置路径 =================
indir_root = "/Users/bianzj/Downloads/data/PRODUCTS/SITE/"
infile_sites = "/Users/bianzj/Downloads/data/msg/sites.txt"

# --- 1. 读取站点信息 (经度用于计算当地时) ---
site_info = read_txt_str(infile_sites, r",")
# 假设格式: 站点名, 经度, 纬度...
site_geo = {row[0]: float(row[1]) for row in site_info}
site_names = list(site_geo.keys())

# 处理配置
years = ["2017"]
months = [f"{m:02d}" for m in range(1, 13)]
days = [f"{d:02d}" for d in range(1, 32)]





for site in site_names:
    site_path = os.path.join(indir_root, site)
    static_path = os.path.join(site_path, "static")
    if not os.path.exists(static_path): continue

    lon = site_geo[site]  # 获取经度

    # --- 2. 读取静态数据 (Shape: 5, 5) ---
    vza_e, _, _, _, _, _ = read_image_gdal(os.path.join(static_path, "vza_e.tif"))
    vaa_e, _, _, _, _, _ = read_image_gdal(os.path.join(static_path, "vaa_e.tif"))
    vza_i, _, _, _, _, _ = read_image_gdal(os.path.join(static_path, "vza_i.tif"))
    vaa_i, _, _, _, _, _ = read_image_gdal(os.path.join(static_path, "vaa_i.tif"))

    # --- 3. 逐年月日层级进入 ---
    for yr in years:
        for mn in months:
            for dy in days:
                date_dir = os.path.join(site_path, yr, mn, dy)
                if not os.path.exists(date_dir): continue

                # 读取该日 LAI (Shape: 5, 5)
                lai_file = os.path.join(date_dir, f"LAI_{yr}{mn}{dy}.tif")
                if not os.path.exists(lai_file): continue
                lai, _, _, _, _, _ = read_image_gdal(lai_file)

                # --- 4. 逐小时检索并收集 (收集 00-23 小时) ---
                day_lst_e, day_lst_i = [], []
                day_sza, day_saa = [], []
                day_ltimes = []

                # 获取该目录下所有文件列表，减少多次磁盘IO查询
                files_in_day = os.listdir(date_dir)

                for hr in range(3,20):
                    # 构造小时前缀，例如 "2017081012" (对应12点)
                    hour_str = f"{yr}{mn}{dy}{hr:02d}"

                    # 查找该小时的文件 (假设分钟为00，或根据前缀匹配)
                    # 匹配格式如: LST_201708101200_e.tif
                    target_e = [f for f in files_in_day if f.startswith(f"LST_{hour_str}") and f.endswith("_e.tif")]

                    if not target_e: continue

                    # 拿到具体文件名
                    f_e_name = target_e[0]
                    time_id = f_e_name.split("_")[1]  # 完整的时间戳 201708101200

                    # 定义关联文件路径
                    f_e = os.path.join(date_dir, f_e_name)
                    f_i = os.path.join(date_dir, f"LST_{time_id}_i.tif")
                    f_sza = os.path.join(date_dir, f"SZA_{time_id}.tif")
                    f_saa = os.path.join(date_dir, f"SAA_{time_id}.tif")

                    l_e, _, _, _, _, _ = read_image_gdal(f_e)
                    l_i, _, _, _, _, _ = read_image_gdal(f_i)

                    # --- 计算当地时间 (Local Time) ---
                    utc_dt = datetime.strptime(time_id, "%Y%m%d%H%M")
                    # UTC + (经度/15)
                    local_dt = utc_dt + timedelta(hours=lon / 15.0)
                    # 转换为 0-24 的浮点数 (如 13:30 = 13.5)
                    ltime = local_dt.hour + local_dt.minute / 60.0


                    # 确保所有必要时刻的文件都存在
                    if all(os.path.exists(p) for p in [f_i, f_sza, f_saa]):
                        # 读取动态数据
                        sz, _, _, _, _, _ = read_image_gdal(f_sza)
                        sa, _, _, _, _, _ = read_image_gdal(f_saa)
                        # --- 计算角度 (VSA) ---
                        # v_e = np.abs(sa - vaa_e)
                        # v_e[v_e > 180] = 360 - v_e[v_e > 180]
                        # v_i = np.abs(sa - vaa_i)
                        # v_i[v_i > 180] = 360 - v_i[v_i > 180]
                    else:
                        sz = np.zeros_like(l_e)
                        sa = np.zeros_like(l_i)



                    day_lst_e.append(l_e / 100.0 + 273.15)
                    day_lst_i.append(l_i / 100.0 + 273.15)
                    day_ltimes.append(ltime)
                    day_sza.append(sz)
                    day_saa.append(sa)


                # --- 5. 将该天所有小时的数据压成 narray ---
                if len(day_ltimes) > 0:
                    # 转换为 (N, 5, 5) 形状的数组
                    stack_lst_e = np.stack(day_lst_e)
                    stack_lst_i = np.stack(day_lst_i)
                    stack_sza = np.stack(day_sza)
                    stack_saa_e = np.stack(day_saa)


                    # 转换为 (N,) 的当地时间轴
                    stack_times = np.array(day_ltimes)

                    # -----------------------------------------------------
                    # 此时，这一天的数据已经全部压好。
                    # 你可以直接进行大规模矩阵运算：
                    # 示例：假设你要用 stack_lst_e 进行反演计算
                    # 计算量虽大，但利用 numpy 的维度广播 (Broadcasting) 会非常快。
                    # -----------------------------------------------------

                    print(f"站点 {site} 日期 {yr}-{mn}-{dy} 处理完成: "
                          f"共压入 {len(stack_times)} 小时的数据。")