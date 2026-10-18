from pathlib import Path
import pandas as pd
import numpy as np
import json, hashlib
ROOT=Path(r'C:\work\ls4t-msg\cases\official\results\production_assessment\manuscript_validation_update')
OUT=ROOT/'validation_analysis'; OUT.mkdir(exist_ok=True)
def rmse(a,b):return float(np.sqrt(np.mean((a-b)**2)))
eu=pd.read_csv(ROOT/'europe_monthly_hour_pairs.csv.gz')
eu=eu[(eu.domain=='Europe14')&(eu.rule=='joint_10K')].copy()
sites=[]
for s,g in eu.groupby('site'):
 a=g[g.component=='soil']; b=g[g.component=='canopy']
 sites.append(dict(site=s,retained=s not in ['IT-TrF','FR-EM2'],years=','.join(map(str,sorted(a.year.unique()))),months=int(a.month.nunique()),groups=len(a),raw=int(a.n_raw.sum()),soil=rmse(a.prediction,a.reference),canopy=rmse(b.prediction,b.reference)))
pd.DataFrame(sites).to_csv(OUT/'all14_station_support.csv',index=False)
e12=eu[~eu.site.isin(['IT-TrF','FR-EM2'])]
rows=[]
for label,g in [('2018-2024',e12),('2018-2022',e12[e12.year<=2022]),('2023-2024',e12[e12.year>=2023])]:
 for c,d in g.groupby('component'):
  eligible=d.groupby('site').size();d=d[d.site.isin(eligible[eligible>=3].index)]
  station=[rmse(x.prediction,x.reference) for _,x in d.groupby('site')]
  rows.append(dict(domain='Europe12',period=label,component=c,sites=len(station),groups=len(d),raw=int(d.n_raw.sum()),rmse_equal=float(np.mean(station)),rmse_pooled=rmse(d.prediction,d.reference)))
ev=pd.read_csv(ROOT/'evo_monthly_hour_pairs.csv')
for label,g in [('2017-08:12',ev),('2017-08:10',ev[ev.month<=201710]),('2017-11:12',ev[ev.month>=201711])]:
 for c,d in g.groupby('component'):
  rows.append(dict(domain='EVO',period=label,component=c,sites=1,groups=len(d),raw=int(d.n_raw.sum()),rmse_equal=rmse(d.prediction,d.reference),rmse_pooled=rmse(d.prediction,d.reference)))
pd.DataFrame(rows).to_csv(OUT/'temporal_assessment.csv',index=False)
loo=[]
st=pd.DataFrame(sites); st=st[st.retained]
for s in st.site:
 d=st[st.site!=s];loo.append(dict(omitted=s,soil=d.soil.mean(),canopy=d.canopy.mean()))
pd.DataFrame(loo).to_csv(OUT/'leave_one_site_out.csv',index=False)
src=ROOT.parent/'joint_parameter_selection/threshold_sensitivity/europe_10_16_joint/subset_12_sites/hotspot_window_experiment/monthly_pairs.csv.gz'
p=pd.read_csv(src);p=p[(p.hour>=11)&(p.hour<=16)&(p.period=='all')]
pr=[]
for (model,support),a in p.groupby(['model','support']):
 for label,b in [('2018-2024',a),('2018-2022',a[a.year<=2022]),('2023-2024',a[a.year>=2023])]:
  ns=b.groupby('site').size();b=b[b.site.isin(ns[ns>=3].index)]
  for c in ['soil','canopy']:
   vals=[rmse(x[c+'_prediction'],x[c+'_reference']) for _,x in b.groupby('site')]
   bases=[rmse(x[c+'_baseline'],x[c+'_reference']) for _,x in b.groupby('site')]
   pr.append(dict(model=model,support=support,period=label,component=c,sites=len(vals),groups=len(b),raw=int(b.n_raw.sum()),rmse=float(np.mean(vals)),baseline_rmse=float(np.mean(bases))))
pr=pd.DataFrame(pr);pr.to_csv(OUT/'hotspot_window_11_16.csv',index=False)
base=pr[(pr.model=='h0.25_w5_5')&(pr.support=='own_joint')&(pr.period=='2018-2024')]
assert np.isclose(base[base.component=='soil'].rmse.iloc[0],4.0140531231)
assert np.isclose(base[base.component=='canopy'].rmse.iloc[0],3.6260164572)
audit={'new_inversions':0,'regional_production_started':False,'hours':'11-16 UTC','aggregation':'instantaneous screening already applied; existing monthly-hour pairs retained','periods':'retrospective, previously examined','source_sha256':{str(f):hashlib.sha256(f.read_bytes()).hexdigest() for f in [src,ROOT/'europe_monthly_hour_pairs.csv.gz',ROOT/'evo_monthly_hour_pairs.csv']},'loo_ranges':{c:[min(x[c] for x in loo),max(x[c] for x in loo)] for c in ['soil','canopy']}}
(OUT/'analysis_audit.json').write_text(json.dumps(audit,indent=2),encoding='utf-8')
print(pd.DataFrame(rows).to_string(index=False));print(st.to_string(index=False));print(audit['loo_ranges'])
print(pr[(pr.support=='own_joint')&(pr.period=='2018-2024')].pivot(index='model',columns='component',values='rmse').to_string())
