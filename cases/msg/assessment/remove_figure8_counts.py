"""Redraw only figure 8 from existing station metrics, without count labels."""
from pathlib import Path
import textwrap
import prepare_manuscript_validation as v

source=Path(v.__file__)
code=source.read_text(encoding='utf8')
count_line="        for j,r in enumerate(a.itertuples()):ax.text(j,max(r.rmse,r.bulk_rmse)+.2,f'n={r.n}',ha='center',fontsize=7)\n"
if count_line in code:
    code=code.replace(count_line,'')
    source.write_text(code,encoding='utf8')
style=code[code.index('    plt.rcParams.update('):code.index('    sources=')]
block=code[code.index('    fig,axs=plt.subplots(2,1,figsize=(9.2,5.5)'):code.index('    fig,axs=plt.subplots(1,2,figsize=(9.6,3.4)')]
block=block.replace("sites=sorted(eumonth['soil'].site.unique())","sites=sorted(site_metrics.loc[site_metrics.nsites.eq(12)&site_metrics.rule.eq('joint_10K')].site.unique())")
env=vars(v).copy()
env['site_metrics']=v.pd.read_csv(v.OUT/'station_metrics.csv')
exec(textwrap.dedent(style),env)
exec(textwrap.dedent(block),env)
print(v.FIG/'figure08_europe12.png')
