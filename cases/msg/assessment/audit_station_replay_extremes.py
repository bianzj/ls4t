"""Check largest historical residuals against original scalar entry functions."""
from pathlib import Path
import json
import numpy as np
import pandas as pd
from run_station_full_2018_2024 import functions,STATIC,BANDS

OUT=Path(__file__).resolve().parent.parent/'results/production_assessment/msg_5x5/station_direct_2018_2024'

def main():
    new=pd.read_csv(OUT/'station_predictions_all_models.csv.gz',dtype={'timestamp':str})
    new=new.loc[new.model.eq('historical_raw_h025')&new.valid]
    old=pd.read_csv('E:/PRODUCTS/LSCT_Site_Results_2018-2025_all.csv',dtype={'DateTime':str}).drop_duplicates()
    old=old.rename(columns={'Site':'site','DateTime':'timestamp','T_Soil':'background_soil','T_Vegetation':'canopy',
                           'T_Sunlit_Soil':'sunlit_soil','T_Shaded_Soil':'shaded_soil'})
    z=new.merge(old,on=['site','timestamp'],suffixes=('_new','_old'))
    difference=np.abs(np.round(z[[b+'_new' for b in BANDS]].to_numpy(dtype=float),2)-z[[b+'_old' for b in BANDS]].to_numpy(dtype=float))
    reasonable=z[[b+'_old' for b in BANDS]].ge(-23.15).all(axis=1)&z[[b+'_old' for b in BANDS]].le(76.85).all(axis=1)
    z['max_error_K']=np.nanmax(difference,axis=1)
    selected=pd.concat([z.nlargest(3,'max_error_K'),z.loc[reasonable&z.max_error_K.gt(.010001)]]).drop_duplicates(['site','timestamp'])
    selected.to_csv(OUT/'historical_replay_largest_differences.csv',index=False)
    ns=functions();rows=[]
    for r in selected.itertuples():
        folder=OUT/'partitions'/r.site/r.timestamp[:4]
        pred=pd.read_csv(folder/'predictions.csv.gz',dtype={'timestamp':str})
        pred=pred.loc[pred.model.eq('historical_raw_h025')].reset_index(drop=True)
        j=int(np.flatnonzero(pred.timestamp.eq(r.timestamp))[0])
        with np.load(folder/'input_cache.npz') as cache:
            d={k:cache[k][0 if len(cache[k])==1 else j] for k in ['sza','saa','lai']+STATIC}
            for sat in ['e','i']:
                raw=cache[f'lst_{sat}_raw'][j];d[f'lst_{sat}']=np.where(raw==0,np.nan,raw/100+273.15)
        weights=[]
        for sat in ['e','i']:
            vsa=np.abs(d['saa']-d['vaa_'+sat]);vsa=np.where(vsa>180,360-vsa,vsa)
            a,b=ns['hotspot_layer'](d['lai'],.25,d['vza_'+sat],d['sza'],vsa)
            weights.extend([d['emis_s']*a,d['emis_s']*(b-a),d['emis_v']*(1-b)])
        w=np.stack(weights,-1)
        re=ns['planck'](10.5,d['lst_e'])*w[...,:3].sum(-1);ri=ns['planck'](10.5,d['lst_i'])*w[...,3:].sum(-1)
        sun,_=ns['solve_2x2_system_center'](re,ri,w[...,0],w[...,1]+w[...,2],w[...,3],w[...,4]+w[...,5])
        shade,veg=ns['solve_constrained_vectorized2_center'](re-w[...,0]*sun,ri-w[...,3]*sun,w[...,1],w[...,2],w[...,4],w[...,5],sun,dif=3)
        a,b,c=ns['solve_joint_center'](re,ri,w,np.array([sun,min(shade,sun),veg]),lmbda=1000)
        gap=ns['gap_probability_hom_analytical'](d['lai'][2,2],d['sza'][2,2])
        scalar=ns['inv_planck'](10.5,np.array([a*gap+b*(1-gap),c,a,b]))-273.15
        batch=np.array([getattr(r,k+'_new') for k in BANDS]);archive=np.array([getattr(r,k+'_old') for k in BANDS])
        error=float(np.max(np.abs(scalar-batch)));assert error<1e-7
        rows.append({'site':r.site,'timestamp':r.timestamp,'batch_scalar_max_K':error,
            'scalar_archive_max_K':float(np.max(np.abs(np.round(scalar,2)-archive))),
            'scalar_C':scalar.tolist(),'archive_C':archive.tolist()})
    (OUT/'historical_extreme_scalar_audit.json').write_text(json.dumps(rows,indent=2),encoding='utf8')
    print('STRESS_SCALAR_CHECKS',len(rows),'MAX_K',max(r['batch_scalar_max_K'] for r in rows))

if __name__=='__main__':main()
