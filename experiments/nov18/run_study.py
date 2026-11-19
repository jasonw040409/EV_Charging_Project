"""Separate reproducible accelerated study; never rewrites baseline artifacts.
Run from root: .venv/bin/python experiments/nov18/run_study.py
"""
import os,sys,json,csv,math,hashlib,platform,time
from pathlib import Path
from dataclasses import replace,asdict
from email.utils import parsedate_to_datetime as parse
from zoneinfo import ZoneInfo
ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT/'src'))
os.environ.setdefault('MPLCONFIGDIR',str(ROOT/'.mplconfig'))
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from charging import Scenario,immediate,optimize,metrics,soc_from_power
from aging import evaluate,prior_loss
OUT=ROOT/'results/nov18'
METHODS=[('immediate',None,None),('cost_only',0,0),('power_penalty',1,0),('combined',1,10)]
rows=[];trajectories=[];exclusions=[]

def write(name,obj):
    (OUT/name).write_text(json.dumps(obj,indent=2,allow_nan=False)+'\n')

def solve_case(case,a,prices,**meta):
    try:a.validate()
    except ValueError as e:
        exclusions.append(dict(case=case,status='analytically_infeasible',reason=str(e),scenario=asdict(a),**meta));return
    results=[]
    for method,wp,ws in METHODS:
        started=time.perf_counter()
        try:
            p,info=(immediate(a),{'status':'deterministic','max_constraint_residual':0}) if wp is None else optimize(prices,a,wp,ws)
            s=soc_from_power(p,a);m=metrics(p,prices,a)
            if not(m['energy_residual_kwh']<1e-6 and m['power_violation_kw']<1e-6 and m['target_residual']<1e-8 and m['soc_violation']<1e-8 and info['max_constraint_residual']<1e-6):
                raise RuntimeError('Feasibility residual above acceptance limit')
            aging=evaluate(s,a.dt)
            r=dict(case=case,method=method,scenario=asdict(a),**meta,**m,**aging,solver=info,total_wall_seconds=time.perf_counter()-started)
            rows.append(r);results.append(r)
            trajectories.append(dict(case=case,method=method,power_kw=p.tolist(),soc=s.tolist(),price_dollars_per_kwh=np.asarray(prices).tolist(),interval_hours=a.dt,**meta))
        except Exception as e:
            exclusions.append(dict(case=case,method=method,status='numerical_or_evaluation_failure',reason=str(e),**meta))
    return results

def synthetic_prices(a,late=False,flat=False):
    h=np.arange(a.n)*a.dt
    if flat:return np.full(a.n,.20)
    if late:return np.where(h<7,.30,np.where(h<12,.10,.24))
    return np.where(h<4,.30,np.where(h<9,.10,.24))

def select_cohort():
    controls=json.loads((ROOT/'data/acn_sessions_raw.json').read_text())['_items']
    source=ROOT/'data/nov18/acn_candidate_snapshot.json'
    candidates=json.loads(source.read_text())['_items']
    ledger=[];bins={};seen={r['sessionID'] for r in controls}
    for r in sorted(candidates,key=lambda r:(r.get('connectionTime',''),r.get('sessionID',''))):
        sid=r.get('sessionID');reasons=[]
        try:
            start=parse(r['connectionTime']);end=parse(r['disconnectTime']);ZoneInfo(r['timezone'])
            h=(end-start).total_seconds()/3600;e=float(r['kWhDelivered'])
            if not math.isfinite(e) or e<=0 or h<=0:reasons.append('invalid energy/window')
            if r.get('doneChargingTime') and not start<=parse(r['doneChargingTime'])<=end:reasons.append('charging stop outside connected window')
            if e>7.2*h+1e-9:reasons.append('energy exceeds assumed power/window limit')
            if .3+.9*e/60>.9:reasons.append('baseline target exceeds assumed SOC cap')
        except Exception as err:reasons.append('missing or invalid required input: '+str(err))
        if sid in seen:reasons.append('original control or duplicate ID')
        seen.add(sid)
        key=None
        if not reasons:
            key=(0 if h<=4 else 1 if h<=8 else 2,0 if e<=5 else 1 if e<=10 else 2)
            bins.setdefault(key,[]).append(r)
        ledger.append(dict(session_id=sid,screening_reasons=reasons,bin=key))
    for values in bins.values():values.sort(key=lambda r:(parse(r['connectionTime']),r['sessionID']))
    selected=[]
    while len(selected)<10 and any(bins.values()):
        for k in sorted(bins):
            if bins[k] and len(selected)<10:selected.append(bins[k].pop(0))
    cohort=controls+selected
    selected_ids={r['sessionID'] for r in selected}
    for l in ledger:l['selected_addition']=l['session_id'] in selected_ids
    write('selection_ledger.json',ledger)
    write('cohort.json',cohort)
    write('data_provenance.json',dict(url='https://ev.caltech.edu/api/v1/sessions/caltech?max_results=100',retrieved='2026-11-18',authentication='official public DEMO_TOKEN',snapshot_sha256=hashlib.sha256(source.read_bytes()).hexdigest(),selection='Frozen first-page 100-record snapshot; deterministic duration/energy-bin round robin; five original controls plus ten additions. Not random or representative.',deviation_from_nov14_proposal='Bounded first-page snapshot used instead of date-window query; availability and dates documented in cohort. No outcome-based selection.',candidate_count=len(candidates),cohort_count=len(cohort)))
    return cohort,{r['sessionID'] for r in controls}

