from base.util_constant import *
from base.util_file import *
from base.util_data import *

'''
AATSR 数据读取
'''

def aatsr_read_aux_data(indir_emis=r"/home/hero/data/base/0_base/emis/", indir_type=r"/home/hero/data/base/0_base/type/"):
    '''
    aatsr 读取辅助数据
    :param indir_emis: 发射率
    :param indir_type:  地表类型
    :return: 土壤发射率、植被发射率、分类、密度、观测天顶角、方位角
    '''
    # 读取type emis
    infile_type = indir_type + 'type_world_1000.tif'
    infile_soil_emis = indir_emis + r'AG1km.v003.SoilEmi.MODIS.Global.001D_LSE11.tif'
    infile_veg_emis = indir_emis + 'IGBP_Emi.txt'
    infile_vzaN = indir_type + r"vza_n.tif"
    infile_vaaN = indir_type + r"vaa_n.tif"
    infile_vzaO = indir_type + r"vza_f.tif"
    infile_vaaO = indir_type + r"vaa_f.tif"
    [emis_s, temp1, temp2, temp3, temp4, temp5] = read_image_gdal(infile_soil_emis)
    [classif, temp1, temp2, temp3, temp4, temp5] = read_image_gdal(infile_type)
    [vzaN, temp1, temp2, temp3, temp4, temp5] = read_image_gdal(infile_vzaN)
    [vaaN, temp1, temp2, temp3, temp4, temp5] = read_image_gdal(infile_vaaN)
    [vzaO, temp1, temp2, temp3, temp4, temp5] = read_image_gdal(infile_vzaO)
    [vaaO, temp1, temp2, temp3, temp4, temp5] = read_image_gdal(infile_vaaO)
    vzaN, vzaO, vaaN, vaaO = 90 - vzaN / 100, 90 - vzaO / 100, vaaN / 100, vaaO / 100
    emis_s = emis_s / 1000
    classif = np.asarray(classif, np.int_)
    classif[classif == 255] = 17
    emis_v = read_txt_array(infile_veg_emis, 0, 2)
    emis_v = emis_v[classif, 0] / 1000
    return emis_s, emis_v, classif, vzaN, vzaO, vaaN, vaaO


def aatsr_read_crown_data(indir_veg_pra):
    '''
    读取植被参数
    :param indir_veg_pra: 地址
    :return: 树密度、覆盖度、树冠高度
    '''
    infile_std = indir_veg_pra + "Tree_density(STD)/global_TreeDensity_0.01.tif"
    infile_TCC = indir_veg_pra + "Tree_cover(TCC)/global_TreeCover2010_0.01.tif"
    infile_hcr = indir_veg_pra + "Cnopy_height(hcr)/global_CanopyHeight_0.01.tif"
    [std, temp1, temp2, temp3, temp4, temp5] = read_image_gdal(infile_std)
    [TCC, temp1, temp2, temp3, temp4, temp5] = read_image_gdal(infile_TCC)
    [hcr, temp1, temp2, temp3, temp4, temp5] = read_image_gdal(infile_hcr)
    hcr = np.nan_to_num(hcr,0.0)
    std = std / 1000000
    hcr = hcr / 2
    TCC = TCC / 100
    return  std, TCC, hcr


def aatsr_cal_r(tcc, std, lai):
    G = 0.5  # Given constant
    cthetx = 1  # Given constant

    def equation(r, tcc_val, std_val, lai_val):
        areav = np.pi * r ** 2
        bv_in = np.exp(- (G * lai_val) / (areav * std_val))
        return np.log(tcc_val) + areav * (1 - bv_in) * std_val

    r_solution = np.zeros_like(tcc)
    for i in range(tcc.shape[0]):
        for j in range(tcc.shape[1]):
            r_initial_guess = 1.0  # Initial guess for r
            r_result = fsolve(equation, r_initial_guess, args=(tcc[i, j], std[i, j], lai[i, j]))
            r_solution[i, j] = np.clip(r_result[0], 0.5, 30)  # Ensure r is within bounds

    return r_solution


'''
时间 读取
'''
def get_timezone(lat, lon):
    tf = TimezoneFinder()
    timezone_str = tf.timezone_at(lng=lon, lat=lat)
    if timezone_str:
        return pytz.timezone(timezone_str)
    else:
        return None

