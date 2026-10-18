"""Identify historical settings by replay, independently of ground accuracy."""
from pathlib import Path
import argparse,json,sys
import numpy as np
import pandas as pd
from search_evo_parameters import prepare,retrieve
from run_station_full_2018_2024 import functions,STATIC,BANDS

HERE=Path(__file__).resolve().parent
DEFAULT=HERE.parent/'results/production_assessment/msg_5x5/station_direct_2018_2024'

def main():
    parser=argparse.ArgumentParser();parser.add_argument('--root',type=Path,default=DEFAULT)
    parser.add_argument('--output-root',type=Path,default=DEFAULT);args=parser.parse_args()
    root=args.root
    out=args.output_root;out.mkdir(parents=True,exist_ok=True)
    archive=pd.read_csv('E:/PRODUCTS/LSCT_Site_Results_2018-2025_all.csv',dtype={'DateTime':str})
    archive=archive.rename(columns={'Site':'site','DateTime':'timestamp','T_Soil':'background_soil','T_Vegetation':'canopy',
                                    'T_Sunlit_Soil':'sunlit_soil','T_Shaded_Soil':'shaded_soil'})
    archive=archive.drop_duplicates()
    assert not archive.duplicated(['site','timestamp']).any(),'Conflicting historical predictions must be resolved before parameter inference'
    ns=functions();rows=[];sample_rows=[]
    configs=[('hotspot',h,1000,3) for h in [.05,.1,.15,.2,.25,.3,.4,.5]]
    configs += [('lambda',.25,l,3) for l in [1,10,100,1000]]
    configs += [('delta',.25,1000,d) for d in [.5,1,3,10]]
    for sitepath in sorted((root/'partitions').iterdir()):
        pieces=[];obs=[]
        for done in sorted(sitepath.glob('*/complete.json')):
            c=json.loads(done.read_text());pred=pd.read_csv(done.parent/'predictions.csv.gz',dtype={'timestamp':str})
            pred=pred.loc[pred.model.eq('historical_raw_h025')].reset_index(drop=True);pred['cache_index']=np.arange(len(pred))
            z=pred[['site','timestamp','cache_index']].merge(archive,on=['site','timestamp'])
            z=z.loc[z[BANDS].ge(-23.15).all(axis=1)&z[BANDS].le(76.85).all(axis=1)]
            if not len(z):continue
            z=z.iloc[np.linspace(0,len(z)-1,min(16,len(z)),dtype=int)].copy();idx=z.cache_index.to_numpy()
            with np.load(done.parent/'input_cache.npz') as cache:
                data={k:cache[k][idx] if len(cache[k])!=1 else np.repeat(cache[k],len(idx),axis=0) for k in ['sza','saa','lai']+STATIC}
                for sat in ['e','i']:
                    raw=cache[f'lst_{sat}_raw'][idx];data[f'lst_{sat}']=np.where(raw==0,np.nan,raw/100.+273.15)
            pieces.append(data);obs.append(z)
        if not obs:continue
        data={k:np.concatenate([d[k] for d in pieces]) for k in pieces[0]};panel=pd.concat(obs,ignore_index=True)
        sample_rows.append(panel[['site','timestamp','cache_index']]);ref=panel[BANDS].to_numpy();pres={}
        baseline=None
        for kind,h,l,d in configs:
            if h not in pres:
                with np.errstate(all='ignore'):pres[h]=prepare(data,h,'legacy',5,'center',ns['hotspot_layer'])
            with np.errstate(all='ignore'):temp,_,active=retrieve(pres[h],data,l,d,'legacy',return_raw=True)
            temp=np.round(temp-273.15,2);good=np.isfinite(temp).all(axis=1);diff=np.abs(temp-ref)
            if h==.25 and l==1000 and d==3:baseline=temp.copy()
            rows.append({'site':sitepath.name,'factor':kind,'hotspot':h,'lambda':l,'delta_legacy':d,
                'sample_n':len(ref),'finite_predictions':int(good.sum()),'all_four_exact':int((diff<1e-7).all(axis=1).sum()),
                'all_four_within_001':int((diff<=.010001).all(axis=1).sum()),'max_diff_K':float(np.nanmax(diff)),
                'mean_four_band_abs_difference_K':float(np.nanmean(diff)),'constraint_active':int(active.sum()),
                'max_change_from_h025_l1000_d3_K':float(np.nanmax(np.abs(temp-baseline))) if baseline is not None else np.nan})
    result=pd.DataFrame(rows);result.to_csv(out/'original_parameter_sensitivity_replay.csv',index=False)
    pd.concat(sample_rows,ignore_index=True).to_csv(out/'original_parameter_replay_sample.csv',index=False)
    print(result.groupby(['factor','hotspot','lambda','delta_legacy'],as_index=False).agg(
        sample_n=('sample_n','sum'),exact=('all_four_exact','sum'),within001=('all_four_within_001','sum'),
        max_difference_K=('max_diff_K','max')).to_string(index=False),flush=True)

if __name__=='__main__':main()
