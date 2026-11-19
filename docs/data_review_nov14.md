# Five-session data review and November 15 checkpoint proposal

Prepared November 14, 2026 for the member responsible for data review, interpretation, and next experiments. **This is a review and proposal, not a change to the baseline.** The battery-model and implementation owners retain their existing files and decisions.

## What the pilot tells us

We have **five recorded charging sessions**, all starting on April 25, 2018 at the Caltech site. A session is one recorded plug-in visit; it is not necessarily a different vehicle or driver. Applying four scheduling methods to each session produced **twenty simulated schedules**. Twenty schedules do not mean twenty independent observations.

The pilot shows that the software can match recorded energy within recorded connection windows under our assumptions. It does not yet show an advantage from the high-charge penalty: every simulated battery stays below its 70% threshold. The published calendar-aging estimates are positive anyway, because that evaluator is a different calculation without a 70% cutoff. All four methods also have essentially equal electricity costs in these five cases. This is a useful control sample, but a weak sample for demonstrating a cost–stress tradeoff.

Today's inspection checked the actual repository files, not an earlier chat summary. No applicable AGENTS.md was found in the repository or checked parent directories. The read-only audit script and its outputs are in `reviews/nov14/`. No API requests, new optimizer solves, or large sweeps were run today. Existing code, assumptions, data and results were left unchanged.

## A real session, step by step

Use **S2**, session `2_39_95_27_2018-04-25 13:45:09.617470`, raw record `_id=5bc90cb9f9af8b0d7fe77cd3`, station `2-39-95-27`, space `CA-319`.

**State of charge (SOC)** means the battery's charge level as a percentage of its usable capacity, like a fuel gauge. **Energy**, measured in kilowatt-hours (kWh), is the amount delivered. **Power**, measured in kilowatts (kW), is how quickly energy is delivered. For example, 2 kW sustained for 3 hours delivers 6 kWh. A car can remain plugged in long after energy delivery stops.

The source timestamps say this car connected at **06:45:10 on April 25, 2018**, and disconnected at **17:56:16 that day**, in the source site's `America/Los_Angeles` timezone (PDT, UTC−07:00). These correspond to **13:45:10 UTC April 25** and **00:56:16 UTC April 26**. The apparent next-day departure in UTC is not an overnight local session. These source-local times are intentionally not converted to our team's Chicago timezone.

The available window was **11 hours, 11 minutes, 6 seconds**. The recorded delivered energy was **10.013 kWh**. The raw `doneChargingTime` is 16:44:15 UTC, or **09:44:15 local**, well before unplugging. We use disconnect time as the end of availability, rather than shortening the window to when historical charging stopped. That allows simulated schedules to finish later. It assumes the recorded disconnection is known in advance: this is **retrospective known-departure evaluation**, meaning we use information now available after the event, not a prediction a live controller would necessarily know.

The pilot **assumes** a 60-kWh battery arriving at 30% SOC, 90% charging efficiency, and a 7.2-kW grid-power limit. None of these is measured in this record. Treating the delivered energy as grid-side, 90% efficiency means 9.0117 kWh reaches the battery. The other 10% is modeled as charging loss.

The final SOC is derived as follows:

1. Assumed energy on arrival: `60 × 0.30 = 18 kWh`.
2. Modeled energy added: `10.013 × 0.90 = 9.0117 kWh`.
3. Modeled final energy: `18 + 9.0117 = 27.0117 kWh`.
4. Derived final SOC: `27.0117 / 60 = 0.450195`, or **45.0195%**.

Thus 45.0195% is an **assumption-based simulation target**, not an observed battery reading or the driver's requested target. Delivered energy and an assumed capacity cannot reveal the actual starting SOC. `userInputs` is null here, so the requested energy and requested departure are unavailable.

The four simulated schedules answer different questions about delivering the same energy:

