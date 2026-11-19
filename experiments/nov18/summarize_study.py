"""Audit saved trajectories and generate a readable result guide; no solves."""
from pathlib import Path
import json,hashlib
import numpy as np
ROOT=Path(__file__).resolve().parents[2];OUT=ROOT/'results/nov18'
rows=json.loads((OUT/'metrics.json').read_text());ts=json.loads((OUT/'trajectories.json').read_text())
lookup={(r['case'],r['method']):r for r in rows}
for t in ts:
    r=lookup[t['case'],t['method']];a=r['scenario'];p=np.array(t['power_kw']);s=np.array(t['soc']);dt=t['interval_hours']
    assert len(s)==len(p)+1
    assert np.max(np.abs(np.diff(s)-a['efficiency']*p*dt/a['capacity']))<1e-10
    assert abs(p.sum()*dt-r['grid_kwh'])<1e-7
    assert min(p)>-1e-6 and max(p)<a['maximum_power']+1e-6
    assert abs(s[0]-a['initial'])<1e-10 and abs(s[-1]-a['target'])<1e-8
    assert abs(np.mean((np.maximum(s[1:]-a['reference_soc'],0)/(1-a['reference_soc']))**2)-r['high_soc_proxy'])<1e-10
flat=next(t for t in ts if t['case']=='flat' and t['method']=='power_penalty')
assert np.max(np.abs(np.array(flat['power_kw'])-30/.9/12))<1e-5
for t in ts:
    if t['method']=='combined' and t['case'].startswith('real') and max(t['soc'])<.7:
        other=next(x for x in ts if x['case']==t['case'] and x['method']=='power_penalty')
        assert max(abs(np.array(t['power_kw'])-np.array(other['power_kw'])))<1e-4
summary=json.loads((OUT/'run_summary.json').read_text());assert summary['numerical_failures']==0
pairs=json.loads((OUT/'paired_clean_results.json').read_text())
cohort=json.loads((OUT/'cohort.json').read_text())
lines=['# Executed study: what to read tonight','',
'Generated November 18, 2026. Automated checks passed; human interpretation, independent model review and independent reproduction remain incomplete.','',
f"- {len(cohort)} recorded sessions; 236 successful schedules are simulated alternatives, not 236 independent observations.",
'- Five hypothetical SOC cases were analytically infeasible; none had its energy reduced. No numerical/evaluation failures were recorded.',
f'- All {len(ts)} saved power/SOC trajectories passed recomputed dynamics, energy, target and power-bound checks; flat-price uniform charging and inactive combined/power-only agreement passed.',
'- Calendar numbers are provisional model estimates, not measured lifetime improvement.',
'','## Clean paired real-session comparisons','',
'Change means combined minus cost-only on the same session and assumed initial SOC. Negative exposure change is a smaller score; positive cost premium is extra spending. Flagged original control is omitted here and retained in raw outputs.','',
'| Assumed starting SOC | Feasible clean paired cases | Median cost premium ($) | Median high-SOC score change | Median calendar change (ppm) |',
'|---|---:|---:|---:|---:|']
for initial in [.3,.6,.75]:
    p=[r for r in pairs if r['initial_soc']==initial]
    lines.append(f"| {initial:.0%} | {len(p)} | {np.median([r['cost_premium'] for r in p]):.6f} | {np.median([r['high_soc_change'] for r in p]):.6f} | {np.median([r['calendar_change_ppm'] for r in p]):.6f} |")
lines+=['','## Synthetic sensitivity: cost versus exposure','',
'Each row keeps four methods; the table selects cost-only and combined to show the tradeoff. Synthetic window/price variants are hypothetical, separate from real sessions. Threshold variants report different score definitions and should not be ranked by raw score across thresholds.','',
'| Case | Cost-only cost ($) | Combined cost ($) | Cost-only exposure | Combined exposure | Combined total wall time (s) |',
'|---|---:|---:|---:|---:|---:|']
for case in dict.fromkeys(r['case'] for r in rows if r.get('family')=='sensitivity'):
    a=lookup[case,'cost_only'];b=lookup[case,'combined']
    lines.append(f"| {case} | {a['cost_dollars']:.4f} | {b['cost_dollars']:.4f} | {a['high_soc_proxy']:.6f} | {b['high_soc_proxy']:.6f} | {b['total_wall_seconds']:.5f} |")
weights=[r for r in rows if r.get('family')=='weights']
nd=[]
for r in weights:
    fields=['cost_dollars','power_proxy','high_soc_proxy']
    if not any(all(q[k]<=r[k]+1e-9 for k in fields) and any(q[k]<r[k]-1e-9 for k in fields) for q in weights):nd.append(dict(weight_power=r['weight_power'],weight_soc=r['weight_soc'],**{k:r[k] for k in fields}))
(OUT/'nondominated_weight_cases.json').write_text(json.dumps(nd,indent=2)+'\n')
lines+=['','## Read these artifacts in order','',
'1. `representative_soc60.png`: S2 at assumed 60% arrival. Explain when each method charges and waits.',
'2. `paired_tradeoffs.png`: every clean paired case, including zero changes. These are assumed SOC cases on recorded windows under synthetic prices.',
'3. `weight_tradeoffs.png` and `nondominated_weight_cases.json`: expense, concentration and exposure can compete; no single unexplained health score.',
'4. `exclusions.json`: five infeasible SOC assumptions, kept visible rather than repaired.',
'5. `aging_sensitivity.json`: 36 conditional evaluations (four fixed schedules, three current temperatures, three prior ages). Prehistory stays at 25 C/50% SOC; no new schedules are optimized here.',
'','## Remaining interpretation limits','',
'The cohort is a small, deliberately diverse first-page sample, not a population estimate. SOC/capacity/charger/chemistry/temperature and tariffs are assumed. Recorded departure is known in retrospect. Single-run timing is descriptive; hardware noise can outweigh small differences. Runtime includes different problem sizes and cost-only has two stages. Time-resolution changes also change the end-of-slot proxy approximation. No automated check establishes real battery-health improvement.']
(OUT/'findings.md').write_text('\n'.join(lines)+'\n')
(OUT/'additional_checks.json').write_text(json.dumps(dict(trajectory_count=len(ts),checks='PASS: reconstructed dynamics/energy/targets/power bounds/exposure; flat uniform case; inactive power/combined trajectories; zero numerical failures',independent_human_review=False),indent=2)+'\n')
print('\n'.join(lines[:17]))
