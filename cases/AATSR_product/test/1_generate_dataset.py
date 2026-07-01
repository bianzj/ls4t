import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../../../')))
from base.util_lsct import *
from base.util_constant import *
from base.util_file import *
from base.util_data import *
from cases.AATSR_product.util.util_aatsr import *
import numpy as np
import time
from concurrent.futures import ThreadPoolExecutor, as_completed

'''2025.9.25'''
'''生成测试数据'''
def initial_para():
    n ,m = 2,4 # 角度数，组分数
    nl,ns = 5,5 # 行列数
    Tsl = np.full((nl,ns),315)
    Tsh = np.full((nl,ns),295)
    Tvl = np.full((nl,ns),300)
    Tvh = np.full((nl,ns),300)
    hspot = 1.0
    wl = 10.8
    lai = np.random.uniform(0.5, 5.0, size=(nl, ns))
    emisS = np.random.uniform(0.92, 0.95, size=(nl, ns))  # 土壤发射率
    emisV = np.random.uniform(0.93, 0.97, size=(nl, ns))  # 植被发射率
    vza = np.random.uniform(0, 70, size=(nl,ns,n))
    vaa = np.random.uniform(0, 360, size=(nl,ns,n))
    sza = np.full((nl,ns,n),30)
    saa = np.full((nl,ns,n),180)
    mask = np.full((nl,ns,n),1)  # mask = np.random.randint(0, 2, (nl,ns,n)) 
    return n,m,nl,ns,Tsl,Tsh,Tvl,Tvh,lai,hspot,wl,emisS,emisV,vza,sza,vaa,saa, mask

if __name__ == '__main__':
    import time

    '''A.生成区域代码 测试'''
    n,m,nl,ns,Tsl,Tsh,Tvl,Tvh,lai,hspot,wl,emisS,emisV,vza,sza,vaa,saa,mask = initial_para()
    
    print("图像开始生成...")
    start_time = time.time()
    bt,w = generate_hom_Nangle_Mcomponent_mlt(n,m,nl,ns,Tsl,Tsh,Tvl,Tvh,lai,hspot,wl,emisS,emisV,vza,sza,vaa,saa,ifmlt=0)
    lst = np.zeros([nl,ns,n])
    for i in range(n):
        lst[:,:,i] = cal_lst_from_bt(bt[:,:,i],wl,lai,vza[:,:,i],emisS,emisV)
    end_time = time.time()
    
    # bt_test = np.zeros([nl,ns,n])
    # for i in range(n):
    #     bt_test[:,:,i] = inv_planck(wl,cal_rad_from_lst(lst[:,:,i],wl,lai,vza[:,:,i],emisS,emisV))
    # print(bt-bt_test)
    
    # print("\n测试结果:")
    # print(bt.shape,w.shape)
    # print(bt,w)
    print(f"\n执行时间: {end_time - start_time:.4f}秒")

    outfile = r'/home/hero/code/AATSR_product/test/data/test_%01dangele_%01dcomponent_%d_%d.h5' % (n,m,nl,ns)
    name_list = ['n','m','nl','ns','Tsl','Tsh','Tvl','Tvh','lai','hspot','wl','emisS','emisV','vza','sza','vaa','saa','mask','bt','w','lst']
    data_list = [n,m,nl,ns,Tsl,Tsh,Tvl,Tvh,lai,hspot,wl,emisS,emisV,vza,sza,vaa,saa,mask,bt,w,lst]
    dtype_list = ['int','int','int','int','float','float','float','float','float','float','float','float','float','float','float','float','float','float','float','float','float']
    write_h5py_file(outfile,name_list,data_list,dtype_list,compression='gzip',ifcover=1)