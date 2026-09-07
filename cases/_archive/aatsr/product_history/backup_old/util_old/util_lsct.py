# from util.old.util import *
from util.rt.hom import *
from util.rt.crown import *
from timezonefinder import TimezoneFinder
import pytz
from datetime import datetime, timedelta
import pysolar.solar as Sun
from scipy.optimize import fsolve

'''
planck
'''
def planck(wavelength, Ts):
    '''
    基于planck公式，计算某个波长时候，从温度到辐射的转换
    :param wavelength: 波长，10.5
    :param Ts: 温度，可以是亮温，也可以是摄氏度
    :return: 辐射
    '''
    c1 = planck_c1
    c2 = planck_c2
    if isinstance(Ts * 1.0, float):
        wavelength = np.float(wavelength)
        Ts = np.float(Ts)
        rad = c1 / (np.power(wavelength, 5) * (np.exp(c2 / Ts / wavelength) - 1)) * 10000
    else:
        wavelength = np.float(wavelength)
        rad = c1 / (np.power(wavelength, 5) * (np.exp(c2 / Ts / wavelength) - 1)) * 10000
    return rad

def inv_planck(wavelength, rad):
    '''
    基于planck公式，计算从辐射到亮温的转换
    :param wavelength: 波长,10.5
    :param rad: 辐射
    :return: 亮温 （300）
    '''
    c1 = planck_c1 * 10000
    c2 = planck_c2
    temp = c1 / (rad * np.power((wavelength), 5)) + 1
    Ts = c2 / (wavelength * np.log(temp))
    return Ts


'''
AATSR 数据读取
'''

def aatsr_read_aux_data(indir_emis, indir_type):
    '''
    aatsr 读取辅助数据
    :param indir_emis: 发射率
    :param indir_type:  地表类型
    :return: 土壤发射率、植被发射率、分类、密度、树覆盖比例、树冠高度，观测天顶角、方位角
    '''
    # 读取type emis std hcr rcr
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

'''
aatsr_fluxnet 读取
'''
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


'''
TIRT_veg
'''
def sample_hom_bt(Tsl,Tsh,Tvl,Tvh, lai, hspot,wavelength, emissivity_soil, emissivity_leaf,vza, sza, raa):
    '''1.initial'''
    hom = Hom()
    '''2.set variables'''
    hom.set_thermal(Tsl,Tsh,Tvl,Tvh)
    hom.set_structure(lai, hspot)
    hom.set_optical(wavelength, emissivity_soil, emissivity_leaf)
    hom.set_angle(vza, sza, raa)
    ''''3.run'''
    bt = hom.run()
    vza[raa == 180] = vza[raa == 180] * -1
    return bt

def sample_hom_Emis(lai, hspot,wavelength, emissivity_soil, emissivity_leaf,vza, sza, raa):
    '''1.initial'''
    hom = Hom()
    '''2.set variables'''
    hom.set_structure(lai, hspot)
    hom.set_optical(wavelength, emissivity_soil, emissivity_leaf)
    hom.set_angle(vza, sza, raa)
    ''''3.run'''
    emis = hom.run_emis()
    vza[raa == 180] = vza[raa == 180] * -1
    return emis

def sample_crown_bt(Tsl,Tsh,Tvl,Tvh,lai, hspot,stand,rcr,hcr,wavelength, emissivity_soil, emissivity_leaf,vza, sza, raa):
    '''1.initial'''
    crown = Crown()
    '''2.set variables'''
    crown.set_thermal(Tsl,Tsh,Tvl,Tvh)
    crown.set_structure(lai, hspot, stand, hcr, rcr)
    crown.set_optical(wavelength, emissivity_soil, emissivity_leaf)
    crown.set_angle(vza, sza, raa)
    ''''3.run'''
    bt = crown.run()
    vza[raa == 180] = vza[raa == 180] * -1
    return bt

