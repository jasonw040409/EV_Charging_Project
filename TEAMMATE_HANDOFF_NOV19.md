# Start here: CSE 543T EV charging project

**Handoff date: November 19, 2026. Presentation: November 24. Final report/software: December 13 at 11:59 p.m.**

Audience: two teammates joining without prior project knowledge. No previous chat is required. The data/interpretation member has worked with Codex to prepare the prototype, experiments and explanations. Automated work is preparation, not independent human verification. This file explains what exists, what remains, your first actions and how to know whether you understand it. Reading alone cannot guarantee understanding: use the checks and evidence-based review below.

## 1. Your first actions — do these before changing anything

| Time | Both teammates | Model/theory owner (M) | Implementation/verification owner (I) |
|---|---|---|---|
| First 15 minutes | Read sections 2–5 of this file. Open the two figures linked below. Know the distinction between recorded data, assumptions and simulated schedules. | Identify the objectives and hard constraints. | Locate the data snapshot, runner and saved summary. |
| Next 30 minutes | Read your role checklist in section 10. Record questions, not guesses. | Read `docs/model_specification.md`, then `src/aging.py` and `src/charging.py`. | Check that all files exist, then create the isolated reproduction copy in section 9. |
| Next 45–60 minutes | Complete one small check and share the evidence with the team. | Calculate S2's derived SOC and one constant-stress calendar-loss example independently; begin the original-source check. | Install dependencies in the copy, run tests and reproduce the study; check counts and three smoke cases. |
| End of first work block | Send the team: what you checked, exact evidence, issues, next action and expected completion time. | Start a model-review log; do not sign off merely because code runs. | Start a reproduction log; do not sign off merely because output files exist. |

First figures: [overnight synthetic example](results/schedules.png), [S2 at assumed 60% arrival](results/nov18/representative_soc60.png).

**Do not rerun the README's baseline scripts in the shared repository to start.** They overwrite saved baseline outputs. Use the isolated copy below. Do not launch the 50-session expansion before confirming the core and freezing sampling rules.

## 2. Project in ordinary language

A car is plugged in for a known time and needs a fixed amount of energy before leaving. Charging immediately is simple, but electricity may be cheaper later. Charging slowly spreads power; charging late can reduce how long the battery sits at a high charge. Those preferences can conflict.

We built a deterministic, single-vehicle charging scheduler to study these tradeoffs. We compare four scheduling policies using identical physical constraints and energy delivery. We then calculate cost, two explicitly uncalibrated stress scores and a published **calendar-aging-only** estimate. We are applying nonlinear optimization using an existing solver, not inventing a new optimization algorithm or proving battery-life improvement.

Important vocabulary:

| Term | Meaning |
|---|---|
| Power, kW | How quickly electricity is delivered. 2 kW for 3 hours delivers 6 kWh. |
| Energy, kWh | Amount delivered or stored. Grid energy and battery energy differ because of losses. |
| SOC, state of charge | How full the battery is, as a fraction or percentage. It is not battery health. |
| Usable capacity | Energy a full usable battery can hold; assumed 60 kWh here. |
| Objective / penalty | A preference minimized by the optimizer. It can be traded against other preferences. |
| Hard constraint | A rule every acceptable schedule must satisfy. |
| Feasible / infeasible | Whether a schedule can satisfy every hard rule at once. |
| Calendar aging | Capacity loss associated with time/SOC/temperature, including idle time. Not all degradation. |
| Proxy / surrogate | A deliberately simple score expressing a preference, not a calibrated damage measurement. |
| Retrospective | We know actual departure afterward and use it in simulation; no online departure predictor is implemented. |
| Residual | Numerical mismatch from a required equality or bound; near-zero is expected. |
| Ablation | Remove one objective term to see what changes. Our cost-only/power-only/combined comparison does this. |
| Nondominated | No other tested schedule is as good on every chosen metric and strictly better on at least one. Not a guarantee of the entire Pareto frontier. |

The correct central claim is: **we study conditional scheduling tradeoffs under disclosed assumptions using recorded session windows and energy requirements.**

## 3. Course requirements versus team choices

The handout is extracted in `docs/course_requirements_extracted.txt`. It requires a **15–20-minute team presentation**; additional presentation details were to be announced. Our confirmed date is November 24. The handout lists general grading criteria: motivation/contribution/applicability, technical soundness/correctness/implementation effort, and organization/clarity/references/results analysis/insights.

For application projects it requires: define a problem; survey existing optimization models and their pros/cons; develop a model; solve with an existing solver; verify quality using application data. At least one additional study is required. Our chosen route is **model comparison covering optimization difficulty, computational cost and solution quality**. Merely counting solver runs is not enough.

