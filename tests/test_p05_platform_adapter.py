import json
import subprocess
import sys
import unittest
from pathlib import Path

from harness.executor import CommandResult, FakeExecutor
from harness.platform_adapter import adapter_for_platform
from harness.platform_darwin import DarwinPlatformAdapter
from harness.platform_linux import LinuxPlatformAdapter


ROOT = Path(__file__).resolve().parents[1]


class PlatformAdapterP05Test(unittest.TestCase):
    def test_factory_selects_darwin_and_linux(self):
        self.assertIsInstance(adapter_for_platform("darwin"), DarwinPlatformAdapter)
        self.assertIsInstance(adapter_for_platform("linux"), LinuxPlatformAdapter)

    def test_darwin_does_not_claim_network_fault_support(self):
        adapter = DarwinPlatformAdapter()
        self.assertFalse(adapter.supports_network_fault_injection())
        self.assertEqual(adapter.network_fault_backend_hint(), "darwin-unsupported-use-linux-tc-netem")

    def test_linux_migration_path_is_explicit(self):
        adapter = LinuxPlatformAdapter()
        self.assertTrue(adapter.supports_host_network())
        self.assertTrue(adapter.supports_network_fault_injection())
        self.assertEqual(adapter.network_fault_backend_hint(), "linux-tc-netem")

    def test_fake_executor_makes_adapters_mockable(self):
        executor = FakeExecutor([CommandResult(command=("ps", "-p", "123"), exit_code=0, stdout="ok\n")])
        adapter = DarwinPlatformAdapter(executor=executor)
        self.assertTrue(adapter.process_exists(123))
        self.assertEqual(executor.commands, [("ps", "-p", "123")])

    def test_core_planner_does_not_import_platform_specific_modules(self):
        source = (ROOT / "harness" / "planner.py").read_text(encoding="utf-8")
        self.assertNotIn("platform_darwin", source)
        self.assertNotIn("platform_linux", source)

    def test_doctor_dry_run_reports_platform_capabilities(self):
        cp = subprocess.run(
            [sys.executable, "-m", "harness.harnessctl", "doctor", "--dry-run", "--json"],
            cwd=ROOT,
            text=True,
            capture_output=True,
        )
        self.assertEqual(cp.returncode, 0, cp.stderr)
        payload = json.loads(cp.stdout)
        self.assertEqual(payload["status"], "OK")
        self.assertIn("platform_capabilities", payload)
        self.assertEqual(payload["linux_migration_path"]["network_fault_backend_hint"], "linux-tc-netem")


if __name__ == "__main__":
    unittest.main()