def sample_crown_Emis(lai, hspot,stand,rcr,hcr,wavelength, emissivity_soil, emissivity_leaf,vza, sza, raa):
    '''1.initial'''
    crown = Crown()
    '''2.set variables'''
    crown.set_structure(lai, hspot, stand, hcr, rcr)
    crown.set_optical(wavelength, emissivity_soil, emissivity_leaf)
    crown.set_angle(vza, sza, raa)
    ''''3.run'''
    emis = crown.run_emis()
    vza[raa == 180] = vza[raa == 180] * -1
    return emis

'''
计算能量\有效发射率
'''
def cal_rad_from_lst(lst,wl,lai,vza,emisS,emisV):
    '''
    根据lst计算rad
    :param lst: 反演出来的lst
    :param wl: 波长
    :param lai: 叶面积
    :param vza: 天顶角
    :param emisS: 土壤发射率
    :param emisV: 植被发射率
    :return:
    '''
    fvc = 1 - gap_probability_hom_analytical(lai, vza)
    rad = planck(wl, lst)
    # 多次散射项
    F = 0.75
    C = (1 - emisS) * emisV * F * (1 - fvc)
    rad = rad * (fvc * emisV + (1 - fvc) * emisS + C)
    return rad

def cal_effective_emissivity_hom(lai,hspot,wl,emisS,emisV,vza,sza,vaa,saa,component_number):
    nl,ns = np.shape(vza)
    w4 = sample_hom_Emis(lai,hspot,wl,emisS,emisV,vza,sza,np.abs(vaa-saa))
    psoil = gap_probability_hom_analytical(lai,sza)
    if component_number == 2:
        w = np.zeros([2,nl,ns])
        w[0,:,:] = w4[0,:,:] + w4[1,:,:]
        w[1,:,:] = w4[2,:,:] + w4[3,:,:]
    if component_number == 3:
        w = np.zeros([3,nl,ns])
        w[0:2,:,:] = w4[0:2,:,:]
        w[2,:,:] = w4[2,:,:] + w4[3,:,:]
    if component_number == 4:
        w = w4
    return w,psoil

def cal_effective_emissivity_crown(lai,hspot,wl,emisS,emisV,vza,sza,vaa,saa,classif,std,rcr,hcr,component_number):
    nl,ns = np.shape(vza)
    w4,psoil = np.zeros([4, nl, ns]),np.zeros([nl, ns])
    crown_class = [1, 2, 3, 4, 5, 8, 9]
    ind_c = np.isin(classif, crown_class) * (rcr != 0) * (std != 0) * (hcr != 0)
    # hom
    w4[:, ~ind_c]  = sample_hom_Emis(lai[:, ~ind_c] ,0.2,wl,emisS[:, ~ind_c],emisV[:, ~ind_c],vza[:, ~ind_c],sza[:, ~ind_c],np.abs(vaa[:, ~ind_c]-saa[:, ~ind_c]))
    psoil[~ind_c]  = gap_probability_hom_analytical(lai[:, ~ind_c] ,sza[:, ~ind_c])
    # crown
    hspot = 1.0
    w4[:,ind_c] = sample_crown_Emis(lai[ind_c], hspot, std[ind_c], rcr[ind_c], hcr[ind_c], wl,
                                                  emisS[ind_c], emisV[ind_c], vza[ind_c], sza[ind_c],
                                                  np.abs(vaa[ind_c] - saa[ind_c]))
    psoil[ind_c] = gap_probability_hom_analytical(lai[:, ind_c] ,sza[:, ind_c])
    if component_number == 2:
        w = np.zeros([2,nl,ns])
        w[0,:,:] = w4[0,:,:] + w4[1,:,:]
        w[1,:,:] = w4[2,:,:] + w4[3,:,:]
    if component_number == 3:
        w = np.zeros([3,nl,ns])
        w[0:2,:,:] = w4[0:2,:,:]
        w[2,:,:] = w4[2,:,:] + w4[3,:,:]
    if component_number == 4:
        w = w4
    return w,psoil

'''
温差限制、权重
'''

