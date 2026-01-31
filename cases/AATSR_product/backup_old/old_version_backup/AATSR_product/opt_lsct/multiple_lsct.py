import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../../../../')))

from backup_old.old_version_backup.AATSR_product.util.old.util_old import *
from multiprocessing import Pool,cpu_count
from scipy.optimize import fmin
from scipy.optimize import minimize

# sensor_noise = 0.01
# sensor_noise = 0.05
# sensor_noise = 0.5
####### 计算NDVI
def file2Array_dynamic(infile_lst,infile_red,infile_nir):

    [lst, ns, nl, nb, geog, proj] = read_image_gdal(infile_lst)

    [red, temp1, temp2, temp3, temp4, temp5] = read_image_gdal(infile_red)
    [nir, temp1, temp2, temp3, temp4, temp5] = read_image_gdal(infile_nir)

    # lst = resize_data_ls(lst,nl/2,ns/2)
    # red = resize_data_ls(red,nl/2,ns/2)
    # nir = resize_data_ls(nir,nl/2,ns/2)

    ndvi = red*1.0
    ind = (red >0) *(nir >0)
    ndvi[ind] = (nir[ind]-red[ind])/(nir[ind]+red[ind])

    return lst,ndvi,geog,proj


def file2Array_static(infile_emis_s,infile_emis_v,infile_classif):

    number_colume_emis = 2
    time_emissivity = 1000.0
    # get soil emissivity
    [emis_s, ns, nl, nb, geog, proj] = read_image_gdal(infile_emis_s)
   # emis_s = resize_data_line(emis_s,nl/2,ns/2)

    emis_s = emis_s / time_emissivity

    [classif, temp1, temp2, temp3, temp4, temp5] = read_image_gdal(infile_classif)
    #classif = resize_data_near(classif,nl/2,ns/2)
    classif = np.asarray(classif, np.int)

    emis_v = read_txt_array(infile_emis_v, 0, number_colume_emis)
    emis_v = emis_v[classif, 0] / time_emissivity
    return emis_s,emis_v,geog,proj

###### 热点函数，光照面积比例
def file2Array_hotspot(infile_lai,infile_vza_n,infile_vaa_n,infile_sza,infile_saa,resample=1):
    G = 0.5
    rd = np.pi/180.0
    h = 1.0
    hs = 0.2
    d = h*hs


    [lai, ns, nl, nb, geog, proj] = read_image_gdal(infile_lai)
    lai = resize_data_near(lai,nl/resample,ns/resample)


    [sza, ns, nl, nb, geog, proj] = read_image_gdal(infile_sza)
    [vza_n, ns, nl ,nb, geog, proj] = read_image_gdal(infile_vza_n)
    # [vza_o, ns, nl ,nb, geog, proj] = read_image_gdal(infile_vza_o)
    [vaa_n, ns, nl ,nb, geog, proj] = read_image_gdal(infile_vaa_n)
    # [vaa_o, ns, nl ,nb, geog, proj] = read_image_gdal(infile_vaa_o)
    [saa, ns, nl ,nb, geog, proj] = read_image_gdal(infile_saa)
    sza = resize_data_near(sza,nl/resample,ns/resample)
    saa = resize_data_near(saa,nl/resample,ns/resample)

    vza_n = resize_data_near(vza_n, nl/resample, ns/resample)
    vaa_n = resize_data_near(vaa_n, nl/resample, ns/resample)

    raa_n = np.abs(saa-vaa_n)

    costhetanv = np.cos(vza_n*rd)
    costhetas = np.cos(sza*rd)
    costhetavn2 = np.power(costhetanv,2)
    costhetas2 = np.power(costhetas,2)
    gap_n = np.exp(-G*lai/costhetanv)

    sinthetas = np.sin(sza * rd)
    sinthetanv = np.sin(vza_n*rd)
    cosalpha = costhetas * costhetanv + sinthetas * sinthetanv * np.cos(raa_n*rd)
    sigma_n = np.sqrt(1/costhetas2+1/costhetavn2-2*cosalpha/costhetas/costhetanv)
    w_n = d/(h*sigma_n)*(1-np.exp(-h*sigma_n/d))

    pg_n = np.exp(-(G/costhetanv+G/costhetas-w_n*np.sqrt(G*G/costhetanv/costhetas))*lai)/gap_n

    return pg_n

# 根据数组计算热点，窗口，站点验证时使用
def cal_hotspot_fan(laiWindow, vzaWindow, vaaWindow, szaWindow, saaWindow):
    G = 0.5
    rd = np.pi / 180.0
    h = 1.0
    hs = 0.2
    d = h * hs

    raa = np.abs(saaWindow - vaaWindow)
    costhetanv = np.cos(vzaWindow * rd)
    costhetas = np.cos(szaWindow * rd)
    costhetavn2 = np.power(costhetanv, 2)
    costhetas2 = np.power(costhetas, 2)
    gap_n = np.exp(-G * laiWindow / costhetanv)
    sinthetas = np.sin(szaWindow * rd)
    sinthetanv = np.sin(vzaWindow * rd)
    cosalpha = costhetas * costhetanv + sinthetas * sinthetanv * np.cos(raa * rd)
    sigma_n = np.sqrt(1 / costhetas2 + 1 / costhetavn2 - 2 * cosalpha / costhetas / costhetanv)
    w_n = d / (h * sigma_n) * (1 - np.exp(-h * sigma_n / d))

    pg_n = np.exp(-(G / costhetanv + G / costhetas - w_n * np.sqrt(G * G / costhetanv / costhetas)) * laiWindow) / gap_n

    return pg_n

####### 单个像元的计算
def station_hotspot(lai,vza_n,vaa_n,sza,saa,nl,ns,imagex,imagey,off = 4):
    G = 0.5
    rd = np.pi / 180.0
    h = 1.0
    hs = 0.2
    d = h*hs

    lai = resize_data_near(lai,nl,ns)
    sza = resize_data_near(sza,nl,ns)
    saa = resize_data_near(saa,nl,ns)
    vza_n = resize_data_near(vza_n,nl,ns)
    vaa_n = resize_data_near(vaa_n,nl,ns)

    lai_window = lai[imagex-off:imagex+off+1, imagey-off:imagey+off+1]
    sza_window = sza[imagex-off:imagex+off+1, imagey-off:imagey+off+1]
    saa_window = saa[imagex-off:imagex+off+1, imagey-off:imagey+off+1]
    vza_window = vza_n[imagex-off:imagex+off+1, imagey-off:imagey+off+1]
    vaa_window = vaa_n[imagex-off:imagex+off+1, imagey-off:imagey+off+1]

    raa_window = np.abs(saa_window-vaa_window)

    costhetanv = np.cos(vza_window*rd)
    costhetas = np.cos(sza_window*rd)
    costhetavn2 = np.power(costhetanv,2)
    costhetas2 = np.power(costhetas,2)
    gap_n = np.exp(-G*lai_window/costhetanv)

    sinthetas = np.sin(sza_window * rd)
    sinthetanv = np.sin(vza_window*rd)
    cosalpha = costhetas * costhetanv + sinthetas * sinthetanv * np.cos(raa_window*rd)
    sigma_n = np.sqrt(1/costhetas2+1/costhetavn2-2*cosalpha/costhetas/costhetanv)
    w_n = d/(h*sigma_n)*(1-np.exp(-h*sigma_n/d))

    pg_n = np.exp(-(G/costhetanv+G/costhetas-w_n*np.sqrt(G*G/costhetanv/costhetas))*lai_window)/gap_n

    ind = (lai_window > 0)
    return pg_n, ind

######slstr两个角度计算两组分温度，并未采用多线程
def inv_mpl_agl(lst_n,lst_o,emis_s,emis_v,fvc_n,fvc_o,wl=10.8,off=2,off_=0):

    radiance_max_threshold = 20
    radiance_min_threshold = 4.5
    temperature_max_threshold = 350
    temperature_min_threshold = 250
    default_nan_temperature = 0
    soil_radiance_variance = 10
    leaf_radiance_variance = 5
    sensor_noise = 0.25
    pure_soil_threshold = 0.05
    pure_leaf_threshold = 0.95
    fvc_max_threshold = 0.99
    fvc_min_threshold = 0.01
    fd0 =  np.asarray([[1, 4, 7, 4, 1], [4, 16, 26, 16, 4], [7, 26, 41, 26, 7], [4, 16, 26, 16, 4], [1, 4, 7, 4, 1]])
    number_component = 2
    number_angle     = 2
    number_value_threshold = 12


    [nl,ns] = np.shape(lst_n)
    result = np.zeros([number_component, nl, ns])

    ######### FVC_gap
    # fvc_n = (ndvi_n - ndvi_min) / (ndvi_max - ndvi_min)
    fvc_n[fvc_n > fvc_max_threshold] = fvc_max_threshold
    fvc_n[fvc_n < fvc_min_threshold] = fvc_min_threshold

    # fvc_o = (ndvi_o - ndvi_min) / (ndvi_max - ndvi_min)
    fvc_o[fvc_o > fvc_max_threshold] = fvc_max_threshold
    fvc_o[fvc_o < fvc_min_threshold] = fvc_min_threshold

    ####### The radiance
    rad_n = planck(wl, lst_n)
    rad_n = rad_n * (fvc_n * emis_v + (1 - fvc_n) * emis_s)
    rad_o = planck(wl, lst_o)
    rad_o = rad_o * (fvc_o * emis_v + (1 - fvc_o) * emis_s)

    # component effective emissivity matrix
    W1 = np.asarray([emis_s * (1 - fvc_n), emis_v * (fvc_n)])
    W2 = np.asarray([emis_s * (1 - fvc_o), emis_v * (fvc_o)])


    nsi = np.zeros([nl, ns])
    nli = np.zeros([nl, ns])
    for k in range(nl):
        nli[k, :] = k
        nsi[k, :] = np.linspace(0, ns - 1, ns)

    mask = np.zeros([nl,ns])
    ind = (fvc_n > pure_soil_threshold) * (fvc_n < pure_leaf_threshold) *\
          (rad_n > radiance_min_threshold) * (rad_n < radiance_max_threshold) *\
          (rad_o > radiance_min_threshold) * (rad_o < radiance_max_threshold)
    mask[ind] = 1

    part = 6

    for k1 in range(off, nl - off):
        for k2 in range(off, ns - off):

            if (mask[k1, k2] != 1): continue

            nl1 = k1 - off
            nl2 = k1 + off + 1
            ns1 = k2 - off
            ns2 = k2 + off + 1

            offcenter = np.int(((2 * off + 1) * (2 * off + 1) - 1) / 2)
            ns_temp = np.reshape(nsi[nl1:nl2, ns1:ns2] - k2, -1)
            nl_temp = np.reshape(nli[nl1:nl2, ns1:ns2] - k1, -1)
            fd = fd0
            fd = np.reshape(fd, -1) * 1.0

            ### w1 for nadir and w2 for oblique
            w1 = W1[:, nl1:nl2, ns1:ns2]
            w1 = np.asarray(np.reshape(w1, (number_component, -1)))
            w2 = W2[:, nl1:nl2, ns1:ns2]
            w2 = np.asarray(np.reshape(w2, (number_component, -1)))

            n0 = np.ones(len(ns_temp))
            x = np.asarray([n0, ns_temp, nl_temp, ns_temp * nl_temp, ns_temp * ns_temp, nl_temp * nl_temp])
            w11 = np.asarray([w1[j, :] * x[i, :] for j in range(number_component) for i in range(part)])
            w22 = np.asarray([w2[j, :] * x[i, :] for j in range(number_component) for i in range(part)])

            b1 = (np.reshape(rad_n[k1, k2], -1))
            b2 = (np.reshape(rad_o[k1, k2], -1))
            bb1 = (np.reshape(rad_n[nl1:nl2, ns1:ns2], -1))
            bb2 = (np.reshape(rad_o[nl1:nl2, ns1:ns2], -1))

            temp1 = (np.reshape(fvc_n[nl1:nl2, ns1:ns2], -1))
            temp2 = (np.reshape(fvc_o[nl1:nl2, ns1:ns2], -1))
            ind = (bb1 < radiance_max_threshold) * (bb1 > radiance_min_threshold) * \
                  (temp1 > pure_soil_threshold) * (temp1 < pure_leaf_threshold) *\
                  (temp2 > pure_soil_threshold) *(temp2 <pure_leaf_threshold)*\
                  (bb2 < radiance_max_threshold) * (bb2 > radiance_min_threshold)

            num_val_point = np.sum(ind)
            if (num_val_point < number_value_threshold): continue

            ww = np.hstack((w11[:, ind], w22[:, ind]))
            bb = np.hstack((bb1[ind], bb2[ind]))

            w = np.hstack((w1, w2))
            b = np.hstack((b1, b2))

            ###############################################
            ### least-square method
            ###############################################
            ww = np.transpose(ww)

            coeffprior = np.asarray(lstsq(ww, bb,rcond=None))[0]
            # cd1 = np.sum(coeffprior[:6] * x[:, offcenter])
            # cd2 = np.sum(coeffprior[6:] * x[:, offcenter])
            # ctprior = np.transpose(np.matrix([cd1, cd2]))

            ###############################################
            ### Bayes method with priori information
            ###############################################
            # bbb = sorted(b)
            # halfpoint = np.int(num_point / 2)
            # rleaf = np.average(bbb[0])
            # rsoil = np.average(bbb[1])
            # coeffprior = np.transpose(np.matrix([rsoil, 0, 0, 0, 0, 0, rleaf, 0, 0, 0, 0, 0]))
            # bb = np.transpose(np.matrix(bb))
            # ww = np.transpose(ww)
            # Cd = np.matrix(np.diag(np.ones(num_point * 2)) * Cdvaluep)
            # Cm = np.matrix(np.diag(np.ones(2 * part)))
            # Cm[0, 0] = 15.0
            # Cm[part, part] = 10.0
            # pre = np.linalg.inv(np.transpose(ww) * np.linalg.inv(Cd) * ww + np.linalg.inv(Cm))
            # ctprior = pre * (np.transpose(ww) * np.linalg.inv(Cd) * bb + np.linalg.inv(Cm) * coeffprior)

            #################################################
            ### first result without averaging information
            #################################################
            # cd1 = np.sum(coeffprior[:6] * x[:, offcenter])
            # cd2 = np.sum(coeffprior[6:] * x[:, offcenter])
            # ctprior = np.transpose(np.matrix([cd1, cd2]))

            ################################################
            ### first reult with averaing information
            ################################################
            coeffprior = np.asarray(coeffprior)
            ct1 = np.asarray([np.sum(coeffprior[:part] * x[:part, j]) for j in range(25)])
            ct2 = np.asarray([np.sum(coeffprior[part:2 * part] * x[:part, j]) for j in range(25)])
            indnew = ind * (ct2 < radiance_max_threshold) * (ct2 > radiance_min_threshold) *\
                     (ct1 > radiance_min_threshold) * (ct1 < radiance_max_threshold)
            apoint = np.sum(indnew)

            # cd1 = np.sum(coeffprior[:part] * x[:, offcenter])
            # cd2 = np.sum(coeffprior[part:] * x[:, offcenter])
            # ctprior = np.transpose(np.matrix([cd1, cd2]))
            if (apoint <= 1):
                cd1 = np.sum(coeffprior[:part] * x[:, offcenter])
                cd2 = np.sum(coeffprior[part:] * x[:, offcenter])
                ctprior = np.transpose(np.matrix([cd1, cd2]))
            else:
                fd[indnew] = fd[indnew] / np.sum(fd[indnew])

                # inver-distance weight but not used
                # bb0 = bb1[offcenter]
                # fdnew = np.zeros(25)
                # dismax = max(abs(bb1[indnew] - bb0))
                # if dismax != 0:
                #     fdnew[indnew] = 1.0 - abs(1.0 * bb1[indnew] - bb0) / dismax
                # else:
                #     fdnew[:] = 1
                # fdnew[indnew] = fdnew[indnew] / np.sum(fdnew[indnew])
                # fd[indnew] = (fdnew[indnew] * fd[indnew]) / np.sum(fdnew[indnew] * fd[indnew])

                cd1new = np.sum(ct1[indnew] * fd[indnew])
                cd2new = np.sum(ct2[indnew] * fd[indnew])
                ctprior = np.transpose(np.matrix([cd1new, cd2new]))

            #################################################
            ### second result by combining one-point result
            #################################################

            nl1 = k1 - off_
            nl2 = k1 + off_ + 1
            ns1 = k2 - off_
            ns2 = k2 + off_ + 1
            w1 = W1[:, nl1:nl2, ns1:ns2]
            w1 = np.asarray(np.reshape(w1, (number_component, -1)))
            w2 = W2[:, nl1:nl2, ns1:ns2]
            w2 = np.asarray(np.reshape(w2, (number_component, -1)))
            b1 = (np.reshape(rad_n[nl1:nl2, ns1:ns2], -1))
            b2 = (np.reshape(rad_o[nl1:nl2, ns1:ns2], -1))
            w = np.hstack((w1, w2))
            b = np.hstack((b1, b2))
            w = np.transpose(w)

            #################################################
            ### least-squared method
            #################################################
            # coeffprior2 = np.asarray(lstsq(w, b))[0]

            #################################################
            ### Bayes method
            #################################################

            w = np.matrix(w)
            b = np.matrix(b)
            b = np.transpose(b)

            Cd = np.matrix(np.diag(np.ones(number_component)) * sensor_noise)
            Cm = np.diag([soil_radiance_variance, leaf_radiance_variance])
            pre = np.linalg.inv(np.transpose(w) * np.linalg.inv(Cd) * w + np.linalg.inv(Cm))
            coeff = pre * (np.transpose(w) * np.linalg.inv(Cd) * b + np.linalg.inv(Cm) * ctprior)
            ### another solution for using priori information
            #coeff = ctprior + np.transpose(Cd * np.transpose(w) * pre) * (b - np.transpose(w) * ctprior)
            component_radiance = np.asarray(coeff)
            # component_radiance = np.asarray(ctprior)
            # component_radiance = np.asarray(coeffprior2)

            if (np.min(component_radiance) < radiance_min_threshold): continue
            if (np.max(component_radiance) > radiance_max_threshold): continue

            component_temperature = inv_planck(wl, component_radiance)

            result[:, k1, k2] = [component_temperature[0], component_temperature[1]]

    result[result < temperature_min_threshold] = default_nan_temperature
    result[result > temperature_max_threshold] = default_nan_temperature

    return result

