from utils.old.util import *

'''2024.7.7'''
'''生成空间温度分布图'''
'''先重采样到10KM'''

indir = r"E:\AATSR\lsct\\"

ifresample = 0
iffit_lst = 0
iffit_Ts = 0
iffit_Tv = 0
ifave_year = 0
iffit_lst_year = 0
iffit_Ts_year = 0
iffit_Tv_year = 0
ifplot = 1

if ifresample:
    for year in range(2002,2013):
        for month in range(1,13):
            indir_month = indir + r"\%04d\lsct_month\%02d\\" %(year,month)
            if not os.path.exists(indir_month): continue
            outdir_month = indir + r"\%04d\lsct_month_10km\%02d\\" %(year,month)
            mkdir_if_not_exist(outdir_month)
            fileNames = search_file_rej(indir_month,['.tif'],'enp')
            for fileName in fileNames:
                print(fileName)
                infile = indir_month + fileName
                outfile = outdir_month + fileName
                dataset = gdal.Open(infile)
                ds = gdal.Warp(outfile, dataset, xRes=0.1, yRes=0.1)

if iffit_lst:
    data = np.zeros([108,1800,3600])
    i = 0
    for year in range(2003,2012):
        for month in range(1,13):
            indir_month = indir + r"\%04d\lsct_month_10km\%02d\\" %(year,month)
            if not os.path.exists(indir_month): continue
            fileNames = search_file_rej(indir_month, ['lst_n.tif'], 'enp')
            for fileName in fileNames:
                print(fileName)
                infile = indir_month + fileName
                im_data,im_width,im_height,im_bands,im_geotrans,im_proj = read_image_gdal(infile)
                data[i,:,:] = im_data
                i = i +1
    deltaT = np.zeros([1800,3600])
    for i in range(1800):
        print(i)
        for j in range(3600):
            data_p = data[:,i,j]
            data_p = np.reshape(data_p,-1)
            # print(sum(data_p==0))
            data_p[data_p < 23000] = 0
            data_p[data_p > 35000] = 0
            if sum(data_p==0)>30: continue
            data_p[data_p==0] = np.nan
            mask = ~np.isnan(data_p)
            slope, intercept = np.polyfit(np.linspace(start = 1, stop = 108, num = 108)[mask], data_p[mask]/100, 1)
            deltaT[i,j] = slope* 120
            print(slope* 120)
    outfile = indir + "lst_slope.tif"
    write_image_gdal(deltaT,im_width,im_height,im_bands,im_geotrans,im_proj,outfile)

if iffit_Ts:
    data = np.zeros([108,1800,3600])
    i = 0
    for year in range(2003,2012):
        for month in range(1,13):
            indir_month = indir + r"\%04d\lsct_month_10km\%02d\\" %(year,month)
            if not os.path.exists(indir_month): continue
            fileNames = search_file_rej(indir_month, ['lsct_s.tif'], 'enp')
            for fileName in fileNames:
                print(fileName)
                infile = indir_month + fileName
                im_data,im_width,im_height,im_bands,im_geotrans,im_proj = read_image_gdal(infile)
                data[i,:,:] = im_data
                i = i +1
    deltaT = np.zeros([1800,3600])
    for i in range(1800):
        print(i)
        for j in range(3600):
            data_p = data[:,i,j]
            data_p = np.reshape(data_p,-1)
            # print(sum(data_p==0))
            data_p[data_p < 23000] = 0
            data_p[data_p > 35000] = 0
            if sum(data_p==0)>30: continue
            data_p[data_p==0] = np.nan
            mask = ~np.isnan(data_p)
            slope, intercept = np.polyfit(np.linspace(start = 1, stop = 108, num = 108)[mask], data_p[mask]/100, 1)
            deltaT[i,j] = slope* 120
            print(slope* 120)
    outfile = indir + "Ts_slope.tif"
    write_image_gdal(deltaT,im_width,im_height,im_bands,im_geotrans,im_proj,outfile)