def determine_DT_lat_time(DT,month,lat_arr):
    if np.isin(month, [1, 2, 3]):
        DT[lat_arr > 66.5] = 1
        DT[(lat_arr < 66.5) * (lat_arr > 23.5)] = 2
        DT[(lat_arr < 23.5) * (lat_arr > 0)] = 4
        DT[(lat_arr < 0) * (lat_arr > -23.5)] = 5
        DT[(lat_arr < -23.5) * (lat_arr > -66.5)] = 4
        DT[(lat_arr < -66.5)] = 3
    elif np.isin(month, [4,5,6]):
        DT[lat_arr > 66.5] = 2
        DT[(lat_arr < 66.5) * (lat_arr > 23.5)] = 3
        DT[(lat_arr < 23.5) * (lat_arr > 0)] = 5
        DT[(lat_arr < 0) * (lat_arr > -23.5)] = 4
        DT[(lat_arr < -23.5) * (lat_arr > -66.5)] = 3
        DT[(lat_arr < -66.5)] = 2
    elif np.isin(month, [7,8,9]):
        DT[lat_arr > 66.5] = 3
        DT[(lat_arr < 66.5) * (lat_arr > 23.5)] = 4
        DT[(lat_arr < 23.5) * (lat_arr > 0)] = 5
        DT[(lat_arr < 0) * (lat_arr > -23.5)] = 4
        DT[(lat_arr < -23.5) * (lat_arr > -66.5)] = 2
        DT[(lat_arr < -66.5)] = 1
    elif np.isin(month, [10,11,12]):
        DT[lat_arr > 66.5] = 2
        DT[(lat_arr < 66.5) * (lat_arr > 23.5)] = 3
        DT[(lat_arr < 23.5) * (lat_arr > 0)] = 4
        DT[(lat_arr < 0) * (lat_arr > -23.5)] = 5
        DT[(lat_arr < -23.5) * (lat_arr > -66.5)] = 3
        DT[(lat_arr < -66.5)] = 2
    return DT

def set_DT_value_day(DT):
    deta12, deta23 = [0,30], [-15,15]
    # if DT == 1:
    #     deta12, deta23 = [1,10], [-5,5]
    # elif DT == 2:
    #     deta12, deta23 = [3,15], [-7.5,7.5]
    # elif DT == 3:
    #     deta12, deta23 = [5,20], [-10,10]
    # elif DT == 4:
    #     deta12, deta23 = [10,30], [-12.5,12.5]
    # elif DT == 5:
    #     deta12, deta23 = [15,40], [-15,15]
    return deta12, deta23

def set_DT_value_night(DT):
    deta = [-15,10]
    if DT == 1:
        deta = [-2.5,2.5]
    elif DT == 2:
        deta= [-5,2.5]
    elif DT == 3:
        deta = [-7.5,7.5]
    elif DT == 4:
        deta = [-10,10]
    elif DT == 5:
        deta = [-15,15]
    return deta

def calculate_weights(window_size):
    center = window_size // 2
    weights = np.zeros((window_size, window_size))

    for i in range(window_size):
        for j in range(window_size):
            d_ij = np.sqrt((i - center) ** 2 + (j - center) ** 2)
            if d_ij <= window_size:
                weights[i, j] = (1 - (d_ij / window_size) ** 2) ** 2
            else:
                weights[i, j] = 0
    return weights

'''
线性方程组求解
'''
def fitting_linear_2angle_2_component_point(w,b):
    return np.linalg.pinv(w) @ b


def fitting_linear_constraint_2angle_2component_window_weight_old(w,b,weight,deta12):
    '''

    :param w:
    :param b:
    :param weight:
    :param delta:
    :return:
    '''
    def constraint_func(x, lstN, deta12_min, deta12_max):
        # 计算每个约束条件的值
        constraint1 = -deta12_min + (x[0] - x[1])
        constraint2 = deta12_max - (x[0] - x[1])
        # constraint1 = max(x) - lstN
        # constraint2 = lstN - min(x)

        return [constraint1, constraint2]

    def objective_func(x, w, b,weight):
        residuals = np.dot(w, x) - b
        return np.sum(weight*residuals**2)

    lstN = inv_planck(10.8,np.max(b))
    lstN_m = inv_planck(10.8,np.min(b))
    deta12_min = planck(10.8,lstN + deta12[0]/2) -planck(10.8,lstN - deta12[0]/2)
    deta12_max = planck(10.8,lstN + deta12[1]/2) - planck(10.8,lstN- deta12[1]/2)

    # 定义约束条件
    constraints = {'type': 'ineq', 'fun': constraint_func,
                   'args': (lstN, deta12_min, deta12_max)}

    x0 = np.array([lstN, lstN])
    x0 = planck(10.8,x0)
    wl = 10.8
    bounds = [[planck(wl, lstN-5), planck(wl, lstN + 50)], [planck(wl, lstN - 30), planck(wl, lstN + 30)]]
    # SLSQP  trust-constr
    result = minimize(objective_func, x0, args=(w, b,weight),constraints=constraints,bounds = bounds,method ='SLSQP')

    p0 = result.x
    return p0

