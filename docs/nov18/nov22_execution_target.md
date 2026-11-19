# November 22 execution target — agreed direction November 19

User requested more execution by November 22, with November 24 presentation unchanged and no planned content cut. This supplement supersedes the November 18 recovery calendar where it brings execution forward. It does not mark proposed work complete.

## Starting evidence

The saved November 18 summary records 15 real sessions, 236 successful real/synthetic schedules, 224 complete trajectories, five analytically infeasible scenarios, and zero numerical failures. Existing tests passed. Independent human model review and reproduction are still not evidenced as complete. New work must remain separate from baseline data/code/results, with provenance and honest observed-versus-assumed labels.

## Two checkpoints, not one postponed checkpoint

- **November 20:** verified core-results checkpoint. Independently review the battery equations/history and reproduce the existing study; resolve issues; freeze the baseline plots that can support the presentation. Missing human review remains explicitly missing.
- **November 22:** expanded-execution checkpoint. Aim for the larger study and richer interpretation below. Keep the November 20 results as a recoverable presentation baseline.

## Concrete November 22 target

1. **Expand from 15 toward 50 original real sessions**, keeping the frozen 15-session cohort and its controls as a separate reference. Use a separate snapshot/manifest and outcome-independent selection by duration/energy bins. Report quality flags, selection exclusions and infeasible assumptions. Fifty is a stretch execution target, not permission to fabricate records, hide exclusions or claim representativeness. Retain 100 as the final-report expansion target if needed.
2. Run **the same four methods at assumed arrival SOCs 30%, 60%, 75%** on the expanded cohort. This yields at most 600 schedules before infeasibility; report sessions and simulated cases separately. Preserve recorded energy and windows. No energy clipping or silent parameter changes.
3. Produce **paired per-case results and summaries**, separating SOC levels and flagged/clean records. Include cost, both proxies, peak power, conditional calendar loss, feasibility, and runtime. Show medians/interquartile ranges and the number of eligible cases; keep zero-effect and adverse tradeoffs visible.
4. Finish a readable **weight/ablation and sensitivity results pack** using all existing experiment families: window flexibility, price timing/flat prices, initial/target SOC, high-SOC threshold, temperature/history and 60/30/15/5-minute resolution. Existing execution need not be duplicated merely to increase run counts. Repeat timing on a small fixed set (e.g. five runs per resolution) if computational comparisons are included.
5. Add **traceable verification evidence**: full trajectories, status/residual checks, analytic controls, explicit infeasibility ledger and independent reviewer notes. Keep model estimates provisional until the model reviewer signs off. Source review and independent reproduction cannot be replaced by additional solver runs.
6. Draft **three to five supported findings and captions**, each mapped to an output. Include at least one inactive-penalty control, one infeasible case and one competing-metric example. Select representative figures by a predeclared rule, not maximum favorable outcome.
7. Keep **a complete presentation draft and a first timed rehearsal by November 22**. Expanded execution cannot consume rehearsal time. Main slides summarize every planned component; backup slides hold supporting tables. No completed deck or rehearsal is claimed by this plan.

## Day-by-day execution

| Date | Automation/preparation | Manual responsibility |
|---|---|---|
| Nov 19 | Prepare/freeze expanded sampling configuration and source manifest; audit existing results/plots | Model reviewer checks sources/units/history; implementation reviewer reproduces; user continues guided interpretation |
| Nov 20 | Finalize core evidence and prepare bounded expanded runner | Verify core results; record unresolved limitations; approve interpretation of assumptions |
| Nov 21 | Execute larger cohort and summarize paired findings; prepare updated figure/caption pack | Complete full slide draft and review unexpected/zero-effect cases |
| Nov 22 | Finish approved sensitivity/runtime analysis and expanded results; freeze presentation numbers | First timed rehearsal, explain every figure, resolve reviewer questions |
| Nov 23 | Only corrections/reproduction needed to fix concrete issues | Second rehearsal and final slide proofread |
| Nov 24 | Presentation | Deliver preliminary but substantive study |

The automation/manual effort target remains approximately 65%/35% (acceptable manual range 30–40%), estimated across remaining preparation. Guided explanations can support understanding, but do not themselves establish that an independent reviewer checked the source or reproduced outputs. Keep model decisions, interpretation, checking, speaking practice and actual contribution statements human-owned.

## Work retained after presentation

Larger-data expansion toward 100 sessions if useful; deeper sensitivity and feedback-driven analysis; the original optional second-model/cycle-evaluator reproducibility decision; complete related-work comparison and theory; 8–12-page report; independent clean-environment reproduction; actual member contributions; report/software packaging and submission **December 13 at 11:59 p.m.** Moving the 50-session target forward does not delete these tasks.

If access/review fails, retain and present the verified 15-session study with limitations while documenting the uncompleted stretch target. Do not call an unverified expansion a verified result merely to meet the date. This is a dependency report, not a change to the agreed scope.
