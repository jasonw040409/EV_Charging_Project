"""Run the solver-independent upstream test bodies in an isolated copy."""
from pathlib import Path
from tempfile import TemporaryDirectory
import json
import re
import shutil
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[2]
TESTS = [
    "test_infeasible_and_invalid",
    "test_calendar_closed_form_and_units",
    "test_history_split_and_timestep",
    "test_waiting_and_aging_history",
]


def run():
    with TemporaryDirectory() as name:
        dest = Path(name)
        for folder in ["src", "tests"]:
            shutil.copytree(ROOT/folder, dest/folder, ignore=shutil.ignore_patterns("__pycache__"))
        charging = dest/"src/charging.py"
        code = charging.read_text(encoding="utf-8")
        # Move only the eager solver import. Any call into optimize still requires real CVXPY.
        if code.count("import cvxpy as cp\n") != 1:
            raise RuntimeError("unrecognized solver import; inspect updated source")
        revised, count = re.subn(r"(^def optimize\([^\n]+:\n)", r"\1    import cvxpy as cp\n",
                                 code.replace("import cvxpy as cp\n", ""), flags=re.MULTILINE)
        if count != 1:
            raise RuntimeError("unrecognized optimize definition")
        charging.write_text(revised, encoding="utf-8")
        result = subprocess.run([sys.executable, "-m", "unittest", "-v",
                                 *["test_verification.Verification."+t for t in TESTS]],
                                cwd=dest/"tests", stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                                text=True, check=True)
        return dict(scope="Original four solver-independent test bodies; CVXPY import deferred only "
                          "inside a temporary copy of charging.py", tests=TESTS,
                    exit_code=result.returncode, output=result.stdout.splitlines())


if __name__ == "__main__":
    report = run()
    (ROOT/"results/part3/physics_tests.json").write_text(json.dumps(report, indent=2)+"\n",
                                                       encoding="utf-8", newline="\n")
    print("\n".join(report["output"]))
