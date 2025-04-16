from scipy.optimize import minimize
from scipy.optimize import lsq_linear
import numpy as np
from util.rt.crown import *
from util.rt.hom import *
from util.util import *

'''planck'''
rd = np.pi/180.0
planck_c1 = 11910.439340652
planck_c2 = 14388.291040407
temperature_threshold = 100
temperature_zero = 273.15
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
        # if (Ts < temperature_threshold): Ts = Ts + temperature_zero
        wavelength = np.float(wavelength)
        Ts = np.float(Ts)
        rad = c1 / (np.power(wavelength, 5) * (np.exp(c2 / Ts / wavelength) - 1)) * 10000
    else:
        # Ts[Ts < temperature_threshold] = Ts[Ts < temperature_threshold] + temperature_zero
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

'''交叉校正'''
def read_comma_separated_txt(file_path):
    data = []
    with open(file_path, 'r') as file:
        for line in file:
            # 使用逗号(',')分割每一行的数据
            parts = line.strip().split(',')
            # 提取数值并将它们转换为浮点数
            values = [float(part) for part in parts]
            data.append(values)
    return np.array(data)

def cross_correction(lst,coeff_dir,mode):
    '''
    交叉校正
    :param lst:待校正LST
    :param coeff_dir:系数地址
    :param mode: 正反
    :return: 矫正后lst
    '''
    coeff = read_comma_separated_txt(coeff_dir)
    tem_min = coeff[:,0]
    tem_max = coeff[:,1]
    a = coeff[:,2]
    b = coeff[:,3]
    if mode ==1:
        b = -b/a
        a = 1/a
    lst_result = np.zeros_like(lst)
    for i in range(len(a)):
        ind = (lst>=tem_min[i])*(lst<tem_max[i])
        if np.sum(ind) == 0: continue
        lst_result[ind] = lst[ind]*a[i]+b[i]
    return lst_result


'''正向模型'''
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

def sample_crown_BT(lai, hspot,stand,rcr,hcr,wavelength, emissivity_soil, emissivity_leaf,vza, sza, raa,Tsl,Tsh,Tvl,Tvh):
    '''1.initial'''
    crown = Crown()
    '''2.set variables'''
    crown.set_structure(lai, hspot, stand, hcr, rcr)
    crown.set_optical(wavelength, emissivity_soil, emissivity_leaf)
    crown.set_angle(vza, sza, raa)
    crown.set_thermal(Tsl,Tsh,Tvl,Tvh)
    ''''3.run'''
    BT = crown.run()
    vza[raa == 180] = vza[raa == 180] * -1
    return BT

def sample_hom_BT(lai, hspot,wavelength, emissivity_soil, emissivity_leaf,vza, sza, raa,Tsl,Tsh,Tvl,Tvh):
    '''1.initial'''
    hom = Hom()
    '''2.set variables'''
    hom.set_structure(lai, hspot)
    hom.set_optical(wavelength, emissivity_soil, emissivity_leaf)
    hom.set_angle(vza, sza, raa)
    hom.set_thermal(Tsl,Tsh,Tvl,Tvh)
    ''''3.run'''
    BT = hom.run()
    vza[raa == 180] = vza[raa == 180] * -1
    return BT


'''初值'''
'''线性优化'''
def objective_function_2_2(x,w,y):
    a11,a12,a21,a22 = w[0,0],w[0,1],w[1,0],w[1,1]
    y1,y2 = y[0],y[1]
    return abs(a11 * x[0] + a12 * x[1] - y1)**2 + abs(a21 * x[0] + a22 * x[1] - y2)**2

def objective_function_2_3(x,w,y,x_2):
    a11, a12,  a31, a32, a33 = w[0, 0], w[0, 1],  w[2, 0], w[2, 1], w[2, 2]
    y1, y2, y3 = y[0], y[1], y[2]
    xs, xv = x_2[0],x_2[1]
    return abs(a11 * x[0] + a12 * x[1] -(a11 + a12)* xs)  + abs(a31 * x[0] + a32 * x[1] + a33 * xv - y3)