The final report is **8–12 pages**, self-contained, letter-size/single-spaced, with references and actual member contributions, plus software and reproduction instructions. The handout specifies report PDF via Canvas and software email to the TA with group members copied. Confirm any later instructor announcements yourselves. No submission/message has been made by automation.

The handout does not prescribe a slide count, 50 sessions, a live demo, equal speaking times or our internal checkpoints. Those are team planning choices. See `docs/nov18/nov22_execution_target.md` for the newest schedule; older plans are historical context where dates differ.

## 4. What is complete, and what is not

The following are **saved executed results**, not future promises:

| Item | Evidence / status |
|---|---|
| Runnable core and four policies | `src/charging.py`; CVXPY + CLARABEL |
| Calendar-only evaluator | `src/aging.py`; prior source audit in `docs/model_specification.md` |
| Original worked example and five-session pilot | `results/comparison.*`, `results/schedules.png`, `results/real_session_pilot.json` |
| Frozen 100-record candidate snapshot | `data/nov18/acn_candidate_snapshot.json`; not 100 selected evaluation sessions |
| Expanded pilot cohort | 15 original real-session records in `results/nov18/cohort.json` |
| Real-session study | 15 sessions × 3 assumed starts = 45 scenarios; 5 infeasible; 40 feasible × 4 policies = **160 schedules** |
| Synthetic sensitivity | 16 named cases × 4 policies = **64 schedules**; some repeat baseline settings intentionally |
| Weight study | **12 schedules**, one per weight pair |
| Total | **236 successful schedules**, with **224 complete trajectories** (160+64); the 12 weight results have aggregate metrics only |
| Temperature/history post-evaluation | 4 fixed schedules × 3 temperatures × 3 prior ages = **36 estimates**, not 36 new schedules |
| Existing automated tests | Seven passed in the saved `results/nov18/baseline_verification.txt` log |
| Additional automated audit | `results/nov18/additional_checks.json`; dynamics/energy/targets/power/exposure, flat analytic case, inactive-term agreement |
| Preserved baseline artifacts | Saved hash check: `results/nov18/baseline_preservation.json` |

Saved run summary: five analytical infeasibilities, zero numerical/evaluation failures, largest energy residual about **2.22e-11 kWh**. That is a successful numerical execution, not physical battery validation.

**Not complete:** independent model/source review; independent reproduction on a teammate's environment; 50-session expansion; repeated runtime study; final interpretation/captions; actual slide deck; rehearsals; larger final-report evaluation and final report. A slide storyboard and report outline exist, but they are not finished slides/report. Independent reviews must not be retrospectively credited to the existing automated checks.

## 5. The complete model you need to understand

### Physical model and parameters

For intervals t=0,...,N−1, p_t is grid kW and s_t is SOC fraction. dt is hours, E battery kWh, eta efficiency:

```text
s_(t+1) = s_t + eta * p_t * dt / E
0 <= p_t <= Pmax
0 <= s_t <= s_max
s_0 = initial_SOC
s_N = target_SOC
G = E * (target_SOC - initial_SOC) / eta
sum(p_t * dt) = G
```

Defaults: E=60 kWh, eta=.90, Pmax=7.2 kW, s_max=.90, reference SOC=.70. Charging only, continuous power choices, constant power per interval, fixed temperature/efficiency/capacity. No V2G, fleet coupling, forecasting, tapering, thermal dynamics, binary charger activation or degradation feedback on usable capacity.

The target must be at least the start and no greater than .90. Required grid energy must fit `Pmax * connected_hours`. Arrival/departure/prices are known. All methods use exact equal final energy, not “at least enough.” Feasibility under assumed hardware does not establish real charger capability.

### Scores and objectives

```text
C   = sum(price_t * p_t * dt)                         dollars
D_P = mean((p_t/Pmax)^2)                              dimensionless
D_S = mean((max(s_(t+1)-s_ref, 0)/(1-s_ref))^2)         dimensionless
C_ref = max(abs(immediate_charging_cost), 1 dollar)
```

D_P discourages concentration of power; D_S discourages time spent above the chosen SOC threshold. The threshold is **soft**: crossing .70 is allowed. The .90 SOC limit is **hard**. Both scores are assumptions, not fitted health laws. D_S uses end-of-slot SOC and includes waiting. C_ref stays fixed within each instance across weights.

| Policy | Objective / implementation |
|---|---|
| Immediate | Fixed rule: maximum power from arrival, one partial final active interval if needed, then zero. Not an optimizer. |
| Cost-only | First minimize C. Then minimize D_P subject to cost <= optimum + $1e-8. This tie-break spreads equal-price charging. |
| Power penalty | Minimize C/C_ref + 1*D_P. It can pay extra to avoid power concentration. |
| Combined | Minimize C/C_ref + 1*D_P + 10*D_S. Timing and power preferences can conflict. |

