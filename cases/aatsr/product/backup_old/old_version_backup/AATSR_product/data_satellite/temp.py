from utils.old.util import *

infile = r"D:\data\Veg_para\Tree_cover(TCC)\global_TreeCover2010_0.01.tif"
# infile = r"D:\data\Veg_para\Tree_density(STD)\global_TreeDensity_0.01.tif"

lat_ = np.asarray([38.54043])
lon_ = np.asarray([-8.003297])
tcc, ns, nl, nb, geog, proj, dataset = read_image_dataset_gdal(infile)
imagex_, imagey_ = loc2map(lat_, lon_, dataset)
print(imagex_,imagey_)
print(tcc[imagex_,imagey_])