"""Validate completed first month independently from the aggregation routine."""
from pathlib import Path
import json
import h5py
import numpy as np
import produce_msg_5x5 as p

root=Path('E:/PRODUCTS/LSCT/MSG_5X5_PHYSICAL_V1')
month=root/'MONTHLY_HOUR/2017/MSG_LSCT_5X5_MONTH_201708_H12.h5'
with h5py.File(month) as f:
    assert f.attrs['complete']==1 and f.attrs['protocol_hash']==p.PROTOCOL_HASH
    count=f['n_obs'][...];expected=f['data'][...];low=f['low_support'][...]
    stamps=json.loads(f.attrs['source_timestamps_json'])
    assert np.array_equal(np.isfinite(expected).all(0),count>0)
    assert np.array_equal(low,((count>0)&(count<3)).astype('uint8'))
    y,x=np.where(count>0); rng=np.random.default_rng(20261009)
    indices=rng.choice(len(y),size=min(1000,len(y)),replace=False);y,x=y[indices],x[indices]
    H,W=count.shape
samples=[];scenes=[]
for stamp in stamps:
    path=p.instant_path(root,stamp)
    with h5py.File(path) as f:
        a=f['data'][...];n=f['valid_neighbors'][...];q=f['qa'][...]
        valid=np.all(a!=0,0)
        assert np.array_equal(np.any(a!=0,0),valid)
        assert np.all((a[:,valid]>=25000)&(a[:,valid]<=35000))
        assert np.all(n[valid]>=10) and np.all((q[valid]&15)==0)
        assert np.all(a[2,valid]>=a[3,valid])
        assert np.all(a[0,valid]>=a[3,valid]) and np.all(a[0,valid]<=a[2,valid])
        assert f.attrs['valid_pixels']==int(valid.sum()) and f.attrs['complete']==1
        assert f.attrs['code_sha256']==p.sha(p.__file__)
        samples.append(a[:,y,x].astype(float))
        scenes.append({'timestamp':stamp,'valid_pixels':int(valid.sum()),'sha256':p.sha(path)})
values=np.array(samples)*.01;mask=np.all(values!=0,axis=1)
values=np.where(mask[:,None,:],values,np.nan)
actual=np.nanmean(values,axis=0);n=mask.sum(0)
assert np.array_equal(count[y,x],n)
error=float(np.max(np.abs(actual-expected[:,y,x])))
assert error<2e-5
assert p.sha(p.HERE/'msg_lsct3.2-iter.py')=='763de469c6023b2b830061658d9130fcc851b7f7e9397903c27ac2fa159df9c3'
report={'status':'passed','month_hour':'201708_H12','instantaneous_scenes':len(stamps),
        'shape':[4,H,W],'first_timestamp':stamps[0],'last_timestamp':stamps[-1],
        'monthly_valid_pixels':int((count>0).sum()),'monthly_support_histogram':np.bincount(count.ravel(),minlength=32).tolist(),
        'random_monthly_pixels_checked':len(x),'maximum_monthly_difference_K':error,
        'monthly_sha256':p.sha(month),'all_scene_range_mask_order_checks':True,
        'original_regional_source_unchanged':True,'scenes':scenes}
p.atomic_json(root/'first_month_audit.json',report)
p.atomic_json(Path('C:/work/ls4t-msg/cases/official/results/production_assessment/msg_5x5')/'first_month_audit.json',report)
print(json.dumps({k:v for k,v in report.items() if k!='scenes'},indent=2))
