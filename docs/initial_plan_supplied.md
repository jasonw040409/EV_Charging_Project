# Battery-Aware Nonlinear Optimization of EV Charging Schedules

Initial project plan — CSE 543T: Algorithms for Nonlinear Optimization
Prepared November 3, 2026; reset November 14, 2026 for a three-member team starting from zero. Presentation confirmed for November 24. Proposed scope and methods; no implementation or experimental results are claimed.

Planning milestones: a verified core implementation and meaningful comparison results by November 20; slides and rehearsal completed November 21-23; team presentation November 24; final report and software due December 13. These intermediate completion targets are team planning recommendations, not additional rubric requirements.

The previous November 3-13 tasks were not completed. This revision replaces those elapsed milestones with parallel work beginning November 14, while retaining the November 20 results checkpoint, November 21-23 slide/rehearsal period, November 24 presentation, and December 13 submission deadline. Keep the substantive project: two battery-stress terms, all four charging strategies, a small real-session evaluation, a weight tradeoff study, and focused sensitivity analysis. Reduce breadth and duplicate implementation, rather than stripping the study down to one synthetic example.

## Plain-language overview

Imagine an EV plugged in overnight that needs to reach 80% charge before its driver leaves. Charging immediately is easy, but electricity may be cheaper later. Charging only during the cheapest hours can concentrate charging power or finish early and leave the battery at high charge for hours. We will calculate a schedule that balances electricity expense with two simplified stress indicators: concentrated charging power and time spent at high SOC.

The project compares four schedules for the same energy requirement: charge immediately, optimize electricity expense only, add the charging-power penalty, and add both penalties. We then ask what changes in the schedule, how much extra money is spent, and which stress scores decrease. These are modeled stress scores, not direct measurements of battery damage or lifetime.

By November 24, the team should be able to explain the model, show that the code works, and discuss actual comparisons on a worked example and a small set of real charging sessions. The weeks after the presentation are for broader evaluation, stronger analysis, and the report/software package.

## 1. Project aim and research questions

Develop an offline charging scheduler for a plugged-in EV that reaches a specified state of charge (SOC) by departure while balancing electricity expense against simplified battery-stress indicators.

Primary question: How much modeled battery stress can be reduced, and at what electricity-cost premium, by optimizing charging power and timing instead of minimizing electricity expense alone?

Secondary questions:

- How do available charging time, initial SOC, required departure SOC, and electricity-price patterns affect this tradeoff?
- What changes when charging-rate stress and high-SOC exposure are modeled separately versus together?
- Can the model's convex structure support reliable solution and verification at practical time resolutions?

The contribution is an application-specific formulation, reproducible model comparison, and analysis of when battery-aware scheduling matters. This does not claim to invent battery-aware charging or a new solver.

## 2. Rubric alignment and scope

The supplied project handout permits an application project solved with an existing optimizer. It requires a well-defined problem, a survey of existing models, a developed model, an existing-solver solution, and evaluation using application data. It additionally requires at least one comparison, customization, or domain-knowledge study. Comparing cost-only and battery-aware models addresses the comparison requirement directly.

| Rubric consideration | Planned evidence |
| --- | --- |
| Motivation, relevance, applicability | A charging-by-departure problem with an explicit expense/stress tradeoff |
| Clarity of contribution | Clearly specified proxy model, controlled ablations, and sensitivity results |
| Technical soundness | Units, feasibility conditions, convexity argument, optimality conditions, numerical checks |
| Implementation effort | Working solver pipeline, baselines, real-session preprocessing, repeatable experiments |
| Analysis and insights | Tradeoff curves, failure cases, model limitations, effects of charging flexibility |
| Presentation quality | Self-contained report, interpretable plots, references, explicit member contributions |

Core scope: one vehicle per optimization instance; continuous, unidirectional AC charging; deterministic prices and known departure; constant charging efficiency and temperature assumptions. Evaluate many independent real charging sessions.

