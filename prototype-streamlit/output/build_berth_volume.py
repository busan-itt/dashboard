"""Render horizontal workload comparisons from the published report values.

ODT compares unloading/loading side by side. ITT contains only the HJNC
operation for each direction; the opposite terminal is outside this dataset.
"""
from pathlib import Path
import json
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import numpy as np

ROOT = Path(__file__).resolve().parents[1]
CHARTS = ROOT/'assets/correlation-analysis/unified'
BLUE, CORAL, INK = '#3F617C', '#F4A78D', '#192C3A'


def build():
    plt.rcParams.update({'font.family':'Malgun Gothic','font.size':12,
                         'axes.unicode_minus':False,'text.color':INK,
                         'axes.labelcolor':INK,'xtick.color':'#637784','ytick.color':INK})
    values = json.loads((CHARTS/'berth-volume-values.json').read_text(encoding='utf-8'))
    hjnc = json.loads((CHARTS/'unified-berth-values.json').read_text(encoding='utf-8'))['hjnc_volume']
    reports = json.loads((CHARTS/'reports.json').read_text(encoding='utf-8'))
    for key, entry in values.items():
        series = hjnc if key == 'hjnc' else entry['series']
        berths = list(next(iter(series.values())))
        y = np.arange(len(berths))
        fig, ax = plt.subplots(figsize=(11, 5.5))
        paired = len(series) == 2
        maximum = max(max(s.values()) for s in series.values())
        for operation, vals in series.items():
            offset = (-.18 if operation == 'unload' else .18) if paired else 0
            bars = ax.barh(y+offset, [vals[b] for b in berths], height=.29 if paired else .44,
                           color=BLUE if operation == 'unload' else CORAL,
                           label='양하' if operation == 'unload' else '적하')
            ax.bar_label(bars, labels=[f'{vals[b]:,.2f}'.rstrip('0').rstrip('.') for b in berths],
                         padding=7, color=INK, fontsize=11)
        ax.set_yticks(y, berths); ax.invert_yaxis(); ax.set_xlim(0, maximum*1.2)
        ax.set_xlabel('환적 작업 물동량 (TEU)', labelpad=12)
        ax.set_axisbelow(True); ax.grid(axis='x', color='#E7EDF1')
        ax.tick_params(axis='both', length=0, pad=8)
        for spine in ax.spines.values(): spine.set_visible(False)
        ax.legend(frameon=False, ncol=2, loc='upper right', bbox_to_anchor=(1,1.16))
        fig.text(.09,.95,entry['title'],fontsize=19,fontweight='bold',color=INK)
        fig.text(.09,.89,entry['scope'],fontsize=11,color='#637784')
        fig.subplots_adjust(left=.09,right=.98,top=.78,bottom=.15)
        target = CHARTS/reports[key]['berth'][0]['image']
        fig.savefig(target,dpi=160,facecolor='white');plt.close(fig)
        print('Built', target.name)


if __name__ == '__main__':
    build()
