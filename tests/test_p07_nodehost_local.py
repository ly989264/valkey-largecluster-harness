import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from harness.nodehost_client import NodehostClient
from nodehost.local_process import LocalProcessManager


ROOT = Path(__file__).resolve().parents[1]


class NodehostLocalP07Test(unittest.TestCase):
    def test_start_stop_cleanup_are_idempotent_and_run_scoped(self):
        with tempfile.TemporaryDirectory() as td:
            manager = LocalProcessManager.with_root(td)
            manager.prepare("run-a")
            manager.start("run-a", ["node-1", "node-2"])
            manager.start("run-a", ["node-1"])
            manager.start("run-b", ["node-x"])
            self.assertEqual(len(manager.status("run-a")["nodes"]), 2)
            manager.stop("run-a")
            self.assertEqual(manager.status("run-a")["nodes"]["node-1"]["state"], "stopped")
            manager.cleanup("run-a")
            self.assertEqual(manager.status("run-a")["nodes"], {})
            self.assertIn("node-x", manager.status("run-b")["nodes"])

    def test_fake_runtime_metrics_for_multiple_nodes(self):
        with tempfile.TemporaryDirectory() as td:
            client = NodehostClient(td)
            client.start("run", ["node-1", "node-2"])
            metrics = client.metrics("run")["metrics"]
            self.assertEqual(set(metrics), {"node-1", "node-2"})
            self.assertEqual(metrics["node-1"]["state"], "running")
            self.assertIn("rss_bytes", metrics["node-2"])

    def test_nodehostctl_status_json_requires_no_real_valkey(self):
        cp = subprocess.run(
            [sys.executable, "-m", "nodehost.nodehostctl", "status", "--json"],
            cwd=ROOT,
            text=True,
            capture_output=True,
        )
        self.assertEqual(cp.returncode, 0, cp.stderr)
        payload = json.loads(cp.stdout)
        self.assertEqual(payload["status"], "OK")
        self.assertEqual(payload["command"], "status")


if __name__ == "__main__":
    unittest.main()