### sf: sunlitfraction
###### 两个角度尝试三组分，并未采用
def inv_mpl_agl_hs(lst_n, lst_o, emis_s, emis_v,ndvi_n, ndvi_o,fvc,pg_n,pg_o, wl=10.5, ndvi_min=0.05, ndvi_max=0.95, off=2, off_=0):
    radiance_max_threshold = 20
    radiance_min_threshold = 4.5
    temperature_max_threshold = 350
    temperature_min_threshold = 250
    default_nan_temperature = 0
    soil_radiance_variance = 2
    leaf_radiance_variance = 1
    # sensor_noise = 0.05
    pure_soil_threshold = 0.05
    pure_leaf_threshold = 0.95
    fvc_max_threshold = 0.99
    fvc_min_threshold = 0.01
    fd0 = np.asarray([[1, 4, 7, 4, 1], [4, 16, 26, 16, 4], [7, 26, 41, 26, 7], [4, 16, 26, 16, 4], [1, 4, 7, 4, 1]])
    number_component = 3
    number_angle = 2
    number_value_threshold = 12

    [nl, ns] = np.shape(lst_n)
    result = np.zeros([4, nl, ns])

    ######### FVC_LAI

    ######### FVC_NDVI
    fvc_n = (ndvi_n - ndvi_min) / (ndvi_max - ndvi_min)
    fvc_n[fvc_n > fvc_max_threshold] = fvc_max_threshold
    fvc_n[fvc_n < fvc_min_threshold] = fvc_min_threshold

    fvc_o = (ndvi_o - ndvi_min) / (ndvi_max - ndvi_min)
    fvc_o[fvc_o > fvc_max_threshold] = fvc_max_threshold
    fvc_o[fvc_o < fvc_min_threshold] = fvc_min_threshold

    ####### The radiance
    rad_n = planck(wl, lst_n)
    rad_n = rad_n * (fvc * emis_v + (1 - fvc) * emis_s)
    rad_o = planck(wl, lst_o)
    rad_o = rad_o * (fvc * emis_v + (1 - fvc) * emis_s)

    # component effective emissivity matrix
    W1 = np.asarray([emis_s * (1 - fvc_n)*pg_n,emis_s * (1 - fvc_n)*(1-pg_n), emis_v * (fvc_n)])
    W2 = np.asarray([emis_s * (1 - fvc_o)*pg_o, emis_s * (1 - fvc_o)*(1-pg_o),emis_v * (fvc_o)])

    nsi = np.zeros([nl, ns])
    nli = np.zeros([nl, ns])
    for k in range(nl):
        nli[k, :] = k
        nsi[k, :] = np.linspace(0, ns - 1, ns)

    mask = np.zeros([nl, ns])
    ind = (fvc_n > pure_soil_threshold) * (fvc_n < pure_leaf_threshold) * \
          (rad_n > radiance_min_threshold) * (rad_n < radiance_max_threshold) * \
          (rad_o > radiance_min_threshold) * (rad_o < radiance_max_threshold)
    mask[ind] = 1

    part = 6

    for k1 in range(off, nl - off):
        for k2 in range(off, ns - off):

            if (mask[k1, k2] != 1): continue

            nl1 = k1 - off
            nl2 = k1 + off + 1
            ns1 = k2 - off
            ns2 = k2 + off + 1

            offcenter = np.int(((2 * off + 1) * (2 * off + 1) - 1) / 2)
            ns_temp = np.reshape(nsi[nl1:nl2, ns1:ns2] - k2, -1)
            nl_temp = np.reshape(nli[nl1:nl2, ns1:ns2] - k1, -1)
            fd = fd0
            fd = np.reshape(fd, -1) * 1.0

            ### w1 for nadir and w2 for oblique
            w1 = W1[:, nl1:nl2, ns1:ns2]
            w1 = np.asarray(np.reshape(w1, (number_component, -1)))
            w2 = W2[:, nl1:nl2, ns1:ns2]
            w2 = np.asarray(np.reshape(w2, (number_component, -1)))

            n0 = np.ones(len(ns_temp))
            x = np.asarray([n0, ns_temp, nl_temp, ns_temp * nl_temp, ns_temp * ns_temp, nl_temp * nl_temp])
            w11 = np.asarray([w1[j, :] * x[i, :] for j in range(number_component) for i in range(part)])
            w22 = np.asarray([w2[j, :] * x[i, :] for j in range(number_component) for i in range(part)])

            b1 = (np.reshape(rad_n[k1, k2], -1))
            b2 = (np.reshape(rad_o[k1, k2], -1))
            bb1 = (np.reshape(rad_n[nl1:nl2, ns1:ns2], -1))
            bb2 = (np.reshape(rad_o[nl1:nl2, ns1:ns2], -1))

            temp1 = (np.reshape(fvc_n[nl1:nl2, ns1:ns2], -1))
            temp2 = (np.reshape(fvc_o[nl1:nl2, ns1:ns2], -1))
            ind = (bb1 < radiance_max_threshold) * (bb1 > radiance_min_threshold) * \
                  (temp1 > pure_soil_threshold) * (temp1 < pure_leaf_threshold) * \
                  (temp2 > pure_soil_threshold) * (temp2 < pure_leaf_threshold) * \
                  (bb2 < radiance_max_threshold) * (bb2 > radiance_min_threshold)

            num_val_point = np.sum(ind)
            if (num_val_point < number_value_threshold): continue

            ww = np.hstack((w11[:, ind], w22[:, ind]))
            bb = np.hstack((bb1[ind], bb2[ind]))

            w = np.hstack((w1, w2))
            b = np.hstack((b1, b2))

            ###############################################
            ### least-square method
            ###############################################
            ww = np.transpose(ww)

            coeffprior = np.asarray(lstsq(ww, bb, rcond=None))[0]
            # cd1 = np.sum(coeffprior[:6] * x[:, offcenter])
            # cd2 = np.sum(coeffprior[6:] * x[:, offcenter])
            # ctprior = np.transpose(np.matrix([cd1, cd2]))

            ###############################################
            ### Bayes method with priori information
            ###############################################
            # bbb = sorted(b)
            # halfpoint = np.int(num_point / 2)
            # rleaf = np.average(bbb[0])
            # rsoil = np.average(bbb[1])
            # coeffprior = np.transpose(np.matrix([rsoil, 0, 0, 0, 0, 0, rleaf, 0, 0, 0, 0, 0]))
            # bb = np.transpose(np.matrix(bb))
            # ww = np.transpose(ww)
            # Cd = np.matrix(np.diag(np.ones(num_point * 2)) * Cdvaluep)
            # Cm = np.matrix(np.diag(np.ones(2 * part)))
            # Cm[0, 0] = 15.0
            # Cm[part, part] = 10.0
            # pre = np.linalg.inv(np.transpose(ww) * np.linalg.inv(Cd) * ww + np.linalg.inv(Cm))
            # ctprior = pre * (np.transpose(ww) * np.linalg.inv(Cd) * bb + np.linalg.inv(Cm) * coeffprior)

            #################################################
            ### first result without averaging information
            #################################################
            # cd1 = np.sum(coeffprior[:6] * x[:, offcenter])
            # cd2 = np.sum(coeffprior[6:] * x[:, offcenter])
            # ctprior = np.transpose(np.matrix([cd1, cd2]))

            ################################################
            ### first reult with averaing information
            ################################################
            coeffprior = np.asarray(coeffprior)
            ct1 = np.asarray([np.sum(coeffprior[:part] * x[:part, j]) for j in range(25)])
            ct2 = np.asarray([np.sum(coeffprior[part:2 * part] * x[:part, j]) for j in range(25)])
            ct3 = np.asarray([np.sum(coeffprior[2*part:3 * part] * x[:part, j]) for j in range(25)])
            indnew = ind * (ct2 < radiance_max_threshold) * (ct2 > radiance_min_threshold) * \
                     (ct1 > radiance_min_threshold) * (ct1 < radiance_max_threshold) * \
                     (ct3 > radiance_min_threshold) * (ct3 < radiance_max_threshold)
            apoint = np.sum(indnew)
            if (apoint <= 1):
                cd1 = np.sum(coeffprior[:part] * x[:, offcenter])
                cd2 = np.sum(coeffprior[part:2*part] * x[:, offcenter])
                cd3 = np.sum(coeffprior[2*part:3 * part] * x[:, offcenter])
                ctprior = np.transpose(np.matrix([cd1, cd2,cd3]))
            else:
                fd[indnew] = fd[indnew] / np.sum(fd[indnew])

                # inver-distance weight but not used
                # bb0 = bb1[offcenter]
                # fdnew = np.zeros(25)
                # dismax = max(abs(bb1[indnew] - bb0))
                # if dismax != 0:
                #     fdnew[indnew] = 1.0 - abs(1.0 * bb1[indnew] - bb0) / dismax
                # else:
                #     fdnew[:] = 1
                # fdnew[indnew] = fdnew[indnew] / np.sum(fdnew[indnew])
                # fd[indnew] = (fdnew[indnew] * fd[indnew]) / np.sum(fdnew[indnew] * fd[indnew])

                cd1new = np.sum(ct1[indnew] * fd[indnew])
                cd2new = np.sum(ct2[indnew] * fd[indnew])
                cd3new = np.sum(ct3[indnew] * fd[indnew])
                ctprior = np.transpose(np.matrix([cd1new, cd2new, cd3new]))
            component_radiance = ctprior
            component_temperature = inv_planck(wl, ctprior)
            #################################################
            ### second result by combining one-point result
            #################################################

            nl1 = k1 - off_
            nl2 = k1 + off_ + 1
            ns1 = k2 - off_
            ns2 = k2 + off_ + 1
            w1 = W1[:, nl1:nl2, ns1:ns2]
            w1 = np.asarray(np.reshape(w1, (number_component, -1)))
            w2 = W2[:, nl1:nl2, ns1:ns2]
            w2 = np.asarray(np.reshape(w2, (number_component, -1)))
            b1 = (np.reshape(rad_n[nl1:nl2, ns1:ns2], -1))
            b2 = (np.reshape(rad_o[nl1:nl2, ns1:ns2], -1))
            w = np.hstack((w1, w2))
            b = np.hstack((b1, b2))
            w = np.transpose(w)

            #################################################
            ### least-squared method
            #################################################
            # coeffprior = np.asarray(lstsq(w, b))[0]

            #################################################
            ### Bayes method
            #################################################

            # w = np.matrix(w)
            # b = np.matrix(b)
            # b = np.transpose(b)
            #
            # Cd = np.matrix(np.diag(np.ones(number_component)) * sensor_noise)
            # Cm = np.diag([soil_radiance_variance,soil_radiance_variance, leaf_radiance_variance])
            # pre = np.linalg.inv(np.transpose(w) * np.linalg.inv(Cd) * w + np.linalg.inv(Cm))
            # coeff = pre * (np.transpose(w) * np.linalg.inv(Cd) * b + np.linalg.inv(Cm) * ctprior)
            # ### another solution for using priori information
            # # coeff = ctprior + np.transpose(Cd * np.transpose(w) * pre) * (b - np.transpose(w) * ctprior)
            # component_radiance = np.asarray(coeff)
            #
            # if (np.min(component_radiance) < radiance_min_threshold): continue
            # if (np.max(component_radiance) > radiance_max_threshold): continue
            #
            # component_temperature = inv_planck(wl, component_radiance)

            component_temperature = inv_planck(wl, component_radiance)
            rad_soil = pg_n[k1,k2]*component_radiance[0]+(1-pg_n[k1,k2])* component_radiance[1]
            temperature_soil = inv_planck(wl,rad_soil)

            result[:, k1, k2] = [temperature_soil, component_temperature[2],component_temperature[0], component_temperature[1]]


    result[result < temperature_min_threshold] = default_nan_temperature
    result[result > temperature_max_threshold] = default_nan_temperature

    return result

### sf: sunlitfraction
###### 三组分温度反演，未调用多线程，并未实际采用，仅为参考
def inv_mpl_agl_ahi_hs(lst_n, lst_o, lst_ahi,emis_s, emis_v, fvcN, fvcO, fvcAhi,pg_n,pg_o,pg_ahi, wl=10.5, ndvi_min=0.05, ndvi_max=0.95, off=2, off_=0):
    radiance_max_threshold = 20
    radiance_min_threshold = 4.5
    temperature_max_threshold = 350
    temperature_min_threshold = 250
    default_nan_temperature = 0
    soil_radiance_variance = 2
    leaf_radiance_variance = 1
    sensor_noise = 0.05
    pure_soil_threshold = 0.05
    pure_leaf_threshold = 0.95
    fvc_max_threshold = 0.99
    fvc_min_threshold = 0.01
    fd0 = np.asarray([[1, 4, 7, 4, 1], [4, 16, 26, 16, 4], [7, 26, 41, 26, 7], [4, 16, 26, 16, 4], [1, 4, 7, 4, 1]])
    number_component = 3
    number_angle = 2
    number_value_threshold = 12

    [nl, ns] = np.shape(lst_n)
    result = np.zeros([4, nl, ns])

    ######### FVC_NDVI
    # fvc_n = (ndvi_n - ndvi_min) / (ndvi_max - ndvi_min)
    # fvc_n[fvc_n > fvc_max_threshold] = fvc_max_threshold
    # fvc_n[fvc_n < fvc_min_threshold] = fvc_min_threshold
    #
    # fvc_o = (ndvi_o - ndvi_min) / (ndvi_max - ndvi_min)
    # fvc_o[fvc_o > fvc_max_threshold] = fvc_max_threshold
    # fvc_o[fvc_o < fvc_min_threshold] = fvc_min_threshold
    #
    #
    # fvc_ahi = (ndvi_ahi - ndvi_min) / (ndvi_max - ndvi_min)
    # fvc_ahi[fvc_ahi > fvc_max_threshold] = fvc_max_threshold
    # fvc_ahi[fvc_ahi < fvc_min_threshold] = fvc_min_threshold
    ######### FVC LAI
    fvc_n = fvcN * 1.0
    fvc_n[fvc_n > fvc_max_threshold] = fvc_max_threshold
    fvc_n[fvc_n < fvc_min_threshold] = fvc_min_threshold

    fvc_o = fvcO * 1.0
    fvc_o[fvc_o > fvc_max_threshold] = fvc_max_threshold
    fvc_o[fvc_o < fvc_min_threshold] = fvc_min_threshold

    fvc_ahi = fvcAhi * 1.0
    fvc_ahi[fvc_ahi > fvc_max_threshold] = fvc_max_threshold
    fvc_ahi[fvc_ahi < fvc_min_threshold] = fvc_min_threshold
    ####### The radiance
    rad_n = planck(wl, lst_n)
    rad_n = rad_n * (fvc_n * emis_v + (1 - fvc_n) * emis_s)
    rad_o = planck(wl, lst_o)
    rad_o = rad_o * (fvc_o * emis_v + (1 - fvc_o) * emis_s)

    rad_ahi = planck(wl,lst_ahi)
    emisd2_v = resize_data_near(emis_v,nl/2,ns/2)
    emisd2_s = resize_data_near(emis_s,nl/2,ns/2)
    rad_ahi = rad_ahi *(fvc_ahi*emisd2_v + (1-fvc_ahi)*emisd2_s)

    # component effective emissivity matrix
    W1 = np.asarray([emis_s * (1 - fvc_n)*pg_n,emis_s * (1 - fvc_n)*(1-pg_n), emis_v * (fvc_n)])
    W2 = np.asarray([emis_s * (1 - fvc_o)*pg_o, emis_s * (1 - fvc_o)*(1-pg_o),emis_v * (fvc_o)])
    W3 = np.asarray([emisd2_s * (1 - fvc_ahi)*pg_ahi, emisd2_s * (1 - fvc_ahi)*(1-pg_ahi),emisd2_v * (fvc_ahi)])

    nsi = np.zeros([nl, ns])
    nli = np.zeros([nl, ns])
    for k in range(nl):
        nli[k, :] = k
        nsi[k, :] = np.linspace(0, ns - 1, ns)

    mask = np.zeros([nl, ns])
    ind = (fvc_n > pure_soil_threshold) * (fvc_n < pure_leaf_threshold) * \
          (rad_n > radiance_min_threshold) * (rad_n < radiance_max_threshold) * \
          (rad_o > radiance_min_threshold) * (rad_o < radiance_max_threshold)
    mask[ind] = 1

    part = 6

    for k1 in range(off, nl - off):
        for k2 in range(off, ns - off):

            if (mask[k1, k2] != 1): continue

            nl1 = k1 - off
            nl2 = k1 + off + 1
            ns1 = k2 - off
            ns2 = k2 + off + 1

            offcenter = np.int(((2 * off + 1) * (2 * off + 1) - 1) / 2)
            ns_temp = np.reshape(nsi[nl1:nl2, ns1:ns2] - k2, -1)
            nl_temp = np.reshape(nli[nl1:nl2, ns1:ns2] - k1, -1)
            fd = fd0
            fd = np.reshape(fd, -1) * 1.0

            ### w1 for nadir and w2 for oblique
            w1 = W1[:, nl1:nl2, ns1:ns2]
            w1 = np.asarray(np.reshape(w1, (number_component, -1)))
            w2 = W2[:, nl1:nl2, ns1:ns2]
            w2 = np.asarray(np.reshape(w2, (number_component, -1)))


            n0 = np.ones(len(ns_temp))
            x = np.asarray([n0, ns_temp, nl_temp, ns_temp * nl_temp, ns_temp * ns_temp, nl_temp * nl_temp])
            w11 = np.asarray([w1[j, :] * x[i, :] for j in range(number_component) for i in range(part)])
            w22 = np.asarray([w2[j, :] * x[i, :] for j in range(number_component) for i in range(part)])

            b1 = (np.reshape(rad_n[k1, k2], -1))
            b2 = (np.reshape(rad_o[k1, k2], -1))
            bb1 = (np.reshape(rad_n[nl1:nl2, ns1:ns2], -1))
            bb2 = (np.reshape(rad_o[nl1:nl2, ns1:ns2], -1))

            temp1 = (np.reshape(fvc_n[nl1:nl2, ns1:ns2], -1))
            temp2 = (np.reshape(fvc_o[nl1:nl2, ns1:ns2], -1))
            ind = (bb1 < radiance_max_threshold) * (bb1 > radiance_min_threshold) * \
                  (temp1 > pure_soil_threshold) * (temp1 < pure_leaf_threshold) * \
                  (temp2 > pure_soil_threshold) * (temp2 < pure_leaf_threshold) * \
                  (bb2 < radiance_max_threshold) * (bb2 > radiance_min_threshold)

            num_val_point = np.sum(ind)
            if (num_val_point < number_value_threshold): continue

            ww = np.hstack((w11[:, ind], w22[:, ind]))
            bb = np.hstack((bb1[ind], bb2[ind]))

            ###############################################
            ### least-square method
            ###############################################
            ww = np.transpose(ww)

            coeffprior = np.asarray(lstsq(ww, bb, rcond=None))[0]
            # cd1 = np.sum(coeffprior[:6] * x[:, offcenter])
            # cd2 = np.sum(coeffprior[6:] * x[:, offcenter])
            # ctprior = np.transpose(np.matrix([cd1, cd2]))

            ###############################################
            ### Bayes method with priori information
            ###############################################
            # bbb = sorted(b)
            # halfpoint = np.int(num_point / 2)
            # rleaf = np.average(bbb[0])
            # rsoil = np.average(bbb[1])
            # coeffprior = np.transpose(np.matrix([rsoil, 0, 0, 0, 0, 0, rleaf, 0, 0, 0, 0, 0]))
            # bb = np.transpose(np.matrix(bb))
            # ww = np.transpose(ww)
            # Cd = np.matrix(np.diag(np.ones(num_point * 2)) * Cdvaluep)
            # Cm = np.matrix(np.diag(np.ones(2 * part)))
            # Cm[0, 0] = 15.0
            # Cm[part, part] = 10.0
            # pre = np.linalg.inv(np.transpose(ww) * np.linalg.inv(Cd) * ww + np.linalg.inv(Cm))
            # ctprior = pre * (np.transpose(ww) * np.linalg.inv(Cd) * bb + np.linalg.inv(Cm) * coeffprior)

            #################################################
            ### first result without averaging information
            #################################################
            # cd1 = np.sum(coeffprior[:6] * x[:, offcenter])
            # cd2 = np.sum(coeffprior[6:] * x[:, offcenter])
            # ctprior = np.transpose(np.matrix([cd1, cd2]))

            ################################################
            ### first reult with averaing information
            ################################################
            coeffprior = np.asarray(coeffprior)
            ct1 = np.asarray([np.sum(coeffprior[:part] * x[:part, j]) for j in range(25)])
            ct2 = np.asarray([np.sum(coeffprior[part:2 * part] * x[:part, j]) for j in range(25)])
            ct3 = np.asarray([np.sum(coeffprior[2*part:3 * part] * x[:part, j]) for j in range(25)])
            indnew = ind * (ct2 < radiance_max_threshold) * (ct2 > radiance_min_threshold) * \
                     (ct1 > radiance_min_threshold) * (ct1 < radiance_max_threshold) * \
                     (ct3 > radiance_min_threshold) * (ct3 < radiance_max_threshold)
            apoint = np.sum(indnew)
            if (apoint <= 1):
                cd1 = np.sum(coeffprior[:part] * x[:, offcenter])
                cd2 = np.sum(coeffprior[part:2*part] * x[:, offcenter])
                cd3 = np.sum(coeffprior[2*part:3 * part] * x[:, offcenter])
                ctprior = np.transpose(np.matrix([cd1, cd2,cd3]))
            else:
                fd[indnew] = fd[indnew] / np.sum(fd[indnew])

                # inver-distance weight but not used
                # bb0 = bb1[offcenter]
                # fdnew = np.zeros(25)
                # dismax = max(abs(bb1[indnew] - bb0))
                # if dismax != 0:
                #     fdnew[indnew] = 1.0 - abs(1.0 * bb1[indnew] - bb0) / dismax
                # else:
                #     fdnew[:] = 1
                # fdnew[indnew] = fdnew[indnew] / np.sum(fdnew[indnew])
                # fd[indnew] = (fdnew[indnew] * fd[indnew]) / np.sum(fdnew[indnew] * fd[indnew])

                cd1new = np.sum(ct1[indnew] * fd[indnew])
                cd2new = np.sum(ct2[indnew] * fd[indnew])
                cd3new = np.sum(ct3[indnew] * fd[indnew])
                ctprior = np.transpose(np.matrix([cd1new, cd2new, cd3new]))
            component_temperature = inv_planck(wl, ctprior)
            #################################################
            ### second result by combining one-point result
            #################################################

            nl1 = k1 - off_
            nl2 = k1 + off_ + 1
            ns1 = k2 - off_
            ns2 = k2 + off_ + 1
            k11 = np.uint16(k1/2)
            k22 = np.uint16(k2/2)
            w1 = W1[:, nl1:nl2, ns1:ns2]
            w1 = np.asarray(np.reshape(w1, (number_component, -1)))
            w2 = W2[:, nl1:nl2, ns1:ns2]
            w2 = np.asarray(np.reshape(w2, (number_component, -1)))
            w3 = W3[:, k11,k22]
            w3 = np.asarray(np.reshape(w3, (number_component, -1)))

            b1 = np.reshape(rad_n[nl1:nl2, ns1:ns2], -1)
            b2 = np.reshape(rad_o[nl1:nl2, ns1:ns2], -1)
            b3 = np.reshape(rad_ahi[k11,k22],-1)
            w = np.hstack((w1, w2,w3))
            b = np.hstack((b1, b2,b3))
            w = np.transpose(w)

            #################################################
            ### least-squared method
            #################################################
            # coeffprior = np.asarray(lstsq(w, b))[0]

            #################################################
            ### Bayes method
            #################################################

            w = np.matrix(w)
            b = np.matrix(b)
            b = np.transpose(b)

            Cd = np.matrix(np.diag(np.ones(number_component)) * sensor_noise)
            Cm = np.diag([soil_radiance_variance,soil_radiance_variance, leaf_radiance_variance])
            pre = np.linalg.inv(np.transpose(w) * np.linalg.inv(Cd) * w + np.linalg.inv(Cm))
            coeff = pre * (np.transpose(w) * np.linalg.inv(Cd) * b + np.linalg.inv(Cm) * ctprior)
            ### another solution for using priori information
            # coeff = ctprior + np.transpose(Cd * np.transpose(w) * pre) * (b - np.transpose(w) * ctprior)
            component_radiance = np.asarray(coeff)

            if (np.min(component_radiance) < radiance_min_threshold): continue
            if (np.max(component_radiance) > radiance_max_threshold): continue

            component_temperature = inv_planck(wl, component_radiance)
            rad_soil = pg_n[k1,k2]*component_radiance[0]+(1-pg_n[k1,k2])* component_radiance[1]
            temperature_soil = inv_planck(wl,rad_soil)

            result[:, k1, k2] = [temperature_soil, component_temperature[2],component_temperature[0], component_temperature[1]]

    result[result < temperature_min_threshold] = default_nan_temperature
    result[result > temperature_max_threshold] = default_nan_temperature

    return result

'''''''''''''''''''''多像元和多角度 贝叶斯算法计算'''''''''''''''''''''''''''

