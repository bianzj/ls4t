import os
from osgeo import gdal
import numpy as np

def diagnose_tiff_file(file_path):
    """诊断TIFF文件的问题"""
    print(f"\n=== 诊断文件: {file_path} ===")
    
    # 检查文件是否存在
    if not os.path.exists(file_path):
        print("❌ 文件不存在")
        return
    
    print(f"文件大小: {os.path.getsize(file_path) / (1024*1024):.2f} MB")
    
    # 方法1: 直接使用gdal.Open
    print("\n1. 使用gdal.Open直接打开:")
    dataset = gdal.Open(file_path, gdal.GA_ReadOnly)
    if dataset is None:
        print("❌ gdal.Open无法打开文件")
        print(f"GDAL错误: {gdal.GetLastErrorMsg()}")
    else:
        print("✅ gdal.Open成功打开文件")
        print(f"  波段数量: {dataset.RasterCount}")
        print(f"  尺寸: {dataset.RasterXSize} x {dataset.RasterYSize}")
        print(f"  投影: {dataset.GetProjection()[:50]}...")
        
        # 检查每个波段
        for i in range(1, dataset.RasterCount + 1):
            band = dataset.GetRasterBand(i)
            print(f"  波段 {i}: 数据类型={gdal.GetDataTypeName(band.DataType)}, "
                  f"无数据值={band.GetNoDataValue()}")
        
        dataset = None
    
    # 方法2: 使用gdal.Info获取详细信息
    print("\n2. 使用gdal.Info获取详细信息:")
    try:
        info = gdal.Info(file_path)
        print("✅ gdal.Info成功")
        print(info[:500] + "..." if len(info) > 500 else info)
    except Exception as e:
        print(f"❌ gdal.Info失败: {e}")
    
    # 方法3: 尝试不同的驱动
    print("\n3. 尝试不同的驱动:")
    drivers_to_try = ['GTiff', 'HFA', 'VRT']  # 常见的驱动
    
    for driver_name in drivers_to_try:
        driver = gdal.GetDriverByName(driver_name)
        if driver:
            dataset = gdal.Open(file_path, gdal.GA_ReadOnly)
            if dataset:
                print(f"✅ 使用驱动 '{driver_name}' 成功")
                dataset = None
                break
            else:
                print(f"❌ 驱动 '{driver_name}' 失败")
        else:
            print(f"❌ 驱动 '{driver_name}' 不可用")
    
    # 方法4: 使用VRT作为中间格式
    print("\n4. 尝试使用VRT中间格式:")
    try:
        vrt_file = '/tmp/temp.vrt'
        vrt_ds = gdal.BuildVRT(vrt_file, file_path)
        if vrt_ds:
            print("✅ VRT创建成功")
            print(f"  VRT波段数量: {vrt_ds.RasterCount}")
            vrt_ds = None
            if os.path.exists(vrt_file):
                os.remove(vrt_file)
        else:
            print("❌ VRT创建失败")
    except Exception as e:
        print(f"❌ VRT创建异常: {e}")

# 测试您的文件
if __name__ == '__main__':
    # 替换为您的实际文件路径
    test_files = [
        '/media/hero/lsct04/aatsr_lsct_month_v0/aatsr_2012_04_night.tif',
        '/media/hero/lsct04/aatsr_lsct_month_v0/aatsr_2012_04_day.tif'
    ]
    
    for test_file in test_files:
        diagnose_tiff_file(test_file)

    