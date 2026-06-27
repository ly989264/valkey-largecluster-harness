import tempfile
import unittest
from pathlib import Path

from nodehost.config_writer import ConfigWriter
from nodehost.valkey_config import ValkeyConfigRenderer


class ValkeyConfigP08Test(unittest.TestCase):
    def node(self, node_id="node-1", client_port=30001, bus_port=40001, announce_ip="10.0.0.50"):
        return {
            "node_id": node_id,
            "client_port": client_port,
            "bus_port": bus_port,
            "announce_ip": announce_ip,
        }

    def test_renderer_outputs_required_fields_from_node_spec_and_scenario_config(self):
        with tempfile.TemporaryDirectory() as td:
            node_dir = Path(td) / "node-1"
            config = ValkeyConfigRenderer().render(
                self.node(),
                node_dir,
                {"node_timeout_ms": 22000, "bind": "0.0.0.0", "loglevel": "warning"},
            )
        self.assertIn("port 30001\n", config)
        self.assertIn("cluster-enabled yes\n", config)
        self.assertIn("cluster-config-file nodes.conf\n", config)
        self.assertIn("cluster-node-timeout 22000\n", config)
        self.assertIn("cluster-announce-ip 10.0.0.50\n", config)
        self.assertIn("cluster-announce-port 30001\n", config)
        self.assertIn("cluster-announce-bus-port 40001\n", config)
        self.assertIn("cluster-port 40001\n", config)
        self.assertIn("appendonly no\n", config)
        self.assertIn('save ""\n', config)
        self.assertIn("protected-mode no\n", config)
        self.assertIn("bind 0.0.0.0\n", config)
        self.assertIn("loglevel warning\n", config)
        self.assertIn("logfile", config)
        self.assertIn("dir", config)
        self.assertIn("pidfile", config)

    def test_writer_creates_independent_node_directories(self):
        with tempfile.TemporaryDirectory() as td:
            writer = ConfigWriter(td)
            plan = {"nodes": [self.node("node-a", 30001, 40001, "10.0.0.1"), self.node("node-b", 30002, 40002, "10.0.0.2")]}
            written = writer.write_cluster("run-1", plan, {"node_timeout_ms": 15000})
            paths = [Path(item["config_path"]) for item in written]
            self.assertEqual(len({path.parent for path in paths}), 2)
            self.assertTrue(paths[0].exists())
            self.assertTrue(paths[1].exists())
            self.assertIn("cluster-announce-ip 10.0.0.2", paths[1].read_text(encoding="utf-8"))

    def test_renderer_does_not_remap_ports_or_invent_announce_ip(self):
        config = ValkeyConfigRenderer().render(self.node(client_port=31000, bus_port=41000, announce_ip="203.0.113.8"), Path("/tmp/node"), {})
        self.assertIn("port 31000\n", config)
        self.assertIn("cluster-port 41000\n", config)
        self.assertIn("cluster-announce-ip 203.0.113.8\n", config)
        with self.assertRaisesRegex(ValueError, "announce_ip"):
            ValkeyConfigRenderer().render({"node_id": "bad", "client_port": 1, "bus_port": 2}, Path("/tmp/bad"), {})


if __name__ == "__main__":
    unittest.main()