'''计算单个点的lsct3，利用ahi'''
def inv_mpl_agl_ahi_fan(lst_n, lst_o, lst_ahi, emis_s, emis_v, fvcN, fvcO, fvcAhi, pg_n, pg_o, pg_Ahi,ind_n, ind_o, ind_Ahi,wl = 10.8, off = 2):
    radiance_max_threshold = 20
    radiance_min_threshold = 4.5
    temperature_max_threshold = 350
    temperature_min_threshold = 250
    pure_soil_threshold = 0.01
    pure_leaf_threshold = 0.99

    sensor_noise = 0.5

    soil_radiance_variance = 2
    leaf_radiance_variance = 1
    default_nan_temperature = -1
    # fvc_max_threshold = 0.99
    # fvc_min_threshold = 0.01
    number_component = 3
    number_value_threshold = 12
    fd0 = np.asarray([[1, 4, 7, 4, 1], [4, 16, 26, 16, 4], [7, 26, 41, 26, 7], [4, 16, 26, 16, 4], [1, 4, 7, 4, 1]])

    [nl,ns] = np.shape(lst_n)
    result = np.zeros([4, nl, ns])

    '''有效发射率矩阵'''
    wnAll = np.asarray([emis_s*(1-fvcN)*pg_n, emis_s*(1-fvcN)*(1-pg_n), emis_v*fvcN])
    woAll = np.asarray([emis_s*(1-fvcO)*pg_o, emis_s*(1-fvcO)*(1-pg_o), emis_v*fvcO])
    wAhiAll = np.asarray([emis_s*(1-fvcAhi)*pg_Ahi, emis_s*(1-fvcAhi)*(1-pg_Ahi), emis_v*fvcAhi])

    '''辐射'''
    radnAll = planck(wl, lst_n)
    radoAll = planck(wl, lst_o)
    radAhiAll = planck(wl, lst_ahi)

    '''标记可用点，可用为1'''
    maskAll = np.zeros([nl,ns])
    indAll = (lst_n > temperature_min_threshold) * (lst_n < temperature_max_threshold)* \
          (lst_o > temperature_min_threshold) * (lst_o < temperature_max_threshold) * \
          (lst_ahi > temperature_min_threshold) * (lst_ahi < temperature_max_threshold) *\
          (fvcN > pure_soil_threshold) * (fvcN < pure_leaf_threshold)* \
          (ind_n == 1) * (ind_o==1) * (ind_Ahi==1)
    maskAll[indAll] = 1

    '''形成坐标系数， 6*25， 5*5的框'''
    windowX = np.asarray(np.repeat([-2, -1, 0, 1, 2], 5)).reshape(5, -1).transpose().reshape(-1)
    windowY = np.asarray(np.repeat([2, 1, 0, -1, -2], 5))
    coef0 = np.ones([5, 5]).reshape(-1)
    windowCoef = np.asarray([coef0, windowX, windowY, windowX * windowY, windowX * windowX, windowY * windowY])

    '''5*5的框循环'''
    for k1 in range(off, nl-off):
        for k2 in range(off, ns-off):
            if(maskAll[k1, k2] != 1): continue

            '''多像元计算   6*N 个系数'''
            nl1 = k1 - off
            nl2 = k1 + off + 1
            ns1 = k2 - off
            ns2 = k2 + off + 1

            mask = maskAll[nl1:nl2, ns1:ns2]
            if(sum(mask) < number_value_threshold): continue
            mask = mask.reshape(-1)
            ind = (mask==1)

            wn = wnAll[:, nl1:nl2, ns1:ns2]
            wo = woAll[:, nl1:nl2, ns1:ns2]
            wAhi = wAhiAll[:, nl1:nl2, ns1:ns2]
            wn = np.asarray(np.reshape(wn, (number_component, -1)))
            wo = np.asarray(np.reshape(wo, (number_component, -1)))
            wAhi = np.asarray(np.reshape(wAhi, (number_component, -1)))

            radn = radnAll[nl1:nl2, ns1:ns2]
            rado = radoAll[nl1:nl2, ns1:ns2]
            radAhi = radAhiAll[nl1:nl2, ns1:ns2]

            w1 = np.asarray([wn[j, :] * windowCoef[i, :] for j in range(number_component) for i in range(6)])
            w2 = np.asarray([wo[j, :] * windowCoef[i, :] for j in range(number_component) for i in range(6)])
            radn = radn.reshape(-1)
            rado = rado.reshape(-1)

            temp1 = (np.reshape(fvcN[nl1:nl2, ns1:ns2], -1))
            temp2 = (np.reshape(fvcO[nl1:nl2, ns1:ns2], -1))
            ind = (radn < radiance_max_threshold) * (rado > radiance_min_threshold) * \
                  (temp1 > pure_soil_threshold) * (temp1 < pure_leaf_threshold) * \
                  (temp2 > pure_soil_threshold) * (temp2 < pure_leaf_threshold) * \
                  (rado < radiance_max_threshold) * (rado > radiance_min_threshold) * \
                  (np.isnan(w1[0,:]) != 1) * (np.isnan(w1[1,:]) != 1) * (np.isnan(w1[2,:]) != 1)
            num_val_point = np.sum(ind)
            if (num_val_point < number_value_threshold): continue

            ww = np.hstack((w1[:, ind], w2[:, ind])).transpose()
            bb = np.hstack((radn[ind], rado[ind]))
            coeffprior = np.asarray(fitting_lsct(ww,bb))


            ct1 = np.asarray([np.sum(coeffprior[:6] * windowCoef[:, j]) for j in range(25)])
            ct2 = np.asarray([np.sum(coeffprior[6:12] * windowCoef[:, j]) for j in range(25)])
            ct3 = np.asarray([np.sum(coeffprior[12:] * windowCoef[:, j]) for j in range(25)])
            offcenter = int((2*off+1)*(2*off+1)/2)
            # cd1 = np.sum(coeffprior[:6] * windowCoef[:, offcenter])
            # cd2 = np.sum(coeffprior[6:12] * windowCoef[:, offcenter])
            # cd3 = np.sum(coeffprior[12:] * windowCoef[:, offcenter])
            # ctprior = np.transpose(np.asarray([cd1, cd2, cd3]))

            indnew = ind*(ct1 < radiance_max_threshold) * (ct1 > radiance_min_threshold)* \
                     (ct2 < radiance_max_threshold) * (ct2 > radiance_min_threshold)* \
                     (ct3 < radiance_max_threshold) * (ct3 > radiance_min_threshold)
            pointNum = np.sum(indnew)

            if pointNum<=1:
                offcenter = int((2*off+1)*(2*off+1)/2)
                cd1 = np.sum(coeffprior[:6] * windowCoef[:, offcenter])
                cd2 = np.sum(coeffprior[6:12] * windowCoef[:, offcenter])
                cd3 = np.sum(coeffprior[12:] * windowCoef[:, offcenter])
                ctprior = np.transpose(np.asarray([cd1, cd2, cd3]))
            else:
                fd = np.reshape(fd0, -1) * 1.0
                fd[indnew] = fd[indnew]/np.sum(fd[indnew])
                cd1 = np.sum(ct1[indnew] * fd[indnew])
                cd2 = np.sum(ct2[indnew] * fd[indnew])
                cd3 = np.sum(ct3[indnew] * fd[indnew])
                ctprior = np.transpose(np.asarray([cd1, cd2, cd3]))
            # component_temperature = inv_planck(wl, ctprior)

            '''多角度计算'''
            wn_2 = wnAll[:, k1, k2]
            wo_2 = woAll[:, k1, k2]
            wAhi_2 = wAhiAll[:, k1, k2]
            wn_2 = np.asarray(np.reshape(wn_2, (number_component, -1)))
            wo_2 = np.asarray(np.reshape(wo_2, (number_component, -1)))
            wAhi_2 = np.asarray(np.reshape(wAhi_2, (number_component, -1)))

            radn_2 = radnAll[k1, k2]
            rado_2 = radoAll[k1, k2]
            radAhi_2 = radAhiAll[k1, k2]

            ww_2 = np.hstack((wn_2, wo_2, wAhi_2)).transpose()
            bb_2 = np.hstack((radn_2, rado_2, radAhi_2)).transpose()
            coeffprior_2 = np.asarray(lstsq(ww_2, bb_2))[0]

            Cd = np.asarray(np.diag(np.ones(number_component)) * sensor_noise)
            Cm = np.diag([soil_radiance_variance, soil_radiance_variance, leaf_radiance_variance])
            pre = np.linalg.inv(np.transpose(ww_2) * np.linalg.inv(Cd) * ww_2 + np.linalg.inv(Cm))
            coeff = pre * (np.transpose(ww_2) * np.linalg.inv(Cd) * bb_2 + np.linalg.inv(Cm) * ctprior)
            ### another solution for using priori information
            # coeff = ctprior + np.transpose(Cd * np.transpose(w) * pre) * (b - np.transpose(w) * ctprior)
            component_radiance = np.diagonal(coeff)

            if (np.min(component_radiance) < radiance_min_threshold):
                result[:, k1, k2] = [-1, -1, -1, -1]
                continue
            if (np.max(component_radiance) > radiance_max_threshold):
                result[:, k1, k2] = [-1, -1, -1, -1]
                continue
            component_temperature = inv_planck(wl, component_radiance)
            rad_soil = pg_n[k1, k2] * component_radiance[0] + (1 - pg_n[k1, k2]) * component_radiance[1]
            temperature_soil = inv_planck(wl, rad_soil)

            result[:, k1, k2] = [temperature_soil, component_temperature[2], component_temperature[0],
                                 component_temperature[1]]

        # result[result < temperature_min_threshold] = default_nan_temperature
        # result[result > temperature_max_threshold] = default_nan_temperature

    return result

'''计算单个点的lsct3，不用ahi'''
def inv_mpl_agl_fan(lst_n, lst_o, lst_ahi, emis_s, emis_v, fvcN, fvcO, fvcAhi, pg_n, pg_o, pg_Ahi,ind_n, ind_o, ind_Ahi,wl = 10.8, off = 2):
    radiance_max_threshold = 20
    radiance_min_threshold = 4.5
    temperature_max_threshold = 350
    temperature_min_threshold = 250
    pure_soil_threshold = 0.01
    pure_leaf_threshold = 0.99

    sensor_noise = 0.5

    soil_radiance_variance = 2
    leaf_radiance_variance = 1
    default_nan_temperature = -1
    # fvc_max_threshold = 0.99
    # fvc_min_threshold = 0.01
    number_component = 3
    number_value_threshold = 12
    fd0 = np.asarray([[1, 4, 7, 4, 1], [4, 16, 26, 16, 4], [7, 26, 41, 26, 7], [4, 16, 26, 16, 4], [1, 4, 7, 4, 1]])

    [nl,ns] = np.shape(lst_n)
    result = np.zeros([4, nl, ns])

    '''有效发射率矩阵'''
    wnAll = np.asarray([emis_s*(1-fvcN)*pg_n, emis_s*(1-fvcN)*(1-pg_n), emis_v*fvcN])
    woAll = np.asarray([emis_s*(1-fvcO)*pg_o, emis_s*(1-fvcO)*(1-pg_o), emis_v*fvcO])
    wAhiAll = np.asarray([emis_s*(1-fvcAhi)*pg_Ahi, emis_s*(1-fvcAhi)*(1-pg_Ahi), emis_v*fvcAhi])

    '''辐射'''
    radnAll = planck(wl, lst_n)
    radoAll = planck(wl, lst_o)
    radAhiAll = planck(wl, lst_ahi)

    '''标记可用点，可用为1'''
    maskAll = np.zeros([nl,ns])
    indAll = (lst_n > temperature_min_threshold) * (lst_n < temperature_max_threshold)* \
          (lst_o > temperature_min_threshold) * (lst_o < temperature_max_threshold) * \
          (lst_ahi > temperature_min_threshold) * (lst_ahi < temperature_max_threshold) *\
          (fvcN > pure_soil_threshold) * (fvcN < pure_leaf_threshold)* \
          (ind_n == 1) * (ind_o==1) * (ind_Ahi==1)
    maskAll[indAll] = 1

    '''形成坐标系数， 6*25， 5*5的框'''
    windowX = np.asarray(np.repeat([-2, -1, 0, 1, 2], 5)).reshape(5, -1).transpose().reshape(-1)
    windowY = np.asarray(np.repeat([2, 1, 0, -1, -2], 5))
    coef0 = np.ones([5, 5]).reshape(-1)
    windowCoef = np.asarray([coef0, windowX, windowY, windowX * windowY, windowX * windowX, windowY * windowY])

    '''5*5的框循环'''
    for k1 in range(off, nl-off):
        for k2 in range(off, ns-off):
            if(maskAll[k1, k2] != 1): continue

            '''多像元计算   6*N 个系数'''
            nl1 = k1 - off
            nl2 = k1 + off + 1
            ns1 = k2 - off
            ns2 = k2 + off + 1

            mask = maskAll[nl1:nl2, ns1:ns2]
            if(sum(mask) < number_value_threshold): continue
            mask = mask.reshape(-1)
            ind = (mask==1)

            wn = wnAll[:, nl1:nl2, ns1:ns2]
            wo = woAll[:, nl1:nl2, ns1:ns2]
            wAhi = wAhiAll[:, nl1:nl2, ns1:ns2]
            wn = np.asarray(np.reshape(wn, (number_component, -1)))
            wo = np.asarray(np.reshape(wo, (number_component, -1)))
            wAhi = np.asarray(np.reshape(wAhi, (number_component, -1)))

            radn = radnAll[nl1:nl2, ns1:ns2]
            rado = radoAll[nl1:nl2, ns1:ns2]
            radAhi = radAhiAll[nl1:nl2, ns1:ns2]

            w1 = np.asarray([wn[j, :] * windowCoef[i, :] for j in range(number_component) for i in range(6)])
            w2 = np.asarray([wo[j, :] * windowCoef[i, :] for j in range(number_component) for i in range(6)])
            radn = radn.reshape(-1)
            rado = rado.reshape(-1)

            temp1 = (np.reshape(fvcN[nl1:nl2, ns1:ns2], -1))
            temp2 = (np.reshape(fvcO[nl1:nl2, ns1:ns2], -1))
            ind = (radn < radiance_max_threshold) * (rado > radiance_min_threshold) * \
                  (temp1 > pure_soil_threshold) * (temp1 < pure_leaf_threshold) * \
                  (temp2 > pure_soil_threshold) * (temp2 < pure_leaf_threshold) * \
                  (rado < radiance_max_threshold) * (rado > radiance_min_threshold) * \
                  (np.isnan(w1[0,:]) != 1) * (np.isnan(w1[1,:]) != 1) * (np.isnan(w1[2,:]) != 1)
            num_val_point = np.sum(ind)
            if (num_val_point < number_value_threshold): continue

            ww = np.hstack((w1[:, ind], w2[:, ind])).transpose()
            bb = np.hstack((radn[ind], rado[ind]))
            coeffprior = np.asarray(fitting_lsct(ww,bb))


            ct1 = np.asarray([np.sum(coeffprior[:6] * windowCoef[:, j]) for j in range(25)])
            ct2 = np.asarray([np.sum(coeffprior[6:12] * windowCoef[:, j]) for j in range(25)])
            ct3 = np.asarray([np.sum(coeffprior[12:] * windowCoef[:, j]) for j in range(25)])
            offcenter = int((2*off+1)*(2*off+1)/2)
            # cd1 = np.sum(coeffprior[:6] * windowCoef[:, offcenter])
            # cd2 = np.sum(coeffprior[6:12] * windowCoef[:, offcenter])
            # cd3 = np.sum(coeffprior[12:] * windowCoef[:, offcenter])
            # ctprior = np.transpose(np.asarray([cd1, cd2, cd3]))

            indnew = ind*(ct1 < radiance_max_threshold) * (ct1 > radiance_min_threshold)* \
                     (ct2 < radiance_max_threshold) * (ct2 > radiance_min_threshold)* \
                     (ct3 < radiance_max_threshold) * (ct3 > radiance_min_threshold)
            pointNum = np.sum(indnew)

            if pointNum<=1:
                offcenter = int((2*off+1)*(2*off+1)/2)
                cd1 = np.sum(coeffprior[:6] * windowCoef[:, offcenter])
                cd2 = np.sum(coeffprior[6:12] * windowCoef[:, offcenter])
                cd3 = np.sum(coeffprior[12:] * windowCoef[:, offcenter])
                ctprior = np.transpose(np.asarray([cd1, cd2, cd3]))
            else:
                fd = np.reshape(fd0, -1) * 1.0
                fd[indnew] = fd[indnew]/np.sum(fd[indnew])
                cd1 = np.sum(ct1[indnew] * fd[indnew])
                cd2 = np.sum(ct2[indnew] * fd[indnew])
                cd3 = np.sum(ct3[indnew] * fd[indnew])
                ctprior = np.transpose(np.asarray([cd1, cd2, cd3]))
            # component_temperature = inv_planck(wl, ctprior)

            '''多角度计算'''
            wn_2 = wnAll[:, k1, k2]
            wo_2 = woAll[:, k1, k2]
            wAhi_2 = wAhiAll[:, k1, k2]
            wn_2 = np.asarray(np.reshape(wn_2, (number_component, -1)))
            wo_2 = np.asarray(np.reshape(wo_2, (number_component, -1)))
            wAhi_2 = np.asarray(np.reshape(wAhi_2, (number_component, -1)))

            radn_2 = radnAll[k1, k2]
            rado_2 = radoAll[k1, k2]
            radAhi_2 = radAhiAll[k1, k2]

            ww_2 = np.hstack((wn_2, wo_2)).transpose()
            bb_2 = np.hstack((radn_2, rado_2)).transpose()
            coeffprior_2 = np.asarray(lstsq(ww_2, bb_2))[0]

            Cd = np.asarray(np.diag(np.ones(2)) * sensor_noise)
            Cm = np.diag([soil_radiance_variance, soil_radiance_variance, leaf_radiance_variance])
            pre = np.linalg.inv(np.matmul(np.matmul(np.transpose(ww_2), np.linalg.inv(Cd)), ww_2) + np.linalg.inv(Cm))
            coeff = pre * (np.matmul(np.matmul(np.transpose(ww_2), np.linalg.inv(Cd)), bb_2) + np.linalg.inv(Cm) * ctprior)
            ### another solution for using priori information
            # coeff = ctprior + np.transpose(Cd * np.transpose(w) * pre) * (b - np.transpose(w) * ctprior)
            component_radiance = np.diagonal(coeff)

            if (np.min(component_radiance) < radiance_min_threshold):
                result[:, k1, k2] = [-1, -1, -1, -1]
                continue
            if (np.max(component_radiance) > radiance_max_threshold):
                result[:, k1, k2] = [-1, -1, -1, -1]
                continue
            component_temperature = inv_planck(wl, component_radiance)
            rad_soil = pg_n[k1, k2] * component_radiance[0] + (1 - pg_n[k1, k2]) * component_radiance[1]
            temperature_soil = inv_planck(wl, rad_soil)

            result[:, k1, k2] = [temperature_soil, component_temperature[2], component_temperature[0],
                                 component_temperature[1]]

        # result[result < temperature_min_threshold] = default_nan_temperature
        # result[result > temperature_max_threshold] = default_nan_temperature

    return result

'''计算单个点的lsct2,利用ahi'''
def inv_mpl_agl_ahi_fan_2(lst_n, lst_o, lst_ahi, emis_s, emis_v, fvcN, fvcO, fvcAhi, ind_n, ind_o, ind_Ahi,wl = 10.8, off = 2, sensor_noise = 0.5):
    radiance_max_threshold = 20
    radiance_min_threshold = 4.5
    temperature_max_threshold = 350
    temperature_min_threshold = 250
    pure_soil_threshold = 0.01
    pure_leaf_threshold = 0.99

    soil_radiance_variance = 2
    leaf_radiance_variance = 1
    default_nan_temperature = -1
    # fvc_max_threshold = 0.99
    # fvc_min_threshold = 0.01
    number_component = 2
    number_value_threshold = 12
    fd0 = np.asarray([[1, 4, 7, 4, 1], [4, 16, 26, 16, 4],
                      [7, 26, 41, 26, 7], [4, 16, 26, 16, 4],
                      [1, 4, 7, 4, 1]])

    [nl,ns] = np.shape(lst_n)
    result = np.zeros([number_component, nl, ns])

    '''有效发射率矩阵'''
    wnAll = np.asarray([emis_s*(1-fvcN), emis_v*fvcN])
    woAll = np.asarray([emis_s*(1-fvcO), emis_v*fvcO])
    wAhiAll = np.asarray([emis_s*(1-fvcAhi), emis_v*fvcAhi])

    '''辐射'''
    radnAll = planck(wl, lst_n)
    radoAll = planck(wl, lst_o)
    radAhiAll = planck(wl, lst_ahi)

    '''标记可用点，可用为1'''
    maskAll = np.zeros([nl,ns])
    indAll = (lst_n > temperature_min_threshold) * (lst_n < temperature_max_threshold)* \
          (lst_o > temperature_min_threshold) * (lst_o < temperature_max_threshold) * \
          (lst_ahi > temperature_min_threshold) * (lst_ahi < temperature_max_threshold) *\
          (fvcN > pure_soil_threshold) * (fvcN < pure_leaf_threshold)* \
          (ind_n == 1) * (ind_o==1) * (ind_Ahi==1)
    maskAll[indAll] = 1

    '''形成坐标系数， 6*25， 5*5的框'''
    windowX = np.asarray(np.repeat([-2, -1, 0, 1, 2], 5)).reshape(5, -1).transpose().reshape(-1)
    windowY = np.asarray(np.repeat([2, 1, 0, -1, -2], 5))
    coef0 = np.ones([5, 5]).reshape(-1)
    windowCoef = np.asarray([coef0, windowX, windowY, windowX * windowY, windowX * windowX, windowY * windowY])

    '''5*5的框循环'''
    for k1 in range(off, nl-off):
        for k2 in range(off, ns-off):
            if(maskAll[k1, k2] != 1): continue

            '''多像元计算   6*N 个系数'''
            nl1 = k1 - off
            nl2 = k1 + off + 1
            ns1 = k2 - off
            ns2 = k2 + off + 1

            mask = maskAll[nl1:nl2, ns1:ns2]
            if(sum(mask) < number_value_threshold): continue
            mask = mask.reshape(-1)
            ind = (mask==1)

            wn = wnAll[:, nl1:nl2, ns1:ns2]
            wo = woAll[:, nl1:nl2, ns1:ns2]
            wAhi = wAhiAll[:, nl1:nl2, ns1:ns2]
            wn = np.asarray(np.reshape(wn, (number_component, -1)))
            wo = np.asarray(np.reshape(wo, (number_component, -1)))
            wAhi = np.asarray(np.reshape(wAhi, (number_component, -1)))

            radn = radnAll[nl1:nl2, ns1:ns2]
            rado = radoAll[nl1:nl2, ns1:ns2]
            radAhi = radAhiAll[nl1:nl2, ns1:ns2]

            w1 = np.asarray([wn[j, :] * windowCoef[i, :] for j in range(number_component) for i in range(6)])
            w2 = np.asarray([wo[j, :] * windowCoef[i, :] for j in range(number_component) for i in range(6)])
            radn = radn.reshape(-1)
            rado = rado.reshape(-1)

            temp1 = (np.reshape(fvcN[nl1:nl2, ns1:ns2], -1))
            temp2 = (np.reshape(fvcO[nl1:nl2, ns1:ns2], -1))
            ind = (radn < radiance_max_threshold) * (rado > radiance_min_threshold) * \
                  (temp1 > pure_soil_threshold) * (temp1 < pure_leaf_threshold) * \
                  (temp2 > pure_soil_threshold) * (temp2 < pure_leaf_threshold) * \
                  (rado < radiance_max_threshold) * (rado > radiance_min_threshold) * \
                  (np.isnan(w1[0,:]) != 1) * (np.isnan(w1[1,:]) != 1) * (np.isnan(w1[2,:]) != 1)
            num_val_point = np.sum(ind)
            if (num_val_point < number_value_threshold): continue

            ww = np.hstack((w1[:, ind], w2[:, ind])).transpose()
            bb = np.hstack((radn[ind], rado[ind]))
            coeffprior = np.asarray(fitting_lsct_2(ww,bb))


            ct1 = np.asarray([np.sum(coeffprior[:6] * windowCoef[:, j]) for j in range(25)])
            ct2 = np.asarray([np.sum(coeffprior[6:12] * windowCoef[:, j]) for j in range(25)])
            offcenter = int((2*off+1)*(2*off+1)/2)
            # cd1 = np.sum(coeffprior[:6] * windowCoef[:, offcenter])
            # cd2 = np.sum(coeffprior[6:12] * windowCoef[:, offcenter])
            # cd3 = np.sum(coeffprior[12:] * windowCoef[:, offcenter])
            # ctprior = np.transpose(np.asarray([cd1, cd2, cd3]))

            indnew = ind*(ct1 < radiance_max_threshold) * (ct1 > radiance_min_threshold)* \
                     (ct2 < radiance_max_threshold) * (ct2 > radiance_min_threshold)
            pointNum = np.sum(indnew)

            if pointNum<=1:
                offcenter = int((2*off+1)*(2*off+1)/2)
                cd1 = np.sum(coeffprior[:6] * windowCoef[:, offcenter])
                cd2 = np.sum(coeffprior[6:12] * windowCoef[:, offcenter])
                ctprior = np.transpose(np.asarray([cd1, cd2]))
            else:
                fd = np.reshape(fd0, -1) * 1.0
                fd[indnew] = fd[indnew]/np.sum(fd[indnew])
                cd1 = np.sum(ct1[indnew] * fd[indnew])
                cd2 = np.sum(ct2[indnew] * fd[indnew])
                ctprior = np.transpose(np.asarray([cd1, cd2]))
            # component_temperature = inv_planck(wl, ctprior)

            '''多角度计算'''
            wn_2 = wnAll[:, k1, k2]
            wo_2 = woAll[:, k1, k2]
            wAhi_2 = wAhiAll[:, k1, k2]
            wn_2 = np.asarray(np.reshape(wn_2, (number_component, -1)))
            wo_2 = np.asarray(np.reshape(wo_2, (number_component, -1)))
            wAhi_2 = np.asarray(np.reshape(wAhi_2, (number_component, -1)))

            radn_2 = radnAll[k1, k2]
            rado_2 = radoAll[k1, k2]
            radAhi_2 = radAhiAll[k1, k2]

            ww_2 = np.hstack((wn_2, wo_2, wAhi_2)).transpose()
            bb_2 = np.hstack((radn_2, rado_2, radAhi_2)).transpose()
            coeffprior_2 = np.asarray(lstsq(ww_2, bb_2))[0]

            Cd = np.asarray(np.diag(np.ones(3)) * sensor_noise)
            Cm = np.diag([soil_radiance_variance,leaf_radiance_variance])
            pre = np.linalg.inv(np.matmul(np.matmul(np.transpose(ww_2) , np.linalg.inv(Cd)) , ww_2) + np.linalg.inv(Cm))
            coeff = pre * (np.matmul(np.matmul(np.transpose(ww_2) , np.linalg.inv(Cd)) , bb_2 )+ np.linalg.inv(Cm) * ctprior)
            ### another solution for using priori information
            # coeff = ctprior + np.transpose(Cd * np.transpose(w) * pre) * (b - np.transpose(w) * ctprior)
            component_radiance = np.diagonal(coeff)

            if (np.min(component_radiance) < radiance_min_threshold):
                result[:, k1, k2] = [-1, -1]
                continue
            if (np.max(component_radiance) > radiance_max_threshold):
                result[:, k1, k2] = [-1, -1]
                continue
            component_temperature = inv_planck(wl, component_radiance)
            # rad_soil = pg_n[k1, k2] * component_radiance[0] + (1 - pg_n[k1, k2]) * component_radiance[1]
            # temperature_soil = inv_planck(wl, rad_soil)

            result[:, k1, k2] = [component_temperature[0],
                                 component_temperature[1]]

        # result[result < temperature_min_threshold] = default_nan_temperature
        # result[result > temperature_max_threshold] = default_nan_temperature

    return result

