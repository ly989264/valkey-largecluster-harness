"""Cluster creation flow that consumes ClusterPlan without replanning."""


class ClusterCreator:
    def __init__(self, cli, event_recorder=None):
        self.cli = cli
        self.event_recorder = event_recorder

    def create(self, cluster_plan):
        nodes = list(cluster_plan["nodes"])
        for node in nodes:
            self.cli.add_node(node)
        if nodes:
            seed = nodes[0]["node_id"]
            for node in nodes[1:]:
                self.cli.meet(seed, node["node_id"])
                self._event("cluster", action="meet", source=seed, target=node["node_id"])
        if hasattr(self.cli, "converge_known_nodes"):
            self.cli.converge_known_nodes()
            self._event("cluster", action="known_nodes_sampled", count=len(nodes))
        for node in nodes:
            if node.get("role") == "primary" and "slot_range" in node:
                self.cli.assign_slots(node["node_id"], node["slot_range"])
                self._event("cluster", action="slots_assigned", node_id=node["node_id"])
        for replica in cluster_plan.get("replica_placements", []):
            self.cli.replicate(replica["replica_node_id"], replica["primary_node_id"])
            self._event("cluster", action="replica_configured", replica_id=replica["replica_node_id"], primary_id=replica["primary_node_id"])
        if hasattr(self.cli, "set_cluster_ok"):
            self.cli.set_cluster_ok()
            self._event("cluster", action="cluster_ok")
        return {"status": "OK", "nodes": len(nodes)}

    def _event(self, event_type, **fields):
        if self.event_recorder is not None:
            self.event_recorder.append(event_type, **fields)
