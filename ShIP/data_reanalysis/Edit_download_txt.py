import os.path

from util.util import *

'''脚本用于检查文本文件下载地址'''

dir = r"F:\data\S3_2020\\"
infile =  r"F:\data\S3_2020\\S3_2020(15)_Europe.txt"
outfile = r"F:\data\S3_2020\\S3_2020(15)_Europe_new.txt"

data = read_txt_str(infile,'\n')
new_url = []
count = 0
for i in range(len(data)):
    url = data[i][0]
    fileName = url[-98:]
    search_file = dir + fileName
    if os.path.exists(search_file): continue
    count = count + 1
    new_url.append(url)
    # print(fileName)
print(count)
np.savetxt(outfile,new_url,fmt = '%s')