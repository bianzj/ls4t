import sys
sys.path.append('/home/hero/code/AATSR_product')
from util.util_ls4t import *

# def inv_lsct_Nangle_Mcomponent_window(n,m,w,b,wl,method='ls'):


if __name__ == '__main__':
    '''读取数据'''
    n,m,nl,ns = 3,3,5,5
    infile = outfile = r'/home/hero/code/AATSR_product/test/data/test_%01dangele_%01dcomponent_%d_%d.h5' % (n,m,nl,ns)
    name_list = ['n','m','nl','ns','Tsl','Tsh','Tvl','Tvh','lai','hspot','wl','emisS','emisV','vza','sza','vaa','saa','mask','bt','w','lst']
    n,m,nl,ns,Tsl,Tsh,Tvl,Tvh,lai,hspot,wl,emisS,emisV,vza,sza,vaa,saa,mask,bt,w,lst = read_h5py_items(infile,name_list)

    b = planck(wl,bt)


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
    #                 d23 = [-15,15]
    #                 constraints = {
    #                     'type': 'ineq',  # 不等式约束
    #                     'fun': constraint_func_Nangle_3component,
    #                     'args': (lst_win, d12,d23,ws, wl)  # 注意是元组
    #                 }

    #             x0,bounds = set_x0_bnds_Nangle_Mcomponent(lst_win,n,m,ws=5)

    #             p = fitting_Nangle_Mcomponent_window(w_win,b_win,n,m,mask_win,weights,constraints,x0,bounds,ws,method='SLSQP')
    #             result[i,j,:] = p
    # lsct = inv_planck(wl,result)
    # for i in range(m):
    #     print(np.mean(lsct[:,:,i][lsct[:,:,i] != 0]))
    # end_time = time.time()
    # print(f"\n执行时间: {end_time - start_time:.4f}秒")