'''计算单个点的lsct2，不用AHi,虽然输入了ahi，但是没用，这里只是方便修改和统一对比'''
def inv_mpl_agl_fan_2(lst_n, lst_o, lst_ahi, emis_s, emis_v, fvcN, fvcO, fvcAhi, wl = 10.8, off = 2, sensor_noise = 0.5):
    radiance_max_threshold = 20
    radiance_min_threshold = 4.5
    temperature_max_threshold = 350
    temperature_min_threshold = 250
    pure_soil_threshold = 0.01
    pure_leaf_threshold = 0.99

    soil_radiance_variance = 2
    leaf_radiance_variance = 1
    default_nan_temperature = -1
    # fvc_max_threshold = 0.99
    # fvc_min_threshold = 0.01
    number_component = 2
    number_value_threshold = 12
    fd0 = np.asarray([[1, 4, 7, 4, 1], [4, 16, 26, 16, 4], [7, 26, 41, 26, 7], [4, 16, 26, 16, 4], [1, 4, 7, 4, 1]])

    [nl,ns] = np.shape(lst_n)
    result = np.zeros([number_component, nl, ns])

    '''有效发射率矩阵'''
    wnAll = np.asarray([emis_s*(1-fvcN), emis_v*fvcN])
    woAll = np.asarray([emis_s*(1-fvcO), emis_v*fvcO])
    wAhiAll = np.asarray([emis_s*(1-fvcAhi), emis_v*fvcAhi])

    '''辐射'''
    radnAll = planck(wl, lst_n)
    radoAll = planck(wl, lst_o)
    radAhiAll = planck(wl, lst_ahi)

    '''标记可用点，可用为1'''
    maskAll = np.zeros([nl,ns])
    indAll = (lst_n > temperature_min_threshold) * (lst_n < temperature_max_threshold)* \
          (lst_o > temperature_min_threshold) * (lst_o < temperature_max_threshold) * \
          (lst_ahi > temperature_min_threshold) * (lst_ahi < temperature_max_threshold) *\
          (fvcN > pure_soil_threshold) * (fvcN < pure_leaf_threshold)
    maskAll[indAll] = 1

    '''形成坐标系数， 6*25， 5*5的框'''
    windowX = np.asarray(np.repeat([-2, -1, 0, 1, 2], 5)).reshape(5, -1).transpose().reshape(-1)
    windowY = np.asarray(np.repeat([2, 1, 0, -1, -2], 5))
    coef0 = np.ones([5, 5]).reshape(-1)
    windowCoef = np.asarray([coef0, windowX, windowY, windowX * windowY, windowX * windowX, windowY * windowY])

    '''5*5的框循环'''
    for k1 in range(off, nl-off):
        for k2 in range(off, ns-off):
            if(maskAll[k1, k2] != 1): continue

            '''多像元计算   6*N 个系数'''
            nl1 = k1 - off
            nl2 = k1 + off + 1
            ns1 = k2 - off
            ns2 = k2 + off + 1

            mask = maskAll[nl1:nl2, ns1:ns2]
            if(sum(mask) < number_value_threshold): continue
            mask = mask.reshape(-1)
            ind = (mask==1)

            wn = wnAll[:, nl1:nl2, ns1:ns2]
            wo = woAll[:, nl1:nl2, ns1:ns2]
            wAhi = wAhiAll[:, nl1:nl2, ns1:ns2]
            wn = np.asarray(np.reshape(wn, (number_component, -1)))
            wo = np.asarray(np.reshape(wo, (number_component, -1)))
            wAhi = np.asarray(np.reshape(wAhi, (number_component, -1)))

            radn = radnAll[nl1:nl2, ns1:ns2]
            rado = radoAll[nl1:nl2, ns1:ns2]
            radAhi = radAhiAll[nl1:nl2, ns1:ns2]

            w1 = np.asarray([wn[j, :] * windowCoef[i, :] for j in range(number_component) for i in range(6)])
            w2 = np.asarray([wo[j, :] * windowCoef[i, :] for j in range(number_component) for i in range(6)])
            radn = radn.reshape(-1)
            rado = rado.reshape(-1)

            temp1 = (np.reshape(fvcN[nl1:nl2, ns1:ns2], -1))
            temp2 = (np.reshape(fvcO[nl1:nl2, ns1:ns2], -1))
            ind = (radn < radiance_max_threshold) * (rado > radiance_min_threshold) * \
                  (temp1 > pure_soil_threshold) * (temp1 < pure_leaf_threshold) * \
                  (temp2 > pure_soil_threshold) * (temp2 < pure_leaf_threshold) * \
                  (rado < radiance_max_threshold) * (rado > radiance_min_threshold) * \
                  (np.isnan(w1[0,:]) != 1) * (np.isnan(w1[1,:]) != 1) * (np.isnan(w1[2,:]) != 1)
            num_val_point = np.sum(ind)
            if (num_val_point < number_value_threshold): continue

            ww = np.hstack((w1[:, ind], w2[:, ind])).transpose()
            bb = np.hstack((radn[ind], rado[ind]))
            coeffprior = np.asarray(fitting_lsct_2(ww,bb))


            ct1 = np.asarray([np.sum(coeffprior[:6] * windowCoef[:, j]) for j in range(25)])
            ct2 = np.asarray([np.sum(coeffprior[6:12] * windowCoef[:, j]) for j in range(25)])
            offcenter = int((2*off+1)*(2*off+1)/2)
            # cd1 = np.sum(coeffprior[:6] * windowCoef[:, offcenter])
            # cd2 = np.sum(coeffprior[6:12] * windowCoef[:, offcenter])
            # cd3 = np.sum(coeffprior[12:] * windowCoef[:, offcenter])
            # ctprior = np.transpose(np.asarray([cd1, cd2, cd3]))

            indnew = ind*(ct1 < radiance_max_threshold) * (ct1 > radiance_min_threshold)* \
                     (ct2 < radiance_max_threshold) * (ct2 > radiance_min_threshold)
            pointNum = np.sum(indnew)

            if pointNum<=1:
                offcenter = int((2*off+1)*(2*off+1)/2)
                cd1 = np.sum(coeffprior[:6] * windowCoef[:, offcenter])
                cd2 = np.sum(coeffprior[6:12] * windowCoef[:, offcenter])
                ctprior = np.transpose(np.asarray([cd1, cd2]))
            else:
                fd = np.reshape(fd0, -1) * 1.0
                fd[indnew] = fd[indnew]/np.sum(fd[indnew])
                cd1 = np.sum(ct1[indnew] * fd[indnew])
                cd2 = np.sum(ct2[indnew] * fd[indnew])
                ctprior = np.transpose(np.asarray([cd1, cd2]))
            # component_temperature = inv_planck(wl, ctprior)

            '''多角度计算'''
            wn_2 = wnAll[:, k1, k2]
            wo_2 = woAll[:, k1, k2]
            wAhi_2 = wAhiAll[:, k1, k2]
            wn_2 = np.asarray(np.reshape(wn_2, (number_component, -1)))
            wo_2 = np.asarray(np.reshape(wo_2, (number_component, -1)))
            wAhi_2 = np.asarray(np.reshape(wAhi_2, (number_component, -1)))

            radn_2 = radnAll[k1, k2]
            rado_2 = radoAll[k1, k2]
            radAhi_2 = radAhiAll[k1, k2]

            ww_2 = np.hstack((wn_2, wo_2)).transpose()
            bb_2 = np.hstack((radn_2, rado_2)).transpose()
            coeffprior_2 = np.asarray(lstsq(ww_2, bb_2))[0]

            Cd = np.asarray(np.diag(np.ones(2)) * sensor_noise)
            Cm = np.diag([soil_radiance_variance,leaf_radiance_variance])
            pre = np.linalg.inv(np.matmul(np.matmul(np.transpose(ww_2) , np.linalg.inv(Cd)) , ww_2) + np.linalg.inv(Cm))
            coeff = pre * (np.matmul(np.matmul(np.transpose(ww_2) , np.linalg.inv(Cd)) , bb_2 )+ np.linalg.inv(Cm) * ctprior)
            ### another solution for using priori information
            # coeff = ctprior + np.transpose(Cd * np.transpose(w) * pre) * (b - np.transpose(w) * ctprior)
            component_radiance = np.diagonal(coeff)

            if (np.min(component_radiance) < radiance_min_threshold):
                result[:, k1, k2] = [-1, -1]
                continue
            if (np.max(component_radiance) > radiance_max_threshold):
                result[:, k1, k2] = [-1, -1]
                continue

            component_temperature = inv_planck(wl, component_radiance)
            # rad_soil = pg_n[k1, k2] * component_radiance[0] + (1 - pg_n[k1, k2]) * component_radiance[1]
            # temperature_soil = inv_planck(wl, rad_soil)

            result[:, k1, k2] = [component_temperature[0],
                                 component_temperature[1]]
        # result[result < temperature_min_threshold] = default_nan_temperature
        # result[result > temperature_max_threshold] = default_nan_temperature

    return result



''''''''''''''''''''' 多像元和多角度的 单个算法计算'''''''''''''''''''''''''''

'''计算单个点的lsct2，未利用ahi， 多像元'''
def inv_mpl_fan_2(lst_n, lst_o, lst_ahi, emis_s, emis_v, fvcN, fvcO, fvcAhi, pg_n, pg_o, pg_Ahi,ind_n, ind_o, ind_Ahi,wl = 10.8, off = 2):
    radiance_max_threshold = 20
    radiance_min_threshold = 4.5
    temperature_max_threshold = 350
    temperature_min_threshold = 250
    pure_soil_threshold = 0.01
    pure_leaf_threshold = 0.99

    sensor_noise = 0.5

    soil_radiance_variance = 2
    leaf_radiance_variance = 1
    default_nan_temperature = -1
    # fvc_max_threshold = 0.99
    # fvc_min_threshold = 0.01
    number_component = 2
    number_value_threshold = 12
    fd0 = np.asarray([[1, 4, 7, 4, 1], [4, 16, 26, 16, 4], [7, 26, 41, 26, 7], [4, 16, 26, 16, 4], [1, 4, 7, 4, 1]])

    [nl,ns] = np.shape(lst_n)
    result = np.zeros([number_component, nl, ns])

    '''有效发射率矩阵'''
    wnAll = np.asarray([emis_s*(1-fvcN), emis_v*fvcN])
    woAll = np.asarray([emis_s*(1-fvcO), emis_v*fvcO])
    wAhiAll = np.asarray([emis_s*(1-fvcAhi), emis_v*fvcAhi])

    '''辐射'''
    radnAll = planck(wl, lst_n)
    radoAll = planck(wl, lst_o)
    radAhiAll = planck(wl, lst_ahi)

    '''标记可用点，可用为1'''
    maskAll = np.zeros([nl,ns])
    indAll = (lst_n > temperature_min_threshold) * (lst_n < temperature_max_threshold)* \
          (lst_o > temperature_min_threshold) * (lst_o < temperature_max_threshold) * \
          (lst_ahi > temperature_min_threshold) * (lst_ahi < temperature_max_threshold) *\
          (fvcN > pure_soil_threshold) * (fvcN < pure_leaf_threshold)* \
          (ind_n == 1) * (ind_o==1) * (ind_Ahi==1)
    maskAll[indAll] = 1

    '''形成坐标系数， 6*25， 5*5的框'''
    windowX = np.asarray(np.repeat([-2, -1, 0, 1, 2], 5)).reshape(5, -1).transpose().reshape(-1)
    windowY = np.asarray(np.repeat([2, 1, 0, -1, -2], 5))
    coef0 = np.ones([5, 5]).reshape(-1)
    windowCoef = np.asarray([coef0, windowX, windowY, windowX * windowY, windowX * windowX, windowY * windowY])

    '''5*5的框循环'''
    for k1 in range(off, nl-off):
        for k2 in range(off, ns-off):
            if(maskAll[k1, k2] != 1): continue

            '''多像元计算   6*N 个系数'''
            nl1 = k1 - off
            nl2 = k1 + off + 1
            ns1 = k2 - off
            ns2 = k2 + off + 1

            mask = maskAll[nl1:nl2, ns1:ns2]
            if(sum(mask) < number_value_threshold):
                result[:, k1, k2] = [-3, -3]
                continue
            mask = mask.reshape(-1)
            ind = (mask==1)

            wn = wnAll[:, nl1:nl2, ns1:ns2]
            wo = woAll[:, nl1:nl2, ns1:ns2]
            wAhi = wAhiAll[:, nl1:nl2, ns1:ns2]
            wn = np.asarray(np.reshape(wn, (number_component, -1)))
            wo = np.asarray(np.reshape(wo, (number_component, -1)))
            wAhi = np.asarray(np.reshape(wAhi, (number_component, -1)))

            radn = radnAll[nl1:nl2, ns1:ns2]
            rado = radoAll[nl1:nl2, ns1:ns2]
            radAhi = radAhiAll[nl1:nl2, ns1:ns2]

            w1 = np.asarray([wn[j, :] * windowCoef[i, :] for j in range(number_component) for i in range(6)])
            w2 = np.asarray([wo[j, :] * windowCoef[i, :] for j in range(number_component) for i in range(6)])
            radn = radn.reshape(-1)
            rado = rado.reshape(-1)

            temp1 = (np.reshape(fvcN[nl1:nl2, ns1:ns2], -1))
            temp2 = (np.reshape(fvcO[nl1:nl2, ns1:ns2], -1))
            ind = (radn < radiance_max_threshold) * (rado > radiance_min_threshold) * \
                  (temp1 > pure_soil_threshold) * (temp1 < pure_leaf_threshold) * \
                  (temp2 > pure_soil_threshold) * (temp2 < pure_leaf_threshold) * \
                  (rado < radiance_max_threshold) * (rado > radiance_min_threshold) * \
                  (np.isnan(w1[0,:]) != 1) * (np.isnan(w1[1,:]) != 1) * (np.isnan(w1[2,:]) != 1)
            num_val_point = np.sum(ind)
            if (num_val_point < number_value_threshold):
                result[:, k1, k2] = [-3, -3]
                continue

            ww = np.hstack((w1[:, ind], w2[:, ind])).transpose()
            bb = np.hstack((radn[ind], rado[ind]))
            coeffprior = np.asarray(fitting_lsct_2(ww,bb))


            ct1 = np.asarray([np.sum(coeffprior[:6] * windowCoef[:, j]) for j in range(25)])
            ct2 = np.asarray([np.sum(coeffprior[6:12] * windowCoef[:, j]) for j in range(25)])
            offcenter = int((2*off+1)*(2*off+1)/2)

            indnew = ind*(ct1 < radiance_max_threshold) * (ct1 > radiance_min_threshold)* \
                     (ct2 < radiance_max_threshold) * (ct2 > radiance_min_threshold)
            pointNum = np.sum(indnew)

            if pointNum<=1:
                offcenter = int((2*off+1)*(2*off+1)/2)
                cd1 = np.sum(coeffprior[:6] * windowCoef[:, offcenter])
                cd2 = np.sum(coeffprior[6:12] * windowCoef[:, offcenter])
                ctprior = np.transpose(np.asarray([cd1, cd2]))
            else:
                fd = np.reshape(fd0, -1) * 1.0
                fd[indnew] = fd[indnew]/np.sum(fd[indnew])
                cd1 = np.sum(ct1[indnew] * fd[indnew])
                cd2 = np.sum(ct2[indnew] * fd[indnew])
                ctprior = np.transpose(np.asarray([cd1, cd2]))
            component_temperature = inv_planck(wl, ctprior)

            if (np.min(ctprior) < radiance_min_threshold):
                result[:, k1, k2] = [-1, -1]
                continue
            if (np.max(ctprior) > radiance_max_threshold):
                result[:, k1, k2] = [-1, -1]
                continue

            result[:, k1, k2] = [component_temperature[0],
                                 component_temperature[1]]

    return result