| Method | Plain-language meaning |
|---|---|
| Immediate | Start at the assumed maximum power, finish the energy requirement, then wait plugged in. The final active interval may use less than maximum power. |
| Cost-only | Minimize the synthetic electricity bill. When several equally cheap choices exist, the documented tie-break spreads charging by minimizing squared power within $0.00000001 of the cheapest bill. |
| Power penalty | Balance the bill with a penalty for concentrating power. This is a scheduling preference, not a calibrated damage equation. |
| Combined | Use the same power penalty and add a penalty for spending time above 70% SOC. Here it adds no meaningful effect because SOC remains below 70%. |

For S2, all four cost approximately **$1.50195** under the synthetic tariff. Immediate charging peaks at 7.2 kW; the optimized schedules peak at about 1.0601 kW. The saved calendar estimates are about **27.0220 ppm** for immediate and **26.5586 ppm** for the optimized methods. A ppm is one millionth of original capacity; these are small, conditional model estimates, not measured damage. They do not establish longer battery life.

The original record provides energy and event times, not the historical power trace in this saved response. We are not claiming that the driver actually followed any of these four simulated schedules.

## All five recorded sessions

All times below are **April 25, 2018, Los Angeles local time, PDT (UTC−07:00)**. Durations use the raw event timestamp fields. Final SOC assumes 30% arrival, 60 kWh capacity and 90% efficiency.

| Label / space | Connected | Disconnected | Available time | Delivered energy (kWh) | Derived final SOC | Quality note |
|---|---|---|---|---:|---:|---|
| S1 / CA-496 | 04:08:04 | 06:20:10 | 2:12:06 | 7.932 | 41.8980% | Charging-stop time is 60 seconds after disconnect |
| S2 / CA-319 | 06:45:10 | 17:56:16 | 11:11:06 | 10.013 | 45.0195% | No stop/departure ordering flag |
| S3 / CA-489 | 06:45:50 | 16:04:45 | 9:18:55 | 5.257 | 37.8855% | No stop/departure ordering flag |
| S4 / CA-327 | 07:37:06 | 16:55:34 | 9:18:28 | 5.177 | 37.7655% | No stop/departure ordering flag |
| S5 / CA-490 | 07:40:34 | 16:03:12 | 8:22:38 | 10.119 | 45.1785% | No stop/departure ordering flag |

Use these exact identifiers to join the table to the raw JSON and saved results:

| Label | Full sessionID | Raw `_id` |
|---|---|---|
| S1 | `2_39_78_362_2018-04-25 11:08:04.400812` | `5bc90cb9f9af8b0d7fe77cd2` |
| S2 | `2_39_95_27_2018-04-25 13:45:09.617470` | `5bc90cb9f9af8b0d7fe77cd3` |
| S3 | `2_39_79_380_2018-04-25 13:45:49.962001` | `5bc90cb9f9af8b0d7fe77cd4` |
| S4 | `2_39_79_379_2018-04-25 14:37:06.460772` | `5bc90cb9f9af8b0d7fe77cd5` |
| S5 | `2_39_79_381_2018-04-25 14:40:33.638896` | `5bc90cb9f9af8b0d7fe77cd6` |

Some timestamp-like text embedded in sessionID differs slightly from the event fields. For example, S2's identifier ends in `13:45:09.617470`, while its `connectionTime` says `13:45:10 GMT`. Use the timestamp field to calculate time and the identifier only for tracing; do not silently replace one with the other.

## Recorded inputs versus assumptions

| Input | What is actually available | Interpretation rule |
|---|---|---|
| Plug-in and unplug timestamps | Present for all five, with source timezone | Preserve actual dates/windows; no shifting to overnight hours |
| Delivered energy | `kWhDelivered`, present for all five | Match this amount in the replay; treating it as grid-side is the pilot's convention |
| Historical charging-stop timestamp | Present for all five | Distinct from unplug time; S1 is inconsistent by 60 seconds |
| Site/station/session identifiers | Present; one site and five distinct stations | Five sessions do not establish five distinct vehicles |
| User inputs and user ID | Both null for all five | Requested energy, requested departure and driver identity unavailable |
| Battery capacity, initial SOC and target | Capacity/arrival assumed; target calculated | Label every simulated SOC as assumed or derived |
| Power limit / efficiency | Assumed 7.2 kW / 90% | Feasibility is conditional on these values, not a statement about actual hardware |
| Tariff | Synthetic $0.30/kWh from 16:00–21:00 local, otherwise $0.15 | No observed bill or actual utility tariff is present |
| Chemistry / temperature | Assumed cell-specific LFP response / constant 25°C | No measured chemistry or thermal trace is present |
| Prior aging history | Assumed 365 days at 25°C and 50% SOC | Shared initial calendar-loss state, not measured age or total battery health |

