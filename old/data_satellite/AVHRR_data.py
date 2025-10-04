
from util.util import *
from pyhdf.SD import SD, SDC
import time
import os
os.environ['PROJ_LIB'] = r'C:\Users\zzz\anaconda3\envs\patrol\Library\share\proj'
#####################################
### functions

'''
AVHRR 数据范围特别大，处理方式类似于AHI
'''
###############################################3
####### Examples
################################################

##############################################
######## from hdf to tif and projected to WGS84
##############################################

indir_raw = r'G:\n19_raw\\'
indir_med = r'G:\n19_med\\'
indir_tif = r'G:\n19_tif\\'
indir_lst = r'G:\n19_lst\\'
symbol = 'N19'

ifproj = 1
ifresample = 1

if ifproj ==1:

    fileNames = search_file(indir_raw, ['AVHRR'])
    fileNum = len(fileNames)

    for k in range(fileNum):

        fileName = fileNames[k]
        infile = indir_raw + fileName
        print(k,infile)
        mark = fileName[10:10+22]
        date_str = fileName[-27:-20]

        hh = 0
        mm = 0
        time_str = '%02d'%hh+'%02d'%mm
        continue

        if(len(infile_ref)==0):
            continue
        infile_ref = indir_raw + infile_ref[0]
        if(os.path.exists(infile_ref)==0):
            continue

        ### for day data_satellite

        dayNight = 'day'


        fileName = infile
        objectName = r'BT_CH4'
        bt1 = getDatafromNc(fileName, objectName,1)
        fileName = infile
        objectName = r'BT_CH5'
        bt2 = getDatafromNc(fileName, objectName,1)



        fileName = infile
        objectName = r'SREFL_CH1'
        red = getDatafromNc(fileName, objectName,1)

        fileName = infile
        objectName = r'SREFL_CH2'
        nir = getDatafromNc(fileName, objectName,1)


        fileName = infile
        objectName = r'sensor_azimuth'
        psi = getDatafromNc_group(fileName,datasetName, objectName,1)

        fileName = infile_ref
        objectName = r'sensor_zenith'
        vza = getDatafromNc_group(fileName,datasetName, objectName,1)

        fileName = infile_ref
        datasetName ='geolocation_data'
        objectName = r'solar_zenith'
        sza = getDatafromNc_group(fileName,datasetName, objectName,1)

        fileName = infile_ref
        datasetName ='geolocation_data'
        objectName = r'solar_azimuth'
        saa = getDatafromNc_group(fileName,datasetName, objectName,1)

        psi = np.abs(vaa-saa)
        psi[psi > 180] = 360 - psi[psi > 180]


        fileName = infile_ref
        datasetName ='geolocation_data'
        objectName = r'latitude'
        lat = getDatafromNc_group(fileName,datasetName, objectName,1)

        fileName = infile_ref
        datasetName ='geolocation_data'
        objectName = r'longitude'
        lon = getDatafromNc_group(fileName,datasetName, objectName,1)

        # bt15 = inv_planck(m15_g, m15)
        # bt16 = inv_planck(m16_g, m16)
        nl_temp = nl
        ns_temp = ns
        if nl_temp > nl_ref: nl_temp = nl_ref
        if ns_temp > ns_ref: ns_temp = ns_ref

        vmr = vm.ViirsMender(lon[:nl_temp,:ns_temp], lat[:nl_temp,:ns_temp], vm.MOD_RESOLUTION)
        vmr.mend(bt1[:nl_temp,:ns_temp])
        vmr.mend(bt2[:nl_temp,:ns_temp])
        vmr.mend(sza[:nl_temp,:ns_temp])
        vmr.mend(vza[:nl_temp,:ns_temp])
        vmr.mend(psi[:nl_temp,:ns_temp])
        vmr.mend(lat[:nl_temp,:ns_temp])
        vmr.mend(lon[:nl_temp,:ns_temp])
        if dayNight == 'day':
            vmr.mend(red[:nl_temp,:ns_temp])
            vmr.mend(nir[:nl_temp,:ns_temp])


        outfile = indir_med + '\\lat.tif'
        write_image_gdal(lat[:nl_temp, :ns_temp], ns_temp, nl_temp, 1, '', '', outfile)
        outfile = indir_med + '\\lon.tif'
        write_image_gdal(lon[:nl_temp, :ns_temp], ns_temp, nl_temp, 1, '', '', outfile)

        outfile = indir_med + '\\vza.tif'
        write_image_gdal(vza[:nl_temp, :ns_temp], ns_temp, nl_temp, 1, '', '', outfile)
        outfile = indir_med + '\\sza.tif'
        write_image_gdal(sza[:nl_temp, :ns_temp], ns_temp, nl_temp, 1, '', '', outfile)
        outfile = indir_med + '\\psi.tif'
        write_image_gdal(psi[:nl_temp, :ns_temp], ns_temp, nl_temp, 1, '', '', outfile)
        outfile = indir_med + '\\bt1.tif'
        write_image_gdal(bt1[:nl_temp, :ns_temp], ns_temp, nl_temp, 1, '', '', outfile)
        outfile = indir_med + '\\bt2.tif'
        write_image_gdal(bt2[:nl_temp, :ns_temp], ns_temp, nl_temp, 1, '', '', outfile)

        if dayNight == 'day':
            outfile = indir_med + '\\nir.tif'
            write_image_gdal(nir[:nl_temp, :ns_temp], ns_temp, nl_temp, 1, '', '', outfile)
            outfile = indir_med + '\\red.tif'
            write_image_gdal(red[:nl_temp, :ns_temp], ns_temp, nl_temp, 1, '', '', outfile)



        fileDir = indir_med
        nl = nl_temp
        ns = ns_temp

        file = 'psi'
        datafile = fileDir+'\\'+file+'.tif'
        xfile = fileDir+'\\lon.tif'
        yfile = fileDir+'\\lat.tif'
        vrtfile = fileDir+'\\'+file+'.vrt'
        write_vrt(vrtfile,datafile,xfile,yfile,ns,nl)
        outfile = fileDir+'\\'+symbol+'_'+date_str+'_'+time_str+'_'+file+'_proj.tif'
        dst_ds = gdal.Warp(outfile, vrtfile, geoloc=True, resampleAlg=gdal.GRIORA_NearestNeighbour)

        file = 'sza'
        datafile = fileDir+'\\'+file+'.tif'
        xfile = fileDir+'\\lon.tif'
        yfile = fileDir+'\\lat.tif'
        vrtfile = fileDir+'\\'+file+'.vrt'
        write_vrt(vrtfile,datafile,xfile,yfile,ns,nl)
        outfile = fileDir+'\\'+symbol+'_'+date_str+'_'+time_str+'_'+file+'_proj.tif'
        dst_ds = gdal.Warp(outfile, vrtfile, geoloc=True, resampleAlg=gdal.GRIORA_NearestNeighbour)

        file = 'vza'
        datafile = fileDir+'\\'+file+'.tif'
        xfile = fileDir+'\\lon.tif'
        yfile = fileDir+'\\lat.tif'
        vrtfile = fileDir+'\\'+file+'.vrt'
        write_vrt(vrtfile,datafile,xfile,yfile,ns,nl)
        outfile = fileDir+'\\'+symbol+'_'+date_str+'_'+time_str+'_'+file+'_proj.tif'
        dst_ds = gdal.Warp(outfile, vrtfile, geoloc=True, resampleAlg=gdal.GRIORA_NearestNeighbour)

        file = 'bt1'
        datafile = fileDir+'\\'+file+'.tif'
        xfile = fileDir+'\\lon.tif'
        yfile = fileDir+'\\lat.tif'
        vrtfile = fileDir+'\\'+file+'.vrt'
        write_vrt(vrtfile,datafile,xfile,yfile,ns,nl)
        outfile = fileDir+'\\'+symbol+'_'+date_str+'_'+time_str+'_'+file+'_proj.tif'
        dst_ds = gdal.Warp(outfile, vrtfile, geoloc=True, resampleAlg=gdal.GRIORA_NearestNeighbour)

        file = 'bt2'
        datafile = fileDir+'\\'+file+'.tif'
        xfile = fileDir+'\\lon.tif'
        yfile = fileDir+'\\lat.tif'
        vrtfile = fileDir+'\\'+file+'.vrt'
        write_vrt(vrtfile,datafile,xfile,yfile,ns,nl)
        outfile = fileDir+'\\'+symbol+'_'+date_str+'_'+time_str+'_'+file+'_proj.tif'
        dst_ds = gdal.Warp(outfile, vrtfile, geoloc=True, resampleAlg=gdal.GRIORA_NearestNeighbour)

        if dayNight == 'day':
            file = 'red'
            datafile = fileDir+'\\'+file+'.tif'
            xfile = fileDir+'\\lon.tif'
            yfile = fileDir+'\\lat.tif'
            vrtfile = fileDir+'\\'+file+'.vrt'
            write_vrt(vrtfile,datafile,xfile,yfile,ns,nl)
            outfile = fileDir+'\\'+symbol+'_'+date_str+'_'+time_str+'_'+file+'_proj.tif'
            dst_ds = gdal.Warp(outfile, vrtfile, geoloc=True, resampleAlg=gdal.GRIORA_NearestNeighbour)

            file = 'nir'
            datafile = fileDir+'\\'+file+'.tif'
            xfile = fileDir+'\\lon.tif'
            yfile = fileDir+'\\lat.tif'
            vrtfile = fileDir+'\\'+file+'.vrt'
            write_vrt(vrtfile,datafile,xfile,yfile,ns,nl)
            outfile = fileDir+'\\'+symbol+'_'+date_str+'_'+time_str+'_'+file+'_proj.tif'
            dst_ds = gdal.Warp(outfile, vrtfile, geoloc=True, resampleAlg=gdal.GRIORA_NearestNeighbour)

