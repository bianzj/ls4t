import os
import sys
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))
from base.util_lsct.packages import *
from base.util_lsct.fitting import *

'''
lsct_inv
组分温度反演方法
Nangle_Mcomponent_point/window_Constraints
'''
def fitting_Nangle_Mcomponent_point(w,b,n,m,method='ridge'):
    '''
    多角度 多组分 点
    :param w: 有效发射率矩阵, shape (n,m)
    :param b: 亮温矩阵, shape (n,)
    :param n: 角度数
    :param m: 组分数
    :param method: 线性求解方法 ridge、lasso、bayesianridge、ls
    :return: p： 组分能量，shape (m,)
    '''
    w , b = np.asarray(w), np.asarray(b)
    if w.shape[0]!=n or w.shape[1]!=m:
        print('Error: w shape is not match n angles and m components')
        return -1
    if b.shape[0]!=n:
        print('Error: b shape is not match n angles')
        return -1
    if method in ['ridge','lasso','bayesianridge']:
        p = fitting_unknown_linear_sklearn(b,w,method=method)
    elif method =='ls':
        p = fitting_unknown_linear_ls(b,w)
    return p


def fitting_Nangle_Mcomponent_window(w,b,n,m,mask,weight,constraints,x0,bounds,window_size =5,method='SLSQP'):
    '''
    多角度 多组分 窗口
    :param w: 有效发射率矩阵 shape(ws,ws,n,m) ws:窗口大小
    :param b: 亮温矩阵 shape(ws,ws,n)
    :param mask: 窗口掩码,能反演是1，不能是0 shape(ws,ws,n)
    :param n: 角度数
    :param m: 组分数
    :param window_size: 窗口大小
    :param method: 非线性求解方法 BFGS/powell/SLSQP/L-BFGS-B/TNC
    :return: p： 组分能量 shape(nl,ns,m）
    '''
    ws = window_size
    w, b, mask = np.asarray(w), np.asarray(b), np.asarray(mask)
    if w.shape[0]!=ws or w.shape[1]!=ws or w.shape[2]!=n or w.shape[3]!=m:
        print('Error: w shape is not match window size * window size *  n angles * m components')
        return -1
    if b.shape[0]!=ws or b.shape[1]!=ws or b.shape[2]!=n:
        print('Error: b shape is not match window size * window size * n angles')
        return -1
    if mask.shape[0]!=ws or mask.shape[1]!=ws or mask.shape[2]!=n:
        print('Error: mask shape is not match window size * window size * n angles')
        return -1

    w = w.reshape(-1,m)
    b = b.reshape(-1)
    # 将mask沿角度维度重复n次
    # mask = np.tile(mask.reshape(-1,1), (1,n)).reshape(-1)
    mask = mask.astype(bool)
    mask = mask.reshape(-1)
    weight = weight.reshape(-1)
    weight = np.tile(weight.reshape(-1,1), (1,n)).reshape(-1)

    num_val_point = np.sum(mask)
    if num_val_point < 2 * m:
        return np.full((m,), np.nan)
    
    # 将weights应用于mask区域
    masked_weights = weight[mask]
    
    def objective_func(x, y, A, xn, weight):
        residuals = np.dot(A, x) - y
        return np.sum(weight * residuals**2)
        
    x = fitting_unknown_nonlinear_min(objective_func,
                                    b[mask],
                                    w[mask],
                                    m,
                                    x0,
                                    bounds,
                                    method=method,
                                    constraints=constraints,
                                    weight=masked_weights)  # 使用关键字参数传入权重
    return x