import os
import numpy as np
import pandas as pd
import h5py
import pvlib
from pvlib.location import Location
# 以下为您的自定义工具模块，请确保它们存在于 sys.path 中
from base.util_data import *
from base.util_lsct import *
from base.util_file import *
from base.util_plot import *

# ================= 配置路径 =================
indir = '/media/hero/MSG/'
indir_rs = '/media/hero/rs/'
indir0_lsct = indir + '/PRODUCTS/LSCT/MLST_COMPONENT/'
indir0_lai = indir_rs + '/veg/lai_2021-2025_0.01/'
indir0_lai = indir_rs + '/veg/lai_2002-2020_0.01/'
outdir_root = indir + '/results/'          # 所有 CSV 直接放在此目录
os.makedirs(outdir_root, exist_ok=True)
altitude = 0

# ================= 1. 读取全局静态数据 =================
print("正在读取静态数据及坐标映射...")
infile_vza_e = indir + "/Static/combined_euro_vza.tif"
infile_vaa_e = indir + "/Static/combined_euro_vaa.tif"
infile_lat_e = indir + "/Static/combined_euro_lat.tif"
infile_lon_e = indir + "/Static/combined_euro_lon.tif"
infile_ref_world = indir + "/map/MCD12C1_2011_0.01.tif"

# 读取数组及尺寸信息
[vza, nss, nll, _, _, _, _] = read_image_dataset_gdal(infile_vza_e)
[vaa, _, _, _, _, _, _] = read_image_dataset_gdal(infile_vaa_e)
[lat, _, _, _, _, _, _] = read_image_dataset_gdal(infile_lat_e)
[lon, _, _, _, _, _, _] = read_image_dataset_gdal(infile_lon_e)

# 角度校正（VZA/VAA 缩放）
vza, vaa = vza / 100.0, (360 + vaa / 100.0) % 360
lat, lon = lat / 100.0, lon / 100.0         # 修正：使用 np.flipud
# 若经纬度存在异常值，置为 NaN
ind = (lat > 90) | (lat < -90)
lat[ind] = np.nan
lon[ind] = np.nan

# 土地类型（此处仅读取作为示例，后续未使用）
[land_type_map, _, _, _, _, _, dataset_map] = read_image_dataset_gdal(infile_ref_world)
indx, indy = loc2map(lat.flatten(), lon.flatten(), dataset_map)
indx, indy = indx.reshape(nll, nss), indy.reshape(nll, nss)
land_type = land_type_map[indx, indy].astype(np.int16)

# ================= 2. 站点定位 =================
infile_sites = indir + "/field/sites-2025.csv"
df_sites = pd.read_csv(infile_sites)   # 需包含列: id, lat, lon
site_names = df_sites['id'].astype(str).tolist()
site_lats = df_sites['lat'].values.astype(float)
site_lons = df_sites['lon'].values.astype(float)
num_sites = len(site_names)

half = 2   # 5×5 窗口（此处仅用中心点，窗口未实际使用）
lin_ = []  # 站点中心行索引
col_ = []  # 站点中心列索引
for k in range(num_sites):
    distance = (lon - site_lons[k])**2 + (lat - site_lats[k])**2
    try:
        min_idx = np.nanargmin(distance)
        r, c = np.unravel_index(min_idx, lat.shape)
        lin_.append(r)
        col_.append(c)
    except ValueError:
        print(f"Warning: 站点 {k} ({site_names[k]}) 在网格中无有效像素")
        lin_.append(None)
        col_.append(None)

# ================= 3. 初始化数据容器 =================
# 按站点存储所有记录，每个记录为 [year, month, day, hour, LST1, LST2, LST3, LST4]
site_data = {name: [] for name in site_names}

# ================= 4. 循环提取动态数据（2025年10月3-4日，9-16时） =================
print("开始提取动态数据...")
lai_cache = []   # 缓存已读取的 LAI 数组，键为文件路径
lai0 = np.zeros([nll,nss])
for kyear in range(2018, 2020):
    for kmonth in range(1, 12):
        for kday in range(1, 32):
            # 处理 LAI（仅示意，若需要可扩展，此处略）
            kdoy = date2DOY(kyear, kmonth, kday)   # 假定 date2DOY 已定义
            kkdoy = int(kdoy / 4) * 4 + 1
            infile_lai = os.path.join(indir0_lai, f"{kyear:04d}", f"LAI_{kyear:04d}{kkdoy:03d}.h5")

            # 若需要 LAI 值，可在此读取并加入记录（略）

            if infile_lai not in lai_cache:
                if not os.path.exists(infile_lai):
                    print(f"LAI 文件缺失: {infile_lai}")
                    lai_full = None
                else:
                    # 读取 LAI 数据（假设读取函数 read_h5py_item 可用）
                    lai_full = read_h5py_item(infile_lai, "/data")  # 或直接用 h5py
                    lai_full = lai_full / 1000.0
                    lai_full[lai_full > 10] = np.nan
                    lai0 = lai_full[indx,indy]
                    lai_cache.append(infile_lai)

            for khour in range(9, 17):
                file_id = f"{kyear:04d}{kmonth:02d}{kday:02d}{khour:02d}00"
                indir_h = os.path.join(indir0_lsct, f"{kyear:04d}/{kmonth:02d}/{kday:02d}")
                infile_lsct = os.path.join(indir_h, f"MSG_LSCT_{file_id}.h5")

                if not os.path.exists(infile_lsct):
                    print(f"文件缺失: {infile_lsct}")
                    continue

                print(f"处理: {file_id}")
                with h5py.File(infile_lsct, 'r') as f:
                    # 自动查找形状为 (4, rows, cols) 的数据集（LST 4分量）
                    ds = next((v for v in f.values()
                               if isinstance(v, h5py.Dataset) and v.ndim == 3 and v.shape[0] == 4), None)
                    if ds is None:
                        print(f"跳过 {infile_lsct}: 未找到符合要求的数据集")
                        continue
                    arr = ds[()].astype(np.float64) / 100.0
                    arr[np.isnan(arr)] = 0

                    # 提取所有有效站点的中心像素值
                    valid_sites = [i for i in range(num_sites) if lin_[i] is not None]
                    if not valid_sites:
                        continue
                    rows = [lin_[i] for i in valid_sites]
                    cols = [col_[i] for i in valid_sites]
                    vals = arr[:, rows, cols]   # 形状 (4, m)
                    lais = lai0[rows,cols]
                    lais[np.isnan(lais)] = 0

                    # 将数据存入对应站点的列表
                    for idx, site_idx in enumerate(valid_sites):
                        site_name = site_names[site_idx]
                        record = [kyear, kmonth, kday, khour] +  vals[:, idx].tolist() + [lais[idx]]
                        site_data[site_name].append(record)

# ================= 5. 保存为 CSV（直接放在 outdir_root 下） =================
print("正在保存 CSV 文件...")
for site_name, records in site_data.items():
    if not records:
        print(f"站点 {site_name} 无数据，跳过")
        continue
    df = pd.DataFrame(records, columns=['year', 'month', 'day', 'hour', 'LST1', 'LST2', 'LST3', 'LST4','LAI'])
    df = df.sort_values(['year', 'month', 'day', 'hour'])

    # 按年份分别保存，文件名：站点名_年份.csv
    for yr in df['year'].unique():
        df_yr = df[df['year'] == yr].copy()
        outfile = os.path.join(outdir_root, f"{site_name}_{yr}.csv")
        df_yr.to_csv(outfile, index=False)
        print(f"已保存: {outfile}")

print("所有站点数据处理完成！")