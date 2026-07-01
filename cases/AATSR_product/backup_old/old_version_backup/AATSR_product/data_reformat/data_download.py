import calendar

from utils.old.util import *

'''2024.6.3'''
'''删除2009年vza_n,vaa_n,vza_f,vaa_f'''

year = 2004
for year in range(year,year+1):
    for month in range(2, 5):
        daynum = calendar.monthrange(year, month)[1]
        for day in range(1, daynum + 1):
            dir = r"H:\AATSR\%04d\tif\%02d\%02d\\" %(year,month,day)
            if not os.path.exists(dir): continue
            fileNames = search_file(dir,'.tif')
            if len(fileNames) == 0: continue
            print(f"scp remote-server:/data1/public1/Bianzj/AATSR/AATSR_tif/%04d/%02d/%02d/*clo_n.tif '/drives/h/AATSR/%04d/tif/%02d/%02d/' &&" %(year,month,day,year,month,day))
            print(
                f"scp remote-server:/data1/public1/Bianzj/AATSR/AATSR_tif/%04d/%02d/%02d/*clo_f.tif '/drives/h/AATSR/%04d/tif/%02d/%02d/' &&" % (
                year, month, day, year, month, day))
            print(
                f"scp remote-server:/data1/public1/Bianzj/AATSR/AATSR_tif/%04d/%02d/%02d/*saa.tif '/drives/h/AATSR/%04d/tif/%02d/%02d/' &&" % (
                year, month, day, year, month, day))

