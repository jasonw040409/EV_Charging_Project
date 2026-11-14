# Model specification and evidence audit

Verified November 14, 2026. This is a worked modeling study, not battery-health validation.

## Evidence and model selection

Selected: **Naumann calendar capacity-loss model for Sony US26650FTC1, LFP/graphite, 3 Ah cylindrical cells**. Original article: Naumann, Schimpe, Keil, Hesse, Jossen (2018), *Analysis and modeling of calendar aging of a commercial LiFePO4/graphite cell*, Journal of Energy Storage 17, 153–169, [DOI](https://doi.org/10.1016/j.est.2018.01.019).

**Full text actually verified:** Naumann's 2018 author dissertation, *Techno-economic evaluation of stationary battery energy storage systems with special consideration of aging*, [TUM full text](https://mediatum.ub.tum.de/doc/1434981/document.pdf), Chapter 5, printed pp. 69–75, Table 5.1 (printed p. 74; PDF page 92). Equation numbers below are **dissertation numbers**, not article numbers. The article's repository landing page and DOI were found, but the article PDF was not obtained. Do not describe this as full-text verification of the journal article.

**Implementation cross-check:** [official TUM SimSES calendar source, pinned revision d8bb790](https://github.com/tum-ees/simses/blob/d8bb7906ed58bb47be531f09e031ad6f4bf5ee39/src/simses/model/degradation/sony_lfp_calendar.py). The capacity coefficients, cubic SOC dependence and virtual-time continuation agree with the dissertation. A local reference copy is under `sources/`. SimSES uses R=8.3144598; we retain the dissertation's R=8.314. The resistance branch is excluded; notably the checked implementation has a squared SOC expression, while the inspected BLAST resistance branch has a cubic expression. We do not conflate these branches or use resistance estimates.

Why this choice: accessible primary full text, few explicit coefficients, clear history dependence, no voltage/SOC reconstruction or uncertain cycle closure needed for an isolated charging event. Tradeoff: **calendar loss only**. It cannot test a charging-rate damage hypothesis. The power penalty remains a separate scheduling proxy. The original calendar experiments stored cells; applying their law during charging is an additional quasi-static assumption, not validated by these optimization results.

Candidate disposition:

| Candidate | Evidence checked | Decision |
|---|---|---|
| Naumann 2018 | Author dissertation full text; official capacity implementation | Implement calendar capacity component now |
| Schmalstieg 2014 | [Original-paper DOI/abstract](https://doi.org/10.1016/j.jpowsour.2014.02.012); full paper not verified | Defer; do not copy coefficients from reviews or invent voltage curves |
| Naumann cycle model | Dissertation cycle chapter and official SimSES source located | Defer until independent verification of C-rate units, percent conversion, partial cycles, history and domain |
| BLAST Sony model | [Official source](https://github.com/NatLabRockies/BLAST-Lite/blob/main/blast/models/lfp_gr_SonyMurata3Ah_2018.py) inspected | A reidentified capacity model, not the original Naumann law; avoid labeling it Naumann 2018 |
| Montes 2024 | Not full-text verified in this work | No equations or coefficients used |

## Published law, units, and history

Let q be lost capacity as a **fraction of initial capacity**, s the SOC fraction, T the cell temperature in kelvin, and t elapsed time in **seconds**. At fixed conditions:

```
q(t) = k(T,s) sqrt(t)                                      [Eq. 5.1]
k(T,s) = k_ref exp[-Ea/R (1/T - 1/T_ref)] g(s)              [Eq. 5.3]
g(s) = c (s - 0.5)^3 + d                                  [Eq. 5.12]
```

| Parameter | Implemented value | Units / interpretation |
|---|---:|---|
| k_ref | 1.2571e-5 | fraction / sqrt(second) |
| Ea | 17126 | J/mol |
| R | 8.314 | J/(mol K) |
| T_ref | 298.15 | K |
| c | 2.8575 | dimensionless |
| d | 0.60225 | dimensionless |

Table 5.1 reports k_ref=0.0012571 **percent** per sqrt(second); dividing by 100 gives the implemented coefficient. Percent loss, fractional loss, and ppm must not be interchanged. We report increments in ppm of original capacity (fraction times 1e6), not percent lifetime gained.

For a history state q_old and current stress k, Eq. 5.17 gives virtual time `t_virtual=(q_old/k)^2`. Exact constant-stress continuation is

```
q_new = sqrt(q_old^2 + k^2 delta_seconds).
```

This follows by integrating Eq. 5.15 with virtual time; it is not a new fitted damage equation. For varying s within a constant-power interval, integrate `k(T,s(t))^2` over actual seconds. At constant T the integrand is degree six in the linearly varying SOC. Four-point Gauss–Legendre quadrature integrates it exactly to floating-point precision. This avoids midpoint/end-point approximation error in this evaluator. Do **not** add `k sqrt(delta_t)` independently each interval. Do not reset q between intervals or between sequential sessions.

Default assumed history: 365 days at 25 C and SOC 0.5; `prior_loss` computes q_old with the same published law. This is an explicit synthetic prehistory shared by all schedules, not observed vehicle age or total SOH. Calendar-loss state is sufficient for this component's continuation; chronological age alone is insufficient if past stress is unknown. A measured total SOH cannot be assigned wholly to calendar fade without justification. Cycling throughput is **not** an input to this selected component; cumulative cycle usage and cycling loss are unmodeled, not silently assumed to be a verified zero. Never restart from a fresh cell to compare successive real-world sessions.

## Tested conditions and limits

The dissertation describes an 885-day calendar study. Static storage temperatures include 0, 10, 25, 40, 60 C, with nine SOC levels from 0 to 100% at 40 C; not every temperature/SOC combination was tested. Arrhenius fitting uses 25, 40 and 60 C because low-temperature measurements were ambiguous relative to the small losses. SOC fitting uses the 40 C data at the end of the study. Dynamic validation switches storage conditions on roughly monthly timescales (Chapter 5.1.3), not every 15 minutes. Early reversible capacity behavior associated with anode overhang is omitted. Extrapolation to a 12-hour scheduling difference is particularly uncertain relative to experimental errors.

Code rejects temperatures outside the studied 0–60 C envelope and SOC outside 0–1; this envelope is not a claim of uniform accuracy inside it. All present experiments use 25 C and s=0.3–0.8. A 60-kWh pack is assigned the cell's normalized response without a pack calibration. Fixed usable capacity, temperature, efficiency and linear SOC dynamics omit tapering, thermal behavior, plating, resistance, imbalance and capacity feedback. This evaluator predicts **conditional incremental calendar capacity loss**, not total degradation, lifetime, safety, or measured health improvement.

## Scheduler and surrogate objective

Grid power p_t in kW, interval dt in hours, E=60 kWh, eta=0.9:

```
s_(t+1) = s_t + eta p_t dt / E
0 <= p_t <= 7.2; 0 <= s_t <= 0.9
s_0=0.3; s_N=0.8
```

For every strategy, battery energy is exactly 30 kWh and grid energy 33 1/3 kWh; the last immediate-charging interval can be partial-power. Minimum full-power duration is 4.62963 hours. Whole window is 18:00–06:00, 48 intervals, dt=0.25 h. No export/discharge. Physical feasibility requires E(s_goal-s_init)<=eta P_max N dt.

```
C = dt sum(price_t p_t)                         dollars
D_P = (1/N) sum((p_t/P_max)^2)                  dimensionless
D_S = (1/N) sum((max(s_(t+1)-0.7,0)/0.3)^2)      dimensionless
objective = C/C_ref + lambda_P D_P + lambda_S D_S
```

D_S uses end-of-slot SOC, a conservative approximation to continuous exposure during monotone charging, including waiting. It is a proxy distinct from the continuously integrated published evaluator. C_ref=max(abs(immediate cost),$1) is fixed for each instance across weights. Threshold 0.7 and weights are assumptions; no damage calibration is claimed.

Synthetic prices: 18:00–22:00 $0.30/kWh; 22:00–03:00 $0.10; 03:00–06:00 $0.24. These are not a utility tariff. Strategies: immediate; cost-only; power penalty (1,0); combined (1,10). The 12-pair sweep uses lambda_P in {0,0.1,1,10}, lambda_S in {0,1,10}. Weights were illustrative choices, not fitted after a health outcome.

Primary stack: CVXPY with CLARABEL only. Cost-only first minimizes C, then minimizes D_P within **$1e-8** of the minimum cost. This documented tolerance-based lexicographic rule resolves equal-price ambiguity and uniquely spreads charging within equally cheap slots. The secondary objective is not a claim that all cost-only controllers behave this way. Solver optimal status and residuals are checked; raw p is saved without clipping or energy repair.

The epigraph variable z>=s-0.7, z>=0 yields a convex quadratic objective with affine constraints. D_P has positive definite Hessian `2 I/(N P_max^2)`; D_S is convex as a squared positive part of an affine SOC. With lambda_P>0 the power schedule is unique. For affine constraints Ap<=b, Bp=e and quadratic objective 0.5 p'Hp+f'p, KKT conditions are feasibility, mu>=0, `Hp+f+A'mu+B'nu=0`, and `mu_i(Ap-b)_i=0`; for epigraph form include z and its constraints. These are the team's basis for an independent derivation, not a reported numerical dual-residual check. Saved residuals are primal constraint violations, with mixed units; separate energy/power/SOC residuals are also saved. Reported solver time is the final stage only; wall time includes both stages and CVXPY construction/solve.

## Mapping and verification

| Formula or role | Code |
|---|---|
| Dynamics, constraints, QP/tie-break | `src/charging.py`, `optimize` |
| Immediate policy and equal energy | `immediate`, `soc_from_power` |
| Published coefficient and history initialization | `src/aging.py`, `stress`, `prior_loss` |
| Eq. 5.17 continuation / exact integral | `evaluate` |
| Saved schedules, metrics and figures | `src/run_example.py` |
| Five-record data audit and pilots | `src/inspect_data.py` |
| Analytic and physical verification | `tests/test_verification.py` |

Checks cover all four physical schedules, exact cheap-slot cost, uniform charging under flat prices for quadratic and tie-broken cost-only cases, invalid/infeasible inputs, percent conversion, constant-stress closed form, history splitting, identical-path timestep refinement, and waiting after charging. This verifies implementation against mathematics; it does not validate the cell model on new battery measurements.

Research corrections carried forward: Wang's generalized model has rate-dependent parameters; arXiv:2205.15440 is Maheshwari-inspired, not Wang; SSRN 6773556 was posted May 2026. These are user-supplied corrections, not independently full-text verified claims here, and none supplies equations used in code. Delivered energy plus capacity does not identify initial SOC. Agreement or disagreement between models is a robustness study, never proof of improved real battery health.
