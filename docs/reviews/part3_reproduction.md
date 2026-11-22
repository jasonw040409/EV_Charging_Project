# Member 3 · Implementation and reproduction

**Chengze Wu's project track · November 22, 2026 · baseline commit `469c2b1838fbc5e2f2ebd3b2d12b05cf4f7b6af4`.** Automated execution on Windows with Python 3.14 and NumPy 2.5.4. The scheduled energy, expenses, and SOC paths agree with an independent implementation. Exact-environment replay of the original CVXPY/CLARABEL runner remains open.

## Reproducibility checklist

| Check | Local result | Evidence |
|---|---|---|
| Install the original pins | Blocked. pip could not resolve pypi.org. The environment lacked CVXPY and Matplotlib. | `requirements.txt` records the original versions. |
| Run original seven tests | Discovery stopped importing CVXPY. No test body ran. | `replay_original.py` retains the tests log and exit code. |
| Run original synthetic, five-session and November 18 studies | All three exited during import. No fresh CLARABEL results were generated. | Replay helper runs all four commands independently, each with a separate log. |
| Run the existing November 18 summarizer on copied artifacts | Passed its trajectory, flat-price and inactive-penalty checks for 224 trajectories. | `experiments/nov18/summarize_study.py` |
| Rerun the four policies independently | Passed for 160 real-session and 64 synthetic schedules. All 20 original pilot rows also matched on seven physical and economic metrics. | `results/part3/verification.json`, `expansion.json` |
| Recheck sensitivity | All 12 weight-pair objective values agreed within 1e-6. All 36 temperature/history estimates agreed within 1e-8 ppm using polynomial moments. | `verification.json` |
| Expand using frozen records and repeat timing | 50 distinct sessions, 133 feasible scenarios, 532 complete trajectories. Five timed solves per method at each of four resolutions. | `results/part3/` |

## How to run

From the repository root, these commands use NumPy. On Windows the study also needs the IANA time-zone database, available through the Python package `tzdata`.

```sh
python experiments/part3/verify.py
python experiments/part3/study.py --sessions 50
```

The first command checks every saved trajectory before independently solving each case. The second writes the membership, exclusion ledger, complete compressed JSON trajectories, paired differences and timing samples under `results/part3/`. Runtime depends on hardware and background activity.

To reproduce the original stack, start with Python 3.12 in a clean environment and install `requirements.txt` (also install `tzdata` on Windows). Run the following command with a **new** destination. It copies inputs and source, logs each exit code and compares regenerated rows with saved rows by case and method. A failed import or out-of-tolerance metric exits nonzero.

```sh
python experiments/part3/replay_original.py ../ev-original-replay
```

## What was checked

For each path, the verifier checks N power values, N+1 SOC boundaries, interval duration, cumulative SOC, power bounds, final SOC, energy and price-weighted cost. It recomputes both proxies and integrates the calendar law along each linear SOC segment. Computing the polynomial moments independently checks the quadrature implementation, including idle time. Real-session checks derive window length and energy from frozen ACN fields. Starting SOC, capacity, efficiency, power limit and tariff remain assumptions.

The independent solver normalizes power to a fraction of charger capacity. Fixed energy gives a fixed sum of fractions. With nonnegative power and a feasible departure SOC, every intermediate SOC lies between arrival and departure. Immediate charging fills earliest slots. Cost-only fills cheaper slots first and spreads equal-price energy evenly. The original solver allows a $1e-8 cost margin in its second stage. For weighted objectives, projected gradients enforce the fixed sum and power bounds. The best feasible linearized objective gives an upper bound on remaining convex suboptimality. The largest observed normalized gap was 9.01e-10. The largest expense difference across the 224 schedules was $3.85e-8, and the largest calendar difference was 4.98e-8 ppm. A weight pair can have several optimal schedules, so the weight sweep compares objective values.

| Smoke case | Check and result |
|---|---|
| Synthetic overnight | All four schedules deliver 33.3333 grid kWh. Independent expenses in policy order are $9.0933, $3.3333, $3.8263 and $4.2707. |
| Flat synthetic tariff | The analytic uniform power is 33.3333 / 12 = 2.77778 kW. The saved flat-price check and independent solution agree. |
| S2, 60% arrival | 10.013 grid kWh gives a 75.0195% target. Cost-only high-SOC score is 0.007308. Combined gives 0.005699. |
| S3, 60% arrival | The high-SOC score stays zero for every policy. |
| S2, 75% arrival | Target 90.0195% exceeds the 90% cap. The case is in the exclusion ledger. |

## Expansion and presentation notes

1. **Equal-energy comparison.** On the synthetic overnight case, combined charging spends about $0.94 more than cost-only. Both deliver the same 30 battery kWh by departure. The additional cost buys a lower modeled high-SOC score under the selected weights.
2. **Who enters the comparison.** Keep the original 15 records in order. Select 35 more before solving, from Jason's existing eligibility ledger. Cycle through duration/energy bins in ascending order and use connection time then ID within each bin. This is a deterministic extension of one frozen page. Team approval of the extension rule is pending. The manifest records the selected IDs and SHA-256 hashes of the frozen inputs.
3. **Where comparisons are possible.** Simulate 30%, 60% and 75% starts. Of 150 scenarios, 17 would exceed the SOC cap (one at 60%, sixteen at 75%). The remaining 133 have four schedules each. Retain the timing-flagged control in raw results. Removing that control leaves 49, 48 and 33 clean paired cases by starting SOC. Median combined-minus-cost-only calendar changes are effectively zero at 30% and 60%, and −0.8055 ppm at 75%. These are conditional calendar-model estimates from different feasible subsets.
4. **Computational cost.** Use `timing.json` for the independent solver's one warm-up and five measured calls per resolution and policy. The timer covers schedule computation, including the optimality check where applicable. It excludes file I/O and post-evaluation. Historical CLARABEL measurements cover a different implementation and timing scope. A repeated native CLARABEL benchmark and human review remain open.
