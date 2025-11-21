'''2025.3.3'''
'''将浅层温度推到表皮'''

from utils.old.util import *
import pandas as pd
import numpy as np

'''热传导参数库 (可扩展为站点专属参数)'''
SOIL_PARAMS = {
    # 示例：假设大部分站点为壤土（需替换为实际数据）
    'default': {'k': 0.5, 'rho': 1.8e3, 'c': 1.5e3},  # 单位: W/m·K, kg/m³, J/kg·K
    # 可根据站点名匹配特定参数，例如：
    'HBHB': {'k': 0.5, 'rho': 1.3e3, 'c': 1.5e3}  # 沙土站点示例
}


def calculate_skin_temperature(df, z=0.05, soil_type='default'):
    """通过热传导方程计算地表温度"""
    # 获取土壤热属性
    params = SOIL_PARAMS.get(soil_type, SOIL_PARAMS['default'])
    k, rho, c = params['k'], params['rho'], params['c']
    alpha = k / (rho * c)  # 热扩散率 m²/s

    # 计算温度变化率 dT/dt (°C/s)
    time_diff = (df['time'].diff().dt.total_seconds()).fillna(1800)  # 默认30分钟间隔
    dT_dt = df['一层土壤温度'].diff() / time_diff

    # 热传导方程参数
    omega = 2 * np.pi / (24 * 3600)  # 日周期角频率 (rad/s)
    phase_shift = z / np.sqrt(alpha * omega)

    # 计算表皮温度
    df['T_skin'] = df['一层土壤温度'] + phase_shift * dT_dt

    # 日间温度合理性修正（避免夜间异常）
    df['hour'] = df['time'].dt.hour
    df.loc[df['hour'].between(6, 18), 'T_skin'] = np.maximum(df['T_skin'], df['一层土壤温度'])

    return df



'''ChinaFlux'''
base_dir = r'/home/hero/data/AATSR/Validation/ChinaFlux/'
ChinaFlux_dir = r'/home/hero/data/AATSR/Sites/ChinaNet/data/'
outdir = r'/home/hero/data/AATSR/Validation/ChinaFlux/surface/'
mkdir_if_not_exist(outdir)

site_names = search_dir(ChinaFlux_dir,'min')

for site_name in site_names:
    print(site_name)
    filenames = search_file(ChinaFlux_dir + site_name,'xlsx')
    for filename in filenames:
        print(filename)
        infile = ChinaFlux_dir + site_name + '/' + filename
        data = pd.read_excel(infile, skiprows=[1])

        data['time'] = pd.to_datetime(
            data[['年', '月', '日', '时', '分', '秒']].rename(
                columns={'年': 'year', '月': 'month', '日': 'day', '时': 'hour', '分': 'minute', '秒': 'second'})
        )
        data = data.sort_values('time').reset_index(drop=True)

        # 计算表皮温度（需根据实际站点设置soil_type）
        processed_data = calculate_skin_temperature(data, soil_type='default')  # 示例：用站点名前4字符匹配

        # 保存结果（保留原始列，新增T_skin）
        mkdir_if_not_exist(outdir+site_name)
        output_path = os.path.join(outdir + site_name + '/' + filename)
        processed_data.to_excel(output_path, index=False)
        print(f'Saved: {output_path}')