The source response is a five-record first-page convenience sample, with no random sampling documented. All five start on one day, four have long daytime windows, and all delivered energies are approximately 5–10 kWh. It is too small and narrow for a population-level conclusion. Its saved API metadata describes that snapshot, not current dataset size or current access availability.

## Why the high-SOC penalty is zero

This finding follows from the current implementation, not just the README:

- `src/inspect_data.py` sets each target to `.3 + .9 * energy / 60`. It inherits `initial=.3` from `Scenario` in `src/charging.py`.
- `Scenario.reference_soc` is `.7`. Reported `high_soc_proxy` uses only the amount **above** this threshold at each interval end, squares it, and averages it over the full connection window. At or below 70%, the contribution is zero.
- Charging is unidirectional: the model does not discharge the battery. With nonnegative power and a fixed departure target, SOC cannot rise above its target and then fall again.
- Targets range from **37.7655% to 45.1785%**. Therefore no feasible path in any of these five cases reaches 70%.

For reference, starting from 30%, more than **26.6667 grid kWh** would be needed to end above 70% under the same capacity/efficiency assumptions. None of these records supplies that amount. This arithmetic is an explanation, not a reason to discard the lower-energy records.

Power-only uses weights (1,0); combined uses (1,10) for power and high-SOC penalties. Because the added high-SOC term is zero everywhere feasible here, they have the same effective objective and should give the same power schedule up to numerical precision. A lower calendar estimate for combined at an extremely tiny decimal difference is not evidence of improvement.

### Check of saved results

The separate audit read all 20 result rows and checked raw JSON, CSV and inspection-summary agreement. Each session has exactly the four expected strategies. All 15 optimized results say `optimal`; the five immediate policies say `deterministic`. All 20 report zero high-SOC penalty and a positive calendar increment.

| Saved-data check | Largest observed value |
|---|---:|
| Difference between delivered grid energy and energy requirement | 3.951 × 10⁻¹² kWh |
| Departure-target mismatch | 5.923 × 10⁻¹⁴ SOC fraction |
| Reported power / SOC bound violation | 0 / 0 |
| Reported optimizer constraint residual | 3.952 × 10⁻¹² (mixed units) |
| Absolute combined–power-only cost difference | 1.684 × 10⁻¹² dollars |
| Absolute combined–power-only peak difference | 1.948 × 10⁻⁸ kW |
| Absolute combined–power-only calendar difference | 4.518 × 10⁻¹⁰ ppm |

These are tiny numerical differences, consistent with the expected equality. No material metric discrepancy was found and nothing was repaired. Some cost-only rows cost approximately $10⁻⁸ more than the theoretical minimum, consistent with the explicitly allowed tie-break tolerance.

**Audit limit:** the real-session result JSON saves aggregate scores, not interval-by-interval power/SOC arrays. We can verify field consistency and the mathematical inactive-term argument, but cannot independently compare every saved power value or reconstruct every calendar estimate from those aggregates. Ask the implementation owner to save trajectories in a separate experiment output directory. Today's review did not rerun the original seven tests or claim a new full solver validation.

### Zero threshold penalty does not mean zero aging

The high-SOC term is a deliberately chosen scheduling score with a 70% cutoff. The calendar evaluator in `src/aging.py` estimates capacity loss as time passes, based on SOC, temperature and prior calendar damage. Its stress factor is already positive at the pilot SOC values. It also includes waiting after charging finishes. The saved estimates range from approximately **5.1785 to 27.0220 ppm per session**, despite the zero threshold score.

