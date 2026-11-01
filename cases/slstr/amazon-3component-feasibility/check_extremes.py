"""Read trial output and collocated source values for the coldest valid soil result."""
import json
from pathlib import Path
import numpy as np
from osgeo import gdal
gdal.UseExceptions()
cfg=json.loads((Path(__file__).parent/'config.json').read_text());scene=cfg['scene'];base=Path(cfg['source_root'])/str(cfg['year']);out=Path(cfg['output_root'])/'scene'/scene
def read(p):
 d=gdal.Open(str(p));return d.ReadAsArray()
soil=read(out/'soil.tif');veg=read(out/'vegetation.tif');sun=read(out/'sunlit_soil.tif');shade=read(out/'shaded_soil.tif');lst=read(base/'lst'/scene/'lst_obliq.tif').astype('float32')/100
valid=np.isfinite(soil)&(soil>0);idx=np.unravel_index(np.where(valid,soil,np.inf).argmin(),soil.shape)
lat=float(read(base/'tif'/scene/'lat_obliq.tif')[idx])/100;lon=float(read(base/'tif'/scene/'lon_obliq.tif')[idx])/100
lat=-(lat-90) if lat>=90 else lat;lon=-(lon-180) if lon>=180 else lon
r={'row_col':[int(x) for x in idx],'latitude_deg':lat,'longitude_deg':lon,'soil_k':float(soil[idx]),'vegetation_k':float(veg[idx]),'sunlit_soil_k':float(sun[idx]),'shaded_soil_k':float(shade[idx]),'oblique_lst_k':float(lst[idx]),'soil_below_250_count':int(((soil<250)&valid).sum()),'soil_minus_veg_below_minus30_count':int(((soil-veg< -30)&valid).sum()),'interpretation':'Potentially anomalous values for follow-up, not an independent accuracy assessment.'}
(Path(cfg['output_root'])/'extremes.json').write_text(json.dumps(r,indent=2),encoding='utf-8');print(json.dumps(r))