Organize execution into two stages. Before November 24, establish a coherent project story with the formulation, a working implementation, verified baseline comparisons, and preliminary data-informed results. After the presentation, incorporate feedback, broaden the experiments, and complete the final report and reproducibility package. Keep the central research question and core model consistent across both stages.

Excluded from the core: vehicle-to-grid discharge, binary charger activation, battery electrochemistry, learned battery models, online forecasting, and full distribution-network power flow. These would add substantial work without being necessary for the rubric.

### What stays and what changes in the accelerated plan

| Component | Revised decision |
| --- | --- |
| Both power-related and high-SOC stress terms | Keep throughout; they are the main modeling idea |
| Immediate, price-only, rate-aware, and combined strategies | Keep all four; share one modeling/evaluation pipeline |
| One vehicle per session, evaluated across real sessions | Keep; aim for 10-20 cleaned sessions before the presentation |
| Tradeoff analysis | Keep; use a modest predefined weight grid rather than a large search |
| Sensitivity analysis | Keep a focused charging-window/price-pattern study before presentation; broaden afterward |
| Theory and verification | Keep convexity, a compact derivative/KKT treatment, feasibility and energy checks |
| Literature survey | Focus on roughly 3-5 directly relevant sources instead of a broad review |
| Solver implementation | Choose one stack and one primary solver by Nov 14; remove the duplicate AMPL/Python implementation task |
| Large sample expansion and full sensitivity matrix | Move after Nov 24, still before the final deadline |
| External degradation simulation, fleet/V2G, temperature model, new algorithm | Remove from this delivery plan; discuss as future work |

## 3. Initial mathematical model

Index the connected charging session by t = 0,...,T-1. Let delta_t be the time-step length in hours, H = T delta_t the session duration, and s_t the SOC fraction at a time boundary.

| Symbol | Meaning | Unit |
| --- | --- | --- |
| p_t | Grid-side charging power, decision variable | kW |
| s_t | Battery SOC, decision variable | fraction |
| z_t | Nonnegative excess SOC above a reference threshold | fraction |
| c_t | Electricity price | $/kWh |
| E | Usable battery capacity | kWh |
| eta | Constant charging efficiency | dimensionless |
| P_max | Maximum grid-side charging power | kW |
| s_init, s_goal | Arrival and required departure SOC | fraction |
| s_max | Hard upper SOC bound | fraction |
| s_ref | Reference threshold for the high-SOC exposure proxy | fraction |

### Constraints

\[
s_{t+1}=s_t+\frac{\eta p_t\Delta t}{E}.
\]

\[
0\le p_t\le P_{\max},\qquad 0\le s_t\le s_{\max}.
\]

\[
s_0=s_{\mathrm{init}},\qquad s_T=s_{\mathrm{goal}}.
\]

Use the same exact final SOC in all compared schedules to avoid comparing different amounts of delivered energy. Assume s_goal >= s_init and s_goal <= s_max. For this constant-power-cap model, feasibility additionally requires

\[
E(s_{\mathrm{goal}}-s_{\mathrm{init}})\le\eta P_{\max}H.
\]

For the high-SOC term introduce

\[
z_t\ge s_{t+1}-s_{\mathrm{ref}},\qquad 0\le z_t\le1-s_{\mathrm{ref}}.
\]

When its objective weight is positive, minimization makes z_t equal max(s_(t+1)-s_ref,0). Recalculate this positive part directly when reporting scores, including when its optimization weight is zero. Using the end-of-interval SOC gives a conservative discrete approximation of exposure during charging.

### Objective

Electricity expense:

\[
C(p)=\sum_t c_t p_t\Delta t.
\]

Normalized charging-rate stress proxy:

\[
D_P(p)=\frac{\Delta t}{H}\sum_t\left(\frac{p_t}{P_{\max}}\right)^2.
\]

Normalized high-SOC exposure proxy:

\[
D_S(s)=\frac{\Delta t}{H}\sum_t\left(\frac{\max(s_{t+1}-s_{\mathrm{ref}},0)}{1-s_{\mathrm{ref}}}\right)^2.
\]

