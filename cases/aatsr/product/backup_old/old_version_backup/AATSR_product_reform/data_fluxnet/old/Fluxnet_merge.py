from utils.old.util import *

'''2024.7.5'''
'''将所有数据进行合成'''

indir = r"D:\data\AATSR_product\Fluxnet_AATSR\2_val_2002-2012\0_raw_h5_2002-2012\Merge_csv\\"
outfile = r"D:\data\AATSR_product\Fluxnet_AATSR\2_val_2002-2012\0_raw_h5_2002-2012\\All_sites.csv"

fileNames = search_file(indir,'.csv')
all_data = pd.DataFrame()

for fileName in fileNames:
    print(fileName)
    file_path = os.path.join(indir, fileName)
    data = pd.read_csv(file_path)

    # Add a column for the site name (file name without extension)
    site_name = fileName[:-4]
    data['site_name'] = site_name
    data = data.fillna(-9999).replace(0, -9999)
    # Append the data to the all_data DataFrame
    all_data = pd.concat([all_data, data], ignore_index=True)

# Save the combined data to a CSV file
all_data.to_csv(outfile, index=False)
