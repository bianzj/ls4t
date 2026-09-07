from base.util_packages import *
from base.util_lst import *


def find_hot_cold_line(ndvi,lst,lu=3,ld=3,M=20,N=5):
    '''
    按照方差确定有效数据
    :param ndvi: 植被指数
    :param lst: 地表温度
    :param lu: 上边界方差倍数
    :param ld: 下边界方差倍数
    :param M: 大分类
    :param N: 大分类的小分类
    :return:
    '''
    ind = (~np.isnan(ndvi)) * (~np.isnan(lst))
    ndvi = ndvi[ind]
    lst = lst[ind]
    ind = (ndvi > 0.01) * (lst < 360) * (ndvi < 1.0) * (lst > 275)
    ndvi = ndvi[ind]
    lst = lst[ind]

    ndvimin = np.min(ndvi)
    ndvimax = np.max(ndvi)
    ndvistep = (ndvimax - ndvimin) / M * 1.0

    lstmax_value = np.zeros(M)
    lstmin_value = np.zeros(M)
    ndvi_value = np.zeros(M)

    ### obtian a general result
    ok_maxtemp_ = np.ones([M, N])
    ok_mintemp_ = np.ones([M, N])
    lstmax_temp_ = np.ones([M, N])
    lstmin_temp_ = np.ones([M, N])
    ndvi_temp_ = np.ones([M, N])
    for k in range(M):
        ndvi1 = ndvimin + k * ndvistep
        ndvi2 = ndvi1 + ndvistep
        ind = (ndvi < ndvi2) * (ndvi >= ndvi1)
        lst_interval = lst[ind]
        ndvi_interval = ndvi[ind]
        ndvistepnew = (ndvi2 - ndvi1) / N

        for kk in range(N):
            ndvi11 = ndvi1 + kk * ndvistepnew
            ndvi22 = ndvi11 + ndvistepnew
            ind0 = (ndvi_interval >= ndvi11) * (ndvi_interval < ndvi22)
            temp1 = np.average(lst_interval[ind0])

            temp2 = np.std(lst_interval[ind0])
            temp3 = temp2
            # ind = ind0*(lst_interval>temp1)
            # temp2 = np.std(lst_interval[ind])
            # ind = ind0 * (lst_interval < temp1)
            # temp3 = np.std(lst_interval[ind])

            ind = (lst_interval <= temp1 + lu * temp2) * (lst_interval >= temp1 - ld * temp3) * ind0
            if np.sum(ind) <=0:continue
            ndvi_temp_[k][kk] = (ndvi11 + ndvi22) / 2.0
            lstmax_temp_[k][kk] = np.max(lst_interval[ind])
            lstmax_temp_[k][kk] = np.max(lst_interval[ind])

            lstmin_temp_[k][kk] = np.min(lst_interval[ind])

    ### obtain the linear regresion for warm line
    for k in range(M):
        if np.sum(ok_maxtemp_[k]) <= 2: continue
        lstave = np.average(lstmax_temp_[k])
        lststd = np.std(lstmax_temp_[k])
        ind = lstmax_temp_[k] < lstave - lststd
        ok_maxtemp_[k][ind] = 0
        ind = ok_maxtemp_[k] == 1
        lstmax_value[k] = (np.average(lstmax_temp_[k][ind]))
        ndvi_value[k] = (np.average(ndvi_temp_[k]))

    ind = (~np.isnan(ndvi_value)) * (~np.isnan(lstmax_value))*(lstmax_value>250)
    fmax = np.polyfit(ndvi_value[ind], lstmax_value[ind], 1)
    lstmax_value_ref = np.polyval(fmax, ndvi_value)
    rmse = np.sqrt(np.average(np.power(lstmax_value[ind] - lstmax_value_ref[ind], 2)))
    lstmax_temp_ref_ = np.polyval(fmax, ndvi_temp_)
    for k_iter in range(N):
        for k in range(M):
            if np.sum(ok_maxtemp_[k]) <= 2: continue
            ndvi_temp = ndvi_temp_[k]
            lstmax_temp = lstmax_temp_[k]
            lstmax_temp_ref = lstmax_temp_ref_[k]
            ind = np.abs(lstmax_temp - lstmax_temp_ref) > 3 * rmse
            ok_maxtemp_[k][ind] = 0
            ind = ok_maxtemp_[k] == 1
            lstmax_value[k] = (np.average(lstmax_temp_[k][ind]))
            ndvi_value[k] = (np.average(ndvi_temp_[k][ind]))
        ind = (~np.isnan(ndvi_value)) * (~np.isnan(lstmax_value))*(lstmax_value>250)
        fmax = np.polyfit(ndvi_value[ind], lstmax_value[ind], 1)
        lstmax_value_ref = np.polyval(fmax, ndvi_value)
        rmse = np.sqrt(np.average(np.power(lstmax_value[ind] - lstmax_value_ref[ind], 2)))
        lstmax_temp_ref_ = np.polyval(fmax, ndvi_temp_)

    ### obtain the linear regresion for cold line
    for k in range(M):
        if np.sum(ok_mintemp_[k]) <= 2: continue
        lstave = np.average(lstmin_temp_[k])
        lststd = np.std(lstmin_temp_[k])
        ind = lstmin_temp_[k] > lstave + lststd
        ok_mintemp_[k][ind] = 0
        ind = ok_mintemp_[k] == 1
        lstmin_value[k] = (np.average(lstmin_temp_[k][ind]))
        ndvi_value[k] = (np.average(ndvi_temp_[k][ind]))

    ind = (~np.isnan(ndvi_value)) * (~np.isnan(lstmin_value))*(lstmin_value>250)
    fmin = np.polyfit(ndvi_value[ind], lstmin_value[ind], 1)
    lstmin_value_ref = np.polyval(fmin, ndvi_value)
    rmse = np.sqrt(np.average(np.power(lstmin_value[ind] - lstmin_value_ref[ind], 2)))
    lstmin_temp_ref_ = np.polyval(fmin, ndvi_temp_)
    for k_iter in range(N):
        for k in range(M):
            if np.sum(ok_mintemp_[k]) <= 2: continue
            ndvi_temp = ndvi_temp_[k]
            lstmin_temp = lstmin_temp_[k]
            lstmin_temp_ref = lstmin_temp_ref_[k]
            ind = np.abs(lstmin_temp - lstmin_temp_ref) > 3 * rmse
            ok_mintemp_[k][ind] = 0
            ind = ok_mintemp_[k] == 1
            lstmin_value[k] = (np.average(lstmin_temp_[k][ind]))
            ndvi_value[k] = (np.average(ndvi_temp_[k]))
        ind = (~np.isnan(ndvi_value)) * (~np.isnan(lstmin_value))*(lstmin_value>250)
        fmin = np.polyfit(ndvi_value[ind], lstmin_value[ind], 1)
        lstmin_value_ref = np.polyval(fmin, ndvi_value)
        rmse = np.sqrt(np.average(np.power(lstmin_value[ind] - lstmin_value_ref[ind], 2)))
        lstmin_temp_ref_ = np.polyval(fmin, ndvi_temp_)

    return ndvi_value,lstmax_value,fmax,lstmin_value,fmin


