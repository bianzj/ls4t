from utils.old.util import *

'''2024.6.20'''
'''解决提取数据少一位的问题'''

indir = r"D:\data\AATSR_product\Fluxnet_AATSR\0_raw_h5_2002-2012\\"

sites = search_dir(indir,'')
for site in sites:
    indir_site = indir + site  + r"\\"
    fileNames = search_file(indir_site,['.h5'])
    for fileName in fileNames:
        if (len(fileName)!=24):
            print(fileName)
            files = search_file(indir_site,[fileName[:-3]])
            if len(files) == 2:
                if len(files[0]) == 24:
                    fn = files[0]
                else:
                    fn = files[1]
                os.remove(indir_site + fn)
                os.rename(indir_site + fileName,indir_site + fn)
            elif len(files) ==1:
                print("Lack origin!")