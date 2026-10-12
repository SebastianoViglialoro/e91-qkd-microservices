"""Export the security_status -> key_status thesis diagram, without simulations."""
from pathlib import Path
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch, FancyArrowPatch, Polygon

OUT = Path(__file__).resolve().parents[1] / 'docs' / 'figures'
OUT.mkdir(parents=True, exist_ok=True)
plt.rcParams.update({'font.family':'DejaVu Serif','svg.fonttype':'none','pdf.fonttype':42,'mathtext.fontset':'dejavuserif'})
fig,ax=plt.subplots(figsize=(7.2,4.7))
fig.subplots_adjust(left=.02,right=.98,bottom=.035,top=.98)
ax.set(xlim=(0,14.5),ylim=(0,9)); ax.axis('off')
ink='#222222'

def box(x,y,w,h,text,size=10):
    ax.add_patch(FancyBboxPatch((x-w/2,y-h/2),w,h,boxstyle='round,pad=0.02,rounding_size=.07',facecolor='#F6F6F6',edgecolor=ink,lw=.85,zorder=3))
    ax.text(x,y,text,ha='center',va='center',fontsize=size,color=ink,zorder=4)

def arrow(points):
    for a,b in zip(points[:-2],points[1:-1]):
        ax.plot([a[0],b[0]],[a[1],b[1]],color=ink,lw=.85,zorder=1)
    ax.add_patch(FancyArrowPatch(points[-2],points[-1],arrowstyle='-|>',mutation_scale=10,lw=.85,color=ink,zorder=1))

box(7.2,8.2,7.2,.85,'Valutazione delle metriche di sessione')
box(7.2,6.65,3.8,.8,'security_status')
arrow([(7.2,7.75),(7.2,7.07)])
for x,state in [(4.1,'secure'),(9.5,'degraded'),(12.6,'insecure')]:
    arrow([(7.2,6.23),(7.2,5.7),(x,5.7),(x,5.08)])
    box(x,4.7,2.5,.72,state)

# Only the secure branch tests the available sifted material.
x,y,w,h=4.1,3.05,4.4,1.65
ax.add_patch(Polygon([(x,y+h/2),(x+w/2,y),(x,y-h/2),(x-w/2,y)],closed=True,facecolor='white',edgecolor=ink,lw=.9,zorder=3))
ax.text(x,y,r'$N_{\mathrm{sifted}} \geq L_{\min}$',ha='center',va='center',fontsize=11,zorder=4)
arrow([(4.1,4.32),(4.1,3.91)])
box(9.5,3.05,3.35,.8,'discarded_degraded',8.1)
box(12.6,3.05,2.2,.8,'discarded',8.1)
arrow([(9.5,4.32),(9.5,3.47)])
arrow([(12.6,4.32),(12.6,3.47)])
box(1.8,1.02,2.9,.8,'generated',8.1)
box(6.15,1.02,4.65,.8,'insufficient_key_material',8.1)
arrow([(1.88,3.05),(1.8,3.05),(1.8,1.44)])
arrow([(6.32,3.05),(6.7,3.05),(6.7,1.44)])
ax.text(1.47,2.25,'sì',ha='center',fontsize=9)
ax.text(7.04,2.25,'no',ha='center',fontsize=9)
for ext in ('pdf','svg','png'):
    fig.savefig(OUT/f'security_status_key_status.{ext}',dpi=400,facecolor='white')
plt.close(fig)