def find_hot_cold_line_condition(ndvi,lst,percent = 0.05, M=20,N=5):
    '''
    按照百分比确定有效数据
    :param ndvi: 植被指数
    :param lst: 温度
    :param percent: 消除奇异值 0.05
    :param M: 大分类
    :param N: 大分类的小分类
    :return:
    '''
    ind = (~np.isnan(ndvi)) * (~np.isnan(lst))
    ndvi = ndvi[ind]
    lst = lst[ind]
    ind = (ndvi > 0.01) * (lst < 330) * (ndvi < 1.0) * (lst > 275)
    ndvi = ndvi[ind]
    lst = lst[ind]

    ndvimin = np.min(ndvi)
    ndvimax = np.max(ndvi)
    ndvistep = (ndvimax - ndvimin) / M * 1.0

    lstmax_value = np.zeros(M)
    lstmin_value = np.zeros(M)
    ndvi_value = np.zeros(M)

    ### obtian a general result
    ok_maxtemp_ = np.ones([M, N])
    ok_mintemp_ = np.ones([M, N])
    lstmax_temp_ = np.ones([M, N])
    lstmin_temp_ = np.ones([M, N])
    ndvi_temp_ = np.ones([M, N])
    for k in range(M):
        ndvi1 = ndvimin + k * ndvistep
        ndvi2 = ndvi1 + ndvistep
        ind = (ndvi < ndvi2) * (ndvi >= ndvi1)
        lst_interval = lst[ind]
        ndvi_interval = ndvi[ind]
        ndvistepnew = (ndvi2 - ndvi1) / N

        for kk in range(N):
            ndvi11 = ndvi1 + kk * ndvistepnew
            ndvi22 = ndvi11 + ndvistepnew
            ind0 = (ndvi_interval >= ndvi11) * (ndvi_interval < ndvi22)
            temp1 = np.average(lst_interval[ind0])

            temp2 = np.std(lst_interval[ind0])
            temp3 = temp2*1.0
            # ind = ind0*(lst_interval>temp1)
            # temp2 = np.std(lst_interval[ind])
            # ind = ind0 * (lst_interval < temp1)
            # temp3 = np.std(lst_interval[ind])

            ind = (lst_interval <= (temp1 + 3.0 * temp2)) * (lst_interval >= (temp1 - 3.0 * temp3)) * ind0
            if np.sum(ind) <=0:continue
            ndvi_temp_[k][kk] = (ndvi11 + ndvi22) / 2.0
            lstmax_temp_[k][kk] = np.percentile(lst_interval[ind],100-percent)
            lstmin_temp_[k][kk] = np.percentile(lst_interval[ind],percent)

    ### obtain the linear regresion for warm line
    for k in range(M):
        if np.sum(ok_maxtemp_[k]) <= 3: continue
        lstave = np.average(lstmax_temp_[k])
        lststd = np.std(lstmax_temp_[k])
        ind = lstmax_temp_[k] < lstave - lststd
        ok_maxtemp_[k][ind] = 0
        ind = ok_maxtemp_[k] == 1
        lstmax_value[k] = (np.average(lstmax_temp_[k][ind]))
        ndvi_value[k] = (np.average(ndvi_temp_[k]))

    ind = (~np.isnan(ndvi_value)) * (~np.isnan(lstmax_value))*(lstmax_value>250)
    fmax = np.polyfit(ndvi_value[ind], lstmax_value[ind], 1)
    lstmax_value_ref = np.polyval(fmax, ndvi_value)
    rmse = np.sqrt(np.average(np.power(lstmax_value[ind] - lstmax_value_ref[ind], 2)))
    lstmax_temp_ref_ = np.polyval(fmax, ndvi_temp_)
    for k_iter in range(N):
        for k in range(M):
            if np.sum(ok_maxtemp_[k]) <= 3: continue
            ndvi_temp = ndvi_temp_[k]
            lstmax_temp = lstmax_temp_[k]
            lstmax_temp_ref = lstmax_temp_ref_[k]
            ind = np.abs(lstmax_temp - lstmax_temp_ref) > 2 * rmse
            ok_maxtemp_[k][ind] = 0
            ind = ok_maxtemp_[k] == 1
            lstmax_value[k] = (np.average(lstmax_temp_[k][ind]))
            ndvi_value[k] = (np.average(ndvi_temp_[k][ind]))
        ind = (~np.isnan(ndvi_value)) * (~np.isnan(lstmax_value))*(lstmax_value>250)
        fmax = np.polyfit(ndvi_value[ind], lstmax_value[ind], 1)
        lstmax_value_ref = np.polyval(fmax, ndvi_value)
        rmse = np.sqrt(np.average(np.power(lstmax_value[ind] - lstmax_value_ref[ind], 2)))
        lstmax_temp_ref_ = np.polyval(fmax, ndvi_temp_)

    ### obtain the linear regresion for cold line
    for k in range(M):
        if np.sum(ok_mintemp_[k]) <= 3: continue
        lstave = np.average(lstmin_temp_[k])
        lststd = np.std(lstmin_temp_[k])
        ind = lstmin_temp_[k] > lstave + lststd
        ok_mintemp_[k][ind] = 0
        ind = ok_mintemp_[k] == 1
        lstmin_value[k] = (np.average(lstmin_temp_[k][ind]))
        ndvi_value[k] = (np.average(ndvi_temp_[k][ind]))

    ind = (~np.isnan(ndvi_value)) * (~np.isnan(lstmin_value))*(lstmin_value>250)
    fmin = np.polyfit(ndvi_value[ind], lstmin_value[ind], 1)
    lstmin_value_ref = np.polyval(fmin, ndvi_value)
    rmse = np.sqrt(np.average(np.power(lstmin_value[ind] - lstmin_value_ref[ind], 2)))
    lstmin_temp_ref_ = np.polyval(fmin, ndvi_temp_)
    for k_iter in range(N):
        for k in range(M):
            if np.sum(ok_mintemp_[k]) <= 3: continue
            ndvi_temp = ndvi_temp_[k]
            lstmin_temp = lstmin_temp_[k]
            lstmin_temp_ref = lstmin_temp_ref_[k]
            ind = np.abs(lstmin_temp - lstmin_temp_ref) > 2 * rmse
            ok_mintemp_[k][ind] = 0
            ind = ok_mintemp_[k] == 1
            lstmin_value[k] = (np.average(lstmin_temp_[k][ind]))
            ndvi_value[k] = (np.average(ndvi_temp_[k]))
        ind = (~np.isnan(ndvi_value)) * (~np.isnan(lstmin_value))*(lstmin_value>250)
        fmin = np.polyfit(ndvi_value[ind], lstmin_value[ind], 1)
        lstmin_value_ref = np.polyval(fmin, ndvi_value)
        rmse = np.sqrt(np.average(np.power(lstmin_value[ind] - lstmin_value_ref[ind], 2)))
        lstmin_temp_ref_ = np.polyval(fmin, ndvi_temp_)

    return ndvi_value,lstmax_value,fmax,lstmin_value,fmin

