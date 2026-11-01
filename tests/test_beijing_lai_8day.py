"""Numerical contracts for the case: calendar, provenance, masks and seasonal recovery."""
import importlib.util
from pathlib import Path
import numpy as np
import pytest

for optional_dependency in ["rasterio", "pyproj", "numba"]:
    pytest.importorskip(optional_dependency)

path=Path(__file__).resolve().parent/'run.py'
if not path.exists():
    path=Path(__file__).resolve().parents[1]/'cases'/'landsat-beijing-lai'/'run.py'
spec=importlib.util.spec_from_file_location('beijing_lai_case',path)
m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)

def test_calendar_has_complete_years_and_no_2026():
 cal=m.build_calendar(2015,2025)
 assert len(cal)==506
 for year in range(2015,2026):
  rr=[r for r in cal if r['start'].year==year]
  assert len(rr)==46 and rr[-1]['stop']==m.date(year+1,1,1)
  assert sum(r['days'] for r in rr)==(m.date(year+1,1,1)-m.date(year,1,1)).days
 assert cal[-1]['stop']==m.date(2026,1,1)

def test_linear_anchors_and_no_extrapolation_without_seasonal_support():
 x=np.array([0.,16.,32.]);X=np.ones((3,5));vals=np.array([0,1000,65535],np.uint16)
 v,code,near=m.estimate(8.,x,vals,X,X[0],np.zeros(5),False,32,96,64,-1e9,-1e9)
 assert abs(v-.5)<1e-9 and code==2 and near==8
 assert m.estimate(100.,x,vals,X,X[0],np.zeros(5),False,32,96,64,-1e9,-1e9)[1]==0

def test_reconstruction_keeps_observed_mean_and_nodata_separate():
 x=np.array([0.,4.,16.]);X=np.ones((3,5));cube=np.array([[1000,65535,1000],[3000,65535,1000],[3000,65535,1000]],np.uint16)
 starts=np.array([0.,8.,16.]);ends=starts+8;centers=starts+3.5
 r=m.reconstruct(cube,np.array([True,True,False]),x,X,np.zeros(3,np.int32),np.zeros(3,np.int32),centers,np.ones((3,5)),starts,ends,.15,8,3,3,32,96,64)
 assert r[0,0,0]==2000 and r[0,1,0]==1 and r[0,3,0]==2
 assert r[1,1,0]==2 and r[1,3,0]==0
 assert np.all(r[:,0,1]==65535) and np.all(r[:,1,1]==0)
 assert np.all(r[:,:,2]==65535)

def test_harmonic_fit_does_not_use_withheld_values():
 dates=[m.date(y,mo,15) for y in range(2015,2026) for mo in range(1,13)]
 X=m.basis(dates);x=np.arange(len(dates),dtype=float)
 years=np.array([d.year-2015 for d in dates],np.int32);q=np.array([(d.month-1)//3 for d in dates],np.int32)
 truth=1.5+.7*X[:,1]-.3*X[:,2]
 vals=np.rint(truth*1000).astype(np.uint16)
 lo,hi=55.,65.
 beta,ok=m.fit_curve(vals,X,years,q,lo,hi,x,.15,8,3,3)
 altered=vals.copy();altered[55:66]=3500
 beta2,ok2=m.fit_curve(altered,X,years,q,lo,hi,x,.15,8,3,3)
 assert ok and ok2 and np.allclose(beta,beta2)
 assert np.sqrt(np.mean((X@beta-truth)**2))<.03


def test_frozen_seasonal_prior_ignores_extension_year_but_keeps_anchors():
 dates=[m.date(y,mo,15) for y in range(2015,2027) for mo in range(1,13)]
 X=m.basis(dates);x=np.arange(len(dates),dtype=float)
 years=np.array([d.year-2015 if d.year<=2025 else -1 for d in dates],np.int32)
 q=np.array([(d.month-1)//3 for d in dates],np.int32)
 vals=np.rint((1.5+.5*X[:,1])*1000).astype(np.uint16)
 a,ok=m.fit_curve(vals,X,years,q,-1e9,-1e9,x,.15,8,3,3)
 vals[years<0]=3500
 b,ok2=m.fit_curve(vals,X,years,q,-1e9,-1e9,x,.15,8,3,3)
 assert ok and ok2 and np.allclose(a,b)
 assert m.estimate(x[-1],x,vals,X,X[-1],b,ok,32,96,64,-1e9,-1e9)[0]==3.5


def test_seasonal_fit_supports_twelve_distinct_year_indices():
 dates=[m.date(y,mo,15) for y in range(2015,2027) for mo in range(1,13)]
 X=m.basis(dates);x=np.arange(len(dates),dtype=float)
 years=np.array([d.year-2015 for d in dates],np.int32)
 q=np.array([(d.month-1)//3 for d in dates],np.int32)
 beta,ok=m.fit_curve(np.full(len(dates),1500,np.uint16),X,years,q,-1e9,-1e9,x,.15,8,3,3)
 assert ok and np.max(np.abs(X@beta-1.5))<1e-6