def fitting_linear_constraint_2angle_2component_window_weight(w,b,weight,lstN,lstO,deta12):
    '''

    :param w:
    :param b:
    :param weight:
    :param lstN:
    :param lstO:
    :param deta12:
    :return:
    '''
    def constraint_func(x, lstN, lstO, deta12_min, deta12_max):
        # 计算每个约束条件的值
        # constraint1 = -deta12_min + (x[0] - x[1])
        # constraint2 = deta12_max - (x[0] - x[1])
        constraint1 = max(x) - max(planck(10.8,np.array([lstN,lstO]))) - 0.01
        constraint2 = min(planck(10.8,np.array([lstN,lstO]))) - min(x) - 0.01
        return [constraint1, constraint2]

    def objective_func(x, w, b,weight):
        residuals = np.dot(w, x) - b
        return np.sum(weight*residuals**2)
    deta12_min = planck(10.8,lstN + deta12[0]/2) -planck(10.8,lstN - deta12[0]/2)
    deta12_max = planck(10.8,lstN + deta12[1]/2) - planck(10.8,lstN- deta12[1]/2)

    # 定义约束条件
    constraints = {'type': 'ineq', 'fun': constraint_func,
                   'args': (lstN, lstO, deta12_min, deta12_max)}
    wl =10.8
    x0 = np.array([(planck(10.8,np.array([lstN]))), (planck(10.8,np.array([lstO])))])
    # SLSQP  trust-constr
    result = minimize(objective_func, x0, args=(w, b,weight),constraints=constraints,method ='SLSQP')

    p0 = result.x
    return p0

def fitting_linear_constraint_2angle_3component_window_weight(w,b,weight, deta12,deta23):
    '''
    两角度 多窗口 加权重 加温差限制 解 三组分
    :param w:
    :param b:
    :param weight:
    :param deta12:
    :param deta23:
    :return:
    '''
    def constraint_func(x, lstN, deta12_min, deta12_max, deta23_min, deta23_max):
        # 计算每个约束条件的值
        constraint1 = -deta12_min + (x[0] - x[1])
        constraint2 = deta12_max - (x[0] - x[1])
        constraint3 = -deta23_min + (x[1] - x[2])
        constraint4 = deta23_max - (x[1] - x[2])
        return [constraint1, constraint2, constraint3, constraint4]

    def objective_func(x, w, b,weight):
        residuals = np.dot(w, x) - b
        return np.sum(weight*residuals**2)
    lstN = inv_planck(10.8,np.max(b))
    deta12_min = planck(10.8,lstN +  deta12[0]/2) -planck(10.8,lstN - deta12[0]/2)
    deta12_max = planck(10.8,lstN + deta12[1]/2) - planck(10.8,lstN- deta12[1]/2)
    deta23_min = planck(10.8,lstN + deta23[0]/2) - planck(10.8,lstN- deta23[0]/2)
    deta23_max = planck(10.8,lstN + deta23[1]/2) - planck(10.8,lstN- deta23[1]/2)

    # 定义约束条件
    constraints = {'type': 'ineq', 'fun': constraint_func,
                   'args': (lstN, deta12_min, deta12_max, deta23_min, deta23_max)}

    x0 = np.array([lstN, lstN, lstN])
    x0 = planck(10.8,x0)
    wl = 10.8
    bounds = [[planck(wl, lstN-5), planck(wl, lstN + 50)], [planck(wl, lstN - 30), planck(wl, lstN + 30)],
              [planck(wl, lstN - 30), planck(wl, lstN + 30)]]
    # SLSQP  trust-constr
    result = minimize(objective_func, x0, args=(w, b,weight),constraints=constraints,bounds = bounds,method ='SLSQP')

    p0 = result.x
    return p0

