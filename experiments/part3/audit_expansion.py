"""Check the expanded paths against raw records and SciPy HiGHS linear optimality bounds."""
import gzip
import json
import sys
from collections import Counter
from email.utils import parsedate_to_datetime as parse

import numpy as np
import scipy
from scipy.optimize import linprog

from verify import METHODS, OUT, ROOT, check, read, save

sys.path.insert(0, str(ROOT / "src"))
from aging import evaluate


def audit():
    source = read(ROOT / "data/nov18/acn_candidate_snapshot.json")["_items"]
    raw = {r["sessionID"]: r for r in source}
    config = read(OUT / "cohort.json")
    starts = config["starting_soc"]
    expected, rejected = set(), set()
    for sid in config["session_ids"]:
        r = raw[sid]
        hours = (parse(r["disconnectTime"]) - parse(r["connectionTime"])).total_seconds() / 3600
        energy = r["kWhDelivered"]
        for arrival in starts:
            if arrival + .9*energy/60 > .9 or energy > 7.2*hours + 1e-9:
                rejected.add((sid, arrival))
            else:
                expected.update((sid, arrival, method) for method in METHODS)
    exclusions = read(OUT / "exclusions.json")
    assert len(rejected) == len(exclusions)
    assert rejected == {(r["session_id"], r["initial"]) for r in exclusions}
    with gzip.open(OUT / "trajectories.json.gz", "rt") as stream:
        paths = json.load(stream)
    seen = set()
    worst = Counter()
    lp_solves = 0
    for t in paths:
        sid, start, method = key = t["session_id"], t["initial"], t["method"]
        if key in seen or key not in expected:
            raise ValueError(f"unexpected or repeated schedule {key}")
        seen.add(key)
        r = raw[sid]
        hours = (parse(r["disconnectTime"]) - parse(r["connectionTime"])).total_seconds()/3600
        p = np.array(t["power_kw"])
        prices = np.array(t["prices"])
        n = len(p)
        dt = hours / n
        energy = r["kWhDelivered"]
        soc = np.r_[start, start + np.cumsum(p)*dt*.9/60]
        check(t["scenario"]["dt"], dt, 1e-12, str(key))
        check(t["soc"], soc, 1e-8, str(key))
        check(p, np.clip(p, 0, 7.2), 1e-6, str(key))
        check(soc, np.clip(soc, 0, .9), 1e-8, str(key))
        e_error = abs(sum(p)*dt-energy)
        check(e_error, 0, 1e-6, str(key))
        cal = evaluate(soc, dt)["calendar_increment_ppm"]
        cal_error = abs(cal-t["metrics"]["calendar_increment_ppm"])
        check(cal_error, 0, 1e-8, str(key))
        worst["energy_kwh"] = max(worst["energy_kwh"], e_error)
        worst["calendar_ppm"] = max(worst["calendar_ppm"], cal_error)
        cap = 7.2
        front = np.clip(energy/dt - cap*np.arange(n), 0, cap)
        if method == "immediate":
            check(p, front, 1e-8, str(key))
            continue
        # At fixed energy and nonnegative power the SOC bounds follow from the endpoints.
        # Minimize the tangent plane over the physical feasible set with an external LP solver.
        gradient = prices*dt
        if method != "cost_only":
            gradient = gradient/max(abs(prices @ front * dt), 1) + 2*p/(n*cap**2)
        if method == "combined":
            excess = np.maximum(soc[1:] - .7, 0)
            gradient += 20*(.9*dt/60)*np.cumsum(excess[::-1])[::-1]/(n*.3**2)
        lp = linprog(gradient, A_eq=[np.ones(n)], b_eq=[energy/dt], bounds=(0, cap), method="highs")
        if not lp.success:
            raise RuntimeError(f"{key}: {lp.message}")
        gap = abs(float(gradient @ p - lp.fun))
        check(gap, 0., 1e-7, str(key))
        unit = "cost_only_gap_dollars" if method == "cost_only" else "weighted_gap_dimensionless"
        worst[unit] = max(worst[unit], gap)
        lp_solves += 1
        if method == "cost_only":
            for price in np.unique(prices):
                check(np.ptp(p[prices == price]), 0, 1e-8, "equal-price tie-break")
    if seen != expected:
        raise ValueError(f"{len(expected-seen)} missing schedules")
    return dict(scipy=scipy.__version__, paths=len(paths), exclusions=len(rejected),
                lp_certificates=lp_solves, maximum_errors=dict(worst),
                calendar_evaluator="original src/aging.py evaluated on reconstructed SOC")


if __name__ == "__main__":
    save("expansion_audit.json", audit())
