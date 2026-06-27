"""Controller-side nodehost client contract."""

from nodehost.local_process import LocalProcessManager


class NodehostClient:
    def __init__(self, root):
        self.manager = LocalProcessManager.with_root(root)

    def status(self, run_id=None):
        return self.manager.status(run_id)

    def prepare(self, run_id):
        return self.manager.prepare(run_id)

    def start(self, run_id, node_ids):
        return self.manager.start(run_id, list(node_ids))

    def stop(self, run_id, node_ids=None):
        return self.manager.stop(run_id, list(node_ids) if node_ids is not None else None)

    def metrics(self, run_id):
        return self.manager.metrics(run_id)

    def cleanup(self, run_id):
        return self.manager.cleanup(run_id)
