from utils.old.util import *

'''2024.4.18'''
'''统计ERA5 land utc11 Ts-lst'''

indir = r"G:\ERA5_land_2002-2012\Monthly_Average_Hour\tif_loc_11\\"
outdir = r"G:\ERA5_land_2002-2012\Monthly_Average_Hour\Ts-lst\\"

time = []
delta_list = []
for year in range(2002,2013):
    fileNames = search_file_rej(indir + r"%04d\\" %year,['.tif'],'enp')
    for fileName in fileNames:
        print(fileName)
        infile = indir + r"%04d\\" %year + fileName
        data, im_width, im_height, im_bands, im_geotrans, im_proj = read_image_gdal(infile)
        skt = data[0,:,:]/100
        stl1 = data[1,:,:]/100
        t2m = data[2,:,:]/100
        delta = stl1[stl1!=0] - skt[stl1!=0]
        print(np.mean(delta[np.abs(delta)<20]))
        delta_list.append(np.mean(delta[np.abs(delta)<20]))
        time.append(int(fileName[-10:-4]))

        plt.hist(delta, bins=30, color='skyblue', edgecolor='black')
        plt.xlabel('Delta')
        plt.ylabel('Frequency')
        plt.title('Histogram of Delta')
        plt.grid(True)
        plt.xlim(-20,20)
        plt.savefig(outdir + fileName[:-4] + '.png')
        plt.close()

delta = np.array(delta_list)
time = np.array(time)

plt.figure(figsize=(6,4))
x = range(len(delta_list))
plt.plot(x[:12],delta[:12])
time_ = time[:12]
plt.xticks(x[:12],time_,rotation='45')
plt.savefig(outdir + 'Range.png')
plt.tight_layout()
plt.show()
