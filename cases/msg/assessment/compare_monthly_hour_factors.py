"""One-factor physical sensitivity, monthly-hour only; no parameter reselection."""
from pathlib import Path
import json
import numpy as np
import pandas as pd
import select_joint_station_parameters as joint
from search_evo_parameters import solve, planck, prepare, retrieve

ROOT = joint.OUT
OUT = ROOT / 'monthly_hour_factor_sensitivity'

def window_prepare(data, h, w1size, w2size, hotspot):
    angles = []
    for sat in ['e', 'i']:
        a = np.abs(data['saa'] - data['vaa_' + sat])
        angles.append(np.where(a > 180, 360 - a, a))
    w1, b1 = hotspot(data['lai'], h, data['vza_e'], data['sza'], angles[0])
    w2, b2 = hotspot(data['lai'], h, data['vza_i'], data['sza'], angles[1])
    w = np.stack([data['emis_s']*w1, data['emis_s']*(b1-w1), data['emis_v']*(1-b1),
                  data['emis_s']*w2, data['emis_s']*(b2-w2), data['emis_v']*(1-b2)], axis=-1)
    re = planck(data['lst_e'])*w[..., :3].sum(axis=-1)
    ri = planck(data['lst_i'])*w[..., 3:].sum(axis=-1)
    first, _ = solve(re, ri, w[...,0], w[...,1]+w[...,2], w[...,3], w[...,4]+w[...,5], size=w1size)
    rre = re - w[...,0]*first[:,None,None]
    rri = ri - w[...,3]*first[:,None,None]
    shade, veg = solve(rre, rri, w[...,1], w[...,2], w[...,4], w[...,5], size=w2size)
    return w[:,2,2], re[:,2,2], ri[:,2,2], rre[:,2,2], rri[:,2,2], first, shade, veg

