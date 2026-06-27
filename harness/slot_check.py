"""Slot coverage checks."""


def check_slots(cluster_info):
    covered = []
    for node_id, state in cluster_info.items():
        if state.get("role") == "primary":
            for slot_range in state.get("slots", []):
                covered.extend(range(slot_range["start"], slot_range["end"] + 1))
    if len(covered) != 16384 or set(covered) != set(range(16384)):
        return {"status": "FAIL", "reason": "slots_missing"}
    return {"status": "OK"}
