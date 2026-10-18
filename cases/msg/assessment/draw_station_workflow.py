from pathlib import Path
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch
out=Path(r'C:\work\ls4t-msg\cases\official\results\production_assessment\manuscript_validation_update\figures')
fig,ax=plt.subplots(figsize=(10,8.4));ax.set_xlim(0,10);ax.set_ylim(0,10);ax.axis('off')
boxes=[('Paired EURO and IODC inputs','Signed LST decoding; LAI and effective emissivities\nValid paired neighbors; daylight and viewing-angle screening'),('Stage 1  |  5 × 5 neighborhood','Estimate sunlit-soil radiance and the residual mixture\nShared local component-radiance approximation'),('Stage 2  |  5 × 5 neighborhood','Fix sunlit soil; estimate shaded soil and canopy\nApply sequential radiance constraints (δ = 3)'),('Regularized joint adjustment','Update all three component radiances around the sequential target\nλ = 1000; enforce shaded-soil ≤ sunlit-soil radiance'),('Component temperatures and paired evaluation','Aggregate soil radiances in the solar direction, then invert Planck\nScreen instantaneous pairs; form separate monthly means at 11–16 UTC')]
for i,(title,body) in enumerate(boxes):
 y=8.35-i*1.88
 ax.add_patch(FancyBboxPatch((.35,y),9.3,1.42,boxstyle='round,pad=0.12',facecolor='#edf3f7',edgecolor='#35576d',linewidth=1.25))
 ax.text(5,y+1.06,title,ha='center',va='center',fontsize=13,weight='bold',color='#183b50')
 ax.text(5,y+.49,body,ha='center',va='center',fontsize=11,linespacing=1.45)
 if i<4:ax.annotate('',xy=(5,y-.36),xytext=(5,y-.13),arrowprops=dict(arrowstyle='-|>',color='#35576d',lw=1.6))
fig.subplots_adjust(left=.015,right=.985,top=.99,bottom=.005)
fig.savefig(out/'figure03_station_workflow.png',dpi=220,facecolor='white');fig.savefig(out/'figure03_station_workflow.pdf')