Optimize

\[
\min_{p,s,z}\;\frac{C(p)}{C_{\mathrm{ref}}}+\lambda_P D_P(p)+\lambda_S D_S(s),
\qquad \lambda_P,\lambda_S\ge0.
\]

C_ref is a fixed positive reference cost for a given instance, such as the immediate-charging cost under positive illustrative prices. It stays fixed across the weight sweep. This makes the weight choices interpretable without adding dollars to an uncalibrated stress score.

The two stress terms intentionally represent different scheduling preferences: a quadratic power penalty favors spreading a fixed amount of charging; high-SOC exposure discourages finishing too early and waiting at high SOC. Their competition with price produces the study's main tradeoff.

These are proposed engineering proxies, not fitted capacity-loss equations. The high-SOC threshold and relative weights must be justified as assumptions and varied in sensitivity analysis. Report reductions in proxy scores, not percentage extensions of battery life. Detailed degradation depends on chemistry, temperature, current, and usage history; the BLAST documentation is a useful source for this distinction.

### Why this is nonlinear optimization

The objective contains quadratic terms in charging power and excess SOC. With the z formulation, all constraints are affine and the quadratic objective is convex, giving a convex quadratic program (QP). Nonlinear does not imply nonconvex.

The technical section should derive the gradient/Hessian, explain positive semidefiniteness, and state the KKT conditions. With lambda_P > 0, the objective is strictly convex in p, so a feasible instance has a unique optimal power schedule. Cost-only instances can have multiple optima, especially under flat time-of-use prices; document the tie-breaking rule and avoid presenting a single arbitrary LP solution as the only cost-optimal schedule. A useful additional benchmark minimizes stress within a tiny tolerance of minimum electricity expense.

## 4. Worked scenario for explanation and debugging

Use this explicitly illustrative setup first:

- Plug-in window: 18:00 to 06:00, 12 hours, 15-minute steps (T=48).
- Usable capacity: E=60 kWh; efficiency eta=0.90.
- Arrival SOC: 0.30; departure SOC: 0.80; upper bound: 0.90.
- Charger maximum: 7.2 kW; illustrative high-SOC reference: 0.70.
- Prices: a synthetic profile with an early overnight low-price period and a higher-price period near departure, making early cheap completion and later charging compete.

Required battery energy is 30 kWh; required grid energy is 33.33 kWh; the minimum charging duration at maximum power is approximately 4.63 hours. The 12-hour window is therefore feasible and allows scheduling flexibility.

Expected qualitative behavior is a hypothesis: cost-only charging uses cheap periods, the power penalty spreads charging, and the high-SOC term can shift some energy closer to departure. Flat prices and tight deadlines are useful cases where tradeoffs may shrink or disappear.

## 5. Models, algorithms, and verification

| Model | Objective/policy | Purpose |
| --- | --- | --- |
| Immediate charging | Maximum power from arrival, with a partial final step | Practical baseline |
| M0: price-only | C(p) | Optimized LP baseline |
| M1: rate-aware | C/C_ref + lambda_P D_P | Isolate the quadratic power penalty |
| M2: combined battery-aware | C/C_ref + lambda_P D_P + lambda_S D_S | Main proposed model |

All four use identical physical constraints and terminal energy requirements. They are evaluated on expense, D_P, and D_S separately, rather than ranking models only by their own objective values. Add a price-optimal, stress-minimizing tie-break benchmark where needed.

Use one implementation stack: Python for data, experiments, and figures, with CVXPY and one suitable QP solver for optimization. If the team already has a working AMPL setup and unanimously prefers it, make that choice on November 14 and use it consistently; do not build both interfaces. Reuse the same model code for M0, M1, and M2 by changing the objective weights. The immediate-charging baseline is a short deterministic policy.

