import sys
import os
import h5py
import joblib
import numpy as np
import glob
import shutil
import warnings
from datetime import datetime, timedelta

warnings.filterwarnings("ignore")

# ================= ��️ 配置区域 ��️ =================

BASE_DIR = r'/home/hero/data/AATSR/aatsr_validation/sites_validation/aatsr_sites/'
INPUT_ROOT_DIR = os.path.join(BASE_DIR, '0_raw_h5_Ta')      # 原始数据
OUTPUT_ROOT_DIR = os.path.join(BASE_DIR, '0_raw_h5_Ta_td') # 结果数据

MODEL_PATH = r'/home/hero/data/AATSR/aatsr_validation/sites_validation/sites_data/Fluxnet/Fluxnet_data/processed_Ts0cm/rf_ts0cm_model.pkl'

# 变量查找配置
KEYS_CONFIG = {
    'Ta':   ['Ta', 'Meteo/Ta', 't_air', 'TA'],
    'LAI':  ['lai', 'LAI', 'Meteo/lai', 'Lai'],
    'IGBP': ['type', 'IGBP', 'Meteo/type', 'Type'],
    'Lat':  ['lat', 'Geolocation/Latitude', 'Latitude'],
    'Sec':  ['sec', 'Time/sec']
}

# ================= 核心逻辑 =================

def check_paths_safety():
    if os.path.abspath(INPUT_ROOT_DIR) == os.path.abspath(OUTPUT_ROOT_DIR):
        print("❌ [严重错误] 输入与输出目录不能相同！")
        sys.exit(1)

def smart_get_ds(h5_obj, key_type):
    """智能查找数据集"""
    candidates = KEYS_CONFIG[key_type]
    # 1. 精确匹配
    for key in candidates:
        if key in h5_obj: return h5_obj[key][()]
    
    # 2. 模糊匹配
    found_val = None
    target_short = candidates[0].split('/')[-1].lower()
    def visit(name, obj):
        nonlocal found_val
        if found_val is not None: return
        if name.split('/')[-1].lower() == target_short and isinstance(obj, h5py.Dataset):
            found_val = obj[()]
    h5_obj.visititems(visit)
    return found_val

def parse_time(filepath, sec_val):
    try:
        filename = os.path.basename(filepath)
        parts = filename.split('_')
        year, doy = parts[1], parts[2]
        base = datetime.strptime(f"{year}_{doy}", "%Y_%j")
        offset = np.nanmean(sec_val).item() if hasattr(sec_val, 'mean') else float(sec_val)
        return base + timedelta(seconds=int(offset))
    except:
        return None

def compute_td_dif(h5_file_obj, model):
    """
    动态形状计算函数
    """
    try:
        # 1. 读取所有变量
        ta = smart_get_ds(h5_file_obj, 'Ta')
        lai = smart_get_ds(h5_file_obj, 'LAI')
        igbp = smart_get_ds(h5_file_obj, 'IGBP')
        lat = smart_get_ds(h5_file_obj, 'Lat')
        sec = smart_get_ds(h5_file_obj, 'Sec')
        
        # 2. 检查缺失
        missing = []
        if ta is None: missing.append("Ta")
        if lai is None: missing.append("lai")
        if igbp is None: missing.append("type")
        if lat is None: missing.append("lat")
        if sec is None: missing.append("sec")
        if missing: return False, f"Missing: {missing}"

        # 3. 计算时间
        ts = parse_time(h5_file_obj.filename, sec)
        if ts is None: return False, "Time Parse Error"

        # 4. 确定基准形状 (使用 Lat 或 LAI 作为形状基准)
        lat = np.squeeze(lat)
        lai = np.squeeze(lai)
        igbp = np.squeeze(igbp)
        
        # 以 Lat 的形状为准 (因为它是地理定位基础)
        target_shape = lat.shape
        
        # 5. 数据预处理 & 广播
        
        # Ta 处理: 可能是标量，也可能是矩阵
        if np.ndim(ta) == 0 or ta.size == 1:
            # 如果是标量，广播到 target_shape (如 31x21)
            scalar_ta = float(ta.item() if hasattr(ta, 'item') else ta)
            ta = np.full(target_shape, scalar_ta)
        else:
            ta = np.squeeze(ta)
            
        # Ta K -> C
        if np.nanmean(ta) > 200: ta = ta - 273.15
        
        # LAI /1000
        lai = lai.astype(np.float32)
        if np.nanmax(lai) > 100: lai = lai / 1000.0
            
        # Lat /100
        lat = lat.astype(np.float32) / 100.0
        
        # 6. 最终形状一致性检查
        # 这里的检查是动态的，不再是硬编码 (31,31)
        if ta.shape != target_shape or lai.shape != target_shape or igbp.shape != target_shape:
            return False, f"Shape Mismatch: Lat{target_shape} vs Ta{ta.shape}/LAI{lai.shape}"
            
        # 7. 构造特征
        rows, cols = target_shape
        n = rows * cols
        
        X = np.column_stack((
            ta.flatten(),
            lai.flatten(),
            lat.flatten(),
            igbp.flatten(),
            np.full(n, ts.month),
            np.full(n, ts.day),
            np.full(n, ts.hour)
        ))
        
        # 8. 预测
        mask = ~np.isnan(X).any(axis=1)
        res = np.full(n, np.nan)
        if np.sum(mask) > 0:
            res[mask] = model.predict(X[mask])
            
        return True, res.reshape(rows, cols)

    except Exception as e:
        return False, str(e)

