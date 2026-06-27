"""Valkey CLI interface and fake implementation."""

from harness.fake_cluster import FakeCluster


class ValkeyCli:
    def add_node(self, node):
        raise NotImplementedError

    def meet(self, source_id, target_id):
        raise NotImplementedError

    def assign_slots(self, node_id, slot_range):
        raise NotImplementedError

    def replicate(self, replica_id, primary_id):
        raise NotImplementedError

    def cluster_info(self):
        raise NotImplementedError


class FakeValkeyCli(ValkeyCli):
    def __init__(self, cluster=None):
        self.cluster = cluster or FakeCluster()
        self.commands = []

    def add_node(self, node):
        self.commands.append(("add_node", node["node_id"]))
        self.cluster.add_node(node)

    def meet(self, source_id, target_id):
        self.commands.append(("meet", source_id, target_id))
        self.cluster.meet(source_id, target_id)

    def converge_known_nodes(self):
        self.commands.append(("converge_known_nodes",))
        self.cluster.converge_known_nodes()

    def assign_slots(self, node_id, slot_range):
        self.commands.append(("assign_slots", node_id, slot_range["start"], slot_range["end"]))
        self.cluster.assign_slots(node_id, slot_range)

    def replicate(self, replica_id, primary_id):
        self.commands.append(("replicate", replica_id, primary_id))
        self.cluster.replicate(replica_id, primary_id)

    def set_cluster_ok(self):
        self.commands.append(("set_cluster_ok",))
        self.cluster.set_cluster_ok()

    def cluster_info(self):
        return self.cluster.snapshot()