def plots():
    real=[r for r in rows if r.get('family')=='real' and not r.get('timing_flag')]
    paired=[]
    for c in sorted({r['case'] for r in real}):
        d={r['method']:r for r in real if r['case']==c}
        if len(d)==4:
            b=d['cost_only'];m=d['combined']
            paired.append(dict(case=c,initial_soc=m['scenario']['initial'],cost_premium=m['cost_dollars']-b['cost_dollars'],high_soc_change=m['high_soc_proxy']-b['high_soc_proxy'],calendar_change_ppm=m['calendar_increment_ppm']-b['calendar_increment_ppm']))
    write('paired_clean_results.json',paired)
    fig,axes=plt.subplots(1,2,figsize=(11,4),layout='constrained')
    for initial in [.3,.6,.75]:
        x=[r for r in paired if r['initial_soc']==initial]
        axes[0].scatter([r['cost_premium'] for r in x],[r['high_soc_change'] for r in x],label=f'Assumed start {initial:.0%}')
        axes[1].scatter([r['cost_premium'] for r in x],[r['calendar_change_ppm'] for r in x])
    axes[0].set_ylabel('Change in high-SOC proxy');axes[1].set_ylabel('Change in calendar estimate (ppm)')
    for ax in axes:ax.set_xlabel('Combined minus cost-only expense ($)');ax.axhline(0,color='grey',lw=.8);ax.grid(alpha=.2)
    axes[0].legend(fontsize=8);fig.suptitle('Clean real-session cases | synthetic prices | assumed SOC')
    fig.savefig(OUT/'paired_tradeoffs.png',dpi=160);plt.close(fig)
    # Representative selected before inspecting outcomes: S2 with assumed 60% start.
    case='real_1_soc60'
    ts=[r for r in trajectories if r['case']==case]
    fig,axes=plt.subplots(3,1,figsize=(9,7),sharex=True,layout='constrained')
    for i,r in enumerate(ts):
        t=np.arange(len(r['soc']))*r['interval_hours']
        if i==0:axes[0].stairs(r['price_dollars_per_kwh'],t,color='black')
        axes[1].stairs(r['power_kw'],t,label=r['method']);axes[2].plot(t,np.array(r['soc'])*100)
    axes[0].set_ylabel('Synthetic $/kWh');axes[1].set_ylabel('Grid kW');axes[2].set_ylabel('Assumed SOC (%)')
    axes[1].legend(fontsize=8,ncol=2);axes[2].axhline(70,ls=':',color='grey');axes[2].set_xlabel('Hours since actual connection')
    fig.suptitle('S2 at assumed 60% arrival | retrospective known departure')
    fig.savefig(OUT/'representative_soc60.png',dpi=160);plt.close(fig)
    sweep=[r for r in rows if r.get('family')=='weights']
    fig,ax=plt.subplots(figsize=(6,4),layout='constrained')
    ax.scatter([r['cost_dollars'] for r in sweep],[r['high_soc_proxy'] for r in sweep]);ax.set_xlabel('Expense ($)');ax.set_ylabel('High-SOC proxy');ax.set_title('Synthetic 12-pair weight study');ax.grid(alpha=.2)
    fig.savefig(OUT/'weight_tradeoffs.png',dpi=160);plt.close(fig)

