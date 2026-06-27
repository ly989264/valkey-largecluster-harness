import tempfile
import unittest

from harness.cluster_check import ClusterChecker
from harness.cluster_create import ClusterCreator
from harness.events import EventRecorder, replay_events
from harness.fake_cluster import FakeCluster
from harness.planner import build_cluster_plan
from harness.valkey_cli import FakeValkeyCli


def small_plan():
    return build_cluster_plan("inventories/two-mac-physical-aligned.yaml", "scenarios/smoke-6.yaml")["cluster_plan"]


class ClusterStateMachineP09Test(unittest.TestCase):
    def test_create_flow_follows_plan_order_without_replanning(self):
        cli = FakeValkeyCli()
        plan = small_plan()
        ClusterCreator(cli).create(plan)
        add_order = [cmd[1] for cmd in cli.commands if cmd[0] == "add_node"]
        self.assertEqual(add_order, [node["node_id"] for node in plan["nodes"]])
        self.assertNotIn(("plan",), cli.commands)

    def test_checker_passes_complete_fake_cluster(self):
        cli = FakeValkeyCli()
        ClusterCreator(cli).create(small_plan())
        self.assertEqual(ClusterChecker().check(cli.cluster_info()), {"status": "OK"})

    def test_checker_surfaces_incomplete_convergence(self):
        cluster = FakeCluster()
        plan = small_plan()
        for node in plan["nodes"]:
            cluster.add_node(node)
        result = ClusterChecker().check(cluster.snapshot())
        self.assertEqual(result["status"], "FAIL")
        self.assertEqual(result["reason"], "known_nodes_missing")

    def test_checker_distinguishes_slots_replica_and_cluster_fail(self):
        cli = FakeValkeyCli()
        ClusterCreator(cli).create(small_plan())
        info = cli.cluster_info()
        first_primary = next(node_id for node_id, state in info.items() if state["role"] == "primary")
        info[first_primary]["slots"] = []
        self.assertEqual(ClusterChecker().check(info)["reason"], "slots_missing")
        info = cli.cluster_info()
        first_replica = next(node_id for node_id, state in info.items() if state["role"] == "replica")
        info[first_replica]["replicates"] = None
        self.assertEqual(ClusterChecker().check(info)["reason"], "replica_missing")
        info = cli.cluster_info()
        info[first_primary]["cluster_state"] = "fail"
        self.assertEqual(ClusterChecker().check(info)["reason"], "cluster_fail")

    def test_creator_records_cluster_events(self):
        with tempfile.TemporaryDirectory() as td:
            recorder = EventRecorder(__import__("pathlib").Path(td) / "events.jsonl")
            cli = FakeValkeyCli()
            ClusterCreator(cli, recorder).create(small_plan())
            actions = [item["event"].get("action") for item in replay_events(recorder.path) if item["valid"]]
        self.assertIn("meet", actions)
        self.assertIn("slots_assigned", actions)
        self.assertIn("replica_configured", actions)
        self.assertIn("cluster_ok", actions)


if __name__ == "__main__":
    unittest.main()