def objective_function_3_2(x,w,y):
    a11,a12,a21,a22,a31,a32 = w[0,0],w[0,1],w[1,0],w[1,1],w[2,0],w[2,1]
    y1,y2,y3 = y[0],y[1],y[2]
    return abs(a11 * x[0] + a12 * x[1] - y1) + abs(a21 * x[0] + a22 * x[1] - y2) + abs(a31 * x[0] + a32 * x[1] - y3)

def objective_function_3_3(x,w,y):
    a11,a12,a13,a21,a22,a23,a31,a32,a33 = w[0,0],w[0,1],w[0,2],w[1,0],w[1,1],w[1,2],w[2,0],w[2,1],w[2,2]
    y1,y2,y3 = y[0],y[1],y[2]
    return abs(a11 * x[0] + a12 * x[1] + a13 * x[2]- y1) + abs(a21 * x[0] + a22 * x[1]+ a23 * x[2] - y2) + abs(a31 * x[0] + a32 * x[1]+ a33 * x[2] - y3)

def solve_initial_2(radN, radO, radM, w1, w2, w3,Ts_min,Ts_max,Tv_min,Tv_max,Ts_Tv_min,Ts_Tv_max):
    '''
    假设植被温度和土壤温度相等，解初值
    :param lstN:垂直温度
    :param lstO: 倾斜
    :param lstM: 静止
    :param w1: 垂直
    :param w2: 倾斜
    :param w3: 静止
    :return: 初解
    '''
    wl = 10.8
    # 只用两个角度解：
    w = np.zeros([2, 2])
    w[0, 0] = w1[0] + w1[1]
    w[0, 1] = w1[2]
    w[1, 0] = w2[0] + w2[1]
    w[1, 1] = w2[2]
    b = np.array([radN,radO])
    # b = np.array([radN * (w[0,0]+w[0,1]), radO* (w[1,0]+w[1,1])])
    coeff = np.asarray(lstsq(w, b, rcond=None))[0]
    lstN = inv_planck(wl,radN)

    if Ts_max==0:
        '''范围限制'''
        Ts_min = lstN -2
        Ts_max = lstN + 30
        Tv_min = lstN -15
        Tv_max = lstN + 5
        '''温差限制'''
        Ts_Tv_min = -5
        Ts_Tv_max = 30

    '''范围限制'''
    Ts_min = lstN +Ts_min
    Ts_max = lstN + Ts_max
    Tv_min = lstN +Tv_min
    Tv_max = lstN +Tv_max


    constraints = (
        {'type': 'ineq', 'fun': lambda x: x[0] - x[1] - (planck(wl,lstN+Ts_Tv_min)-planck(wl,lstN))},
        {'type': 'ineq', 'fun': lambda x: (planck(wl, lstN + Ts_Tv_max) - planck(wl, lstN))-x[0] + x[1]},
    )

    # {'type': 'ineq', 'fun': lambda x: x[0] - x[1] - 0.5},

    # initial_guess = [planck(10.8,300), planck(10.8,290)]
    initial_guess = [planck(wl, (lstN+10)), planck(wl, (lstN-10))]
    bounds = [[planck(wl,Ts_min),planck(wl,Ts_max)],[planck(wl,Tv_min),planck(wl,Tv_max)]]

    # 使用minimize函数求解优化问题
    # methods: COBYLA L-BFGS-B trust-constr SLSQP
    result = minimize(objective_function_2_2, initial_guess,args=(w,b), constraints=constraints, bounds = bounds, method='SLSQP')

    # 输出结果
    print("初值:%.2f  %.2f"%(inv_planck(wl,result.x[0]),inv_planck(wl,result.x[1])))
    print("最小值 =", result.fun)
    return [result.x[0],result.x[1]]


