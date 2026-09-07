import pandas as pd
import numpy as np
import glob
import os
from scipy.special import erfc
import warnings

# 忽略运行时警告 (如除以0的临时警告)
warnings.filterwarnings('ignore')

# ================= 配置区域 =================
INPUT_DIR = "/home/hero/data/AATSR/aatsr_validation/sites_validation/sites_data/Fluxnet/Fluxnet_data/"
OUTPUT_DIR = os.path.join(INPUT_DIR, "processed_Ts0cm_new")

# 物理设置
DEPTH_OBS = 0.05  # 5cm 观测深度
DT_SECONDS = 1800 # 30分钟 时间步长

# ================= Part 1: SCOPE 参数化方案 (Soil_Inertia1.m) =================

def get_soil_parameters_scope(swc_array):
    """
    完全复刻 SCOPE 模型 (Soil_Inertia1.m) 的参数计算逻辑。
    来源: User uploaded 'Soil_Inertia1.m'
    方法: Murray and Verhoef (2022)
    """
    # 1. 确定计算用的 SMC (Soil Moisture Content)
    # 使用全序列均值作为该站点的背景参数 (FFT反演需要参数稳定)
    if swc_array is None or np.isnan(swc_array).all():
        SMC = 0.2 # 默认值
    else:
        SMC = np.nanmean(swc_array)
        
    # [关键] 单位转换: Fluxnet SWC 若为 0-100，转为 0-1
    if SMC > 1.0: 
        SMC /= 100.0
    
    # === 参数定义 (来自 Soil_Inertia1.m) ===
    theta_s = 0.435  # 饱和含水量/孔隙度
    phis = 0.435     # 孔隙度 (同 theta_s)
    
    # 物理限制 (SMC 不能超过孔隙度)
    SMC = np.clip(SMC, 0.0, theta_s)
    
    # === 计算过程 ===
    
    # 1. 饱和度 Sr
    Sr = SMC / theta_s 
    
    # 2. Kersten Number (Ke) - 调节干湿导热权重的系数
    gamma_s = 0.96   # 质地参数
    dels = 1.33      # 形状参数
    
    # 公式: ke = exp(gamma_s * (1 - Sr^(gamma_s - dels)))
    if Sr > 1e-7:
        exponent = gamma_s - dels
        term = np.power(Sr, exponent)
        ke = np.exp(gamma_s * (1.0 - term))
    else:
        ke = 0.0
        
    # 3. 固体与干土导热率
    # lambda_d (干土)
    lambda_d = -0.56 * phis + 0.51
    
    # lambda_s (固体颗粒混合)
    QC = 0.60        # 石英含量
    lambda_qc = 7.7  # 石英导热率
    # SCOPE 特有写法: 固体 = 石英^QC * 干土^(1-QC)
    lambda_s_solid = (lambda_qc**QC) * (lambda_d**(1.0 - QC))
    
    # 4. 饱和导热率 lambda_w (注意这里变量名对应代码逻辑)
    lambda_wtr = 0.57 # 水的导热率
    # lambda_w = 固体^(1-phi) * 水^phi
    lambda_sat = (lambda_s_solid**(1.0 - phis)) * (lambda_wtr**phis)
    
    # 5. 最终热导率 lambdas
    # lambdas = ke * (lambda_sat - lambda_d) + lambda_d
    lam = ke * (lambda_sat - lambda_d) + lambda_d
    
    # 6. 体积热容 Hc
    Hcs = 2.0e6  # 干土热容 J/m3/K
    Hcw = 4.2e6  # 水热容 J/m3/K
    # Hc = 水部分 + 干土部分(1-孔隙度)
    # 注意: SCOPE 源码里用的是 (1-theta_s)*Hcs
    cv = (Hcw * SMC) + (1.0 - theta_s) * Hcs
    
    # 7. 最终热扩散率 kappa (Thermal Diffusivity)
    kappa = lam / cv
    
    return kappa, lam

# ================= Part 2: Wang (2012) 物理反演 (FFT加速) =================

def calculate_green_function_diff(n_steps, dt, z, kappa, lam):
    """
    计算格林函数(脉冲响应)的导数。
    物理基础: Wang (2012) Eq. 2 & Eq. 7
    """
    t = np.arange(1, n_steps + 1) * dt
    # 1D 半无限大介质热传导的格林函数导数项 (Heat Flux Kernel)
    # 公式: (z / 2*sqrt(pi*k*t^3)) * exp(-z^2 / 4kt) ... 
    # 注: 这里根据热通量和温度的关系进行了推导
    factor1 = (2 * np.sqrt(kappa * t / np.pi) / lam) * np.exp(- (z**2) / (4 * kappa * t))
    factor2 = (z / lam) * erfc(z / (2 * np.sqrt(kappa * t)))
    g_z = factor1 - factor2
    
    # 离散化导数 (Difference)
    dg_z = np.diff(g_z, prepend=0)
    return dg_z

