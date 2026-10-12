"""Draw a compact campaign overview from the saved CSV; no runs are executed."""
import csv
from collections import Counter
from pathlib import Path
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch

ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'docs'/'figures'
OUT.mkdir(parents=True,exist_ok=True)
with (ROOT/'results/final/final_experiment_runs.csv').open() as f:
    rows=list(csv.DictReader(f))
counts=Counter(r['scenario_name'] for r in rows)
repeats=set(counts.values())
if len(repeats)!=1:
    raise ValueError('The campaign does not have uniform repetition counts')
plt.rcParams.update({'font.family':'DejaVu Serif','svg.fonttype':'none','pdf.fonttype':42})
# Native size: 16.5 x 3.8 cm, leaving room for a short caption.
fig,ax=plt.subplots(figsize=(16.5/2.54,3.8/2.54))
fig.subplots_adjust(left=.008,right=.992,bottom=.035,top=.975)
ax.set(xlim=(0,10),ylim=(0,2.5));ax.axis('off')
items=[('Baseline','Riferimento\nideale'),('Link Loss','Attenuazione\ne perdite'),
       ('Noise','bit_flip\ndepolarizing'),('Eve','randomize\nintercept_resend'),
       ('Combined','Noise + Eve\nLink Loss +\nNoise + Eve')]
for i,(title,detail) in enumerate(items):
    x=1+2*i
    ax.add_patch(FancyBboxPatch((x-.94,.88),1.88,1.5,boxstyle='round,pad=0.015,rounding_size=.06',facecolor='#F6F6F6',edgecolor='#222222',lw=.75))
    ax.text(x,2.08,title,ha='center',va='center',fontsize=9,fontweight='bold')
    ax.text(x,1.46,detail,ha='center',va='center',fontsize=7.6,linespacing=1.35)
# A shared bracket groups parallel families without implying sequential stages.
ax.plot([.35,.35,9.65,9.65],[.75,.60,.60,.75],color='#333333',lw=.75)
ax.plot([5,5],[.60,.46],color='#333333',lw=.75)
ax.text(5,.22,f'{len(counts)} scenari × {next(iter(repeats))} ripetizioni = {len(rows)} run',
        ha='center',va='center',fontsize=9.5)
for ext in ('pdf','svg','png'):
    fig.savefig(OUT/f'campagna_sperimentale_schema.{ext}',dpi=400,facecolor='white')
plt.close(fig)
