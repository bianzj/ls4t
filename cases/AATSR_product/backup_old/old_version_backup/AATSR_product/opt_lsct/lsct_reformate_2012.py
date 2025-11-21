from utils.old.util_old import *
import calendar

'''2012年数据重构'''


indir = r'G:\AATSR\2012\lsct\\'
outdir = r'G:\AATSR\2012\lsct_\\'

for month in range(4,5):
    daynum = calendar.monthrange(2012,month)[1]
    for day in range(1,15):
        # day = d +1
        indir_day = indir + "%02d//%02d//" %(month,day)
        if not os.path.exists(indir_day): continue
        outdir_day = outdir + "%02d//%02d//" %(month,day)
        mkdir_if_not_exist(outdir_day)

        fileNames = search_file_rej(indir_day,['lsct'],'enp')
        fileNum = len(fileNames)
        for fileName in fileNames:
            infile = indir_day + fileName
            outfile = outdir_day + fileName
            if os.path.exists(outfile): continue
            print(fileName)
            [lsct, ns, nl, bands, geog, proj] = read_image_gdal(infile)
            print(ns, nl, bands)
            ts = np.reshape(lsct[:, :, 0], [bands, nl])
            tv = np.reshape(lsct[:, :, 1], [bands, nl])
            lsct_new = np.zeros([ns,bands,nl+4])
            lsct_new[0,:,2:-2] = ts
            lsct_new[1,:,2:-2] = tv
            outfile = outdir_day + fileName
            write_image_gdal(lsct_new, ns, nl, bands, geog, proj,outfile)