Optimization implementation uses an auxiliary z>=0, z>=s_end−s_ref, z<=1−s_ref. With positive high-SOC weight its minimum gives actual excess; with zero weight z need not equal excess, so reported metrics recompute the positive part directly. Affine constraints and positive-semidefinite quadratic objective make this a convex quadratic program. Positive power weight gives unique p; cost-only uniqueness is handled by the second-stage rule. Nonlinear does not imply nonconvex.

CLARABEL settings: absolute/relative gap and feasibility tolerances 1e-10; max 300 iterations; require `optimal`. Runtime reporting distinguishes whole-case time from final solver-stage time (cost-only solves twice). Existing assertion thresholds: energy/power/optimizer residual <1e-6; SOC/target residual <1e-8. Residual fields have different units—do not mix them into a physical quantity.

### Scenario differences

**Synthetic example:** 18:00–06:00, 48 fifteen-minute slots, start30%/goal80%, grid requirement33⅓ kWh, battery30 kWh. Synthetic prices:18–22 $0.30;22–03 $0.10;03–06 $0.24. Baseline costs immediate $9.0933, cost-only $3.3333, power $3.8263, combined $4.2707.

**Real-session replay:** recorded window and `kWhDelivered`; assume grid-side delivered energy, E60/eta.9/Pmax7.2. Initial SOC is .30/.60/.75, target=`initial + .9*recorded_kWh/60`. Slot count=ceil(hours/.25), dt=hours/count: actual endpoints preserved. Synthetic daytime price is $0.30 from16:00–21:00 source-local, $0.15 otherwise. Slot price is sampled at slot start; tariff-boundary slots are not split. All methods retain recorded energy. Invalid assumptions are logged; they do not change the record.

### Published evaluator: separate from optimization

The selected law is the Naumann Sony US26650FTC1 LFP/graphite calendar capacity model. It **does not enter any of our four optimization objectives**; it evaluates the schedules afterward. It cannot assess total cycling damage or prove gentler power improves battery health.

```text
q(t) = k(T,s) * sqrt(t_seconds)
k(T,s) = k_ref * exp[-Ea/R * (1/T - 1/T_ref)]
         * (2.8575*(s-.5)^3 + .60225)
k_ref = 1.2571e-5 fraction/sqrt(second)
Ea = 17126 J/mol; R = 8.314 J/(mol K); T_ref = 298.15 K
```

Original table gives k_ref=.0012571 **percent**/sqrt(second): divide by100 for fractional loss. Output ppm means fractional loss×1e6, not percent life gained.

History continuation: `q_new² = q_old² + integral(k(T,s(t))² dt_seconds)`. Do not restart the square-root clock every interval. Four-node Gauss quadrature integrates the degree-six SOC expression over linear-within-slot SOC at fixed T. Default q_old comes from 365 days at25°C/50%SOC; present temperature25°C. Each session is an independently initialized hypothetical comparison, not successive observations of one identified battery. Current-temperature sensitivity uses15/25/35°C and prehistories0/365/1095 days; prehistory remains25°C/50%SOC.

**Source verification already documented, not independently re-established by this handoff:** Naumann's author dissertation full text was inspected, not the journal article PDF. Dissertation Chapter5 printed pp69–75, Eq5.1/5.3/5.12/5.15/5.17 and Table5.1; official pinned SimSES capacity implementation cross-check. Links and differences are in `docs/model_specification.md` and `sources/manifest.json`:

- Author full text: https://mediatum.ub.tum.de/doc/1434981/document.pdf
- Original article DOI: https://doi.org/10.1016/j.est.2018.01.019
- Reference code: `sources/sony_lfp_calendar_reference.py`; license retained.

Stored-cell experiments, roughly885-day study, temperature/SOC fit coverage, early reversible effects and monthly-scale stress switching limit transfer to minute-scale charging and modern packs. A 0–60°C/0–100% code envelope is not proof of uniform accuracy. Independent reviewer must assess transfer and language. The resistance branch is excluded. Literature alternatives/cycle laws remain unimplemented unless verified; do not substitute invented coefficients. Two models would test robustness, not validate real health improvement.

## 6. Data: what is real and what is assumed

Real: original ACN event timestamps, delivered energy, site/station/session identifiers. Assumed: battery capacity, starting/target SOC, chemistry, temperature/history, power limit, efficiency and tariffs. Generated: all alternative power/SOC schedules and aging estimates. We have **not** compared against the original measured minute-by-minute power traces; the saved raw responses contain totals/event times.

Initial data retrieval used the official tutorial's public DEMO_TOKEN after unauthenticated access failed. Reproduction uses frozen JSON, no credentials/network needed after dependencies. Do not confuse the official fallback simulator archive's field called requested energy with actual user-requested energy. `userInputs` and userID are null in all five original controls; delivered energy is not a measured request and need not reveal driver satisfaction.

