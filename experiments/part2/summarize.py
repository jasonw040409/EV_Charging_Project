"""Generate a count-driven summary of an existing Part 2 pack."""
import json,sys
from pathlib import Path
import numpy as np
p=Path(sys.argv[1]); read=lambda name:json.loads((p/name).read_text())
m=read('manifest.json'); rows=read('metrics.json'); paired=read('paired_summary.json'); timing=read('timing.json'); failures=read('failures.json')
lines=['# Automated experiment summary','',f"Sessions: {m['cohort_count']}; attempted cases: {m['attempted_case_count']}; schedules and saved paths: {len(rows)}; complete unflagged paired cases: {m['paired_case_count']}; post-evaluations: {m['aging_evaluations']}.",f"Failures/exclusions: {m['failure_counts'] or 'none'}. Flagged timing records remain in metrics and are excluded from paired summaries.",'','## Paired combined minus cost-only','', '| Start SOC | Metric | Count | Median | Q1 | Q3 |','|---:|---|---:|---:|---:|---:|']
for x in paired:
    fmt=lambda v:'—' if v is None else f'{v:.6g}'
    lines.append(f"| {x['initial']:.0%} | {x['metric']} | {x['count']} | {fmt(x['median'])} | {fmt(x['q1'])} | {fmt(x['q3'])} |")
lines+=['','## Repeated solve timings','', 'Each cell is the median outer call time in seconds; see timing.json for individual runs and scores.','', '| Resolution (min) | Method | Runs | Median seconds |','|---:|---|---:|---:|']
for minutes in sorted({x['minutes'] for x in timing}, reverse=True):
    for method in dict.fromkeys(x['method'] for x in timing):
        v=[x['outer_seconds'] for x in timing if x['minutes']==minutes and x['method']==method]
        if v: lines.append(f'| {minutes} | {method} | {len(v)} | {np.median(v):.6f} |')
lines+=['','Synthetic prices and assumed SOC; no measured health claim. Timings include construction and solve, not aging or file output. Cost-only has two solves; solver-reported time is its final stage only.','']
(p/'summary.md').write_text('\n'.join(lines))
print(f"Wrote {p/'summary.md'}; {len(failures)} exclusions/failures, {len(timing)} timing observations")
