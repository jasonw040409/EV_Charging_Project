# Automated experiment summary

Sessions: 15; attempted cases: 73; schedules and saved paths: 236; complete unflagged paired cases: 37; post-evaluations: 36.
Failures/exclusions: {'infeasible_assumed_scenario': 5}. Flagged timing records remain in metrics and are excluded from paired summaries.

## Paired combined minus cost-only

| Start SOC | Metric | Count | Median | Q1 | Q3 |
|---:|---|---:|---:|---:|---:|
| 30% | cost_dollars | 14 | -7.4199e-13 | -9.98769e-09 | -9.07885e-14 |
| 30% | power_proxy | 14 | -2.60447e-15 | -1.18198e-14 | 2.14636e-10 |
| 30% | high_soc_proxy | 14 | 0 | 0 | 0 |
| 30% | calendar_increment_ppm | 14 | 1.52706e-10 | 1.81388e-12 | 3.16826e-09 |
| 60% | cost_dollars | 14 | -4.17305e-13 | -7.35441e-09 | -2.40044e-13 |
| 60% | power_proxy | 14 | 1.2849e-10 | -1.27426e-14 | 0.00527692 |
| 60% | high_soc_proxy | 14 | -1.83652e-16 | -0.00186939 | 0 |
| 60% | calendar_increment_ppm | 14 | -1.0945e-11 | -0.246947 | -1.82965e-13 |
| 75% | cost_dollars | 9 | -4.49363e-13 | -1.00076e-12 | -1.10356e-13 |
| 75% | power_proxy | 9 | 0.0486253 | 0.0294867 | 0.0631186 |
| 75% | high_soc_proxy | 9 | -0.0541169 | -0.0665022 | -0.01985 |
| 75% | calendar_increment_ppm | 9 | -0.94214 | -1.73917 | -0.411177 |

## Repeated solve timings

Each cell is the median outer call time in seconds; see timing.json for individual runs and scores.

| Resolution (min) | Method | Runs | Median seconds |
|---:|---|---:|---:|
| 60 | cost_only | 5 | 0.018718 |
| 60 | power_penalty | 5 | 0.010578 |
| 60 | combined | 5 | 0.010865 |
| 30 | cost_only | 5 | 0.021099 |
| 30 | power_penalty | 5 | 0.011140 |
| 30 | combined | 5 | 0.011611 |
| 15 | cost_only | 5 | 0.022805 |
| 15 | power_penalty | 5 | 0.012480 |
| 15 | combined | 5 | 0.013150 |
| 5 | cost_only | 5 | 0.034749 |
| 5 | power_penalty | 5 | 0.018089 |
| 5 | combined | 5 | 0.020579 |

Synthetic prices and assumed SOC; no measured health claim. Timings include construction and solve, not aging or file output. Cost-only has two solves; solver-reported time is its final stage only.