Verification should include the analytic feasibility test, SOC and power-bound residuals, energy balance, final SOC, and solver termination status. In a flat-price case with only the quadratic power penalty, the solution should be constant charging power when feasible, providing a useful analytic check. Inspect available stationarity/duality residuals and record solver settings. An independent check by another team member is required in the work plan; a second solver is not required. Record runtime, separating setup and solve time where available.

## 6. Data plan

Start with synthetic scenarios to debug the model, while a different member obtains real-session data in parallel. Caltech ACN-Data documents connection/disconnection timestamps and delivered energy. Verify that a small sample is accessible by November 15, clean and freeze approximately 10-20 sessions by November 17, and complete the pilot comparison by November 20. After the presentation, aim to expand to approximately 50-100 sessions using the same preprocessing rules. These sample sizes are planning targets, not rubric requirements; prioritize complete, traceable comparisons over increasing the count.

Real charging-session data will not automatically supply all battery parameters. Treat delivered grid energy as a fixed observed-energy benchmark, not necessarily the driver's true requested energy. For each session, assign and disclose compatible E and s_init assumptions, then derive s_goal = s_init + eta * delivered_energy / E. Screen infeasible sessions and document exclusions rather than silently reducing the requested energy.

Use timestamps to define the charging window, distinguish disconnection from last charging time, and handle timezones consistently. Initially use documented synthetic price profiles; if a real tariff is added, state its source and date. Do not present illustrative prices as a live local utility tariff. Handle partial boundary intervals consistently across all models.

The resulting study is data-informed schedule simulation, not a field validation of battery lifetime. If access to real sessions is unresolved by the end of November 15, the data owner should seek an accessible documented charging-session alternative or clarify an acceptable data source with the instructor. Solver development continues with synthetic inputs during this process. If only synthetic results are ready for November 24, label them explicitly and explain the remaining real-data work; this is a fallback, not the intended presentation scope or an assumption that synthetic-only evaluation satisfies the final requirements.

## 7. Experiment plan and expected figures

1. Representative-session comparison: overlay p_t and s_t for the baselines and proposed model, with a shared price panel.
2. Cost/stress tradeoffs: sweep lambda_P and lambda_S over zero and several logarithmically spaced positive values. Plot expense against each stress indicator; show selected nondominated solutions. Do not collapse unlike stress mechanisms into one unexplained score.
3. Model ablation: compare M0, M1, and M2 on the same sessions. Recompute both stress metrics for every schedule.
4. Scenario sensitivity: vary time flexibility, initial/target SOC, price timing, and the assumed high-SOC threshold. Include flat prices and barely feasible deadlines.
5. Computational study: vary the time resolution, such as 60, 30, 15, and 5 minutes, on a fixed physical horizon. Compare runtime, accuracy, and feasibility; keep the dt factors so objectives remain comparable.

Report per-session electricity cost, D_P, D_S, peak power, target attainment, maximum constraint violation, and runtime. Summarize paired differences across sessions and report distributions or median/interquartile range. Separate feasible and infeasible instances. Report cost differences relative to the optimized price-only baseline and immediate charging. No numerical improvement is promised in advance.

Priority figures: charging-power/SOC comparison; expense-versus-stress tradeoff; ablation summary; sensitivity or computational scaling. A null result in a realistic low-power regime is informative if explained.

### Experiment priorities around November 24

Before the presentation, complete the representative-session comparison, a modest weight sweep, and the M0/M1/M2 comparison on 10-20 pilot sessions, alongside immediate charging. An initial grid such as {0, 0.1, 1, 10, 100} for each normalized weight gives 25 combinations; M0 and M1 are already included along the zero-weight axes. Inspect numerical scaling on the worked example, then freeze the grid by November 17. Do not select weights solely to produce a favorable claimed result.

Also keep a small sensitivity study on clearly labeled synthetic scenarios: test three feasible charging-window lengths and three price patterns (flat, cheaper earlier, cheaper later), using a few fixed weight choices. This adds an explanation of when battery-aware scheduling changes behavior without requiring a large experiment matrix. Hold other inputs fixed, and disclose any infeasible cases. Keep these controlled scenarios separate from the real-session results.

