from util import *
import zipfile


'''
数据的批量解压
'''


indir = r'E:\slstr_2022\\'
outdir = r'E:\slstr_2022\\'
filenames = search_file(indir,'zip')

print(filenames)
for filename in filenames:
    infile = indir + filename
    if(os.path.exists(indir+filename[:-4]+'.SEN3')==1):
        continue

    print(infile)
    with zipfile.ZipFile(indir+filename,'r') as z:
        z.extractall(outdir)