def fitting_unknown_linear_sklearn(y,A,method='ridge'):
    '''
    线性反演未知数，
    :param y: 因变量
    :param x: 自变量
    :param method: 方法，推荐ridge，然后是lasso，因为lasso会倾向于拟合0
    :return: 回归系数
    '''
    alphas = [0.0001,0.001,0.01,0.1,1,10,100]
    coeffs = 1.0
    if method=='ridge':
        clf = RidgeCV(alphas=alphas, fit_intercept=False)
        clf.fit(A, y)
        coeffs = clf.coef_
    elif method =='lasso':
        lasso = LassoCV(alphas=alphas, fit_intercept=False)
        lasso.fit(A, y)
        coeffs = lasso.coef_
    elif method =='bayesianridge':
        clf = BayesianRidge(fit_intercept=False)
        clf.fit(A,y)
        coeffs = clf.coef_

    return coeffs


'''
多线程
'''
def doMultiple_line_inv_2_AATSR(param):
    return inv_lsct2_AATSR_line((param[0]), (param[1]), (param[2]), (param[3]), (param[4]), (param[5]),(param[6]),(param[7]),(param[8]),(param[9]))

def doMultiple_line_inv_2_AATSR_ridge(param):
    return inv_lsct2_AATSR_line_ridge((param[0]), (param[1]), (param[2]), (param[3]), (param[4]), (param[5]),(param[6]),(param[7]),(param[8]))

def doMultiple_line_inv_3_AATSR(param):
    return inv_lsct3_AATSR_line((param[0]), (param[1]), (param[2]), (param[3]), (param[4]), (param[5]),(param[6]),(param[7]),(param[8]))


'''组分温度求解'''
def inv_lsct3_AATSR_line(wNLine, wOLine, radNLine, radOLine, maskNLine,maskOLine, psoilLine, DTLine,ns = 1024):
    wl = 10.8
    window_size = wNLine.shape[1]
    off = int((window_size-1)/2)
    number_component= 3
    result = np.zeros([number_component+1,ns])
    for kk in range(off, ns-off):
        ns1 = kk - off
        ns2 = kk + off + 1
        ###### w1是nadir，w2是oblique
        maskN = np.reshape(maskNLine[:, ns1:ns2], -1)
        maskO = np.reshape(maskOLine[:, ns1:ns2], -1)
        if maskN[int((window_size*window_size-1)/2)]==0 or maskO[int((window_size*window_size-1)/2)]==0:
            continue
        DT = DTLine[off, kk]
        delta12, delta23 = set_DT_value_day(DT)
        psoil = psoilLine[off,kk]

        w1 = wNLine[:, :, ns1:ns2]
        w1 = np.asarray(np.reshape(w1, (number_component, -1)))
        w2 = wOLine[:, :, ns1:ns2]
        w2 = np.asarray(np.reshape(w2, (number_component, -1)))
        w = np.concatenate((w1, w2), axis=1)

        b1 = (np.reshape(radNLine[:, ns1:ns2], -1))
        b2 = (np.reshape(radOLine[:, ns1:ns2], -1))
        b = np.concatenate((b1, b2))

        ind = np.concatenate((maskN, maskO))
        num_val_point = np.sum(ind)

        weight = calculate_weights(window_size)
        weight = np.reshape(weight, -1)
        weight = np.concatenate((weight,weight))

        if num_val_point < 10: continue
        # 两角度 多像元 三组分解
        coeff = fitting_linear_constraint_2angle_3component_window_weight(w[:,ind].T,b[ind],weight[ind],delta12, delta23)
        lsct3 = inv_planck(wl, coeff)
        if np.mean(lsct3) ==0: continue
        p0 = [psoil * coeff[0] + (1-psoil) * coeff[1], coeff[2]]
        Ts, Tv = inv_planck(wl,p0[0]), inv_planck(wl,p0[1])
        id = int(((window_size**2+1)/2-1))
        lstN,lstF = inv_planck(10.8,b1[id]/np.sum(w1[:,id])),inv_planck(10.8,b2[id]/np.sum(w2[:,id]))
        result[:, kk] = [lsct3[0], lsct3[1], Ts, Tv]
        # # 判断值是否在中间
        # if (Ts - lstN) * (Tv - lstN) < 0 and (Ts - lstF) * (Tv - lstF) < 0:
        #     # print("yes")
        #     result[:,kk] = [lsct3[0],lsct3[1],Tv, nan, nan]
        # # else:
        # #     print("no")
        # else:
        #     #不在中间则换单点结果
        #     w = np.array([[w1[0, id] + w1[1, id], w1[2, id]], [w2[0, id] + w2[1, id], w2[2, id]]])
        #     w = np.matrix(w)
        #     b = np.array([b1[id], b2[id]])
        #     b = np.matrix(b).reshape((2, -1))
        #     coeff = fitting_linear_2angle_2_component_point(w,b)
        #     Ts, Tv = inv_planck(wl, coeff[0]), inv_planck(wl, coeff[1])
        #     if (Ts - lstN) * (Tv - lstN) < 0 and (Ts - lstF) * (Tv - lstF) < 0:
        #         result[:, kk] = [nan, nan, nan, Ts, Tv]
    return result

