"""Cluster convergence checks."""

from harness.slot_check import check_slots


class ClusterChecker:
    def check(self, cluster_info):
        node_ids = set(cluster_info)
        for node_id, state in cluster_info.items():
            if set(state.get("known_nodes", [])) != node_ids:
                return {"status": "FAIL", "reason": "known_nodes_missing", "node_id": node_id}
            if state.get("cluster_state") != "ok":
                return {"status": "FAIL", "reason": "cluster_fail", "node_id": node_id}
        slot_result = check_slots(cluster_info)
        if slot_result["status"] != "OK":
            return slot_result
        primaries = {node_id for node_id, state in cluster_info.items() if state.get("role") == "primary"}
        for node_id, state in cluster_info.items():
            if state.get("role") == "replica" and state.get("replicates") not in primaries:
                return {"status": "FAIL", "reason": "replica_missing", "node_id": node_id}
        return {"status": "OK"}