def calculate_surface_kernel(n_steps, dt, kappa, lam):
    """
    计算地表 (z=0) 的响应核
    """
    t = np.arange(1, n_steps + 1) * dt
    # z=0 时，erfc(0)=1，exp(0)=1，公式简化
    g_0 = (2 * np.sqrt(kappa * t / np.pi) / lam)
    dg_0 = np.diff(g_0, prepend=0)
    return dg_0

def invert_surface_temperature(T_obs, swc_array, z_obs, dt):
    """
    利用 FFT 进行反卷积，求解 Ts0cm
    """
    n = len(T_obs)
    
    # 1. 预处理温度序列 (去基线，变为波动量)
    T_init = T_obs[0] 
    theta_z = T_obs - T_init
    
    # 2. 获取物理参数 (SCOPE 方案)
    kappa, lam = get_soil_parameters_scope(swc_array)
    
    # 3. 生成格林函数 (Wang 2012 物理核)
    dg_z = calculate_green_function_diff(n, dt, z_obs, kappa, lam)
    dg_0 = calculate_surface_kernel(n, dt, kappa, lam)
    
    # 4. FFT 运算 (数学加速求解)
    # 补零到 2 的幂次以提高 FFT 效率
    n_fft = 2**(int(np.log2(n)) + 1)
    
    # 转到频域
    Theta_f = np.fft.rfft(theta_z, n=n_fft)
    dGz_f = np.fft.rfft(dg_z, n=n_fft)
    
    # 5. 反卷积 (频域除法)
    # 正则化: 防止除以接近 0 的高频噪声
    # 动态阈值: 最大振幅的 1e-9
    threshold = 1e-9 * np.max(np.abs(dGz_f))
    dGz_f[np.abs(dGz_f) < threshold] = threshold
    
    # 核心公式: G0_flux = Theta_z / Green_z
    G0_f = Theta_f / dGz_f
    
    # 6. 计算地表温度波动
    dG0_f = np.fft.rfft(dg_0, n=n_fft)
    Theta0_f = G0_f * dG0_f # 频域乘法 = 时域卷积
    
    # 7. 逆变换回时域
    theta_0 = np.fft.irfft(Theta0_f, n=n_fft)[:n]
    
    # 8. 恢复基线
    Ts_0 = theta_0 + T_init
    
    return Ts_0

# ================= Part 3: 文件处理流程 =================

def process_file(filepath):
    filename = os.path.basename(filepath)
    
    try:
        # 读取
        df = pd.read_csv(filepath, na_values=['-9999', '-9999.0', -9999, -9999.0])
        
        # 检查必要列
        if 'TS_F_MDS_1' not in df.columns:
            return

        ts_raw = df['TS_F_MDS_1'].values
        
        # 记录缺失位置 (Mask)
        mask_is_missing = np.isnan(ts_raw)
        
        if mask_is_missing.all():
            return # 全空跳过

        # 填补缺失值 (FFT 需要连续信号)
        # 使用线性插值 + 前后填充
        ts_for_calc = pd.Series(ts_raw).interpolate(method='linear').fillna(method='bfill').fillna(method='ffill').values
        
        # 获取 SWC
        swc_data = None
        if 'SWC_F_MDS_1' in df.columns:
            swc_data = df['SWC_F_MDS_1'].values
            # 同样需要填补 SWC 的缺失值以计算平均参数
            swc_data = pd.Series(swc_data).interpolate(method='linear').fillna(method='bfill').fillna(method='ffill').values
        
        # 执行核心反演
        print(f"[PROCESS] {filename}")
        ts_surface_full = invert_surface_temperature(ts_for_calc, swc_data, DEPTH_OBS, DT_SECONDS)
        
        # 恢复 NaN (只保留原始数据存在的时刻)
        ts_surface_full[mask_is_missing] = np.nan
        
        # 写入结果
        df['Ts0cm'] = np.round(ts_surface_full, 3)
        
        output_path = os.path.join(OUTPUT_DIR, filename)
        df.to_csv(output_path, index=False)
        
    except Exception as e:
        print(f"[ERROR] {filename}: {e}")

def main():
    # 创建输出目录
    if not os.path.exists(OUTPUT_DIR):
        os.makedirs(OUTPUT_DIR)
        
    # 获取所有文件
    csv_files = glob.glob(os.path.join(INPUT_DIR, "*.csv"))
    print(f"Total Files Found: {len(csv_files)}")
    
    # 循环处理
    for f in csv_files:
        process_file(f)

    print("All processing complete.")

if __name__ == "__main__":
    main()