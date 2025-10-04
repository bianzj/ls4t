import gdal
from util.util import *
import warnings
warnings.filterwarnings("ignore")

os.environ['PROJ_LIB'] = r'C:\Users\Y\anaconda3\envs\python37\Lib\site-packages\osgeo\data\proj'
os.environ['GDAL_DATA'] = r'C:\Users\Y\anaconda3\envs\python37\Lib\site-packages\osgeo\data\gdal'
os.environ['PYTHONIOENCODING'] = 'utf-8'

'''2023.12.20'''
'''用于处理MODIS水色数据L2产品'''

indir_GF = r"D:\data\other\SST\GF\\"
indir_GF_1km = r"D:\data\other\SST\GF_1000\\"
indir_modis = r"D:\data\other\SST\MODIS\raw\\"
outdir_med = r"D:\data\other\SST\MODIS\med\\"
outdir_tif = r"D:\data\other\SST\MODIS\tif\\"
outdir_out = r"D:\data\other\SST\MODIS\out\\"
mkdir_if_not_exist(indir_GF_1km)
mkdir_if_not_exist(outdir_med)
mkdir_if_not_exist(outdir_tif)
mkdir_if_not_exist(outdir_out)

ifextract = 0
ifresampleGF = 0
ifreproj = 1

if ifextract:
    fileNames = search_file_rej(indir_modis, ['SST','nc'],'SST4')
    fileNum = len(fileNames)

    for fileName in fileNames:
        print(fileName)
        infile = indir_modis + fileName
        outfile_tem = outdir_med + "sst.tif"
        outfile_lat = outdir_med + "lat.tif"
        outfile_lon = outdir_med + "lon.tif"
        outfile = outdir_tif + fileName[:-3] + ".tif"
        dataset = gdal.Open(infile)
        sst_subdataset = 'HDF5:"{}"://geophysical_data/sst'.format(infile)
        sst_ds = gdal.Open(sst_subdataset)
        sst_data = sst_ds.ReadAsArray()*0.005 + 273.15
        nl, ns = np.shape(sst_data)

        lat_subdataset = 'HDF5:"{}"://navigation_data/latitude'.format(infile)
        lat_ds = gdal.Open(lat_subdataset)
        lat_data = lat_ds.ReadAsArray()

        lon_subdataset = 'HDF5:"{}"://navigation_data/longitude'.format(infile)
        lon_ds = gdal.Open(lon_subdataset)
        lon_data = lon_ds.ReadAsArray()

        write_image_gdal(sst_data,ns, nl, 1, '', '', outfile_tem)
        write_image_gdal(lat_data,ns, nl, 1, '', '', outfile_lat)
        write_image_gdal(lon_data,ns, nl, 1, '', '', outfile_lon)

        file = 'sst'
        fileDir = outdir_med
        datafile = fileDir + '\\' + file + '.tif'
        xfile = fileDir + '\\lon.tif'
        yfile = fileDir + '\\lat.tif'
        vrtfile = fileDir + '\\' + file + '.vrt'
        write_vrt(vrtfile, datafile, xfile, yfile, ns, nl)
        dst_ds = gdal.Warp(outfile, vrtfile, geoloc=True, resampleAlg=gdal.GRA_NearestNeighbour)

if ifresampleGF:
    fileNames = search_file_rej(indir_GF,['tif'],'enp')
    fileNum = len(fileNames)

    for fileName in fileNames:
        infile = indir_GF + fileName
        outfile = indir_GF_1km + fileName
        dataset = gdal.Open(infile)
        resample_method = 'average'  # 'cubic'
        warpDs = gdal.Warp(outfile, dataset, xRes=1000, yRes=1000,resampleAlg=resample_method)


if ifreproj:
    fileNames = search_file_rej(indir_GF_1km, ['.tif'],'enp')
    fileNum = len(fileNames)

    for fileName in fileNames:
        infile = indir_GF_1km + fileName
        print(infile)
        time_str = fileName[23:31]
        monthday = time_str[4:8]
        [data, ns, nl, nb, geog_type, proj_type] = read_image_gdal(infile)
        xmin, xscale, xroate, ymax, yroate, yscale = geog_type
        xmax = xmin + ns * xscale
        ymin = ymax + nl * yscale
        spatial_range = (xmin, ymin, xmax, ymax)

        fileNames_mod = search_file_rej(outdir_tif,[monthday],'enp')
        for fileName_mod in fileNames_mod:
            infile_mod = outdir_tif + fileName_mod
            outfile_mod = outdir_out + fileName_mod[:-3] + "_out.tif"
            [mod, temp1, temp2, temp3, temp4, temp5] = read_image_gdal(infile_mod)
            mod_ds =  gdal.Open(infile_mod)

            warpDs = gdal.Warp(outfile_mod, mod_ds, dstSRS=proj_type, xRes=1000, yRes=1000, outputBounds=spatial_range)
            del warpDs
            ds = None