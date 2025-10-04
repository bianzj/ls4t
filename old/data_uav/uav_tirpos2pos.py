import numpy as np

'''
将Tau2相机自带的POS信息转换成可读可用的结果
'''

def read_txt2pos(infile):
    '''
    将Tau2的Pos数据进行了整理，得到结果
    :param infile:
    :return: 参考，经度，纬度和高度
    '''
    ref_ = []
    lat_ = []
    lon_ = []
    ele_ = []
    with open(infile) as f:
        line = f.readline()
        while line:
            fields = line.split(',')
            if np.size(fields) < 3:
                line = f.readline()
                continue
            ref_.append(fields[0][:5])
            lat_.append(fields[2])
            lon_.append(fields[4])
            ele_.append(fields[9])
            line = f.readline()
    ref_ = np.asarray(ref_, dtype=int)
    lat_ = np.asarray(lat_,dtype=float)/100.0
    lon_ = np.asarray(lon_,dtype=float)/100.0
    ele_ = np.asarray(ele_,dtype=float)
    return ref_,lon_,lat_,ele_

infile1 = r'E:\20211414chengde\rawdata\14\tir\DIR003\MID000\GPS000.txt'
infile2 = r'E:\20211414chengde\rawdata\14\tir\DIR003\MID001\GPS001.txt'

camera = 0
### 假设高度都是100米
height = 100
outfile = r'E:\20211414chengde\rawdata\14\tir\DIR003\GPS_%d.txt'%height


pos1 = read_txt2pos(infile1)
pos2 = read_txt2pos(infile2)

pos = np.hstack([pos1,pos2])
pos = np.transpose(pos)
fo = open(outfile,'w')
pos[:,3] = height
numline,numpo = np.shape(pos)
for k in range(0,numline):
    fo.writelines(["%05d.tif "%pos[k,0],"%.5f "%pos[k,1],"%.5f "%pos[k,2],"%.5f \n"%pos[k,3]])
fo.close()

