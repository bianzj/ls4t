import sys
import os
import numpy as np
import pandas as pd
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../../../')))
from base.util_lsct import *
from base.util_constant import *
from base.util_file import *
from base.util_data import *


if __name__ == '__main__':
    indx, indy = 7459, 16456
    indir_lai = r'/media/hero/lsct02/lai/'
    
    # 创建列表存储结果
    results = []
    
    for year in range(2009, 2010):
        indir_lai_year = indir_lai + str(year) + '/'
        fileNames = search_file_rej(indir_lai_year, ['h5'], 'xml')
        fileNames.sort()
        
        for i, fileName in enumerate(fileNames):
            print(i, fileName)
            
            # 从文件名中提取年份和年积日
            # 假设文件名格式为 LAI_2002001.h5
            base_name = os.path.splitext(fileName)[0]  # 去掉扩展名
            if base_name.startswith('LAI_'):
                date_str = base_name[4:]  # 去掉'LAI_'前缀
                file_year = int(date_str[:4])  # 前4位是年份
                doy = int(date_str[4:])  # 后3位是年积日
                
                # 转换年积日为月日
                month, day = doy2date(file_year, doy)
                
                # 创建日期字符串 (年月日格式)
                date_formatted = f"{file_year}-{month:02d}-{day:02d}"
                
                # 读取LAI数据
                lai = read_h5py_item(indir_lai_year + fileName, 'data')
                lai = np.array(lai) / 1000
                lai_value = lai[indx, indy]
                
                print(f"位置({indx},{indy})的LAI值: {lai_value}")
                
                # 存储结果
                results.append({
                    'date': date_formatted,
                    'lai_value': lai_value
                })
    
    # 将结果转换为DataFrame并保存为CSV
    if results:
        df = pd.DataFrame(results)
        output_csv = f'Dahra_lai.csv'
        df.to_csv(output_csv, index=False)
        print(f"结果已保存到: {output_csv}")
        print(f"共处理了 {len(results)} 个文件")
    else:
        print("没有找到任何数据文件")