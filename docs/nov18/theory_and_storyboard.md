# Theory notes and full presentation/report structure

Draft prepared automatically November 18. Human source review, derivations and rehearsal remain outstanding.

## Mathematical explanation for the reviewer

Power p_t is grid kW, SOC s_t a fraction, dt hours. Dynamics: s_(t+1)=s_t+eta*p_t*dt/E. Fixed departure energy and nonnegative power mean SOC is monotone. All compared methods deliver identical energy within the same window.

Normalize expense by C_ref=max(abs(immediate expense),1). Penalize D_P=sum((p/Pmax)^2)/N and D_S=sum((max(s_end-.7,0)/.3)^2)/N. With z>=s_end-.7 and z>=0, the weighted objective is quadratic and constraints affine. Its Hessian in (p,z) is block diagonal: 2*lambda_P/(N*Pmax^2) times identity and 2*lambda_S/(N*(1-s_ref)^2) times identity. Nonnegative weights imply positive semidefiniteness; lambda_P>0 gives a unique power schedule. When weights vanish, auxiliary z need not equal actual excess; the reporting function recalculates excess directly.

For the affine-constrained quadratic objective 0.5*x'H*x+f'x, KKT conditions are primal feasibility, nonnegative inequality multipliers, Hx+f+A'mu+B'nu=0, and complementarity mu_i(Ax-b)_i=0. These are symbolic conditions, not a numerical dual-residual audit. Independently derive signs and active constraints before including in the report. Cost-only uses a second minimum-power-concentration solve within $1e-8 of optimum expense.

Under flat prices and only the quadratic power penalty, equal charging power minimizes sum(p_t^2) for a fixed sum of powers, provided it obeys the cap. Expected synthetic uniform grid power is (30/.9)/12=2.7777778 kW. The existing test checks this. The calendar model's squared accumulated-loss state grows by integral(k(T,SOC)^2 dt_seconds); it is not restarted each interval. Refer to the existing model specification for source verification status and units.

## 15–20-minute presentation storyboard — retain every substantive component

1. Motivation and question (1 min): equal energy by departure; expense versus explicit stress preferences.
2. What is observed and what is assumed (1.5 min): real timestamps/energy, unknown battery SOC/chemistry; retrospective departure knowledge.
3. Physical formulation (2 min): power/SOC dynamics, fixed energy, cap and feasibility.
4. Four scheduling models (1.5 min): immediate, cost-only tie-break, power penalty, combined.
5. Convexity and solution method (1.5 min): quadratic objective, affine constraints, analytic uniform check; primary solver and residuals.
6. Published evaluator and history (1.5 min): Naumann calendar-only, units, prior history, whole-window exposure; scope and source limits.
7. Synthetic worked example (1.5 min): power/SOC/price curves, same energy, actual expense differences.
8. Real data selection and SOC sensitivity (2 min): original controls, diverse additions, 30/60/75% assumed starts, quality flags and infeasibility.
9. Ablations and weight tradeoffs (1.5 min): separate scores, expense premium, zero-effect cases, avoid unexplained total-health score.
10. Flexibility/price/threshold/initial-target/resolution results (2 min): small multiples or compact table; runtime and feasibility.
11. Temperature/history conditional sensitivity (1 min): unchanged schedules, provisional estimates; model uncertainty and unmeasured health.
12. Findings, limits, next steps and actual member contributions (1.5 min): no measured life benefit claim; post-presentation larger sample and final deliverables.

Target about 18.5 minutes before questions. Use only reviewed numbers. A slide storyboard is not a finished slide deck; build slides Nov 21 and rehearse Nov 22–23.

## Self-contained 8–12-page report outline

Abstract; motivation and contribution; related optimization and battery-aging work with verified sources; mathematical formulation and assumptions; convexity/KKT and solution method; implementation and analytic verification; data access/selection/exclusions/assumed inputs; synthetic and application-data results; ablations/weights/sensitivities/runtime; interpretation and model limits; future work; actual member contributions; references. Retain figures and commands linked to frozen outputs. Draft prose from results, not from hoped-for conclusions.

