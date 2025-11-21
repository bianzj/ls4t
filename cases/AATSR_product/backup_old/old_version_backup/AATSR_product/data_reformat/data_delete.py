import calendar
import glob
from utils.old.util import *

'''2024.6.3'''
'''删除2009年vza_n,vaa_n,vza_f,vaa_f'''

indir = r"E:\AATSR\2011\tif\\"

for month in range(1,13):
    daynum = calendar.monthrange(2009,month)[1]
    for day in range(1,daynum+1):
        indir_day = indir + "%02d//%02d" % (month,day)
        if not os.path.exists(indir_day): continue

        files_to_delete = glob.glob(os.path.join(indir_day, '*vza_n.tif')) + glob.glob(
            os.path.join(indir_day, '*vza_f.tif')) + glob.glob(
            os.path.join(indir_day, '*vaa_n.tif'))+ glob.glob(
            os.path.join(indir_day, '*vaa_f.tif'))

        # 删除找到的文件
        for file_path in files_to_delete:
            try:
                os.remove(file_path)
                print(f'Successfully deleted: {file_path}')
            except Exception as e:
                print(f'Error deleting file {file_path}: {e}')