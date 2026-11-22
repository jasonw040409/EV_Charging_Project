# Presentation Findings and Evidence

Prepared November 22, 2026 for the data and interpretation section of the November 24 presentation. These findings describe the frozen 15-session pilot under assumed battery settings and synthetic prices. Comparisons below are **Combined minus Power penalty**, not Combined minus cost-only. Numerical exports and figure checks are complete; independent model review and reproduction are separate team responsibilities.

The central finding is that adding the high-SOC penalty can delay charging and reduce the exposure score while increasing peak power. Effects vary across cases, and the smaller feasible sample at 75% starting SOC limits comparisons across starting-SOC groups. These are scheduling results, not measured battery-health benefits.

## Finding 1  Adding the high SOC penalty does not always change the schedule

**Slide wording:** “At an assumed 30% arrival SOC, adding the high-SOC penalty produces essentially no change in the clean cases.”

Across 14 clean paired cases at 30%, all cost, exposure and peak-power differences are within the reporting tolerances. At 60%, the response is mixed: exposure falls in six cases and is essentially unchanged in eight. The median exposure change at 60% is zero, so the median alone would hide the six reductions.

**Explain aloud:** “The extra preference matters only when it can affect the feasible schedules. Some sessions never approach the threshold; others have room to change charging timing. We therefore show individual cases as well as the median.”

**Evidence:** [Paired tradeoff figure](../results/data_review_nov21/figures/paired_tradeoffs_slide.png), left panel; [paired summary](../results/data_review_nov21/paired_change_summary.csv), clean groups, assumed starts 30/60%, high_soc_proxy, comparison combined/reference power_penalty. The 30% cost and peak rows support the broader unchanged statement.

**Qualification:** “Essentially unchanged” means within the reporting tolerances, not exact mathematical equality. Do not infer a universal physical threshold or claim all possible low-start sessions behave this way.

## Finding 2  Lower high SOC exposure can come with higher peak power

**Slide wording:** “Combined scheduling reduces high-SOC exposure in some cases by shifting energy later, but uses higher peak charging power.”

At 60% assumed start, six of the 14 clean cases have lower exposure; six have higher peak power. At 75%, all nine clean cases have lower exposure and higher peaks than Power penalty. In the 75% group, median paired changes are approximately -0.05412 in the normalized exposure score and +5.107 kW in peak power.

**Explain aloud:** “Delaying some energy keeps the battery less full for longer. To catch up before departure or the end of the cheap period, the schedule may charge faster later. We are trading one scheduling preference against another.”

**Evidence:** [Paired tradeoff figure](../results/data_review_nov21/figures/paired_tradeoffs_slide.png), left and middle panels; [paired summary](../results/data_review_nov21/paired_change_summary.csv), clean 60/75% high_soc_proxy and peak_kw rows. [Individual paired changes](../results/data_review_nov21/paired_case_changes.csv) preserve the session identities.

**Qualification:** Peak power is a maximum; D_P measures squared concentration across the entire window. They are different metrics. A lower exposure score is not proof of longer life, and a higher peak within the 7.2-kW cap is not itself a constraint violation. The present model does not include facility demand charges or grid impacts.

### S2 explains the mechanism

The S2 representative case starts at an assumed 60% and finishes at a derived 75.0195%, matching 10.013 recorded grid kWh within the actual connection window. Power penalty and Combined both cost approximately $1.50195 under synthetic prices. Combined reduces the high-SOC score from 0.00730753 to 0.00569930, while peak power increases from 1.0601 to 3.4106 kW.

**Suggested caption:** “For S2 with assumed 60% arrival SOC, Combined delays some charging and reduces high-SOC exposure at essentially unchanged energy cost, while increasing peak power.”

**Evidence:** [S2 slide figure](../results/data_review_nov21/figures/s2_soc60_schedules_slide.png); [frozen metrics](../results/nov18/metrics.json), case `real_1_soc60`, methods power_penalty and combined; [saved trajectories](../results/nov18/trajectories.json), same case. Full session ID: `2_39_95_27_2018-04-25 13:45:09.617470`.

The plot uses source-local Los Angeles clock time; it is not Chicago time. Actual connection is 06:45:10 and disconnection 17:56:16 on April 25, 2018. The exact synthetic tariff step follows interval-start assignment, so the visible step need not fall exactly at 16:00.

## Finding 3  Lower exposure often has no additional energy cost in this sample

**Slide wording:** “Expense is essentially unchanged for most paired cases, but some cases incur an additional cost.”

| Assumed arrival SOC | Clean paired cases | Higher cost | Within cost tolerance | Lower cost |
|---|---:|---:|---:|---:|
| 30% | 14 | 0 | 14 | 0 |
| 60% | 14 | 2 | 12 | 0 |
| 75% | 9 | 1 | 8 | 0 |

The median paired cost change is essentially zero in each group. Cost premiums occur in particular cases rather than being universal. S2 illustrates a zero-premium timing change because the alternative schedule can still fit within cheap hours.

**Explain aloud:** “Changing the timing does not necessarily change the bill when energy stays within the same price period. But if a schedule uses more expensive intervals, there can be a premium.”

