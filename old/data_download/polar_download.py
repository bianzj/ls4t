from subprocess import Popen
from util.util import *

'''
从earthdata和copernicus下载数据
From earthdata, download remote sensing data onboard polar satellite, such as modis, viirs, avhrr;
From earthdata, download remote sensing data onboard polar satellite, such as sentinel;
'''

'''
从earthdata下载，
需要现在系统里下单，
然后通过下单后的订单号下载
'''
k = 0
target_dir = 'F:/vnp' ### target directory
order_number = '501783069' #### order number
# strips = 'Ymlhbnpqb3RoZXI6WW1saGJucHFRSEpoWkdrdVlXTXVZMjQ9OjE2NTMwMjk3NjU6NTg1ODdmODg5MWI5Zjg3NzJhNWU5YjVhYjI0MzA1NzViNzA1Zjg2ZA'
while k<100:
    p = Popen('wget -e robots=off -m -np -R .html,.tmp -nH -c --cut-dirs=3 "https://ladsweb.modaps.eosdis.nasa.gov/archive/orders/'+order_number+'/" --header "Authorization: Bearer Ymlhbnpqb3RoZXI6WW1saGJucHFRSEpoWkdrdVlXTXVZMjQ9OjE2NTMwMjk3NjU6NTg1ODdmODg5MWI5Zjg3NzJhNWU5YjVhYjI0MzA1NzViNzA1Zjg2ZA" -P '+target_dir)
    stdout, stderr = p.communicate()
    k = k+1
print('success!')


#### 下载ecostress
# infile = r'E:\ecos_2019\123.txt'
# usernamee = "bianzjnew"
# password = "123457Abc"
# outdir = r'E:\ecos_2019\\'
# tempdata = read_txt_str(infile,'\n')
# for k in range(1):
#     for temp in tempdata:
#         # if 'https' not in temp:continue
#         print(temp)
#         dirname = temp[0][72:108]
#         filename = temp[0][68:]
#         url = temp[0]
#         print(filename,url)
#         line = r'wget -c --no-check-certificate --user=' +usernamee + " --password=" +password  + " " +url +  " -O " +outdir+filename
#         p = Popen(line)
#         stdout,stderr = p.communicate()


'''
copernicus下载，
会从系统下载下来包含文件名和路径的文档，
先从文档中解析出路径，然后进行下载
'''
infile = r'C:\Users\zzz\Downloads\products_pbt.meta4'
usernamee = "bianzj"
password = "123457Abc"
outdir = r'E:\slstr_2022\\'
tempdata = read_txt_str(infile,'name="')

for k in range(10):
    for temp in tempdata[0]:
        if 'zip' not in temp:continue
        filename = temp[:98]
        url = temp[183:183+98]
        print(filename,url)
        line = r'wget -c --no-check-certificate --user=' +usernamee + " --password=" +password  + " " +url +  " -O " +outdir+filename
        p = Popen(line)
        stdout,stderr = p.communicate()


    # for temp in tempdata[1]:
    #     if 'zip' not in temp: continue
    #     filename = temp[:98]
    #     url = temp[182:182+98]
    #     print(filename, url)
    #     # line = r'wget --no-check-certificate --user=' + usernamee + " --password=" + password + " " + temp[:98] + " -P " + outdir
    #     # p = Popen(line)
    #     # stdout, stderr = p.communicate()
    #     # line = r'wget --no-check-certificate --user=' +usernamee + " --password=" +password  + " " +temp[:98] + " -P "+outdir
    #     # p = Popen(line)
    #     # stdout,stderr = p.communicate()