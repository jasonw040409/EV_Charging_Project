"""Run unmodified project entry points in a fresh directory; retain command logs."""
import argparse
import json
from math import isclose
from pathlib import Path
import shutil
import subprocess
import sys

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
            for field in FIELDS:
                if not isclose(row[field], expected[case][field], abs_tol=1e-5, rel_tol=1e-7):
                    raise ValueError(f"{file} {case} {field}: {row[field]} vs {expected[case][field]}")
        print(f"{file}: matched {len(actual)} rows")
    exclusions = "results/nov18/exclusions.json"
    if keyed(ROOT/exclusions, ["case"]) != keyed(dest/exclusions, ["case"]):
        raise ValueError("exclusion ledger changed")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("output", type=Path, help="new directory for the replay and logs")
    main(parser.parse_args().output.resolve())
