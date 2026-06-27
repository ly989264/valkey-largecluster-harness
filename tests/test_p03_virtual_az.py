import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from harness.planner import build_topology_plan


ROOT = Path(__file__).resolve().parents[1]


class VirtualAZPlanningTest(unittest.TestCase):
    def test_single_az_warns_and_uses_one_virtual_az(self):
        with tempfile.TemporaryDirectory() as td:
            scenario = Path(td) / "single.yaml"
            scenario.write_text(
                '{"scenario_id":"single","topology_mode":"single_az","cluster":{"total_nodes":6,"replicas_per_primary":1,"virtual_az_count":1}}',
                encoding="utf-8",
            )
            plan = build_topology_plan(ROOT / "inventories/single-mac-dev.yaml", scenario)
        self.assertEqual(plan["virtual_azs"], ["az-1"])
        self.assertIn("no AZ isolation", plan["warnings"][0])

    def test_physical_aligned_two_hosts_three_virtual_azs_warns_about_weak_isolation(self):
        plan = build_topology_plan(ROOT / "inventories/two-mac-physical-aligned.yaml", ROOT / "scenarios/smoke-6.yaml")
        self.assertEqual(plan["virtual_azs"], ["az-1", "az-2", "az-3"])
        self.assertTrue(any("physical isolation is weak" in warning or "share" in warning for warning in plan["warnings"]))
        self.assertEqual(plan["node_drafts"], sorted(plan["node_drafts"], key=lambda x: (x["physical_host_id"], x["virtual_az_id"], x["node_index"])))

    def test_uniform_interleaved_emits_every_host_by_virtual_az_matrix_entry(self):
        plan = build_topology_plan(ROOT / "inventories/three-mac-uniform-interleaved.yaml", ROOT / "scenarios/scale-100.yaml")
        matrix = plan["virtual_az_host_matrix"]
        self.assertEqual(len(matrix), 9)
        pairs = {(row["physical_host_id"], row["virtual_az_id"]) for row in matrix}
        self.assertIn(("mac-1", "az-1"), pairs)
        self.assertIn(("mac-3", "az-3"), pairs)

    def test_custom_placement_follows_mapping_and_weights(self):
        with tempfile.TemporaryDirectory() as td:
            scenario = Path(td) / "custom.yaml"
            scenario.write_text(
                '{"scenario_id":"custom","topology_mode":"custom","custom_placement":[{"physical_host_id":"mac-2","virtual_az_id":"az-b","weight":2},{"physical_host_id":"mac-1","virtual_az_id":"az-a","weight":1}],"cluster":{"total_nodes":6,"replicas_per_primary":1,"virtual_az_count":2}}',
                encoding="utf-8",
            )
            plan = build_topology_plan(ROOT / "inventories/two-mac-physical-aligned.yaml", scenario)
        self.assertEqual(
            plan["placements"],
            [
                {"physical_host_id": "mac-1", "virtual_az_id": "az-a", "weight": 1},
                {"physical_host_id": "mac-2", "virtual_az_id": "az-b", "weight": 2},
            ],
        )
        self.assertEqual(len([n for n in plan["node_drafts"] if n["virtual_az_id"] == "az-b"]), 4)

    def test_plan_command_is_byte_stable(self):
        cmd = [
            sys.executable,
            "-m",
            "harness.harnessctl",
            "plan",
            "--inventory",
            "inventories/three-mac-uniform-interleaved.yaml",
            "--scenario",
            "scenarios/scale-100.yaml",
            "--json",
        ]
        one = subprocess.run(cmd, cwd=ROOT, text=True, capture_output=True)
        two = subprocess.run(cmd, cwd=ROOT, text=True, capture_output=True)
        self.assertEqual(one.returncode, 0, one.stderr)
        self.assertEqual(one.stdout, two.stdout)
        payload = json.loads(one.stdout)
        self.assertEqual(payload["status"], "OK")
        self.assertIn("virtual_az_host_matrix", payload["plan"])


if __name__ == "__main__":
    unittest.main()
