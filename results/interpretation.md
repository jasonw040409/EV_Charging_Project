# Interpretation of the executed results

The synthetic example is feasible for every strategy, delivers 30 battery kWh, and compares schedules across the full 12-hour connection. The largest saved synthetic QP constraint residual is approximately 1.7e-12. Seven unit tests passed; see `verification.txt`. The plot was visually inspected for readable labels and complete SOC/power traces.

The main comparison is in `comparison.md`. Cost-only uses the five-hour cheap period and finishes at 03:00; its tie-break spreads power within that equally cheap window. The combined objective shifts some charging to the more expensive period near departure. It lowers both normalized surrogates for this selected weight pair and lowers the conditional calendar estimate from 30.7634 to 29.2660 ppm relative to cost-only. The cost premium is $0.9374 (about 28.1%). These tiny modeled calendar differences have not been validated against physical aging data.

Lower integrated squared power does not require lower peak power: the combined schedule peaks at 6.6051 kW versus power-only's 5.9624 kW. We do not claim that every stress metric improves together or that slower charging always helps. The 12-pair sweep is saved, but a full Pareto and sensitivity analysis remains team work.

The five raw ACN records yielded 20 feasible pilot schedules. The largest grid-energy residual was below 4e-12 kWh in this execution. They preserve actual windows and use retrospective departure knowledge. One doneChargingTime is after disconnectTime and is flagged. No session energy was clipped.

**Sampling limitation discovered:** assumed targets in this five-session sample are only about 0.378–0.452. Consequently the 0.70 high-SOC proxy is zero for every real-session pilot. Combined and power-only should therefore coincide to solver tolerance in this pilot. This is an informative inactive-term case, not evidence that the SOC term has been tested on high-SOC application sessions. Before November 20, add predeclared initial-SOC sensitivity and a traceable broader energy/window sample that activates the SOC term under disclosed assumptions; retain these low-SOC sessions as controls. Do not select only sessions that make a favored method look good, and do not describe assumed high SOC as measured.

The published evaluator is calendar-only, uses a specific LFP cell and synthetic prior damage, and omits cycling and thermal effects. It supports a conditional comparison of SOC/time exposure. Charging-rate damage, chemistry transferability, battery lifetime and real health benefits remain uncertain.
