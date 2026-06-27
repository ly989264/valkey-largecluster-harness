import json
import subprocess
import sys
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def run_cli(*args):
    return subprocess.run([sys.executable, "-m", "harness.harnessctl", *args], cwd=ROOT, text=True, capture_output=True)


class HarnessCtlP01Test(unittest.TestCase):
    def test_version_json_is_stable(self):
        cp = run_cli("version", "--json")
        self.assertEqual(cp.returncode, 0, cp.stderr)
        self.assertEqual(json.loads(cp.stdout), {"command": "version", "status": "OK", "version": "0.1.0"})

    def test_doctor_dry_run_does_not_probe_external_runtime(self):
        cp = run_cli("doctor", "--dry-run", "--json")
        self.assertEqual(cp.returncode, 0, cp.stderr)
        payload = json.loads(cp.stdout)
        self.assertEqual(payload["status"], "OK")
        self.assertEqual(payload["mode"], "dry-run")
        self.assertIn("no Docker, SSH, Valkey, or network access attempted", payload["reason"])
        self.assertIn({"name": "external_runtime", "status": "NOT_VALIDATED"}, payload["checks"])

    def test_not_implemented_shells_return_json(self):
        for command in ("validate", "plan", "run-scenario", "report"):
            cp = run_cli(command, "--json")
            self.assertEqual(cp.returncode, 0, cp.stderr)
            payload = json.loads(cp.stdout)
            self.assertEqual(payload["command"], command)
            self.assertEqual(payload["status"], "NOT_IMPLEMENTED")
            self.assertIn("P01", payload["reason"])

    def test_help_commands_exit_zero(self):
        for command in ("validate", "plan", "run-scenario", "report"):
            cp = run_cli(command, "--help")
            self.assertEqual(cp.returncode, 0, cp.stderr)
            self.assertIn(command, cp.stdout)


if __name__ == "__main__":
    unittest.main()
