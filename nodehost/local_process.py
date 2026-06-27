"""Local fake process manager for nodehost."""

from nodehost.fake_valkey import FakeValkeyRuntime
from nodehost.process_table import ProcessTable


class LocalProcessManager:
    def __init__(self, table, runtime=None):
        self.table = table
        self.runtime = runtime or FakeValkeyRuntime()

    @classmethod
    def with_root(cls, root):
        return cls(ProcessTable(root))

    def prepare(self, run_id):
        data = self.table.load(run_id)
        return self.table.save(run_id, data)

    def start(self, run_id, node_ids):
        data = self.table.load(run_id)
        for node_id in node_ids:
            current = data["nodes"].get(node_id)
            if current and current.get("state") == "running":
                continue
            data["nodes"][node_id] = self.runtime.start_node(node_id)
        return self.table.save(run_id, data)

    def stop(self, run_id, node_ids=None):
        data = self.table.load(run_id)
        targets = node_ids or list(data["nodes"].keys())
        for node_id in targets:
            if node_id in data["nodes"]:
                data["nodes"][node_id] = self.runtime.stop_node(data["nodes"][node_id])
        return self.table.save(run_id, data)

    def status(self, run_id=None):
        if run_id is None:
            return {"status": "OK", "runs_root": str(self.table.root)}
        return self.table.load(run_id)

    def metrics(self, run_id):
        data = self.table.load(run_id)
        return {"run_id": run_id, "metrics": {node_id: self.runtime.metrics(node) for node_id, node in data["nodes"].items()}}

    def cleanup(self, run_id):
        return self.table.cleanup(run_id)
