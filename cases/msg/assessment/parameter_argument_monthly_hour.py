"""Station-only monthly-hour argument for inversion parameters; no production writes."""
from pathlib import Path
import itertools, json, hashlib, datetime
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import select_joint_station_parameters as joint
from search_evo_parameters import retrieve, prepare
from compare_monthly_hour_factors import window_prepare

IMPL = Path('C:/work/ls4t-msg/cases/official/implementation')
ROOT = IMPL.parent/'results/production_assessment'
OUT = ROOT/'parameter_argument_monthly_hour'
BASE = dict(hotspot=.25, **{'lambda':1000.}, delta=3., first_window=5, second_window=5)
GRIDS = dict(hotspot=[.025,.05,.1,.15,.2,.25,.3,.35,.4,.5],
             **{'lambda':[.0001,.001,.01,.1,1.,10.,100.,1000.,10000.]},
             delta=[0.,.25,.5,1.,2.,3.,4.,5.,7.,10.])
PRED_KEYS = ['soil','canopy']

def sha(p): return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def js(name, value): (OUT/name).write_text(json.dumps(value,ensure_ascii=False,indent=2,allow_nan=False),encoding='utf8')
def md(df):
    x=df.copy()
    for c in x:
        if pd.api.types.is_float_dtype(x[c]): x[c]=x[c].map(lambda v:'NA' if pd.isna(v) else f'{v:.3f}')
    return '| '+' | '.join(x.columns)+' |\n| '+' | '.join(['---']*len(x.columns))+' |\n'+'\n'.join('| '+' | '.join(map(str,r))+' |' for r in x.itertuples(index=False,name=None))

def design():
    configs={'baseline':BASE.copy()}; members=[]
    def add(name,c):
        for n,old in configs.items():
            if old==c:return n
        configs[name]=c;return name
    for factor,vals in GRIDS.items():
        for value in vals:
            name=add(f'{factor}_{value:g}',{**BASE,factor:value})
            members.append(dict(family=factor,value=str(value),model=name))
    for w1,w2 in itertools.product([1,3,5],repeat=2):
        name=add(f'window_{w1}_{w2}',{**BASE,'first_window':w1,'second_window':w2})
        members.append(dict(family='window',value=f'{w1}/{w2}',model=name))
    for h,d in itertools.product([.05,.15,.25,.35,.5],[.5,1.,2.,3.,5.]):
        name=add(f'interaction_h{h:g}_d{d:g}',{**BASE,'hotspot':h,'delta':d})
        members.append(dict(family='hotspot_delta',value=f'{h:g}/{d:g}',model=name))
    return configs,pd.DataFrame(members)

