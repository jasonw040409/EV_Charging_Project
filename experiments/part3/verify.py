"""Verify frozen trajectories and independently solve the same charging objectives."""
import json
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[2]
BASE = ROOT / "results/nov18"
OUT = ROOT / "results/part3"
METHODS = ("immediate", "cost_only", "power_penalty", "combined")
WEIGHTS = {"power_penalty": (1, 0), "combined": (1, 10)}


def read(path):
    return json.loads(path.read_text(encoding="utf-8"))


def save(name, value):
    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / name).write_text(json.dumps(value, indent=2, allow_nan=False) + "\n", encoding="utf-8", newline="\n")


def check(actual, expected, tol, label):
    np.testing.assert_allclose(actual, expected, rtol=0, atol=tol, err_msg=label)


def fill(order, demand):
    """Fill [0,1] slots in a specified order until normalized demand is met."""
    x = np.empty(len(order))
    x[order] = np.clip(demand - np.arange(len(order)), 0, 1)
    return x


def project(y, demand):
    """Project onto the unit box intersected with sum(x) = demand."""
    breakpoints = np.r_[y - 1, y]
    order = np.argsort(breakpoints)
    edges = breakpoints[order]
    slopes = np.r_[np.ones(y.size), -np.ones(y.size)][order]
    widths = np.diff(edges)
    mass = np.r_[0, np.cumsum(np.cumsum(slopes)[:-1] * widths)]
    wanted = len(y) - demand
    shift = np.interp(wanted, mass, edges)
    return np.clip(y - shift, 0, 1)


def solve(a, prices, method):
    """Independent normalized-power solution. The gap bounds convex suboptimality."""
    n, dt, limit = a["n"], a["dt"], a["maximum_power"]
    step = a["efficiency"] * dt * limit / a["capacity"]
    demand = (a["target"] - a["initial"]) / step
    if not (0 <= a["initial"] <= a["target"] <= a["maximum_soc"] and 0 <= demand <= n + 1e-9):
        raise ValueError("infeasible scenario")
    immediate = fill(np.arange(n), demand)
    if method == "immediate":
        return limit * immediate, 0.
    if method == "cost_only":
        x = fill(np.argsort(prices, kind="stable"), demand)
        for price in np.unique(prices):
            mask = prices == price
            x[mask] = np.mean(x[mask])
        return limit * x, 0.
    wp, ws = method if isinstance(method, tuple) else WEIGHTS[method]
    if wp == ws == 0:
        return solve(a, prices, "cost_only")
    cost = prices * (limit * dt) / max(abs(prices @ immediate * limit * dt), 1.)
    ref = a["reference_soc"]
    factor = 2 * ws * step / (n * (1 - ref) ** 2)

    def grad(x):
        excess = np.maximum(a["initial"] + step * np.cumsum(x) - ref, 0)
        return cost + 2 * wp / n * x + factor * np.cumsum(excess[::-1])[::-1]

    # Spectral norm of the lower triangular cumulative-sum matrix.
    norm = 1 / (2 * np.sin(np.pi / (4 * n + 2)))
    lipschitz = 2 * wp / n + factor * step * norm**2
    momentum = (np.sqrt(lipschitz) - np.sqrt(2*wp/n)) / (np.sqrt(lipschitz) + np.sqrt(2*wp/n))
    x = np.full(n, demand / n)
    y = x.copy()
    for i in range(20000):
        new = project(y - grad(y) / lipschitz, demand)
        extrapolation = momentum if wp > 0 else i / (i + 3)
        y = new + extrapolation * (new - x)
        x = new
        if i % 8 == 0:
            g = grad(x)
            gap = g @ (x - fill(np.argsort(g), demand))
            if abs(gap) < 1e-9:
                return x * limit, float(abs(gap))
    raise ArithmeticError("convex optimality gap did not converge")