'''计算单个点的lsct3，未利用ahi， 多像元'''
def inv_mpl_fan(lst_n, lst_o, lst_ahi, emis_s, emis_v, fvcN, fvcO, fvcAhi, pg_n, pg_o, pg_Ahi,ind_n, ind_o, ind_Ahi,wl = 10.8, off = 2):
    radiance_max_threshold = 20
    radiance_min_threshold = 4.5
    temperature_max_threshold = 350
    temperature_min_threshold = 250
    pure_soil_threshold = 0.01
    pure_leaf_threshold = 0.99

    sensor_noise = 0.5

    soil_radiance_variance = 2
    leaf_radiance_variance = 1
    default_nan_temperature = -1
    # fvc_max_threshold = 0.99
    # fvc_min_threshold = 0.01
    number_component = 3
    number_value_threshold = 12
    fd0 = np.asarray([[1, 4, 7, 4, 1], [4, 16, 26, 16, 4], [7, 26, 41, 26, 7], [4, 16, 26, 16, 4], [1, 4, 7, 4, 1]])

    [nl,ns] = np.shape(lst_n)
    result = np.zeros([4, nl, ns])

    '''有效发射率矩阵'''
    wnAll = np.asarray([emis_s*(1-fvcN)*pg_n, emis_s*(1-fvcN)*(1-pg_n), emis_v*fvcN])
    woAll = np.asarray([emis_s*(1-fvcO)*pg_o, emis_s*(1-fvcO)*(1-pg_o), emis_v*fvcO])
    wAhiAll = np.asarray([emis_s*(1-fvcAhi)*pg_Ahi, emis_s*(1-fvcAhi)*(1-pg_Ahi), emis_v*fvcAhi])

    '''辐射'''
    radnAll = planck(wl, lst_n)
    radoAll = planck(wl, lst_o)
    radAhiAll = planck(wl, lst_ahi)

    '''标记可用点，可用为1'''
    maskAll = np.zeros([nl,ns])
    indAll = (lst_n > temperature_min_threshold) * (lst_n < temperature_max_threshold)* \
          (lst_o > temperature_min_threshold) * (lst_o < temperature_max_threshold) * \
          (lst_ahi > temperature_min_threshold) * (lst_ahi < temperature_max_threshold) *\
          (fvcN > pure_soil_threshold) * (fvcN < pure_leaf_threshold)* \
          (ind_n == 1) * (ind_o==1) * (ind_Ahi==1)
    maskAll[indAll] = 1

    '''形成坐标系数， 6*25， 5*5的框'''
    windowX = np.asarray(np.repeat([-2, -1, 0, 1, 2], 5)).reshape(5, -1).transpose().reshape(-1)
    windowY = np.asarray(np.repeat([2, 1, 0, -1, -2], 5))
    coef0 = np.ones([5, 5]).reshape(-1)
    windowCoef = np.asarray([coef0, windowX, windowY, windowX * windowY, windowX * windowX, windowY * windowY])

    '''5*5的框循环'''
    for k1 in range(off, nl-off):
        for k2 in range(off, ns-off):
            if(maskAll[k1, k2] != 1): continue

            '''多像元计算   6*N 个系数'''
            nl1 = k1 - off
            nl2 = k1 + off + 1
            ns1 = k2 - off
            ns2 = k2 + off + 1

            mask = maskAll[nl1:nl2, ns1:ns2]
            if(sum(mask) < number_value_threshold):
                result[:, k1, k2] = [-3, -3, -3, -3]
                continue
            mask = mask.reshape(-1)
            ind = (mask==1)

            wn = wnAll[:, nl1:nl2, ns1:ns2]
            wo = woAll[:, nl1:nl2, ns1:ns2]
            wAhi = wAhiAll[:, nl1:nl2, ns1:ns2]
            wn = np.asarray(np.reshape(wn, (number_component, -1)))
            wo = np.asarray(np.reshape(wo, (number_component, -1)))
            wAhi = np.asarray(np.reshape(wAhi, (number_component, -1)))

            radn = radnAll[nl1:nl2, ns1:ns2]
            rado = radoAll[nl1:nl2, ns1:ns2]
            radAhi = radAhiAll[nl1:nl2, ns1:ns2]

            w1 = np.asarray([wn[j, :] * windowCoef[i, :] for j in range(number_component) for i in range(6)])
            w2 = np.asarray([wo[j, :] * windowCoef[i, :] for j in range(number_component) for i in range(6)])
            radn = radn.reshape(-1)
            rado = rado.reshape(-1)

            temp1 = (np.reshape(fvcN[nl1:nl2, ns1:ns2], -1))
            temp2 = (np.reshape(fvcO[nl1:nl2, ns1:ns2], -1))
            ind = (radn < radiance_max_threshold) * (rado > radiance_min_threshold) * \
                  (temp1 > pure_soil_threshold) * (temp1 < pure_leaf_threshold) * \
                  (temp2 > pure_soil_threshold) * (temp2 < pure_leaf_threshold) * \
                  (rado < radiance_max_threshold) * (rado > radiance_min_threshold) * \
                  (np.isnan(w1[0,:]) != 1) * (np.isnan(w1[1,:]) != 1) * (np.isnan(w1[2,:]) != 1)
            num_val_point = np.sum(ind)
            if (num_val_point < number_value_threshold):
                result[:, k1, k2] = [-3, -3, -3, -3]
                continue

            ww = np.hstack((w1[:, ind], w2[:, ind])).transpose()
            bb = np.hstack((radn[ind], rado[ind]))
            coeffprior = np.asarray(fitting_lsct(ww,bb))


            ct1 = np.asarray([np.sum(coeffprior[:6] * windowCoef[:, j]) for j in range(25)])
            ct2 = np.asarray([np.sum(coeffprior[6:12] * windowCoef[:, j]) for j in range(25)])
            ct3 = np.asarray([np.sum(coeffprior[12:] * windowCoef[:, j]) for j in range(25)])
            offcenter = int((2*off+1)*(2*off+1)/2)
            # cd1 = np.sum(coeffprior[:6] * windowCoef[:, offcenter])
            # cd2 = np.sum(coeffprior[6:12] * windowCoef[:, offcenter])
            # cd3 = np.sum(coeffprior[12:] * windowCoef[:, offcenter])
            # ctprior = np.transpose(np.asarray([cd1, cd2, cd3]))

            indnew = ind*(ct1 < radiance_max_threshold) * (ct1 > radiance_min_threshold)* \
                     (ct2 < radiance_max_threshold) * (ct2 > radiance_min_threshold)* \
                     (ct3 < radiance_max_threshold) * (ct3 > radiance_min_threshold)
            pointNum = np.sum(indnew)

            if pointNum<=1:
                offcenter = int((2*off+1)*(2*off+1)/2)
                cd1 = np.sum(coeffprior[:6] * windowCoef[:, offcenter])
                cd2 = np.sum(coeffprior[6:12] * windowCoef[:, offcenter])
                cd3 = np.sum(coeffprior[12:] * windowCoef[:, offcenter])
                ctprior = np.transpose(np.asarray([cd1, cd2, cd3]))
            else:
                fd = np.reshape(fd0, -1) * 1.0
                fd[indnew] = fd[indnew]/np.sum(fd[indnew])
                cd1 = np.sum(ct1[indnew] * fd[indnew])
                cd2 = np.sum(ct2[indnew] * fd[indnew])
                cd3 = np.sum(ct3[indnew] * fd[indnew])
                ctprior = np.transpose(np.asarray([cd1, cd2, cd3]))
            component_temperature = inv_planck(wl, ctprior)

            if (np.min(ctprior) < radiance_min_threshold):
                result[:, k1, k2] = [-1, -1, -1, -1]
                continue
            if (np.max(ctprior) > radiance_max_threshold):
                result[:, k1, k2] = [-1, -1, -1, -1]
                continue

            rad_soil = pg_n[k1, k2] * ctprior[0] + (1 - pg_n[k1, k2]) * ctprior[1]
            temperature_soil = inv_planck(wl, rad_soil)

            result[:, k1, k2] = [temperature_soil, component_temperature[2], component_temperature[0],
                                 component_temperature[1]]

        # result[result < temperature_min_threshold] = default_nan_temperature
        # result[result > temperature_max_threshold] = default_nan_temperature

    return result

'''计算单个点的lsct3，利用ahi, 多角度'''
def inv_agl_ahi_fan(lst_n, lst_o, lst_ahi, emis_s, emis_v, fvcN, fvcO, fvcAhi, pg_n, pg_o, pg_Ahi,ind_n, ind_o, ind_Ahi,wl = 10.8, off = 2):
    radiance_max_threshold = 20
    radiance_min_threshold = 4.5
    temperature_max_threshold = 350
    temperature_min_threshold = 250
    pure_soil_threshold = 0.01
    pure_leaf_threshold = 0.99

    sensor_noise = 0.5

    soil_radiance_variance = 2
    leaf_radiance_variance = 1
    default_nan_temperature = -1
    # fvc_max_threshold = 0.99
    # fvc_min_threshold = 0.01
    number_component = 3
    number_value_threshold = 12
    fd0 = np.asarray([[1, 4, 7, 4, 1], [4, 16, 26, 16, 4], [7, 26, 41, 26, 7], [4, 16, 26, 16, 4], [1, 4, 7, 4, 1]])

    [nl,ns] = np.shape(lst_n)
    result = np.zeros([4, nl, ns])

    '''有效发射率矩阵'''
    wnAll = np.asarray([emis_s*(1-fvcN)*pg_n, emis_s*(1-fvcN)*(1-pg_n), emis_v*fvcN])
    woAll = np.asarray([emis_s*(1-fvcO)*pg_o, emis_s*(1-fvcO)*(1-pg_o), emis_v*fvcO])
    wAhiAll = np.asarray([emis_s*(1-fvcAhi)*pg_Ahi, emis_s*(1-fvcAhi)*(1-pg_Ahi), emis_v*fvcAhi])

    '''辐射'''
    radnAll = planck(wl, lst_n)
    radoAll = planck(wl, lst_o)
    radAhiAll = planck(wl, lst_ahi)

    '''标记可用点，可用为1'''
    maskAll = np.zeros([nl,ns])
    indAll = (lst_n > temperature_min_threshold) * (lst_n < temperature_max_threshold)* \
          (lst_o > temperature_min_threshold) * (lst_o < temperature_max_threshold) * \
          (lst_ahi > temperature_min_threshold) * (lst_ahi < temperature_max_threshold) *\
          (fvcN > pure_soil_threshold) * (fvcN < pure_leaf_threshold)* \
          (ind_n == 1) * (ind_o==1) * (ind_Ahi==1)
    maskAll[indAll] = 1

    '''形成坐标系数， 6*25， 5*5的框'''
    windowX = np.asarray(np.repeat([-2, -1, 0, 1, 2], 5)).reshape(5, -1).transpose().reshape(-1)
    windowY = np.asarray(np.repeat([2, 1, 0, -1, -2], 5))
    coef0 = np.ones([5, 5]).reshape(-1)
    windowCoef = np.asarray([coef0, windowX, windowY, windowX * windowY, windowX * windowX, windowY * windowY])

    '''5*5的框循环'''
    for k1 in range(off, nl-off):
        for k2 in range(off, ns-off):
            if(maskAll[k1, k2] != 1): continue

            '''多角度计算'''
            wn_2 = wnAll[:, k1, k2]
            wo_2 = woAll[:, k1, k2]
            wAhi_2 = wAhiAll[:, k1, k2]

            if (len(wn_2[np.isnan(wn_2)]) > 0):
                result[:, k1, k2] = [-2, -2, -2, -2]
                continue
            if (len(wo_2[np.isnan(wo_2)]) > 0):
                result[:, k1, k2] = [-2, -2, -2, -2]
                continue

            wn_2 = np.asarray(np.reshape(wn_2, (number_component, -1)))
            wo_2 = np.asarray(np.reshape(wo_2, (number_component, -1)))
            wAhi_2 = np.asarray(np.reshape(wAhi_2, (number_component, -1)))

            radn_2 = radnAll[k1, k2]
            rado_2 = radoAll[k1, k2]
            radAhi_2 = radAhiAll[k1, k2]

            ww_2 = np.hstack((wn_2, wo_2, wAhi_2)).transpose()
            bb_2 = np.hstack((radn_2, rado_2, radAhi_2)).transpose()
            coeffprior_2 = np.asarray(lstsq(ww_2, bb_2))[0]

            ### another solution for using priori information
            # coeff = ctprior + np.transpose(Cd * np.transpose(w) * pre) * (b - np.transpose(w) * ctprior)
            component_radiance = coeffprior_2

            if (np.min(component_radiance) < radiance_min_threshold):
                result[:, k1, k2] = [-1, -1, -1, -1]
                continue
            if (np.max(component_radiance) > radiance_max_threshold):
                result[:, k1, k2] = [-1, -1, -1, -1]
                continue
            component_temperature = inv_planck(wl, component_radiance)
            rad_soil = pg_n[k1, k2] * component_radiance[0] + (1 - pg_n[k1, k2]) * component_radiance[1]
            temperature_soil = inv_planck(wl, rad_soil)

            result[:, k1, k2] = [temperature_soil, component_temperature[2], component_temperature[0],
                                 component_temperature[1]]

    return result

'''计算单个点的lsct3，未利用ahi, 多角度'''
def inv_agl_fan(lst_n, lst_o, lst_ahi, emis_s, emis_v, fvcN, fvcO, fvcAhi, pg_n, pg_o, pg_Ahi,ind_n, ind_o, ind_Ahi,wl = 10.8, off = 2):
    radiance_max_threshold = 20
    radiance_min_threshold = 4.5
    temperature_max_threshold = 350
    temperature_min_threshold = 250
    pure_soil_threshold = 0.01
    pure_leaf_threshold = 0.99

    sensor_noise = 0.5

    soil_radiance_variance = 2
    leaf_radiance_variance = 1
    default_nan_temperature = -1
    # fvc_max_threshold = 0.99
    # fvc_min_threshold = 0.01
    number_component = 3
    number_value_threshold = 12
    fd0 = np.asarray([[1, 4, 7, 4, 1], [4, 16, 26, 16, 4], [7, 26, 41, 26, 7], [4, 16, 26, 16, 4], [1, 4, 7, 4, 1]])

    [nl,ns] = np.shape(lst_n)
    result = np.zeros([4, nl, ns])

    '''有效发射率矩阵'''
    wnAll = np.asarray([emis_s*(1-fvcN)*pg_n, emis_s*(1-fvcN)*(1-pg_n), emis_v*fvcN])
    woAll = np.asarray([emis_s*(1-fvcO)*pg_o, emis_s*(1-fvcO)*(1-pg_o), emis_v*fvcO])
    wAhiAll = np.asarray([emis_s*(1-fvcAhi)*pg_Ahi, emis_s*(1-fvcAhi)*(1-pg_Ahi), emis_v*fvcAhi])

    '''辐射'''
    radnAll = planck(wl, lst_n)
    radoAll = planck(wl, lst_o)
    radAhiAll = planck(wl, lst_ahi)

    '''标记可用点，可用为1'''
    maskAll = np.zeros([nl,ns])
    indAll = (lst_n > temperature_min_threshold) * (lst_n < temperature_max_threshold)* \
          (lst_o > temperature_min_threshold) * (lst_o < temperature_max_threshold) * \
          (lst_ahi > temperature_min_threshold) * (lst_ahi < temperature_max_threshold) *\
          (fvcN > pure_soil_threshold) * (fvcN < pure_leaf_threshold)* \
          (ind_n == 1) * (ind_o==1) * (ind_Ahi==1)
    maskAll[indAll] = 1

    '''形成坐标系数， 6*25， 5*5的框'''
    windowX = np.asarray(np.repeat([-2, -1, 0, 1, 2], 5)).reshape(5, -1).transpose().reshape(-1)
    windowY = np.asarray(np.repeat([2, 1, 0, -1, -2], 5))
    coef0 = np.ones([5, 5]).reshape(-1)
    windowCoef = np.asarray([coef0, windowX, windowY, windowX * windowY, windowX * windowX, windowY * windowY])

    '''5*5的框循环'''
    for k1 in range(off, nl-off):
        for k2 in range(off, ns-off):
            if(maskAll[k1, k2] != 1): continue

            '''多角度计算'''
            wn_2 = wnAll[:, k1, k2]
            wo_2 = woAll[:, k1, k2]
            wAhi_2 = wAhiAll[:, k1, k2]

            if (len(wn_2[np.isnan(wn_2)]) > 0):
                result[:, k1, k2] = [-2, -2, -2, -2]
                continue
            if (len(wo_2[np.isnan(wo_2)]) > 0):
                result[:, k1, k2] = [-2, -2, -2, -2]
                continue

            wn_2 = np.asarray(np.reshape(wn_2, (number_component, -1)))
            wo_2 = np.asarray(np.reshape(wo_2, (number_component, -1)))
            wAhi_2 = np.asarray(np.reshape(wAhi_2, (number_component, -1)))

            radn_2 = radnAll[k1, k2]
            rado_2 = radoAll[k1, k2]
            radAhi_2 = radAhiAll[k1, k2]

            ww_2 = np.hstack((wn_2, wo_2)).transpose()
            bb_2 = np.hstack((radn_2, rado_2)).transpose()
            coeffprior_2 = np.asarray(lstsq(ww_2, bb_2))[0]

            ### another solution for using priori information
            # coeff = ctprior + np.transpose(Cd * np.transpose(w) * pre) * (b - np.transpose(w) * ctprior)
            component_radiance = coeffprior_2

            if (np.min(component_radiance) < radiance_min_threshold):
                result[:, k1, k2] = [-1, -1, -1, -1]
                continue
            if (np.max(component_radiance) > radiance_max_threshold):
                result[:, k1, k2] = [-1, -1, -1, -1]
                continue
            component_temperature = inv_planck(wl, component_radiance)
            rad_soil = pg_n[k1, k2] * component_radiance[0] + (1 - pg_n[k1, k2]) * component_radiance[1]
            temperature_soil = inv_planck(wl, rad_soil)

            result[:, k1, k2] = [temperature_soil, component_temperature[2], component_temperature[0],
                                 component_temperature[1]]

    return result

'''计算单个点的lsct2,利用ahi, 多角度'''
def inv_agl_ahi_fan_2(lst_n, lst_o, lst_ahi, emis_s, emis_v, fvcN, fvcO, fvcAhi, pg_n, pg_o, pg_Ahi,ind_n, ind_o, ind_Ahi,wl = 10.8, off = 2):
    radiance_max_threshold = 20
    radiance_min_threshold = 4.5
    temperature_max_threshold = 350
    temperature_min_threshold = 250
    pure_soil_threshold = 0.01
    pure_leaf_threshold = 0.99

    sensor_noise = 0.5

    soil_radiance_variance = 2
    leaf_radiance_variance = 1
    default_nan_temperature = -1
    # fvc_max_threshold = 0.99
    # fvc_min_threshold = 0.01
    number_component = 2
    number_value_threshold = 12
    fd0 = np.asarray([[1, 4, 7, 4, 1], [4, 16, 26, 16, 4], [7, 26, 41, 26, 7], [4, 16, 26, 16, 4], [1, 4, 7, 4, 1]])

    [nl,ns] = np.shape(lst_n)
    result = np.zeros([number_component, nl, ns])

    '''有效发射率矩阵'''
    wnAll = np.asarray([emis_s*(1-fvcN), emis_v*fvcN])
    woAll = np.asarray([emis_s*(1-fvcO), emis_v*fvcO])
    wAhiAll = np.asarray([emis_s*(1-fvcAhi), emis_v*fvcAhi])

    '''辐射'''
    radnAll = planck(wl, lst_n)
    radoAll = planck(wl, lst_o)
    radAhiAll = planck(wl, lst_ahi)

    '''标记可用点，可用为1'''
    maskAll = np.zeros([nl,ns])
    indAll = (lst_n > temperature_min_threshold) * (lst_n < temperature_max_threshold)* \
          (lst_o > temperature_min_threshold) * (lst_o < temperature_max_threshold) * \
          (lst_ahi > temperature_min_threshold) * (lst_ahi < temperature_max_threshold) *\
          (fvcN > pure_soil_threshold) * (fvcN < pure_leaf_threshold)* \
          (ind_n == 1) * (ind_o==1) * (ind_Ahi==1)
    maskAll[indAll] = 1

    '''形成坐标系数， 6*25， 5*5的框'''
    windowX = np.asarray(np.repeat([-2, -1, 0, 1, 2], 5)).reshape(5, -1).transpose().reshape(-1)
    windowY = np.asarray(np.repeat([2, 1, 0, -1, -2], 5))
    coef0 = np.ones([5, 5]).reshape(-1)
    windowCoef = np.asarray([coef0, windowX, windowY, windowX * windowY, windowX * windowX, windowY * windowY])

    '''5*5的框循环'''
    for k1 in range(off, nl-off):
        for k2 in range(off, ns-off):
            if(maskAll[k1, k2] != 1): continue

            '''多角度计算'''
            wn_2 = wnAll[:, k1, k2]
            wo_2 = woAll[:, k1, k2]
            wAhi_2 = wAhiAll[:, k1, k2]

            if (len(wn_2[np.isnan(wn_2)]) > 0):
                result[:, k1, k2] = [-2, -2]
                continue
            if (len(wo_2[np.isnan(wo_2)]) > 0):
                result[:, k1, k2] = [-2, -2]
                continue

            wn_2 = np.asarray(np.reshape(wn_2, (number_component, -1)))
            wo_2 = np.asarray(np.reshape(wo_2, (number_component, -1)))
            wAhi_2 = np.asarray(np.reshape(wAhi_2, (number_component, -1)))

            radn_2 = radnAll[k1, k2]
            rado_2 = radoAll[k1, k2]
            radAhi_2 = radAhiAll[k1, k2]

            ww_2 = np.hstack((wn_2, wo_2, wAhi_2)).transpose()
            bb_2 = np.hstack((radn_2, rado_2, radAhi_2)).transpose()
            coeffprior_2 = np.asarray(lstsq(ww_2, bb_2))[0]

            component_radiance = coeffprior_2

            if (np.min(component_radiance) < radiance_min_threshold):
                result[:, k1, k2] = [-1, -1]
                continue
            if (np.max(component_radiance) > radiance_max_threshold):
                result[:, k1, k2] = [-1, -1]
                continue
            component_temperature = inv_planck(wl, component_radiance)
            # rad_soil = pg_n[k1, k2] * component_radiance[0] + (1 - pg_n[k1, k2]) * component_radiance[1]
            # temperature_soil = inv_planck(wl, rad_soil)

            result[:, k1, k2] = [component_temperature[0],
                                 component_temperature[1]]

        # result[result < temperature_min_threshold] = default_nan_temperature
        # result[result > temperature_max_threshold] = default_nan_temperature

    return result

'''计算单个点的lsct2,未利用ahi, 多角度'''
def inv_agl_fan_2(lst_n, lst_o, lst_ahi, emis_s, emis_v, fvcN, fvcO, fvcAhi, pg_n, pg_o, pg_Ahi,ind_n, ind_o, ind_Ahi,wl = 10.8, off = 2):
    radiance_max_threshold = 20
    radiance_min_threshold = 4.5
    temperature_max_threshold = 350
    temperature_min_threshold = 250
    pure_soil_threshold = 0.01
    pure_leaf_threshold = 0.99

    sensor_noise = 0.5

    soil_radiance_variance = 2
    leaf_radiance_variance = 1
    default_nan_temperature = -1
    # fvc_max_threshold = 0.99
    # fvc_min_threshold = 0.01
    number_component = 2
    number_value_threshold = 12
    fd0 = np.asarray([[1, 4, 7, 4, 1], [4, 16, 26, 16, 4], [7, 26, 41, 26, 7], [4, 16, 26, 16, 4], [1, 4, 7, 4, 1]])

    [nl,ns] = np.shape(lst_n)
    result = np.zeros([number_component, nl, ns])

    '''有效发射率矩阵'''
    wnAll = np.asarray([emis_s*(1-fvcN), emis_v*fvcN])
    woAll = np.asarray([emis_s*(1-fvcO), emis_v*fvcO])
    wAhiAll = np.asarray([emis_s*(1-fvcAhi), emis_v*fvcAhi])

    '''辐射'''
    radnAll = planck(wl, lst_n)
    radoAll = planck(wl, lst_o)
    radAhiAll = planck(wl, lst_ahi)

    '''标记可用点，可用为1'''
    maskAll = np.zeros([nl,ns])
    indAll = (lst_n > temperature_min_threshold) * (lst_n < temperature_max_threshold)* \
          (lst_o > temperature_min_threshold) * (lst_o < temperature_max_threshold) * \
          (lst_ahi > temperature_min_threshold) * (lst_ahi < temperature_max_threshold) *\
          (fvcN > pure_soil_threshold) * (fvcN < pure_leaf_threshold)* \
          (ind_n == 1) * (ind_o==1) * (ind_Ahi==1)
    maskAll[indAll] = 1

    '''形成坐标系数， 6*25， 5*5的框'''
    windowX = np.asarray(np.repeat([-2, -1, 0, 1, 2], 5)).reshape(5, -1).transpose().reshape(-1)
    windowY = np.asarray(np.repeat([2, 1, 0, -1, -2], 5))
    coef0 = np.ones([5, 5]).reshape(-1)
    windowCoef = np.asarray([coef0, windowX, windowY, windowX * windowY, windowX * windowX, windowY * windowY])

    '''5*5的框循环'''
    for k1 in range(off, nl-off):
        for k2 in range(off, ns-off):
            if(maskAll[k1, k2] != 1): continue

            '''多角度计算'''
            wn_2 = wnAll[:, k1, k2]
            wo_2 = woAll[:, k1, k2]
            wAhi_2 = wAhiAll[:, k1, k2]

            if (len(wn_2[np.isnan(wn_2)]) > 0):
                result[:, k1, k2] = [-2, -2]
                continue
            if (len(wo_2[np.isnan(wo_2)]) > 0):
                result[:, k1, k2] = [-2, -2]
                continue

            wn_2 = np.asarray(np.reshape(wn_2, (number_component, -1)))
            wo_2 = np.asarray(np.reshape(wo_2, (number_component, -1)))
            wAhi_2 = np.asarray(np.reshape(wAhi_2, (number_component, -1)))

            radn_2 = radnAll[k1, k2]
            rado_2 = radoAll[k1, k2]
            radAhi_2 = radAhiAll[k1, k2]

            ww_2 = np.hstack((wn_2, wo_2)).transpose()
            bb_2 = np.hstack((radn_2, rado_2)).transpose()
            coeffprior_2 = np.asarray(lstsq(ww_2, bb_2))[0]

            component_radiance = coeffprior_2

            if (np.min(component_radiance) < radiance_min_threshold):
                result[:, k1, k2] = [-1, -1]
                continue
            if (np.max(component_radiance) > radiance_max_threshold):
                result[:, k1, k2] = [-1, -1]
                continue
            component_temperature = inv_planck(wl, component_radiance)
            # rad_soil = pg_n[k1, k2] * component_radiance[0] + (1 - pg_n[k1, k2]) * component_radiance[1]
            # temperature_soil = inv_planck(wl, rad_soil)

            result[:, k1, k2] = [component_temperature[0],
                                 component_temperature[1]]

        # result[result < temperature_min_threshold] = default_nan_temperature
        # result[result > temperature_max_threshold] = default_nan_temperature

    return result