def main():
    OUT.mkdir(exist_ok=True,parents=True)
    cohort,control_ids=select_cohort()
    for i,r in enumerate(cohort):
        start=parse(r['connectionTime']);end=parse(r['disconnectTime']);h=(end-start).total_seconds()/3600;e=r['kWhDelivered'];n=math.ceil(h/.25)
        local=start.astimezone(ZoneInfo(r['timezone']));clock=local.hour+local.minute/60+local.second/3600+np.arange(n)*h/n
        flag=bool(r.get('doneChargingTime') and not start<=parse(r['doneChargingTime'])<=end)
        prices=np.where((clock%24>=16)&(clock%24<21),.30,.15)
        for initial in [.3,.6,.75]:
            a=Scenario(n=n,dt=h/n,initial=initial,target=initial+.9*e/60)
            solve_case(f'real_{i}_soc{int(initial*100)}',a,prices,family='real',session_id=r['sessionID'],timing_flag=flag,original_control=r['sessionID'] in control_ids)
    print('Real-session study finished',flush=True)
    base=Scenario()
    variants=[('baseline',base,False,False),('flat',base,False,True),('late_cheap',base,True,False)]
    for hours in [5,8,12]:variants.append((f'window_{hours}h',replace(base,n=int(hours*4)),False,False))
    for ref in [.6,.7,.8]:variants.append((f'threshold_{ref}',replace(base,reference_soc=ref),False,False))
    for start,goal in [(.2,.8),(.5,.8),(.3,.9)]:variants.append((f'soc_{start}_{goal}',replace(base,initial=start,target=goal),False,False))
    for minutes in [60,30,15,5]:variants.append((f'resolution_{minutes}m',replace(base,n=int(720/minutes),dt=minutes/60),False,False))
    for name,a,late,flat in variants:solve_case(name,a,synthetic_prices(a,late,flat),family='sensitivity')
    for wp in [0,.1,1,10]:
        for ws in [0,1,10]:
            p,info=optimize(synthetic_prices(base),base,wp,ws);m=metrics(p,synthetic_prices(base),base)
            if m['energy_residual_kwh']>=1e-6 or info['max_constraint_residual']>=1e-6:raise RuntimeError('Weight sweep feasibility')
            rows.append(dict(case=f'weight_{wp}_{ws}',method='weighted',family='weights',weight_power=wp,weight_soc=ws,scenario=asdict(base),**m,**evaluate(soc_from_power(p,base),base.dt),solver=info))
    # Post-evaluation sensitivity changes no power schedule; same prehistory within each paired case.
    aging=[]
    for r in trajectories:
        if r['case']!='baseline':continue
        for temperature in [15,25,35]:
            for days in [0,365,1095]:
                aging.append(dict(method=r['method'],prior_days=days,prehistory_temperature_c=25,prehistory_soc=.5,**evaluate(r['soc'],r['interval_hours'],prior_loss(days),temperature)))
    write('aging_sensitivity.json',aging)
    write('metrics.json',rows);write('trajectories.json',trajectories);write('exclusions.json',exclusions)
    plots()
    summary=dict(successful_schedules=len(rows),trajectory_count=len(trajectories),excluded_scenarios_or_failures=len(exclusions),cohort_sessions=len(cohort),analytically_infeasible=sum(r['status']=='analytically_infeasible' for r in exclusions),numerical_failures=sum(r['status']!='analytically_infeasible' for r in exclusions),max_energy_residual_kwh=max(r['energy_residual_kwh'] for r in rows),python=platform.python_version(),numpy=np.__version__,calendar_estimates='provisional, pending independent model review',manual_review='not completed by automation')
    write('run_summary.json',summary)
    print(json.dumps(summary,indent=2))
if __name__=='__main__':main()
