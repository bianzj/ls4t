import os
import numpy as np
import pandas as pd
import pvlib
from pvlib.location import Location
from base.util_data import *
from base.util_lsct import *
from base.util_file import *
from base.util_plot import *

# ================= 配置路径 =================
indir = "/Users/bianzj/Downloads/data/"
indir0_euro = indir + '/PRODUCTS/MSG/MLST/HDF5'
indir0_iodc = indir + '/PRODUCTS/MSG-IODC/MLST/HDF5'
indir0_lai = indir + '/lai/'
outdir_root = indir + '/PRODUCTS/SITE/'  # 提取后的存放根目录
if not os.path.exists(outdir_root): os.makedirs(outdir_root)

altitude = 0  # 用于计算太阳角度的海拔高度

# ================= 1. 读取全局静态数据 =================
print("正在读取静态数据及坐标映射...")
infile_source = indir + "/map/MCD12C1_2011_0.01.tif"
infile_vza_i = indir + "/msg/static/MSG_vza.tif"
infile_vaa_i = indir + "/msg/static/MSG_vaa.tif"
infile_lat_i = indir + "/msg/static/IODC_lat.tif"
infile_lon_i = indir + "/msg/static/IODC_lon.tif"
targevar = "LST"
# 读取角度和经纬度
[vza, nll, nss, _, _, _, _] = read_image_dataset_gdal(infile_vza_i)
[vaa, _, _, _, _, _, _] = read_image_dataset_gdal(infile_vaa_i)
[lat, _, _, _, _, _, _] = read_image_dataset_gdal(infile_lat_i)
[lon, _, _, _, _, _, _] = read_image_dataset_gdal(infile_lon_i)

# 角度校正
vza, vaa = vza / 100.0, (360 + vaa / 100.0) % 360
lat, lon = lat / 100.0, lon / 100.0
ind = (lat > 90) | (lat < -90)
lat[ind] = np.nan
lon[ind] = np.nan
lat = flipud(lat)

# 土地类型映射 (针对 MSG 网格)
[land_type_map, _, _, _, _, _, dataset_map] = read_image_dataset_gdal(infile_source)
indx, indy = loc2map(lat.flatten(), lon.flatten(), dataset_map)
indx, indy = indx.reshape(nll, nss), indy.reshape(nll, nss)
land_type = land_type_map[indx, indy].astype(np.int16)

# 发射率读取与处理
indir_ems = indir + '/lse/'
infile_soil_emis = indir_ems + 'emis1.tif'
infile_veg_emis = indir_ems + 'IGBP_Emi.txt'
[emis_s_full, _, _, _, _, _] = read_image_gdal(infile_soil_emis)
emis_s = emis_s_full[indx, indy]
if np.nanmean(emis_s[emis_s > 0]) > 1.0:
    emis_s = emis_s / 1000.0

emis_v_table = read_txt_array(infile_veg_emis, 0, 2)
emis_v = emis_v_table[land_type, 0] / 1000.0

# ================= 2. 站点定位 =================
infile_sites = indir + "/msg/sites.txt"
site_info = read_txt_str(infile_sites, r",")
site_names = [_[0] for _ in site_info]
site_lats = np.array([_[1] for _ in site_info], dtype=float)
site_lons = np.array([_[2] for _ in site_info], dtype=float)
num_sites = len(site_names)

half = 2  # 5x5 窗口范围
nl_s, ns_s = 2 * half + 1, 2 * half + 1
num_s = nl_s * ns_s

# 计算各站点在矩阵中的中心行列索引
lin_ = []
col_ = []
for k in range(num_sites):
    # 计算距离平方
    distance = (lon - site_lons[k]) ** 2 + (lat - site_lats[k]) ** 2

    # 核心修改：使用 np.nanargmin 忽略 NaN 值
    try:
        min_idx = np.nanargmin(distance)
        r, c = np.unravel_index(min_idx, lat.shape)
        lin_.append(r)
        col_.append(c)
    except ValueError:
        # 如果整张距离表全是 NaN（比如该站点对应的 lon/lat 全是无效值），nanargmin 会报错
        print(f"Warning: Site {k} has no valid coordinates in the grid.")
        lin_.append(None)  # 或者根据需求填入 np.nan
        col_.append(None)