def inv_process(bb,ww,b,w,x,ind,wl=10.8):
 #   return 1
    part = 6
    radiance_max_threshold = 17
    radiance_min_threshold = 6.5
    temperature_max_threshold = 350
    temperature_min_threshold = 250
    default_nan_temperature = 0
    soil_radiance_variance = 2
    leaf_radiance_variance = 1
    sensor_noise = 0.05
    pure_soil_threshold = 0.05
    pure_leaf_threshold = 0.95
    fvc_max_threshold = 0.99
    fvc_min_threshold = 0.01
    number_component = 2
    fd0 = np.asarray([[1, 4, 7, 4, 1], [4, 16, 26, 16, 4], [7, 26, 41, 26, 7], [4, 16, 26, 16, 4], [1, 4, 7, 4, 1]])
    number_angle = 2
    off = 2
    off_ = 1
    number_value_threshold = 12
    offcenter = np.int(((2 * off + 1) * (2 * off + 1) - 1) / 2)

    fd = fd0
    fd = np.reshape(fd, -1) * 1.0


    ###############################################
    ### least-square method
    ###############################################
    ww = np.transpose(ww)
    coeffprior = np.asarray(lstsq(ww, bb,rcond=None))[0]
    # cd1 = np.sum(coeffprior[:6] * x[:, offcenter])
    # cd2 = np.sum(coeffprior[6:] * x[:, offcenter])
    # ctprior = np.transpose(np.matrix([cd1, cd2]))

    ###############################################
    ### Bayes method with priori information
    ###############################################
    # bbb = sorted(b)
    # halfpoint = np.int(num_point / 2)
    # rleaf = np.average(bbb[0])
    # rsoil = np.average(bbb[1])
    # coeffprior = np.transpose(np.matrix([rsoil, 0, 0, 0, 0, 0, rleaf, 0, 0, 0, 0, 0]))
    # bb = np.transpose(np.matrix(bb))
    # ww = np.transpose(ww)
    # Cd = np.matrix(np.diag(np.ones(num_point * 2)) * Cdvaluep)
    # Cm = np.matrix(np.diag(np.ones(2 * part)))
    # Cm[0, 0] = 15.0
    # Cm[part, part] = 10.0
    # pre = np.linalg.inv(np.transpose(ww) * np.linalg.inv(Cd) * ww + np.linalg.inv(Cm))
    # ctprior = pre * (np.transpose(ww) * np.linalg.inv(Cd) * bb + np.linalg.inv(Cm) * coeffprior)

    #################################################
    ### first result without averaging information
    #################################################
    # cd1 = np.sum(coeffprior[:6] * x[:, offcenter])
    # cd2 = np.sum(coeffprior[6:] * x[:, offcenter])
    # ctprior = np.transpose(np.matrix([cd1, cd2]))

    ################################################
    ### first reult with averaing information
    ################################################
    coeffprior = np.asarray(coeffprior)
    ct1 = np.asarray([np.sum(coeffprior[:part] * x[:part, j]) for j in range(25)])
    ct2 = np.asarray([np.sum(coeffprior[part:2 * part] * x[:part, j]) for j in range(25)])

    indnew = ind * (ct2 < radiance_max_threshold) * (ct2 > radiance_min_threshold) * \
             (ct1 > radiance_min_threshold) * (ct1 < radiance_max_threshold)
    apoint = np.sum(indnew)
    if (apoint <= 1):
        cd1 = np.sum(coeffprior[:part] * x[:, offcenter])
        cd2 = np.sum(coeffprior[part:] * x[:, offcenter])
        ctprior = np.transpose(np.matrix([cd1, cd2]))
    else:
        fd[indnew] = fd[indnew] / np.sum(fd[indnew])

        # inver-distance weight but not used
        # bb0 = bb1[offcenter]
        # fdnew = np.zeros(25)
        # dismax = max(abs(bb1[indnew] - bb0))
        # if dismax != 0:
        #     fdnew[indnew] = 1.0 - abs(1.0 * bb1[indnew] - bb0) / dismax
        # else:
        #     fdnew[:] = 1
        # fdnew[indnew] = fdnew[indnew] / np.sum(fdnew[indnew])
        # fd[indnew] = (fdnew[indnew] * fd[indnew]) / np.sum(fdnew[indnew] * fd[indnew])

        cd1new = np.sum(ct1[indnew] * fd[indnew])
        cd2new = np.sum(ct2[indnew] * fd[indnew])
        ctprior = np.transpose(np.matrix([cd1new, cd2new]))

    #################################################
    ### second result by combining one-point result
    #################################################


    #################################################
    ### least-squared method
    #################################################
    # coeffprior = np.asarray(lstsq(w, b))[0]

    #################################################
    ### Bayes method
    #################################################

    w = np.matrix(w)
    b = np.matrix(b)
    b = np.transpose(b)

    Cd = np.matrix(np.diag(np.ones(number_component)) * sensor_noise)
    Cm = np.diag([soil_radiance_variance, leaf_radiance_variance])
    pre = np.linalg.inv(np.transpose(w) * np.linalg.inv(Cd) * w + np.linalg.inv(Cm))
    coeff = pre * (np.transpose(w) * np.linalg.inv(Cd) * b + np.linalg.inv(Cm) * ctprior)
    ### another solution for using priori information
    # coeff = ctprior + np.transpose(Cd * np.transpose(w) * pre) * (b - np.transpose(w) * ctprior)
    component_radiance = np.asarray(coeff)

    if (np.min(component_radiance) < radiance_min_threshold): return [0,0]
    if (np.max(component_radiance) > radiance_max_threshold): return [0,0]

    component_temperature = inv_planck(wl, component_radiance)

    result = [component_temperature[0], component_temperature[1]]

    return result

'''多线程三组分温度反演程序：共三个'''
######分行计算的三组分温度结果，为多线程内部函数调用
def line_inv(wNLine, wOLine, wALine, radNLine, radOLine, radAhiLine, maskLine,ns = 1024):
    wl = 10.8
    off_ = 0
    radiance_max_threshold = 20
    radiance_min_threshold = 4.5
    temperature_max_threshold = 350
    temperature_min_threshold = 250
    default_nan_temperature = 0
    soil_radiance_variance = 2
    leaf_radiance_variance = 1
    sensor_noise = 0.05
    pure_soil_threshold = 0.05
    pure_leaf_threshold = 0.95
    fvc_max_threshold = 0.99
    fvc_min_threshold = 0.01
    number_component = 3
    number_angle = 2
    number_value_threshold = 12

    result = np.zeros([3,ns])

    ###
    off = 2
    for kk in range(off, ns-off):


        maskk = maskLine[2,kk]
        if maskk == 0: continue

        ns1 = kk - off
        ns2 = kk + off + 1

        w1 = wNLine[:,:, ns1:ns2]
        w1 = np.asarray(np.reshape(w1, (number_component, -1)))
        w2 = wOLine[:,:, ns1:ns2]
        w2 = np.asarray(np.reshape(w2, (number_component, -1)))

        bb1 = (np.reshape(radNLine[:, ns1:ns2], -1))
        bb2 = (np.reshape(radOLine[:, ns1:ns2], -1))



        mask = np.reshape(maskLine[:, ns1:ns2],-1)
        ind = (mask==1) * (np.isnan(w1[0,:])==0)

        num_val_point = np.sum(ind)
        if (num_val_point < number_value_threshold): continue

        ### w1 for nadir and w2 for oblique
        ns_temp = np.asarray([-2, -1, 0, 1, 2, -2, -1, 0, 1, 2, -2, -1, 0, 1, 2, -2, -1, 0, 1, 2, -2, -1, 0, 1, 2])
        nl_temp = np.asarray(np.repeat([-2, -1, 0, 1, 2], 5))
        part = 6

        n0 = np.ones(len(ns_temp))
        x = np.asarray([n0, ns_temp, nl_temp, ns_temp * nl_temp, ns_temp * ns_temp, nl_temp * nl_temp])
        w11 = np.asarray([w1[j, :] * x[i, :] for j in range(number_component) for i in range(part)])
        w22 = np.asarray([w2[j, :] * x[i, :] for j in range(number_component) for i in range(part)])

        ww = np.hstack((w11[:, ind], w22[:, ind]))
        bb = np.hstack((bb1[ind], bb2[ind]))

        ###############################################
        ### least-square method
        ###############################################
        ww = np.transpose(ww)
        # print(kk)
        coeffprior = np.asarray(lstsq(ww, bb, rcond=None))[0]
        # cd1 = np.sum(coeffprior[:6] * x[:, offcenter])
        # cd2 = np.sum(coeffprior[6:] * x[:, offcenter])
        # ctprior = np.transpose(np.matrix([cd1, cd2]))

        ###############################################
        ### Bayes method with priori information
        ###############################################
        # bbb = sorted(b)
        # halfpoint = np.int(num_point / 2)
        # rleaf = np.average(bbb[0])
        # rsoil = np.average(bbb[1])
        # coeffprior = np.transpose(np.matrix([rsoil, 0, 0, 0, 0, 0, rleaf, 0, 0, 0, 0, 0]))
        # bb = np.transpose(np.matrix(bb))
        # ww = np.transpose(ww)
        # Cd = np.matrix(np.diag(np.ones(num_point * 2)) * Cdvaluep)
        # Cm = np.matrix(np.diag(np.ones(2 * part)))
        # Cm[0, 0] = 15.0
        # Cm[part, part] = 10.0
        # pre = np.linalg.inv(np.transpose(ww) * np.linalg.inv(Cd) * ww + np.linalg.inv(Cm))
        # ctprior = pre * (np.transpose(ww) * np.linalg.inv(Cd) * bb + np.linalg.inv(Cm) * coeffprior)

        #################################################
        ### first result without averaging information
        #################################################
        # cd1 = np.sum(coeffprior[:6] * x[:, offcenter])
        # cd2 = np.sum(coeffprior[6:] * x[:, offcenter])
        # ctprior = np.transpose(np.matrix([cd1, cd2]))

        ################################################
        ### first reult with averaing information
        ################################################
        offcenter = np.int(((2 * off + 1) * (2 * off + 1) - 1) / 2)
        fd = np.asarray([[1, 4, 7, 4, 1], [4, 16, 26, 16, 4], [7, 26, 41, 26, 7], [4, 16, 26, 16, 4], [1, 4, 7, 4, 1]])
        fd = np.reshape(fd, -1) * 1.0

        coeffprior = np.asarray(coeffprior)
        ct1 = np.asarray([np.sum(coeffprior[:part] * x[:part, j]) for j in range(25)])
        ct2 = np.asarray([np.sum(coeffprior[part:2 * part] * x[:part, j]) for j in range(25)])
        ct3 = np.asarray([np.sum(coeffprior[2 * part:3 * part] * x[:part, j]) for j in range(25)])
        indnew = ind * (ct2 < radiance_max_threshold) * (ct2 > radiance_min_threshold) * \
                 (ct1 > radiance_min_threshold) * (ct1 < radiance_max_threshold) * \
                 (ct3 > radiance_min_threshold) * (ct3 < radiance_max_threshold)
        apoint = np.sum(indnew)
        if (apoint <= 1):
            cd1 = np.sum(coeffprior[:part] * x[:, offcenter])
            cd2 = np.sum(coeffprior[part:2 * part] * x[:, offcenter])
            cd3 = np.sum(coeffprior[2 * part:3 * part] * x[:, offcenter])
            ctprior = np.transpose(np.matrix([cd1, cd2, cd3]))
        else:
            fd[indnew] = fd[indnew] / np.sum(fd[indnew])

            # inver-distance weight but not used
            # bb0 = bb1[offcenter]
            # fdnew = np.zeros(25)
            # dismax = max(abs(bb1[indnew] - bb0))
            # if dismax != 0:
            #     fdnew[indnew] = 1.0 - abs(1.0 * bb1[indnew] - bb0) / dismax
            # else:
            #     fdnew[:] = 1
            # fdnew[indnew] = fdnew[indnew] / np.sum(fdnew[indnew])
            # fd[indnew] = (fdnew[indnew] * fd[indnew]) / np.sum(fdnew[indnew] * fd[indnew])

            cd1new = np.sum(ct1[indnew] * fd[indnew])
            cd2new = np.sum(ct2[indnew] * fd[indnew])
            cd3new = np.sum(ct3[indnew] * fd[indnew])
            ctprior = np.transpose(np.matrix([cd1new, cd2new, cd3new]))
        component_temperature = inv_planck(wl, ctprior)
        #################################################
        ### second result by combining one-point result
        #################################################

        ns1 = kk - off_
        ns2 = kk + off_ + 1
        # k22 = np.uint16(kk / 2)
        w1 = wNLine[:, 2, ns1:ns2]
        w1 = np.asarray(np.reshape(w1, (number_component, -1)))
        w2 = wOLine[:,2, ns1:ns2]
        w2 = np.asarray(np.reshape(w2, (number_component, -1)))
        w3 = wALine[:,2, ns1:ns2]
        w3 = np.asarray(np.reshape(w3, (number_component, -1)))

        b1 = np.reshape(radNLine[2, ns1:ns2], -1)
        b2 = np.reshape(radOLine[2, ns1:ns2], -1)
        b3 = np.reshape(radAhiLine[2, ns1:ns2], -1)
        w = np.hstack((w1, w2, w3))
        b = np.hstack((b1, b2, b3))
        w = np.transpose(w)

        #################################################
        ### least-squared method
        #################################################
        # coeffprior = np.asarray(lstsq(w, b))[0]

        #################################################
        ### Bayes method
        #################################################

        w = np.matrix(w)
        b = np.matrix(b)
        b = np.transpose(b)


        Cd = np.matrix(np.diag(np.ones(number_component)) * sensor_noise)
        Cm = np.diag([soil_radiance_variance, soil_radiance_variance, leaf_radiance_variance])
        pre = np.linalg.inv(np.transpose(w) * np.linalg.inv(Cd) * w + np.linalg.inv(Cm))
        coeff = pre * (np.transpose(w) * np.linalg.inv(Cd) * b + np.linalg.inv(Cm) * ctprior)
        ### another solution for using priori information
        # coeff = ctprior + np.transpose(Cd * np.transpose(w) * pre) * (b - np.transpose(w) * ctprior)
        component_radiance = np.asarray(coeff)

        if (np.min(component_radiance) < radiance_min_threshold): continue
        if (np.max(component_radiance) > radiance_max_threshold): continue

        component_temperature = inv_planck(wl, component_radiance)
        # rad_soil = pg_n[k1, k2] * component_radiance[0] + (1 - pg_n[k1, k2]) * component_radiance[1]
        # temperature_soil = inv_planck(wl, rad_soil)

        result[:, kk] = [component_temperature[0], component_temperature[1], component_temperature[2]]
    #
    # result[result < temperature_min_threshold] = default_nan_temperature
    # result[result > temperature_max_threshold] = default_nan_temperature

    return result

def line_myinv(wNLine, wOLine, wALine, radNLine, radOLine, radAhiLine, maskLine, ns=1024):
    off = 2
    num_component = 3
    radiance_max_threshold = 20
    radiance_min_threshold = 4.5
    soil_radiance_variance = 2
    leaf_radiance_variance = 1
    number_value_threshold = 12

    result = np.zeros([3, ns])

    ################# multi_pixel ###################
    num_coef = 6
    windowX = np.asarray(np.repeat([-2,-1,0,1,2],5)).reshape(5,-1).transpose().reshape(-1)
    windowY = np.asarray(np.repeat([2,1,0,-1,-2],5))
    coef0 = np.ones([5,5]).reshape(-1)
    windowCoef = np.asarray([coef0, windowX, windowY, windowX*windowX, windowY*windowY, windowX*windowY])


    for kk in range(off, ns-off):
        maskk = maskLine[2, kk]
        if maskk == 0: continue

        ns1 = kk-off
        ns2 = kk + off

        wnTemp = wNLine[:, :, ns1:ns2]
        woTemp = wOLine[:, :, ns1:ns2]

        wn = np.asarray([wnTemp[j, :] * windowCoef[i,:] for j in range(num_component) for i in range(num_coef)])
        wo = np.asarray(woTemp[j,:] * windowCoef[i,:] for j in range(num_component) for i in range(num_coef))

        radn = radNLine[:, ns1:ns2]
        rado = radOLine[:, ns1:ns2]

        # ww = np.hstack((wn[:, ind], wo[:, ind])).transpose()
        # bb = np.hstack((radn[ind], rado[ind]))
        # coeffprior = np.asarray(lstsq(ww, bb, rcond=None))[0]

def fitting_lsct(ww,bb):

    res = fmin(fun_lsct, x0=[0.1,0.1,0.1,0.1,0.1,0.1,0.1,0.1,0.1,0.1,0.1,0.1,0.1,0.1,0.1,0.1,0.1,0.1],args=(ww,bb,),disp = 0)

    return res

def fun_lsct(x,ww,bb):
    mea = bb
    xx = np.zeros(18)
    for i in range(len(x)):
        xx[i] = x[i]
    mod = np.matmul(ww,xx)

    for i in range(0,18):
        mod = mod + 0.5 * xx[i] *xx[i]*0.0001
    res = mod - mea
    return np.sum(res*res)
    # return 1

def fitting_lsct_2(ww,bb,method = 'powell'):

    #res = fmin(fun_lsct_2, x0=[300.1,1.1,1.1,1.1,1.1,1.1,290.1,1.1,1.1,1.1,1.1,1.1],args=(ww,bb,),disp = 0)

    x0 = np.asarray([300.1,0.1,0.1,0.1,0.1,0.1,290.1,0.1,0.1,0.1,0.1,0.1])
    bnds = ((-1, 1), (-1, 1), (-1, 1), (-0.1,10))
    res = minimize(fun_lsct_2, x0,
                   args=(ww,bb,),
                   method = 'slsqp') ### good
                   # method = 'TNC',### sparse
                   # method ='L-BFGS-B',
                   #bounds=bnds)

    return res.x

def fun_lsct_2(x,ww,bb):
    mea = bb
    xx = np.zeros(12)
    for i in range(len(x)):
        xx[i] = x[i]
    mod = np.matmul(ww,xx)

    for i in range(0,12):
        if i == 0: continue;
        if i == 6: continue;
        mod = mod + 0.5 * xx[i] *xx[i]*0.0001
    res = mod - mea
    return np.sum(res*res)