The Nov 18 snapshot has100 candidates; selection retains five original controls plus ten additions via duration bins <=4,4–8,>8 h and energy bins <=5,5–10,>10 kWh. Screen required fields, duplicate IDs, nonpositive energy/windows, charging-stop ordering and baseline physical feasibility; sort each bin by actual connection and sessionID; round-robin bins. This is a diverse convenience cohort, not random or representative. Selection ledger records exclusions and unused records. Selection differed explicitly from the earlier proposed date-window query. Do not hide that change.

Original S1 has charging stop60 seconds after disconnect; kept flagged for diagnosis. Clean paired summaries exclude flagged cases. Preserve actual local dates and windows; never move workplace sessions into overnight time. Parse raw GMT event fields and convert using America/Los_Angeles; do not parse timestamps out of sessionID strings.

### Essential worked example: S2

Find sessionID `2_39_95_27_2018-04-25 13:45:09.617470`, space CA-319, in `data/acn_sessions_raw.json` or the cohort. Raw connection=`Wed, 25 Apr 2018 13:45:10 GMT`; disconnect=`Thu, 26 Apr 2018 00:56:16 GMT`. Los Angeles is UTC−7 on those dates: local06:45:10–17:56:16 April25, duration11h11m06s. Delivered grid energy10.013 kWh, battery addition9.0117 kWh, SOC increase15.0195 percentage points.

| Assumed start | Derived target | Consequence |
|---|---:|---|
|30%|45.0195%|Never crosses70%; high-SOC score zero|
|60%|75.0195%|High-SOC term active; feasible|
|75%|90.0195%|Above90% cap; infeasible, even though only slightly above|

At60% start, S2 power-only and combined both cost about$1.50195. High-SOC score falls from.00730753 to.00569930, while peak power rises from1.0601 to3.4106 kW and D_P rises from.0183071 to.0226325. Explain this tradeoff rather than claiming every score improves. The zero cost premium is valid: cheap hours can accommodate delivery.

## 7. Current findings to verify, not memorize

1. Original five controls at30% start all finish below46%; their high-SOC scores are zero. Power-only/combined therefore match numerically. Calendar aging remains positive; it has no70% cutoff.
2. Assumed60% or75% arrivals activate the high-SOC score in some cases. Across all clean60% cases the median change rounds to zero; that does not mean every case is unchanged. Inspect S2 individually and distributions.
3. Combined can reduce exposure while increasing power concentration/peak. Do not say slower charging always helps or every metric improves.
4. The synthetic8-hour case has combined exposure.006202 versus cost-only.006183: adding two weighted preferences does not guarantee a lower value of each individual score than cost-only. Investigate and explain, not silently delete.
5. Current clean paired-case counts are14/14/9 for assumed30/60/75% starts. Different feasible denominators must be disclosed. The five excluded scenarios are `real_1_soc75`, `real_4_soc75`, `real_7_soc75`, `real_10_soc75`, `real_13_soc75`; generic saved reason is “Invalid physical parameters.” Confirm the target/cap cause from scenario fields and give a specific explanation in your review without rewriting frozen evidence.
6. Resolution changes affect both optimization and the end-of-slot exposure approximation. Single-run times are descriptive; repeat small fixed tests if claiming computational scaling. Some sensitivity cases duplicate baseline settings, so they are not independent observations.

Do not interpret tiny negative near-zero dollar differences or displayed −0.000000 as meaningful savings. Read exact numbers and solver/tie-break tolerances.

## 8. Repository map and safe ownership

All paths below are relative to this repository, so this handoff remains portable.

| Files | Purpose | Owner/review action |
|---|---|---|
|`src/charging.py`, `src/aging.py`|Physical/QP model, policies, metrics, calendar evaluator|M reviews semantics; I proposes fixes separately|
|`src/run_example.py`, `src/inspect_data.py`|Original baseline runners; overwrite baseline results if run here|Read; do not rerun in shared root|
|`tests/test_verification.py`|Seven analytic/physical/history tests|I reproduces; M independently checks their meaning|
|`data/acn_sessions_raw.json`, `data/inspection.json`, `data/sample_sessions.csv`|Original five records and audit|User owns interpretation; keep immutable|
|`data/nov18/acn_candidate_snapshot.json`|Frozen100-candidate source|I reuses for reproduction; expansion gets a new snapshot|
|`experiments/nov18/run_study.py`|15-session/sensitivity study runner|I reads/runs only in isolated copy initially|
|`experiments/nov18/summarize_study.py`|Saved-output audit and readable summaries|I reproduces; user interprets|
|`results/nov18/metrics.json`, `trajectories.json`|Scores/settings/metadata; complete power/SOC/price paths|All cite output identity for claims|
|`results/nov18/cohort.json`, `selection_ledger.json`, `data_provenance.json`|Selected raw records and selection evidence|User checks selection; I preserves mapping|
|`results/nov18/exclusions.json`, `run_summary.json`, `additional_checks.json`|Infeasibilities/failures/counts/check status|I audits; user explains limitations|
|`results/nov18/findings.md`, PNGs, `paired_clean_results.json`|Tables, plots and paired comparisons|User drafts captions; M/I verify claims|
|`results/nov18/aging_sensitivity.json`, `nondominated_weight_cases.json`|Post-evaluation history/temperature and weight tradeoffs|M checks meaning; user presents|
|`docs/model_specification.md`, `sources/manifest.json`|Prior source audit, equations and provenance|M begins independent source review|
|`docs/data_review_nov14.md`|Beginner walkthrough and original-data review|All read example; older experiment proposals superseded by newest schedule|
|`docs/nov18/nov22_execution_target.md`|Newest schedule|All retain scope/deadlines|
|`docs/nov18/theory_and_storyboard.md`|Draft derivations, slide storyboard/report outline|Draft only, contains overlapping storyboard sections; choose one coherent final structure|
|`docs/nov18/manual_workbook.md`|Guided understanding tasks|User's human practice, not teammate review sign-off|