def solve_initial_3_2(rad, w,Ts_Tv_range):
    '''
    三个角度求两个组分温度
    :param lstN:垂直温度
    :param lstO: 倾斜
    :param lstM: 静止
    :param w1: 垂直
    :param w2: 倾斜
    :param w3: 静止
    :return: 初解
    '''
    wl = 10.8

    '''第一次求初值，获取植被和平均土壤温度'''
    b = rad
    coeff = np.asarray(lstsq(w, b, rcond=None))[0]
    Ts_Tv_min = Ts_Tv_range[0]
    Ts_Tv_max = Ts_Tv_range[1]

    lstN = inv_planck(wl,np.max(w))


    constraints = (
        {'type': 'ineq', 'fun': lambda x: x[0] - x[1] - (planck(wl,lstN+Ts_Tv_min)-planck(wl,lstN))},
        {'type': 'ineq', 'fun': lambda x: (planck(wl, lstN + Ts_Tv_max) - planck(wl, lstN))-x[0] + x[1]},
        # {'type': 'ineq', 'fun': lambda x: x[0] - planck(wl,Ts_min)},
        # {'type': 'ineq', 'fun': lambda x: planck(wl,Ts_max) - x[0] },
        # {'type': 'ineq', 'fun': lambda x: x[1] - planck(wl,Tv_min)},
        # {'type': 'ineq', 'fun': lambda x: planck(wl,Tv_max) - x[1]}
    )


    initial_guess = np.asarray(lstsq(w, b, rcond=None))[0]

    # 使用minimize函数求解优化问题
    result = minimize(objective_function_3_2, initial_guess, method='SLSQP',args=(w,b), constraints=constraints)
    return [result.x[0],result.x[1]]


def solve_initial_3_old(radN, radO, radM, w1, w2, w3,Tsl_min,Tsl_max,Tsh_min,Tsh_max,Tv_min,Tv_max,Tsl_Tsh_min,Tsl_Tsh_max,Tsh_Tv_min ,Tsh_Tv_max):
    '''
    线性优化直接解光照、阴影土壤和植被温度
    :param lstN:垂直温度
    :param lstO: 倾斜
    :param lstM: 静止
    :param w1: 垂直
    :param w2: 倾斜
    :param w3: 静止
    :return: 初解
    '''
    wl = 10.8
    # 只用两个角度解：
    w = np.zeros([3, 3])
    w = np.array([w1,w2,w3])

    b = np.array([radN,radO,radM])
    # b = np.array([radN * (w[0,0]+w[0,1]), radO* (w[1,0]+w[1,1])])
    # coeff = np.asarray(lstsq(w, b, rcond=None))[0]
    lstN = np.max([inv_planck(wl,radN),inv_planck(wl,radO),inv_planck(wl,radM)])

    if Tsl_min + Tsl_max ==0:
        '''范围限制'''
        Tsl_min = lstN + 5
        Tsl_max = lstN + 30
        Tsh_min = lstN - 10
        Tsh_max = lstN + 5
        Tv_min = lstN - 10
        Tv_max = lstN + 5
        '''温差限制'''
        Tsl_Tsh_min = 10
        Tsl_Tsh_max = 30
        Tsh_Tv_min = -5
        Tsh_Tv_max = 5

    Tsl_min = lstN + Tsl_min
    Tsl_max = lstN + Tsl_max
    Tsh_min = lstN + Tsh_min
    Tsh_max = lstN + Tsh_max
    Tv_min = lstN + Tv_min
    Tv_max = lstN + Tv_max

    constraints = (
        {'type': 'ineq', 'fun': lambda x: x[0] - x[1] - (planck(wl,lstN + Tsl_Tsh_min)-planck(wl,lstN))},
        {'type': 'ineq', 'fun': lambda x: (planck(wl, lstN + Tsl_Tsh_max) - planck(wl, lstN))-x[0] + x[1]},
        {'type': 'ineq', 'fun': lambda x: (x[1] - x[2] - (planck(wl, lstN + Tsh_Tv_min) - planck(wl, lstN)))},
        {'type': 'ineq', 'fun': lambda x: (planck(wl, lstN + Tsh_Tv_max) - planck(wl, lstN)) - x[1] + x[2]}
    )
    # {'type': 'ineq', 'fun': lambda x: x[0] - planck(wl, Tsl_min)},
    # {'type': 'ineq', 'fun': lambda x: planck(wl, Tsl_max) - x[0]},
    # {'type': 'ineq', 'fun': lambda x: x[1] - planck(wl, Tsh_min)},
    # {'type': 'ineq', 'fun': lambda x: planck(wl, Tsh_max) - x[1]},
    # {'type': 'ineq', 'fun': lambda x: x[2] - planck(wl, Tv_min)},
    # {'type': 'ineq', 'fun': lambda x: planck(wl, Tv_max) - x[2]},
    # methods: COBYLA L-BFGS-B trust-constr SLSQP
    bounds = [[planck(wl,Tsl_min),planck(wl,Tsl_max)],[planck(wl,Tsh_min),planck(wl,Tsh_max)],[planck(wl,Tv_min),planck(wl,Tv_max)]]

    # {'type': 'ineq', 'fun': lambda x: x[0] - x[1] - 0.5},

    # initial_guess = [planck(10.8,300), planck(10.8,290)]
    # initial_guess = [planck(wl, (lstN+15)), planck(wl, (lstN-10)), planck(wl, (lstN-5))]
    initial_guess = [planck(wl, (315)), planck(wl, (300)), planck(wl, (303))]

    # 使用minimize函数求解优化问题 # SLSQP trust-constr
    # methods: COBYLA L-BFGS-B trust-constr SLSQP
    result = minimize(objective_function_3_3, initial_guess,args=(w,b), constraints=constraints,bounds = bounds, method='trust-constr')

    # 输出结果
    print("初值:%.2f  %.2f %.2f"%(inv_planck(wl,result.x[0]),inv_planck(wl,result.x[1]),inv_planck(wl,result.x[2])))
    print("最小值 =", result.fun)
    return [result.x[0],result.x[1],result.x[2]]