def scalar_window_check(data,pre,c):
    wcenter,re,ri,rre,rri,sun,shade,veg=pre
    finite=np.flatnonzero(np.isfinite(np.stack([sun,shade,veg],axis=1)).all(axis=1))
    checks=[]
    for idx in finite[np.linspace(0,len(finite)-1,min(3,len(finite)),dtype=int)] if len(finite) else []:
        sub={k:v[idx:idx+1] for k,v in data.items()}
        # Independent least-squares systems, scalar sums via explicit neighbor loops.
        ns=joint.functions();waves=[]
        from search_evo_parameters import planck
        for sat in ['e','i']:
            angle=np.abs(sub['saa']-sub['vaa_'+sat]);angle=np.where(angle>180,360-angle,angle)
            a,b=ns['hotspot_layer'](sub['lai'],c['hotspot'],sub['vza_'+sat],sub['sza'],angle)
            waves.append(np.stack([sub['emis_s']*a,sub['emis_s']*(b-a),sub['emis_v']*(1-b)],axis=-1)[0])
        rad=[planck(sub['lst_'+sat][0])*wave.sum(axis=-1) for sat,wave in zip(['e','i'],waves)]
        common=np.isfinite(rad[0])&np.isfinite(rad[1])&np.isfinite(waves[0]).all(axis=-1)&np.isfinite(waves[1]).all(axis=-1)
        def fit(size,stage,first=0.):
            A=[];b=[]
            for y in range(2-size//2,3+size//2):
                for x in range(2-size//2,3+size//2):
                    if not common[y,x]:continue
                    for wave,r in zip(waves,rad):
                        q=wave[y,x]
                        A.append([q[0],q[1]+q[2]] if stage==1 else [q[1],q[2]])
                        b.append(r[y,x] if stage==1 else r[y,x]-q[0]*first)
            return np.linalg.lstsq(np.asarray(A),np.asarray(b),rcond=None)[0]
        first=fit(c['first_window'],1)[0];second=fit(c['second_window'],2,first)
        error=float(np.max(np.abs(np.array([first,*second])-np.array([sun[idx],shade[idx],veg[idx]]))))
        assert error<1e-4, (c,int(idx),error)
        checks.append(dict(first_window=c['first_window'],second_window=c['second_window'],index=int(idx),max_radiance_difference=error))
    return checks

def main():
    OUT.mkdir(exist_ok=True)
    if (OUT/'complete.json').exists():raise RuntimeError('Completed study exists; inspect it rather than duplicate it.')
    configs,members=design();members.to_csv(OUT/'design_membership.csv',index=False)
    paused=Path('E:/PRODUCTS/LSCT/MSG_5X5_PHYSICAL_V1/status.json');paused_sha=sha(paused)
    assert json.loads(paused.read_text(encoding='utf-8-sig'))['status']=='paused'
    protocol=dict(created_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),
        purpose='Parameter argument at monthly-hour scale, not a new optimal-parameter claim',
        configs=configs, grids=GRIDS, windows=[1,3,5], baseline=BASE,
        periods=dict(direct='EVO 2017 Aug-Dec',indirect='14 European sites 2018-2024'),
        temporal_split=dict(development='EVO Aug-Oct 2017, Europe 2018-2022',validation='EVO Nov-Dec 2017, Europe 2023-2024'),
        independence='Retrospective; these periods were previously inspected',
        monthly_rule='Each site/year/month/UTC hour, paired means, >=3 instantaneous pairs, >=3 groups/site',
        weighting='Within site equal monthly-hour groups; summary equal sites; direct and indirect kept separate',
        eligibility='Fixed baseline input panel and physical mask, including >=10 valid pairs in cached 5x5; all output bands 250-350 K',
        threshold='Only European component-wise instantaneous absolute error <=10 K; no EVO error filter',
        supports=['own_unfiltered','own_10K','paired_unfiltered','paired_baseline_10K','paired_both_10K'],
        paired_baseline_10K='Use candidate/baseline common finite inputs, but screen by baseline error only; candidate errors may exceed 10 K',
        window_limit='Center residual architecture, true central subsets of cached 5x5; no larger windows or boundary padding',
        zero_lambda='Excluded: two directional equations cannot uniquely solve three unknown components without a prior',
        bootstrap='Development-independent ranking not attempted. 2000 station-block draws for Europe, calendar-month-block draws for EVO, on retrospective validation monthly means; descriptive pointwise intervals only',
        source_sha256={str(p):sha(p) for p in [Path(__file__),IMPL/'select_joint_station_parameters.py',IMPL/'search_evo_parameters.py',IMPL/'compare_monthly_hour_factors.py',IMPL/'msg_lsct3.2-iter-site-cons-ig-center.py']})
    js('protocol.json',protocol);js('progress.json',dict(status='loading',total=len(configs)))
    joint.OUT=OUT;data,panel=joint.load_panel();ns=joint.functions();predictions={};pre_cache={};scalar=[]
    for i,(name,c) in enumerate(configs.items()):
        key=(c['hotspot'],c['first_window'],c['second_window'])
        with np.errstate(all='ignore'):
            if key not in pre_cache:pre_cache[key]=window_prepare(data,*key,ns['hotspot_layer'])
            pre=pre_cache[key]
            if c['hotspot']==.25 and c['lambda']==1000 and c['delta']==3:
                scalar.extend(scalar_window_check(data,pre,c))
            if name=='baseline':
                old=prepare(data,.25,'physical',5,'center',ns['hotspot_layer'])
                assert all(np.allclose(a,b,equal_nan=True,rtol=0,atol=1e-10) for a,b in zip(pre,old))
            temp,valid,active=retrieve(pre,data,c['lambda'],c['delta'],return_raw=True)
            temp=temp-273.15;temp[~valid|~panel.input_eligible.to_numpy()]=np.nan
        predictions[name]=joint.projected(temp,panel)
        js('progress.json',dict(status='inverting',completed=i+1,total=len(configs),model=name))
        print('INVERSION',i+1,'/',len(configs),name,flush=True)
    np.savez_compressed(OUT/'component_predictions.npz',**{name+'__'+comp:val[comp] for name,val in predictions.items() for comp in PRED_KEYS})
    scalar_df=pd.DataFrame(scalar);scalar_df.to_csv(OUT/'scalar_window_checks.csv',index=False)
    rows=[];coverage=[];monthly=[];boot=[];rng=np.random.default_rng(20261009)
    for ni,(name,values) in enumerate(predictions.items()):
        for comp in PRED_KEYS:
            eligible=panel['eligible_'+comp].to_numpy();ref=panel[comp+'_reference'].to_numpy()
            v=values[comp];b=predictions['baseline'][comp]
            direct=panel.domain.eq('direct').to_numpy()
            own=eligible&np.isfinite(v);common=own&np.isfinite(b)
            own10=own&(direct|(np.abs(v-ref)<=10));base10=direct|(np.abs(b-ref)<=10)
            masks=dict(own_unfiltered=own,own_10K=own10,paired_unfiltered=common,
                       paired_baseline_10K=common&base10,paired_both_10K=common&base10&(direct|(np.abs(v-ref)<=10)))
            for support,mask in masks.items():
                # A fixed eligible denominator exposes both prediction failure and reference-based exclusions.
                cv=panel[['domain','site','split']].copy();cv['eligible']=eligible;cv['kept']=mask
                cv=cv.groupby(['domain','site','split'],as_index=False)[['eligible','kept']].sum()
                cv['model']=name;cv['component']=comp;cv['support']=support;coverage.append(cv)
                z=panel.loc[mask,['domain','site','time','split','month','hour']].copy()
                z['reference']=ref[mask];z['prediction']=v[mask];z['baseline']=b[mask]
                g=z.groupby(['domain','site','split','month','hour'],as_index=False).agg(
                    reference=('reference','mean'),prediction=('prediction','mean'),baseline=('baseline','mean'),n_raw=('prediction','size'))
                g=g.loc[g.n_raw.ge(3)].copy();g['model']=name;g['component']=comp;g['support']=support
                monthly.append(g)
                for split in ['all','development','validation']:
                    a=g if split=='all' else g.loc[g.split.eq(split)]
                    for (domain,site),q in a.groupby(['domain','site']):
                        if len(q)<3:continue
                        err=q.prediction-q.reference;be=q.baseline-q.reference
                        paired=support.startswith('paired_')
                        rows.append(dict(model=name,component=comp,support=support,split=split,domain=domain,site=site,
                            rmse_K=float(np.sqrt(np.mean(err**2))),bias_K=float(err.mean()),mae_K=float(np.mean(np.abs(err))),
                            baseline_rmse_K=float(np.sqrt(np.mean(be**2))) if paired else np.nan,
                            mse_difference_K2=float(np.mean(err**2-be**2)) if paired else np.nan,
                            temperature_change_rms_K=float(np.sqrt(np.mean((q.prediction-q.baseline)**2))) if paired else np.nan,
                            n_groups=len(q),n_raw=int(q.n_raw.sum())))
                if support in ['paired_unfiltered','paired_baseline_10K']:
                    for domain in ['direct','indirect']:
                        a=g.loc[g.split.eq('validation')&g.domain.eq(domain)].copy()
                        if a.empty:continue
                        a['diff']=(a.prediction-a.reference)**2-(a.baseline-a.reference)**2
                        block='month' if domain=='direct' else 'site'
                        sizes=a.groupby('site').size();a=a.loc[a.site.isin(sizes.loc[sizes>=3].index)]
                        arr=a.groupby(block)['diff'].mean().to_numpy()
                        if not len(arr):continue
                        draws=rng.choice(arr,(2000,len(arr)),replace=True).mean(axis=1)
                        boot.append(dict(model=name,domain=domain,component=comp,support=support,blocks=len(arr),block=block,
                            mean_block_mse_difference_K2=float(arr.mean()),ci_low=float(np.quantile(draws,.025)),ci_high=float(np.quantile(draws,.975))))
        if (ni+1)%5==0:
            js('progress.json',dict(status='monthly_metrics',completed=ni+1,total=len(configs)))
            print('MONTHLY_METRICS',ni+1,'/',len(configs),flush=True)
    metrics=pd.DataFrame(rows);metrics.to_csv(OUT/'station_metrics.csv',index=False)
    summary=metrics.groupby(['model','domain','component','support','split'],as_index=False).agg(
        sites=('site','size'),mean_site_rmse_K=('rmse_K','mean'),mean_site_bias_K=('bias_K','mean'),
        mean_site_baseline_rmse_K=('baseline_rmse_K','mean'),mean_site_mse_difference_K2=('mse_difference_K2','mean'),
        mean_site_temperature_change_rms_K=('temperature_change_rms_K','mean'),n_groups=('n_groups','sum'),n_raw=('n_raw','sum'))
    summary.to_csv(OUT/'summary.csv',index=False)
    cv=pd.concat(coverage,ignore_index=True);cv['coverage']=cv.kept/cv.eligible.replace(0,np.nan)
    cv.to_csv(OUT/'station_coverage.csv',index=False)
    cvs=cv.groupby(['model','domain','component','support','split'],as_index=False).agg(
        sites=('site','size'),mean_site_coverage=('coverage','mean'),eligible=('eligible','sum'),kept=('kept','sum'))
    cvs.to_csv(OUT/'coverage_summary.csv',index=False)
    allmonth=pd.concat(monthly,ignore_index=True);allmonth.to_csv(OUT/'monthly_hour_pairs.csv.gz',index=False)
    pd.DataFrame(boot).to_csv(OUT/'validation_block_intervals.csv',index=False)
    # Readback checks compare saved means, counts and baseline metrics, not only in-memory results.
    read=pd.read_csv(OUT/'monthly_hour_pairs.csv.gz');checks=[]
    for r in metrics.sample(min(100,len(metrics)),random_state=20261009).itertuples():
        z=read.loc[read.model.eq(r.model)&read.site.eq(r.site)&read.component.eq(r.component)&read.support.eq(r.support)]
        if r.split!='all':z=z.loc[z.split.eq(r.split)]
        assert len(z)==r.n_groups and z.n_raw.sum()==r.n_raw
        checks.append(abs(float(np.sqrt(np.mean((z.prediction-z.reference)**2)))-r.rmse_K))
    assert max(checks)<1e-9
    prev=pd.read_csv(ROOT/'joint_parameter_selection/monthly_hour_factor_sensitivity/monthly_hour_summary.csv')
    for support,old_support in [('own_unfiltered','unfiltered'),('own_10K','europe_instant_10K')]:
        a=summary.loc[summary.model.eq('baseline')&summary.support.eq(support)&summary.split.eq('all')]
        b=prev.loc[prev.model.eq('baseline')&prev.family.eq('own')&prev.support.eq(old_support)&prev.split.eq('all')]
        q=a.merge(b,on=['domain','component'],suffixes=('_new','_old'));assert len(q)==4
        assert (q.mean_site_rmse_K_new-q.mean_site_rmse_K_old).abs().max()<1e-9
    assert sha(paused)==paused_sha
    render(summary,cv,members,configs)
    report(summary,cvs,members,configs)
    js('complete.json',dict(status='passed',configs=len(configs),design_memberships=len(members),
        monthly_rows=len(allmonth),station_metric_rows=len(metrics),readback_metric_checks=len(checks),
        max_readback_difference_K=max(checks),scalar_window_checks=len(scalar),
        max_scalar_radiance_difference=float(scalar_df.max_radiance_difference.max()),regional_status_unchanged=True,
        source_hashes_unchanged=all(sha(p)==h for p,h in protocol['source_sha256'].items())))
    js('progress.json',dict(status='complete',completed=len(configs),total=len(configs)))
    print('COMPLETE',OUT,flush=True)

def render(summary,coverage,members,configs):
    plt.rcParams.update({'font.family':'DejaVu Sans','font.size':9})
    for domain,title in [('direct','EVO direct component comparison'),('indirect','European indirect station comparison')]:
        fig,axs=plt.subplots(3,4,figsize=(16,10),layout='constrained')
        for col,factor in enumerate(['hotspot','lambda','delta','window']):
            des=members.loc[members.family.eq(factor)].copy();x=np.arange(len(des))
            labels=des.value.tolist()
            for row,comp in enumerate(PRED_KEYS):
                for support,color,label in [('own_unfiltered','#2369A8','No residual filter'),('own_10K','#D46B25','Europe instantaneous <=10 K')]:
                    if domain=='direct' and support=='own_10K':continue
                    a=summary.loc[summary.domain.eq(domain)&summary.component.eq(comp)&summary.support.eq(support)&summary.split.eq('all')]
                    a=des.merge(a,on='model',how='left')
                    axs[row,col].plot(x,a.mean_site_rmse_K,'o-',color=color,label=label,markersize=3)
                axs[row,col].set_title(f'{factor}: {comp}');axs[row,col].set_ylabel('Mean site monthly-hour RMSE (K)')
            for comp,color in [('soil','#2369A8'),('canopy','#D46B25')]:
                a=coverage.loc[coverage.domain.eq(domain)&coverage.component.eq(comp)&coverage.support.eq('own_10K')]
                a=a.groupby(['model','site'],as_index=False)[['eligible','kept']].sum();a['ratio']=a.kept/a.eligible.replace(0,np.nan)
                a=a.groupby('model',as_index=False).ratio.mean();a=des.merge(a,on='model',how='left')
                axs[2,col].plot(x,a.ratio,'o-',color=color,label=comp,markersize=3)
            axs[2,col].set_ylabel('Mean site retained fraction');axs[2,col].set_ylim(0,1)
            for row in range(3):
                axs[row,col].set_xticks(x,labels,rotation=55);axs[row,col].grid(alpha=.2)
        axs[0,0].legend(fontsize=8);axs[2,0].legend(fontsize=8)
        fig.suptitle(title+' | monthly-hour means | all available years\nOwn-support curves: interpret RMSE together with retained coverage; windows = first/second stage size')
        fig.savefig(OUT/f'parameter_effects_{domain}.png',dpi=170)
        fig.savefig(OUT/f'parameter_effects_{domain}.pdf');plt.close(fig)
    # Heatmaps describe tested h/d combinations; all other settings fixed.
    fig,axs=plt.subplots(2,2,figsize=(11,8),layout='constrained')
    for i,domain in enumerate(['direct','indirect']):
        for j,comp in enumerate(PRED_KEYS):
            a=summary.loc[summary.domain.eq(domain)&summary.component.eq(comp)&summary.support.eq('own_10K')&summary.split.eq('development')]
            a=members.loc[members.family.eq('hotspot_delta')].merge(a,on='model')
            a['h']=a.model.map(lambda n:configs[n]['hotspot']);a['d']=a.model.map(lambda n:configs[n]['delta'])
            tab=a.pivot(index='h',columns='d',values='mean_site_rmse_K').sort_index()
            im=axs[i,j].imshow(tab.to_numpy(),aspect='auto',cmap='viridis')
            axs[i,j].set_xticks(np.arange(len(tab.columns)),tab.columns);axs[i,j].set_yticks(np.arange(len(tab)),tab.index)
            axs[i,j].set_xlabel('delta (radiance units)');axs[i,j].set_ylabel('hotspot');axs[i,j].set_title(domain+' '+comp)
            for yy,xx in itertools.product(range(len(tab)),range(len(tab.columns))):axs[i,j].text(xx,yy,f'{tab.iloc[yy,xx]:.2f}',ha='center',va='center',fontsize=8,color='white')
            fig.colorbar(im,ax=axs[i,j],label='Monthly-hour RMSE (K)')
    fig.suptitle('Development-period h/d interaction | own support | Europe filtered <=10 K\nDirect and indirect references differ; no pooled accuracy or optimum claim')
    fig.savefig(OUT/'hotspot_delta_interaction.png',dpi=170);fig.savefig(OUT/'hotspot_delta_interaction.pdf');plt.close(fig)

def report(summary,coverage,members,configs):
    base=summary.loc[summary.model.eq('baseline')&summary.support.isin(['own_unfiltered','own_10K'])&summary.split.eq('all')]
    one=members.loc[members.family.ne('hotspot_delta')].merge(summary,on='model')
    one=one.loc[one.support.eq('own_10K')&one.split.eq('all')]
    ranges=one.groupby(['family','domain','component'],as_index=False).agg(min_rmse_K=('mean_site_rmse_K','min'),max_rmse_K=('mean_site_rmse_K','max'),min_sites=('sites','min'),max_sites=('sites','max'))
    ranges.to_csv(OUT/'factor_rmse_ranges.csv',index=False)
    text=f'''# 逐小时月均反演参数论证

## 试验完成情况

已运行{len(configs)}套独立配置，包含四类单因素试验、两个阶段窗口的9种组合，以及25种hotspot/delta组合（与单因素重复的配置只计算一次）。
所有输入来自站点5×5原始缓存，直接反演后匹配参考，未从区域成品提取；区域生产保持暂停，论文与冻结配置未修改。

基准：hotspot=0.25、lambda=1000、delta=3，两个阶段5×5、中心残差。物理普朗克波长10.5e-6 m，delta单位W m^-2 sr^-1 um^-1。

## 参数范围与科学含义

- hotspot={GRIDS['hotspot']}：影响阳照/阴影组分的方向性权重。
- lambda={GRIDS['lambda']}：先验正则化强度。lambda=0未测试，因为两个方向观测对三个未知组分欠定，不能唯一求解。
- delta={GRIDS['delta']}：限制第二阶段先验阴影土壤与冠层的辐射量差；不是10 K参考误差阈值，也不是最终温差的直接硬约束。
- 两阶段window分别为1、3、5，合计9种组合。“3/5”表示第一阶段3×3、第二阶段5×5。1×1作为无空间邻域的对照；未测试超过缓存范围的7×7或9×9。所有窗口沿用同一基准输入资格，避免同时改变输入QC。
- 交互网格：hotspot=[0.05,0.15,0.25,0.35,0.5]，delta=[0.5,1,2,3,5]；lambda=1000，两个阶段5×5。该网格并非全部参数的穷举。

## 评价规则

EVO：2017年8—12月，10—16 UTC，阳照土壤和冠层直接参考，不按预测误差筛选。
欧洲：2018—2024年14站，11—16 UTC，背景土壤对TS_1、冠层对TA，仅为间接一致性；土壤探针与表面辐射温度、气温与冠层温度并非相同物理量。
每年每月每个UTC小时分别计算配对均值，至少3个瞬时配对；每站至少3个组。逐站计算RMSE，再站点等权平均，不把EVO与欧洲合成一个物理RMSE。

输出同时包含以下口径：

1. own_unfiltered：每个配置自身物理有效样本，不按参考误差剔除。
2. own_10K：欧洲各组分瞬时绝对误差<=10 K后计算逐小时月均；EVO保持不变。它是条件性指标，必须结合样本损失解释。
3. paired_unfiltered：每个配置与基准共同有效的瞬时配对，两者用完全相同的参考和时间求月均。
4. paired_baseline_10K：在共同有效配对上，仅用固定基准的10 K条件定义样本。候选配置不再按自身误差删点，因此候选月均误差可以超过10 K。
5. paired_both_10K：候选与基准都通过10 K的共同样本，仅作敏感性展示。

后三种固定双方配对的指标用于区分真实温度/误差变化与删点影响；不同候选的共同子集仍可能不同，不能跨候选盲目比较一个数。
参考误差筛选不能用于无人值守区域生产，因为那里没有这些站点实测参考。

## 基准逐小时月均精度

{md(base[['domain','component','support','sites','mean_site_rmse_K','n_groups','n_raw']])}

## 单因素范围内的RMSE变化

下面是各自有效样本、欧洲10 K筛选后的范围；不是最优配置排名。站点数变化也列出，防止仅凭少数保留站的低RMSE下结论。

{md(ranges)}

## 图与逐站证据

![EVO参数曲线](parameter_effects_direct.png)

![欧洲参数曲线](parameter_effects_indirect.png)

![hotspot和delta组合](hotspot_delta_interaction.png)

图中的曲线同时展示误差和保留比例，横轴为离散试验值而非连续等距物理刻度。窗口图按第一/第二阶段排列。
热图只展示开发时段的描述性结果，各格有效样本可能不同，不能把最小色块直接选作生产参数。

## 开发/保留时段与不确定性

开发时段为EVO 2017年8—10月、欧洲2018—2022年；保留时段为EVO 11—12月、欧洲2023—2024年。
这些时段此前已经查看过，因此仅称回顾性分时段核验，不称独立未见测试。未依据保留时段自动重选参数。
validation_block_intervals.csv对共同样本上的“候选减基准”月均MSE差进行2000次分块重采样：欧洲以站点、EVO以月份为块。
负值有利于候选；EVO保留期只有两个月，区间极不稳定，只可描述。欧洲空间相关、样本可用性及多重比较也限制区间解释；未作确认性显著性检验。
first_window/second_window的独立最小二乘核验与基准回放结果见complete.json及scalar_window_checks.csv。

## 文件

- protocol.json、design_membership.csv：事先保存的范围与设计。
- summary.csv、station_metrics.csv：全部配置按域、组分、时段及口径的精度。
- station_coverage.csv、coverage_summary.csv：固定输入参考候选上的有效记录及筛选比例，不能解释为全年卫星覆盖率。
- monthly_hour_pairs.csv.gz：可复算的逐小时月均配对。
- component_predictions.npz、frozen_reference_panel.csv.gz：配置预测与固定输入/参考行对应，用于复算瞬时到月均过程。
- complete.json：完成及核验记录。

本试验提供参数敏感性证据，不生成“唯一最优”的标签。若要替换基准，需要同时核对EVO与间接站点、土壤与冠层、开发与保留时段，以及覆盖率，不能只依据筛选后的最小RMSE。
'''
    (OUT/'逐小时月均参数论证.md').write_text(text,encoding='utf8')

if __name__=='__main__':main()
