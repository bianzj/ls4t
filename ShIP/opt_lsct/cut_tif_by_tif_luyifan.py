from util.util import *

def cut_tif_bytif(prefile_dir,targetArea_dir,outfile_dir):
    """
    使用目标区域tif裁剪tif，并输出
    :param prefile_dir: 原数据
    :param targetArea_dir: 目标格式
    :param outfile_dir: 输出
    :return: none
    """
    '''读取目标区域信息'''
    dataset = gdal.Open(targetArea_dir)
    if dataset == None:
        print(targetArea_dir+ " ")
    [data, ns, nl, im_bands, geog, proj] = read_image_gdal(targetArea_dir)
    nsi = np.zeros([nl, ns])
    nli = np.zeros([nl, ns])
    for k in range(nl):
        nli[k, :] = k
        nsi[k, :] = np.linspace(0, ns - 1, ns)
    nli = np.reshape(nli, -1)
    nsi = np.reshape(nsi, -1)
    temp1, temp2 = imagexy2geo(dataset, nli, nsi)
    lon, lat = geo2lonlat(dataset, temp1, temp2)
    '''读取待裁剪区域信息'''
    [dataset,im_width,im_height,im_bands,g,p] = read_image_gdal(prefile_dir)
    dataset = gdal.Open(prefile_dir)
    data = dataset.ReadAsArray(0, 0, im_width, im_height)
    temp1, temp2 = lonlat2geo(dataset, lat, lon)
    imagex, imagey = geo2imagexy(dataset, temp1, temp2)
    '''裁剪'''
    out_result = np.zeros([nl, ns])
    imagex = np.asarray(imagex, np.int_)
    imagey = np.asarray(imagey, np.int_)
    ind = (imagex > 0) * (imagex < im_height - 1) * (imagey > 0) * (imagey < im_width - 1)
    imagex[imagex < 0] = 0
    imagex[imagex > (im_height - 1)] = im_height - 1
    imagey[imagey < 0] = 0
    imagey[imagey > (im_width - 1)] = im_width - 1
    temp = data[imagex, imagey]
    # indnew = (temp<1.5)*(temp>0)*ind
    indnew = ind
    out_result = np.reshape(out_result, [-1])
    out_result[indnew] = temp[indnew]
    out_result = np.reshape(out_result, [nl, ns])
    '''输出'''
    if os.path.exists(outfile_dir) == 1:
        print('file exists')
        return
    write_image_gdal(out_result, ns, nl, 1, geog, proj, outfile_dir)
    print("save",outfile_dir," successful!")

# source_dir = r"J:\AHI_add\ahi_lst\\"
# out_dir = r"J:\AHI_add\ahi_lst_cut\\"
# target_tif = r"J:\AHI_add\AHI_2022161_0330_lst.tif"
#
# filesName = search_file(source_dir, ['tif'])
# filesNum = len(filesName)

# for fileI in range(filesNum):
#     filename = filesName[fileI]
#     infile = source_dir + filename
#     outfile = out_dir + filename
#     cut_tif_bytif(infile,target_tif,outfile)

source_file = r"D:\data\emis\\emis2_polar.tif"
out_file = r"D:\data\emis\\emis2_polar_beijing.tif"
target_tif = r"D:\data\type\\type_beijing_1000.tif"
cut_tif_bytif(source_file,target_tif,out_file)