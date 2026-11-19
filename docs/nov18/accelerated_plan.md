# Accelerated recovery plan — November 18, 2026

Presentation remains November 24. This supplements the original plan without deleting or marking unfinished content complete. November 14–17 milestones slipped: neither teammate has started independent review. Only the data/interpretation member is available tonight. Do not count automated execution as independent human review.

## Working split: 65% automated preparation, 35% manual effort

Interpret the requested 30–40% manual share as **estimated effort across the remaining work**, not file count or a claim about measured productivity. Planning budget: 20 equivalent work-hours of preparation, 13 allocated to automation and 7 to people. Machine runtime is not comparable to human hours; these are estimates to keep people focused on understanding and checking. Track actual time and rebalance at the November 20 checkpoint. Manual tasks remain visibly blank until a person completes them.

| Work package | Automated allocation | Manual allocation | Completion evidence |
|---|---:|---:|---|
| Data access, screening, cohort and provenance | 2 h | 1 h | New snapshot, selection ledger; human checks three originals |
| Model/theory explanation and implementation verification | 2 h | 1.5 h | Existing model specification, tests, theory worksheet; independent source/units sign-off |
| Four methods, SOC study, weights, sensitivities and figures | 4 h | 1 h | Runnable study and outputs; human reads paired results and failure cases |
| Interpretation and report preparation | 2 h | 1 h | Evidence-led notes and report outline; human writes conclusions in own words |
| Presentation structure and rehearsal | 2 h | 2 h | Slide storyboard; people build/review delivery and rehearse |
| Final package and reproducibility | 1 h | .5 h | Commands/package audit; human checks reproduction/submission checklist |
| **Total** | **13 h (65%)** | **7 h (35%)** | Effort estimates, not completed-time claims |

Tonight, concentrate your manual effort on the first 90 minutes of `manual_workbook.md`. Do not try to become the battery-model reviewer in one evening. New calendar estimates remain provisional while that review is missing. The original model, inputs and outputs are preserved; the new runner imports existing code and writes separate outputs.

## All original content retained

| Planned content | Accelerated location / date |
|---|---|
| Source-verified battery model, chemistry/units/range/history/limitations | Existing specification retained; independent reviewer signs off Nov 19 |
| Convex formulation, derivatives/Hessian, KKT and analytic checks | Theory worksheet tonight; independent derivation Nov 19–20 |
| Immediate, cost-only, power-only and combined comparison | New runner, tonight; same energy and physical constraints |
| Both uncalibrated power and high-SOC scores | Retained, independently reported |
| 10–20 real sessions, actual windows and source assumptions | 15-case cohort tonight, with screening and anomaly ledger |
| Starting SOC sensitivity and inactive controls | 30/60/75% scenarios, original five controls retained |
| Weight tradeoffs / model ablation / nondominated interpretation | 12 weight pairs and comparison figures tonight; human interpretation Nov 19 |
| Flexibility, initial/target SOC, price timing, high-SOC threshold sensitivity | Separate synthetic cases tonight, labeled as synthetic |
| Runtime and 60/30/15/5-minute resolution comparison | Tonight; wall and solver times retained; repeated timing if needed Nov 19 |
| Independent reproduction, source checks, failures and limitations | Teammates Nov 19–20; not replaced by automated assertions |
| Nov 20 verified-results checkpoint | Retained; freeze only evidence that passes review |
| Nov 21–23 slides and rehearsal, Nov 24 presentation | Retained, using storyboard and reviewed results |
| Post-presentation 50–100 sessions and paired summaries | Nov 25–29; same frozen selection rules, traceable larger cohort |
| Broader temperature/history/threshold/resolution sensitivity | First small grid tonight, review/expand Nov 30–Dec 4 |
| Optional second published evaluator / cycle-model feasibility | Retain original decision gate Nov 30–Dec 4: requires verified equations/domain/history; optional in original plan, not silently dropped |
| 8–12-page report, actual contributions, citations and reproducible software | Draft structure tonight, writing Dec 5–8, audit Dec 9–11, proofread Dec 12 |
| Final report and software submission | **December 13, 11:59 p.m.**, target earlier that day |

No extra forecasting, V2G, fleet coordination or duplicate optimization framework is added. These were already outside the original scope.

## Recovery calendar and owners

**Tonight, Nov 18:** automation prepares the separate study, trajectory outputs, exclusions, figures, checks and handoff. You complete the first workbook tasks and record questions. No need to wait for absent teammates to perform reversible exploratory runs.

**Nov 19:** model member independently checks source equations, percent/fraction conversion, calendar history and transfer limits; implementation member reproduces commands and inspects trajectories/residuals and the three smoke cases. You check cohort IDs/times, read the paired comparisons and draft captions. These are proposed assignments, not acknowledgments from teammates. If they remain absent, log independent review as missing; continue your own checks without calling them independent.

**Nov 20:** close review issues, verify all planned comparison families, freeze plots and tables for presentation. Retain failed/infeasible cases. If review is incomplete, label results provisional explicitly; do not claim the checkpoint passed merely because a script ran. Escalate the staffing/schedule issue to the team using the prepared update.

**Nov 21:** build full slide draft from storyboard; **Nov 22:** timed 15–20-minute rehearsal; **Nov 23:** corrections and second run; **Nov 24:** present. All members should understand the assumptions and contribute to delivery once available.

**Nov 25–Dec 13:** retain the original larger sample, deeper sensitivity, model-dependence decision, report, reproduction and submission tasks above. Do not relabel tonight's pilot as the final study.

## Reproduction and outputs

From repository root:

```sh
.venv/bin/python -m unittest discover -s tests -v
.venv/bin/python experiments/nov18/run_study.py
```

The second command uses frozen inputs and writes only `results/nov18/`. It does not fetch data. Outputs include selected raw cohort, candidate screening ledger, provenance, metric rows, complete power/SOC/price trajectories, exclusions/failures, paired clean comparisons, figures and a run summary. The initial public-demo-token download is separate; no personal credential is needed for replay. Dates/access are a snapshot, not guaranteed ongoing availability.

Selection is fixed before optimization: retain the original five, screen a bounded first-page snapshot of 100 records, exclude invalid fields/time-order flags/infeasible baseline assumptions for additions, then choose ten additions by chronological round-robin across duration (≤4, 4–8, >8 h) and energy (≤5, 5–10, >10 kWh) bins. This differs from the Nov 14 proposed date-window query; the bounded snapshot is an explicit availability choice, not an outcome-based selection. All candidates and reasons are logged. The flagged original control remains diagnostic; clean paired plots exclude it. This cohort is not a random or representative population sample.

Starting SOC is explicitly set along with the derived target. Infeasible scenarios are logged, never repaired by reducing recorded energy. Calendar temperature/history sensitivity is post-evaluation of unchanged schedules; it does not show optimization under a calibrated damage objective. The 365-day history remains at 25°C/50% SOC when evaluating alternate current temperatures, as labeled in the output.
