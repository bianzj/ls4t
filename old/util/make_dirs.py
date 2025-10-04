import os

indir = r'E:\ShIP_DVT\temp\\'
for kmonth in range(1,13):
    for kday in range(1,32):
        path = indir + '%02d\\'%kmonth+'%02d'%kday
        os.makedirs(path)

# indir = r'E:\ShIP_KDTC\Coeff_KDTC_SSVinRL_heihe\\'
# for kmonth in range(1,13):
#     for kday in range(1,32):
#         path = indir + '%02d\\'%kmonth+'%02d'%kday
#         os.makedirs(path)

#
# for kmonth in range(1,13):
#     path = indir +'%02d'%kmonth
#     os.makedirs(path)