if iffit_Tv:
    data = np.zeros([108,1800,3600])
    i = 0
    for year in range(2003,2012):
        for month in range(1,13):
            indir_month = indir + r"\%04d\lsct_month_10km\%02d\\" %(year,month)
            if not os.path.exists(indir_month): continue
            fileNames = search_file_rej(indir_month, ['lsct_v.tif'], 'enp')
            for fileName in fileNames:
                print(fileName)
                infile = indir_month + fileName
                im_data,im_width,im_height,im_bands,im_geotrans,im_proj = read_image_gdal(infile)
                data[i,:,:] = im_data
                i = i +1
    deltaT = np.zeros([1800,3600])
    for i in range(1800):
        print(i)
        for j in range(3600):
            data_p = data[:,i,j]
            data_p = np.reshape(data_p,-1)
            # print(sum(data_p==0))
            data_p[data_p < 23000] = 0
            data_p[data_p > 35000] = 0
            if sum(data_p==0)>30: continue
            data_p[data_p==0] = np.nan
            mask = ~np.isnan(data_p)
            slope, intercept = np.polyfit(np.linspace(start = 1, stop = 108, num = 108)[mask], data_p[mask]/100, 1)
            deltaT[i,j] = slope* 120
            print(slope* 120)
    outfile = indir + "Tv_slope.tif"
    write_image_gdal(deltaT,im_width,im_height,im_bands,im_geotrans,im_proj,outfile)

if ifave_year:
    items = ['_count.tif', '_lsct_s.tif', '_lsct_v.tif', '_lst_f.tif', '_lst_n.tif']
    for item in items:
        for year in range(2003, 2012):
            temp = np.zeros([12, 1800, 3600])
            valid_count = np.zeros([12, 1800, 3600])
            for month in range(1, 13):
                indir_month = indir + r"\%04d\lsct_month_10km\%02d\\" % (year, month)
                if not os.path.exists(indir_month):
                    continue
                outdir_year = r"E:\AATSR\lsct\\year_ave\\"
                mkdir_if_not_exist(outdir_year)
                fileNames = search_file_rej(indir_month, [item], 'enp')
                for fileName in fileNames:
                    print(fileName)
                    infile = indir_month + fileName
                    im_data, im_width, im_height, im_bands, im_geotrans, im_proj = read_image_gdal(infile)
                    mask = im_data != 0
                    temp[month - 1, :, :] += im_data * mask
                    valid_count[month - 1, :, :] += mask
            valid_months = valid_count.sum(axis=0)
            valid_months[valid_months == 0] = 1  # 防止除以0
            year_ave = temp.sum(axis=0) / valid_months
            outfile = outdir_year + "AATSR_%04d" % year + item
            write_image_gdal(year_ave,im_width,im_height,im_bands,im_geotrans,im_proj,outfile)

if iffit_lst_year:
    item = 'lst_n'
    data = np.zeros([9,1800,3600])
    i = 0
    for year in range(2003,2012):
        indir_month = r"E:\AATSR\lsct\year_ave\\"
        infile = indir_month + r"AATSR_%04d_"%year + item + r".tif"
        im_data,im_width,im_height,im_bands,im_geotrans,im_proj = read_image_gdal(infile)
        data[i,:,:] = im_data
        i = i +1

    deltaT = np.zeros([1800,3600])
    for i in range(1800):
        print(i)
        for j in range(3600):
            data_p = data[:,i,j]
            data_p = np.reshape(data_p,-1)
            data_p[data_p < 23000] = 0
            data_p[data_p > 35000] = 0
            # print(sum(data_p == 0))
            if sum(data_p==0)>3: continue
            data_p[data_p==0] = np.nan
            mask = ~np.isnan(data_p)
            slope, intercept = np.polyfit(np.linspace(start = 1, stop = 9, num = 9)[mask], data_p[mask]/100, 1)
            deltaT[i,j] = slope
            print(slope)
    outfile = indir + "lst_slope_year.tif"
    write_image_gdal(deltaT,im_width,im_height,im_bands,im_geotrans,im_proj,outfile)

