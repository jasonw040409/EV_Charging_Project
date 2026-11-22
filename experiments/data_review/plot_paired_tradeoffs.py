"""Task 4, figure 2: concise slide export of frozen clean paired changes.

Run: .venv/bin/python experiments/data_review/plot_paired_tradeoffs.py
No optimizer runs. Raw deltas retained, with horizontal offsets for visibility.
"""
import argparse
import csv
import hashlib
import json
import math
import os
import statistics
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
os.environ.setdefault('MPLCONFIGDIR', str(ROOT / '.mplconfig'))
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.lines import Line2D
from matplotlib.ticker import FuncFormatter, MaxNLocator
import numpy as np

PANELS = [('high_soc_proxy', 'High-SOC exposure', 'Change in score'),
          ('peak_kw', 'Peak charging power', 'Change in peak (kW)'),
          ('cost_dollars', 'Electricity cost', 'Change in cost ($)')]


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--analysis-dir', default='results/data_review_nov21')
    parser.add_argument('--study-dir', default='results/nov18')
    parser.add_argument('--output-dir', default='results/data_review_nov21/figures')
    parser.add_argument('--pdf-dir', default='output/pdf/data_review_nov21')
    args = parser.parse_args()
    analysis, study, output, pdf_dir = [(ROOT/p).resolve() for p in
        [args.analysis_dir, args.study_dir, args.output_dir, args.pdf_dir]]
    paths = [analysis/'paired_case_changes.csv', study/'metrics.json']
    hashes = {str(p):hashlib.sha256(p.read_bytes()).hexdigest() for p in paths}
    with paths[0].open() as stream:
        rows = list(csv.DictReader(stream))
    source = {(r['case'],r['method']):r for r in json.loads(paths[1].read_text()) if r.get('family')=='real'}
    selected = [r for r in rows if r['quality_group']=='clean' and
                r['comparison_method']=='combined' and r['reference_method']=='power_penalty' and
                r['metric'] in {p[0] for p in PANELS}]
    groups = {}
    for initial in [30,60,75]:
        groups[initial] = {}
        for metric, _, _ in PANELS:
            values = sorted([r for r in selected if float(r['assumed_initial_soc_pct'])==initial and r['metric']==metric],
                            key=lambda r:r['case'])
            if not values or len({r['case'] for r in values})!=len(values):
                raise ValueError('Empty group or duplicate case')
            for r in values:
                a,b=source[r['case'],'combined'],source[r['case'],'power_penalty']
                if a['timing_flag'] or b['timing_flag'] or a['session_id']!=r['session_id'] or a['scenario']!=b['scenario']:
                    raise ValueError('Invalid clean paired membership')
                if not math.isclose(float(r['change']),a[metric]-b[metric],abs_tol=1e-12):
                    raise ValueError('Analysis export differs from frozen study')
            groups[initial][metric]=values
        if len({tuple(r['case'] for r in v) for v in groups[initial].values()})!=1:
            raise ValueError('Metrics have different case denominators')
    plt.style.use('default')
    plt.rcParams.update({'font.size':12, 'axes.labelsize':12,
                         'xtick.labelsize':11, 'ytick.labelsize':11, 'pdf.fonttype':42})
    fig,axes=plt.subplots(1,3,figsize=(14,7.875))
    fig.subplots_adjust(left=.08,right=.975,bottom=.17,top=.85,wspace=.36)
    fig.suptitle('Paired changes: combined minus power penalty', fontsize=16,
                 fontweight='normal', y=.975)
    fig.legend(handles=[Line2D([],[],marker='o',linestyle='',color='tab:blue',markersize=5,label='Session pair'),
                        Line2D([],[],color='black',lw=2,label='Median')],
               loc='upper center',bbox_to_anchor=(.5,.945),ncol=2,
               frameon=True,fancybox=False,fontsize=11)
    medians=[]
    for ax,(metric,title,ylabel) in zip(axes,PANELS):
        all_values=[]
        for pos,initial in enumerate([30,60,75]):
            records=groups[initial][metric]
            values=[float(r['change']) for r in records]
            offsets=np.linspace(-.17,.17,len(values)) if len(values)>1 else [0]
            ax.scatter(pos+np.array(offsets),values,s=26,color='tab:blue',alpha=.75,zorder=3)
            median=statistics.median(values)
            ax.plot([pos-.23,pos+.23],[median,median],color='black',lw=2,zorder=4,solid_capstyle='round')
            medians.append(dict(assumed_initial_soc_pct=initial,metric=metric,case_count=len(values),median_change=median))
            all_values.extend(values)
        low,high=min(min(all_values),0),max(max(all_values),0)
        span=max(high-low, .01 if metric=='high_soc_proxy' else .1)
        ax.set_ylim(low-.10*span,high+.14*span)
        ax.axhline(0,color='0.4',linestyle='--',lw=1,zorder=1)
        ax.set_xticks([0,1,2],[f"{s}%\nn = {len(groups[s][metric])}" for s in [30,60,75]])
        ax.set_xlim(-.5,2.5)
        axis_labels={'high_soc_proxy':'High-SOC score difference',
                     'peak_kw':'Peak power difference (kW)',
                     'cost_dollars':'Cost difference ($)'}
        ax.set_ylabel(axis_labels[metric],labelpad=9)
        ax.yaxis.set_major_locator(MaxNLocator(nbins=5))
        ax.yaxis.set_major_formatter(FuncFormatter(lambda x,pos: '0' if abs(x)<1e-10 else f'{x:g}'))
        ax.grid(axis='y',color='0.85',lw=.6,alpha=.7)
        ax.set_axisbelow(True)
    fig.supxlabel('Assumed initial SOC',fontsize=12,y=.055)
    output.mkdir(parents=True,exist_ok=True);pdf_dir.mkdir(parents=True,exist_ok=True)
    stem='paired_tradeoffs_slide'
    png,pdf=output/(stem+'.png'),pdf_dir/(stem+'.pdf')
    fig.savefig(png,dpi=220,facecolor='white');fig.savefig(pdf,facecolor='white');plt.close(fig)
    caption=(
        'Each dot compares Combined with Power penalty for the same recorded session and assumed arrival SOC. '
        'Vertical values are Combined minus Power penalty; horizontal offsets separate individual cases and have no quantitative meaning. '
        'Black bars show median paired changes, not differences between unpaired medians. '
        'Negative exposure changes mean a smaller high-SOC score; positive peak/cost changes mean larger peaks/extra cost. '
        'Only complete clean pairs are shown (14, 14 and 9 at assumed 30%, 60%, 75% starts). '
        'The flagged original control and analytically infeasible cases are excluded from this figure, not erased from the study. '
        'SOC and prices are assumed/synthetic; repeated SOC scenarios are not independent sessions. '
        'Very small raw numerical differences remain in the plot but are not practically interpretable. '
        'These scheduling-proxy findings do not establish measured battery-health improvement; scientific review remains outstanding.')
    (output/(stem+'_caption.txt')).write_text(caption+'\n')
    for p,h in hashes.items():
        if hashlib.sha256(Path(p).read_bytes()).hexdigest()!=h:
            raise RuntimeError('Frozen input changed')
    manifest=dict(input_sha256=hashes,comparison='combined minus power_penalty',
                  clean_case_counts={s:len(groups[s]['cost_dollars']) for s in groups},
                  paired_medians=medians,source_cross_check='PASS: every plotted delta and case membership checked against frozen metrics',
                  outputs=dict(png=str(png),pdf=str(pdf)),optimizer_executed=False,original_inputs_unchanged=True)
    (output/(stem+'_manifest.json')).write_text(json.dumps(manifest,indent=2)+'\n')
    print(png);print(pdf)


if __name__=='__main__':main()
