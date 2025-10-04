from util.util import *
import scipy.io as scio

'''
类似JP的方法，更弱一点，认为所有的图像的观测角度相同
所有图像直接平均（ns,nl），例如（640,480）
得到一副认为包含角度效应的等效的结果，
从该图像（ns，nl)进行了等角度的离散，存入角度矩阵（azim，zen）例如（360,60）
这里的假设是所有图像对应的地表类型一样，而且图像的观测角度也一样；
'''


ns = 480
nl = 640

result = np.zeros([ns,nl])
result_sum = np.zeros([ns,nl])
result_ave = np.zeros([ns,nl])

indir= r'G:\Airborne\heihe20120803\20120803-FLIR\10-2\\'
outfile1 = r'G:\Airborne\heihe20120803\test\\track10_2_ave.tif'
outfile2 = r'G:\Airborne\heihe20120803\test\\track10_2_sta.tif'

infiles = search_file(indir,'MAT')
n_infiles = size(infiles)


'''widas angular information'''
vza,ns,nl,nb,geog,proj = read_image_gdal('D:\code\TiRT_Evaluation\matlab\Zen2.tif')
vaa,ns,nl,nb,geog,proj = read_image_gdal('D:\code\TiRT_Evaluation\matlab\Az2.tif')
vza = np.transpose(vza)
vaa = np.transpose(vaa)

vza[vza<0] = - vza[vza<0]
vaa = vaa + 120+180
vaa = vaa % 360
plt.imshow(vza)
plt.show()
plt.imshow(vaa)
plt.show()
#
for k in range(n_infiles):
    infile = indir + infiles[k]
    temp = scio.loadmat(infile)[infiles[k][:-4]]

    ind = (temp > 297) *(temp < 304)
    result[ind] = result[ind] + temp[ind]
    result_sum[ind] = result_sum[ind] + 1

ind = result_sum > 0
result_ave[ind] = result[ind] / result_sum[ind]

result_sta = np.zeros([50, 360])
for k in range(50):
    for kk in range(360):
        ind = (k-0.5 < vza) *( vza < k+0.5) * (vaa < kk +0.5) *(kk-0.5<vaa)
        if np.sum(ind) > 0:
            result_sta[k, kk] = np.average(result_ave[ind])


plt.imshow(result_ave)
plt.show()
write_image_gdal(result_ave, nl, ns, 1, '', '', outfile1)
write_image_gdal(result_sta, 360, 50, 1, '', '', outfile2)
