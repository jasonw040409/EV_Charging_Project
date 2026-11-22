"""Validate all expanded paths and time the original CVXPY models after baseline replay."""
import gzip
import json
import platform
import sys
from importlib.metadata import version
from pathlib import Path
from statistics import median
from time import perf_counter

import numpy as np
from verify import METHODS, OUT, ROOT, WEIGHTS, check, measure


def grouped_tie_break(a, prices, immediate):
    """For cost-only, equal-price slots share one power at the squared-power minimum."""
    import cvxpy as cp
    levels, membership, counts = np.unique(prices, return_inverse=True, return_counts=True)
    cheapest = np.sort(prices) @ immediate(a) * a.dt
    group_power = cp.Variable(len(levels))
    energy = cp.multiply(counts * a.dt, group_power)
    cost = levels @ energy
    problem = cp.Problem(cp.Minimize(cp.sum(cp.multiply(counts, cp.square(group_power)))),
                         [group_power >= 0, group_power <= a.maximum_power,
                          cp.sum(energy) == a.grid_energy, cost <= cheapest + 1e-8])
    problem.solve(solver="CLARABEL", tol_gap_abs=1e-10, tol_gap_rel=1e-10,
                  tol_feas=1e-10, max_iter=300)
    if problem.status != "optimal" or cost.value > cheapest + 1e-8 + 1e-10:
        raise RuntimeError(f"Grouped cost-only verification failed: {problem.status}")
    return group_power.value[membership], dict(status=problem.status,
            price_groups=len(levels), cost_premium_dollars=float(cost.value-cheapest))


def run_native(dest):
    sys.path.insert(0, str(dest / "src"))
    from charging import Scenario, immediate, optimize

    def run(a, prices, method):
        if method == "immediate":
            return immediate(a), {"status": "deterministic"}
        return optimize(prices, a, *WEIGHTS.get(method, (0, 0)))

    differences = {}
    failures = []
    with gzip.open(OUT / "trajectories.json.gz", "rt") as stream:
        paths = json.load(stream)
    for t in paths:
        a = Scenario(**t["scenario"])
        prices = np.asarray(t["prices"])
        try:
            p, info = run(a, prices, t["method"])
        except RuntimeError as error:
            if t["method"] != "cost_only" or not str(error).startswith("Tie-break failed:"):
                raise
            p, info = grouped_tie_break(a, prices, immediate)
            failures.append(dict(session_id=t["session_id"], initial=t["initial"], method=t["method"],
                                 error=str(error), grouped_recheck=info))
        if info.get("max_constraint_residual", 0) >= 1e-6:
            raise ValueError(f"solver residual: {info}")
        _, metrics = measure(t["scenario"], p, prices)
        for field, value in metrics.items():
            error = abs(value - t["metrics"][field])
            differences[field] = max(differences.get(field, 0), error)
            check(value, t["metrics"][field], 1e-4, f"{t['session_id']} {t['method']} {field}")
    timed = []
    for minutes in [60, 30, 15, 5]:
        a = Scenario(n=720//minutes, dt=minutes/60)
        h = np.arange(a.n)*a.dt
        prices = np.where(h<4, .30, np.where(h<9, .10, .24))
        for method in METHODS:
            run(a, prices, method)
            samples = []
            for _ in range(5):
                start = perf_counter()
                _, info = run(a, prices, method)
                elapsed = perf_counter() - start
                samples.append(dict(call_seconds=elapsed, last_solver_stage_seconds=info.get("solver_seconds"),
                                    status=info["status"]))
            timed.append(dict(minutes=minutes, method=method, samples=samples,
                              median_call_seconds=median(s["call_seconds"] for s in samples)))
    report = dict(paths=len(paths), original_verified=len(paths)-len(failures), original_failures=failures,
                  max_absolute_metric_differences=differences, timings=timed,
                  hardware=platform.processor(), platform=platform.platform(), python=sys.version,
                  packages={p:version(p) for p in ["numpy","scipy","matplotlib","cvxpy","clarabel"]},
                  scope="One warmup then five full scheduling calls. Cost-only has two solves. "
                        "last_solver_stage_seconds covers only the final solver stage.")
    (dest/"native_results.json").write_text(json.dumps(report, indent=2), encoding="utf-8")
