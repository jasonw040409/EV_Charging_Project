"""Run unmodified project entry points in a fresh directory; retain command logs."""
import argparse
import json
from math import isclose
from pathlib import Path
import shutil
import subprocess
import sys
from importlib.metadata import PackageNotFoundError, version

ROOT = Path(__file__).resolve().parents[2]
FIELDS = ("cost_dollars", "grid_kwh", "battery_kwh", "departure_soc", "power_proxy",
          "high_soc_proxy", "peak_kw", "calendar_increment_ppm")


def keyed(path, keys):
    rows = json.loads(path.read_text())
    data = {tuple(r[k] for k in keys): r for r in rows}
    if len(data) != len(rows):
        raise ValueError(f"duplicate identifiers in {path}")
    return data


def main(dest):
    dest.mkdir(parents=True, exist_ok=False)
    for folder in ["src", "data", "tests", "experiments/nov18"]:
        shutil.copytree(ROOT/folder, dest/folder)
    commands = {
        "tests": ["-m", "unittest", "discover", "-s", "tests", "-v"],
        "synthetic": ["src/run_example.py"],
        "pilot": ["src/inspect_data.py"],
        "study": ["experiments/nov18/run_study.py"],
    }
    statuses = {}
    for name, args in commands.items():
        with (dest/f"{name}.log").open("wb") as log:
            run = subprocess.run([sys.executable, *args], cwd=dest, stdout=log, stderr=subprocess.STDOUT)
        statuses[name] = run.returncode
    packages = {}
    for package in ["cvxpy", "clarabel", "numpy", "scipy", "matplotlib"]:
        try:
            packages[package] = version(package)
        except PackageNotFoundError:
            packages[package] = None
    summary = dict(python=sys.version, packages=packages, exit_codes=statuses,
                   commands=commands, errors={})
    for name, code in statuses.items():
        if code:
            lines = (dest/f"{name}.log").read_text(errors="replace").splitlines()
            summary["errors"][name] = next((line for line in lines if "ModuleNotFoundError:" in line),
                                           lines[-1] if lines else "empty log")
    (dest/"entry_points.json").write_text(json.dumps(summary, indent=2)+"\n", encoding="utf-8", newline="\n")
    print(json.dumps(statuses))
    if any(statuses.values()):
        raise SystemExit(1)
    for file, keys in [("comparison.json", ["strategy"]), ("real_session_pilot.json", ["session_id","strategy"]),
                       ("weight_sweep.json", ["weight_power","weight_soc"]), ("nov18/metrics.json", ["case","method"])]:
        expected = keyed(ROOT/"results"/file, keys)
        actual = keyed(dest/"results"/file, keys)
        if actual.keys() != expected.keys():
            raise ValueError(f"case set changed: {file}")
        for case, row in actual.items():
            # Without a positive power weight the primary objective can have multiple minimizers.
            if row.get("weight_power") == 0 and row.get("weight_soc", 0) > 0:
                saved = expected[case]
                def objective(r):
                    cref = r.get("cost_reference", r.get("solver", {}).get("cost_reference"))
                    return r["cost_dollars"]/cref + r["weight_soc"]*r["high_soc_proxy"]
                if not isclose(objective(row), objective(saved), abs_tol=1e-6, rel_tol=0):
                    raise ValueError(f"{file} {case}: primary objective changed")
                if not isclose(row["grid_kwh"], saved["grid_kwh"], abs_tol=1e-6, rel_tol=0):
                    raise ValueError(f"{file} {case}: energy changed")
                continue
            for field in FIELDS:
                if not isclose(row[field], expected[case][field], abs_tol=1e-5, rel_tol=1e-7):
                    raise ValueError(f"{file} {case} {field}: {row[field]} vs {expected[case][field]}")
        print(f"{file}: matched {len(actual)} rows")
    exclusions = "results/nov18/exclusions.json"
    if keyed(ROOT/exclusions, ["case"]) != keyed(dest/exclusions, ["case"]):
        raise ValueError("exclusion ledger changed")
    from native_checks import run_native
    run_native(dest)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("output", type=Path, help="new directory for the replay and logs")
    main(parser.parse_args().output.resolve())
