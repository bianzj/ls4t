"""Build manuscript validation evidence and figures from saved station predictions."""
from pathlib import Path
import hashlib,json
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

ROOT=Path('C:/work/ls4t-msg/cases/official/results/production_assessment')
J=ROOT/'joint_parameter_selection'
OUT=ROOT/'manuscript_validation_update'
FIG=OUT/'figures'
EXCLUDED={'IT-TrF','FR-EM2'}
COLORS={'sunlit':'#C66B20','background':'#7965AC','canopy':'#287B65','reference':'#286DA8','bulk':'#8A9199'}

def agg(a):
    g=a.groupby(['site','year','month','hour'],as_index=False).agg(
        prediction=('prediction','mean'),reference=('reference','mean'),bulk=('bulk','mean'),n_raw=('time','size'))
    return g.loc[g.n_raw>=3].copy()

def metrics(g):
    e=g.prediction-g.reference
    return dict(rmse=float(np.sqrt(np.mean(e**2))),bias=float(e.mean()),n=len(g),n_raw=int(g.n_raw.sum()),
        bulk_rmse=float(np.sqrt(np.mean((g.bulk-g.reference)**2))))

def savefig(fig,name):
    fig.savefig(FIG/(name+'.png'),dpi=320,facecolor='white')
    fig.savefig(FIG/(name+'.pdf'),facecolor='white')
    plt.close(fig)

