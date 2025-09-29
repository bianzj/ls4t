import os
import sys
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))
from base.util_lsct.packages import *
from base.util_lsct.emis import cal_effective_emissivity_hom, cal_effective_emissivity_crown

'''
lsct_forward
正向模型，生成测试数据集，验证结果和速度
'''
def sample_hom_bt(Tsl,Tsh,Tvl,Tvh, lai, hspot,wavelength, emissivity_soil, emissivity_leaf,vza, sza, raa):

    # 注意输入 全部为单值（角度为list） 或全部为array
    '''1.initial'''
    hom = Hom()
    '''2.set variables'''
    hom.set_thermal(Tsl,Tsh,Tvl,Tvh)
    hom.set_structure(lai, hspot)
    hom.set_optical(wavelength, emissivity_soil, emissivity_leaf)
    hom.set_angle(vza, sza, raa)
    ''''3.run'''
    bt = hom.run()
    vza[raa == 180] = vza[raa == 180] * -1
    return bt

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

def sample_crown_bt(Tsl,Tsh,Tvl,Tvh,lai, hspot,stand,rcr,hcr,wavelength, emissivity_soil, emissivity_leaf,vza, sza, raa):
    '''1.initial'''
    crown = Crown()
    '''2.set variables'''
    crown.set_thermal(Tsl,Tsh,Tvl,Tvh)
    crown.set_structure(lai, hspot, stand, hcr, rcr)
    crown.set_optical(wavelength, emissivity_soil, emissivity_leaf)
    crown.set_angle(vza, sza, raa)
    ''''3.run'''
    bt = crown.run()
    vza[raa == 180] = vza[raa == 180] * -1
    return bt

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


def _process_block(i_start, i_end, j_start, j_end, Tsl_block, Tsh_block, Tvl_block, Tvh_block,
                  lai_block, hspot, wl, emisS_block, emisV_block, vza_block, sza_block, raa_block, n, m):
    '''generate_hom_Nangle_Mcomponent_mlt 处理单个数据块的辅助函数'''
    block_bt = np.zeros((i_end-i_start, j_end-j_start, n))
    block_w = np.zeros((i_end-i_start, j_end-j_start, n, m))
    
    for i in range(i_end - i_start):
        for j in range(j_end - j_start):
            block_bt[i, j, :] = sample_hom_bt(
                Tsl_block[i, j], Tsh_block[i, j], Tvl_block[i, j], Tvh_block[i, j],
                lai_block[i, j], hspot, wl, emisS_block[i, j], emisV_block[i, j],
                vza_block[i, j, :], sza_block[i, j, :], raa_block[i, j, :])
            
            block_w[i, j, :, :] = cal_effective_emissivity_hom(
                lai_block[i, j], hspot, wl, emisS_block[i, j], emisV_block[i, j],
                vza_block[i, j, :], sza_block[i, j, :],
                vza_block[i, j, :] + 180, sza_block[i, j, :] + 180,  # 临时处理方位角
                angle_number=n, component_number=m)
    
    return block_bt, block_w, (i_start, i_end, j_start, j_end)