def solve_initial_3(rad, w,Tsl_Tsh_range,Tsh_Tv_range):
    '''
    线性优化直接解光照、阴影土壤和植被温度
    '''
    wl = 10.8
    b = rad

    Tsl_Tsh_min = Tsl_Tsh_range[0]
    Tsl_Tsh_max = Tsl_Tsh_range[1]
    Tsh_Tv_min = Tsh_Tv_range[0]
    Tsh_Tv_max = Tsh_Tv_range[1]

    lstN = inv_planck(wl,np.max(w))

    constraints = (
        {'type': 'ineq', 'fun': lambda x: x[0] - x[1] - (planck(wl,lstN + Tsl_Tsh_min)-planck(wl,lstN))},
        {'type': 'ineq', 'fun': lambda x: (planck(wl, lstN + Tsl_Tsh_max) - planck(wl, lstN))-x[0] + x[1]},
        {'type': 'ineq', 'fun': lambda x: (x[1] - x[2] - (planck(wl, lstN + Tsh_Tv_min) - planck(wl, lstN)))},
        {'type': 'ineq', 'fun': lambda x: (planck(wl, lstN + Tsh_Tv_max) - planck(wl, lstN)) - x[1] + x[2]}
    )

    # methods: COBYLA L-BFGS-B trust-constr SLSQP

    # {'type': 'ineq', 'fun': lambda x: x[0] - x[1] - 0.5},
    initial_guess = np.asarray(lstsq(w, b, rcond=None))[0]

    # 使用minimize函数求解优化问题 # SLSQP trust-constr
    # methods: COBYLA L-BFGS-B trust-constr SLSQP
    result = minimize(objective_function_3_3, initial_guess,args=(w,b), constraints=constraints, method='SLSQP')

    # # 输出结果
    # print("初值:%.2f  %.2f %.2f"%(inv_planck(wl,result.x[0]),inv_planck(wl,result.x[1]),inv_planck(wl,result.x[2])))
    # print("残差最小值 =", result.fun)
    return [result.x[0],result.x[1],result.x[2]]


'''组分温度反演'''
'''反演方法'''
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
    elif method == 'lasso':
        lasso = LassoCV(alphas=alphas, fit_intercept=False, cv=3)  # Adjust the number of folds here
        lasso.fit(A, y)
        coeffs = lasso.coef_
    elif method =='bayesianridge':
        clf = BayesianRidge(fit_intercept=False)
        clf.fit(A,y)
        coeffs = clf.coef_

    return coeffs


