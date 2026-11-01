"""Plot saved LSCT3 cloud/temperature diagnosis without changing products."""
from pathlib import Path
import argparse
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.colors import ListedColormap,BoundaryNorm
from matplotlib.patches import Rectangle
p=argparse.ArgumentParser();p.add_argument('diagnostics',type=Path);a=p.parse_args()
z=np.load(a.diagnostics/'focus_patch.npz');sl=(slice(20,61),slice(20,61))
fig,axes=plt.subplots(2,2,figsize=(11.5,9.5),layout='constrained')
fig.suptitle('Amazon daytime LSCT3: cloud-edge and cold-output diagnosis\n26 Apr 2024, 14:01 UTC | focus 5.92 S, 58.49 W',fontsize=15)
extent=(-20.5,20.5,20.5,-20.5)
for ax,view,title in zip(axes.flat[:2],('nadir','obliq'),('Nadir LST: focus 273.64 K','Oblique LST: focus 290.13 K')):
 im=ax.imshow(z['lst_'+view][sl],extent=extent,vmin=260,vmax=310,cmap='viridis',interpolation='nearest')
 cloud=z['cloud_'+view][sl]!=0
 ax.contour(np.arange(-20,21),np.arange(-20,21),cloud.astype(int),levels=[.5],colors=['#f04444'],linewidths=.7)
 fig.colorbar(im,ax=ax,label='Input LST (K)',fraction=.046,pad=.025)
 ax.set_title(title)
ax=axes[1,0];arr=z['product_soil'][sl];arr=np.ma.masked_where(arr<=0,arr)
cmap=plt.get_cmap('viridis').copy();cmap.set_bad('white')
im=ax.imshow(arr,extent=extent,vmin=200,vmax=320,cmap=cmap,interpolation='nearest')
fig.colorbar(im,ax=ax,label='Retrieved soil temperature (K)',fraction=.046,pad=.025)
ax.set_title('Soil inversion: focus 212.93 K (unphysical here)')
ax=axes[1,1]
combined=(z['cloud_nadir'][sl]!=0).astype(int)+2*(z['cloud_obliq'][sl]!=0)
cmap=ListedColormap(['#eeeeee','#7b3294','#008837','#cc3311'])
im=ax.imshow(combined,extent=extent,cmap=cmap,norm=BoundaryNorm([-.5,.5,1.5,2.5,3.5],4),interpolation='nearest')
cb=fig.colorbar(im,ax=ax,ticks=[0,1,2,3],fraction=.046,pad=.025);cb.ax.set_yticklabels(['Neither','Nadir','Oblique','Both'])
ax.set_title('Existing cloud flags: focus unflagged in both views')
for ax in axes.flat:
 ax.add_patch(Rectangle((-2.5,-2.5),5,5,fill=False,edgecolor='black',linewidth=1.4))
 ax.scatter([0],[0],marker='+',color='#ff00dd',s=90,linewidths=2)
 ax.set_xlabel('Column offset from focus');ax.set_ylabel('Row offset from focus')
 ax.set_xticks([-20,-10,0,10,20]);ax.set_yticks([-20,-10,0,10,20])
fig.supxlabel('Black box = 5 x 5 retrieval window | magenta + = focus | red outlines = flagged clouds\nPixel-grid diagnostic; existing L1 flags do not establish that unflagged pixels are cloud-free.',fontsize=10)
fig.savefig(a.diagnostics/'cloud_cold_focus.png',dpi=160)
print(a.diagnostics/'cloud_cold_focus.png')
