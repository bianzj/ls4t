import numpy as np
from util.util import *

'''
例如文献中的图，没有原始数据
从图片上获取数据，并保存成txt
'''


infile = r'D:\code\ShIP_LSTNDVI\data\Cropland.jpg'

mydata,ns,nl,nb,geog,proj = read_image_gdal(infile)

g = mydata[1,:,:]
r = mydata[0,:,:]
b = mydata[2,:,:]
upper_ = []
lower_ = []
center_ = []
for ks in range(1,ns):
    tempg = g[20:210,ks]
    tempr = r[20:210,ks]
    tempb = b[20:210,ks]
    tempp = np.where((tempr >= 80) & (tempr <= 150) &
                     (tempg >= 150) & (tempg <= 180) &
                     (tempb >= 201) & (tempb <= 220))
    if np.size(tempp)<=1:
        upper = np.max(temppp)
        lower = np.min(temppp)
        continue
    temppp = tempp
    upper = np.max(temppp)
    lower = np.min(temppp)
    center = (upper + lower) * 0.5
    upper_.append(upper)
    lower_.append(lower)
    center_.append(center)

upper_ = np.asarray(upper_)
lower_ = np.asarray(lower_)
center_ = np.asarray(center_)

bl = (300-20-center_)/300.0

Cab = bl*60

bll = 413/365.0
x = (np.linspace(1,365,365)*bll + 0.5)-1
y = Cab[x.astype(np.int)]

plt.plot(y,'o-')
plt.show()

outfile = r'D:\code\ShIP_LSTNDVI\data\Cab.txt'
np.savetxt(outfile,y,fmt='%.2f')