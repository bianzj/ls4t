"""Read-only diagnostic of a prior daytime LSCT3 trial; writes diagnostics only."""
import os
os.environ['PATH']='C:/work/miniconda/envs/python311/Library/bin;'+os.environ.get('PATH','')
os.environ['OPENBLAS_NUM_THREADS']='1'
os.environ['OMP_NUM_THREADS']='1'
os.environ['PYTHONDONTWRITEBYTECODE']='1'
import sys,json,inspect,hashlib
from pathlib import Path
sys.path.insert(0,'C:/work/ls4t')
sys.path.insert(0,str(Path(__file__).resolve().parent))
import numpy as np
from scipy.ndimage import distance_transform_edt,maximum_filter
from scipy.optimize import minimize
from osgeo import gdal
gdal.UseExceptions()
import retrieval_v5 as m
# This diagnostic reproduces the preserved unfiltered trial, even when the
# current production configuration has a newer temperature filter.
cfg=json.loads(Path('E:/lsct/lsct3/feasibility_20261101_numpy2/report.json').read_text())['configuration']
out=Path(cfg['output_root'])/'diagnostics'
out.mkdir(parents=True,exist_ok=True)
name=cfg['scene'];r,c=366,769
# Evaluate the unchanged historical calculation, then return its locals before
# any product or marker write. This diagnostic never alters source products.
source=inspect.getsource(m.scene).replace('def scene(', 'def diagnostic_scene(',1)
needle='    for name,array,description in zip(PRODUCTS,outputs,'
assert source.count(needle)==1
source=source.replace(needle,'    return locals()\n'+needle)
exec(compile(source,'<read-only-scene-diagnostic>','exec'),m.__dict__)
m.setup(cfg['source_root'],tuple(cfg['region_wsen']))
m._STATE['output_dir']=str(out/'not_written')
s=m.diagnostic_scene(cfg['year'],name)
assert isinstance(s,dict) and 'outputs' in s
assert not (out/'not_written').exists()
views=s['views'];shape=s['lat'].shape
original=Path(cfg['output_root'])/'scene'/name
saved=[m.read(original/f) for f in m.PRODUCTS]
assert all(np.array_equal(a,b) for a,b in zip(saved,s['outputs']))
valid=saved[0]>0;cold=valid&(saved[0]<250)
flags={};dist={};data={};tif=Path(cfg['source_root'])/str(cfg['year'])/'tif'/name
for view in ('nadir','obliq'):
 a=m.read(tif/f'cloud_{view}.tif')
 if view=='nadir':a=a[:,m.adjust_xmin_no_g:m.adjust_xmax_no_g]
 flags[view]=a;dist[view]=distance_transform_edt(a==0)
 for field in ('red','nir','bt8','bt9'):
  a=m.read(tif/f'{field}_{view}.tif')
  if view=='nadir':a=a[:,m.adjust_xmin_no_g:m.adjust_xmax_no_g]
  data[f'{field}_{view}']=a

def summary(a,mask):
 v=np.asarray(a)[mask];v=v[np.isfinite(v)]
 return {'n':len(v),'min':float(np.min(v)),'median':float(np.median(v)),'max':float(np.max(v)),'p05':float(np.quantile(v,.05)),'p95':float(np.quantile(v,.95))} if len(v) else None