**Evidence:** [Paired tradeoff figure](../results/data_review_nov21/figures/paired_tradeoffs_slide.png), right panel; [paired summary](../results/data_review_nov21/paired_change_summary.csv), cost_dollars rows, clean cases, combined versus power_penalty. Individual case costs remain in [paired changes](../results/data_review_nov21/paired_case_changes.csv).

**Qualification:** The tariff is synthetic and contains energy charges only. These are simulated expenses, not observed bills or a guarantee of free exposure reduction. Near-zero negative differences from numerical rounding are not meaningful savings.

## Finding 4  Higher assumed starting charge reduces the feasible sample

**Slide wording:** “The 75% starting-SOC comparison contains nine clean cases because five hypothetical targets exceed the assumed cap and one feasible record is timing-flagged.”

| Assumed arrival SOC | Clean feasible | Flagged feasible | Infeasible | Total |
|---|---:|---:|---:|---:|
| 30% | 14 | 1 | 0 | 15 |
| 60% | 14 | 1 | 0 | 15 |
| 75% | 9 | 1 | 5 | 15 |

At 75% starting SOC, a 60-kWh battery has 9 battery kWh of space before the 90% cap, equivalent to 10 grid kWh at 90% efficiency. Five selected records delivered more than 10 kWh. Their hypothetical targets exceed the cap; changing timing cannot fix the final-energy conflict. The energy was not reduced to force feasibility.

**Explain aloud:** “These failures are caused by a combination of our assumptions. They do not mean the original real-world charging sessions were impossible.”

**Evidence:** [Availability figure](../results/data_review_nov21/figures/scenario_availability_slide.png); [scenario counts](../results/data_review_nov21/scenario_availability_by_soc.csv); [exclusion details](../results/data_review_nov21/scenario_exclusion_details.csv); [original exclusion evidence](../results/nov18/exclusions.json). The timing flag is explained in [session summary](../results/data_review_nov21/session_summary.csv).

**Qualification:** The 75% group has different membership from the 30/60% groups. Within each group the two methods use identical cases, but cross-group differences cannot be attributed solely to arrival SOC. A common-nine-session sensitivity comparison remains a useful next check; it has not been executed in this data-review sequence. “Clean” means no detected charging-stop ordering flag, not complete validation of every field.

## Finding 5  We have real session inputs rather than measured battery states or field validation

**Slide wording:** “Recorded availability and energy anchor the simulation; battery states, tariff and health outcomes remain assumed or modeled.”

The study has 15 recorded sessions, three assumed arrival SOCs, 45 hypothetical scenarios, 40 feasible scenarios and 160 real-session-based schedules. The broader November 18 study also contains 64 synthetic sensitivity schedules and 12 weight schedules, for 236 successful schedules in total. These counts do not describe 236 independent real observations. Fifteen records are selected from a bounded candidate snapshot, not randomly sampled from all EV charging.

**Explain aloud:** “We ask how alternative schedules could deliver recorded energy during recorded windows. We do not know the true arrival SOC or reproduce the historical minute-by-minute charging trace.”

**Evidence:** [Cohort](../results/nov18/cohort.json), [provenance](../results/nov18/data_provenance.json), [quality summary](../results/data_review_nov21/data_quality_summary.csv), [run summary](../results/nov18/run_summary.json), [model specification](model_specification.md).

**Qualification:** Capacity, SOC, efficiency, power limit, chemistry, temperature/history and prices are assumed. Actual departure is used retrospectively. The published evaluator estimates calendar capacity loss only; it is separate from the two optimizer penalties and does not establish real lifetime improvement. Independent model/source review and teammate reproduction must be reported according to their actual status.

## How to use these findings in the presentation

Use three figures in this order:

1. Availability: define eligible counts and why n differs before presenting group comparisons.
2. S2: explain the timing mechanism on one traceable example.
3. Paired tradeoffs: show variation, unchanged cases and the exposure/peak/cost tradeoff across cases.

Use Findings 1–3 as the main result messages. Findings 4–5 explain denominators and scope; keep them beside the results, not buried as an unrelated final disclaimer. Full IDs, formulas, tolerances and extra tables belong in speaking notes or backup material rather than crowded main figures.

A concise closing statement for this section is:

> Under disclosed battery and price assumptions, adding a high-SOC penalty changes some charging schedules and can lower exposure by delaying delivery. This can require higher peak power or additional expense. Effects are case-dependent, and our data-informed simulations do not establish measured battery-health improvement.

## Reporting and review rules

All differences here are paired within session and assumed start, then summarized. A median paired difference is not the same operation as subtracting two independently computed group medians. Case counts for 30/60/75% are 14/14/9 in clean summaries. They are not independent replicated studies because sessions recur across SOC assumptions.

Numerical classification tolerances are $1e-7 for cost, 1e-8 for proxy scores and 1e-5 kW for peak. Raw deltas remain unchanged in the exports. These tolerances distinguish rounding noise; they are not thresholds for practical importance or statistical significance. No statistical significance or population-wide inference is claimed.

Before the final slide freeze, the model reviewer checks scientific wording; the implementation reviewer checks numerical provenance and reproduction; the data/interpretation member explains the figures and confirms every caption matches its evidence. The current figures use the 15-session pilot. Do not relabel them as a 50-session expansion unless that expansion has actually been executed and separately checked.
