

from geotiepoints.geointerpolator import GeoInterpolator
import numpy as np
# 假设你已读取了MSG数据文件，并获取了其行、列数
lines = 3712  # SEVIRI全盘数据的标准行数
cols = 3712   # 标准列数
# 创建插值器对象
interpolator = GeoInterpolator()
# 获取每个像元的经纬度
lons, lats = interpolator.get_lonlats()
# lons, lats 现在是形状为 (3712, 3712) 的数组，包含了每个像元的经度和纬度。


