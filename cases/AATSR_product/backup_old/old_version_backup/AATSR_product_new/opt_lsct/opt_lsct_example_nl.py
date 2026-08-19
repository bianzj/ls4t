from utils.old.util_lsct import *
import time

'''
组分温度反演样例
'''

'''case 1 hom'''
'''替换成自己的数据'''
np.random.seed(42)
wl = 10.8
nl,ns = 43520, 51
'''无误差'''
Tsl = np.full([nl,ns],310.0)
Tsh = np.full([nl,ns],305)
Tvl = np.full([nl,ns],300.0)
Tvh = np.full([nl,ns],300.0)

emisS = np.random.normal(loc=0.95, scale=0.01, size=(nl, ns))
emisV = np.random.normal(loc=0.98, scale=0.01, size=(nl, ns))
vzaN = np.random.uniform(0.0, 15, (nl, ns))
vzaF = np.random.normal(loc=55.0, scale=0.5, size=(nl, ns))
vaaN = np.random.uniform(0.0, 360, (nl, ns))
vaaF = np.random.uniform(0.0, 30, (nl, ns))

sza1 = np.linspace(55, 10, num=nl * ns // 2)
sza2 = np.linspace(10, 55, num=nl * ns // 2)
sza = np.concatenate((sza1, sza2)).reshape(nl, ns)
saa = np.linspace(120,240,num=nl * ns).reshape(nl,ns)

hspot = 0.2
lai = np.random.uniform(0.5, 5.0, (nl, ns))

BTN = sample_hom_bt(Tsl,Tsh,Tvl,Tvh,lai,hspot,wl,emisS,emisV,vzaN,sza,np.abs(saa-vaaN))
BTF = sample_hom_bt(Tsl,Tsh,Tvl,Tvh,lai,hspot,wl,emisS,emisV,vzaF,sza,np.abs(saa-vaaF))

'''开始反演'''
start_time = time.time()
# 计算能量
radN = planck(wl,BTN)
radF = planck(wl,BTF)

# 计算有效发射率
wN,psoil = cal_effective_emissivity_hom(lai,hspot,wl,emisS,emisV,vzaN,sza,vaaN,saa,3)
wF,psoil = cal_effective_emissivity_hom(lai,hspot,wl,emisS,emisV,vzaF,sza,vaaF,saa,3)

# mask 异常值
rad_th_max, rad_th_min = 20, 4.5
maskN = (radN > rad_th_min) * (radN < rad_th_max)
maskF = (radF > rad_th_min) * (radF < rad_th_max)
DT = np.ones_like(radN)

# 反演方法：
# 两角度 5 像元  -> 三组分解 -> 两组分解
window_size = 5
off = int((window_size - 1) / 2)
para = []
results = np.zeros([5,nl,ns])
for kn in range(off, ns - off):
    ###### 取wN的所有组分的n列，行全部，进行多线程的操作
    wNLine = np.transpose(wN[:,:, kn - off: kn + off + 1],(0,2,1))
    wOLine = np.transpose(wF[:, :,kn - off: kn + off + 1],(0,2,1))
    radNLine = np.transpose(radN[:,kn - off:kn + off + 1],(1,0))
    radOLine = np.transpose(radF[:,kn - off:kn + off + 1],(1,0))
    maskNLine = np.transpose(maskN[:,kn - off: kn + off + 1],(1,0))
    maskOLine = np.transpose(maskF[:,kn - off: kn + off + 1],(1,0))
    psoilLine = np.transpose(psoil[:,kn - off: kn + off + 1],(1,0))
    DTLine = np.transpose(DT[:,kn - off:kn + off + 1],(1,0))
    '''调试用,非多线程'''
    # results[:,kn,:] = inv_lsct3_AATSR_line(wNLine, wOLine, radNLine, radOLine, maskNLine, maskOLine, psoilLine,DTLine, nl)
    '''多线程'''
    para.append([wNLine, wOLine, radNLine, radOLine, maskNLine, maskOLine, psoilLine,DTLine, nl])
tasks = []
pool = Pool(min(24, cpu_count()))
for p in para:
    tasks.append(pool.apply_async(doMultiple_line_inv_3_AATSR, (p,)))
pool.close()
pool.join()
results = np.array([task.get() for task in tasks])
results_transposed = np.transpose(results, (1, 2, 0))
results = np.zeros((5, nl, ns))
results[:, :,2:-2] = results_transposed

Tsl_inv = results[0,:,:]
Tsh_inv = results[1,:,:]
Tv_inv = results[2,:,:]
Ts_b_inv = results[3,:,:]
Tv_b_inv = results[4,:,:]


'''简单精度验证'''
invalid_num = np.sum(np.abs(Tsl_inv - Tsl) < 10)
bias, rmse, r2 = cal_rmse_r2(Tsl, Tsl_inv)
print(f"Tsl(bias,rmse,r2): {bias:.3f}, {rmse:.3f}, {r2[1]:.3f}, invalid_num: {invalid_num}")

invalid_num = np.sum(np.abs(Tsh_inv - Tsh) < 10)
bias, rmse, r2 = cal_rmse_r2(Tsh, Tsh_inv)
print(f"Tsh(bias,rmse,r2): {bias:.3f}, {rmse:.3f}, {r2[1]:.3f}, invalid_num: {invalid_num}")

Ts = psoil * planck(wl, Tsl) + (1 - psoil) * planck(wl, Tsh)
Ts = inv_planck(wl, Ts)
Ts_inv = psoil * planck(wl, Tsl_inv) + (1 - psoil) * planck(wl, Tsh_inv)
Ts_inv = inv_planck(wl, Ts_inv)

invalid_num = np.sum(np.abs(Ts_inv - Ts) < 10)
bias, rmse, r2 = cal_rmse_r2(Ts, Ts_inv)
print(f"Ts(bias,rmse,r2): {bias:.3f}, {rmse:.3f}, {r2[1]:.3f}, invalid_num: {invalid_num}")

invalid_num = np.sum(np.abs(Tvl - Tv_inv) < 10)
bias, rmse, r2 = cal_rmse_r2(Tvl, Tv_inv)
print(f"Tv(bias,rmse,r2): {bias:.3f}, {rmse:.3f}, {r2[1]:.3f}, invalid_num: {invalid_num}")

Ts_b = psoil * planck(wl, Tsl) + (1 - psoil) * planck(wl, Tsh)
Ts_b = inv_planck(wl, Ts_b)
invalid_num = np.sum(np.abs(Ts_b_inv - Ts_b) < 10)
bias, rmse, r2 = cal_rmse_r2(Ts_b, Ts_b_inv)
print(f"Ts_b(bias,rmse,r2): {bias:.3f}, {rmse:.3f}, {r2[1]:.3f}, invalid_num: {invalid_num}")

invalid_num = np.sum(np.abs(Tvl - Tv_b_inv) < 10)
bias, rmse, r2 = cal_rmse_r2(Tvl, Tv_b_inv)
print(f"Tv_b(bias,rmse,r2): {bias:.3f}, {rmse:.3f}, {r2[1]:.3f}, invalid_num: {invalid_num}")

end_time = time.time()
elapsed_time = end_time - start_time
print(f"运行时间: {elapsed_time:.4f} 秒")