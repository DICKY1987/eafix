import json
import subprocess
import sys
from pathlib import Path

TOOLS_DIR = Path(__file__).resolve().parent.parent / "tools"


def run_tool(name, *args):
    """Run a tool script from the tools directory and return stdout."""
    cmd = [sys.executable, str(TOOLS_DIR / name), *map(str, args)]
    result = subprocess.run(cmd, capture_output=True, text=True, check=True)
    return result.stdout.strip()


def test_trading_framework_scan():
    out = run_tool("trading_framework_scan.py", "bundle")
    assert json.loads(out) == {"frameworks": []}


def test_detect_trading_issues():
    out = run_tool("detect_trading_issues.py", "bundle")
    assert json.loads(out) == {"issues": []}


def test_map_trading_remediations():
    out = run_tool("map_trading_remediations.py", "findings", "bundle")
    assert json.loads(out) == {"remediations": []}


def test_apply_trading_patch():
    out = run_tool("apply_trading_patch.py", "bundle", "plan")
    assert json.loads(out) == {"artifact": "trading_system_vN+1"}


def test_run_trading_validation():
    out = run_tool("run_trading_validation.py", "artifact")
    data = json.loads(out)
    assert data["gates"] == {"A": True, "B": True, "C": True}


def test_compute_trading_metrics():
    out = run_tool("compute_trading_metrics.py", "validation", "findings")
    data = json.loads(out)
    assert data["trading_system_quality"] == 100


def test_make_trading_diff():
    out = run_tool("make_trading_diff.py", "vN", "vN1")
    assert out == ""
