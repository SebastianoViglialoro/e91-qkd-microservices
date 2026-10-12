"""Export a print-oriented thesis figure; no simulations or results are changed."""
from pathlib import Path
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch, FancyArrowPatch, Rectangle

OUT = Path(__file__).resolve().parents[1] / 'docs' / 'figures'
OUT.mkdir(parents=True, exist_ok=True)
plt.rcParams.update({'font.family': 'DejaVu Serif', 'svg.fonttype': 'none', 'pdf.fonttype': 42})
# Sized for a thesis text block; font sizes remain readable at native width.
fig, ax = plt.subplots(figsize=(6.3, 7.8))
fig.subplots_adjust(left=.015, right=.985, bottom=.015, top=.985)
ax.set(xlim=(0,10), ylim=(0,12.5)); ax.axis('off')
ink = '#222222'

def area(x,y,w,h,title):
    ax.add_patch(Rectangle((x,y),w,h,facecolor='white',edgecolor='#777777',lw=.7,zorder=0))
    ax.text(x+w/2,y+h-.28,title,ha='center',va='center',fontsize=8.4,fontweight='bold',color=ink)

def box(x,y,w,h,text,size=9,subtitle=None):
    ax.add_patch(FancyBboxPatch((x-w/2,y-h/2),w,h,boxstyle='round,pad=0.015,rounding_size=.055',facecolor='#F6F6F6',edgecolor=ink,lw=.8,zorder=3))
    title_y = y + (.23 if subtitle and '\n' in subtitle else .14 if subtitle else 0)
    ax.text(x,title_y,text,ha='center',va='center',fontsize=size,color=ink,linespacing=1.35,zorder=4)
    if subtitle:
        ax.text(x,y-.15,subtitle,ha='center',va='center',fontsize=7.3,color=ink,linespacing=1.35,zorder=4)

def arrow(points,dashed=False):
    for a,b in zip(points[:-2],points[1:-1]):
        ax.plot([a[0],b[0]],[a[1],b[1]],color=ink,lw=.8,ls='--' if dashed else '-',zorder=1)
    ax.add_patch(FancyArrowPatch(points[-2],points[-1],arrowstyle='-|>',mutation_scale=9,lw=.8,linestyle='--' if dashed else '-',color=ink,zorder=1))

# Infrastructure is a side plane, not a fourth sequential processing stage.
area(.1,.55,2.5,11.75,'INFRASTRUTTURA')
box(1.35,11.2,2.1,.65,'API Gateway')
box(1.35,9.9,2.1,.7,'Orchestrator')
arrow([(1.35,10.86),(1.35,10.27)])
box(1.35,2.05,2.1,.85,'Result Store\nMini KMS')
box(1.35,.99,2.1,.6,'Dashboard')
arrow([(1.35,1.61),(1.35,1.31)])

area(2.9,5.45,7,6.85,'PIANO QUANTISTICO SIMULATO')
box(6.4,11.2,3.7,.65,'Entangled Source')
box(6.4,10.05,3.7,.8,'Quantum Channel\nLink Loss')
arrow([(6.4,10.86),(6.4,10.47)])
box(8.9,8.85,1.55,.7,'Noise / Eve',8,subtitle='perturbazioni')
arrow([(8.27,10.05),(8.9,10.05),(8.9,9.22)])
# Receiver bases feed the single joint sampler; final outcomes return to the
# receivers for registration. Vertically separated stages keep arrows legible.
box(4.6,8.85,2.1,.75,'Receiver Alice',size=8.3,subtitle='selezione della base')
box(6.95,8.85,2.1,.75,'Receiver Bob',size=8.3,subtitle='selezione della base')
arrow([(5.45,9.63),(5.45,9.43),(4.6,9.43),(4.6,9.24)])
arrow([(6.95,9.63),(6.95,9.24)])
box(6.4,7.42,4.55,.95,'Joint Outcome Sampling',subtitle='campionamento centralizzato\napplicazione Noise/Eve')
arrow([(4.6,8.46),(4.6,8.13),(5.35,8.13),(5.35,7.91)])
arrow([(6.95,8.46),(6.95,7.91)])
arrow([(8.9,8.48),(8.9,7.42),(8.7,7.42)])
arrow([(2.42,9.9),(2.74,9.9),(2.74,7.42),(4.1,7.42)],True)
box(4.6,6.03,2.65,.72,'Alice',subtitle='registrazione outcome')
box(8,6.03,2.65,.72,'Bob',subtitle='registrazione outcome')
arrow([(5.35,6.93),(5.35,6.62),(4.6,6.62),(4.6,6.41)])
arrow([(7.4,6.93),(7.4,6.62),(8,6.62),(8,6.41)])

area(2.9,.55,7,4.55,'PIANO CLASSICO')
box(6.4,4.18,4.55,.8,'Classical Channel',subtitle='associazione dei record e sifting')
arrow([(4.6,5.65),(4.6,5.28),(3.2,5.28),(3.2,4.18),(4.1,4.18)])
arrow([(8,5.65),(8,5.28),(9.6,5.28),(9.6,4.18),(8.7,4.18)])
box(6.4,2.82,4.55,.8,'Sifting-Bell-Test',subtitle='CHSH, QBER, security_status')
arrow([(6.4,3.76),(6.4,3.24)])
box(6.4,1.42,4.55,.8,'Key Processing',subtitle='final_key, key_status')
arrow([(6.4,2.40),(6.4,1.84)])
arrow([(4.1,1.42),(2.75,1.42),(2.75,2.05),(2.42,2.05)])
for ext in ('svg','pdf','png'):
    fig.savefig(OUT / f'architettura_pipeline_tesi.{ext}',dpi=400,facecolor='white')
plt.close(fig)
