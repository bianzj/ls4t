from matplotlib.transforms import offset_copy
from base.util_constant import *
from base.util_file import *
from base.util_data import *
from base.util_packages import *
from multiprocessing import Pool, freeze_support, cpu_count


'''
多线程 按列跑示例
推荐每列或每行一个进程
'''
def fun(n,m,ws,wl,w,b,mask,lst):
    return 

if __name__ == '__main__':
    nl, ns = 43520, 512
    n,m = 2,3
    ws = 5
    off = ws // 2
    wl = 10.8

    b = np.zeros([nl,ns,m])
    w = np.zeros([nl,ns,n,m])
    mask = np.zeros([nl,ns,n])
    lst = np.zeros([nl,ns,n])
    
    ### From here ###
    para = []
    for kn in range(off, ns-off):
        wLine = w[:,kn-off:kn+off+1,:,:]
        bLine = b[:,kn-off:kn+off+1,:]
        maskLine = mask[:,kn-off:kn+off+1,:]
        lstLine = lst[:,kn-off:kn+off+1,:]
        para.append([n,m,ws,wl,wLine,bLine,maskLine,lstLine])
    tasks= []
    pool = Pool(min(192,cpu_count()))
    tasks = [pool.apply_async(fun, tuple(p)) for p in para]
    pool.close()
    pool.join()
    results = [t.get() for t in tasks]

    lsct = np.zeros((nl, ns, m))
    for idx, res in enumerate(results):
        kn = idx + off
        # 如果 res 形状是 (nl, m)，直接赋值
        lsct[:, kn, :] = res