Calendar loss here is a conditional prediction for a specific cell model transferred to an assumed pack. It does not include cycling damage, thermal behavior or measured battery-health change. Do not sum these five independently initialized simulations as if they were five successive visits by one identified vehicle, or rank methods by raw calendar values across sessions of very different duration. Compare methods **within the same session and assumption case** first.

### A second inactive comparison: electricity cost

The recorded energies can all fit in the pilot's cheap time slots. The code's interval-start tariff assignment leaves ample cheap capacity, so all four methods cost essentially `0.15 × recorded kWh`: **$1.18980, $1.50195, $0.78855, $0.77655, $1.51785** for S1–S5. The cost-only tie-break already spreads charging within cheap periods, making it similar to power-only in these cases. Equal costs are a valid outcome, not a failed experiment; these five cases alone cannot demonstrate a meaningful willingness-to-pay tradeoff.

## Proposed next experiments — team decision for November 15

This proposal keeps today's baseline intact. Use a new runner/configuration and a new output directory, for example `experiments/nov15/` and `results/nov15_proposed/`, only after the owners agree. Retain the original five low-SOC cases as labeled controls. Fix the sample and rules before seeing optimizer outcomes.

### Expand toward 15 real sessions, with 10–20 as a practical range

1. Retain S1–S5 in the review ledger. Mark S1 as a flagged diagnostic/control; it need not be included in a clean primary aggregate.
2. Seek ten additional raw Caltech sessions from a predeclared bounded window, **April 25 through May 1, 2018 inclusive, source-local dates**. Use documented ACN access; freeze query parameters, retrieval date, raw responses, pagination and hashes separately. Confirm access on November 15; it has not been rechecked today. If needed, the documented official archive is a transformed-data fallback and must form a separately labeled dataset, not be mixed silently with raw records.
3. Require unique sessionID, valid parseable connection/disconnection/timezone, positive duration and finite positive delivered energy. Log missing required fields, duplicates and nonpositive windows with reasons. Missing optional user inputs must not be imputed as measured requests. Flag inconsistent stop times; exclude them from the primary clean summary and show a with-flagged-records sensitivity separately. Keep raw records unchanged.
4. Choose diverse windows and energy amounts **before any scheduling runs**. Proposed duration bins: ≤4 h, >4–8 h, >8 h. Proposed energy bins: ≤5 kWh, >5–10 kWh, >10 kWh. Cross these into nine bins. Within each nonempty bin, sort by connection time then sessionID, and take the earliest eligible unused record. Fill remaining places by cycling through those bins in fixed order, taking the next earliest record, until ten additions are selected. Report empty bins; do not invent diversity or keep searching until an optimizer looks favorable.
5. Screen physical availability using `recorded_kWh ≤ 7.2 × connected_hours` under the assumed charger. Retain records that fail in the selection/exclusion ledger and report the failure count; do not silently lower energy or discard them for having inconvenient outcomes. Fill feasible evaluation slots from the next record in the same predeclared order. Also record required full-power time and the ratio `recorded_kWh/(7.2 × hours)` to show how tight each window is. Keep high-ratio feasible cases: they may offer little scheduling freedom, which is useful evidence.
6. If this window has too few usable records or empty diversity bins, report the limitation and use one predeclared extension, May 2–7, in the same order. Freeze the available 10–20-session cohort by November 17 rather than delaying results for a larger sample. This is a deliberately diverse case study, not a random estimate of the whole EV population.

No selection criterion refers to cost savings, penalty reductions or favored-method rankings. The original five controls remain visible even if the clean aggregate excludes S1. If 15 total includes S1, report that there are at most 14 clean records rather than relabeling the anomaly as clean.

### Small starting-SOC sensitivity

Hold recorded energy, actual windows and all other baseline assumptions fixed. Compare **assumed arrival SOCs of 30%, 60%, and 75%**. Recalculate the target for each case as `arrival_SOC + 0.9 × recorded_kWh / 60`. These are alternative hypothetical starting conditions for the same visit, not three measured battery states or three independent sessions.

Only arithmetic feasibility checks were run today; no new schedules were optimized. The five existing records give this preview:

| Session | Target at 30% start | Target at 60% start | Target at 75% start |
|---|---:|---:|---:|
| S1 | 41.8980% | 71.8980% | 86.8980% |
| S2 | 45.0195% | 75.0195% | **90.0195% — infeasible** |
| S3 | 37.8855% | 67.8855% | 82.8855% |
| S4 | 37.7655% | 67.7655% | 82.7655% |
| S5 | 45.1785% | 75.1785% | **90.1785% — infeasible** |

All five pass the power/window-energy check. At 60% start, three targets exceed 70% and two remain below: a useful active-term versus inactive-term comparison. At 75% start, all paths already begin above the threshold, but S2 and S5 exceed the fixed 90% hard cap and cannot be scheduled under these assumptions. Those failures are informative even though S2 misses the cap by only 0.0195 percentage points. Do not round it down to feasible.

For each scenario require `0 ≤ start ≤ target ≤ 0.90` and `recorded_kWh ≤ 7.2 × hours`. If it fails, save an infeasible status, the reason and original energy, and skip all four methods. Never cap the target, reduce energy, extend/shift the window, or count an infeasible solver result as a successful schedule. Keep analytic infeasibility distinct from a numerical solver failure. Compare the four methods on identical feasible cases; show counts and reasons alongside paired summaries so exclusions do not change denominators invisibly.

### Proposed experiment matrix and useful figures

| Stage | Cases / comparisons | Question and output |
|---|---|---|
| Small smoke check, Nov 15 | One clean active case (S2, 60% start), one clean inactive case (S3, 60%), one analytically infeasible case (S2, 75%); four methods only for feasible cases | Does the separate runner propagate arrival and target consistently, activate the intended term, preserve energy, and record infeasibility? At most 8 new schedules; owner-run next, not run today. |
| SOC pilot, Nov 16 | Five original sessions × three starting SOC assumptions × four policies, skipping infeasible cases | At most 52 feasible schedules by today's arithmetic. Show the targets/feasibility table and one price–power–SOC plot with a visible 70% line. Keep the flagged S1 separate. |
| Frozen real-session study, Nov 17–19 | About 15 sessions × three starting SOC assumptions × four policies; at most 180 schedules before exclusions | Compare cost, both separate penalty scores, peak power, calendar estimates, feasibility and runtime, paired within session/SOC case. Use fixed weights (1,0)/(1,10), not a new large weight sweep. |
| Presentation selection, Nov 19–20 | Predeclare earliest clean active case and earliest clean inactive case; include tight-window case if available | Plot full-window price/power/SOC for representative cases without choosing the largest improvement. Plot per-case cost premium versus high-SOC score change; mark zero-change cases and infeasible counts. |

Use a small feasibility heatmap/table with rows=session and columns=assumed arrival SOC, a paired high-SOC comparison plot, and a cost-versus-exposure plot. Put calendar estimates in their own panel labeled **conditional calendar model**, not on an unexplained combined health axis. Show the full connected window, including waiting. Summarize medians/ranges of paired differences, report case/session counts, and state the sample-selection limits. Do not treat 180 simulated schedules as 180 independent data records.

The proposal does not guarantee the high-SOC term will reduce every metric or create a cost premium. If the expanded sample still has little tariff competition, report that. A separately labeled synthetic price-timing contrast using the same recorded windows could then test timing mechanisms, but it must not be called an observed tariff or be selected after searching for favorable outcomes. The existing overnight synthetic example can remain the presentation's illustrative tradeoff case.

## Questions and dependencies for the two reviewers

**Battery-model reviewer — confirmation needed before presenting extended calendar estimates:**

1. Are 60%/75% hypothetical arrival levels and resulting paths up to 90% acceptable for this cell-specific calendar model? Confirm the distinction between a tested SOC envelope and demonstrated accuracy for short dynamic charging. Does the omission of tapering near 90% need a stated additional limitation or narrower primary sensitivity?
2. Can we retain the baseline 25°C, cell-to-pack transfer and 365-day prehistory as explicitly illustrative assumptions? Carry the same initial calendar-loss state across paired alternatives; if a different history is needed, propose a separate labeled case rather than editing the baseline.
3. Confirm language: 70% is an uncalibrated scheduler threshold, not a damage-onset boundary, and the calendar estimate omits cycling loss. Review claims and units before figures enter slides. No second aging model is required for this checkpoint.