def utc_to_local(utc_time,lon,lat):
    utc_time = pd.to_datetime(utc_time).dt.tz_localize('UTC')
    timezone = get_timezone(lat, lon)
    local_time = utc_time.dt.tz_convert(timezone)
    return local_time


'''
云量读取
'''

def aatsr_clo(clo):
    """
    将输入的十进制数或数组转换为二进制，
    第一位表示是否为陆地，第二位表示是否有云。
    只有陆地（第一位为1）且无云（第二位为0）时返回 True，否则返回 False。

    :param clo: 十进制整数或数组
    :return: 是否符合条件（True/False），单个值返回 bool，数组返回 np.ndarray，维度与输入相同
    """

    def check_condition(value):
        value = int(value)
        binary_str = format(value, 'b').zfill(2)  # 转换为二进制字符串，至少两位
        is_land = binary_str[-1] == '1'  # 低位第一位表示是否为陆地
        no_cloud = binary_str[-2] == '0'  # 低位第二位表示是否有云
        return is_land and no_cloud

    vectorized_check = np.vectorize(check_condition)
    return vectorized_check(clo)

def aatsr_clo_optimized(clo):
    """
    优化版：使用位运算检查最低两位
    最低位(第0位)表示是否为陆地(1)，第1位表示是否有云(0)
    只有陆地且无云时返回True
    
    :param clo: 十进制整数或数组
    :return: 是否符合条件(bool或np.ndarray)
    """
    # 转换为整数类型确保位运算正确
    clo = np.asarray(clo, dtype=np.int32)
    
    # 使用位运算同时检查两个条件:
    # 1. (clo & 0b01) == 1 检查最低位是否为1(陆地)
    # 2. (clo & 0b10) == 0 检查第1位是否为0(无云)
    return np.bitwise_and((clo & 0b01) == 1, (clo & 0b10) == 0)


'''
aatsr_sites fluxnet 切片数据读取
'''
def aatsr_read_sites_obs(infile,ifNDVI=1):
    items_obs = ['nirN','nirF','redN','redF','cloN','cloF']
    [nirN, nirF, redN, redF, cloN, cloF] = read_h5py_items(infile, items_obs)
    cloN_mask = aatsr_clo_optimized(cloN)
    cloF_mask = aatsr_clo_optimized(cloF)
    if ifNDVI == 1:
        ndviN = (nirN - redN) / (nirN + redN)
        ndviF = (nirF - redF) / (nirF + redF)
        ndviN[ndviN < -1] = -1
        ndviN[ndviN > 1] = 1
        ndviF[ndviF < -1] = -1
        ndviF[ndviF > 1] = 1
        ndviN[(redN ==0) + (nirN==0)] = np.nan
        ndviF[(redF ==0) + (nirF==0)] = np.nan
        return ndviN, ndviF
    return nirN, nirF, redN, redF

def aatsr_read_sites_clo(infile):
    items_clo = ['cloN','cloF']
    [cloN, cloF] = read_h5py_items(infile, items_clo)
    cloN_mask = aatsr_clo_optimized(cloN)
    cloF_mask = aatsr_clo_optimized(cloF)
    return cloN_mask, cloF_mask

def aatsr_read_sites_lst(infile):
    items_lst = ['lstN','lstO']
    [lstN, lstO] = read_h5py_items(infile, items_lst)
    lstN, lstF = lstN / 100, lstO / 100
    return lstN, lstF

def aatsr_read_sites_angle(infile):
    items_angle = ['vzaN','vzaF','vaaN','vaaF','sza','saa']
    [vzaN, vzaF, vaaN, vaaF, sza, saa] = read_h5py_items(infile, items_angle)
    vzaN,vzaF,vaaN,vaaF,sza,saa = vzaN / 100,vzaF/100,vaaN/100,vaaF/100,sza/100,saa/100
    sza[sza>=90] = 90
    return vzaN,vzaF,vaaN,vaaF,sza,saa

def aatsr_read_sites_emis(infile):
    items_emis = ['emis_s','emis_v','type','lai']
    [emis_s,emis_v,type_,lai] = read_h5py_items(infile, items_emis)
    lai = np.array(lai)/1000
    return emis_s,emis_v,type_,lai

def aatsr_read_sites_loc(infile):
    items_loc = ['indx','indy','ref_indx','ref_indy','lat','lon']
    [indx,indy,ref_indx,ref_indy,lat,lon] = read_h5py_items(infile, items_loc)
    return indx,indy,ref_indx,ref_indy,lat,lon