Include basic correctness evidence: matched delivered energy, target attainment, power/SOC constraint residuals, and the flat-price analytic check. Aim for four presentation-ready outputs by November 20: a charging-power/SOC figure, a cost-versus-stress tradeoff plot, a pilot-results comparison table, and one compact sensitivity figure or table. Present findings supported by those runs, including weak or absent tradeoffs if that is what occurs.

After the presentation, expand the real-session sample, confirm the tradeoff findings across sessions, and add focused initial/target-SOC and high-SOC-threshold sensitivity checks. Run a small time-resolution/runtime comparison, such as 30-, 15-, and 5-minute steps on fixed physical horizons. Incorporate presentation feedback before freezing the final analysis. Keep exploratory findings distinct from conclusions supported across the larger sample; do not reopen the project scope or add new model families.

If work slips before November 20, preserve the two stress terms, all four comparison policies, a verified worked example, and the real-session pilot. Reduce the number of weight settings and sensitivity scenarios before cutting any core model. If needed, move the compact sensitivity study after the presentation and state that explicitly. The presentation should communicate the complete project question and approach, with completed work and remaining experiments clearly distinguished.

External degradation-model validation, such as BLAST-Lite integration, is removed from the implementation schedule. Discuss independent battery validation as a limitation/future direction. The final report should distinguish the mathematical improvement in a chosen stress proxy from an independently validated improvement in battery health.

## 8. Work packages and schedule

### Three-member ownership

Members A/B/C are placeholders for the actual team members. Assign the strongest optimization programmer to B; the other two roles also include substantive technical work. All members write and present their own material and review one another's outputs.

| Member | Main responsibility | Concrete outputs by Nov 20 | Final-report/software ownership |
| --- | --- | --- | --- |
| A: model, theory, and independent checks | Define exactly what is optimized; review roughly 3-5 relevant sources; justify assumptions; derive convexity and a compact gradient/Hessian/KKT treatment; independently check saved schedules and interpret limitations | One agreed formulation/specification by Nov 15; analytic toy-case expectations and metric/feasibility checker by Nov 17; verified results and model/theory notes by Nov 20 | Introduction/related work, formulation/theory, discussion of assumptions and battery-health limitations; independently reproduce key results |
| B: optimization and baseline implementation | Build one shared solver function for M0/M1/M2 plus immediate charging; implement fixed terminal energy, constraints, deterministic price-only tie handling, solver status and saved outputs | Working example by Nov 16; all four strategies and output interface by Nov 17; robust pilot runs and numerical fixes by Nov 20 | Implementation/method section, runtime/time-resolution study, dependency records and executable reproduction commands |
| C: data, experiments, and visual comparison | Obtain/clean real sessions; construct transparent synthetic prices/scenarios; run common weight sweeps; compute paired comparisons; prepare plots and focused sensitivity results | Data access confirmed by Nov 15; 10-20 cleaned sessions and experiment configuration by Nov 17; tradeoff plot, pilot table, schedule figure, and compact sensitivity output by Nov 20 | Data/experimental setup and results sections, expanded session/parameter studies, final tables and figures |

Keep work parallel from the first day. B starts with the illustrative constants already specified in this plan; C does not wait for the solver to obtain data; A does not wait for experimental results to review the model and create analytic checks. A and B settle open modeling questions by November 15 so the core implementation can stabilize.

### Shared input/output agreement and handoffs

