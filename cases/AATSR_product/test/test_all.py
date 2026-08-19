import sys
sys.path.append('/home/hero/code/AATSR_product')
from util.util_ls4t import *

'''2025.9.11'''
'''所有代码测试'''
def initial_para():
    n ,m = 2,2 # 角度数，组分数
    nl,ns = 4352,51 # 行列数
    Tsl = np.full((nl,ns),315)
    Tsh = np.full((nl,ns),315)
    Tvl = np.full((nl,ns),300)
    Tvh = np.full((nl,ns),300)
    hspot = 1.0
    wl = 10.8
    lai = np.random.uniform(0.1, 5.0, size=(nl, ns))
    emisS = np.random.uniform(0.92, 0.95, size=(nl, ns))  # 土壤发射率
    emisV = np.random.uniform(0.95, 0.97, size=(nl, ns))  # 植被发射率
    vza = np.random.uniform(0, 70, size=(nl,ns,n))
    vaa = np.random.uniform(0, 360, size=(nl,ns,n))
    sza = np.full((nl,ns,n),45)
    saa = np.full((nl,ns,n),180)
    mask = np.full((nl,ns,n),1)
    return n,m,nl,ns,Tsl,Tsh,Tvl,Tvh,lai,hspot,wl,emisS,emisV,vza,sza,vaa,saa, mask

if __name__ == '__main__':
    import time

    '''A.生成区域代码 测试'''
    n,m,nl,ns,Tsl,Tsh,Tvl,Tvh,lai,hspot,wl,emisS,emisV,vza,sza,vaa,saa,mask = initial_para()
    
    print("图像开始生成...")
    start_time = time.time()
    bt,w = generate_hom_Nangle_Mcomponent_mlt(n,m,nl,ns,Tsl,Tsh,Tvl,Tvh,lai,hspot,wl,emisS,emisV,vza,sza,vaa,saa,ifmlt=1)
    lst = np.zeros([nl,ns,n])
    for i in range(n):
        lst[:,:,i] = cal_lst_from_bt(bt[:,:,i],wl,lai,vza[:,:,i],emisS,emisV)
    end_time = time.time()
    
    # print("\n测试结果:")
    # print(bt.shape,w.shape)
    # print(bt,w)
    print(f"\n执行时间: {end_time - start_time:.4f}秒")


    '''B. 反演代码 测试'''
    b= planck(wl,bt)
    # 1. 测试单点代码
    print("开始单点反演...")
    start_time = time.time()
    result = np.zeros([nl,ns,m])
    for i in range(nl):
        for j in range(ns):
            if np.sum(mask[i,j,:]) >= n:
                p = fitting_Nangle_Mcomponent_point(w[i,j,:,:],b[i,j,:],n,m,method = 'ls')
                result[i,j,:] = p
    lsct = inv_planck(wl,result)
    print(lsct)
    end_time = time.time()
    print(f"\n执行时间: {end_time - start_time:.4f}秒")

    # # 2. 测试窗口代码
    # print("开始窗口反演...")
    # start_time = time.time()
    # result = np.zeros([nl,ns,m])

    # ws = 5
    # off = ws//2
    # weights = set_weights(ws)

    # for i in range(off,nl-off):
    #     for j in range(off,ns-off):
    #         if np.sum(mask[i,j,:]) >= n:
    #             w_win = w[i-off:i+off+1,j-off:j+off+1,:,:]
    #             b_win = b[i-off:i+off+1,j-off:j+off+1,:]
    #             mask_win = mask[i-off:i+off+1,j-off:j+off+1,:]
    #             lst_win = lst[i-off:i+off+1,j-off:j+off+1,:]

    #             if_constraint = True
    #             if not if_constraint: # 结果正确性约束，约等于无约束
    #                 constraints = {
    #                     'type': 'ineq',  # 不等式约束
    #                     'fun': constraint_func_Nangle,
    #                     'args': (lst_win, ws, wl)  # 注意是元组
    #                 }

    #             elif m == 2:
    #                 # 两组分温差约束
    #                 d = [-5,30]
    #                 constraints = {
    #                     'type': 'ineq',  # 不等式约束
    #                     'fun': constraint_func_Nangle_2component,
    #                     'args': (lst_win, d,ws, wl)  # 注意是元组
    #                 }
    #             elif m == 3:
    #                 # 三组分温差约束
    #                 d12 = [0,30]
    #                 d23 = [-10,10]
    #                 constraints = {
    #                     'type': 'ineq',  # 不等式约束
    #                     'fun': constraint_func_Nangle_3component,
    #                     'args': (lst_win, d12,d23,ws, wl)  # 注意是元组
    #                 }

    #                 x0,bounds = set_x0_bnds_Nangle_Mcomponent(lst,n,m,ws=5)

    #             p = fitting_Nangle_Mcomponent_window(w_win,b_win,n,m,mask_win,weights,constraints,x0,bounds,ws,method='SLSQP')
    #             result[i,j,:] = p
    # lsct = inv_planck(wl,result)
    # print(lsct[:,:,0])
    # print(lsct[:,:,1])
    # print(lsct[:,:,2])
    # # print(lsct[:,:,3])
    # end_time = time.time()
    # print(f"\n执行时间: {end_time - start_time:.4f}秒")