def SVD_bayesian(A,b,x0,times=3):
    '''基于贝叶斯理论的初值SVD分解'''
    U, s, VT = np.linalg.svd(A)
    V = VT.T
    Sigma = np.zeros(np.shape(A))
    Sigma[:len(s), :len(s)] = np.diag(s)
    s = np.diag(s)

    b = b.reshape([-1,1])
    p0 = x0.reshape([-1,1])
    # pm = np.asarray(lstsq(A, b, rcond=None))[0]
    pm = np.asarray((lsq_linear(A, b.reshape(-1), bounds=(5,25))).x)
    pm = pm.reshape([-1,1])
    # print(inv_planck(10.8,pm))
    # print("模型解为：" )
    # print((inv_planck(10.8, pm)))

    temp1 = dot(V, np.linalg.inv((dot(s, s) + np.identity(s.shape[0]))))
    temp2 = dot(dot(dot(s, s), VT), pm) + dot(VT, p0)
    p = dot(temp1 ,temp2)
    # print(inv_planck(10.8,p))

    for i in range(times):
        temp1 = dot(V.T, np.linalg.inv((dot(s, s) + np.identity(s.shape[0]))))
        temp2 = dot(dot(Sigma.T, U.T), b-dot(A,p)) + dot(V, p0-p)
        detap = dot(temp1,temp2)
        p = p+detap
        # print(i,inv_planck(10.8,p))
    return p

def SVD_bayesian_Truncated(A,b,x0,kmin,times=10):
    '''SVD分解'''
    U, s, VT = np.linalg.svd(A)

    '''根据条件数判断留奇异值个数'''
    # print(s[0],s[1],s[2])
    s_sum = np.sum(s)
    s_add = 0
    k = 0
    while s_add/s_sum < 0.990:
        s_add = s_add + s[k]
        k=k+1
    if k<kmin: k=kmin
    # print("保留%01d个奇异值，前后条件数为%03f，%03f"%(k,s[0]/s[-1],s[0]/s[k-1]))
    U_ = np.matrix(U[:, :k])
    s_ = np.matrix(np.diag(s[0:k]))
    VT_ = np.matrix(VT[:k, :])
    A_ = U_ * s_ * VT_

    # x_ = np.asarray(lstsq(A_, b, rcond=None))[0]
    p0 = x0.reshape([-1,1])
    pm = np.asarray(lstsq(A_, b, rcond=None))[0]
    print("模型解为：%.2f  %.2f"% (inv_planck(10.8, pm[0]), inv_planck(10.8, pm[1])))

    # temp1 = dot(V_.T, np.linalg.inv((dot(s_, s_) + np.identity(s_.shape[0]))))
    # temp2 = dot(dot(dot(s_, s_), V_), pm) + dot(V_, p0)
    # s= np.matrix(np.diag(s))
    # temp1 = dot(VT.T, np.linalg.inv((dot(s, s) + np.identity(s.shape[0]))))
    # temp2 = dot(dot(dot(s, s), VT), pm) + dot(VT, p0)
    # p = dot(temp1 , temp2)

    temp1 = dot(VT_.T, np.linalg.inv((dot(s_, s_) + np.identity(s_.shape[0]))))
    temp2 = dot(dot(dot(s_, s_), VT_), pm) + dot(VT_, p0)
    p = dot(temp1,  temp2)

    for i in range(times):
        temp1 = dot(VT_.T, np.linalg.inv((dot(s_, s_) + np.identity(s_.shape[0]))))
        temp2 = dot(dot(s_, U_.T), b - A_ * p) + dot(VT_, p0 - p)
        detap = temp1 * temp2
        p = p + detap
    return p

