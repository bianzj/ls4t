import os
import numpy as np
import pandas as pd
from base.files import read_image_dataset_gdal, read_image_gdal, read_txt_array, write_image_gdal
from base.spatial import loc2map

# ================= 配置路径 =================
indir = '/media/hero/MSG/'
indir_rs = '/media/hero/rs/'
indir0_lst_euro = indir + '/PRODUCTS/MSG/MLST/GEOTIFF'
indir0_lst_iodc = indir + '/PRODUCTS/MSG-IODC/MLST/GEOTIFF'
indir0_euro_lai = indir + '/PRODUCTS/MSG/MDLAI/GEOTIFF'
indir0_lsct = indir +  '/PRODUCTS/LSCT/MLST_COMPONENT/'
indir0_lai = indir_rs + '/veg/lai_2021-2025_0.01/'
outdir_root = indir + '/PRODUCTS/SITE/'  # 提取后的存放根目录
if not os.path.exists(outdir_root): os.makedirs(outdir_root)
altitude = 0  # 用于计算太阳角度的海拔高度

# ================= 1. 读取全局静态数据 =================
print("正在读取静态数据及坐标映射...")
infile_ref_world = indir + "/map/MCD12C1_2011_0.01.tif"
infile_vza_e = indir + "/Static/combined_euro_vza.tif"
infile_vaa_e = indir + "/Static/combined_euro_vaa.tif"
infile_lat_e = indir + "/Static/combined_euro_lat.tif"
infile_lon_e = indir + "/Static/combined_euro_lon.tif"
infile_vza_i = indir + "/Static/combined_iodc_vza.tif"
infile_vaa_i = indir + "/Static/combined_iodc_vaa.tif"
targevar = "LST"
# 读取角度和经纬度
[vza, nll, nss, _, _, _, _] = read_image_dataset_gdal(infile_vza_e)
[vaa, _, _, _, _, _, _] = read_image_dataset_gdal(infile_vaa_e)
[lat, _, _, _, _, _, _] = read_image_dataset_gdal(infile_lat_e)
[lon, _, _, _, _, _, _] = read_image_dataset_gdal(infile_lon_e)
[vzai, nss, nll, _, _, _, _] = read_image_dataset_gdal(infile_vza_i)
[vaai, _, _, _, _, _, _] = read_image_dataset_gdal(infile_vaa_i)
# 角度校正
vza, vaa = vza / 100.0, (360 + vaa / 100.0) % 360
vzai, vaai = vzai / 100.0, (360 + vaai / 100.0) % 360
lat, lon = lat / 100.0, lon / 100.0
ind = (lat > 90) | (lat < -90)
lat[ind] = np.nan
lon[ind] = np.nan


# 土地类型映射 (针对 MSG 网格)
[land_type_map, _, _, _, _, _, dataset_map] = read_image_dataset_gdal(infile_ref_world)
indx, indy = loc2map(lat.flatten(), lon.flatten(), dataset_map)
indx, indy = indx.reshape(nll, nss), indy.reshape(nll, nss)
land_type = land_type_map[indx, indy].astype(np.int16)

# 发射率读取与处理
indir_ems = indir + '/lse/'
infile_soil_emis = indir_ems + 'AG1km.v003.SoilEmi.ABI.Global.001D_LSE11.tif'
infile_veg_emis = indir_ems + 'IGBP_Emi.txt'
[emis_s_full, _, _, _, _, _] = read_image_gdal(infile_soil_emis)
emis_s = emis_s_full[indx, indy]
if np.nanmean(emis_s[emis_s > 0]) > 1.0:
    emis_s = emis_s / 1000.0

emis_v_table = read_txt_array(infile_veg_emis, 0, 2)
emis_v = emis_v_table[land_type, 0] / 1000.0

# ================= 2. 站点定位 =================
infile_sites = indir + "/field/sites-2025.csv"
df_sites = pd.read_csv(infile_sites)   # 需包含列: id, lat, lon
site_names = df_sites['id'].astype(str).tolist()
site_lats = df_sites['lat'].values.astype(float)
site_lons = df_sites['lon'].values.astype(float)
num_sites = len(site_names)

half = 2  # 5x5 窗口范围
nl_s, ns_s = 2 * half + 1, 2 * half + 1
num_s = nl_s * ns_s

# 计算各站点在矩阵中的中心行列索引
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
# print("正在保存站点静态数据切片...")
for ksite in range(num_sites):
    r, c = lin_[ksite], col_[ksite]
    l1, l2, c1, c2 = r - half, r + half + 1, c - half, c + half + 1
    site_static_dir = os.path.join(outdir_root, site_names[ksite], "static")
    if not os.path.exists(site_static_dir): os.makedirs(site_static_dir)
    # if os.path.exists(os.path.join(site_static_dir, "lon.tif")):continue
    write_image_gdal(lon[l1:l2, c1:c2], nl_s, ns_s, 1, "", "", os.path.join(site_static_dir, "lon.tif"))
    write_image_gdal(lat[l1:l2, c1:c2], nl_s, ns_s, 1, "", "", os.path.join(site_static_dir, "lat.tif"))
    write_image_gdal(vza[l1:l2, c1:c2], nl_s, ns_s, 1, "", "", os.path.join(site_static_dir, "vza_e.tif"))
    write_image_gdal(vaa[l1:l2, c1:c2], nl_s, ns_s, 1, "", "", os.path.join(site_static_dir, "vaa_e.tif"))
    write_image_gdal(vzai[l1:l2, c1:c2], nl_s, ns_s, 1, "", "", os.path.join(site_static_dir, "vza_i.tif"))
    write_image_gdal(vaai[l1:l2, c1:c2], nl_s, ns_s, 1, "", "", os.path.join(site_static_dir, "vaa_i.tif"))
    write_image_gdal(land_type[l1:l2, c1:c2].astype(np.float32), nl_s, ns_s, 1, "", "",
                     os.path.join(site_static_dir, "lc.tif"))
    write_image_gdal(emis_s[l1:l2, c1:c2], nl_s, ns_s, 1, "", "", os.path.join(site_static_dir, "emis_s.tif"))
    write_image_gdal(emis_v[l1:l2, c1:c2], nl_s, ns_s, 1, "", "", os.path.join(site_static_dir, "emis_v.tif"))
