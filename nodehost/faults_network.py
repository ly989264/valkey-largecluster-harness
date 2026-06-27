"""Nodehost network fault helpers."""

from harness.network_faults import targets_for_virtual_az


def plan_network_fault(cluster_plan, backend, action, virtual_az_id, **kwargs):
    targets = targets_for_virtual_az(cluster_plan, virtual_az_id)
    if action == "isolate":
        return backend.isolate(targets).to_dict()
    if action == "heal":
        return backend.heal(targets).to_dict()
    if action == "delay":
        return backend.delay(targets, kwargs["milliseconds"]).to_dict()
    if action == "loss":
        return backend.loss(targets, kwargs["percent"]).to_dict()
    if action == "clear":
        return backend.clear(targets).to_dict()
    raise ValueError(f"unknown network fault action {action}")
