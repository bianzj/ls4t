"""Independent historical scalar solver comparison and tile-boundary checks."""
from pathlib import Path
import json, sys
import numpy as np
import produce_msg_5x5 as p


def main():
    sys.path.insert(0,str(p.REPO))
    source=p.HERE/'msg_lsct3.2-iter-site-cons-ig-center.py'
    ns={};exec(compile(source.read_text(encoding='utf8').split('# ================= 主程序')[0],str(source),'exec'),ns)
    cached=np.load('C:/work/ls4t-msg/cases/official/results/production_assessment/parameter_search/input_cache.npz')
    errors=[];cases=0;invalid=0;fixture=None
    for i in range(0,len(cached['lai']),7):
        d={k:v[0 if len(v)==1 else i].astype('float64').copy() for k,v in cached.items()}
        if not np.all((d['sza']>=0)&(d['sza']<90)): continue
        for missing in [False,True]:
            z={k:v.copy() for k,v in d.items()}
            if missing:z['lst_e'][0,0]=np.nan
            we,be=ns['hotspot_layer'](z['lai'],.05,z['vza_e'],z['sza'],np.abs(z['saa']-z['vaa_e']))
            wi,bi=ns['hotspot_layer'](z['lai'],.05,z['vza_i'],z['sza'],np.abs(z['saa']-z['vaa_i']))
            w=np.stack([z['emis_s']*we,z['emis_s']*(be-we),z['emis_v']*(1-be),
                        z['emis_s']*wi,z['emis_s']*(bi-wi),z['emis_v']*(1-bi)],-1)
            re=p.planck(z['lst_e'])*w[...,:3].sum(-1);ri=p.planck(z['lst_i'])*w[...,3:].sum(-1)
            sun,_=ns['solve_2x2_system_center'](re,ri,w[...,0],w[...,1]+w[...,2],w[...,3],w[...,4]+w[...,5])
            shade,veg=ns['solve_constrained_vectorized2_center'](re-w[...,0]*sun,ri-w[...,3]*sun,w[...,1],w[...,2],w[...,4],w[...,5],sun,dif=3)
            shade=min(shade,sun)
            a,b,c=ns['solve_joint_center'](re,ri,w,np.array([sun,shade,veg]),lmbda=1000)
            gap=np.exp(-.5*z['lai'][2,2]/np.cos(np.radians(z['sza'][2,2])))
            ref=p.inverse(np.array([a*gap+b*(1-gap),c,a,b]))
            valid=np.isfinite(ref).all() and np.all((ref>=250)&(ref<=350)) and z['lai'][2,2]>=.05
            actual=p.retrieve(z)[0][:,2,2]
            assert np.isfinite(actual).all()==valid,(i,missing,actual,ref)
            if valid:errors.append(float(np.max(np.abs(actual-ref))));fixture=z
            else:invalid+=1
            cases+=1
    assert cases>100 and max(errors)<1e-7
    full={k:np.tile(v,(7,4)) for k,v in fixture.items()}
    all_result=p.retrieve(full)
    tile_results=[[],[],[]];H=full['lai'].shape[0]
    for y in range(0,H,8):
        lo=max(0,y-2);hi=min(H,y+8+2);end=min(H,y+8)
        result=p.retrieve({k:v[lo:hi] for k,v in full.items()})
        for j,a in enumerate(result): tile_results[j].append(a[:,y-lo:end-lo] if j==0 else a[y-lo:end-lo])
    tiled=[np.concatenate(v,axis=1 if j==0 else 0) for j,v in enumerate(tile_results)]
    np.testing.assert_allclose(tiled[0],all_result[0],rtol=0,atol=1e-7,equal_nan=True)
    assert np.array_equal(tiled[1],all_result[1]) and np.array_equal(tiled[2],all_result[2])
    night={k:v.copy() for k,v in fixture.items()};night['sza'][:]=95
    assert not np.isfinite(p.retrieve(night)[0]).any()
    center={k:v.copy() for k,v in fixture.items()};center['lst_e'][2,2]=np.nan
    assert not np.isfinite(p.retrieve(center)[0][:,2,2]).any()
    ts=np.array([250.,273.15,300.,350.]);np.testing.assert_allclose(p.inverse(p.planck(ts)),ts,rtol=0,atol=1e-10)
    report={'status':'passed','producer_sha256':p.sha(p.__file__),'historical_scalar_sha256':p.sha(source),
            'scalar_cases':cases,'invalid_cases':invalid,'maximum_temperature_difference_K':max(errors),
            'tile_halo_invariance':True,'missing_neighbor_and_center_checked':True,'night_checked':True,
            'B300_W_m2_sr_um':float(p.planck(300.)),'limitation':'Numerical method verification, not independent ground accuracy.'}
    out=Path('C:/work/ls4t-msg/cases/official/results/production_assessment/msg_5x5')
    p.atomic_json(out/'verification.json',report)
    print(json.dumps(report,indent=2))


if __name__=='__main__':main()
