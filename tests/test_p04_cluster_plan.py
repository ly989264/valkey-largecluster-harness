import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from harness.config import load_inventory, load_scenario
from harness.planner import build_cluster_plan, build_topology_plan
from harness.port_allocator import PortAllocationError, allocate_ports


ROOT = Path(__file__).resolve().parents[1]


class ClusterPlanP04Test(unittest.TestCase):
    def test_smoke_6_has_three_primaries_and_three_replicas(self):
        plan = build_cluster_plan(ROOT / "inventories/two-mac-physical-aligned.yaml", ROOT / "scenarios/smoke-6.yaml")
        roles = [node["role"] for node in plan["nodes"]]
        self.assertEqual(roles.count("primary"), 3)
        self.assertEqual(roles.count("replica"), 3)

    def test_slots_cover_full_range_without_gap_or_overlap(self):
        plan = build_cluster_plan(ROOT / "inventories/two-mac-physical-aligned.yaml", ROOT / "scenarios/smoke-6.yaml")
        ranges = plan["slot_ranges"]
        self.assertEqual(ranges[0], {"start": 0, "end": 5461})
        self.assertEqual(ranges[-1]["end"], 16383)
        for left, right in zip(ranges, ranges[1:]):
            self.assertEqual(left["end"] + 1, right["start"])

    def test_ports_are_unique_and_non_overlapping(self):
        plan = build_cluster_plan(ROOT / "inventories/two-mac-physical-aligned.yaml", ROOT / "scenarios/smoke-6.yaml")
        client_ports = {node["client_port"] for node in plan["nodes"]}
        bus_ports = {node["bus_port"] for node in plan["nodes"]}
        self.assertEqual(len(client_ports), 6)
        self.assertEqual(len(bus_ports), 6)
        self.assertFalse(client_ports & bus_ports)

    def test_port_allocator_fails_on_insufficient_or_overlapping_ranges(self):
        inventory = load_inventory(ROOT / "inventories/two-mac-physical-aligned.yaml")
        with self.assertRaises(PortAllocationError):
            allocate_ports(inventory.port_ranges, inventory.port_ranges.count + 1)
        with tempfile.TemporaryDirectory() as td:
            bad = Path(td) / "bad.json"
            bad.write_text(
                '{"inventory_id":"bad","physical_hosts":[{"id":"h1","address":"a","platform":"darwin","virtual_azs":["az-1"]}],"port_ranges":{"client_start":100,"bus_start":105,"count":10}}',
                encoding="utf-8",
            )
            with self.assertRaisesRegex(Exception, "overlap"):
                load_inventory(bad)

    def test_invalid_role_grouping_fails_in_config_layer(self):
        with tempfile.TemporaryDirectory() as td:
            bad = Path(td) / "bad.json"
            bad.write_text(
                '{"scenario_id":"bad","topology_mode":"single_az","cluster":{"total_nodes":5,"replicas_per_primary":1}}',
                encoding="utf-8",
            )
            with self.assertRaisesRegex(Exception, "divisible"):
                load_scenario(bad)

    def test_replica_anti_affinity_uses_different_virtual_az_when_possible(self):
        plan = build_cluster_plan(ROOT / "inventories/two-mac-physical-aligned.yaml", ROOT / "scenarios/smoke-6.yaml")
        by_id = {node["node_id"]: node for node in plan["nodes"]}
        for replica in plan["replica_placements"]:
            replica_node = by_id[replica["replica_node_id"]]
            primary_node = by_id[replica["primary_node_id"]]
            self.assertNotEqual(replica_node["virtual_az_id"], primary_node["virtual_az_id"])
            self.assertEqual(replica["anti_affinity"], "virtual_az")

    def test_cli_plan_emits_full_cluster_plan_json(self):
        cp = subprocess.run(
            [
                sys.executable,
                "-m",
                "harness.harnessctl",
                "plan",
                "--inventory",
                "inventories/two-mac-physical-aligned.yaml",
                "--scenario",
                "scenarios/smoke-6.yaml",
                "--json",
            ],
            cwd=ROOT,
            text=True,
            capture_output=True,
        )
        self.assertEqual(cp.returncode, 0, cp.stderr)
        payload = json.loads(cp.stdout)
        self.assertIn("cluster_plan", payload["plan"])
        self.assertIn("virtual_az_host_matrix", payload["plan"])

    def test_topology_plan_remains_available_for_p03_contract(self):
        topology = build_topology_plan(ROOT / "inventories/two-mac-physical-aligned.yaml", ROOT / "scenarios/smoke-6.yaml")
        self.assertIn("node_drafts", topology)


if __name__ == "__main__":
    unittest.main()