Some new experiment/docs/data files are currently **untracked in Git**. A branch name or clean-looking commit alone may not contain this study. Before another machine reproduces, confirm it receives the listed files, including frozen snapshots and runners. Do not share `.venv` as a portable environment; install pinned dependencies. Preserve unrelated work; no destructive Git actions.

Proposed new ownership locations (create when doing the work): M writes `docs/reviews/model_review_nov20.md`; I writes `docs/reviews/reproduction_nov20.md`; both record issues in a shared `docs/reviews/issues_nov20.md`; user prepares captions/slides. Put expansion code under `experiments/nov22/`, new snapshots under `data/nov22/`, outputs under `results/nov22/`. These are suggested paths, not files already completed. Do not edit the same baseline file concurrently. M specifies a model issue; I implements an agreed change in a new version and records affected outputs.

## 9. Reproduce safely — implementation owner's exact starting procedure

### Preconditions and installation

Use macOS/Linux or a compatible shell with Python3.12, `cp`, and `mktemp`. On Windows use WSL or adapt the commands. Existing execution used Python3.12.14; direct requirements are pinned in `requirements.txt` (NumPy2.3.5, SciPy1.18.1, CVXPY1.9.3, CLARABEL0.11.1, Matplotlib3.11.2). A pinned dependency may fail on an incompatible platform/Python: record the error and ask the team before silently substituting versions. Installing dependencies needs internet; replaying the frozen study does not.

From the repository root in one terminal, create an **isolated copy**. Substitute your Python3.12 executable if `python3.12` is not installed. On the original owner's Mac, the existing `.venv/bin/python` is usable, but an independent fresh environment provides stronger evidence.

```sh
project_root="$PWD"
review_copy="$(mktemp -d "${TMPDIR:-/tmp}/ev-reproduce.XXXXXX")"
mkdir -p "$review_copy/experiments"
cp -R src tests data requirements.txt "$review_copy/"
cp -R experiments/nov18 "$review_copy/experiments/"
cd "$review_copy"
python3.12 -m venv .venv
.venv/bin/python -m pip install -r requirements.txt
mkdir -p results/nov18
.venv/bin/python -m unittest discover -s tests -v > results/nov18/reviewer_tests.txt 2>&1
cat results/nov18/reviewer_tests.txt
```

Inspect that the log actually says **seven tests, OK**. Stop and document any failure. Do not treat a displayed command as executed evidence. Then:

```sh
.venv/bin/python experiments/nov18/run_study.py > results/nov18/reviewer_run.txt 2>&1
cat results/nov18/reviewer_run.txt
.venv/bin/python experiments/nov18/summarize_study.py
cat results/nov18/run_summary.json
```

Expected counts for unchanged inputs/code:15 sessions;236 metric rows;224 trajectories;5 analytical infeasibilities;0 numerical failures;36 aging evaluations. Cost/power/SOC results should agree within documented numerical tolerances; runtime, iterations or image binary hashes need not be identical. No API call is part of this procedure. Font-cache creation may make the first plot slower. On a failure, read the traceback and `exclusions.json`; do not use an old saved summary as proof the new command succeeded. The runner catches some per-case exceptions and continues, so **process exit0 alone is insufficient**: require numerical_failures=0 and expected counts.

To inspect a specific case without rerunning anything, from the copied root:

```sh
.venv/bin/python - <<'PY'
import json
rows=json.load(open('results/nov18/metrics.json'))
for r in rows:
    if r['case']=='real_1_soc60':
        print(r['method'],r['cost_dollars'],r['high_soc_proxy'],r['peak_kw'])
exclusions=json.load(open('results/nov18/exclusions.json'))
print('S2 at75%:',[r for r in exclusions if r['case']=='real_1_soc75'])
PY
```

