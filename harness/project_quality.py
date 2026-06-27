"""Project-wide quality checks for the completed harness."""

import json
import subprocess
import sys
from pathlib import Path

from harness.config import load_document
from harness.report_builder import build_report


ROOT = Path(__file__).resolve().parents[1]
REQUIRED_STATUS_REPRESENTATION = {"MISSING", "INCONCLUSIVE", "NOT_VALIDATED", "SKIPPED_RESOURCE", "FAIL"}


def run_project_quality(candidate_phase="P16", run_tests=True):
    checks = []
    manifest = _load_json(ROOT / "codex" / "phase_manifest.json")
    state = _load_json(ROOT / "codex" / "loop_state.json")
    phase_ids = [phase["id"] for phase in manifest["phases"]]
    _check(checks, "manifest consistency", phase_ids == manifest.get("phase_ids"), "phase_ids match phases")
    _check(checks, "candidate phase", candidate_phase in phase_ids, candidate_phase)
    prior_ok = all(state["phases"].get(f"P{idx:02d}", {}).get("status") == "PASS" for idx in range(16))
    _check(checks, "P00-P15 passed", prior_ok, "loop_state prior phases")
    _check(checks, "forbidden patterns", _forbidden_scan_ok(), "scripts/forbidden_guard.py scan")
    _check(checks, "scale scenarios", _scale_scenarios_ok(), "scale ladder files")
    report = build_report(ROOT / "artifacts", ROOT / "scenarios")
    counts = report.status_counts()
    status_ok = all(counts[status] > 0 for status in REQUIRED_STATUS_REPRESENTATION)
    _check(checks, "report status honesty", status_ok, json.dumps(counts, sort_keys=True))
    _check(checks, "scale-2000-empty disclaimer", _scale_2000_disclaimer_ok(), "does_not_validate fields")
    if run_tests:
        _check(checks, "P16 tests runnable", _run_p16_tests_ok(), "python3 -m unittest discover -s tests -p 'test_p16_report_and_scale.py'")
    status = "OK" if all(check["ok"] for check in checks) else "FAIL"
    return {"status": status, "candidate_phase": candidate_phase, "checks": checks}


def _check(checks, name, ok, evidence):
    checks.append({"name": name, "ok": bool(ok), "evidence": evidence})


def _load_json(path):
    with path.open(encoding="utf-8") as f:
        return json.load(f)


def _forbidden_scan_ok():
    cp = subprocess.run(
        [sys.executable, "scripts/forbidden_guard.py", "scan", "--json"],
        cwd=ROOT,
        text=True,
        capture_output=True,
    )
    return cp.returncode == 0


def _scale_scenarios_ok():
    expected = {
        "scale-100.yaml": 100,
        "scale-300.yaml": 300,
        "scale-500.yaml": 500,
        "scale-1000.yaml": 1000,
        "scale-2000-empty.yaml": 2000,
    }
    for filename, total_nodes in expected.items():
        path = ROOT / "scenarios" / filename
        if not path.exists():
            return False
        data = load_document(path)
        if int(data["cluster"]["total_nodes"]) != total_nodes:
            return False
    return True


def _scale_2000_disclaimer_ok():
    data = load_document(ROOT / "scenarios" / "scale-2000-empty.yaml")
    missing = {"throughput", "production_latency", "production_rto", "physical_3az_durability"} - set(data.get("does_not_validate", []))
    return not missing and data.get("validation_profile") == "best-effort-empty-node-smoke"


def _run_p16_tests_ok():
    cp = subprocess.run(
        [sys.executable, "-m", "unittest", "discover", "-s", "tests", "-p", "test_p16_report_and_scale.py"],
        cwd=ROOT,
        text=True,
        capture_output=True,
    )
    return cp.returncode == 0
