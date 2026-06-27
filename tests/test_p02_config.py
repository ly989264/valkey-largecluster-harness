import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from harness.config import ConfigError, load_inventory, load_scenario, validate_config


ROOT = Path(__file__).resolve().parents[1]


def run_validate(inventory, scenario):
    return subprocess.run(
        [sys.executable, "-m", "harness.harnessctl", "validate", "--inventory", inventory, "--scenario", scenario, "--json"],
        cwd=ROOT,
        text=True,
        capture_output=True,
    )


class ConfigP02Test(unittest.TestCase):
    def test_samples_validate(self):
        for inventory in [
            "inventories/single-mac-dev.yaml",
            "inventories/two-mac-physical-aligned.yaml",
            "inventories/three-mac-uniform-interleaved.yaml",
        ]:
            result = validate_config(ROOT / inventory, ROOT / "scenarios/smoke-6.yaml")
            self.assertEqual(result["scenario"]["cluster"]["total_nodes"], 6)
            self.assertIn("node_timeout_ms", result["defaults"])

    def test_scale_100_sample_validates(self):
        result = validate_config(ROOT / "inventories/three-mac-uniform-interleaved.yaml", ROOT / "scenarios/scale-100.yaml")
        self.assertEqual(result["scenario"]["cluster"]["total_nodes"], 100)

    def test_cli_validate_outputs_json(self):
        cp = run_validate("inventories/single-mac-dev.yaml", "scenarios/smoke-6.yaml")
        self.assertEqual(cp.returncode, 0, cp.stderr)
        payload = json.loads(cp.stdout)
        self.assertEqual(payload["status"], "OK")
        self.assertEqual(payload["command"], "validate")

    def test_missing_physical_hosts_fails(self):
        with tempfile.TemporaryDirectory() as td:
            path = Path(td) / "bad.yaml"
            path.write_text('{"inventory_id":"bad","port_ranges":{"client_start":1,"bus_start":100,"count":10}}', encoding="utf-8")
            with self.assertRaisesRegex(ConfigError, "physical_hosts"):
                load_inventory(path)

    def test_illegal_topology_mode_fails(self):
        with tempfile.TemporaryDirectory() as td:
            path = Path(td) / "bad.yaml"
            path.write_text('{"scenario_id":"bad","topology_mode":"random","cluster":{"total_nodes":6}}', encoding="utf-8")
            with self.assertRaisesRegex(ConfigError, "topology_mode"):
                load_scenario(path)

    def test_overlapping_ports_fail(self):
        with tempfile.TemporaryDirectory() as td:
            path = Path(td) / "bad.yaml"
            path.write_text(
                '{"inventory_id":"bad","physical_hosts":[{"id":"h1","address":"a","platform":"darwin","virtual_azs":["az-1"]}],"port_ranges":{"client_start":100,"bus_start":105,"count":10}}',
                encoding="utf-8",
            )
            with self.assertRaisesRegex(ConfigError, "overlap"):
                load_inventory(path)

    def test_total_nodes_and_replica_settings_fail(self):
        with tempfile.TemporaryDirectory() as td:
            zero = Path(td) / "zero.yaml"
            zero.write_text('{"scenario_id":"bad","topology_mode":"single_az","cluster":{"total_nodes":0}}', encoding="utf-8")
            with self.assertRaisesRegex(ConfigError, "total_nodes"):
                load_scenario(zero)
            bad_replica = Path(td) / "replica.yaml"
            bad_replica.write_text('{"scenario_id":"bad","topology_mode":"single_az","cluster":{"total_nodes":5,"replicas_per_primary":1}}', encoding="utf-8")
            with self.assertRaisesRegex(ConfigError, "divisible"):
                load_scenario(bad_replica)


if __name__ == "__main__":
    unittest.main()
