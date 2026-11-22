# Member 3 · Implementation and reproduction

**Chengze Wu's project track · November 22, 2026 · baseline commit `469c2b1838fbc5e2f2ebd3b2d12b05cf4f7b6af4`.** Automated execution on Windows with Python 3.14 and NumPy 2.5.4. The scheduled energy, expenses, and SOC paths agree with an independent implementation. Exact-environment replay of the original CVXPY/CLARABEL runner remains open.

## Reproducibility checklist

| Check | Local result | Evidence |
|---|---|---|
| Install the original pins | Recovered SciPy 1.18.1 and Matplotlib 3.11.2 from local wheels. CVXPY 1.9.3 and CLARABEL 0.11.1 were unavailable in the inspected caches. pip could not resolve PyPI. | `results/part3/original_entry_points.json` records versions, commands, exit codes and import errors from the latest replay. |
| Run original seven tests | Discovery stopped importing CVXPY. No test body ran. | `replay_original.py` retains the tests log and exit code. |
| Isolate the solver-independent tests | All four original physics/calendar test bodies passed. Only the eager CVXPY import was moved inside `optimize` in a temporary copy. These results are separate from unmodified test discovery. | `experiments/part3/physics_tests.py`, `results/part3/physics_tests.json` |
| Run original synthetic, five-session and November 18 studies | All three exited during import. No fresh CLARABEL results were generated. | Replay helper runs all four commands independently, each with a separate log. |
| Run the existing November 18 summarizer on copied artifacts | Passed its trajectory, flat-price and inactive-penalty checks for 224 trajectories. | `experiments/nov18/summarize_study.py` |
| Rerun the four policies independently | Passed for 160 real-session and 64 synthetic schedules. All 20 original pilot rows also matched on seven physical and economic metrics. | `results/part3/verification.json`, `expansion.json` |
| Recheck sensitivity | All 12 weight-pair objective values agreed within 1e-6. All 36 temperature/history estimates agreed within 1e-8 ppm using polynomial moments. | `verification.json` |
| Expand using frozen records and repeat timing | 50 distinct sessions, 133 feasible scenarios, 532 complete trajectories. Five timed solves per method at each of four resolutions. | `results/part3/` |
| Cross-check the expansion independently | Reconstructed 532 schedules against the original ACN records. The 133 immediate schedules matched the earliest-slot rule. SciPy HiGHS certified all 399 optimized schedules. Re-evaluated all 532 paths with the original calendar evaluator. | `results/part3/expansion_audit.json` |

## How to run

From the repository root, these commands use NumPy. On Windows the study also needs the IANA time-zone database, available through the Python package `tzdata`.

```sh
python experiments/part3/verify.py
python experiments/part3/study.py --sessions 50
python experiments/part3/audit_expansion.py
python experiments/part3/physics_tests.py
```

The first command checks every saved trajectory before independently solving each case. The second writes the membership, exclusion ledger, complete compressed JSON trajectories, paired differences and timing samples under `results/part3/`. The third needs SciPy. It reads the serialized results and solves a separate linear program for each optimized schedule. Runtime depends on hardware and background activity.

To reproduce the original stack, start with Python 3.12 in a clean environment and install `requirements.txt` (also install `tzdata` on Windows). Run the following command with a **new** destination. It copies inputs and source, logs each exit code and compares regenerated rows with saved rows by case and method. A failed import or out-of-tolerance metric exits nonzero.

```sh
python experiments/part3/replay_original.py ../ev-original-replay
```

A successful baseline replay automatically checks the 532 expansion paths against the original solver, then records one warm-up and five fresh original-solver runs at each resolution and policy in the destination's `native_results.json`. Those two native steps remain pending until CVXPY and CLARABEL are installed. The latest local failure log is in `results/part3/original_entry_points.json`.

## Code and equation cross-check

| Location | Implementation and check |
|---|---|
| `src/charging.py`, `Scenario.grid_energy` and `soc_from_power` | Grid energy is capacity times SOC gain divided by efficiency. Each SOC increment uses grid kW times hours times efficiency divided by capacity. Reconstructing expanded schedules from the raw source gave a maximum grid energy error of 4.71e-14 kWh. |
| `src/charging.py`, `optimize` | Cost-only first minimizes price-weighted energy, then spreads power within a $1e-8 cost margin. The independent solution spreads power evenly within the exact cheapest-price solution. HiGHS bounded the largest expanded cost-only optimality gap at 2.23e-15 dollars. |
| `experiments/nov18/run_study.py`, real-session loop | The code derives target SOC separately at every arrival SOC. S2's 10.013 kWh raises SOC by 15.0195 percentage points for each arrival assumption. |
| `src/aging.py`, `evaluate` | The original function integrates over the entire connected window including idle slots. Across all expanded paths, comparison to independently integrated polynomial moments gave a maximum difference of 4.98e-14 ppm. |

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

The three editable slides in `part3_slides.pptx` include English speaker notes, evidence filenames and the timing method.

1. **Equal-energy comparison.** On the synthetic overnight case, combined charging spends about $0.94 more than cost-only. Both deliver the same 30 battery kWh by departure. The additional cost buys a lower modeled high-SOC score under the selected weights.
2. **Who enters the comparison.** Keep the original 15 records in order. Select 35 more before solving, from Jason's existing eligibility ledger. Cycle through duration/energy bins in ascending order and use connection time then ID within each bin. This is a deterministic extension of one frozen page. Team approval of the extension rule is pending. The manifest records the selected IDs and SHA-256 hashes of the frozen inputs.
3. **Where comparisons are possible.** Simulate 30%, 60% and 75% starts. Of 150 scenarios, 17 would exceed the SOC cap (one at 60%, sixteen at 75%). The remaining 133 have four schedules each. Retain the timing-flagged control in raw results. Removing that control leaves 49, 48 and 33 clean paired cases by starting SOC. Median combined-minus-cost-only calendar changes are effectively zero at 30% and 60%, and −0.8055 ppm at 75%. These are conditional calendar-model estimates from different feasible subsets.
4. **Computational cost.** Use `timing.json` for the independent solver's one warm-up and five measured calls per resolution and policy. The timer covers schedule computation, including the optimality check where applicable. It excludes file I/O and post-evaluation. Historical CLARABEL measurements cover a different implementation and timing scope. A repeated native CLARABEL benchmark and human review remain open.
