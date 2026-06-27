import tempfile
import unittest
from pathlib import Path

from harness.events import EventRecorder, replay_events
from harness.faults import FaultExecutor, FaultPlan, select_fault_targets
from harness.planner import build_cluster_plan
from nodehost.faults_process import ProcessFaultBackend
from nodehost.process_table import ProcessTable


def plan():
    return build_cluster_plan("inventories/two-mac-physical-aligned.yaml", "scenarios/smoke-6.yaml")["cluster_plan"]


class ProcessFaultsP11Test(unittest.TestCase):
    def test_virtual_az_selection_reads_cluster_plan(self):
        cluster_plan = plan()
        az = cluster_plan["nodes"][0]["virtual_az_id"]
        targets = select_fault_targets(cluster_plan, FaultPlan("pause", "virtual_az", az))
        self.assertTrue(targets)
        self.assertEqual(targets, [node["node_id"] for node in cluster_plan["nodes"] if node["virtual_az_id"] == az])

    def test_process_fault_backend_kill_pause_resume_restart(self):
        with tempfile.TemporaryDirectory() as td:
            table = ProcessTable(td)
            table.save("run", {"run_id": "run", "nodes": {"node-1": {"node_id": "node-1", "state": "running", "metrics": {}}}})
            backend = ProcessFaultBackend(table)
            backend.apply("run", "pause", ["node-1"])
            self.assertEqual(table.load("run")["nodes"]["node-1"]["state"], "paused")
            backend.apply("run", "resume", ["node-1"])
            backend.apply("run", "resume", ["node-1"])
            self.assertEqual(table.load("run")["nodes"]["node-1"]["state"], "running")
            backend.apply("run", "restart", ["node-1"])
            backend.apply("run", "restart", ["node-1"])
            self.assertEqual(table.load("run")["nodes"]["node-1"]["restart_count"], 2)
            backend.apply("run", "kill", ["node-1"])
            self.assertEqual(table.load("run")["nodes"]["node-1"]["state"], "killed")

    def test_fault_executor_records_before_after_events(self):
        with tempfile.TemporaryDirectory() as td:
            cluster_plan = plan()
            table = ProcessTable(Path(td) / "state")
            table.save("run", {"run_id": "run", "nodes": {node["node_id"]: {"node_id": node["node_id"], "state": "running", "metrics": {}} for node in cluster_plan["nodes"]}})
            recorder = EventRecorder(Path(td) / "events.jsonl")
            result = FaultExecutor(ProcessFaultBackend(table), recorder).execute("run", cluster_plan, FaultPlan("pause", "node", cluster_plan["nodes"][0]["node_id"]))
            self.assertEqual(result["status"], "OK")
            phases = [item["event"]["phase"] for item in replay_events(recorder.path) if item["valid"]]
            self.assertEqual(phases, ["before", "after"])


if __name__ == "__main__":
    unittest.main()
