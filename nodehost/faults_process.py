"""Fake process fault backend."""


class ProcessFaultBackend:
    def __init__(self, process_table):
        self.process_table = process_table

    def apply(self, run_id, action, node_ids):
        data = self.process_table.load(run_id)
        for node_id in node_ids:
            node = data["nodes"].setdefault(node_id, {"node_id": node_id, "state": "unknown", "metrics": {}})
            if action == "kill":
                node["state"] = "killed"
            elif action == "pause":
                node["state"] = "paused"
            elif action == "resume":
                if node.get("state") == "paused":
                    node["state"] = "running"
            elif action == "restart":
                node["state"] = "running"
                node["restart_count"] = int(node.get("restart_count", 0)) + 1
            else:
                raise ValueError(f"unsupported process fault action {action}")
        self.process_table.save(run_id, data)
        return {"run_id": run_id, "nodes": {node_id: data["nodes"][node_id] for node_id in node_ids}}