def solution(gr,rhs,maxiter=2):
 tc=(views[0][3][np.array([r]),np.array([c])]+views[1][3][np.array([r]),np.array([c])])/2
 sigma2=float(np.maximum((m.NOISE_K*m.derivative(tc))**2,1e-10)[0])
 A=np.asarray(gr,np.float64)/sigma2+s['prior_precision'];b=np.asarray(rhs,np.float64)/sigma2+s['prior_precision']@s['x0']
 share=float(np.clip(views[1][4][r,c]/max(views[1][5][r,c],1e-6),0,1))
 WW=np.concatenate([v[0][r-2:r+3,c-2:c+3].reshape(-1,3) for v in views]).astype(np.float64)
 YY=np.concatenate([v[1][r-2:r+3,c-2:c+3].reshape(-1) for v in views]).astype(np.float64)
 lo=float(m.planck(m.WL,200));hi=float(m.planck(m.WL,400))
 def actual(z):
  if np.any(z<=0):return 1e99
  gap=float(m.inv_planck(m.WL,share*z[0]+(1-share)*z[1])-m.inv_planck(m.WL,z[2]))
  return float(np.sum((WW@z-YY)**2)/sigma2+(z-s['x0'])@s['prior_precision']@(z-s['x0'])+((gap-9)/10)**2)
 def describe(z):
  temp=m.inv_planck(m.WL,z) if np.all(z>0) else np.full(3,np.nan)
  mix=share*z[0]+(1-share)*z[1]
  return {'radiances':z.tolist(),'temp_sun_shade_veg_K':temp.tolist(),'soil_K':float(m.inv_planck(m.WL,mix)) if mix>0 else None,'objective':actual(z)}
 x=np.linalg.solve(A,b);traj=[describe(x)]
 for _ in range(maxiter):
  xs=np.clip(x,lo,hi);mix=share*xs[0]+(1-share)*xs[1]
  ts=m.inv_planck(m.WL,mix);tv=m.inv_planck(m.WL,xs[2]);diff=ts-tv
  J=np.array([share/max(m.derivative(ts),1e-8),(1-share)/max(m.derivative(ts),1e-8),-1/max(m.derivative(tv),1e-8)])
  target=9-diff+J@x
  ag=A+np.outer(J,J)/100;bg=b+J*target/100
  x=np.linalg.solve(ag,bg);traj.append(describe(x))
 if x[0]<x[1]:
  C=np.array([[1.,0.],[1.,0.],[0.,1.]])
  x=C@np.linalg.solve(C.T@ag@C,C.T@bg);traj.append({'projection':True,**describe(x)})
 opt=minimize(actual,np.clip(x,lo,hi),bounds=[(lo,hi)]*3,method='SLSQP',constraints=[{'type':'ineq','fun':lambda z:z[0]-z[1]}],options={'ftol':1e-10,'maxiter':500})
 return {'trajectory':traj,'sigma2':sigma2,'condition_gram':float(np.linalg.cond(gr)),'condition_A':float(np.linalg.cond(A)),'gram_eigenvalues':np.linalg.eigvalsh(gr).tolist(),'design_singular_values':np.linalg.svd(WW,compute_uv=False).tolist(),'soil_sun_share':share,'bounded_nonlinear_diagnostic':{'success':bool(opt.success),'message':str(opt.message),**describe(opt.x)}}

report={'scene':name,'focus':{'row_col':[r,c],'lat':float(s['lat'][r,c]),'lon':float(s['lon'][r,c]),'lai':float(s['lai'][r,c]),'landcover_class':int(s['cls'][r,c]),'soil_emis':float(s['es'][r,c]),'vegetation_emis':float(s['ev'][r,c]),'solar_zenith_deg':float(s['sza'][r,c]),'outputs_K':{f:float(a[r,c]) for f,a in zip(m.PRODUCTS,saved)},'views':{}},'counts':{'valid_output':int(valid.sum()),'soil_below_250K':int(cold.sum())},'scope':'No product reprocessing or changes. Raw/cloud inputs not modified. Diagnostic nonlinear optimum is not a corrected/validated product.'}
for i,v in enumerate(('nadir','obliq')):
 W,Y,good,T,sun,soil=views[i]
 win=(slice(r-2,r+3),slice(c-2,c+3))
 report['focus']['views'][v]={'cloud_flag':int(flags[v][r,c]),'flagged_5x5':int((flags[v][win]!=0).sum()),'good_5x5':int(good[win].sum()),'nearest_flagged_distance_pixels':float(dist[v][r,c]),'lst_K':float(T[r,c]),'bt8_K':float(data[f'bt8_{v}'][r,c]/100),'bt9_K':float(data[f'bt9_{v}'][r,c]/100),'red_raw':float(data[f'red_{v}'][r,c]),'nir_raw':float(data[f'nir_{v}'][r,c]),'soil_fraction':float(soil[r,c]),'sunlit_fraction':float(sun[r,c]),'shaded_fraction':float(soil[r,c]-sun[r,c]),'W':W[r,c].tolist(),'lst_5x5_K':T[win].tolist(),'cloud_5x5':flags[v][win].tolist(),'good_lst_5x5':summary(T[win],good[win])}
 report.setdefault('population',{})[v]={}
 for label,mask in [('all_valid',valid),('soil_below_250K',cold)]:
  report['population'][v][label]={'cloud_nearest_pixels':summary(dist[v],mask),'cloud_within_2_pixels':int((mask&(maximum_filter((flags[v]!=0).astype(np.uint8),size=5)>0)).sum()),'cloud_within_5_pixels':int((mask&(maximum_filter((flags[v]!=0).astype(np.uint8),size=11)>0)).sum()),'lst_K':summary(T,mask),'soil_fraction':summary(soil,mask)}