if iffit_Ts_year:
    item = 'lsct_s'
    data = np.zeros([9,1800,3600])
    i = 0
    for year in range(2003,2012):
        indir_month = r"E:\AATSR\lsct\year_ave\\"
        infile = indir_month + r"AATSR_%04d_"%year + item + r".tif"
        im_data,im_width,im_height,im_bands,im_geotrans,im_proj = read_image_gdal(infile)
        data[i,:,:] = im_data
        i = i +1

    deltaT = np.zeros([1800,3600])
    for i in range(1800):
        print(i)
        for j in range(3600):
            data_p = data[:,i,j]
            data_p = np.reshape(data_p,-1)
            data_p[data_p < 23000] = 0
            data_p[data_p > 35000] = 0
            # print(sum(data_p == 0))
            if sum(data_p==0)>3: continue
            data_p[data_p==0] = np.nan
            mask = ~np.isnan(data_p)
            slope, intercept = np.polyfit(np.linspace(start = 1, stop = 9, num = 9)[mask], data_p[mask]/100, 1)
            deltaT[i,j] = slope
            print(slope)
    outfile = indir + "Ts_slope_year.tif"
    write_image_gdal(deltaT,im_width,im_height,im_bands,im_geotrans,im_proj,outfile)

if iffit_Tv_year:
    item = 'lsct_v'
    data = np.zeros([9,1800,3600])
    i = 0
    for year in range(2003,2012):
        indir_month = r"E:\AATSR\lsct\year_ave\\"
        infile = indir_month + r"AATSR_%04d_"%year + item + r".tif"
        im_data,im_width,im_height,im_bands,im_geotrans,im_proj = read_image_gdal(infile)
        data[i,:,:] = im_data
        i = i +1

    deltaT = np.zeros([1800,3600])
    for i in range(1800):
        print(i)
        for j in range(3600):
            data_p = data[:,i,j]
            data_p = np.reshape(data_p,-1)
            data_p[data_p < 23000] = 0
            data_p[data_p > 35000] = 0
            # print(sum(data_p == 0))
            if sum(data_p==0)>3: continue
            data_p[data_p==0] = np.nan
            mask = ~np.isnan(data_p)
            slope, intercept = np.polyfit(np.linspace(start = 1, stop = 9, num = 9)[mask], data_p[mask]/100, 1)
            deltaT[i,j] = slope
            print(slope)
    outfile = indir + "Tv_slope_year.tif"
    write_image_gdal(deltaT,im_width,im_height,im_bands,im_geotrans,im_proj,outfile)

if ifplot:
    infile = r"E:\AATSR\lsct\Tv_slope_year.tif"
    dataset = gdal.Open(infile)
    band = dataset.GetRasterBand(1)
    data = band.ReadAsArray()

    plt.rc('font', family='Times New Roman')

    # 定义颜色映射
    cmap = plt.get_cmap('coolwarm')

    # 创建图像
    fig, ax = plt.subplots(figsize=(10, 5))
    data[data==0]=np.nan
    cax = ax.imshow(data, cmap=cmap, vmin=-1.0, vmax=1.0, extent=[-180, 180, -90, 90])

    # 添加颜色条
    cbar = fig.colorbar(cax, ticks=np.arange(-1.0, 1.1, 0.5))
    cbar.ax.set_yticklabels(['-1.0', '-0.5', '0', '0.5', '1.0'])

    # 设置坐标系范围
    ax.set_xlim(-180, 180)
    ax.set_ylim(-90, 90)
    ax.set_xlabel('Longitude')
    ax.set_ylabel('Latitude')
    plt.tight_layout()
    plt.show()