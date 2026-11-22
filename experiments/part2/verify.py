"""Audit saved pack against equations and the frozen November 18 outputs."""
import hashlib,json,sys
from pathlib import Path
import numpy as np
ROOT=Path(__file__).resolve().parents[2]; sys.path.insert(0,str(ROOT/'src'))
from aging import evaluate
from charging import Scenario
out=Path(sys.argv[1]); read=lambda p:json.loads(p.read_text())
rows=read(out/'metrics.json'); paths=read(out/'trajectories.json'); failures=read(out/'failures.json'); old=read(ROOT/'results/nov18/metrics.json'); oldage=read(ROOT/'results/nov18/aging_sensitivity.json'); age=read(out/'aging_sensitivity.json')
lookup={(r['case'],r['method']):r for r in rows}; oldmap={(r['case'],r['method']):r for r in old}; assert set(lookup)==set(oldmap)
fields=['cost_dollars','power_proxy','high_soc_proxy','grid_kwh','battery_kwh','peak_kw','departure_soc','calendar_increment_ppm']
diffs={f:max(abs(r[f]-oldmap[k][f]) for k,r in lookup.items()) for f in fields}
assert all(v<1e-5 for v in diffs.values()), diffs
assert len(paths)==len(rows)
max_dynamics=0.; smoke={}; pathmap={(p['case'],p['method']):p for p in paths}
for p in paths:
    r=lookup[p['case'],p['method']]; a=Scenario(**r['scenario']); power=np.array(p['power_kw']); soc=np.array(p['soc']); c=np.array(p['prices'])
    assert len(power)==len(c)==a.n and len(soc)==a.n+1
    reconstructed=a.initial+np.r_[0,np.cumsum(power*a.efficiency*a.dt/a.capacity)]
    max_dynamics=max(max_dynamics,float(np.max(np.abs(soc-reconstructed))))
    assert np.max(np.abs(soc-reconstructed))<1e-12 and abs(soc[-1]-a.target)<1e-8
    assert abs(sum(power)*a.dt-a.grid_energy)<1e-6 and min(power)>-1e-6 and max(power)<a.maximum_power+1e-6
    assert abs(c@power*a.dt-r['cost_dollars'])<1e-8
    assert abs(evaluate(soc,a.dt)['calendar_increment_ppm']-r['calendar_increment_ppm'])<1e-8
for case in ['real_1_soc60','real_2_soc60','flat']:
    smoke[case]=[dict(method=m,intervals=len(pathmap[case,m]['power_kw']),soc_boundaries=len(pathmap[case,m]['soc']),initial=lookup[case,m]['scenario']['initial'],target=lookup[case,m]['scenario']['target'],grid_kwh=lookup[case,m]['grid_kwh'],max_residual=lookup[case,m]['energy_residual_kwh']) for m in ['immediate','cost_only','power_penalty','combined']]
assert any(f['case']=='real_1_soc75' and f['category']=='infeasible_assumed_scenario' for f in failures)
active_diff=float(np.max(np.abs(np.array(pathmap['real_1_soc60','power_penalty']['power_kw'])-np.array(pathmap['real_1_soc60','combined']['power_kw']))))
inactive_diff=float(np.max(np.abs(np.array(pathmap['real_2_soc60','power_penalty']['power_kw'])-np.array(pathmap['real_2_soc60','combined']['power_kw']))))
assert active_diff>1e-3 and inactive_diff<1e-5
flat=pathmap['flat','cost_only']['power_kw']; assert np.max(np.abs(np.array(flat)-np.mean(flat)))<1e-5
assert len(age)==len(oldage) and all(abs(x['calendar_increment_ppm']-y['calendar_increment_ppm'])<1e-5 for x,y in zip(age,oldage))
preserved=read(ROOT/'docs/part2/preserved_files_sha256.json'); changed=[p for p,h in preserved.items() if not (ROOT/p).is_file() or hashlib.sha256((ROOT/p).read_bytes()).hexdigest()!=h]; assert not changed,changed
result=dict(status='PASS',baseline_metric_rows_compared=len(rows),max_absolute_metric_differences=diffs,trajectories_checked=len(paths),max_soc_dynamics_error=max_dynamics,aging_sensitivity_compared=len(age),smoke_cases=smoke,active_power_difference_kw=active_diff,inactive_power_difference_kw=inactive_diff,smoke_infeasible=[f for f in failures if f['case']=='real_1_soc75'],preserved_file_count=len(preserved),changed_preserved_files=changed,independent_human_review=False)
(out/'verification.json').write_text(json.dumps(result,indent=2)+'\n'); print(json.dumps(result,indent=2))