def inv_lsct2_AATSR_line(wNLine, wOLine, radNLine, radOLine, maskNLine,maskOLine, lstNLine,lstFLine, DTLine,ns = 1024):
    wl = 10.8
    window_size = wNLine.shape[1]
    off = int((window_size-1)/2)
    number_component= 2
    result = np.zeros([number_component+2,ns])
    for kk in range(off, ns-off):
        ns1 = kk - off
        ns2 = kk + off + 1
        ###### w1是nadir，w2是oblique
        maskN = np.reshape(maskNLine[:, ns1:ns2], -1)
        maskO = np.reshape(maskOLine[:, ns1:ns2], -1)
        if maskN[int((window_size*window_size-1)/2)]==0 or maskO[int((window_size*window_size-1)/2)]==0:
            continue
        id = int((window_size*window_size-1)/2)
        lstN = np.reshape(lstNLine[:, ns1:ns2], -1)[int((window_size*window_size-1)/2)]
        lstF = np.reshape(lstFLine[:, ns1:ns2], -1)[int((window_size*window_size-1)/2)]
        DT = DTLine[off, kk]
        delta12, delta23 = set_DT_value_day(DT)

        w1 = wNLine[:, :, ns1:ns2]
        w1 = np.asarray(np.reshape(w1, (number_component, -1)))
        w2 = wOLine[:, :, ns1:ns2]
        w2 = np.asarray(np.reshape(w2, (number_component, -1)))
        w = np.concatenate((w1, w2), axis=1)

        b1 = (np.reshape(radNLine[:, ns1:ns2], -1))
        b2 = (np.reshape(radOLine[:, ns1:ns2], -1))
        b = np.concatenate((b1, b2))

        ind = np.concatenate((maskN, maskO))
        num_val_point = np.sum(ind)

        weight = calculate_weights(window_size)
        weight = np.reshape(weight, -1)
        weight = np.concatenate((weight,weight))

        if num_val_point < 8: continue
        # 两角度 多像元 两组分解
        coeff = fitting_linear_constraint_2angle_2component_window_weight(w[:,ind].T,b[ind],weight[ind],lstN,lstF,delta12)
        lsct2 = inv_planck(wl, coeff)
        if np.mean(lsct2) ==0: continue
        Ts, Tv = lsct2[0], lsct2[1]

        #不在中间则换单点结果
        w = np.array([[w1[:, id] ], [w2[:, id]]])
        w = np.matrix(w)
        b = np.array([b1[id], b2[id]])
        b = np.matrix(b).reshape((2, -1))
        coeff = fitting_linear_2angle_2_component_point(w,b)
        Ts, Tv = inv_planck(wl, coeff[0]), inv_planck(wl, coeff[1])
        result[:, kk] = [lsct2[0],lsct2[1], Ts, Tv]
    return result