report['population']['lai']={'all_valid':summary(s['lai'],valid),'soil_below_250K':summary(s['lai'],cold)}
report['population']['absolute_view_lst_difference_K']={'all_valid':summary(abs(views[0][3]-views[1][3]),valid),'soil_below_250K':summary(abs(views[0][3]-views[1][3]),cold)}
report['population']['valid_extent']={'lat_min':float(s['lat'][valid].min()),'lat_max':float(s['lat'][valid].max()),'lon_min':float(s['lon'][valid].min()),'lon_max':float(s['lon'][valid].max())}
report['focus']['float32_filtered_solution']=solution(s['gram'][r,c],s['rhs'][r,c])
reproduced=report['focus']['float32_filtered_solution']['trajectory'][-1]
assert abs(reproduced['soil_K']-float(saved[0][r,c]))<5e-4,(reproduced['soil_K'],saved[0][r,c])
WW=np.concatenate([v[0][r-2:r+3,c-2:c+3].reshape(-1,3) for v in views]).astype(np.float64)
YY=np.concatenate([v[1][r-2:r+3,c-2:c+3].reshape(-1) for v in views]).astype(np.float64)
report['focus']['float64_direct_solution']=solution(WW.T@WW,WW.T@YY)
rawroot=Path(cfg['source_root'])/str(cfg['year'])/'raw'
report['raw_availability']={'exact_scene_exists':(rawroot/name).exists(),'timestamp_matches':[p.name for p in rawroot.iterdir() if '20240426T140123' in p.name] if rawroot.exists() else []}
report['cold_pixels']=[{'row':int(rr),'col':int(cc),'lat':float(s['lat'][rr,cc]),'lon':float(s['lon'][rr,cc]),'soil_K':float(saved[0][rr,cc]),'vegetation_K':float(saved[1][rr,cc]),'lst_nadir_K':float(views[0][3][rr,cc]),'lst_obliq_K':float(views[1][3][rr,cc]),'lai':float(s['lai'][rr,cc]),'distance_cloud_nadir_pixels':float(dist['nadir'][rr,cc]),'distance_cloud_oblique_pixels':float(dist['obliq'][rr,cc])} for rr,cc in zip(*np.where(cold))]
def json_finite(value):
 if isinstance(value,dict):return {k:json_finite(v) for k,v in value.items()}
 if isinstance(value,list):return [json_finite(v) for v in value]
 if isinstance(value,float) and not np.isfinite(value):return None
 return value
report=json_finite(report)
report['code_sha256']=hashlib.sha256(Path(__file__).read_bytes()).hexdigest()
p=out/'cloud_cold_diagnosis.json';p.write_text(json.dumps(report,indent=2,allow_nan=False),encoding='utf-8')
win=(slice(r-40,r+41),slice(c-40,c+41))
patch={f'product_{k}':a[win] for k,a in zip(('soil','vegetation','sunlit_soil','shaded_soil'),saved)}
patch.update({f'cloud_{v}':a[win] for v,a in flags.items()})
patch.update({f'lst_{v}':views[i][3][win] for i,v in enumerate(('nadir','obliq'))})
patch.update({k:a[win] for k,a in data.items()})
patch.update({'lat':s['lat'][win],'lon':s['lon'][win],'lai':s['lai'][win]})
np.savez_compressed(out/'focus_patch.npz',**patch)
print(json.dumps({k:v for k,v in report.items() if k not in ('cold_pixels',)},indent=2))
