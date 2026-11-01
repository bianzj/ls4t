import importlib.util
from pathlib import Path
import numpy as np
import pandas as pd
import pytest
for dependency in ['rasterio','pyproj','scipy','shapely','geopandas']:
 pytest.importorskip(dependency)
p=Path(__file__).with_name('run.py')
if not p.exists():p=Path(__file__).parents[1]/'cases'/'beijing-building-structure'/'run.py'
spec=importlib.util.spec_from_file_location('building_case',p);m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)

def test_shifted_exact_overlap_conserves_partial_cells():
 w=m.overlap_matrix(-5,30,2,0,10,4)
 a=np.ones((4,4));out=w.dot((w.dot(a)).T).T
 assert np.allclose(out,[[625,375],[375,225]])
 assert abs(out.sum()-1600)<1e-9

def test_rotated_rectangle_dimensions_are_not_axis_aligned_bbox():
 from shapely.geometry import box
 from shapely.affinity import rotate
 g=rotate(box(0,0,10,20),37)
 length,width,angles,rects=m.rectangles([g])
 assert abs(length[0]-20)<1e-8 and abs(width[0]-10)<1e-8
 assert abs(rects[0].area-200)<1e-8

def test_unknown_cells_are_excluded_from_density_denominator():
 from affine import Affine
 h=np.zeros((4,4));h[0,1]=20;known=np.ones((4,4),bool);known[0,0]=False
 patches=pd.DataFrame({'centroid_east_m':[15.],'centroid_north_m':[35.]})
 out=m.coarse_statistics(h,known,h>0,patches,{'transform':Affine(10,0,0,0,-10,40),'crs':'EPSG:32650'},20)
 cell=out.iloc[0]
 assert cell.known_area_m2==300 and cell.building_area_m2==100
 assert abs(cell.building_density_fraction-1/3)<1e-12 and cell.patch_centroid_count==1
