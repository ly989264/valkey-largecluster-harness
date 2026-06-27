import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from harness.scenario_runner import ScenarioRunner


ROOT = Path(__file__).resolve().parents[1]


class SingleMacSmokeP10Test(unittest.TestCase):
    def test_fake_smoke_run_returns_pass_and_writes_artifacts(self):
        with tempfile.TemporaryDirectory() as td:
            runner = ScenarioRunner(run_root=Path(td) / "runs", nodehost_root=Path(td) / "nodehost")
            result = runner.run(ROOT / "inventories/single-mac-dev.yaml", ROOT / "scenarios/smoke-6.yaml", "run-1", backend="fake")
            self.assertEqual(result["status"], "PASS")
            run_dir = Path(result["artifacts"])
            self.assertTrue((run_dir / "events.jsonl").exists())
            self.assertTrue((run_dir / "run_status.json").exists())
            self.assertTrue((run_dir / "cluster_plan.json").exists())
            self.assertTrue((run_dir / "commands.jsonl").exists())
            self.assertEqual(json.loads((run_dir / "run_status.json").read_text(encoding="utf-8"))["status"], "PASS")

    def test_cleanup_runs_after_success(self):
        with tempfile.TemporaryDirectory() as td:
            nodehost_root = Path(td) / "nodehost"
            runner = ScenarioRunner(run_root=Path(td) / "runs", nodehost_root=nodehost_root)
            runner.run(ROOT / "inventories/single-mac-dev.yaml", ROOT / "scenarios/smoke-6.yaml", "run-clean", backend="fake")
            self.assertFalse((nodehost_root / "run-clean" / "process_table.json").exists())

    def test_optional_real_backend_skips_when_binary_absent(self):
        with tempfile.TemporaryDirectory() as td:
            result = ScenarioRunner(run_root=Path(td) / "runs", nodehost_root=Path(td) / "nodehost").run(
                ROOT / "inventories/single-mac-dev.yaml",
                ROOT / "scenarios/smoke-6.yaml",
                "run-real",
                backend="real",
            )
            if result["status"] == "SKIPPED_RESOURCE":
                self.assertIn("valkey-server", result["reason"])
            else:
                self.assertEqual(result["status"], "PASS")

    def test_cli_run_scenario_fake(self):
        cp = subprocess.run(
            [
                sys.executable,
                "-m",
                "harness.harnessctl",
                "run-scenario",
                "--inventory",
                "inventories/single-mac-dev.yaml",
                "--scenario",
                "scenarios/smoke-6.yaml",
                "--run-id",
                "p10-unit-cli",
                "--backend",
                "fake",
                "--json",
            ],
            cwd=ROOT,
            text=True,
            capture_output=True,
        )
        self.assertEqual(cp.returncode, 0, cp.stderr)
        self.assertEqual(json.loads(cp.stdout)["status"], "PASS")


if __name__ == "__main__":
    unittest.main()
