# from utils.multiple_lsct import *
from utils.old.util_lsct import *
import warnings
warnings.filterwarnings("ignore")
from utils.old.util_constant import *

def inv_lsct2_ang_pixel


def line_inv_2_s(wNLine, wOLine, radNLine, radOLine, maskLine,nl = 1024):
    '''
    this is for the sample rec
    '''
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

    result = np.zeros([number_component,nl])
    result_point = np.zeros([number_component, nl])

    off = 2
    for kk in range(off, nl-off):
        maskk = maskLine[kk,2]
        if maskk == 0: continue

        nl1 = kk - off
        nl2 = kk + off + 1
        ###### w1是nadir，w2是oblique
        w1 = wNLine[:,nl1:nl2,:]
        w1 = np.asarray(np.reshape(w1, (number_component, -1)))
        w2 = wOLine[:, nl1:nl2, :]
        w2 = np.asarray(np.reshape(w2, (number_component, -1)))

        bb1 = (np.reshape(radNLine[nl1:nl2, :], -1))
        bb2 = (np.reshape(radOLine[nl1:nl2, :], -1))

        mask = np.reshape(maskLine[nl1:nl2, :], -1)
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

        nl1 = kk - off_
        nl2 = kk + off_ + 1
        w1 = wNLine[:,nl1:nl2, 2]
        w1 = np.asarray(np.reshape(w1, (number_component, -1)))
        w2 = wOLine[:,nl1:nl2, 2]
        w2 = np.asarray(np.reshape(w2, (number_component, -1)))
        b1 = (np.reshape(radNLine[nl1:nl2,2], -1))
        b2 = (np.reshape(radOLine[nl1:nl2,2], -1))
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