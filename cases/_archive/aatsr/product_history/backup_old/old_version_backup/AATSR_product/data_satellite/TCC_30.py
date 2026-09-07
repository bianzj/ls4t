from utils.old.util import *
import zipfile

'''2024.7.3'''
'''TCC_30'''

indir_zip = r"C:\Users\ShIP\Downloads\TCC\\"
indir_raw = r"D:\data\Veg_para\TCC\raw\\"

ifunzip = 1

if ifunzip:
    fileNames = search_file(indir_zip,'zip')
    for i,fileName in enumerate(fileNames):
        print(i,fileName)
        infile = os.path.join(indir_zip,fileName)
        extract_path = indir_raw + fileName[:-4]
        with zipfile.ZipFile(infile, 'r') as zip_ref:
            zip_ref.extractall(extract_path)