def measure(a, p, prices, days=365, temperature=25):
    dt = a["dt"]
    soc = np.r_[a["initial"], a["initial"] + np.cumsum(p) * dt * a["efficiency"] / a["capacity"]]
    grid = float(sum(p) * dt)
    expected = (a["target"] - a["initial"]) * a["capacity"] / a["efficiency"]
    check(grid, expected, 1e-6, "grid energy")
    check(soc[-1], a["target"], 1e-8, "target SOC")
    check(p, np.clip(p, 0, a["maximum_power"]), 1e-6, "power bounds")
    check(soc, np.clip(soc, 0, a["maximum_soc"]), 1e-8, "SOC bounds")
    # Independently integrate the squared cubic SOC law by its polynomial moments.
    lo, hi = soc[:-1] - .5, soc[1:] - .5
    def moment(k):
        return sum(lo**i * hi**(k-i) for i in range(k+1)) / (k+1)
    integral = 1.2571e-5**2 * dt * 3600 * np.sum(
        2.8575**2 * moment(6) + 2*2.8575*.60225 * moment(3) + .60225**2)
    integral *= np.exp(-2 * 17126 / 8.314 * (1/(temperature+273.15) - 1/298.15))
    prior = 1.2571e-5 * .60225 * np.sqrt(days * 86400)
    loss = integral / (np.sqrt(prior**2 + integral) + prior)
    return soc, dict(grid_kwh=grid, cost_dollars=float(prices @ p * dt),
                     power_proxy=float(np.mean((p / a["maximum_power"])**2)),
                     high_soc_proxy=float(np.mean((np.maximum(soc[1:] - a["reference_soc"], 0)
                                                  / (1 - a["reference_soc"]))**2)),
                     calendar_increment_ppm=float(loss * 1e6), peak_kw=float(max(p)))


def audit():
    rows = {(r["case"], r["method"]): r for r in read(BASE / "metrics.json") if r["family"] != "weights"}
    paths = read(BASE / "trajectories.json")
    assert len(rows) == len(paths) == 224
    seen, worst, gaps = set(), {}, []
    reference = {}
    for t in paths:
        key = t["case"], t["method"]
        if key in seen:
            raise ValueError(f"duplicate trajectory {key}")
        seen.add(key)
        r = rows[key]
        a = r["scenario"]
        p, prices = np.array(t["power_kw"]), np.array(t["price_dollars_per_kwh"])
        assert p.shape == prices.shape == (a["n"],) and len(t["soc"]) == a["n"] + 1
        check(t["interval_hours"], a["dt"], 1e-14, str(key))
        soc, metrics = measure(a, p, prices)
        check(soc, t["soc"], 1e-8, str(key))
        for name, value in metrics.items():
            check(value, r[name], 1e-8, f"{key} {name}")
        power, gap = solve(a, prices, key[1])
        _, independent = measure(a, power, prices)
        gaps.append(gap)
        for name, value in independent.items():
            worst[name] = max(worst.get(name, 0), abs(value - r[name]))
        check(independent["cost_dollars"], r["cost_dollars"], 1e-5, str(key))
        wp, ws = WEIGHTS.get(key[1], (0, 0))
        cref = max(abs(prices @ fill(np.arange(a["n"]), r["grid_kwh"] / (a["dt"] * a["maximum_power"]))
                       * a["maximum_power"] * a["dt"]), 1)
        delta = ((independent["cost_dollars"] - r["cost_dollars"]) / cref
                 + wp*(independent["power_proxy"] - r["power_proxy"])
                 + ws*(independent["high_soc_proxy"] - r["high_soc_proxy"]))
        check(delta, 0, 1e-6, str(key))
        if key[0] in ("baseline", "flat", "real_1_soc60", "real_2_soc60"):
            reference["/".join(key)] = independent
    assert seen == set(rows)
    variations = read(BASE / "aging_sensitivity.json")
    baseline = {t["method"]: t for t in paths if t["case"] == "baseline"}
    a = rows["baseline", "immediate"]["scenario"]
    assert len(variations) == 36
    for v in variations:
        t = baseline[v["method"]]
        _, m = measure(a, np.array(t["power_kw"]), np.array(t["price_dollars_per_kwh"]),
                       v["prior_days"], v["temperature_c"])
        check(m["calendar_increment_ppm"], v["calendar_increment_ppm"], 1e-8, "calendar sensitivity")
    weights = read(ROOT / "results/weight_sweep.json")
    assert len(weights) == 12
    prices = np.array(baseline["immediate"]["price_dollars_per_kwh"])
    for r in weights:
        wp, ws = r["weight_power"], r["weight_soc"]
        p, gap = solve(a, prices, (wp, ws))
        _, m = measure(a, p, prices)
        delta = ((m["cost_dollars"] - r["cost_dollars"]) / r["cost_reference"]
                 + wp * (m["power_proxy"] - r["power_proxy"])
                 + ws * (m["high_soc_proxy"] - r["high_soc_proxy"]))
        check(delta, 0., 1e-6, f"weighted objective {(wp, ws)}")
        gaps.append(gap)
    return dict(trajectories=len(seen), max_normalized_gap=max(gaps),
                weight_objectives=len(weights), temperature_history_checks=len(variations),
                max_absolute_independent_differences=worst, examples=reference)


if __name__ == "__main__":
    save("verification.json", audit())
