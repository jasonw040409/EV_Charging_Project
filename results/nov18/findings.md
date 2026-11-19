# Executed study: what to read tonight

Generated November 18, 2026. Automated checks passed; human interpretation, independent model review and independent reproduction remain incomplete.

- 15 recorded sessions; 236 successful schedules are simulated alternatives, not 236 independent observations.
- Five hypothetical SOC cases were analytically infeasible; none had its energy reduced. No numerical/evaluation failures were recorded.
- All 224 saved power/SOC trajectories passed recomputed dynamics, energy, target and power-bound checks; flat-price uniform charging and inactive combined/power-only agreement passed.
- Calendar numbers are provisional model estimates, not measured lifetime improvement.

## Clean paired real-session comparisons

Change means combined minus cost-only on the same session and assumed initial SOC. Negative exposure change is a smaller score; positive cost premium is extra spending. Flagged original control is omitted here and retained in raw outputs.

| Assumed starting SOC | Feasible clean paired cases | Median cost premium ($) | Median high-SOC score change | Median calendar change (ppm) |
|---|---:|---:|---:|---:|
| 30% | 14 | -0.000000 | 0.000000 | 0.000000 |
| 60% | 14 | -0.000000 | -0.000000 | -0.000000 |
| 75% | 9 | -0.000000 | -0.054117 | -0.942140 |

## Synthetic sensitivity: cost versus exposure

Each row keeps four methods; the table selects cost-only and combined to show the tradeoff. Synthetic window/price variants are hypothetical, separate from real sessions. Threshold variants report different score definitions and should not be ranked by raw score across thresholds.

| Case | Cost-only cost ($) | Combined cost ($) | Cost-only exposure | Combined exposure | Combined total wall time (s) |
|---|---:|---:|---:|---:|---:|
| baseline | 3.3333 | 4.2707 | 0.032118 | 0.005289 | 0.01107 |
| flat | 6.6667 | 6.6667 | 0.008605 | 0.004739 | 0.01068 |
| late_cheap | 3.3333 | 3.5317 | 0.004340 | 0.004135 | 0.01068 |
| window_5h | 8.5600 | 8.5600 | 0.009892 | 0.009892 | 0.00855 |
| window_8h | 4.2400 | 4.7905 | 0.006183 | 0.006202 | 0.00969 |
| window_12h | 3.3333 | 4.2707 | 0.032118 | 0.005289 | 0.00975 |
| threshold_0.6 | 3.3333 | 4.8877 | 0.079102 | 0.017772 | 0.01036 |
| threshold_0.7 | 3.3333 | 4.2707 | 0.032118 | 0.005289 | 0.01028 |
| threshold_0.8 | 3.3333 | 3.8263 | 0.000000 | 0.000000 | 0.01022 |
| soc_0.2_0.8 | 4.5600 | 5.2139 | 0.015838 | 0.004969 | 0.01045 |
| soc_0.5_0.8 | 2.0000 | 2.6556 | 0.034138 | 0.007102 | 0.01042 |
| soc_0.3_0.9 | 4.5600 | 5.8118 | 0.093737 | 0.028796 | 0.01019 |
| resolution_60m | 3.3333 | 4.2582 | 0.037037 | 0.010401 | 0.00830 |
| resolution_30m | 3.3333 | 4.2669 | 0.033565 | 0.006805 | 0.00965 |
| resolution_15m | 3.3333 | 4.2707 | 0.032118 | 0.005289 | 0.01049 |
| resolution_5m | 3.3333 | 4.2714 | 0.031261 | 0.004414 | 0.01589 |

## Read these artifacts in order

1. `representative_soc60.png`: S2 at assumed 60% arrival. Explain when each method charges and waits.
2. `paired_tradeoffs.png`: every clean paired case, including zero changes. These are assumed SOC cases on recorded windows under synthetic prices.
3. `weight_tradeoffs.png` and `nondominated_weight_cases.json`: expense, concentration and exposure can compete; no single unexplained health score.
4. `exclusions.json`: five infeasible SOC assumptions, kept visible rather than repaired.
5. `aging_sensitivity.json`: 36 conditional evaluations (four fixed schedules, three current temperatures, three prior ages). Prehistory stays at 25 C/50% SOC; no new schedules are optimized here.

## Remaining interpretation limits

The cohort is a small, deliberately diverse first-page sample, not a population estimate. SOC/capacity/charger/chemistry/temperature and tariffs are assumed. Recorded departure is known in retrospect. Single-run timing is descriptive; hardware noise can outweigh small differences. Runtime includes different problem sizes and cost-only has two stages. Time-resolution changes also change the end-of-slot proxy approximation. No automated check establishes real battery-health improvement.