Three smoke cases: S2 at60% (`real_1_soc60`) active; S3 at60% (`real_2_soc60`) inactive; S2 at75% (`real_1_soc75`) infeasible. S2 is cohort index1, not index2; index starts at0. Do not confuse the original five-session pilot's30% assumptions with the later60% representative figure.

Record the temporary copy path, Python/package versions, commands, logs and discrepancies in your review. Copy **only your reviewer evidence** to your owned shared-repository review directory; do not overwrite the original frozen results. Do not erase the copy until the review evidence is retained. These instructions are for a human reproduction: any assistant check of the instructions remains automated, not your independent sign-off.

## 10. Your detailed responsibilities and completion criteria

### M — model/theory owner

Your responsibility is **“Is the formulation scientifically defensible, and are claims appropriately limited?”** Do not wait for the bigger sample: existing code/data are sufficient for your core review.

1. **Source audit:** read the dissertation portions and official reference implementation yourself. Record exact title/source/location/equation numbers and whether each source was actually obtained in full text. The journal article is not previously full-text verified. Independently check the fraction/percent conversion, seconds/hours, T in kelvin, parameters and history mapping. If source access fails, record it as unresolved, not verified.
2. **One independent numerical calculation:** at25°C/50%SOC, `k=1.2571e-5*.60225`. For constant conditions with365-day prehistory and12 more hours, calculate `k*(sqrt(365*86400+43200)-sqrt(365*86400))`. Compare to `evaluate` without resetting age. Explain why adding fresh square-root losses every15min is incorrect.
3. **Physical formulation:** derive required energy and the power/window feasibility condition; inspect equal-energy and target logic; review constant efficiency/capacity and omission of tapering near90%. Evaluate60/75% hypothetical starts and paths up to90% for model applicability.
4. **Optimization theory:** derive gradient/Hessian in the (p,z) formulation, convexity, and KKT conditions with consistent constraint signs. Confirm uniqueness in p when power weight>0 and the role of tie-breaking. Do not claim numerical dual/stationarity residuals were measured: current logs report primal feasibility, not a full KKT audit.
5. **Interpretation:** explain why the proxies and published evaluator are different, why70% is not a damage onset, why zero proxy does not mean zero aging, and why normalized cell losses do not establish pack lifetime. Review the short-session/storage-law transfer.
6. **Prior work:** prepare a compact comparison of source-verified alternatives/pros/cons and the selected scheduler, sufficient for the application rubric. Use original sources; background studies were absent and should not be treated as equations. Do not invent a second evaluator to fill a table.
7. **Output:** `model_review_nov20.md` with evidence-based decisions, corrections, unresolved questions and signed/date-reviewed claims. Prepare equations/limitations and speaking notes for your slides. If a change is necessary, specify it to I before requesting affected experiments be rerun.

Done means another member can trace your conclusions to source/code and you can explain the key equations unaided. A signature without checked evidence is not enough. Optional second-evaluator/cycle-law feasibility is retained for the original post-presentation gate; do not casually change scope or declare it implemented.

### I — implementation/verification owner

Your responsibility is **“Does the code implement the stated model, and can someone else reproduce it?”**

1. Reproduce in section9, retain logs, compare counts and key metrics, and confirm the frozen input manifest. Check that all untracked necessary files were transferred.
2. Inspect source-to-equation mapping in `src/charging.py`, `src/aging.py`, the experiment runner and summarizer. In particular, starting SOC and derived target must change together; grid/battery energy must not be confused; all waiting must be included; cost-only has two stages.
3. Independently inspect at least the three smoke cases and one flat-price case. Check arrays have N powers/N+1 SOC values; reconstruct SOC using dt in hours; check target/bounds/energy, and repeat calendar check after M's guidance. A score-only table cannot replace path inspection.
4. Audit failures and exclusions: five present cases are analytical, not numerical failures. For future data, distinguish invalid record, infeasible assumed scenario, optimizer failure and aging-evaluator failure. Record reasons before filtering for paired comparisons. No clipping or timestamp/energy repair.
5. Check solver/status/residual thresholds, numerical tolerances and objective weights. The summarizer currently contains hardcoded narrative counts236/five and the runner's cohort target is hardcoded10 additions. A larger study needs a separate configurable version and dynamically generated summaries; changing only a file name or snapshot is not sufficient.
6. Coordinate the **50-session target by Nov 22** with the user's selection requirements. Create separate code/config/snapshots/outputs. Retain15 reference cases, select35 additions with frozen duration/energy-bin rules before solving, preserve original records/windows, keep a ledger for all candidates and use the same four policies at30/60/75%. Confirm enough eligible candidates; current100-record snapshot is a candidate pool, not a guarantee of50 usable sessions. If more raw data is needed, freeze query/pagination/date/hash; do not use personal credentials committed to code. Record changes in sampling availability explicitly.
7. Produce paired summaries with case counts, medians/interquartile ranges and full distributions; save full trajectories and input/config hashes. Preserve zero-effect/worse-metric cases. Current weight results lack saved trajectories; add them only to a separate new version if required for deeper audit.
8. Retain all sensitivity families already executed. Repeat timing on a small fixed case set (e.g. five runs for each60/30/15/5min resolution), label warm-up/setup/solver scopes and hardware, and avoid overclaiming speed trends from single-run noise. Compare models on objective structure, runtime and solution metrics, not only expense.
9. Output `reproduction_nov20.md`, issue/fix evidence and a new verified result pack byNov22. Prepare implementation/verification/runtime slides. If fixing a bug, show before/after evidence, identify affected outputs and request M/user interpretation review.

