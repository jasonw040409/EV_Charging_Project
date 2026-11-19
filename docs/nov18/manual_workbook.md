# Your manual workbook — start tonight

These tasks are intentionally left for people. Do not tick a box because an automated answer exists. Write your answer in the space, explain it aloud, and record actual time. Expected total manual allocation through packaging/rehearsal is 7 hours (35% of the estimated remaining preparation effort); tonight's recommended first block is 90 minutes. Take breaks or move the second block to Nov 19 if needed.

## First 90 minutes tonight — you can do this alone

### 1. Understand one real session (20 minutes)

Read the S2 walkthrough in `docs/data_review_nov14.md`. SOC means how full the battery is. kWh is energy; kW is the rate of delivery.

- [ ] Find S2 directly in `data/acn_sessions_raw.json` using its sessionID. Write local connection/departure times and delivered energy.
- [ ] Explain why connection duration differs from active charging duration.
- [ ] Calculate `10.013 × .9 = ___ battery kWh`, then `30% + (answer/60 × 100) = ___ final SOC`.
- [ ] Explain why this final SOC is a hypothetical value, not a measurement.

Your answers:
S2: connected on Wed, 25 Apr 2018 13:45:10 GMT and disconnected on Thu, 26 Apr 2018 00:56:16 GMT. Delivered energy = 10.013 kWh
The  


> [Write here. Expected numerical checkpoints: 9.0117 kWh; 45.0195%.]

### 2. Explain a useful failure (20 minutes)

- [ ] At an assumed 60% start, compute S2's target. Does it cross the 70% penalty threshold?
- [ ] At an assumed 75% start, compute the target. Why does a result just over 90% still violate our hard cap?
- [ ] Say aloud: “70% is a soft preference; 90% is our hard upper constraint.” Explain what that means without equations.
- [ ] Explain why we must keep the 10.013-kWh recorded energy even if a hypothetical scenario is infeasible.

Your explanation:

> [Expected checkpoints: 75.0195% at 60% start; 90.0195% at 75% start. Record the latter as infeasible, not 90%.]

### 3. Read a plot (25 minutes)

Open `results/nov18/representative_soc60.png` when generated. The three panels show synthetic price, grid power and assumed SOC over the actual connected window.

- [ ] Find when each method charges and when it waits. Point to the 70% line.
- [ ] Write one sentence describing what changes from power-only to combined.
- [ ] Check `results/nov18/paired_clean_results.json`: is there a cost premium for this case? Report zero if there is none.
- [ ] Write one observation that the plot supports, and one claim it cannot support (for example, measured lifetime improvement).

Your caption:

> [Describe the observed output, not the outcome you hoped for.]

### 4. Prepare the teammate handoff (25 minutes)

- [ ] Read `accelerated_plan.md`; record the two questions you most need answered.
- [ ] Identify which plot/metric you could explain to a classmate now.
- [ ] Prepare this update for sharing yourself; no message has been sent automatically:

> We have lost the Nov 14–17 review period. The automated study now preserves all four methods and planned experiment families in separate outputs, with real SOC explicitly assumed. Please take independent model/source review and implementation reproduction on Nov 19 so we can freeze verified results Nov 20. I am reviewing data selection, failure cases and interpretation. Automated success is not a substitute for either review. Presentation/rehearsal dates remain Nov 21–24.

## Remaining manual work — keep this human-owned

| Allocation | Person / action | Record evidence, not just completion |
|---|---|---|
| Remaining 40 min data review | You inspect two more raw records plus the selection/exclusion ledger | IDs, timestamp checks, observed/assumed distinctions and anomaly decision |
| 90 min model/theory review | Model teammate when available | Independently calculate constant-stress aging; check source equation/unit/history mapping; derive convexity/KKT; sign/date limitations review |
| Remaining 15 min interpretation | You examine paired cost/stress/peak/calendar results and an infeasible case | Three supported findings, one counterexample or zero-effect case, two limitations |
| Remaining 35 min report reasoning | You/team write explanations and actual contribution statements | Original wording; map each result claim to a saved output |
| 120 min presentation | All available members explain their slides and rehearse aloud | Timed runs, questions missed and corrections; speaking practice cannot be automated |
| 30 min final reproduction/submission audit | Implementation teammate plus you | Independent command result, figure consistency, final files/recipients/deadline checked by a person |

The first 90 minutes include 20 minutes of data review, 45 minutes of interpretation/plot reading and 25 minutes of report/team explanation preparation. Time categories are estimates; use actual time rather than making totals look exact. Across the full effort budget, target 30–40% manual, not a rigid quota of busywork.

Unresolved questions / reviewer responses:

> [Leave blank until a person answers.]

Actual time log (date, task, minutes, evidence):

> [Leave blank until performed.]