**Implementation/reproduction reviewer — requests for a separate runner:**

1. Set both `Scenario(initial=assumed_start, target=assumed_start + efficiency*energy/capacity)` explicitly. The current data runner hardcodes `.3` in the target and inherits `.3` as the initial value: changing only one would break the sensitivity experiment. This is a proposal, not a baseline patch.
2. Save per-interval power, SOC boundaries, price, actual dt, settings, input identifiers/hashes, feasibility reasons, solver status and residuals in separate experiment outputs. Retain the current tie-break and weights for controlled comparison. Ensure invalid records do not abort the entire cohort without a ledger entry.
3. Review tariff boundary treatment. Current slots preserve exact connection endpoints and are equal lengths ≤15 min, but each slot takes its price from its start time. A slot crossing 16:00 is not split at the tariff change. Preserve this baseline behavior and disclose it; decide whether a separate boundary-resolution check is needed before comparing tiny dollar differences.
4. Run the three-case smoke check before expansion, then compare inactive-case trajectories directly. The original aggregates support expected equality but do not prove point-by-point equivalence. Distinguish setup-plus-total wall time from final-solver-stage time, especially for the two-stage cost-only rule.

**Your data/interpretation responsibilities:** freeze the cohort and assumptions; preserve raw fields; keep the exclusion ledger and labels; check the returned outputs against original times/energy; prepare paired comparisons and simple captions. Do not independently change the battery law or the other member's baseline runner.

## Checkpoint schedule

| Date | Concrete handoff |
|---|---|
| **Nov 15** | Agree on this selection rule, three SOC levels, flag policy and reviewer dependencies; confirm documented data access; implementation owner runs only the small smoke checks next |
| Nov 16–17 | Freeze roughly 10–20 raw sessions and metadata; execute the separate SOC pilot and approved cohort study |
| Nov 18–19 | Audit feasible/infeasible counts, original energy matching and paired plots; resolve claim/units questions with both reviewers |
| **Nov 20** | Verified presentation results, frozen tables/figures, assumptions and unresolved limitations |
| **Nov 21–23** | Slides, timed rehearsal and final corrections |
| **Nov 24** | Presentation |
| Nov 25–Dec 12 | Incorporate feedback, improve analysis and reproducibility, complete the report and software package |
| **Dec 13, 11:59 p.m.** | Final report and software deadline |

## Short update to share with the team

> I reviewed the five original ACN sessions and all twenty simulated results. The SOC values are assumed: every case starts at 30% and finishes between 37.77% and 45.18%. None reaches the 70% penalty threshold, so combined and power-only match to numerical precision; calendar aging is still positive. All four methods also cost essentially the same in this sample. One session has a charging-stop timestamp one minute after disconnect and is flagged. I propose retaining these controls, adding about ten records selected by quality/window/energy rules, and testing assumed starts of 30%, 60% and 75% in a separate experiment runner. Simple arithmetic predicts some active penalties and two 75%-start infeasibilities in the current five; no new sweep has been run. Please confirm the model's applicability and the runner's initial/target handling on November 15 so we can freeze verified results by November 20.

## Evidence and reproduction of this review

Read: `README.md`, both data/model specifications, the current project plan, `data/acn_sessions_raw.json`, `data/sample_sessions.csv`, `data/inspection.json`, `results/real_session_pilot.json`, `results/interpretation.md`, `src/inspect_data.py`, `src/charging.py` and `src/aging.py`.

From the repository root, run the standard-library-only review audit:

```sh
.venv/bin/python reviews/nov14/audit_pilot.py
```

It writes only `reviews/nov14/pilot_audit.json`, containing input hashes, full identifiers/times, saved metric comparisons, consistency assertions and the 15-case arithmetic feasibility preview. It does not import baseline modules, call the API, solve optimization problems or overwrite baseline results. Its assertions passed on November 14. `reviews/nov14/preservation_check.json` records the final hash comparison against the 36 files present before this review.
