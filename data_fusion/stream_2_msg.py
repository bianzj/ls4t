import matplotlib.pyplot as plt

from base.util_lst import *
from base.util_phys import *
from base.util_data import *
from base.util_file import *
from base.rt.hotspot import *
from base.rt.gap import *
import pvlib
from pvlib.location import Location
from osgeo import gdal
from osgeo import osr
import os
import pyresample as pr
from satpy import Scene
import satpy

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


def read_h5(path):
    with h5py.File(path, 'r') as f:
        # 返回第一个 dataset 的数据 (常用于简单 H5 文件)
        key = list(f.keys())[0]
        return f[key][()]

indir_stream0 = '/Users/bianzj/Downloads/data/stream/'
indir_msglai_e0 = '/Users/bianzj/Downloads/data/msg/PRODUCTS/MSG/MLAI/GEOTIFF/'
indir_msglst_e0 = '/Users/bianzj/Downloads/data/msg/PRODUCTS/MSG/MLST/GEOTIFF/'
indir_msglst_i0 = '/Users/bianzj/Downloads/data/msg/PRODUCTS/MSG-IODC/MLST/GEOTIFF/'
indir_msglai_i0 = '/Users/bianzj/Downloads/data/msg/PRODUCTS/MSG-IODC/MLAI/GEOTIFF/'
indir_static = '/Users/bianzj/Downloads/data/msg/Static/'

infile = os.path.join(indir_static, "combined_euro_lat.tif")
lat0, ns, nl, nb, geog, proj = read_image_gdal(infile)
infile = os.path.join(indir_static, "combined_euro_lon.tif")
lon0, ns, nl, nb, geog, proj = read_image_gdal(infile)

lat0 = lat0 / 100.0
lon0 = lon0 / 100.0
ns_short = np.int16(ns / 20)
nl_short = np.int16(nl / 20)
lat = resize_data(lat0, nl_short, ns_short)
lon = resize_data(lon0, nl_short, ns_short)
ind = (lat < -90) | (lat > 90)
lat[ind] = np.nan
lon[ind] = np.nan

infile = os.path.join(indir_static, "combined_euro_vza.tif")
vza_e, ns, nl, nb, geog, proj = read_image_gdal(infile)
infile = os.path.join(indir_static, "combined_euro_vaa.tif")
vaa_e, ns, nl, nb, geog, proj = read_image_gdal(infile)
infile = os.path.join(indir_static, "combined_iodc_vza.tif")
vza_i, ns, nl, nb, geog, proj = read_image_gdal(infile)
infile = os.path.join(indir_static, "combined_iodc_vaa.tif")
vaa_i, ns, nl, nb, geog, proj = read_image_gdal(infile)
vza_i = vza_i / 100.0
vaa_i = vaa_i / 100.0
vza_e = vza_e / 100.0
vaa_e = vaa_e / 100.0


tcw_dir_0 = r"/Users/bianzj/Downloads/data/map/MCD12C1_2011_0.25.tif"
dataset = gdal.Open(tcw_dir_0)
indx, indy = loc2map(lat0, lon0, dataset)
indx = np.reshape(indx, [nl,ns])
indy = np.reshape(indy, [nl,ns])

kyear = 2019
kmonth = 6
kday = 21
khour = 13
kmin = 0
altitude = 0
hspot_val = 0.2
kdoy = date2DOY(kyear, kmonth, kday)
date_str = '%04d'%kyear + '%02d'%kmonth + '%02d'%kday



indir_msglai_e = indir_msglai_e0 + '/%04d/'%kyear + '/%02d/'%kmonth + '/%02d/'%kday
infile = indir_msglai_e+"HDF5_LSASAF_MSG_LAI_MSG-Disk_" +'%04d'%kyear + '%02d'%kmonth + '%02d'%kday + '0000.tif'
lai_e,ns,nl,nb,goeg,proj = read_image_gdal(infile)
indir_msglai_i = indir_msglai_i0 + '/%04d/'%kyear + '/%02d/'%kmonth + '/%02d/'%kday
infile = indir_msglai_i+"HDF5_LSASAF_MSG-IODC_LAI_IODC-Disk_" +'%04d'%kyear + '%02d'%kmonth + '%02d'%kday + '0000.tif'
lai_i,ns,nl,nb,goeg,proj = read_image_gdal(infile)

