"""Separate, offline Part 2 replay. Never writes to the reference pack."""
import argparse, collections, hashlib, json, math, os, platform, sys, time
from dataclasses import asdict, replace
from email.utils import parsedate_to_datetime as parse
from pathlib import Path
from zoneinfo import ZoneInfo
ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT/'src'))
import numpy as np
import cvxpy, clarabel
from charging import Scenario, immediate, optimize, metrics, soc_from_power
from aging import evaluate, prior_loss

METHODS = [('immediate', None, None), ('cost_only', 0, 0), ('power_penalty', 1, 0), ('combined', 1, 10)]

def sha(path): return hashlib.sha256(path.read_bytes()).hexdigest()
def dump(path, obj): path.write_text(json.dumps(obj, indent=2, allow_nan=False)+'\n')
def prices(a, mode='baseline'):
    h = np.arange(a.n)*a.dt
    if mode == 'flat': return np.full(a.n, .2)
    if mode == 'late': return np.where(h<7,.30,np.where(h<12,.10,.24))
    return np.where(h<4,.30,np.where(h<9,.10,.24))

def main():
    ap=argparse.ArgumentParser(); ap.add_argument('--config', default='experiments/part2/config.json'); ap.add_argument('--out', required=True)
    args=ap.parse_args(); cfgpath=(ROOT/args.config).resolve(); cfg=json.loads(cfgpath.read_text()); out=Path(args.out).resolve()
    if out == ROOT or out in [ROOT/'results',ROOT/'results/nov18'] or ROOT/'results/nov18' in out.parents: raise ValueError('Output must be separate from frozen results')
    if out.exists() and any(out.iterdir()): raise ValueError('Output directory must be empty')
    out.mkdir(parents=True,exist_ok=True)
    cohortpath=(ROOT/cfg['cohort_file']).resolve(); cohort=json.loads(cohortpath.read_text()); rows=[]; paths=[]; failures=[]; case_ids=set()
    def fail(case, category, error, **meta): failures.append(dict(case=case,category=category,reason=str(error),**meta))
    def solve(case,a,c,family,methods=METHODS,**meta):
        if case in case_ids: raise ValueError('Duplicate case ID: '+case)
        case_ids.add(case)
        try: a.validate()
        except ValueError as e: fail(case,'infeasible_assumed_scenario' if 'Infeasible' in str(e) or a.target>a.maximum_soc else 'invalid_scenario',e,scenario=asdict(a),**meta); return
        for method,wp,ws in methods:
            try:
                p,info=(immediate(a),{'status':'deterministic','max_constraint_residual':0}) if wp is None else optimize(c,a,wp,ws)
                s=soc_from_power(p,a); m=metrics(p,c,a)
                assert len(p)==a.n and len(s)==a.n+1 and len(c)==a.n
                assert np.allclose(s, a.initial+np.r_[0,np.cumsum(p*a.efficiency*a.dt/a.capacity)],atol=1e-12,rtol=0)
                assert m['energy_residual_kwh']<1e-6 and m['power_violation_kw']<1e-6 and m['target_residual']<1e-8 and m['soc_violation']<1e-8 and info['max_constraint_residual']<1e-6
            except Exception as e: fail(case,'optimizer_or_path_failure',repr(e),method=method,**meta); continue
            try: age=evaluate(s,a.dt)
            except Exception as e: fail(case,'aging_evaluator_failure',repr(e),method=method,**meta); continue
            rows.append(dict(case=case,method=method,family=family,scenario=asdict(a),**meta,**m,**age,solver=info))
            paths.append(dict(case=case,method=method,family=family,power_kw=p.tolist(),soc=s.tolist(),prices=np.asarray(c).tolist(),dt=a.dt))
    seen=set()
    for i,r in enumerate(cohort):
        case=f'real_{i}'
        try:
            sid=r['sessionID']; start=parse(r['connectionTime']); end=parse(r['disconnectTime']); h=(end-start).total_seconds()/3600; e=float(r['kWhDelivered']); tz=ZoneInfo(r['timezone'])
            if not sid or sid in seen or not math.isfinite(e) or e<=0 or h<=0: raise ValueError('missing/duplicate ID or invalid energy/window')
            seen.add(sid); n=math.ceil(h/.25); local=start.astimezone(tz); clock=local.hour+local.minute/60+local.second/3600+np.arange(n)*h/n
            c=np.where((clock%24>=16)&(clock%24<21),.30,.15)
            flag=bool(r.get('doneChargingTime') and not start<=parse(r['doneChargingTime'])<=end)
        except Exception as ex: fail(case,'invalid_record',repr(ex)); continue
        for initial in cfg['initial_socs']:
            a=Scenario(n=n,dt=h/n,initial=initial,target=initial+.9*e/60)
            solve(f'{case}_soc{int(round(initial*100))}',a,c,'real',session_id=sid,timing_flag=flag)
    base=Scenario(); variants=[('baseline',base,'baseline'),('flat',base,'flat'),('late_cheap',base,'late')]
    variants += [(f'window_{h}h',replace(base,n=int(h*4)),'baseline') for h in [5,8,12]]
    variants += [(f'threshold_{x}',replace(base,reference_soc=x),'baseline') for x in [.6,.7,.8]]
    variants += [(f'soc_{x}_{y}',replace(base,initial=x,target=y),'baseline') for x,y in [(.2,.8),(.5,.8),(.3,.9)]]
    variants += [(f'resolution_{m}m',replace(base,n=int(720/m),dt=m/60),'baseline') for m in [60,30,15,5]]
    for name,a,mode in variants: solve(name,a,prices(a,mode),'sensitivity')
    for wp in cfg['power_weights']:
        for ws in cfg['soc_weights']:
            solve(f'weight_{wp}_{ws}',base,prices(base),'weights',[('weighted',wp,ws)],weight_power=wp,weight_soc=ws)
    aging=[]
    for p in paths:
        if p['case']=='baseline':
            for temp in [15,25,35]:
                for days in [0,365,1095]: aging.append(dict(method=p['method'],prior_days=days,**evaluate(p['soc'],p['dt'],prior_loss(days),temp)))
    timing=[]
    for minutes in cfg['timing_minutes']:
        a=replace(base,n=int(720/minutes),dt=minutes/60); c=prices(a)
        for method,wp,ws in METHODS[1:]:
            optimize(c,a,wp,ws) # unrecorded warm-up per resolution/method
            for repetition in range(cfg['timing_repeats']):
                start=time.perf_counter(); p,info=optimize(c,a,wp,ws); outer=time.perf_counter()-start
                m=metrics(p,c,a)
                if m['energy_residual_kwh']>=1e-6 or info['max_constraint_residual']>=1e-6: raise RuntimeError('timing solve failed feasibility')
                timing.append(dict(minutes=minutes,method=method,repetition=repetition+1,outer_seconds=outer,solver=info, cost_dollars=m['cost_dollars'],power_proxy=m['power_proxy'],high_soc_proxy=m['high_soc_proxy']))
    paired=[]
    for case in sorted({r['case'] for r in rows if r['family']=='real' and not r['timing_flag']}):
        d={r['method']:r for r in rows if r['case']==case}
        if all(m[0] in d for m in METHODS):
            a,b=d['cost_only'],d['combined']; paired.append(dict(case=case,initial=a['scenario']['initial'],**{k:b[k]-a[k] for k in ['cost_dollars','power_proxy','high_soc_proxy','calendar_increment_ppm']}))
    summaries=[]
    for initial in cfg['initial_socs']:
        group=[r for r in paired if r['initial']==initial]
        for k in ['cost_dollars','power_proxy','high_soc_proxy','calendar_increment_ppm']:
            vals=[r[k] for r in group]
            summaries.append(dict(initial=initial,metric=k,count=len(vals),median=float(np.median(vals)) if vals else None,q1=float(np.percentile(vals,25)) if vals else None,q3=float(np.percentile(vals,75)) if vals else None))
    inputs=[cfgpath,cohortpath,ROOT/'src/charging.py',ROOT/'src/aging.py',Path(__file__).resolve(),ROOT/'requirements.txt']
    manifest=dict(input_sha256={str(p.relative_to(ROOT)) if p.is_relative_to(ROOT) else str(p):sha(p) for p in inputs}, cohort_count=len(cohort),attempted_case_count=len(case_ids),successful_schedules=len(rows),trajectory_count=len(paths),failure_counts=dict(collections.Counter(f['category'] for f in failures)),paired_case_count=len(paired),aging_evaluations=len(aging),timing_runs=len(timing),python=platform.python_version(),platform=platform.platform(),processor=platform.processor(),machine=platform.machine(),cpu_count=os.cpu_count(),numpy=np.__version__,cvxpy=cvxpy.__version__,clarabel=clarabel.__version__, independent_human_review=False)
    for name,obj in [('metrics.json',rows),('trajectories.json',paths),('failures.json',failures),('paired_cases.json',paired),('paired_summary.json',summaries),('aging_sensitivity.json',aging),('timing.json',timing),('manifest.json',manifest)]: dump(out/name,obj)
    print(json.dumps(manifest,indent=2))
if __name__=='__main__': main()