def main():
    OUT.mkdir(exist_ok=True)
    joint.OUT = OUT  # Isolate panel/manifest writes from the frozen selection.
    data, panel = joint.load_panel()
    ns = joint.functions()
    base = dict(hotspot=.25, **{'lambda':1000.}, delta=3., first_window=5, second_window=5)
    configs = {'baseline': base}
    families = {}
    for factor, values in [('hotspot',[.05,.1,.15,.2,.3,.4,.5]), ('lambda',[.01,.1,1.,10.,100.]), ('delta',[.5,1.,2.,5.])]:
        families[factor] = ['baseline']
        for v in values:
            name = f'{factor}_{v:g}'
            configs[name] = {**base, factor:v}; families[factor].append(name)
    families['window'] = ['baseline']
    for w1, w2 in [(3,5),(5,3),(3,3)]:
        name = f'window_{w1}x{w2}'
        configs[name] = {**base, 'first_window':w1, 'second_window':w2}
        families['window'].append(name)
    # A single common panel also permits comparison across parameter families.
    families['all_factors'] = list(configs)
    protocol = dict(scope='Post-selection sensitivity only, all periods previously inspected; no reranking',
        configs=configs, families=families, monthly_hour_min_pairs=3,
        window_limit='Central 3x3 versus 5x5 using existing 5x5 cache; baseline physical input eligibility retained',
        support='Own support with and without instantaneous 10 K filtering; family-common valid support; family-common 10 K support',
        source_sha256={str(Path(__file__)):joint.sha(Path(__file__)), str(Path(joint.__file__)):joint.sha(Path(joint.__file__))})
    (OUT/'protocol.json').write_text(json.dumps(protocol,indent=2),encoding='utf8')
    predictions={}; pre_cache={}; window_check=0.
    with np.errstate(all='ignore'):
        for name,c in configs.items():
            key=(c['hotspot'],c['first_window'],c['second_window'])
            if key not in pre_cache:
                pre_cache[key]=window_prepare(data,*key,ns['hotspot_layer'])
            pre=pre_cache[key]
            if name=='baseline':
                original=prepare(data,.25,'physical',5,'center',ns['hotspot_layer'])
                for a,b in zip(original,pre):
                    assert np.allclose(a,b,equal_nan=True,rtol=0,atol=1e-10)
                    window_check=max(window_check,float(np.nanmax(np.abs(a-b))))
            temp,valid,_=retrieve(pre,data,c['lambda'],c['delta'],return_raw=True)
            temp=temp-273.15;temp[~valid|~panel.input_eligible.to_numpy()]=np.nan
            predictions[name]=joint.projected(temp,panel)
            print('DONE',name,flush=True)
    rows=[]; monthly_rows=[]; changes=[]
    def evaluate(name,component,mask,support,family):
        z=panel.loc[mask,['domain','site','time','split','month','hour']].copy()
        z['prediction']=predictions[name][component][mask]
        z['reference']=panel.loc[mask,component+'_reference'].to_numpy()
        z['baseline']=predictions['baseline'][component][mask]
        for split in ['all','development','validation']:
            a=z if split=='all' else z.loc[z.split.eq(split)]
            g=a.groupby(['domain','site','month','hour'],as_index=False).agg(
                prediction=('prediction','mean'),reference=('reference','mean'),baseline=('baseline','mean'),n_raw=('prediction','size'))
            g=g.loc[g.n_raw.ge(3)].copy()
            if name=='baseline' and family=='own' and split=='all':
                g['component']=component;g['support']=support;monthly_rows.append(g)
            for (domain,site), b in g.groupby(['domain','site']):
                if len(b)<3:continue
                error=b.prediction-b.reference
                rows.append(dict(model=name,family=family,support=support,component=component,split=split,domain=domain,site=site,
                    rmse_K=float(np.sqrt(np.mean(error**2))),bias_K=float(error.mean()),n_groups=len(b),n_raw=int(b.n_raw.sum())))
                if family!='own':
                    changes.append(dict(model=name,family=family,support=support,component=component,split=split,domain=domain,site=site,
                        monthly_temperature_change_rms_K=float(np.sqrt(np.mean((b.prediction-b.baseline)**2))),n_groups=len(b)))
    for component in ['soil','canopy']:
        eligible=panel['eligible_'+component].to_numpy()
        ref=panel[component+'_reference'].to_numpy()
        for name,values in predictions.items():
            mask=eligible & np.isfinite(values[component])
            evaluate(name,component,mask,'unfiltered','own')
            # EVO direct observations are not filtered by model-reference error.
            filtered=mask & (panel.domain.eq('direct').to_numpy() | (np.abs(values[component]-ref)<=10))
            evaluate(name,component,filtered,'europe_instant_10K','own')
        for family,names in families.items():
            common=eligible & np.logical_and.reduce([np.isfinite(predictions[n][component]) for n in names])
            common10=common & (panel.domain.eq('direct').to_numpy() | np.logical_and.reduce([np.abs(predictions[n][component]-ref)<=10 for n in names]))
            for name in names:
                evaluate(name,component,common,'common_unfiltered',family)
                evaluate(name,component,common10,'common_europe_10K',family)
    met=pd.DataFrame(rows);met.to_csv(OUT/'station_monthly_hour_metrics.csv',index=False)
    keys=['model','family','support','component','split','domain']
    summary=met.groupby(keys,as_index=False).agg(sites=('site','size'),mean_site_rmse_K=('rmse_K','mean'),
        mean_site_bias_K=('bias_K','mean'),n_groups=('n_groups','sum'),n_raw=('n_raw','sum'))
    summary.to_csv(OUT/'monthly_hour_summary.csv',index=False)
    delta=pd.DataFrame(changes).groupby(keys,as_index=False).agg(sites=('site','size'),
        mean_site_temperature_change_rms_K=('monthly_temperature_change_rms_K','mean'),n_groups=('n_groups','sum'))
    delta.to_csv(OUT/'monthly_temperature_changes.csv',index=False)
    pd.concat(monthly_rows,ignore_index=True).to_csv(OUT/'selected_monthly_hour_pairs.csv',index=False)
    # Reproduce the previously reported European baseline with and without filtering.
    old=pd.read_csv(ROOT/'threshold_sensitivity/summary.csv')
    check=[]
    for support,mode in [('unfiltered','unfiltered'),('europe_instant_10K','instant_component_10K')]:
        a=summary.loc[summary.model.eq('baseline') & summary.family.eq('own') & summary.support.eq(support) & summary.split.eq('all') & summary.domain.eq('indirect')]
        b=old.loc[old['mode'].eq(mode) & old.split.eq('all') & old.scale.eq('monthly_hour')]
        z=a.merge(b,on='component',suffixes=('_new','_old'));assert len(z)==2
        check.extend(np.abs(z.mean_site_rmse_K_new-z.mean_site_rmse_K_old))
    assert max(check)<1e-9
    (OUT/'audit.json').write_text(json.dumps(dict(status='passed',original_5x5_prepare_max_difference=window_check,
        baseline_monthly_rmse_max_difference_K=max(check),configs=len(configs),regional_production_restarted=False),indent=2),encoding='utf8')
    print('OWN EUROPE ALL PERIODS')
    print(summary.loc[summary.family.eq('own') & summary.support.eq('europe_instant_10K') & summary.split.eq('all') & summary.domain.eq('indirect')].to_string(index=False))

if __name__=='__main__':main()