def line_inv_zhengze(wNLine, wOLine, wALine, radNLine, radOLine, radAhiLine, maskLine,ns = 1024):
    wl = 10.8
    off_ = 0
    radiance_max_threshold = 20
    radiance_min_threshold = 4.5
    temperature_max_threshold = 350
    temperature_min_threshold = 250
    default_nan_temperature = 0
    soil_radiance_variance = 2
    leaf_radiance_variance = 1
    sensor_noise = 0.05
    pure_soil_threshold = 0.05
    pure_leaf_threshold = 0.95
    fvc_max_threshold = 0.99
    fvc_min_threshold = 0.01
    number_component = 3
    number_angle = 2
    number_value_threshold = 12

    result = np.zeros([3,ns])

    ###
    off = 2
    for kk in range(off, ns-off):


        maskk = maskLine[2,kk]
        if maskk == 0: continue

        ns1 = kk - off
        ns2 = kk + off + 1

        w1 = wNLine[:,:, ns1:ns2]
        w1 = np.asarray(np.reshape(w1, (number_component, -1)))
        w2 = wOLine[:,:, ns1:ns2]
        w2 = np.asarray(np.reshape(w2, (number_component, -1)))

        bb1 = (np.reshape(radNLine[:, ns1:ns2], -1))
        bb2 = (np.reshape(radOLine[:, ns1:ns2], -1))



        mask = np.reshape(maskLine[:, ns1:ns2],-1)
        ind = (mask==1) * (np.isnan(w1[0,:])==0)

        num_val_point = np.sum(ind)
        if (num_val_point < number_value_threshold): continue

        ### w1 for nadir and w2 for oblique
        ns_temp = np.asarray([-2, -1, 0, 1, 2, -2, -1, 0, 1, 2, -2, -1, 0, 1, 2, -2, -1, 0, 1, 2, -2, -1, 0, 1, 2])
        nl_temp = np.asarray(np.repeat([-2, -1, 0, 1, 2], 5))
        part = 6

        n0 = np.ones(len(ns_temp))
        x = np.asarray([n0, ns_temp, nl_temp, ns_temp * nl_temp, ns_temp * ns_temp, nl_temp * nl_temp])
        w11 = np.asarray([w1[j, :] * x[i, :] for j in range(number_component) for i in range(part)])
        w22 = np.asarray([w2[j, :] * x[i, :] for j in range(number_component) for i in range(part)])

        ww = np.hstack((w11[:, ind], w22[:, ind]))
        bb = np.hstack((bb1[ind], bb2[ind]))

        ###############################################
        ### least-square method
        ###############################################
        ww = np.transpose(ww)

        coeffprior = fitting_lsct(ww,bb)
        # print(kk)
        # coeffprior = np.asarray(lstsq(ww, bb, rcond=None))[0]
        # cd1 = np.sum(coeffprior[:6] * x[:, offcenter])
        # cd2 = np.sum(coeffprior[6:] * x[:, offcenter])
        # ctprior = np.transpose(np.matrix([cd1, cd2]))

        ###############################################
        ### Bayes method with priori information
        ###############################################
        # bbb = sorted(b)
        # halfpoint = np.int(num_point / 2)
        # rleaf = np.average(bbb[0])
        # rsoil = np.average(bbb[1])
        # coeffprior = np.transpose(np.matrix([rsoil, 0, 0, 0, 0, 0, rleaf, 0, 0, 0, 0, 0]))
        # bb = np.transpose(np.matrix(bb))
        # ww = np.transpose(ww)
        # Cd = np.matrix(np.diag(np.ones(num_point * 2)) * Cdvaluep)
        # Cm = np.matrix(np.diag(np.ones(2 * part)))
        # Cm[0, 0] = 15.0
        # Cm[part, part] = 10.0
        # pre = np.linalg.inv(np.transpose(ww) * np.linalg.inv(Cd) * ww + np.linalg.inv(Cm))
        # ctprior = pre * (np.transpose(ww) * np.linalg.inv(Cd) * bb + np.linalg.inv(Cm) * coeffprior)

        #################################################
        ### first result without averaging information
        #################################################
        # cd1 = np.sum(coeffprior[:6] * x[:, offcenter])
        # cd2 = np.sum(coeffprior[6:] * x[:, offcenter])
        # ctprior = np.transpose(np.matrix([cd1, cd2]))

        ################################################
        ### first reult with averaing information
        ################################################
        offcenter = np.int(((2 * off + 1) * (2 * off + 1) - 1) / 2)
        fd = np.asarray([[1, 4, 7, 4, 1], [4, 16, 26, 16, 4], [7, 26, 41, 26, 7], [4, 16, 26, 16, 4], [1, 4, 7, 4, 1]])
        fd = np.reshape(fd, -1) * 1.0

        coeffprior = np.asarray(coeffprior)
        ct1 = np.asarray([np.sum(coeffprior[:part] * x[:part, j]) for j in range(25)])
        ct2 = np.asarray([np.sum(coeffprior[part:2 * part] * x[:part, j]) for j in range(25)])
        ct3 = np.asarray([np.sum(coeffprior[2 * part:3 * part] * x[:part, j]) for j in range(25)])
        indnew = ind * (ct2 < radiance_max_threshold) * (ct2 > radiance_min_threshold) * \
                 (ct1 > radiance_min_threshold) * (ct1 < radiance_max_threshold) * \
                 (ct3 > radiance_min_threshold) * (ct3 < radiance_max_threshold)
        apoint = np.sum(indnew)
        if (apoint <= 1):
            cd1 = np.sum(coeffprior[:part] * x[:, offcenter])
            cd2 = np.sum(coeffprior[part:2 * part] * x[:, offcenter])
            cd3 = np.sum(coeffprior[2 * part:3 * part] * x[:, offcenter])
            ctprior = np.transpose(np.matrix([cd1, cd2, cd3]))
        else:
            fd[indnew] = fd[indnew] / np.sum(fd[indnew])

            # inver-distance weight but not used
            # bb0 = bb1[offcenter]
            # fdnew = np.zeros(25)
            # dismax = max(abs(bb1[indnew] - bb0))
            # if dismax != 0:
            #     fdnew[indnew] = 1.0 - abs(1.0 * bb1[indnew] - bb0) / dismax
            # else:
            #     fdnew[:] = 1
            # fdnew[indnew] = fdnew[indnew] / np.sum(fdnew[indnew])
            # fd[indnew] = (fdnew[indnew] * fd[indnew]) / np.sum(fdnew[indnew] * fd[indnew])

            cd1new = np.sum(ct1[indnew] * fd[indnew])
            cd2new = np.sum(ct2[indnew] * fd[indnew])
            cd3new = np.sum(ct3[indnew] * fd[indnew])
            ctprior = np.transpose(np.matrix([cd1new, cd2new, cd3new]))
        component_temperature = inv_planck(wl, ctprior)
        #################################################
        ### second result by combining one-point result
        #################################################

        ns1 = kk - off_
        ns2 = kk + off_ + 1
        # k22 = np.uint16(kk / 2)
        w1 = wNLine[:, 2, ns1:ns2]
        w1 = np.asarray(np.reshape(w1, (number_component, -1)))
        w2 = wOLine[:,2, ns1:ns2]
        w2 = np.asarray(np.reshape(w2, (number_component, -1)))
        w3 = wALine[:,2, ns1:ns2]
        w3 = np.asarray(np.reshape(w3, (number_component, -1)))

        b1 = np.reshape(radNLine[2, ns1:ns2], -1)
        b2 = np.reshape(radOLine[2, ns1:ns2], -1)
        b3 = np.reshape(radAhiLine[2, ns1:ns2], -1)
        w = np.hstack((w1, w2, w3))
        b = np.hstack((b1, b2, b3))
        w = np.transpose(w)

        #################################################
        ### least-squared method
        #################################################
        # coeffprior = np.asarray(lstsq(w, b))[0]

        #################################################
        ### Bayes method
        #################################################

        w = np.matrix(w)
        b = np.matrix(b)
        b = np.transpose(b)


        Cd = np.matrix(np.diag(np.ones(number_component)) * sensor_noise)
        Cm = np.diag([soil_radiance_variance, soil_radiance_variance, leaf_radiance_variance])
        pre = np.linalg.inv(np.transpose(w) * np.linalg.inv(Cd) * w + np.linalg.inv(Cm))
        coeff = pre * (np.transpose(w) * np.linalg.inv(Cd) * b + np.linalg.inv(Cm) * ctprior)
        ### another solution for using priori information
        # coeff = ctprior + np.transpose(Cd * np.transpose(w) * pre) * (b - np.transpose(w) * ctprior)
        component_radiance = np.asarray(coeff)

        if (np.min(component_radiance) < radiance_min_threshold): continue
        if (np.max(component_radiance) > radiance_max_threshold): continue

        component_temperature = inv_planck(wl, component_radiance)
        # rad_soil = pg_n[k1, k2] * component_radiance[0] + (1 - pg_n[k1, k2]) * component_radiance[1]
        # temperature_soil = inv_planck(wl, rad_soil)

        result[:, kk] = [component_temperature[0], component_temperature[1], component_temperature[2]]
    #
    # result[result < temperature_min_threshold] = default_nan_temperature
    # result[result > temperature_max_threshold] = default_nan_temperature

    return result

def line_slstr_ahi_2(wNLine, wOLine, wALine, radNLine, radOLine, radAhiLine, maskLine,ns = 1024):
    wl = 10.8
    off_ = 0
    radiance_max_threshold = 20
    radiance_min_threshold = 4.5
    temperature_max_threshold = 350
    temperature_min_threshold = 250
    default_nan_temperature = 0
    soil_radiance_variance = 2
    leaf_radiance_variance = 1
    sensor_noise = 0.05
    pure_soil_threshold = 0.01
    pure_leaf_threshold = 0.99
    fvc_max_threshold = 0.99
    fvc_min_threshold = 0.01
    number_component = 2
    number_observation = 3
    number_angle = 2
    number_value_threshold = 6

    result = np.zeros([2,ns])

    ###
    off = 2
    for kk in range(off, ns-off):


        maskk = maskLine[2,kk]
        if maskk == 0: continue
        isprior = 1
        ns1 = kk - off
        ns2 = kk + off + 1

        w1 = wNLine[:,:, ns1:ns2]
        w1 = np.asarray(np.reshape(w1, (number_component, -1)))
        w2 = wOLine[:,:, ns1:ns2]
        w2 = np.asarray(np.reshape(w2, (number_component, -1)))

        bb1 = (np.reshape(radNLine[:, ns1:ns2], -1))
        bb2 = (np.reshape(radOLine[:, ns1:ns2], -1))



        mask = np.reshape(maskLine[:, ns1:ns2],-1)
        ind = (mask==1) * (np.isnan(w1[0,:])==0)

        num_val_point = np.sum(ind)
        if (num_val_point < number_value_threshold): continue

        ### w1 for nadir and w2 for oblique
        ns_temp = np.asarray([-2, -1, 0, 1, 2, -2, -1, 0, 1, 2, -2, -1, 0, 1, 2, -2, -1, 0, 1, 2, -2, -1, 0, 1, 2])
        nl_temp = np.asarray(np.repeat([-2, -1, 0, 1, 2], 5))
        part = 6

        n0 = np.ones(len(ns_temp))
        x = np.asarray([n0, ns_temp, nl_temp, ns_temp * nl_temp, ns_temp * ns_temp, nl_temp * nl_temp])
        w11 = np.asarray([w1[j, :] * x[i, :] for j in range(number_component) for i in range(part)])
        w22 = np.asarray([w2[j, :] * x[i, :] for j in range(number_component) for i in range(part)])

        ww = np.hstack((w11[:, ind], w22[:, ind]))
        bb = np.hstack((bb1[ind], bb2[ind]))


        ###############################################
        ### least-square method
        ###############################################
        ww = np.transpose(ww)

        coeffprior = fitting_lsct_2(ww,bb)
        # print(kk)
        #coeffprior = np.asarray(lstsq(ww, bb, rcond=None))[0]
        # cd1 = np.sum(coeffprior[:6] * x[:, offcenter])
        # cd2 = np.sum(coeffprior[6:] * x[:, offcenter])
        # ctprior = np.transpose(np.matrix([cd1, cd2]))

        ###############################################
        ### Bayes method with priori information
        ###############################################
        # bbb = sorted(b)
        # halfpoint = np.int(num_point / 2)
        # rleaf = np.average(bbb[0])
        # rsoil = np.average(bbb[1])
        # coeffprior = np.transpose(np.matrix([rsoil, 0, 0, 0, 0, 0, rleaf, 0, 0, 0, 0, 0]))
        # bb = np.transpose(np.matrix(bb))
        # ww = np.transpose(ww)
        # Cd = np.matrix(np.diag(np.ones(num_point * 2)) * Cdvaluep)
        # Cm = np.matrix(np.diag(np.ones(2 * part)))
        # Cm[0, 0] = 15.0
        # Cm[part, part] = 10.0
        # pre = np.linalg.inv(np.transpose(ww) * np.linalg.inv(Cd) * ww + np.linalg.inv(Cm))
        # ctprior = pre * (np.transpose(ww) * np.linalg.inv(Cd) * bb + np.linalg.inv(Cm) * coeffprior)

        #################################################
        ### first result without averaging information
        #################################################
        # cd1 = np.sum(coeffprior[:6] * x[:, offcenter])
        # cd2 = np.sum(coeffprior[6:] * x[:, offcenter])
        # ctprior = np.transpose(np.matrix([cd1, cd2]))

        ################################################
        ### first reult with averaing information
        ################################################
        offcenter = np.int(((2 * off + 1) * (2 * off + 1) - 1) / 2)
        fd = np.asarray([[1, 4, 7, 4, 1], [4, 16, 26, 16, 4], [7, 26, 41, 26, 7], [4, 16, 26, 16, 4], [1, 4, 7, 4, 1]])
        fd = np.reshape(fd, -1) * 1.0

        coeffprior = np.asarray(coeffprior)
        ct1 = np.asarray([np.sum(coeffprior[:part] * x[:part, j]) for j in range(25)])
        ct2 = np.asarray([np.sum(coeffprior[part:2 * part] * x[:part, j]) for j in range(25)])


        indnew = ind * (ct2 < radiance_max_threshold) * (ct2 > radiance_min_threshold) * \
                 (ct1 > radiance_min_threshold) * (ct1 < radiance_max_threshold)
        apoint = np.sum(indnew)
        if (apoint <= 1):
            cd1 = np.sum(coeffprior[:part] * x[:, offcenter])
            cd2 = np.sum(coeffprior[part:2 * part] * x[:, offcenter])
            ctprior = np.transpose(np.matrix([cd1, cd2]))
        else:
            fd[indnew] = fd[indnew] / np.sum(fd[indnew])

            #inver-distance weight but not used
            # bb0 = bb1[offcenter]
            # fdnew = np.zeros(25)
            # dismax = max(abs(bb1[indnew] - bb0))
            # if dismax != 0:
            #     fdnew[indnew] = 1.0 - abs(1.0 * bb1[indnew] - bb0) / dismax
            # else:
            #     fdnew[:] = 1
            # fdnew[indnew] = fdnew[indnew] / np.sum(fdnew[indnew])
            # fd[indnew] = (fdnew[indnew] * fd[indnew]) / np.sum(fdnew[indnew] * fd[indnew])

            cd1new = np.sum(ct1[indnew] * fd[indnew])
            cd2new = np.sum(ct2[indnew] * fd[indnew])
            ctprior = np.transpose(np.matrix([cd1new, cd2new]))
        component_temperature = inv_planck(wl, ctprior)
        #################################################
        ### second result by combining one-point result
        #################################################

        ns1 = kk - off_
        ns2 = kk + off_ + 1
        # k22 = np.uint16(kk / 2)
        w1 = wNLine[:, 2, ns1:ns2]
        w1 = np.asarray(np.reshape(w1, (number_component, -1)))
        w2 = wOLine[:,2, ns1:ns2]
        w2 = np.asarray(np.reshape(w2, (number_component, -1)))
        w3 = wALine[:,2, ns1:ns2]
        w3 = np.asarray(np.reshape(w3, (number_component, -1)))

        b1 = np.reshape(radNLine[2, ns1:ns2], -1)
        b2 = np.reshape(radOLine[2, ns1:ns2], -1)
        b3 = np.reshape(radAhiLine[2, ns1:ns2], -1)
        w = np.hstack((w1, w2, w3))
        b = np.hstack((b1, b2, b3))
        w = np.transpose(w)

        #################################################
        ### least-squared method
        #################################################
        # coeffprior = np.asarray(lstsq(w, b))[0]

        #################################################
        ### Bayes method
        #################################################

        w = np.matrix(w)
        b = np.matrix(b)
        b = np.transpose(b)


        Cd = np.matrix(np.diag(np.ones(number_observation)) * sensor_noise)
        Cm = np.diag([soil_radiance_variance, leaf_radiance_variance])
        pre = np.linalg.inv(np.transpose(w) * np.linalg.inv(Cd) * w + np.linalg.inv(Cm))
        coeff = pre * (np.transpose(w) * np.linalg.inv(Cd) * b + np.linalg.inv(Cm) * ctprior)
        ### another solution for using priori information
        # coeff = ctprior + np.transpose(Cd * np.transpose(w) * pre) * (b - np.transpose(w) * ctprior)
        component_radiance = np.asarray(coeff)

        if (np.min(component_radiance) < radiance_min_threshold): continue
        if (np.max(component_radiance) > radiance_max_threshold): continue

        component_temperature = inv_planck(wl, component_radiance)
        # rad_soil = pg_n[k1, k2] * component_radiance[0] + (1 - pg_n[k1, k2]) * component_radiance[1]
        # temperature_soil = inv_planck(wl, rad_soil)

        result[:, kk] = [component_temperature[0], component_temperature[1]]
    # result[result < temperature_min_threshold] = default_nan_temperature
    # result[result > temperature_max_threshold] = default_nan_temperature

    return result

#######中间传递参数函数（三组分）
def doMultiple_line_inv(param):
    return line_inv_zhengze((param[0]), (param[1]), (param[2]), (param[3]), (param[4]), (param[5]), (param[6]), (param[7]))

def doMultiple_slstr_ahi_2(param):
    return line_slstr_ahi_2((param[0]), (param[1]), (param[2]), (param[3]), (param[4]), (param[5]), (param[6]), (param[7]))

#######多线程计算三组分
def inv_mpl_agl_multiple(lst_n, lst_o, lst_ahi,emis_s, emis_v, fvcN, fvcO, fvcAhi,pg_n,pg_o,pg_ahi, wl=10.8):
    radiance_max_threshold = 20
    radiance_min_threshold = 4.5
    temperature_max_threshold = 350
    temperature_min_threshold = 250
    default_nan_temperature = 0
    soil_radiance_variance = 2
    leaf_radiance_variance = 1
    # sensor_noise = 0.05
    pure_soil_threshold = 0.05
    pure_leaf_threshold = 0.95
    fvc_max_threshold = 0.99
    fvc_min_threshold = 0.01
    fd0 = np.asarray([[1, 4, 7, 4, 1], [4, 16, 26, 16, 4], [7, 26, 41, 26, 7], [4, 16, 26, 16, 4], [1, 4, 7, 4, 1]])
    number_component = 3
    number_angle = 2
    number_value_threshold = 12
    off = 2
    off_ = 0

    start = time.time()

    [nl, ns] = np.shape(lst_n)
    result = np.zeros([4, nl, ns])

    ######### FVC_NDVI
    # fvc_n = (ndvi_n - ndvi_min) / (ndvi_max - ndvi_min)
    # fvc_n[fvc_n > fvc_max_threshold] = fvc_max_threshold
    # fvc_n[fvc_n < fvc_min_threshold] = fvc_min_threshold
    #
    # fvc_o = (ndvi_o - ndvi_min) / (ndvi_max - ndvi_min)
    # fvc_o[fvc_o > fvc_max_threshold] = fvc_max_threshold
    # fvc_o[fvc_o < fvc_min_threshold] = fvc_min_threshold
    #
    #
    # fvc_ahi = (ndvi_ahi - ndvi_min) / (ndvi_max - ndvi_min)
    # fvc_ahi[fvc_ahi > fvc_max_threshold] = fvc_max_threshold
    # fvc_ahi[fvc_ahi < fvc_min_threshold] = fvc_min_threshold
    ######### FVC LAI
    fvc_n = fvcN * 1.0
    fvc_n[fvc_n > fvc_max_threshold] = fvc_max_threshold
    fvc_n[fvc_n < fvc_min_threshold] = fvc_min_threshold

    fvc_o = fvcO * 1.0
    fvc_o[fvc_o > fvc_max_threshold] = fvc_max_threshold
    fvc_o[fvc_o < fvc_min_threshold] = fvc_min_threshold

    fvc_ahi = fvcAhi * 1.0
    fvc_ahi[fvc_ahi > fvc_max_threshold] = fvc_max_threshold
    fvc_ahi[fvc_ahi < fvc_min_threshold] = fvc_min_threshold
    ####### The radiance
    rad_n = planckK(wl, lst_n)
    rad_n = rad_n * (fvc_n * emis_v + (1 - fvc_n) * emis_s)
    rad_o = planckK(wl, lst_o)
    rad_o = rad_o * (fvc_o * emis_v + (1 - fvc_o) * emis_s)

    rad_ahi = planckK(wl,lst_ahi)
    emisd2_v = resize_data_near(emis_v,nl/2,(ns+1)/2)
    emisd2_s = resize_data_near(emis_s,nl/2,(ns+1)/2)
    # emisd2_v = resize_data_near(emis_v, nl / 2,  ns/ 2)
    # emisd2_s = resize_data_near(emis_s, nl / 2, ns / 2)
    fvc_ahi = resize_data_near(fvc_ahi,nl/2,(ns+1)/2)
    rad_ahiData = rad_ahi *(fvc_ahi*emisd2_v + (1-fvc_ahi)*emisd2_s)
    rad_ahi = resize_data_near(rad_ahiData, nl, ns)

    # component effective emissivity matrix
    wN = np.asarray([emis_s * (1 - fvc_n)*pg_n,emis_s * (1 - fvc_n)*(1-pg_n), emis_v * (fvc_n)])
    wO = np.asarray([emis_s * (1 - fvc_o)*pg_o, emis_s * (1 - fvc_o)*(1-pg_o),emis_v * (fvc_o)])

    pg_ahi = resize_data_near(pg_ahi,nl/2, (ns+1)/2)
    wAhiData= np.asarray([emisd2_s * (1 - fvc_ahi)*pg_ahi, emisd2_s * (1 - fvc_ahi)*(1-pg_ahi),emisd2_v * (fvc_ahi)])
    wAhi = np.asarray([resize_data_near(wAhiData[0], nl, ns), resize_data_near(wAhiData[1],nl,ns), resize_data_near(wAhiData[2],nl,ns)])

    mask = np.zeros([nl, ns])
    ind0 = (fvc_n > pure_soil_threshold) * (fvc_n < pure_leaf_threshold) * \
          (rad_n > radiance_min_threshold) * (rad_n < radiance_max_threshold) * \
          (rad_o > radiance_min_threshold) * (rad_o < radiance_max_threshold)
    mask[ind0] = 1

    para = []
    for kn in range(off, nl-off):
        wNLine = wN[:,kn-off:kn+off+1,:]
        wOLine = wO[:,kn-off:kn+off+1,:]
        wALine = wAhi[:, kn - off:kn + off+1, :]

        radNLine = rad_n[kn-off:kn+off+1,:]
        radOLine = rad_o[kn - off:kn + off+1, :]
        radAhiLine = rad_ahi[kn - off:kn + off+1, :]

        maskLine = mask[kn-off:kn+off+1,:]
        para.append([wNLine, wOLine, wALine, radNLine, radOLine, radAhiLine, maskLine,ns])
    #

    # for p in para:
    #     tasks.append(pool.apply_async(doMultiple_line_inv, (p,)))
    #     # doMultiple_line_inv(p)


    tasks = []
    pool = Pool(min(24, cpu_count()))
    indTemp = 2
    for p in para:
        tasks.append(pool.apply_async(doMultiple_line_inv, (p,)))
    pool.close()
    pool.join()
    results = [task.get() for task in tasks]
    end = time.time()
    results = np.asarray(results)
    resultForm = np.asarray([results[:,0,:], results[:,1,:], results[:,2,:]])
    print('time cost: ', end - start, 's')

    return resultForm

