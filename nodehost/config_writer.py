"""Write isolated Valkey node configuration directories."""

from pathlib import Path

from nodehost.valkey_config import ValkeyConfigRenderer


class ConfigWriter:
    def __init__(self, root, renderer=None):
        self.root = Path(root)
        self.renderer = renderer or ValkeyConfigRenderer()

    def write_node(self, run_id, node, scenario_config):
        node_dir = self.root / run_id / node["node_id"]
        node_dir.mkdir(parents=True, exist_ok=True)
        config = self.renderer.render(node, node_dir, scenario_config)
        path = node_dir / "valkey.conf"
        path.write_text(config, encoding="utf-8")
        return {"node_id": node["node_id"], "node_dir": str(node_dir), "config_path": str(path)}

    def write_cluster(self, run_id, cluster_plan, scenario_config):
        written = []
        for node in cluster_plan["nodes"]:
            written.append(self.write_node(run_id, node, scenario_config))
        return written