# ================= 3. 提取并保存静态数据 (TIF格式) =================
print("正在保存站点静态数据切片...")
for ksite in range(num_sites):
    r, c = lin_[ksite], col_[ksite]
    l1, l2, c1, c2 = r - half, r + half + 1, c - half, c + half + 1

    # 建立目录: 站点/static/
    site_static_dir = os.path.join(outdir_root, site_names[ksite], "static")
    if not os.path.exists(site_static_dir): os.makedirs(site_static_dir)

    # 提取切片并保存为 TIF

    write_image_gdal(vza[l1:l2, c1:c2], nl_s, ns_s, 1, "", "", os.path.join(site_static_dir, "vza_i.tif"))
    write_image_gdal(vaa[l1:l2, c1:c2], nl_s, ns_s, 1, "", "", os.path.join(site_static_dir, "vaa_i.tif"))


# ================= 4. 循环提取动态数据 =================
for kyear in range(2017, 2018):
    for kmonth in range(8, 13):
        for kday in range(1, 32):
            date_str = "%04d%02d%02d" % (kyear, kmonth, kday)

            # --- 4.1 处理 LAI (每天提取一次) ---
            kdoy = date2DOY(kyear, kmonth, kday)
            kkdoy = int(kdoy / 4) * 4 + 1
            infile_lai = os.path.join(indir0_lai, "%04d" % kyear, "lai_%04d%03d.tif" % (kyear, kkdoy))



            # --- 4.2 处理逐小时 LST 及太阳角度 ---
            for khour in range(0, 24):
                file_id = "%04d%02d%02d%02d00" % (kyear, kmonth, kday, khour)
                indir_h = os.path.join(indir0_iodc, "%04d/%02d/%02d" % (kyear, kmonth, kday))
                infile_lst = os.path.join(indir_h, f"HDF5_LSASAF_MSG-IODC_LST_IODC-Disk_{file_id}")

                if not os.path.exists(infile_lst):
                    continue

                print(f"正在处理站点数据: {file_id}")
                with h5py.File(infile_lst, 'r') as f:
                    # 获取 LST 变量
                    if targevar not in f:
                        print(f"跳过 {infile_lst}: 未找到 LST 变量")
                        continue

                    ds_lst = f[targevar]
                    raw_data = ds_lst[:]  # 原始数据通常是 int16

                    # 获取元数据 (LSA SAF 规范)
                    missing_val = ds_lst.attrs.get('MISSING_VALUE', -8000)
                    # 如果你想保存物理值(Kelvin)，需要乘 SCALING_FACTOR (通常是 0.1)
                    # 如果想保存 int16 (Kelvin*10) 以节省空间，则直接处理空值

                    # 处理无效值：将 -8000 转为 0，方便保存为 uint16
                    raw_data_clean = raw_data.astype(np.float32)
                    raw_data_clean[raw_data == missing_val] = np.nan

                for ksite in range(num_sites):
                    r, c = lin_[ksite], col_[ksite]
                    l1, l2, c1, c2 = r - half, r + half + 1, c - half, c + half + 1

                    # 建立存储目录: 站点/年/月/日/
                    outdir = os.path.join(outdir_root, site_names[ksite], "%04d" % kyear, "%02d" % kmonth,
                                          "%02d" % kday)
                    if not os.path.exists(outdir): os.makedirs(outdir)


                    # 保存 LST
                    write_image_gdal(raw_data_clean[l1:l2, c1:c2], nl_s, ns_s, 1, "", "",
                                     os.path.join(outdir, f"LST_{file_id}_i.tif"))


print("站点周边数据 TIF 提取任务全部完成。")