Done means a fresh replay produces traceable outputs with counts and acceptance checks, all discrepancies have dispositions, and reviewers can explain why the tests matter. No hidden modification of baseline files.

### U — existing data/interpretation member (the person who requested this handoff)

U owns data-quality interpretation, observed/assumed labels, source-record spot checks, paired findings and captions, limitations and the accessible project narrative. U is working through guided explanations; this is not independent model/implementation sign-off. U does not need to operate the solver or derive the aging law. U coordinates questions and verifies that slide claims map to evidence. U and I jointly freeze sample rules before expansion; U and M jointly approve health-related wording.

## 11. Schedule, dependencies and deliverables

All dates2026; deadlines use the team's America/Chicago context. Recorded session times remain source-local. No planned content is deleted.

| Date | M | I | U / team |
|---|---|---|---|
| **Nov 19 — start immediately** | Source/units/history and objective review | Isolated reproduction, three smoke cases, existing issues | Guided data/plot review; prepare selection questions |
| **Nov 20 — core checkpoint** | Review log and theory/source/limitations slides | Reproduction log; fix/verify core; freeze expansion configuration | Verify core captions/findings; archive a usable presentation baseline |
| **Nov 21** | Review changed assumptions and draft claims; prepare prior-work comparison | Run expansion toward50 and dynamic summaries; timing study | Full slide draft; review selection/exclusions and result distributions |
| **Nov 22 — expansion checkpoint** | Close scientific claim questions | Freeze checked expanded tables/plots and sensitivity pack | Three–five supported findings; first timed15–20min rehearsal |
| **Nov 23** | Correct and practice answers | Fix concrete reproduction/figure issues only | Second rehearsal, proofread, final slide freeze |
| **Nov 24** | Explain formulation/theory/evaluator | Explain implementation/verification/computational study | Explain motivation/data/results/limits; deliver presentation |

Dependencies: M's corrections -> I's new version/rerun -> U's updated interpretation -> final slides. Meanwhile independent review, data preparation and draft slides proceed in parallel. Share one issue list with ID, severity, evidence/file/case, owner, proposed correction, affected outputs, status and closing evidence. Hold a15-minute daily check-in focused on decisions. No teammate has acknowledged these assignments merely because they appear here.

The human effort target is30–40% (about35%) of remaining preparation: source checks, independent verification, understanding, interpretation and rehearsal. Automate repeatable data cleaning/runs/tables/plots and draft material (about65% estimated). These are effort allocations, not measured completion percentages. Do not manufacture manual busywork or count reading a generated answer as independent proof.

### November20 acceptance

- M and I logs exist with concrete checked evidence, or missing items are explicitly recorded.
- Core equal-energy policies, analytic check, history and source/units are reviewed.
- All failures/flags are visible; conclusions use observed/assumed distinctions.
- Core plots can support the talk if expansion has problems.

### November22 acceptance

- Aim50 **unique sessions**, at most600 schedules before infeasibility; actual counts and eligible denominator reported. This remains a stretch target, not already executed.
- All four policies, original controls, weights/ablations and full planned sensitivity/computation families remain covered.
- Results include paired changes, uncertainty/selection limits, medians/IQR and failure ledger, not cherry-picked winners.
- Three–five findings have exact evidence links and caveats.
- Complete deck and first rehearsal; expansion must not consume speaking practice.

If access or review cannot finish, preserve the core study and mark uncompleted targets/provisional claims honestly, while continuing unresolved work after presentation. Do not silently reduce scope or claim “verified” to hit a date. Send a concrete dependency update to the team/instructor as appropriate; no external communication is automatic.

### Remaining final-report work, not removed