def inv_lsct2_site(radN,radO,w1,w2,imagex_,imagey_,methodname=0,x0=np.zeros(3),wl=10.8):
    '''
    两角度反演两组分
    :param radN:
    :param radO:
    :param w1:
    :param w2:
    :param imagex_:
    :param imagey_:
    :param methodname:
    :param x0:
    :param wl:
    :return:
    '''
    '''调整数据'''
    if isinstance(radN, (list, np.ndarray)) and len(radN)>1:
        [nl, ns] = np.shape(radN)
        radN = radN[imagex_,imagey_]
        radO = radO[imagex_,imagey_]
        w1 = w1[:,imagex_,imagey_]
        w2 = w2[:,imagex_,imagey_]

    b1 = np.reshape(radN,(1,1))
    b2 = np.reshape(radO, (1, 1))
    w1 = np.reshape(w1,(1,2))
    w2 = np.reshape(w2, (1, 2))

    w_ = np.vstack((w1, w2))  # 2*2
    b = np.vstack((b1, b2))  # 2*1
    w = w_
    # w[:,0] = w_[:,0] +w_[:,1]
    # w[:,1] = w_[:,2]
    # w[:,0] = w1
    # w[:,1] = w2

    '''给初值'''
    x0 = np.array(x0)
    lst_max = inv_planck(wl, np.max(b))
    if np.sum(x0) == 0:
        x0 = np.reshape(planck(wl, np.array([lst_max + 10, lst_max - 10])), (2, 1))

    '''反演'''
    # 0（最小二乘）
    # 1 TSVD_Bayesian (截断SVD+贝叶斯)
    if methodname == 0:
        coeff = np.asarray(lstsq(w, b, rcond=None))[0]
    if methodname == 1 or methodname == 'TSVD_Bayesian':
        kmin = 2
        # if (np.average(w[:,0])<=0.1) + (np.average(w[:,0])<=0.1) + (np.average(w[:,0])<=0.1): kmin=3
        coeff = SVD_bayesian_Truncated(w, b, x0, kmin)
    lsct = inv_planck(wl, coeff)
    return lsct

def inv_lsct3_site(radN: object, radO: object, radM: object, w1: object, w2: object, w3: object, imagex_: object, imagey_: object, methodname: object = 0, x0: object = np.zeros(3), wl: object = 10.8) -> object:
    '''
    考虑热点，反演组分温度
    :rtype: object
    :param radN: 垂直方向辐射 nl*ns
    :param radO: 倾斜 nl*ns
    :param radM: 静止 nl*ns
    :param w1: 有效发射率 3* nl*ns
    :param w2: 有效发射率 3* nl*ns
    :param w3: 有效发射率 3* nl*ns
    :param imagex_: 要反演的坐标x,1个值
    :param imagey_:  要反演的坐标y，1个值
    :param methodname: 反演方法
    :param x0: 初值
    :param wl: 中心波长
    :return: 组分温度
    '''
    '''调整数据'''
    if isinstance(radN, (list, np.ndarray)) and len(radN)>1:
        [nl, ns] = np.shape(radN)
        [nl_g, ns_g] = np.shape(radM)
        if nl != nl_g:
            radM = resize_data(radM, nl, ns, method=cv2.INTER_NEAREST)
        radN = radN[imagex_,imagey_]
        radO = radO[imagex_,imagey_]
        radM = radM[imagex_,imagey_]
        w1 = w1[:,imagex_,imagey_]
        w2 = w2[:,imagex_,imagey_]
        w3 = w3[:,imagex_,imagey_]

    b1 = np.reshape(radN,(1,1))
    b2 = np.reshape(radO, (1, 1))
    b3 = np.reshape(radM, (1, 1))
    w1 = np.reshape(w1,(1,3))
    w2 = np.reshape(w2, (1, 3))
    w3 = np.reshape(w3, (1, 3))

    w = np.vstack((w1, w2, w3))  # 3*3
    b = np.vstack((b1, b2, b3))  # 3*1

    '''给初值'''
    x0 = np.array(x0)
    lst_max = inv_planck(wl,np.max(b))
    if np.sum(x0)==0:
        x0 = np.reshape(planck(wl,np.array([lst_max+10,lst_max-10,lst_max-5])),(3,1))

    '''反演'''
    # 0（最小二乘）
    # 1 TSVD_Bayesian (截断SVD+贝叶斯)
    if methodname==0:
        coeff = np.asarray(lstsq(w, b, rcond=None))[0]
    if methodname ==1 or methodname=='SVD_b':
        coeff = SVD_bayesian(w, b, x0)
    if methodname==2 or methodname=='TSVD_b':
        kmin = 2
        # if (np.average(w[:,0])<=0.1) + (np.average(w[:,0])<=0.1) + (np.average(w[:,0])<=0.1): kmin=3
        coeff = SVD_bayesian_Truncated(w, b, x0,kmin)

    lsct = inv_planck(wl, coeff)
    return lsct