#######多线程计算两组分
def inv_mpl_agl_multiple_ahi(lst_n, lst_o, lst_ahi,emis_s, emis_v, fvcN, fvcO, fvcAhi, wl=10.8):
    radiance_max_threshold = 20
    radiance_min_threshold = 4.5
    temperature_max_threshold = 350
    temperature_min_threshold = 250
    default_nan_temperature = 0
    soil_radiance_variance = 2
    leaf_radiance_variance = 1
    # sensor_noise = 0.05
    pure_soil_threshold = 0.01
    pure_leaf_threshold = 0.99
    fvc_max_threshold = 0.99
    fvc_min_threshold = 0.01
    fd0 = np.asarray([[1, 4, 7, 4, 1], [4, 16, 26, 16, 4], [7, 26, 41, 26, 7], [4, 16, 26, 16, 4], [1, 4, 7, 4, 1]])
    number_component = 2
    number_angle = 2
    number_value_threshold = 12
    off = 2
    off_ = 0

    start = time.time()

    [nl, ns] = np.shape(lst_n)
    result = np.zeros([2, nl, ns])

    ######### FVC_NDVI
    # fvc_n = (ndvi_n - ndvi_min) / (ndvi_max - ndvi_min)
    # fvc_n[fvc_n > fvc_max_threshold] = fvc_max_threshold
    # fvc_n[fvc_n < fvc_min_threshold] = fvc_min_threshold
    #
    # fvc_o = (ndvi_o - ndvi_min) / (ndvi_max - ndvi_min)
    # fvc_o[fvc_o > fvc_max_threshold] = fvc_max_threshold
    # fvc_o[fvc_o < fvc_min_threshold] = fvc_min_threshold
    #
    #
    # fvc_ahi = (ndvi_ahi - ndvi_min) / (ndvi_max - ndvi_min)
    # fvc_ahi[fvc_ahi > fvc_max_threshold] = fvc_max_threshold
    # fvc_ahi[fvc_ahi < fvc_min_threshold] = fvc_min_threshold
    ######### FVC LAI
    fvc_n = fvcN * 1.0
    fvc_n[fvc_n > fvc_max_threshold] = fvc_max_threshold
    fvc_n[fvc_n < fvc_min_threshold] = fvc_min_threshold

    fvc_o = fvcO * 1.0
    fvc_o[fvc_o > fvc_max_threshold] = fvc_max_threshold
    fvc_o[fvc_o < fvc_min_threshold] = fvc_min_threshold

    fvc_ahi = fvcAhi * 1.0
    fvc_ahi[fvc_ahi > fvc_max_threshold] = fvc_max_threshold
    fvc_ahi[fvc_ahi < fvc_min_threshold] = fvc_min_threshold
    ####### The radiance
    rad_n = planckK(wl, lst_n)
    rad_n = rad_n * (fvc_n * emis_v + (1 - fvc_n) * emis_s)
    rad_o = planckK(wl, lst_o)
    rad_o = rad_o * (fvc_o * emis_v + (1 - fvc_o) * emis_s)

    rad_ahi = planckK(wl,lst_ahi)
    emisd2_v = resize_data_near(emis_v,nl/2,(ns+1)/2)
    emisd2_s = resize_data_near(emis_s,nl/2,(ns+1)/2)
    # emisd2_v = resize_data_near(emis_v, nl / 2, ns / 2)
    # emisd2_s = resize_data_near(emis_s, nl / 2, ns / 2)
    rad_ahiData = rad_ahi *(fvc_ahi*emisd2_v + (1-fvc_ahi)*emisd2_s)
    rad_ahi = resize_data_near(rad_ahiData, nl, ns)

    # component effective emissivity matrix
    wN = np.asarray([emis_s * (1 - fvc_n), emis_v * (fvc_n)])
    wO = np.asarray([emis_s * (1 - fvc_o), emis_v * (fvc_o)])
    wAhiData= np.asarray([emisd2_s * (1 - fvc_ahi),emisd2_v * (fvc_ahi)])
    wAhi = np.asarray([resize_data_near(wAhiData[0], nl, ns), resize_data_near(wAhiData[1],nl,ns)])

    mask = np.zeros([nl, ns])
    ind0 = (fvc_n > pure_soil_threshold) * (fvc_n < pure_leaf_threshold) * \
          (rad_n > radiance_min_threshold) * (rad_n < radiance_max_threshold) * \
          (rad_o > radiance_min_threshold) * (rad_o < radiance_max_threshold)
    mask[ind0] = 1

    para = []
    for kn in range(off, nl-off):
        wNLine = wN[:,kn-off:kn+off+1,:]
        wOLine = wO[:,kn-off:kn+off+1,:]
        wALine = wAhi[:, kn - off:kn + off+1, :]

        radNLine = rad_n[kn-off:kn+off+1,:]
        radOLine = rad_o[kn - off:kn + off+1, :]
        radAhiLine = rad_ahi[kn - off:kn + off+1, :]

        maskLine = mask[kn-off:kn+off+1,:]
        para.append([wNLine, wOLine, wALine, radNLine, radOLine, radAhiLine, maskLine,ns])

    # for p in para:
    #     # tasks.append(pool.apply_async(doMultiple_line_inv, (p,)))
    #     doMultiple_slstr_ahi_2(p)


    tasks = []
    pool = Pool(min(36, cpu_count()))
    indTemp = 2
    for p in para:
        tasks.append(pool.apply_async(doMultiple_slstr_ahi_2, (p,)))
    pool.close()
    pool.join()
    results = [task.get() for task in tasks]
    end = time.time()
    results = np.asarray(results)
    resultForm = np.asarray([results[:,0,:], results[:,1,:]])
    print('time cost: ', end - start, 's')

    return resultForm


'''多线程两组分温度反演程序：共三个'''
#######中间传递参数函数  两组分
def doMultiple_line_inv_2(param):
    return line_inv_2((param[0]), (param[1]), (param[2]), (param[3]), (param[4]), (param[5]))


# def doMultiple_line_inv_2_s(param):
#     return line_inv_2_s((param[0]), (param[1]), (param[2]), (param[3]), (param[4]), (param[5]))


######分行计算的两组分温度结果，为多线程内部函数调用
def line_inv_2(wNLine, wOLine, radNLine, radOLine, maskLine,ns = 1024):
    wl = 10.8
    off_ = 0
    radiance_max_threshold = 20
    radiance_min_threshold = 4.5
    temperature_max_threshold = 350
    temperature_min_threshold = 250
    default_nan_temperature = 0
    soil_radiance_variance = 2
    leaf_radiance_variance = 1
    sensor_noise = 0.05
    pure_soil_threshold = 0.01
    pure_leaf_threshold = 0.99
    fvc_max_threshold = 0.99
    fvc_min_threshold = 0.01
    number_component = 2
    number_angle = 2
    number_value_threshold = 12

    result = np.zeros([number_component,ns])
    result_point = np.zeros([number_component, ns])

    off = 2
    for kk in range(off, ns-off):
        maskk = maskLine[2,kk]
        if maskk == 0: continue

        ns1 = kk - off
        ns2 = kk + off + 1
        ###### w1是nadir，w2是oblique
        w1 = wNLine[:,:,ns1:ns2]
        w1 = np.asarray(np.reshape(w1, (number_component, -1)))
        w2 = wOLine[:, :, ns1:ns2]
        w2 = np.asarray(np.reshape(w2, (number_component, -1)))

        bb1 = (np.reshape(radNLine[:, ns1:ns2], -1))
        bb2 = (np.reshape(radOLine[:, ns1:ns2], -1))

        mask = np.reshape(maskLine[:, ns1:ns2], -1)
        ind = (mask == 1) * (np.isnan(w1[0, :]) == 0)

        num_val_point = np.sum(ind)
        if (num_val_point < number_value_threshold): continue
        ns_temp = np.asarray([-2, -1, 0, 1, 2, -2, -1, 0, 1, 2, -2, -1, 0, 1, 2, -2, -1, 0, 1, 2, -2, -1, 0, 1, 2])
        nl_temp = np.asarray(np.repeat([-2, -1, 0, 1, 2], 5))
        part = 6

        n0 = np.ones(len(ns_temp))
        x = np.asarray([n0, ns_temp, nl_temp, ns_temp * nl_temp, ns_temp * ns_temp, nl_temp * nl_temp])
        w11 = np.asarray([w1[j, :] * x[i, :] for j in range(number_component) for i in range(part)])
        w22 = np.asarray([w2[j, :] * x[i, :] for j in range(number_component) for i in range(part)])

        ww = np.hstack((w11[:, ind], w22[:, ind]))
        bb = np.hstack((bb1[ind], bb2[ind]))

        ###############################################
        ### least-square method
        ###############################################
        ww = np.transpose(ww)

        coeffprior = np.asarray(lstsq(ww, bb, rcond=None)[0])

        ################################################
        ### first reult with averaing information
        ################################################
        offcenter = np.int_(((2 * off + 1) * (2 * off + 1) - 1) / 2)
        fd = np.asarray([[1, 4, 7, 4, 1], [4, 16, 26, 16, 4], [7, 26, 41, 26, 7], [4, 16, 26, 16, 4], [1, 4, 7, 4, 1]])
        fd = np.reshape(fd, -1) * 1.0

        coeffprior = np.asarray(coeffprior)
        ct1 = np.asarray([np.sum(coeffprior[:part] * x[:part, j]) for j in range(25)])
        ct2 = np.asarray([np.sum(coeffprior[part:2 * part] * x[:part, j]) for j in range(25)])
        indnew = ind * (ct2 < radiance_max_threshold) * (ct2 > radiance_min_threshold) * \
                 (ct1 > radiance_min_threshold) * (ct1 < radiance_max_threshold)
        apoint = np.sum(indnew)
        if (apoint <= 1):
            cd1 = np.sum(coeffprior[:part] * x[:, offcenter])
            cd2 = np.sum(coeffprior[part:] * x[:, offcenter])
            ctprior = np.transpose(np.matrix([cd1, cd2]))
        else:
            fd[indnew] = fd[indnew] / np.sum(fd[indnew])

            cd1new = np.sum(ct1[indnew] * fd[indnew])
            cd2new = np.sum(ct2[indnew] * fd[indnew])
            ctprior = np.transpose(np.matrix([cd1new, cd2new]))
        # component_temperature = inv_planck(wl, ctprior)
        #################################################
        ### second result by combining one-point result
        #################################################

        ns1 = kk - off_
        ns2 = kk + off_ + 1
        w1 = wNLine[:, 2, ns1:ns2]
        w1 = np.asarray(np.reshape(w1, (number_component, -1)))
        w2 = wOLine[:, 2, ns1:ns2]
        w2 = np.asarray(np.reshape(w2, (number_component, -1)))
        b1 = (np.reshape(radNLine[2, ns1:ns2], -1))
        b2 = (np.reshape(radOLine[2, ns1:ns2], -1))
        w = np.hstack((w1, w2))
        b = np.hstack((b1, b2))
        w = np.transpose(w)

        #################################################
        ### least-squared method
        #################################################
        # coeffprior = np.asarray(lstsq(w, b)[0])
        # coeffprior_point = np.asarray(lstsq(w, b)[0])
        # component_temperature_point = inv_planck(wl, coeffprior_point)
        # result_point[:, kk] = [component_temperature_point[0], component_temperature_point[1]]

        #################################################
        ### Bayes method
        #################################################

        w = np.matrix(w)
        b = np.matrix(b)
        b = np.transpose(b)

        Cd = np.matrix(np.diag(np.ones(number_component)) * sensor_noise)
        Cm = np.diag([soil_radiance_variance, leaf_radiance_variance])
        pre = np.linalg.inv(np.transpose(w) * np.linalg.inv(Cd) * w + np.linalg.inv(Cm))
        coeff = pre * (np.transpose(w) * np.linalg.inv(Cd) * b + np.linalg.inv(Cm) * ctprior)
        ### another solution for using priori information
        # coeff = ctprior + np.transpose(Cd * np.transpose(w) * pre) * (b - np.transpose(w) * ctprior)
        component_radiance = np.asarray(coeff)

        if (np.min(component_radiance) < radiance_min_threshold): continue
        if (np.max(component_radiance) > radiance_max_threshold): continue

        component_temperature = inv_planck(wl, component_radiance)

        result[:, kk] = [component_temperature[0][0], component_temperature[1][0]]

    return result

# def line_inv_2_s(wNLine, wOLine, radNLine, radOLine, maskLine,nl = 1024):
#     '''
#     this is for the sample rec
#     '''
#     wl = 10.8
#     off_ = 0
#     radiance_max_threshold = 20
#     radiance_min_threshold = 4.5
#     temperature_max_threshold = 350
#     temperature_min_threshold = 250
#     default_nan_temperature = 0
#     soil_radiance_variance = 2
#     leaf_radiance_variance = 1
#     sensor_noise = 0.05
#     pure_soil_threshold = 0.01
#     pure_leaf_threshold = 0.99
#     fvc_max_threshold = 0.99
#     fvc_min_threshold = 0.01
#     number_component = 2
#     number_angle = 2
#     number_value_threshold = 12

#     result = np.zeros([number_component,nl])
#     result_point = np.zeros([number_component, nl])

#     off = 2
#     for kk in range(off, nl-off):
#         maskk = maskLine[kk,2]
#         if maskk == 0: continue

#         nl1 = kk - off
#         nl2 = kk + off + 1
#         ###### w1是nadir，w2是oblique
#         w1 = wNLine[:,nl1:nl2,:]
#         w1 = np.asarray(np.reshape(w1, (number_component, -1)))
#         w2 = wOLine[:, nl1:nl2, :]
#         w2 = np.asarray(np.reshape(w2, (number_component, -1)))

#         bb1 = (np.reshape(radNLine[nl1:nl2, :], -1))
#         bb2 = (np.reshape(radOLine[nl1:nl2, :], -1))

#         mask = np.reshape(maskLine[nl1:nl2, :], -1)
#         ind = (mask == 1) * (np.isnan(w1[0, :]) == 0)

#         num_val_point = np.sum(ind)
#         if (num_val_point < number_value_threshold): continue
#         ns_temp = np.asarray([-2, -1, 0, 1, 2, -2, -1, 0, 1, 2, -2, -1, 0, 1, 2, -2, -1, 0, 1, 2, -2, -1, 0, 1, 2])
#         nl_temp = np.asarray(np.repeat([-2, -1, 0, 1, 2], 5))
#         part = 6

#         n0 = np.ones(len(ns_temp))
#         x = np.asarray([n0, ns_temp, nl_temp, ns_temp * nl_temp, ns_temp * ns_temp, nl_temp * nl_temp])
#         w11 = np.asarray([w1[j, :] * x[i, :] for j in range(number_component) for i in range(part)])
#         w22 = np.asarray([w2[j, :] * x[i, :] for j in range(number_component) for i in range(part)])

#         ww = np.hstack((w11[:, ind], w22[:, ind]))
#         bb = np.hstack((bb1[ind], bb2[ind]))

#         ###############################################
#         ### least-square method
#         ###############################################
#         ww = np.transpose(ww)

#         coeffprior = np.asarray(lstsq(ww, bb, rcond=None)[0])

#         ################################################
#         ### first reult with averaing information
#         ################################################
#         offcenter = np.int_(((2 * off + 1) * (2 * off + 1) - 1) / 2)
#         fd = np.asarray([[1, 4, 7, 4, 1], [4, 16, 26, 16, 4], [7, 26, 41, 26, 7], [4, 16, 26, 16, 4], [1, 4, 7, 4, 1]])
#         fd = np.reshape(fd, -1) * 1.0

#         coeffprior = np.asarray(coeffprior)
#         ct1 = np.asarray([np.sum(coeffprior[:part] * x[:part, j]) for j in range(25)])
#         ct2 = np.asarray([np.sum(coeffprior[part:2 * part] * x[:part, j]) for j in range(25)])
#         indnew = ind * (ct2 < radiance_max_threshold) * (ct2 > radiance_min_threshold) * \
#                  (ct1 > radiance_min_threshold) * (ct1 < radiance_max_threshold)
#         apoint = np.sum(indnew)
#         if (apoint <= 1):
#             cd1 = np.sum(coeffprior[:part] * x[:, offcenter])
#             cd2 = np.sum(coeffprior[part:] * x[:, offcenter])
#             ctprior = np.transpose(np.matrix([cd1, cd2]))
#         else:
#             fd[indnew] = fd[indnew] / np.sum(fd[indnew])

#             cd1new = np.sum(ct1[indnew] * fd[indnew])
#             cd2new = np.sum(ct2[indnew] * fd[indnew])
#             ctprior = np.transpose(np.matrix([cd1new, cd2new]))
#         # component_temperature = inv_planck(wl, ctprior)
#         #################################################
#         ### second result by combining one-point result
#         #################################################

#         nl1 = kk - off_
#         nl2 = kk + off_ + 1
#         w1 = wNLine[:,nl1:nl2, 2]
#         w1 = np.asarray(np.reshape(w1, (number_component, -1)))
#         w2 = wOLine[:,nl1:nl2, 2]
#         w2 = np.asarray(np.reshape(w2, (number_component, -1)))
#         b1 = (np.reshape(radNLine[nl1:nl2,2], -1))
#         b2 = (np.reshape(radOLine[nl1:nl2,2], -1))
#         w = np.hstack((w1, w2))
#         b = np.hstack((b1, b2))
#         w = np.transpose(w)

#         #################################################
#         ### least-squared method
#         #################################################
#         # coeffprior = np.asarray(lstsq(w, b)[0])
#         # coeffprior_point = np.asarray(lstsq(w, b)[0])
#         # component_temperature_point = inv_planck(wl, coeffprior_point)
#         # result_point[:, kk] = [component_temperature_point[0], component_temperature_point[1]]

#         #################################################
#         ### Bayes method
#         #################################################

#         w = np.matrix(w)
#         b = np.matrix(b)
#         b = np.transpose(b)

#         Cd = np.matrix(np.diag(np.ones(number_component)) * sensor_noise)
#         Cm = np.diag([soil_radiance_variance, leaf_radiance_variance])
#         pre = np.linalg.inv(np.transpose(w) * np.linalg.inv(Cd) * w + np.linalg.inv(Cm))
#         coeff = pre * (np.transpose(w) * np.linalg.inv(Cd) * b + np.linalg.inv(Cm) * ctprior)
#         ### another solution for using priori information
#         # coeff = ctprior + np.transpose(Cd * np.transpose(w) * pre) * (b - np.transpose(w) * ctprior)
#         component_radiance = np.asarray(coeff)

#         if (np.min(component_radiance) < radiance_min_threshold): continue
#         if (np.max(component_radiance) > radiance_max_threshold): continue

#         component_temperature = inv_planck(wl, component_radiance)

#         result[:, kk] = [component_temperature[0][0], component_temperature[1][0]]

#     return result


####### 多线程计算两组分
####### 输入：nadir和oblique两个角度的地表温度，土壤发射率、植被发射率、nadir和obliqu两个角度的植被覆盖度fvc
# def inv_mpl_agl_multiple_2(lst_n, lst_o,emis_s, emis_v, fvcN, fvcO, wl=10.8):
#     radiance_max_threshold = 20
#     radiance_min_threshold = 4.5
#     temperature_max_threshold = 350
#     temperature_min_threshold = 250
#     default_nan_temperature = 0
#     soil_radiance_variance = 2
#     leaf_radiance_variance = 1
#     # sensor_noise = 0.05
#     pure_soil_threshold = 0.01
#     pure_leaf_threshold = 0.99
#     fvc_max_threshold = 0.99
#     fvc_min_threshold = 0.01
#     fd0 = np.asarray([[1, 4, 7, 4, 1], [4, 16, 26, 16, 4], [7, 26, 41, 26, 7], [4, 16, 26, 16, 4], [1, 4, 7, 4, 1]])
#     number_component = 2
#     number_angle = 2
#     number_value_threshold = 12
#     off = 2
#     off_ = 0

#     start = time.time()
#     [nl, ns] = np.shape(lst_n)
#     result = np.zeros([2,nl,ns])

#     ###### fvc LAI 根据LAI计算得到的fvc，为此函数的输入项
#     fvc_n = fvcN * 1.0
#     fvc_n[fvc_n > fvc_max_threshold] = fvc_max_threshold
#     fvc_n[fvc_n < fvc_min_threshold] = fvc_min_threshold

#     fvc_o = fvcO * 1.0
#     fvc_o[fvc_o > fvc_max_threshold] = fvc_max_threshold
#     fvc_o[fvc_o < fvc_min_threshold] = fvc_min_threshold

#     ###### the radiance 根据fvc和植被土壤的发射率计算像元的有效发射率，加上反演得到的地表温度计算像元的能量
#     rad_n = planck(wl, lst_n)
#     rad_n = rad_n * (fvc_n * emis_v + (1 - fvc_n) * emis_s)
#     rad_o = planck(wl, lst_o)
#     rad_o = rad_o * (fvc_o * emis_v + (1 - fvc_o) * emis_s)

#     ###### component effective emissivity matrix 组分有效发射率，分别对应光土壤，植被
#     wN = np.asarray([emis_s * (1 - fvc_n) , emis_v * (fvc_n)])
#     wO = np.asarray([emis_s * (1 - fvc_o) , emis_v * (fvc_o)])

#     mask = np.zeros([nl,ns])
#     ind0 = (fvc_n > pure_soil_threshold) * (fvc_n < pure_leaf_threshold) * \
#            (rad_n > radiance_min_threshold) * (rad_n < radiance_max_threshold) * \
#            (rad_o > radiance_min_threshold) * (rad_o < radiance_max_threshold)
#     mask[ind0] = 1

#     para = []
#     # for kn in range(off, nl-off):
#     #     ###### 取wN的所有组分的5行，列全部，进行多线程的操作, 5行为多像元反演组分温度时候所用到的
#     #     wNLine = wN[:,kn-off: kn + off + 1, :]
#     #     wOLine = wO[:, kn - off: kn + off + 1, :]
#     #     radNLine = rad_n[kn-off:kn+off+1, : ]
#     #     radOLine = rad_o[kn-off:kn+off+1, : ]
#     #     maskLine = mask[kn-off: kn + off+1, : ]
#     #     para.append([wNLine, wOLine, radNLine, radOLine, maskLine, ns])

#     for kn in range(off, ns-off):
#         ###### 取wN的所有组分的5行，列全部，进行多线程的操作, 5行为多像元反演组分温度时候所用到的
#         wNLine = wN[:,:,kn-off: kn + off + 1]
#         wOLine = wO[:,:, kn - off: kn + off + 1]
#         radNLine = rad_n[:,kn-off:kn+off+1 ]
#         radOLine = rad_o[:,kn-off:kn+off+1]
#         maskLine = mask[:,kn-off: kn + off+1 ]
#         para.append([wNLine, wOLine, radNLine, radOLine, maskLine, nl])

#     tasks= []
#     pool = Pool(min(64,cpu_count()))
#     print('cpu_count',cpu_count())
#     for p in para:
#         tasks.append(pool.apply_async(doMultiple_line_inv_2_s, (p,)))
#     pool.close()
#     pool.join()
#     results = [task.get() for task in tasks]
#     end = time.time()
#     results = np.asarray(results)
#     resultForm = np.asarray([results[:,0,:], results[:,1,:]])
#     resultForm = np.transpose(resultForm)
#     print('time cost: ', end - start, 's')
#     return resultForm

#     # ppp = doMultiple_line_inv_2_s(para[0])
#     # ppp1 = doMultiple_line_inv_2_s(para[10])
#     # return 1






