def generate_hom_Nangle_Mcomponent_mlt(n,m,nl,ns,Tsl,Tsh,Tvl,Tvh,lai,hspot,wl,emisS,emisV,vza,sza,vaa,saa,ifmlt):
    '''
    生成均值假设下的区域多角度数据集,加入多线程以加速计算
    :param n: 角度数
    :param m: 组分数
    :param nl: 行数
    :param ns: 列数
    :param Tsl: 光照土壤温度 nl*ns
    :param Tsh: 阴影土壤温度 nl*ns
    :param Tvl: 光照植被温度 nl*ns
    :param Tvh: 阴影植被温度 nl*ns
    :param lai: 叶面积指数 nl*ns
    :param hspot: 热点参数 float
    :param wl: 波长 float
    :param emisS: 土壤发射率 nl*ns
    :param emisV: 植被发射率 nl*ns
    :param vza: 观测天顶角 nl*ns*n
    :param sza: 太阳天顶角 nl*ns*n
    :param vaa: 观测方位角 n*nl*ns
    :param saa: 太阳方位角 n*nl*ns
    :param ifmlt: 是否使用多线程加速
    :return: bt(nl*ns*n),w(nl*ns*n*m)
    '''
    if nl*ns==1: # 数量如果小就不用多线程
        Tsl,Tsh,Tvl,Tvh = float(Tsl),float(Tsh),float(Tvl),float(Tvh)
        lai,hspot,wl,emisS,emisV = float(lai),float(hspot),float(wl),float(emisS),float(emisV)
        vza,sza,vaa,saa = np.reshape(vza,-1),np.reshape(sza,-1),np.reshape(vaa,-1),np.reshape(saa,-1)
        bt = sample_hom_bt(Tsl, Tsh, Tvl, Tvh,lai,hspot,wl,emisS,emisV,vza,sza,np.abs(vaa-saa))
        w = cal_effective_emissivity_hom(lai,hspot,wl,emisS,emisV,vza,sza,vaa,saa,angle_number=n,component_number=m)
        return bt.reshape(n),w.reshape(n,m)

    if not ifmlt:
        bt = np.zeros([nl, ns, n])
        w = np.zeros([nl, ns, n, m])
        for i in range(nl):
            for j in range(ns):
                bt[i, j, :] = sample_hom_bt(Tsl[i, j], Tsh[i, j], Tvl[i, j], Tvh[i, j],
                                            lai[i, j], hspot,
                                            wl,
                                            emisS[i, j], emisV[i, j],
                                            vza[i, j, :], sza[i, j, :], np.abs(vaa[i, j, :] - saa[i, j, :]))
                w[i, j, :, :] = cal_effective_emissivity_hom(lai[i, j], hspot, wl, emisS[i, j], emisV[i, j],
                                                            vza[i, j, :], sza[i, j, :],
                                                            vaa[i, j, :] , saa[i, j, :], angle_number=n, component_number=m)
    if ifmlt:
        # 分块处理优化 - 将大图像分成多个块并行处理
        block_size = 256  # 每个块的大小，可根据实际调整
        num_blocks_i = (nl + block_size - 1) // block_size
        num_blocks_j = (ns + block_size - 1) // block_size
        
        # 创建块索引和参数元组
        block_params = []
        for i in range(num_blocks_i):
            for j in range(num_blocks_j):
                i_start = i * block_size
                i_end = min((i + 1) * block_size, nl)
                j_start = j * block_size
                j_end = min((j + 1) * block_size, ns)
                block_params.append((
                    i_start, i_end, j_start, j_end,
                    Tsl[i_start:i_end, j_start:j_end],
                    Tsh[i_start:i_end, j_start:j_end],
                    Tvl[i_start:i_end, j_start:j_end],
                    Tvh[i_start:i_end, j_start:j_end],
                    lai[i_start:i_end, j_start:j_end],
                    hspot, wl,
                    emisS[i_start:i_end, j_start:j_end],
                    emisV[i_start:i_end, j_start:j_end],
                    vza[i_start:i_end, j_start:j_end, :],
                    sza[i_start:i_end, j_start:j_end, :],
                    np.abs(vaa[i_start:i_end, j_start:j_end, :] - saa[i_start:i_end, j_start:j_end, :]),
                    n, m
                ))
        
        # 使用更大的chunksize减少任务切换开销
        with Pool(processes=cpu_count(), maxtasksperchild=4) as pool:
            results = pool.starmap(_process_block, block_params, chunksize=max(1, len(block_params)//(cpu_count()*4)))
        
        # 合并结果
        bt = np.zeros((nl, ns, n))
        w = np.zeros((nl, ns, n, m))
        for block_bt, block_w, (i_s, i_e, j_s, j_e) in results:
            bt[i_s:i_e, j_s:j_e, :] = block_bt
            w[i_s:i_e, j_s:j_e, :, :] = block_w
    return bt, w