'''带约束线性方程组求解'''
def fitting_linear_constraint_3angle_3component(w,b,deta12,deta23):
    number_component = 3
    sunlit_soil_radiance_variance = 2
    shaded_soil_radiance_variance = 2
    leaf_radiance_variance = 10
    sensor_noise = [5,5,1]

    def constraint_func(x, lstN, deta12_min, deta12_max, deta23_min, deta23_max):
        # 计算每个约束条件的值
        constraint1 = -deta12_min + (x[0] - x[1])
        constraint2 = deta12_max - (x[0] - x[1])
        constraint3 = -deta23_min + (x[1] - x[2])
        constraint4 = deta23_max - (x[1] - x[2])
        constraint5 = -deta12_min + (x[0] - x[2])
        return [constraint1, constraint2, constraint3, constraint4, constraint5]

    def objective_func(x, w, b):
        return np.linalg.norm(np.dot(w.T, x) - b)
    lstN = inv_planck(10.8,np.max(b))
    deta12_min = planck(10.8,lstN + deta12[0]/2) -planck(10.8,lstN - deta12[0]/2)
    deta12_max = planck(10.8,lstN + deta12[1]/2) - planck(10.8,lstN- deta12[1]/2)
    deta23_min = planck(10.8,lstN + deta23[0]/2) - planck(10.8,lstN- deta23[0]/2)
    deta23_max = planck(10.8,lstN + deta23[1]/2) - planck(10.8,lstN- deta23[1]/2)

    # 定义约束条件
    constraints = {'type': 'ineq', 'fun': constraint_func,
                   'args': (lstN, deta12_min, deta12_max, deta23_min, deta23_max)}

    x0 = np.array([lstN, lstN-10, lstN])
    x0 = planck(10.8,x0)
    wl = 10.8
    bounds = [[planck(wl, lstN), planck(wl, lstN + 30)], [planck(wl, lstN - 20), planck(wl, lstN + 20)],
              [planck(wl, lstN - 20), planck(wl, lstN + 20)]]
    # SLSQP  trust-constr
    result = minimize(objective_func, x0, args=(w, b),constraints=constraints,bounds = bounds,method ='trust-constr')

    p0 = result.x

    # Bayesian
    w = np.matrix(w)
    w = np.transpose(w)
    b = np.matrix(b)
    p0 = np.matrix(p0)
    Cd = np.matrix(np.diag(np.ones(number_component)) * sensor_noise)
    Cm = np.diag([sunlit_soil_radiance_variance,shaded_soil_radiance_variance, leaf_radiance_variance])
    pre = np.linalg.inv(np.transpose(w) * np.linalg.inv(Cd) * w + np.linalg.inv(Cm))
    coeff = pre * (np.transpose(w) * np.linalg.inv(Cd) * np.reshape(b,(3,1)) + np.linalg.inv(Cm) * np.reshape(p0,(3,1)))
    return coeff

