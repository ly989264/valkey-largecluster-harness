"""Render Valkey cluster configuration from a NodeSpec-like dict."""


class ValkeyConfigRenderer:
    def render(self, node, node_dir, scenario_config):
        required = ["node_id", "client_port", "bus_port", "announce_ip"]
        missing = [key for key in required if key not in node]
        if missing:
            raise ValueError(f"NodeSpec missing required config fields: {missing}")
        node_timeout_ms = int(scenario_config.get("cluster_node_timeout_ms", scenario_config.get("node_timeout_ms", 15000)))
        bind = scenario_config.get("bind", "0.0.0.0")
        loglevel = scenario_config.get("loglevel", "notice")
        lines = [
            f"port {node['client_port']}",
            "cluster-enabled yes",
            "cluster-config-file nodes.conf",
            f"cluster-node-timeout {node_timeout_ms}",
            f"cluster-announce-ip {node['announce_ip']}",
            f"cluster-announce-port {node['client_port']}",
            f"cluster-announce-bus-port {node['bus_port']}",
            f"cluster-port {node['bus_port']}",
            "appendonly no",
            'save ""',
            "protected-mode no",
            f"bind {bind}",
            f"loglevel {loglevel}",
            f"logfile {node_dir / 'valkey.log'}",
            f"dir {node_dir}",
            f"pidfile {node_dir / 'valkey.pid'}",
        ]
        return "\n".join(lines) + "\n"
