"""Fake Valkey cluster state machine."""


class FakeCluster:
    def __init__(self):
        self.nodes = {}
        self.events = []

    def add_node(self, node):
        node_id = node["node_id"]
        self.nodes[node_id] = {
            "node": dict(node),
            "known_nodes": {node_id},
            "slots": [],
            "replicates": None,
            "cluster_state": "fail",
        }

    def meet(self, source_id, target_id):
        self.nodes[source_id]["known_nodes"].add(target_id)
        self.nodes[target_id]["known_nodes"].add(source_id)
        self.events.append({"event_type": "cluster", "action": "meet", "source": source_id, "target": target_id})

    def converge_known_nodes(self):
        all_ids = set(self.nodes)
        for state in self.nodes.values():
            state["known_nodes"] = set(all_ids)
        self.events.append({"event_type": "cluster", "action": "known_nodes_converged", "count": len(all_ids)})

    def assign_slots(self, node_id, slot_range):
        self.nodes[node_id]["slots"].append(dict(slot_range))
        self.events.append({"event_type": "cluster", "action": "slots_assigned", "node_id": node_id, "slot_range": dict(slot_range)})

    def replicate(self, replica_id, primary_id):
        self.nodes[replica_id]["replicates"] = primary_id
        self.events.append({"event_type": "cluster", "action": "replica_configured", "replica_id": replica_id, "primary_id": primary_id})

    def set_cluster_ok(self):
        for state in self.nodes.values():
            state["cluster_state"] = "ok"
        self.events.append({"event_type": "cluster", "action": "cluster_ok"})

    def snapshot(self):
        return {
            node_id: {
                "known_nodes": sorted(state["known_nodes"]),
                "slots": list(state["slots"]),
                "replicates": state["replicates"],
                "cluster_state": state["cluster_state"],
                "role": state["node"].get("role"),
            }
            for node_id, state in sorted(self.nodes.items())
        }
