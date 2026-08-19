AATSR组分温度反演备忘录

### 数据格式
observe.nc:
    redN,redF,NirN,nirF,bt1N,bt1F,bt2N,bt2F,cloN,cloF
geometry.nc:
    sza,saa,(vzaN,vzaF,vaaN,vaaF)
loc.nc:
    lon.lat,indx,indy
time.nc
    time
lst.nc
    lstN,lstF
lsct_v(n).nc
    Ts(Tsl,Tsh),Tv

### 代码架构：
data_satellite: 数据解压、提取、存h5
inv_lsct: 温度反演
opt_lsct: 组分温度反演
opt_val： 精度验证
util：函数块 rt(辐射传输模块)

### 关键变量格式：
nl,ns : 长(43520)，宽(512)
indx，indy： 点对应WGS84 0.01° 坐标系的行列号
# 观测角度
***N： 垂直观测
***F:  前向观测
# 数据类型(如果只有一种格式不标注)
***_gl: 全球数据WGS84(后可加分辨率_gl1k/_gl5k)
***_st: AATSR条带格式
***_pt: 站点尺度
***_er: ERA5数据后（可加分辨率_er10k/_er25k)


### 更新日程
2024/10/28
开始重构AATSR代码,确定代码格式和规范
重写两组分反演代码

2024/10/30
重构完成标准版组分温度反演算法
测试（43520*51），ns（5*512）约80s,nl（5*43520）约135s。
单个任务越小、塞进去的任务更多，速度更快

2024/11/05
开始跑 lsct v0(单点 两组分) v1（5*5 不加温差限制、 加权重、不考虑森林结构、加范围限制（植被土壤温度在垂直倾斜温度两侧））

2024/11/12
lsct v0 v1 finished


### 后续解决
1.重构：AATSR 如果长度大小不等于43520，存储vzaN/O vaaN/O
2.投影：AATSR 坐标代表的左上角像元带来的上下行轨道的偏差