def main():
    FIG.mkdir(parents=True,exist_ok=True)
    plt.rcParams.update({'font.family':'DejaVu Sans','font.size':9,'axes.labelsize':9,'axes.titlesize':10,
        'axes.spines.top':False,'axes.spines.right':False,'axes.linewidth':.7,'xtick.labelsize':8,'ytick.labelsize':8,
        'legend.fontsize':8,'pdf.fonttype':42,'savefig.bbox':None})
    sources=[J/'threshold_sensitivity/evo_range_0_60_joint/instantaneous_pairs.csv.gz',
        J/'selected_station_predictions.csv.gz',J/'frozen_reference_panel.csv.gz',
        J/'threshold_sensitivity/evo_range_0_60_joint/hours_11_16/summary.csv',
        J/'threshold_sensitivity/europe_10_16_joint/subset_12_sites/station_metrics.csv']
    hashes={str(p):hashlib.sha256(p.read_bytes()).hexdigest() for p in sources}
    evo=pd.read_csv(sources[0]);evo=evo.loc[evo.hour.between(11,16)]
    emonth={};eraw={};facts={};sens=[]
    for kind,soil,component in [('sunlit','sunlit_soil','soil'),('background','background_soil','soil'),('canopy','sunlit_soil','canopy')]:
        a=evo.loc[evo.soil_type.eq(soil)&evo.rule.eq('joint_0_60_10K')].copy()
        a['prediction']=a[component+'_prediction'];a['reference']=a[component+'_reference']
        eraw[kind]=a;emonth[kind]=agg(a);facts['evo_'+kind]=metrics(emonth[kind])
        u=evo.loc[evo.soil_type.eq(soil)&evo.rule.eq('existing_unfiltered')].copy()
        cols=['soil_prediction','canopy_prediction','soil_reference','canopy_reference','bulk']
        u=u.loc[u[cols].ge(0).all(axis=1)&u[cols].le(60).all(axis=1)]
        u['prediction']=u[component+'_prediction'];u['reference']=u[component+'_reference']
        sens.append(dict(domain='EVO',component=kind,rule='range_only',**metrics(agg(u))))
        sens.append(dict(domain='EVO',component=kind,rule='joint_10K',**facts['evo_'+kind]))
    pred=pd.read_csv(sources[1]);panel=pd.read_csv(sources[2])
    x=pred.loc[pred.domain.eq('indirect')&pred.valid&pred.hour.between(11,16)].merge(
        panel[['site','time','soil_reference','canopy_reference','bulk','eligible_soil','eligible_canopy']],on=['site','time'],validate='one_to_one')
    cols=['shaded_soil','canopy','soil_reference','canopy_reference','bulk']
    range_mask=x.eligible_soil&x.eligible_canopy&x[cols].ge(0).all(axis=1)&x[cols].le(60).all(axis=1)
    err=(x.shaded_soil-x.soil_reference).abs().le(10)&(x.canopy-x.canopy_reference).abs().le(10)
    eumonth={};site_records=[];allmonthly=[]
    for nsites in [12,14]:
        for rule,mask in [('range_only',range_mask),('joint_10K',range_mask&err)]:
            a=x.loc[mask & (~x.site.isin(EXCLUDED) if nsites==12 else True)].copy()
            for comp,col,ref in [('soil','shaded_soil','soil_reference'),('canopy','canopy','canopy_reference')]:
                z=a.assign(prediction=a[col],reference=a[ref]);g=agg(z)
                sizes=g.groupby('site').size();g=g.loc[g.site.isin(sizes[sizes>=3].index)]
                station=[]
                for site,b in g.groupby('site'):
                    m=metrics(b);station.append(dict(site=site,**m));site_records.append(dict(nsites=nsites,rule=rule,component=comp,site=site,**m))
                stat=pd.DataFrame(station);assert len(stat)==nsites
                total=dict(rmse=float(stat.rmse.mean()),bias=float(stat.bias.mean()),bulk_rmse=float(stat.bulk_rmse.mean()),n=int(stat.n.sum()),n_raw=int(stat.n_raw.sum()),sites=nsites)
                facts[f'europe{nsites}_{rule}_{comp}']=total
                if nsites==12 and rule=='joint_10K':eumonth[comp]=g
                sens.append(dict(domain=f'Europe{nsites}',component=comp,rule=rule,**total))
                g['domain']=f'Europe{nsites}';g['rule']=rule;g['component']=comp;allmonthly.append(g)
    expected=pd.read_csv(sources[3]);expected=expected.loc[expected.start_hour.eq(11)&expected.rule.eq('joint_0_60_10K')&expected.scale.eq('monthly_hour')]
    for kind,soil,comp in [('sunlit','sunlit_soil','soil'),('background','background_soil','soil'),('canopy','sunlit_soil','canopy')]:
        r=expected.loc[expected.soil_type.eq(soil)&expected.component.eq(comp)].iloc[0]
        assert abs(facts['evo_'+kind]['rmse']-r.rmse_K)<1e-10
        assert facts['evo_'+kind]['n_raw']==r.n_raw
    old=pd.read_csv(sources[4]);old=old.loc[old.start_hour.eq(11)&old.soil_type.eq('shaded_soil')&old.scale.eq('monthly_hour')]
    site_metrics=pd.DataFrame(site_records)
    z=site_metrics.loc[site_metrics.nsites.eq(12)&site_metrics.rule.eq('joint_10K')].merge(old,on=['site','component'],validate='one_to_one')
    assert len(z)==24 and (z.rmse-z.rmse_K).abs().max()<1e-10 and z.n.eq(z.n_groups).all()
    site_metrics.to_csv(OUT/'station_metrics.csv',index=False);pd.concat(allmonthly,ignore_index=True).to_csv(OUT/'europe_monthly_hour_pairs.csv.gz',index=False)
    pd.DataFrame(sens).to_csv(OUT/'filter_sensitivity.csv',index=False)
    rows=[]
    for kind,g in emonth.items():
        c=g.copy();c['component']=kind;rows.append(c)
    pd.concat(rows,ignore_index=True).to_csv(OUT/'evo_monthly_hour_pairs.csv',index=False)
    # Figure 5: August means by hour, including the background cross-component diagnostic.
    fig,axs=plt.subplots(1,3,figsize=(9.6,3.5),layout='constrained')
    for ax,kind,label in zip(axs,['sunlit','background','canopy'],['Sunlit soil','Background soil','Canopy']):
        a=eraw[kind].loc[eraw[kind].month.eq(201708)]
        g=a.groupby('hour').agg(pred=('prediction','mean'),ref=('reference','mean'),bulk=('bulk','mean'),ps=('prediction','std'),rs=('reference','std'),bs=('bulk','std'),n=('time','size'))
        g=g.loc[g.n>=3]
        ax.errorbar(g.index,g.ref,yerr=g.rs,fmt='o-',color=COLORS['reference'],capsize=2,label='Radiometry')
        ax.errorbar(g.index,g.pred,yerr=g.ps,fmt='s-',color=COLORS[kind],capsize=2,label='Retrieval')
        ax.plot(g.index,g.bulk,'^--',color=COLORS['bulk'],label='Bulk LST')
        ax.set(title=label,xlabel='UTC hour',xticks=range(11,17),ylabel='Temperature (°C)')
        for h,r in g.iterrows():ax.text(h,.97,str(int(r.n)),transform=ax.get_xaxis_transform(),ha='center',va='top',fontsize=7)
        ax.grid(alpha=.17);ax.set_ylim(0,65)
        if kind=='sunlit':ax.legend(loc='lower left',frameon=False)
        facts['august_'+kind]=g.round(6).reset_index().to_dict('records')
    savefig(fig,'figure05_evo_diurnal')
    # Figure 6: the soil reference remains sunlit soil in both soil panels.
    fig,axs=plt.subplots(1,3,figsize=(9.6,3.7),layout='constrained')
    for i,(ax,kind,title) in enumerate(zip(axs,['sunlit','background','canopy'],['(a) Sunlit soil','(b) Background soil','(c) Canopy'])):
        g=emonth[kind];m=facts['evo_'+kind]
        ax.scatter(g.reference,g.bulk,s=19,marker='^',color=COLORS['bulk'],alpha=.6,label='Bulk LST',zorder=2)
        ax.scatter(g.reference,g.prediction,s=29,color=COLORS[kind],edgecolors='white',linewidths=.4,label='Retrieval',zorder=3)
        ax.plot([0,60],[0,60],ls='--',lw=1,color='#555555');ax.set(xlim=(0,60),ylim=(0,60),aspect='equal',title=title,
            xlabel='Sunlit-soil radiometry (°C)' if i<2 else 'Canopy radiometry (°C)',ylabel='Estimated temperature (°C)')
        ax.text(.04,.96,f"RMSE = {m['rmse']:.3f} K\nBias = {m['bias']:+.3f} K\nN = {m['n']}",transform=ax.transAxes,va='top',fontsize=8)
        ax.grid(alpha=.17)
        if i==1:ax.text(.97,.05,'Cross-component\ncomparison',transform=ax.transAxes,ha='right',color=COLORS[kind],fontsize=8)
        if i==2:ax.legend(loc='lower right',frameon=False)
    savefig(fig,'figure06_evo_scatter')
    fig,axs=plt.subplots(1,3,figsize=(9.6,3.1),layout='constrained')
    for ax,kind,title in zip(axs,['sunlit','background','canopy'],['Sunlit soil','Background soil','Canopy']):
        g=emonth[kind];r=g.groupby('hour').apply(lambda a:pd.Series({'rmse':np.sqrt(np.mean((a.prediction-a.reference)**2)),'bulk_rmse':np.sqrt(np.mean((a.bulk-a.reference)**2)),'n':len(a)}),include_groups=False)
        ax.plot(r.index,r.rmse,'o-',color=COLORS[kind],label='Retrieval');ax.plot(r.index,r.bulk_rmse,'^--',color=COLORS['bulk'],label='Bulk LST')
        ax.set(title=title,xlabel='UTC hour',ylabel='RMSE (K)',xticks=range(11,17),ylim=(0,None));ax.grid(alpha=.17)
        if kind=='canopy':ax.legend(frameon=False)
        facts['hourly_'+kind]=r.round(6).reset_index().to_dict('records')
    savefig(fig,'figure07_evo_hourly')
    fig,axs=plt.subplots(2,1,figsize=(9.2,5.5),sharex=True,layout='constrained')
    sites=sorted(eumonth['soil'].site.unique());idx=np.arange(len(sites))
    for ax,comp,title,color in zip(axs,['soil','canopy'],['(a) Shaded soil versus soil probe','(b) Canopy versus air temperature'],[COLORS['background'],COLORS['canopy']]):
        a=site_metrics.loc[site_metrics.nsites.eq(12)&site_metrics.rule.eq('joint_10K')&site_metrics.component.eq(comp)].set_index('site').loc[sites]
        ax.bar(idx-.19,a.bulk_rmse,.36,color=COLORS['bulk'],label='Bulk LST');ax.bar(idx+.19,a.rmse,.36,color=color,label='Component')
        top=max(a.bulk_rmse.max(),a.rmse.max())+1.5;ax.set_ylim(0,top)
        ax.set(ylabel='RMSE (K)',title=title);ax.grid(axis='y',alpha=.17);ax.set_axisbelow(True)
        ax.legend(loc='upper right',ncol=2,frameon=False)
    axs[-1].set_xticks(idx,sites,rotation=35,ha='right');savefig(fig,'figure08_europe12')
    fig,axs=plt.subplots(1,2,figsize=(9.6,3.4),layout='constrained')
    for ax,domain,comps,labels in [(axs[0],'EVO',['sunlit','background','canopy'],['Sunlit soil','Background\nsoil','Canopy']),
                                  (axs[1],'Europe12',['soil','canopy'],['Shaded soil','Canopy'])]:
        ss=pd.DataFrame(sens);pos=np.arange(len(comps))
        for off,rule,color,label in [(-.19,'range_only','#A3ADB8','0–60°C only'),(.19,'joint_10K','#326785','+ Joint 10 K')]:
            a=ss.loc[ss.domain.eq(domain)&ss.rule.eq(rule)].set_index('component').loc[comps]
            bars=ax.bar(pos+off,a.rmse,.36,color=color,label=label)
            ax.bar_label(bars,labels=[f'{v:.2f}' for v in a.rmse],fontsize=8,padding=3)
        ax.set(xticks=pos,xticklabels=labels,ylabel='RMSE (K)',title='(a) EVO' if domain=='EVO' else '(b) European 12-station subset')
        ax.set_ylim(0,ax.get_ylim()[1]*1.19);ax.grid(axis='y',alpha=.17);ax.set_axisbelow(True)
    axs[0].legend(frameon=False,fontsize=8);savefig(fig,'figure09_filter_sensitivity')
    for label,records in [('europe12_sites',site_records)]:facts[label]=records
    facts['source_sha256']=hashes
    assert hashes=={str(p):hashlib.sha256(p.read_bytes()).hexdigest() for p in sources}
    (OUT/'validation_facts.json').write_text(json.dumps(facts,ensure_ascii=False,indent=2),encoding='utf8')
    (OUT/'preparation_audit.json').write_text(json.dumps(dict(status='passed',evo_metrics_checked=3,europe_station_metrics_checked=24,new_inversions=0,source_sha256=hashes),indent=2),encoding='utf8')
    print(json.dumps({k:v for k,v in facts.items() if k.startswith('evo_') or k.startswith('europe12_joint') or k.startswith('europe12_range')},indent=2))
    print('OUTPUT',OUT)

if __name__=='__main__':main()