- On November 14 agree the field names, units, and storage format. Inputs include session identifier, interval duration(s), prices, battery capacity/efficiency assumptions, power limit, initial/target SOC, threshold, and objective weights. Outputs include p_t, s_t, electricity expense, both recomputed stress scores, target/bound residuals, solver status, and runtime. Keep observed data separate from assumed inputs.
- By November 15, A provides a short model specification and expected toy-case values; C provides a few session records; B can already run synthetic inputs.
- By November 17, B provides a working single-session optimization function and saved example output; C uses it in the experiment runner; A checks the output independently. C can develop data preparation and plotting against the agreed schema before this handoff.
- By November 19, C supplies draft comparison figures/table; A checks the interpretation and fairness, B resolves solver issues, and all members review the plots.
- By November 20, freeze the presentation result set and save the configurations used. Continue only correctness fixes before Nov 24; use later weeks for broader experiments.
- Use a shared repository/folder and a short daily check-in through Nov 20. Record each member's actual contributions. Each person drafts their own report methods/results notes alongside the work, rather than waiting until December.

| Period, 2026 | Milestone |
| --- | --- |
| Nov 14 | Assign A/B/C; settle the default scope/stack/input-output schema; A begins model review, B starts the worked example, C starts data access |
| Nov 15 | Finalize the formulation and initial weights/assumptions; confirm data access; agree analytic expectations and comparison rules |
| Nov 16-17 | B completes all four strategies; C freezes 10-20 cleaned sessions and the experiment grid; A checks the worked example and flat-price case; integrate by Nov 17 |
| Nov 18-19 | Run the real-session pilot, weight sweep, and focused sensitivity study; generate draft figures/table; resolve errors and document assumptions |
| Nov 20 | Original results checkpoint: verified comparison results, four compact result outputs, supported initial conclusions, and saved reproduction configurations |
| Nov 21-23 | Original slide/rehearsal period: finish a 15-20-minute team presentation and rehearse with coordinated handoffs |
| Nov 24 | Give the project presentation; record feedback and distinguish completed results from remaining studies |
| Nov 25-30 | Incorporate feedback; aim for approximately 50-100 sessions using the existing pipeline; check tradeoff/model-comparison findings across sessions |
| Dec 1-6 | Complete focused SOC/threshold sensitivity and time-resolution/runtime studies; freeze final figures and conclusions |
| Dec 7-10 | Complete the 8-12-page report, member contributions, references, README, and software package |
| Dec 11-12 | Reproduce results from a clean environment; proofread and aim to submit both deliverables early |
| Dec 13, 11:59 p.m. | Official final report/software deadline |

The team presentation is confirmed for November 24. The handout specifies a 15-20-minute project presentation and says additional details will be announced later; it does not explicitly require every experiment or the final report/software to be finished by that date. Our plan therefore aims for a substantive presentation with actual results, while reserving later weeks for broader evaluation and final deliverables. Any subsequent instructor presentation instructions take precedence over this planning interpretation.

The report/software deadline is December 13, 2026, 11:59 p.m. Use the course's stated deadline timezone; the PDF itself does not specify one. It states that lateness/extensions are not allowed. Team/topic registration was due October 17, so verify that this topic is registered or appropriately updated.

### November 20 readiness checkpoint

- The implementation solves the worked example and approximately 10-20 pilot sessions, with feasibility and solver status recorded.
- Immediate charging, price-only, rate-aware, and combined battery-aware schedules deliver equal energy under identical physical constraints.
- The team can explain the objective, constraints, convexity, solver choice, and limitations of the battery-stress proxies.
- One representative power/SOC plot, one tradeoff plot, one pilot-results table, and a compact charging-window/price sensitivity output are reproducible from saved configurations. If the sensitivity output must move after the presentation, retain the other three and state the unfinished work explicitly.
- Initial conclusions are grounded in available results; broad sensitivity analysis and final-scale evaluation have explicit follow-up tasks.

This checkpoint is an internal readiness target. It does not imply that experiments have already been completed or that the rubric mandates these exact outputs by November 20.

### Suggested November 24 presentation structure

Aim for approximately 18 minutes of prepared material within the stated 15-20-minute duration, adjusted if the instructor supplies a separate question-time rule. Use approximately 12 substantive slides for the whole team, about four per member. Keep longer derivations as backup material. Each member presents their technical contribution and understands the common research question.

