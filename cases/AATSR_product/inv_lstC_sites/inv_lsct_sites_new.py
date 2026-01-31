import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../../../')))
from base.util_lsct import *
from base.util_constant import *
from base.util_file import *
from base.util_data import *
from cases.AATSR_product.util.util_aatsr import *
import time
import warnings
warnings.filterwarnings("ignore")

'''2025.12.4'''
'''补充异温方法和对比'''
'''2025.11.18'''
'''贝叶斯反演'''
'''2025.10.21'''
'''站点切片组分温度反演 python311'''
'''反演两组分/三组分+lai/NDVI结果，并验证'''

if __name__ == '__main__':
    ###  反演参数设置
    n, m, ws = 2, 2, 5 # n 角度， m组分， ws窗口大小
    ndvi_max, ndvi_min, k = 0.87, 0.15, 1 # ndvi 参数
    lst_min, lst_max = 250, 350 # 范围参数
    hspot, wl = 1.0, 10.8 # 结构参数
    # 反演方法
    method_effective_emissivity = 'lai' # lai / ndvi
    method_mpl_pixel = 'winconst' # point / winconst / winquad
    method_solve = 'bayesian' # bayesian / nobayesian / none
    # 反演站点设置
    if_Dahra = 1 # 只反演Dahra站点
    if_PureSites = 0 # 只反演纯站点
    if_daynight = 'all' # day/night/all

    label = 'inv_%01dc_' % m + method_effective_emissivity + '_' + method_mpl_pixel + '_' + method_solve

    # 输入输出位置
    indir_h5_sites = r'/home/hero/data/AATSR/aatsr_validation/sites_validation/aatsr_sites/0_raw_h5/'
    infile_pure_soil_sites = r'/home/hero/data/AATSR/aatsr_validation/sites_validation/sites_data/Fluxnet/soil_sites.txt'
    infile_pure_veg_sites = r'/home/hero/data/AATSR/aatsr_validation/sites_validation/sites_data/Fluxnet/veg_sites.txt'
    outdir_h5_sites = r'/home/hero/data/AATSR/aatsr_validation/sites_validation/aatsr_sites/' + label + '/'
    mkdir_if_not_exist(outdir_h5_sites)
    angle_error_file = indir_h5_sites + r'Angle_error.txt'

    siteNames = search_dir(indir_h5_sites,'')
    for i, siteName in enumerate(siteNames):
        if if_Dahra == 1:
            if siteName != 'SN-Dhr': continue
        if if_PureSites == 1:
            soil_sites_list = np.array(read_txt_str(infile_pure_soil_sites,'\n'))[:,0]
            veg_sites_list = np.array(read_txt_str(infile_pure_veg_sites,'\n'))[:,0]
            soil_sites_list = soil_sites_list.tolist()
            soil_sites_list.append('SN-Dhr')
            if siteName not in soil_sites_list and siteName not in veg_sites_list: continue
        print(i,siteName)
        indir_site = indir_h5_sites + siteName + '/'
        outdir_site = outdir_h5_sites + siteName + '/'
        mkdir_if_not_exist(outdir_site)
        fileNames = search_file(indir_site, ['h5'])
        fileNames.sort()
        wl = 10.8
        for i, fileName in enumerate(fileNames):
            year = int(fileName.split('_')[1])
            doy = int(fileName.split('_')[2])
            month,day = doy2date(year,doy)
            if year != 2009: continue
            if doy < 120: continue
            # if fileName != 'AATSR_2009_150_101541.h5': continue

            ### 0. 读取数据
            print(i,fileName)
            start_time = time.time()
            infile = indir_site + fileName
            outfile = outdir_site + fileName
            if os.path.exists(outfile):
                os.remove(outfile)

            ndviN, ndviF = aatsr_read_sites_obs(infile, ifNDVI=1)
            cloN_mask, cloF_mask = aatsr_read_sites_clo(infile)
            lstN,lstF = aatsr_read_sites_lst(infile)
            vzaN,vzaF,vaaN,vaaF,sza,saa = aatsr_read_sites_angle(infile)
            emisS,emisV,type,lai = aatsr_read_sites_emis(infile)
            indx,indy,ref_indx,ref_indy,lat,lon = aatsr_read_sites_loc(infile)
            utc_time = aatsr_read_sites_time(infile)

            # 筛选控制 
            if np.average(sza) > 89: dn = 'night'
            else: dn = 'day'
            if if_daynight != 'all' and if_daynight != dn: 
                print('Pass day/night')
                continue

            if np.average(vzaF) > 60 or np.average(vzaF) < 50:  # 极少部分数据vzaF值异常
                print('Angle error')
                with open(angle_error_file,'a') as f:
                    f.write(siteName + ' ' + fileName + '\n')
                continue
            if np.mean(lstN) == 0: continue

            nl,ns = lstN.shape
            if nl != 31 or ns != 31: continue

            ### 1.计算有效发射率矩阵 w
            off = ws//2
            if method_effective_emissivity == 'lai':
                vza = np.stack((vzaN, vzaF), axis=2)
                vaa = np.stack((vaaN, vaaF), axis=2)
                
                w = cal_effective_emissivity_hom(lai,hspot, wl, emisS,emisV,vza,sza,vaa,saa,n,m)
                w2 = cal_effective_emissivity_hom(lai,hspot, wl, emisS,emisV,vza,sza,vaa,saa,n,2) # FVC,后面可能有用

                if m == 3:
                    psoil = cal_psoil_hom(lai,sza)
                cloN_mask = cloN_mask * (lai>0.01)

            elif method_effective_emissivity == 'ndvi':
                fvcN = cal_fvc_from_ndvi(ndviN,ndvi_min,ndvi_max)  # nl*ns
                fvcF = cal_fvc_from_ndvi(ndviF,ndvi_min,ndvi_max)  # nl*ns
                fvcN[cloN_mask == 0] = 0
                fvcF[cloF_mask == 0] = 0
                wN = np.stack([emisS * (1-fvcN), emisV * fvcN], axis=-1)  # 形状: (nl, ns, m)
                wF = np.stack([emisS * (1-fvcF), emisV * fvcF], axis=-1)  # 形状: (nl, ns, m)
                w = np.stack([wN, wF], axis=2) # 形状: (nl, ns, m, 2)
            
            ### 2.计算观测亮度矩阵 b
            lst = np.stack((lstN,lstF),axis=2)
            if method_effective_emissivity == 'lai': # lai反演0
                bN = cal_rad_from_lst(lstN,wl,lai,vzaN,emisS,emisV)
                bF = cal_rad_from_lst(lstF,wl,lai,vzaF,emisS,emisV)
                b = np.concatenate([bN[:,:,np.newaxis], bF[:,:,np.newaxis]], axis=2) # 形状: (nl, ns, m)
            elif method_effective_emissivity == 'ndvi':
                bN = cal_rad_from_lst_fvc(lstN,wl,fvcN,emisS,emisV)
                bF = cal_rad_from_lst_fvc(lstF,wl,fvcF,emisS,emisV)
                b = np.concatenate([bN[:,:,np.newaxis], bF[:,:,np.newaxis]], axis=2)

            ### 3. 求解
            cloN_mask[np.abs(lstN - lstF)>15] = 0
            cloF_mask[np.abs(lstN - lstF)>15] = 0
            mask = np.concatenate([cloN_mask[:,:,np.newaxis], cloF_mask[:,:,np.newaxis]], axis=2)
            if method_mpl_pixel == 'point':
                lsct = inv_lsct_point(w,b,mask,n,m,wl,method='ls')

            elif method_mpl_pixel == 'winconst':
                if m == 2:
                    lsct = inv_lsct2_winconst(w, b, mask, lst,n, m=2, ws=5, wl=10.8,method = 'SLSQP')
                elif m == 3:
                    if dn == 'day':
                        lsct = inv_lsct3_winconst(w, b, mask, lst, psoil, n, m=3, ws=5, wl=10.8,method = 'SLSQP')
                    elif dn == 'night':
                        lsct = inv_lsct2_winconst(w, b, mask, lst, psoil, n, m=2, ws=5, wl=10.8,method = 'SLSQP')
            
            elif method_mpl_pixel == 'winquad':
                if m == 2:
                    if method_solve == 'bayesian': if_bayesian = 1
                    else: if_bayesian = 0

                    lsct = inv_lsct2_winquad_constraint(w, b, mask,lst,n, m=2, ws=5,wl=10.8,if_bayesian = if_bayesian)

                elif m == 3:  # 这里m=2，中间3组分
                    if method_solve == 'bayesian': if_bayesian = 1
                    else: if_bayesian = 0

                    if dn == 'day':
                        # lsct = inv_lsct3_winquad(w2, w, b, mask,psoil,n, m=2, ws=5,wl=10.8,if_bayesian = if_bayesian)
                        # lsct = inv_lsct3_winquad_constraint(w2, w, b, mask,lst,psoil,n, m=2, ws=5,wl=10.8,if_bayesian = if_bayesian)
                        
                        ### 多线程
                        para = []
                        for kn in range(off, ns-off):
                            wLine = w[:,kn-off:kn+off+1,:,:]
                            w2Line = w2[:,kn-off:kn+off+1,:,:]
                            bLine = b[:,kn-off:kn+off+1,:]
                            maskLine = mask[:,kn-off:kn+off+1,:]
                            lstLine = lst[:,kn-off:kn+off+1,:]
                            psoilLine = psoil[:,kn-off:kn+off+1]
                            para.append([w2Line,wLine,bLine,maskLine,lstLine,psoilLine,n,2,ws,wl,if_bayesian])
                        
                        tasks= []
                        pool = Pool(min(192,cpu_count()))
                        tasks = [pool.apply_async(inv_lsct3_winquad_constraint, tuple(p)) for p in para]
                        pool.close()
                        pool.join()
                        results = [t.get() for t in tasks]
                        lsct = np.zeros((nl, ns, 4))
                        for idx, res in enumerate(results):
                            kn = idx + off
                            # 如果 res 形状是 (nl, m)，直接赋值
                            lsct[:, kn, :] = res[:,off,:]
                    
                    elif dn == 'night':
                        lsct = np.full((nl,ns,4),np.nan)
                        # lsct[:,:,2:] = inv_lsct2_winquad(w2, b, mask,n, m=2, ws=5,wl=10.8,if_bayesian = if_bayesian)
                        # lsct[:,:,2:] = inv_lsct2_winquad_constraint(w2, b, mask,lst,n, m=2, ws=5,wl=10.8,if_bayesian = if_bayesian)

                        ### 多线程
                        para = []
                        for kn in range(off, ns-off):
                            w2Line = w2[:,kn-off:kn+off+1,:,:]
                            bLine = b[:,kn-off:kn+off+1,:]
                            maskLine = mask[:,kn-off:kn+off+1,:]
                            lstLine = lst[:,kn-off:kn+off+1,:]
                            para.append([w2Line,bLine,maskLine,lstLine,n,2,ws,wl,if_bayesian])
                            
                        tasks= []
                        pool = Pool(min(192,cpu_count()))
                        tasks = [pool.apply_async(inv_lsct2_winquad_constraint, tuple(p)) for p in para]
                        pool.close()
                        pool.join()
                        results = [t.get() for t in tasks]

                        for idx, res in enumerate(results):
                            kn = idx + off
                            # 如果 res 形状是 (nl, m)，直接赋值
                            lsct[:, kn, 2:] = res[:,off,:]
            
            
            ### -1. 保存结果
            name_list = ['lstN','lstF','lai','indx','indy','ref_indx','ref_indy','cloN_mask','cloF_mask']
            data_list = [lstN,lstF,lai,indx,indy,ref_indx,ref_indy,cloN_mask,cloF_mask]
            dtype_list = np.full_like(name_list,'f')
            write_h5py_file(outfile,name_list,data_list,dtype_list,compression=None,ifcover = 1)
            write_h5py_item(outfile,'utc_time',utc_time.isoformat(),dtype=h5py.string_dtype())

            if m == 2:
                write_h5py_item(outfile,'Ts',lsct[:,:,0],'f',if_overwrite=1)
                write_h5py_item(outfile,'Tv',lsct[:,:,1],'f',if_overwrite=1)
            if m == 3:
                write_h5py_item(outfile,'Tsl',lsct[:,:,0],'f',if_overwrite=1)
                write_h5py_item(outfile,'Tsh',lsct[:,:,1],'f',if_overwrite=1)
                write_h5py_item(outfile,'Ts',lsct[:,:,2],'f',if_overwrite=1)
                write_h5py_item(outfile,'Tv',lsct[:,:,3],'f',if_overwrite=1)
            
            end_time = time.time()
            print(f"总执行时间: {end_time - start_time:.4f}秒\n")