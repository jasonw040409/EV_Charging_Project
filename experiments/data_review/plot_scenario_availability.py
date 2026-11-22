"""Task 4, figure 3: mutually exclusive availability groups, slide-ready.

Reads the frozen cohort/results and Task 2 summary. No optimization runs.
Run: .venv/bin/python experiments/data_review/plot_scenario_availability.py
"""
import argparse
import csv
import hashlib
import json
import os
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
os.environ.setdefault('MPLCONFIGDIR', str(ROOT / '.mplconfig'))
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import numpy as np


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--analysis-dir', default='results/data_review_nov21')
    parser.add_argument('--study-dir', default='results/nov18')
    parser.add_argument('--output-dir', default='results/data_review_nov21/figures')
    parser.add_argument('--pdf-dir', default='output/pdf/data_review_nov21')
    args = parser.parse_args()
    analysis, study, output, pdf_dir = [(ROOT/p).resolve() for p in
        [args.analysis_dir,args.study_dir,args.output_dir,args.pdf_dir]]
    paths = [analysis/'scenario_availability_by_soc.csv',study/'cohort.json',
             study/'metrics.json',study/'exclusions.json']
    hashes = {str(p):hashlib.sha256(p.read_bytes()).hexdigest() for p in paths}
    with paths[0].open() as stream:
        table = sorted(list(csv.DictReader(stream)),key=lambda r:float(r['assumed_initial_soc_pct']))
    cohort,metrics,exclusions = [json.loads(p.read_text()) for p in paths[1:]]
    cohort_ids = {r['sessionID'] for r in cohort}
    if len(cohort_ids)!=len(cohort):
        raise ValueError('Duplicate cohort sessions')
    counts=[]
    for r in table:
        initial=float(r['assumed_initial_soc_pct'])/100
        completed=[m for m in metrics if m.get('family')=='real' and m['method']=='cost_only' and m['scenario']['initial']==initial]
        failed=[e for e in exclusions if e.get('family')=='real' and e['status']=='analytically_infeasible' and e['scenario']['initial']==initial]
        clean={m['session_id'] for m in completed if not m['timing_flag']}
        flagged={m['session_id'] for m in completed if m['timing_flag']}
        infeasible={e['session_id'] for e in failed}
        if clean & flagged or clean & infeasible or flagged & infeasible:
            raise ValueError('Availability groups overlap')
        if clean|flagged|infeasible != cohort_ids:
            raise ValueError('Availability groups do not account for full cohort')
        if (len(clean),len(flagged),len(infeasible)) != (
            int(r['completed_clean_paired_cases']),int(r['completed_flagged_diagnostic_cases']),int(r['analytically_infeasible_cases'])):
            raise ValueError('Task 2 counts disagree with frozen study')
        for e in failed:
            if e['scenario']['target']<=e['scenario']['maximum_soc']:
                raise ValueError('Review infeasibility explanation before plotting')
        counts.append(dict(assumed_arrival_soc_pct=initial*100,clean_feasible=len(clean),
                           flagged_feasible=len(flagged),infeasible=len(infeasible)))
    plt.style.use('default')
    plt.rcParams.update({'font.size':12, 'axes.labelsize':12,
                         'xtick.labelsize':11, 'ytick.labelsize':12, 'pdf.fonttype':42})
    fig,ax=plt.subplots(figsize=(14,7.875))
    fig.subplots_adjust(left=.13,right=.975,bottom=.13,top=.86)
    ax.set_title('Scenario availability by assumed initial SOC',fontsize=16,
                 fontweight='normal',pad=18)
    categories=[('clean_feasible','Clean feasible','tab:blue','white'),
                ('flagged_feasible','Flagged feasible','0.7','black'),
                ('infeasible','Infeasible','tab:orange','black')]
    left=np.zeros(len(counts));ys=np.arange(len(counts))
    for key,label,color,textcolor in categories:
        values=np.array([r[key] for r in counts])
        ax.barh(ys,values,left=left,height=.5,color=color,label=label)
        for i,v in enumerate(values):
            if v:ax.text(left[i]+v/2,ys[i],str(v),ha='center',va='center',color=textcolor,fontsize=13)
        left+=values
    assert np.all(left==len(cohort))
    ax.set_yticks(ys,[f"{r['assumed_arrival_soc_pct']:.0f}%" for r in counts])
    ax.invert_yaxis();ax.set_ylim(len(counts)-.5,-.5)
    ax.set_xlim(0,len(cohort))
    ax.set_xticks(sorted(set([0,5,10,len(cohort)])))
    ax.set_xlabel('Number of session/SOC scenarios',labelpad=10)
    ax.set_ylabel('Assumed initial SOC',labelpad=10)
    ax.legend(loc='upper center',bbox_to_anchor=(.5,1.01),ncol=3,
              frameon=True,fancybox=False,fontsize=11)
    output.mkdir(parents=True,exist_ok=True);pdf_dir.mkdir(parents=True,exist_ok=True)
    stem='scenario_availability_slide'
    png,pdf=output/(stem+'.png'),pdf_dir/(stem+'.pdf')
    fig.savefig(png,dpi=220,facecolor='white');fig.savefig(pdf,facecolor='white');plt.close(fig)
    caption=(
        'The same 15 recorded sessions are evaluated at three hypothetical starting SOCs. '
        'Bars divide each starting-SOC group into mutually exclusive clean feasible, timing-flagged feasible, '
        'and analytically infeasible scenarios. Only the clean feasible groups (14, 14, 9) enter the main paired plot. '
        'The one flagged original control has a recorded charging-stop time after disconnection and remains in the diagnostic outputs. '
        'At 75% assumed arrival SOC, five targets exceed the assumed 90% upper cap, leaving ten feasible cases; '
        'removing the flagged feasible record leaves nine clean pairs. '
        'Infeasible scenarios reflect the assumed 60-kWh capacity, 90% efficiency and SOC constraints, not proof of invalid real sessions. '
        'Clean means no detected stop-order flag, not proof of complete data quality. '
        'These are 45 hypothetical session/SOC scenarios, not 45 independent real sessions. '
        'Counts describe the frozen November 18 pilot, not an unexecuted 50-session expansion.')
    (output/(stem+'_caption.txt')).write_text(caption+'\n')
    for p,h in hashes.items():
        if hashlib.sha256(Path(p).read_bytes()).hexdigest()!=h:raise RuntimeError('Source changed during plotting')
    manifest=dict(input_sha256=hashes,counts=counts,cohort_sessions=len(cohort),
        source_cross_check='PASS: CSV counts agree with saved study; mutually exclusive groups cover full cohort at each SOC',
        outputs=dict(png=str(png),pdf=str(pdf)),optimizer_executed=False,original_inputs_unchanged=True)
    (output/(stem+'_manifest.json')).write_text(json.dumps(manifest,indent=2)+'\n')
    print(png);print(pdf)


if __name__=='__main__':main()
