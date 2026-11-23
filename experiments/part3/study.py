"""Extend the frozen cohort with the existing screening ledger and run paired scenarios."""
import argparse
from collections import Counter, defaultdict, deque
from datetime import timedelta
from email.utils import parsedate_to_datetime as parse
import gzip
import hashlib
import json
import math
import platform
import sys
from time import perf_counter
from zoneinfo import ZoneInfo

import numpy as np

from verify import BASE, ROOT, OUT, METHODS, check, measure, read, save, solve


def select(count):
    records = read(ROOT / "data/nov18/acn_candidate_snapshot.json")["_items"]
    baseline = read(BASE / "cohort.json")
    ledger = read(BASE / "selection_ledger.json")
    by_id = {r["sessionID"]: r for r in records}
    used = {r["sessionID"] for r in baseline}
    assert len(used) == len(baseline) == 15
    for record in baseline:
        assert by_id[record["sessionID"]] == record
    bins = defaultdict(list)
    for row in ledger:
        sid = row["session_id"]
        if not row["screening_reasons"] and sid not in used:
            bins[tuple(row["bin"])].append(by_id[sid])
    queues = [deque(sorted(bins[k], key=lambda r: (parse(r["connectionTime"]), r["sessionID"])))
              for k in sorted(bins)]
    chosen = list(baseline)
    if not 15 <= count <= 15 + sum(map(len, queues)):
        raise ValueError("requested cohort size outside eligible range")
    while len(chosen) < count:
        for q in queues:
            if q and len(chosen) < count:
                chosen.append(q.popleft())
    selected = {r["sessionID"] for r in chosen}
    for row in ledger:
        row["expansion_selected"] = row["session_id"] in selected
    return chosen, ledger


def scenario(record, start):
    begin, end = map(parse, [record["connectionTime"], record["disconnectTime"]])
    hours = (end - begin).total_seconds() / 3600
    n = math.ceil(hours / .25)
    dt = hours / n
    local = begin.astimezone(ZoneInfo(record["timezone"]))
    prices = np.array([.30 if 16 <= (local + timedelta(hours=i*dt)).hour < 21 else .15
                       for i in range(n)])
    energy = record["kWhDelivered"]
    return dict(n=n, dt=dt, initial=start, target=start + .9*energy/60, maximum_soc=.9,
                maximum_power=7.2, efficiency=.9, capacity=60., reference_soc=.7), prices


def experiment(count):
    chosen, ledger = select(count)
    sources = ["data/nov18/acn_candidate_snapshot.json", "results/nov18/cohort.json",
               "results/nov18/selection_ledger.json"]
    config = dict(session_ids=[r["sessionID"] for r in chosen], starting_soc=[.3,.6,.75],
                  source_sha256={p: hashlib.sha256((ROOT/p).read_bytes()).hexdigest() for p in sources},
                  methods=list(METHODS), selection="Keep the original 15. Round-robin remaining eligible bins "
                  "in ascending (duration,energy) order. Within bins use connection time then ID.")
    save("cohort.json", config)
    save("candidate_ledger.json", ledger)
    old = {(r["session_id"], r["scenario"]["initial"], r["method"]): r
           for r in read(BASE/"metrics.json") if r["family"] == "real"}
    pilot = {(r["session_id"], r["strategy"]): r for r in read(ROOT/"results/real_session_pilot.json")}
    checked = set()
    paths, excluded, changes = [], [], []
    matched = 0
    for index, record in enumerate(chosen):
        sid = record["sessionID"]
        flagged = bool(record.get("doneChargingTime") and not
                       parse(record["connectionTime"]) <= parse(record["doneChargingTime"]) <= parse(record["disconnectTime"]))
        for initial in config["starting_soc"]:
            a, prices = scenario(record, initial)
            if a["target"] > a["maximum_soc"]:
                excluded.append(dict(session_id=sid, initial=initial, target=a["target"], reason="target exceeds 0.90"))
                continue
            paired = {}
            for method in METHODS:
                p, gap = solve(a, prices, method)
                soc, values = measure(a, p, prices)
                check(values["grid_kwh"], record["kWhDelivered"], 1e-6, sid)
                key = sid, initial, method
                for saved in [old.get(key), pilot.get((sid, method)) if initial == .3 else None]:
                    if saved:
                        for field in values:
                            check(values[field], saved[field], 1e-5, f"{key} {field}")
                if key in old:
                    checked.add(key)
                if initial == .3 and (sid, method) in pilot:
                    matched += 1
                paired[method] = values
                paths.append(dict(session_id=sid, initial=initial, method=method, scenario=a, timing_flag=flagged,
                                  power_kw=p.tolist(), soc=soc.tolist(), prices=prices.tolist(), metrics=values,
                                  normalized_optimality_gap=gap))
            changes.append(dict(session_id=sid, initial=initial, timing_flag=flagged,
                                **{k: paired["combined"][k]-paired["cost_only"][k] for k in paired["combined"]}))
    assert checked == set(old) and matched == len(pilot) == 20
    assert len(paths) == (3*len(chosen)-len(excluded))*4
    save("exclusions.json", excluded)
    save("paired_changes.json", changes)
    with (OUT/"trajectories.json.gz").open("wb") as stream:
        with gzip.GzipFile(filename="", fileobj=stream, mode="wb", mtime=0) as output:
            output.write(json.dumps(paths, allow_nan=False, separators=(",", ":")).encode())
    summaries = []
    for initial in config["starting_soc"]:
        clean = [r for r in changes if r["initial"] == initial and not r["timing_flag"]]
        summaries.append(dict(initial=initial, clean_pairs=len(clean),
                              q25_median_q75={k: np.percentile([r[k] for r in clean],[25,50,75]).tolist()
                              for k in ["cost_dollars","power_proxy","high_soc_proxy","calendar_increment_ppm","peak_kw"]}
                              if clean else {}))
    save("expansion.json", dict(solver="independent NumPy implementation", sessions=count, trajectories=len(paths),
                                excluded=len(excluded), exclusions_by_soc=dict(Counter(r["initial"] for r in excluded)),
                                reference_schedules_checked=len(checked), original_pilot_checked=matched,
                                summary_combined_minus_cost_only=summaries))


def benchmark():
    runs = []
    for minutes in [60, 30, 15, 5]:
        n, dt = 720//minutes, minutes/60
        a = dict(n=n,dt=dt,initial=.3,target=.8,maximum_soc=.9,capacity=60,efficiency=.9,
                 maximum_power=7.2,reference_soc=.7)
        h = np.arange(n)*dt
        prices = np.where(h<4,.3,np.where(h<9,.1,.24))
        for method in METHODS:
            solve(a,prices,method)
            elapsed = []
            for _ in range(5):
                start = perf_counter()
                p, gap = solve(a,prices,method)
                elapsed.append(perf_counter()-start)
            measure(a,p,prices)
            runs.append(dict(minutes=minutes,method=method,seconds=elapsed,median_seconds=float(np.median(elapsed))))
    save("timing.json", dict(scope="NumPy solve only, one warm-up then five calls; excludes I/O and evaluation",
                             python=sys.version, platform=platform.platform(),cpu=platform.processor(),
                             numpy=np.__version__, runs=runs))


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--sessions", type=int, default=50)
    args = parser.parse_args()
    experiment(args.sessions)
    benchmark()