def aatsr_read_sites_time(infile):
    items_time = ['ref_time','sec']
    [ref_time,sec] = read_h5py_items(infile, items_time)
    ref_time_str = infile[-18:-10]
    utc_time = datetime.strptime(ref_time_str, '%Y_%j') + timedelta(seconds=int(np.mean(sec)))
    return utc_time

def aatsr_read_sites(site_dir, fileName, timezone, lat, lon, window_size):
    offset = window_size // 2
    infile = os.path.join(site_dir, fileName)
    '''读取数据'''
    items = ['lon', 'lat', 'lstN', 'lstO', 'LAI', 'vzaN', 'vzaO', 'vaaN', 'vaaO', 'sza', 'saa', 'indx', 'indy',
             'ref_indx', 'ref_indy', 'ref_time', 'sec', 'type', 'emis_s', "emis_v", 'cloN', 'cloF']
    lon_, lat_, lstN_, lstO_, lai_, vzaN_, vzaO_, vaaN_, vaaO_, sza_, saa_, indx_, indy_, ref_indx_, ref_indy_, ref_time_, sec_, type_, emis_s_, emis_v_, cloN_, cloF_ = read_h5py_items(
        infile, items)
    ref_time_str = fileName[6:-10]
    utc_time = datetime.strptime(ref_time_str, '%Y_%j') + timedelta(seconds=int(np.mean(sec_)))
    year, doy = int(ref_time_str[:4]), int(ref_time_str[5:8])
    local_time = utc_time.replace(tzinfo=pytz.utc).astimezone(timezone)
    print(local_time)

    '提取站点数据'
    id = (indx_ == ref_indx_) * (indy_ == ref_indy_)
    idx, idy = np.where(id)
    if sum(id) == 0:
        print("No Data!")
        return

    lstN = lstN_[idx[0] - offset:idx[0] + offset + 1, idy[0] - offset:idy[0] + offset + 1]
    lstF = lstO_[idx[0] - offset:idx[0] + offset + 1, idy[0] - offset:idy[0] + offset + 1]
    if np.shape(lstN) != (window_size, window_size): return
    lai = lai_[idx[0] - offset:idx[0] + offset + 1, idy[0] - offset:idy[0] + offset + 1]
    lai[lai >= 100] = lai[lai >= 100] / 1000
    vzaN = vzaN_[idx[0] - offset:idx[0] + offset + 1, idy[0] - offset:idy[0] + offset + 1]
    vzaF = vzaO_[idx[0] - offset:idx[0] + offset + 1, idy[0] - offset:idy[0] + offset + 1]
    vaaN = vaaN_[idx[0] - offset:idx[0] + offset + 1, idy[0] - offset:idy[0] + offset + 1]
    vaaF = vaaO_[idx[0] - offset:idx[0] + offset + 1, idy[0] - offset:idy[0] + offset + 1]
    classif = type_[idx[0] - offset:idx[0] + offset + 1, idy[0] - offset:idy[0] + offset + 1]
    emisS = emis_s_[idx[0] - offset:idx[0] + offset + 1, idy[0] - offset:idy[0] + offset + 1]
    emisV = emis_v_[idx[0] - offset:idx[0] + offset + 1, idy[0] - offset:idy[0] + offset + 1]
    cloN = cloN_[idx[0] - offset:idx[0] + offset + 1, idy[0] - offset:idy[0] + offset + 1]
    cloF = cloF_[idx[0] - offset:idx[0] + offset + 1, idy[0] - offset:idy[0] + offset + 1]
    indx = indx_[idx[0] - offset:idx[0] + offset + 1, idy[0] - offset:idy[0] + offset + 1].astype(int)
    indy = indy_[idx[0] - offset:idx[0] + offset + 1, idy[0] - offset:idy[0] + offset + 1].astype(int)
    '''格式转化'''
    lstN[lstN > 20000] = lstN[lstN > 20000] / 100
    lstF[lstF > 20000] = lstF[lstF > 20000] / 100

    nl, ns = np.shape(lstN)

    if sza_ != []:
        sza = sza_[idx[0] - offset:idx[0] + offset + 1, idy[0] - offset:idy[0] + offset + 1]
        saa = saa_[idx[0] - offset:idx[0] + offset + 1, idy[0] - offset:idy[0] + offset + 1]
        if np.abs(sza[offset, offset] - (90 - Sun.get_altitude(lat, lon, local_time))) < 10:
            sza = sza
        elif sza[offset, offset] > 89.9:
            sza = np.full_like(sza, 89.9)
        else:
            sza = 90 - sza
            print(90 - sza[offset, offset], (90 - Sun.get_altitude(lat, lon, local_time)))
    else:
        sza_ = 90 - Sun.get_altitude(lat, lon, local_time)
        saa_ = Sun.get_azimuth(lat, lon, local_time)
        sza = np.full([nl, ns], sza_)
        saa = np.full([nl, ns], saa_)

    def Azimuth_angle_transform(xaa):
        xaa[xaa < 0] = xaa[xaa < 0] + 360
        return xaa
    vzaN = 90 - vzaN / 100
    vzaF = 90 - vzaF / 100
    vaaN = Azimuth_angle_transform(vaaN)
    vaaF = Azimuth_angle_transform(vaaF)
    saa = Azimuth_angle_transform(saa)
    if np.sum(vaaN) == 0: return

    return lstN, lstF, lai, vzaN, vzaF, vaaN, vaaF, sza, saa, cloN, cloF, emisS, emisV, classif, utc_time, local_time, indx, indy



