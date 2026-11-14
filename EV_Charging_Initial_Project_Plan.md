# Battery-Aware Nonlinear Optimization of EV Charging Schedules

Evidence-based implementation plan, November 14, 2026. Three undergraduate members; names to be filled in by the team. Presentation **November 24**. Final report and software **December 13, 2026 at 11:59 p.m.** Preserve the November 20 results checkpoint and November 21–23 slides/rehearsal period.

## Current evidence and decisions

The repository started empty. The supplied course PDF and provisional plan were read; the original provisional plan is preserved in `docs/initial_plan_supplied.md`. Neither `EV_Charging_Background_Research.md` nor `background_study.md` was found. Their equations are not prerequisites for this implementation.

Completed and executed: one synthetic 48-slot overnight example; all four strategies; one primary CVXPY/CLARABEL stack; published Naumann calendar-capacity evaluator verified from the author's full dissertation and cross-checked with official code; seven analytic/physical/history verification tests; 12 weight combinations; price/power/SOC plot; five original ACN records retrieved through the official tutorial's public demo credential; 20 retrospective pilot schedules on those windows. Saved outputs are under `results/` and `data/`. These are preliminary results, not the finished course project.

Immediate / cost-only / power-penalty / combined example costs are $9.0933 / $3.3333 / $3.8263 / $4.2707. Each supplies 30 battery kWh. The combined schedule reduces the chosen exposure metrics and conditional calendar estimate here but costs $0.9374 more than cost-only. Its peak exceeds power-only's peak. None of these outcomes establishes improved real battery health.

**Model revision:** use two explicitly uncalibrated optimization surrogates, then evaluate with the cell-specific published calendar model. Retain prior calendar damage; do not reset aging every slot. Treat a cycle model as a bounded extension requiring source/units/history verification, not as a last-minute prerequisite to slides. Preserve substantive comparisons across four scheduling models, ablations, weight tradeoffs and application data. A second published evaluator would test model dependence, not validate lifetime improvements.

## Member ownership and near-term acceptance criteria

| Member | Primary responsibility | Next concrete work, November 14–17 | Independent check |
|---|---|---|---|
| Member 1 — modeling/theory | Source audit, equations, assumptions, report methods | Read dissertation pp. 69–75, independently calculate one constant-stress loss; verify convexity, gradients/Hessian, KKT; compare original paper if obtained; audit applicability limits | Review Member 2's SOC/energy units and tie-break implementation |
| Member 2 — implementation/experiments | Solver, reproducibility, plots and weight study | Reproduce README commands; inspect residuals; add flat, barely feasible and altered-price cases; compare 60/30/15/5-minute grids on a fixed horizon | Have Member 1 review formulas and Member 3 replay commands in a clean environment |
| Member 3 — data/evaluation/presentation coordination | ACN provenance, cleaning, pilot expansion, narrative | Review five raw records and one timestamp anomaly; expand to 10–20 documented sessions; retain observed windows, distinguish delivered/requested energy; log assumptions and exclusions | Check solver outputs against original connection windows and energy, review Member 1's limitations language |

No member should claim authorship of work they have not reviewed. The final contributions section must state actual completed contributions, not just these assignments. All three members own slides, rehearsal, final review and answering questions. No delegated agents were used in this implementation.

## Calendar and deliverables

| Date | Deliverable and owner |
|---|---|
| Nov 14 | Working core and five-record access proof now present; each member reproduces and chooses their role |
| Nov 15 | Member 1 completes independent source/units audit; Member 3 confirms repeatable access and sample criteria; Member 2 reviews implementation |
| Nov 16–17 | Freeze 10–20-session pilot with assumptions/exclusions; theory draft; same four policies on every feasible instance |
| Nov 18–19 | All members inspect tradeoffs; Member 2 runs focused flexibility/price and threshold sensitivity; Member 3 writes paired per-session summaries; Member 1 checks interpretation |
| **Nov 20** | **Results checkpoint:** verified table and plots; source citations; analytic checks; real-session provenance; controlled weight/ablation comparisons; recorded unresolved limitations |
| **Nov 21–23** | **Slides and rehearsal:** Nov 21 draft, Nov 22 timed full-team run, Nov 23 corrections and final rehearsal. Target the handout's 15–20 minutes; all members participate |
| **Nov 24** | **Presentation:** show formulation, evidence, feasibility, data assumptions, costs/stresses, and limits; collect feedback |
| Nov 25–29 | Address feedback, expand to 50–100 sessions if access/cleaning support it; add paired summaries and anomaly-exclusion sensitivity |
| Nov 30–Dec 4 | Focused temperature/history/SOC-threshold and time-resolution sensitivity; consider a second source-verified evaluator only if partial-cycle/history treatment is defensible |
| Dec 5–8 | Complete 8–12 page self-contained report with actual contributions, related work, methods, results, comparisons, limitations and references |
| Dec 9–11 | Fresh-environment reproduction, output consistency, report figure/table audit and package freeze |
| Dec 12 | Final team proofread; prepare report PDF and software package; verify submission recipients and contribution statement |
| **Dec 13, 11:59 p.m.** | **Submit report and software** per course handout; target submission earlier that day |

The handout asks for the report PDF via Canvas and software by email to the TA with group members copied. These are submission requirements for the team, not authorization for this assistant to send messages or submit files.

## Minimum substantive experiment set

1. Four strategies with identical physical constraints and delivered energy, independently evaluated on cost, both surrogates and calendar loss. Include peak power, feasibility residuals, status, runtime and tie-break rule.
2. Weight sweep: keep the current modest grid; report cost premiums against optimized cost-only, both stress scores separately, and nondominated points. Explain why penalties are dimensionless and uncalibrated.
3. Application-data comparison: known disconnection retrospectively, actual timestamps; retain observed delivered energy; disclose capacity/initial SOC/chemistry/temperature/charger/tariff assumptions. Report every exclusion rather than clipping energy.
4. Focused sensitivity before Nov 20: flat prices, tight window, price timing and SOC threshold. Broader temperature/history and time-resolution tests after presentation. Vary age through accumulated component-specific damage, not a per-slot clock reset.
5. Compare optimization difficulty and computational cost as well as schedule scores, satisfying the handout's model-comparison requirement. If two published aging models are compared, separate source verification from empirical validation and label conflicting rankings.

## Scope and fallback rules

Keep one vehicle per instance, continuous unidirectional charging, fixed temperature/efficiency, known prices/departure, one primary solver. Exclude forecasting, fleet coupling, V2G, learned degradation, thermal/electrochemical simulation and duplicate AMPL interfaces.

The calendar evaluator's credible role is conditional SOC/time sensitivity; it cannot rank charging-rate damage. Do not turn its small numerical differences into measured battery-life claims. If cycle-law verification is unfinished, keep the explicit calendar-only limitation and the substantive surrogate-model comparison. If demo access becomes unavailable, use frozen original records for reproducibility and documented alternatives for expansion; do not fabricate data. If the five-record sample remains small, prioritize complete traceable analysis over sample-count claims and discuss final application-data expectations with the instructor.

Known pending tasks: independent human source/code review, broader session sampling, focused sensitivity and plots of weight tradeoffs, numeric KKT/dual audit if included in the report, larger-data analysis, slides/rehearsal, and final report/submission. None is marked completed by this plan.
