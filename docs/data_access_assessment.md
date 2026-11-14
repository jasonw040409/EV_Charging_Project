# Data access assessment — November 14, 2026

**Five actual API records were retrieved and inspected.** Raw response: `data/acn_sessions_raw.json`; field audit: `data/sample_sessions.csv` and `data/inspection.json`. Results include 20 assumed-battery retrospective pilot schedules in `results/real_session_pilot.json`.

## Access path and provenance

The [official ACN-Data documentation](https://ev.caltech.edu/dataset) documents fields and API authentication. GET `https://ev.caltech.edu/api/v1/sessions/caltech?max_results=5` without authentication returned JSON error code 401, saved as `data/acn_api_response.json`. The [official Caltech algorithm-comparison tutorial](https://github.com/caltech-netlab/acnportal-experiments/blob/593f5dcbc50544fbdb6d1988e15e935877ae4b26/examples/2-Algorithm-Comparison/2.1-Comparing-Algorithms-with-Constrained-Infrastructure/2.1-comparing-algorithms-with-constrained-infrastructure.ipynb) publishes the public `DEMO_TOKEN`. HTTP basic authentication with that token returned five records. No personal token was discovered or used.

Re-fetch explicitly, if needed (API contents/order can change):

```sh
curl --fail --user 'DEMO_TOKEN:' 'https://ev.caltech.edu/api/v1/sessions/caltech?max_results=5' --output /tmp/acn_new_sample.json
```

Normal reproduction uses the saved response, with no network or credentials. This is an inspectable convenience sample, not a random or representative sample of workplace charging.

A legitimate fallback was also checked: the tutorial's pinned [March 2019 event archive](https://github.com/caltech-netlab/acnportal-experiments/blob/593f5dcbc50544fbdb6d1988e15e935877ae4b26/examples/2-Algorithm-Comparison/2.1-Comparing-Algorithms-with-Constrained-Infrastructure/events/caltech_20190301T000000_20190401T000000_5m_208V_6.6kW.json.gz), saved as `data/acn_events_official.json.gz`. This contains transformed simulator objects, not raw sessions, and is not used for the final five-record audit. The official [conversion source](https://github.com/zach401/acnportal/blob/14e723b11339e56ca3afd2bf4969f9e4bc8c2623/acnportal/acnsim/events/acndata_events.py), copied under `sources/`, maps `kWhDelivered` into a simulator field called requested energy, can optionally clip feasibility, and synthesizes capacity/initial charge. Those values must not be mistaken for observed battery properties. The notebook's public API path ultimately made this fallback unnecessary.

## Observations versus assumptions

| Field | Meaning in this pilot |
|---|---|
| connectionTime / disconnectTime | Observed plug-in window, UTC parsed and converted using supplied America/Los_Angeles timezone |
| kWhDelivered | Observed delivered energy; assumed grid-side for replay energy matching |
| doneChargingTime | Charging stop timestamp, not departure |
| userInputs | Null in these five responses; requested energy/departure unavailable |
| sessionID / stationID / spaceID | Traceable source identifiers; not vehicle chemistry |
| Capacity, initial SOC | **Assumed** 60 kWh and 0.30, not inferred from delivered energy |
| Target SOC | Derived as 0.30 + 0.9 delivered_kWh/60 under those assumptions |
| Temperature / chemistry | Assumed 25 C and selected Sony LFP normalized calendar response |
| Power / efficiency | Assumed 7.2 kW and 0.9, not measured charger limits or car efficiency |
| Price | Synthetic $0.30 16:00–21:00, otherwise $0.15 local; not an observed tariff |
| Age/history | Shared synthetic calendar prehistory described in model specification |

All windows remain at their actual dates and clock times, including a session beginning around 04:08 local. Nothing is moved to overnight hours. Evaluation knows the actual disconnection timestamp in retrospect, so it is **retrospective known-departure evaluation**, not an online deployable predictor. Slot count is ceil(duration/0.25), with equal slot duration duration/count, preserving exact original boundaries with slots no longer than 15 minutes. This differs from the synthetic example's exact 15-minute slots and is saved in source logic.

One record has doneChargingTime one minute after disconnectTime. We flag it and use the physical connection/disconnection window; no timestamp is silently repaired. It remains in this diagnostic pilot, with a planned exclusion sensitivity. Requested energy remains unavailable; delivered-energy matching does not establish that driver needs were satisfied historically.

Screening rejects any assumed target above 0.9, nonpositive window or energy requirements exceeding the power/window limit. No record's observed energy is reduced to force feasibility. Current five-session feasibility is recorded by the executed pilot rather than presumed from archive simulator settings. API timestamps and raw response are preserved for independent review. Larger experiments still need site-specific charger limits, documented sample selection, anomaly handling, and verified timezone/partial-slot policy. The public demo credential may be limited or stop working; obtain a personal token through ACN's documented process if necessary.

Execution finding: all five sessions were feasible under the disclosed assumptions. Their derived targets are below 0.46, so the 0.70 exposure term is inactive in all five. These records establish access and a functioning data pipeline; broader sampling and initial-SOC sensitivity are necessary to study high-SOC effects on real-session windows.
