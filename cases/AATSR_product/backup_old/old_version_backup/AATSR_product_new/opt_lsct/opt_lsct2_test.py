from utils.old.util_lsct import *

'''
10.29
组分温度代码正确性测试
'''

'''case 1 hom'''
np.random.seed(42)

wl = 10.8
nl,ns = 52, 12
'''无误差'''
# Tsl = np.full([nl,ns],310.0)
# Tsh = np.full([nl,ns],305)
# Tvl = np.full([nl,ns],300.0)
# Tvh = np.full([nl,ns],300.0)
'''添加临近像元组分温度偏差'''
area_std = 2.0
Tsl = np.random.normal(loc=310, scale=area_std, size = [nl, ns])
Tsh = Tsl
Tvl = np.random.normal(loc=300, scale=area_std, size = [nl, ns])
Tvh = Tvl

emisS = np.random.normal(loc=0.95, scale=0.01, size=(nl, ns))
emisV = np.random.normal(loc=0.98, scale=0.01, size=(nl, ns))
emisS[emisS>1]=1
emisV[emisV>1]=1
vzaN = np.random.uniform(0.0, 15, (nl, ns))
vzaF = np.random.normal(loc=55.0, scale=0.5, size=(nl, ns))
vaaN = np.random.uniform(0.0, 360, (nl, ns))
vaaF = np.random.uniform(0.0, 30, (nl, ns))

sza1 = np.linspace(55, 10, num=nl * ns // 2)
sza2 = np.linspace(10, 55, num=nl * ns // 2)
sza = np.concatenate((sza1, sza2)).reshape(nl, ns)
saa = np.linspace(120,240,num=nl * ns).reshape(nl,ns)

hspot = 0.2
lai = np.random.uniform(0.5, 3.0, (nl, ns))

BTN = sample_hom_bt(Tsl,Tsh,Tvl,Tvh,lai,hspot,wl,emisS,emisV,vzaN,sza,np.abs(saa-vaaN))
BTF = sample_hom_bt(Tsl,Tsh,Tvl,Tvh,lai,hspot,wl,emisS,emisV,vzaF,sza,np.abs(saa-vaaF))

'''添加bt和lai误差'''
bt_std = 0.0
BTN = BTN + np.random.normal(loc=0.0,scale=bt_std ,size=(nl,ns))
BTF = BTF + np.random.normal(loc=0.0,scale=0 ,size=(nl,ns))
lai_std = 0.0
lai = lai + np.random.normal(loc=0.0,scale=lai_std,size=(nl,ns))
lai[lai<0.1] = 0.1

# 计算能量
radN = planck(wl,BTN)
radF = planck(wl,BTF)

# 计算有效发射率
wN,psoil = cal_effective_emissivity_hom(lai,hspot,wl,emisS,emisV,vzaN,sza,vaaN,saa,2)
wF,psoil2 = cal_effective_emissivity_hom(lai,hspot,wl,emisS,emisV,vzaF,sza,vaaF,saa,2)
# print(np.max(psoil-psoil2))
# print(planck(10.8,300),planck(10.8,310))
# print(np.max(radN),np.min(radN))
# print(np.max(radF),np.min(radF))
# print(np.min(radN-radF))
# print(np.mean(wN[0,:,:]*planck(10.8,315)+wN[1,:,:]*planck(10.8,295)+wN[2,:,:]*planck(10.8,300) - radN))
lstN = inv_planck(wl,radN / np.sum(wN,axis =0))
lstF = inv_planck(wl,radF / np.sum(wF,axis =0))

rad_th_max, rad_th_min = 20, 4.5
maskN = (radN > rad_th_min) * (radN < rad_th_max)
maskF = (radF > rad_th_min) * (radF < rad_th_max)
DT = np.ones_like(radN)

# 反演方法：
# 两角度 5 像元  -> 三组分解 -> 两组分解
window_size = 5
off = int((window_size - 1) / 2)
para = []
results = np.zeros([4,nl,ns])
for kn in range(off, nl - off):
    ###### 取wN的所有组分的n列，行全部，进行多线程的操作
    wNLine = wN[:, kn - off: kn + off + 1, :]
    wOLine = wF[:, kn - off: kn + off + 1, :]
    radNLine = radN[kn - off:kn + off + 1, :]
    radOLine = radF[kn - off:kn + off + 1, :]
    maskNLine = maskN[kn - off: kn + off + 1, :]
    maskOLine = maskF[kn - off: kn + off + 1, :]
    lstNLine = lstN[kn - off: kn + off + 1, :]
    lstFLine = lstF[kn - off: kn + off + 1, :]
    DTLine = DT[kn - off:kn + off + 1, :]
    '''调试用,非多线程'''
    results[:,kn,:] = inv_lsct2_AATSR_line(wNLine, wOLine, radNLine, radOLine, maskNLine, maskOLine, lstNLine, lstFLine,DTLine, ns)
    '''多线程'''
#     para.append([wNLine, wOLine, radNLine, radOLine, maskNLine, maskOLine, lstNLine, lstFLine, DTLine, ns])
# tasks = []
# pool = Pool(min(32, cpu_count()))
# for p in para:
#     tasks.append(pool.apply_async(doMultiple_line_inv_2_AATSR, (p,)))
# pool.close()
# pool.join()
# results = np.array([task.get() for task in tasks])
# results = np.array(results)
# results_transposed = np.transpose(results, (1, 0, 2))
# results = np.zeros((4, nl, ns))
# results[:, 2:-2, :] = results_transposed

Ts_inv = results[0,:,:]
Tv_inv = results[1,:,:]
Ts_b_inv = results[2,:,:]
Tv_b_inv = results[3,:,:]


'''简单精度验证'''
Ts = psoil * planck(wl, Tsl) + (1 - psoil) * planck(wl, Tsh)
Ts = inv_planck(wl, Ts)

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

# end_time = time.time()
# elapsed_time = end_time - start_time
# print(f"运行时间: {elapsed_time:.4f} 秒")