AfterNov24: incorporate feedback; extend toward100 sessions if useful; broaden temperature/history/threshold/resolution analysis; retain the optional second published evaluator/cycle-law reproducibility decision; complete related work and theory; write the8–12-page report with actual contributions; clean-environment reproduction and packaging. Original calendar: expansionNov25–29; deeper analysis/model decisionNov30–Dec 4; reportDec5–8; checksDec9–11; proofread/packageDec12; **submitDec13 by11:59p.m.** Aim earlier that day. Do not assert all optional models are required by the rubric or erase the original optional decision gate.

## 12. Presentation: what each person should be ready to explain

Use the full storyboard as draft material, not a finished deck. A coherent main sequence is:

1. Motivation/research question and contribution (U).
2. Real data, unknowns and assumptions (U).
3. Physical formulation and four objectives; penalty reasoning (M).
4. Convexity/solver/analytic verification (M/I).
5. Published calendar evaluator, source/history and limits (M).
6. Synthetic example, weight tradeoffs and counterexamples (U/I).
7. Real cohort/SOC/feasibility and representative comparison (U).
8. Sensitivity and runtime/resolution (I).
9. Findings, limitations, planned report work and actual contributions (all).

Target15–20min, approximately18min speaking plus whatever question arrangements the instructor gives. Main slides summarize every planned component; detailed coefficient tables, extra tests and sensitivity cases go in backup slides. About3–4 slides per owner is an organizational suggestion, not a rubric rule. Pick one deck editor; each owner checks their content and every member practices the shared story. Do not say each member authored generated code they did not write/review.

### Claims to avoid

| Avoid saying | Say instead |
|---|---|
|“We proved longer battery life.”|“We found conditional proxy/calendar-model tradeoffs; no measured health validation.”|
|“We measured60% SOC.”|“We assumed60% arrival SOC while preserving recorded energy/window.”|
|“We evaluated236 real charging sessions.”|“15 real sessions generated multiple hypothetical cases;236 schedules include synthetic studies.”|
|“70% is where damage begins.”|“70% is our illustrative soft exposure threshold.”|
|“The calendar model penalizes charging power.”|“Power score is a separate surrogate; calendar evaluator uses SOC/time/temperature/history.”|
|“All scores improve with combined optimization.”|“Preferences compete; report each metric and counterexample.”|
|“The data proves real cost savings.”|“Prices are synthetic; expenses are simulated.”|
|“The reviewer checked it because tests passed.”|“Automated checks passed; human review status is separately documented.”|

## 13. Understanding check — explain these without looking at code

Both teammates should be able to answer:

1. Which inputs are observed and which are assumptions? **Observed window/delivered energy; SOC/capacity/chemistry/tariff/etc. assumed.**
2. Why are15 sessions not160 observations? **Four methods and three hypothetical starting conditions are repeated alternatives on the same records.**
3. Is immediate charging an optimization algorithm? **No, it is a fixed baseline policy.**
4. Why can cost-only already produce smooth charging? **Its second-stage squared-power tie-break.**
5. What distinguishes70% from90%? **Soft score threshold versus hard feasibility cap.**
6. Why is S2 at75% start infeasible? **Fixed energy adds15.0195 percentage points, exceeding90%; timing cannot fix final energy.**
7. Why can zero high-SOC score coexist with positive aging? **Calendar law has no70% cutoff.**
8. Why could combined use a higher peak? **It delays energy to reduce exposure and catches up later.**
9. Why is this nonlinear optimization but convex? **Quadratic PSD objective with affine constraints.**
10. What must happen before “independently verified” is claimed? **A person reproduces/checks evidence and records conclusions, not just reads the existing audit.**

M should additionally derive the energy formula and explain virtual-time aging; I should additionally identify a trajectory row and reconstruct its SOC/energy from p/dt independently. If you cannot explain one answer, record it in the issue log and ask for a worked example; do not pretend understanding to meet a deadline.

## 14. Review/handoff templates — leave blank until actually completed

**Model review entry**

```text
Reviewer / date:
Source obtained and exact equation/table/page:
Code/function and units checked:
Independent calculation and comparison:
Operating-range/transfer/history assessment:
Decision: verified / correction needed / unresolved
Allowed claim wording and limits:
Affected cases / requested action / owner:
```

**Reproduction entry**

```text
Reviewer / date / machine / Python and dependency versions:
Input snapshot hashes and isolated copy path:
Commands actually executed; log locations:
Expected versus observed counts/status/residuals:
Cases independently inspected; calculations:
Discrepancy (or none), tolerance and evidence:
Fix/new version and affected outputs, if any:
Decision: reproduced / failed / unresolved
```

**Daily team message**

```text
Completed and checked (evidence):
Still unverified or blocked:
Decision needed from whom:
Next task / owner / due:
Result/slide files ready for the others:
```

**Final quick-start instruction:** M starts at `docs/model_specification.md`; I starts with the isolated reproduction in section9; U continues the data/plot explanations and prepares captions. You can begin these three tracks independently now.