def fitting_linear_constraint_3angle_3component_window(w,b,deta12,deta23):
    number_component = 3
    number_angle = 3
    number_observation = 3*3
    sunlit_soil_radiance_variance = 10
    shaded_soil_radiance_variance = 5
    leaf_radiance_variance = 5
    sensor_noise = 0.25
    ws = 3

    def constraint_func(x, lstN, deta12_min, deta12_max, deta23_min, deta23_max):
        # 计算每个约束条件的值
        constraint1 = -deta12_min + (x[0] - x[1])
        constraint2 = deta12_max - (x[0] - x[1])
        constraint3 = -deta23_min + (x[1] - x[2])
        constraint4 = deta23_max - (x[1] - x[2])
        return [constraint1, constraint2, constraint3, constraint4]

    def objective_func(x, w, b):
        return np.linalg.norm(np.dot(w, x) - b)
    lstN = inv_planck(10.8,np.max(b))
    deta12_min = planck(10.8,lstN +  deta12[0]/2) -planck(10.8,lstN - deta12[0]/2)
    deta12_max = planck(10.8,lstN + deta12[1]/2) - planck(10.8,lstN- deta12[1]/2)
    deta23_min = planck(10.8,lstN + deta23[0]/2) - planck(10.8,lstN- deta23[0]/2)
    deta23_max = planck(10.8,lstN + deta23[1]/2) - planck(10.8,lstN- deta23[1]/2)

    # 定义约束条件
    constraints = {'type': 'ineq', 'fun': constraint_func,
                   'args': (lstN, deta12_min, deta12_max, deta23_min, deta23_max)}

    x0 = np.array([lstN, lstN-10, lstN])
    x0 = planck(10.8,x0)
    wl = 10.8
    bounds = [[planck(wl, lstN-3), planck(wl, lstN + 30)], [planck(wl, lstN - 20), planck(wl, lstN + 20)],
              [planck(wl, lstN - 20), planck(wl, lstN + 20)]]
    # SLSQP  trust-constr
    result = minimize(objective_func, x0, args=(w, b),constraints=constraints,bounds = bounds,method ='SLSQP')

    p0 = result.x

    # Bayesian 12 13 14
    w_p = w.reshape((ws*ws,number_angle,number_component))
    w_p = np.matrix(w_p[4,:,:])
    w_p = np.transpose(w_p)
    b_p = b.reshape((ws*ws,number_angle))
    b_p = np.matrix(b_p[4,:])
    p0 = np.matrix(p0)
    Cd = np.matrix(np.diag(np.ones(number_component)) * sensor_noise)
    Cm = np.diag([sunlit_soil_radiance_variance,shaded_soil_radiance_variance, leaf_radiance_variance])
    pre = np.linalg.inv(np.transpose(w_p) * np.linalg.inv(Cd) * w_p + np.linalg.inv(Cm))
    coeff = pre * (np.transpose(w_p) * np.linalg.inv(Cd) * np.reshape(b_p,(3,1)) + np.linalg.inv(Cm) * np.reshape(p0,(3,1)))
    return coeff

def fitting_linear_constraint_3angle_2component(w,b,deta12):
    number_component = 2
    number_angle = 3
    soil_radiance_variance = 10
    leaf_radiance_variance = 5
    sensor_noise = 0.25

    def constraint_func(x, lstN, deta_min, deta_max):
        # 计算每个约束条件的值
        constraint1 = -deta_min + (x[0] - x[1])
        constraint2 = deta_max - (x[0] - x[1])
        return [constraint1, constraint2]
    def objective_func(x, w, b):
        return np.linalg.norm(np.dot(w.T, x) - b)
    lstN = inv_planck(10.8,np.max(b))
    deta_min = planck(10.8,lstN +  deta12[0]/2) -planck(10.8,lstN - deta12[0]/2)
    deta_max = planck(10.8,lstN + deta12[1]/2) - planck(10.8,lstN- deta12[1]/2)

    constraints = {'type': 'ineq', 'fun': constraint_func,
                   'args': (lstN, deta_min, deta_max)}

    wl = 10.8


    x0 = np.array([lstN+5, lstN-5])
    x0 = planck(10.8,x0)
    # SLSQP  trust-constr
    result = minimize(objective_func, x0, args=(w, b),constraints=constraints,method ='trust-constr')

    p0 = result.x

    # Bayesian
    w = np.matrix(w)
    w = np.transpose(w)
    b = np.matrix(b)
    p0 = np.matrix(p0)
    Cd = np.matrix(np.diag(np.ones(number_angle)) * sensor_noise)
    Cm = np.diag([soil_radiance_variance, leaf_radiance_variance])
    pre = np.linalg.inv(np.transpose(w) * np.linalg.inv(Cd) * w + np.linalg.inv(Cm))
    coeff = pre * (np.transpose(w) * np.linalg.inv(Cd) * np.reshape(b,(3,1)) + np.linalg.inv(Cm) * np.reshape(p0,(2,1)))
    return coeff


def Bayesian_Hotspot_Simulation():
    return 0