Post-presentation: 50–100-session expansion, broader sensitivity, optional independently verified second evaluator and model-dependence discussion, full report/software audit and submission December 13 at 11:59 p.m. Do not claim a second model is implemented or literature review complete merely because it appears in this outline.

## Presentation storyboard — full 15–20 minute presentation

These are slide contents and speaking prompts, not a finished deck. Build the final slides Nov 21 after review; leave rehearsal to people.

| Slide / time | Content to show | Explain aloud |
|---|---|---|
| 1 / 1 min | Problem and research question | A car needs energy by departure. Can timing/power preferences reduce modeled exposure, and at what cost? |
| 2 / 1 min | Actual versus assumed fields | Data provides windows/energy, not initial SOC, battery chemistry or tariffs. |
| 3 / 2 min | Dynamics and equal-energy constraints | Power is delivery speed; energy is the amount. All methods satisfy the same requirement. |
| 4 / 2 min | Four methods and two proxy penalties | 70% is a chosen soft threshold; 90% is the hard cap. Explain cost-only tie-break. |
| 5 / 2 min | Published evaluator and history | Calendar only, specific LFP cell; source verification and limitations; no health/lifetime claims. |
| 6 / 1.5 min | Convexity, solver and analytic verification | Nonlinear quadratic objective can still be convex. Flat-price uniform charging is a checkable answer. |
| 7 / 2 min | Overnight synthetic example and weight tradeoffs | Compare costs, two scores separately and peaks; effects need not all improve together. |
| 8 / 2 min | Frozen cohort, SOC sensitivity, inactive controls and failures | Show observed windows, assumed SOC labels, selection ledger and infeasible counts; 15 sessions are not 160 observations. |
| 9 / 2 min | Real representative plot and paired comparisons | Read exact findings from `results/nov18/findings.md`; zero cost premiums and zero-effect cases are valid outcomes. |
| 10 / 1.5 min | Flexibility, prices, thresholds and resolution/runtime | Explain one counterexample or tight-window case, show computational comparison and discretization limits. |
| 11 / 1 min | Conclusions, limitations, remaining work and actual contributions | Say what was verified, what is only conditional, and what will be completed by Dec 13. |

Target approximately 18 minutes; trim spoken detail to fit, not study content. Put the full temperature/history table, assumptions, solver tolerances and extra sensitivity figures in backup slides. Never invent teammate contributions; fill with actual work completed before presenting.

## Final report structure — 8–12 pages

1. Abstract: question, methods, actual evidence and limits (write last).
2. Introduction/background: charging problem, relevance and application contribution.
3. Related theory/practice: verified source/model comparison with chemistry/input/reproducibility tradeoffs; distinguish abstract-only evidence from full text.
4. Technical model: units, constraints, convex surrogate objective, gradients/Hessian/KKT, tie-break, published calendar equations/history, solver.
5. Implementation and verification: analytic flat case, feasibility/history tests, residuals, saved trajectories and exact reproduction commands.
6. Data/experiments: observed versus assumed fields, cohort selection/exclusions, retrospective departure, four strategies, ablation and weights, SOC/window/price/threshold/time-resolution sensitivity, runtime.
7. Results and discussion: paired session differences, representative plots, nondominated tradeoffs, inactive-term controls, infeasible cases; broader 50–100-session expansion and temperature/history analysis after presentation.
8. Limitations/conclusions/future work: no measured health validation; optional second-model comparison evaluates robustness, not truth.
9. Actual member contributions and references.

Evidence map: data selection -> `data_provenance.json`, `selection_ledger.json`, `cohort.json`; numerical checks -> baseline log and `additional_checks.json`; comparisons -> `metrics.json`, `paired_clean_results.json`, `findings.md`; detailed paths -> `trajectories.json`; failures -> `exclusions.json`; post-evaluation history/temperature -> `aging_sensitivity.json`. Every filename in this map is under `results/nov18/`.