lai = lai_e/1000.0

indir_stream = indir_stream0 + '%03d/'%kdoy
tvh_ = read_h5(f"{indir_stream}tch_sim.h5")
tvs_ = read_h5(f"{indir_stream}tcs_sim.h5")
tss_ = read_h5(f"{indir_stream}tss_sim.h5")
tsh_ = read_h5(f"{indir_stream}tsh_sim.h5")
tvh_ = tvh_[:,indx,indy]
tvs_ = tvs_[:,indx,indy]
tss_ = tss_[:,indx,indy]
tsh_ = tsh_[:,indx,indy]

tvh = tvh_[khour,:,:]
tss = tss_[khour,:,:]
tsh = tsh_[khour,:,:]
tvs = tvs_[khour,:,:]

time_val = pd.to_datetime(f"{date_str} {khour:02d}:{kmin:02d}:00").tz_localize('UTC')
site_temp = Location(lat.flatten(), lon.flatten(), 'Etc/GMT', altitude, 'None')
nloc = len(lat.flatten())
solpos_temp = pvlib.solarposition.get_solarposition(np.repeat(time_val,nloc), site_temp.latitude,site_temp.longitude, site_temp.altitude,method='nrel_numpy')
sza_temp = solpos_temp['zenith'].to_numpy().reshape(lat.shape).astype(np.float32)
saa_temp = solpos_temp['azimuth'].to_numpy().reshape(lat.shape).astype(np.float32)
sza = resize_data(sza_temp, nl,ns)
saa = resize_data(saa_temp, nl,ns)

indir_msglst_e = indir_msglst_e0 + '/%04d/'%kyear + '/%02d/'%kmonth + '/%02d/'%kday
infile = indir_msglst_e+"HDF5_LSASAF_MSG_LST_MSG-Disk_" +'%04d'%kyear + '%02d'%kmonth + '%02d'%kday + '%02d00.tif'%khour
lst_e,ns,nl,nb,goeg,proj = read_image_gdal(infile)
indir_msglst_i = indir_msglst_i0 + '/%04d/'%kyear + '/%02d/'%kmonth + '/%02d/'%kday
infile = indir_msglst_i+"HDF5_LSASAF_MSG-IODC_LST_IODC-Disk_" +'%04d'%kyear + '%02d'%kmonth + '%02d'%kday + '%02d00.tif'%khour
lst_i,ns,nl,nb,goeg,proj = read_image_gdal(infile)
lst_e = lst_e/100.0 + 273.15
lst_i = lst_i/100.0 + 273.15

vsa_e = np.abs(saa - vaa_e)
vsa_i = np.abs(saa - vaa_i)
vsa_e[vsa_e > 180] = 360 - vsa_e[vsa_e > 180]
vsa_i[vsa_i > 180] = 360 - vsa_i[vsa_i > 180]

b1 = gap_probability_hom_analytical(lai, vza_e)
w1, b1 = hotspot_layer(lai, hspot_val, vza_e, sza, vsa_e)

b2 = gap_probability_hom_analytical(lai, vza_i)
w2, b2 = hotspot_layer(lai, hspot_val, vza_i, sza, vsa_i)


bvh = planck(tvh)
bvs = planck(tvs)
bsh = planck(tsh)
bss = planck(tss)

b_e = w1 * bss + (b1 - w1) * bsh + (1-b1) *(bvs)
b_i = w2 * bss + (b2 - w2) * bsh + (1-b2) *(bvs)

lst_ee = inv_planck(b_e)
lst_ii = inv_planck(b_i)

plt.imshow(lst_e)
plt.colorbar()
plt.show()


plt.imshow(lst_ee)
plt.show()

ind = np.abs(lst_i - lst_e) < 0.1
lst_e[ind] = np.nan
lst_i[ind] = np.nan
ind = np.abs(lst_ii - lst_ee) < 0.1
lst_ee[ind] = np.nan
lst_ii[ind] = np.nan

plt.imshow(lst_ii-lst_ee)
plt.colorbar()
plt.show()
plt.imshow(lst_i-lst_e)
plt.colorbar()
plt.show()