'''aatsr_h5 读取'''
def aatsr_read_lst(infile_lst):
    '''
    读取aatsr h5 lst数据
    :param infile_lst: lst文件地址
    :return: 两角度LST
    '''
    items = ['lstN','lstO']
    lstN, lstF = read_h5py_items(infile_lst, items)
    lstN, lstF = lstN/100.0, lstF/100.0
    return lstN, lstF

def aatsr_read_NDVI(infile_obs):
    '''
    读取aatsr h5 obs数据并计算NDVI
    :param infile_obs: obs文件地址
    :return: 两角度NDVI
    '''
    items = ['redN','nirN','redF','nirF']
    redN, nirN, redF, nirF = read_h5py_items(infile_obs, items)
    redN, nirN, redF, nirF = redN/10, nirN/10, redF/10, nirF/10
    ndviN = (nirN - redN) / (nirN + redN)
    ndviF = (nirF - redF) / (nirF + redF)
    ndviN[ndviN < -1] = -1
    ndviN[ndviN > 1] = 1
    ndviF[ndviF < -1] = -1
    ndviF[ndviF > 1] = 1
    ndviN[(redN ==0) + (nirN==0)] = np.nan
    ndviF[(redF ==0) + (nirF==0)] = np.nan
    return ndviN, ndviF

def aatsr_read_clo(infile_clo):
    '''
    读取aatsr h5 clo数据(自动计算并保存mask)
    :param infile_clo: clo文件地址
    :return: 两角度clo
    '''
    items = ['cloN_mask','cloF_mask']
    cloN_mask, cloF_mask = None, None
    
    # 先检查文件是否存在mask数据集
    with h5py.File(infile_clo, 'r') as f:
        if 'cloN_mask' not in f:
            print(f"Warning: Missing clo_mask in {infile_clo}")
            items = ['cloN','cloF']
            cloN, cloF = read_h5py_items(infile_clo, items)
            cloN_mask = aatsr_clo_optimized(cloN)
            cloF_mask = aatsr_clo_optimized(cloF)
        else:
            cloN_mask, cloF_mask = read_h5py_items(infile_clo, items)
            return cloN_mask, cloF_mask
    
    if 'cloN_mask' not in h5py.File(infile_clo, 'r'):
        with h5py.File(infile_clo, 'a') as f_write:
            f_write.create_dataset('cloN_mask', data=cloN_mask, dtype='bool', compression='gzip')
            f_write.create_dataset('cloF_mask', data=cloF_mask, dtype='bool', compression='gzip')
            
    return cloN_mask, cloF_mask

def aatsr_read_loc(infile_loc, iflonlat = 0):
    '''
    读取aatsr h5 loc数据
    :param infile_loc: loc文件地址
    :param iflonlat: 是否返回经纬度，0-否，1-是
    :return: 像元索引(行列)，可选经纬度
    '''
    items = ['indx','indy']
    if iflonlat == 1:
        items = ['indx','indy','lon','lat']
        indx, indy, lon, lat = read_h5py_items(infile_loc, items)
        return indx, indy, lon, lat
    else:
        indx, indy = read_h5py_items(infile_loc, items)
        return indx, indy
    