"""Fake Valkey runtime state for nodehost unit paths."""


class FakeValkeyRuntime:
    def start_node(self, node_id):
        return {"node_id": node_id, "state": "running", "metrics": {"requests": 0, "rss_bytes": 1024, "connected_clients": 0}}

    def stop_node(self, node):
        updated = dict(node)
        updated["state"] = "stopped"
        return updated

    def metrics(self, node):
        metrics = dict(node.get("metrics", {}))
        metrics["state"] = node.get("state", "unknown")
        return metrics