| Member and content | Approximate time | Evidence to include |
| --- | ---: | --- |
| A: problem, related approaches, contribution, and formulation | 6 min | Overnight example; objective and constraints; roles of both stress penalties; concise convexity explanation |
| B: solution approach, verification, and worked-example comparisons | 6 min | One solver pipeline; four strategies; equal-energy/feasibility checks; power and SOC comparison with an explanation of the schedules |
| C: data, empirical comparisons, sensitivity, and conclusions | 6 min | Observed versus assumed inputs; pilot table; weight tradeoff plot; compact sensitivity findings; limitations and work through Dec 13 |

Cover the overall project narrative, but label preliminary results and outstanding experiments accurately. A polished final report and every planned sensitivity study are not internal prerequisites for this presentation.

## 9. Report and software deliverables

Target approximately 10-11 pages within the required 8-12-page, single-spaced, letter-size limit. Unless clarified otherwise, budget references inside that limit.

| Section | Approximate pages |
| --- | ---: |
| Abstract and introduction | 1.0 |
| Related theory and practice, including model pros/cons | 1.0 |
| Formulation and battery-model assumptions | 2.0 |
| Solution method, convexity, and verification | 1.5 |
| Data and experimental setup | 1.0 |
| Results and comparisons | 2.0 |
| Discussion, limitations, conclusions, future work | 1.0 |
| Member contributions and references | 1.0-1.5 |

Submit the report as one PDF through Canvas. The handout separately requires emailing the implemented software package to the TA at cai.d@wustl.edu and copying all group members. This plan does not send any messages or submit anything.

The package should contain the solver/model, baseline policies, data-preparation script, experiment configurations, plotting scripts, dependency versions, and a README with clear commands to reproduce every reported figure/table. Include permitted input snapshots or precise acquisition instructions, fixed random seeds for synthetic cases, and saved configurations/results. Avoid lengthy raw program output in the report.

## 10. Initial references and research tasks

- Course requirements: supplied Project_CSE543.pdf, especially application requirements on page 4 and submission/report requirements on page 2.
- Caltech ACN-Data: https://ev.caltech.edu/dataset.html — session fields, acquisition methods, and timestamp cautions.
- Lee et al., ACN-Data: Analysis and Applications of an Open EV Charging Dataset: https://authors.library.caltech.edu/records/yvh76-f6d35 — dataset publication and application examples.
- BLAST: Battery Lifetime Analysis and Simulation Tool Suite: https://www.nlr.gov/transportation/blast — degradation-model factors and model scope.
- Electric vehicle charge optimization including effects of lithium-ion battery degradation: https://ieeexplore.ieee.org/document/6043046/ — starting paper for the model survey; read the full accessible paper before borrowing an equation or claiming replication.
- CVXPY quadratic-program example: https://www.cvxpy.org/examples/basic/quadratic_program.html — QP structure and dual-variable interpretation.
- CVXPY solver documentation: https://www.cvxpy.org/tutorial/solvers/ — compatible solver selection.
- IPOPT documentation: https://coin-or.github.io/Ipopt/index.html — optional existing NLP solver.

Before freezing the model, read a small set of directly relevant charging/degradation papers and compare their equations, calibration needs, optimization difficulty, and applicability to AC charging. If the selected chemistry or power regime does not support a strong power-stress effect, explain that limitation or revise the proxy before running the main study.

## Immediate next steps

1. November 14: assign the three roles, choose one implementation stack, and start model review, solver coding, and data preparation in parallel.
2. November 15: lock the core formulation, confirm an accessible data source, and agree on inputs/outputs and comparison rules.
3. November 16-17: integrate the four strategies, 10-20 cleaned sessions, and independent correctness checks.
4. November 18-20: complete the weight study, pilot comparisons, and focused sensitivity output; save the result set and prepare defensible initial conclusions.
5. Keep November 21-23 for slides/rehearsal and November 24 for the presentation. Use November 25-December 6 for expanded evaluation, December 7-10 for final writing/packaging, and December 11-12 for reproduction and early submission. The official deadline remains December 13 at 11:59 p.m.