def process_and_save(src_path, dst_path, model):
    # 1. 复制
    try:
        shutil.copy2(src_path, dst_path)
    except Exception as e:
        return False, f"Copy Failed: {e}"

    # 2. 计算并写入
    try:
        with h5py.File(dst_path, 'r+') as f:
            success, result = compute_td_dif(f, model)
            
            if not success:
                raise ValueError(result) # 抛出异常触发清理
            
            if 'td_dif' in f: del f['td_dif']
            f.create_dataset('td_dif', data=result)
            
        return True, "OK"

    except Exception as e:
        # 清理坏文件
        if os.path.exists(dst_path):
            os.remove(dst_path)
        return False, str(e)

# ================= 主程序 =================

def main():
    check_paths_safety()
    
    if not os.path.exists(MODEL_PATH): sys.exit("❌ 模型文件不存在")
    rf_model = joblib.load(MODEL_PATH)
    
    site_dirs = sorted([d for d in os.listdir(INPUT_ROOT_DIR) 
                        if os.path.isdir(os.path.join(INPUT_ROOT_DIR, d))])
    
    print(f"�� 开始处理 {len(site_dirs)} 个站点...")
    print(f"�� 输入: {INPUT_ROOT_DIR}")
    print(f"�� 输出: {OUTPUT_ROOT_DIR}")

    for idx, site in enumerate(site_dirs):
        # 进度打印
        print(f"\n[{idx+1}/{len(site_dirs)}] 处理站点: {site}")
        
        src_dir = os.path.join(INPUT_ROOT_DIR, site)
        dst_dir = os.path.join(OUTPUT_ROOT_DIR, site)
        if not os.path.exists(dst_dir): os.makedirs(dst_dir)

        if site != 'SN-Dhr': continue
            
        h5_files = glob.glob(os.path.join(src_dir, "*.h5"))
        if not h5_files:
            print("  ⚠️ 无文件")
            continue
            
        success_cnt = 0
        fail_cnt = 0
        first_err = None
        
        for f in h5_files:
            dst_file = os.path.join(dst_dir, os.path.basename(f))
            is_ok, msg = process_and_save(f, dst_file, rf_model)
            
            if is_ok:
                success_cnt += 1
            else:
                fail_cnt += 1
                if first_err is None: first_err = f"{os.path.basename(f)} -> {msg}"
        
        print(f"  ✅ 成功: {success_cnt}")
        if fail_cnt > 0:
            print(f"  ❌ 失败: {fail_cnt} (首个错误: {first_err})")

    print("\n�� 全部完成！")

if __name__ == '__main__':
    main()