def inv_lsct2_AATSR_line_ridge(wNLine, wOLine, radNLine, radOLine, maskNLine,maskOLine, psoilLine, DTLine,ns = 1024):
    wl = 10.8
    window_size = wNLine.shape[1]
    off = int((window_size-1)/2)
    number_component= 2
    result = np.zeros([number_component+2,ns])
    for kk in range(off, ns-off):
        ns1 = kk - off
        ns2 = kk + off + 1
        ###### w1是nadir，w2是oblique
        maskN = np.reshape(maskNLine[:, ns1:ns2], -1)
        maskO = np.reshape(maskOLine[:, ns1:ns2], -1)
        if maskN[int((window_size*window_size-1)/2)]==0 or maskO[int((window_size*window_size-1)/2)]==0:
            continue
        DT = DTLine[off, kk]
        delta12, delta23 = set_DT_value_day(DT)
        psoil = psoilLine[off,kk]

        w1 = wNLine[:, :, ns1:ns2]
        w1 = np.asarray(np.reshape(w1, (number_component, -1)))
        w2 = wOLine[:, :, ns1:ns2]
        w2 = np.asarray(np.reshape(w2, (number_component, -1)))
        w = np.concatenate((w1, w2), axis=1)

        b1 = (np.reshape(radNLine[:, ns1:ns2], -1))
        b2 = (np.reshape(radOLine[:, ns1:ns2], -1))
        b = np.concatenate((b1, b2))

        ind = np.concatenate((maskN, maskO))
        num_val_point = np.sum(ind)

        weight = calculate_weights(window_size)
        weight = np.reshape(weight, -1)
        weight = np.concatenate((weight,weight))

        if num_val_point < 10: continue
        # 两角度 多像元 三组分解
        # coeff = fitting_linear_constraint_2angle_2component_window_weight(w[:,ind].T,b[ind],weight[ind],delta12)
        coeff = fitting_unknown_linear_sklearn(b[ind],w[:,ind].T,method = 'ridge')
        lsct2 = inv_planck(wl, coeff)
        if np.mean(lsct2) ==0: continue
        Ts, Tv = lsct2[0], lsct2[1]
        id = int(((window_size**2+1)/2-1))

        lstN,lstF = inv_planck(10.8,b1[id]/np.sum(w1[:,id])),inv_planck(10.8,b2[id]/np.sum(w2[:,id]))

        # 判断值是否在中间
        if (Ts - lstN) * (Tv - lstN) < 0 and (Ts - lstF) * (Tv - lstF) < 0:
            result[:,kk] = [lsct2[0],lsct2[1], nan, nan]
        else:
            #不在中间则换单点结果
            w = np.array([[w1[:, id] ], [w2[:, id]]])
            w = np.matrix(w)
            b = np.array([b1[id], b2[id]])
            b = np.matrix(b).reshape((2, -1))
            coeff = fitting_linear_2angle_2_component_point(w,b)
            Ts, Tv = inv_planck(wl, coeff[0]), inv_planck(wl, coeff[1])
            if (Ts - lstN) * (Tv - lstN) < 0 and (Ts - lstF) * (Tv - lstF) < 0:
                result[:, kk] = [nan, nan, Ts, Tv]

        # w = np.array([[w1[:, id]], [w2[:, id]]])
        # w = np.matrix(w)
        # b = np.array([b1[id], b2[id]])
        # b = np.matrix(b).reshape((2, -1))
        # coeff = fitting_linear_2angle_2_component_point(w,b)
        # Ts, Tv = inv_planck(wl, coeff[0]), inv_planck(wl, coeff[1])
        # result[:, kk] = [lsct2[0],lsct2[1], Ts, Tv]
    return result


'''精度验证'''
def cal_rmse_r2(data1,data2,tshred=10):
    dif = (data2-data1)
    ind = np.abs(dif)<tshred
    bias = np.average(dif[ind])
    rmse = np.sqrt(np.average(dif[ind]*dif[ind]))
    coef = corrcoef(data1[ind],data2[ind])
    r2 = coef[1]*coef[1]
    return bias,rmse,r2