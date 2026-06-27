"""Process fault planning and execution."""

import datetime
from dataclasses import dataclass


@dataclass(frozen=True)
class FaultPlan:
    action: str
    target_type: str
    target: str

    def validate(self):
        if self.action not in {"kill", "pause", "resume", "restart"}:
            raise ValueError("fault action must be kill, pause, resume, or restart")
        if self.target_type not in {"node", "virtual_az"}:
            raise ValueError("target_type must be node or virtual_az")
        if not self.target:
            raise ValueError("fault target is required")


def select_fault_targets(cluster_plan, fault_plan):
    fault_plan.validate()
    nodes = cluster_plan["nodes"]
    if fault_plan.target_type == "node":
        return [node["node_id"] for node in nodes if node["node_id"] == fault_plan.target]
    return [node["node_id"] for node in nodes if node.get("virtual_az_id") == fault_plan.target]


class FaultExecutor:
    def __init__(self, backend, event_recorder=None):
        self.backend = backend
        self.event_recorder = event_recorder

    def execute(self, run_id, cluster_plan, fault_plan):
        targets = select_fault_targets(cluster_plan, fault_plan)
        before = _now()
        self._event("fault", action=fault_plan.action, phase="before", target_type=fault_plan.target_type, target=fault_plan.target, targets=targets, at=before)
        result = self.backend.apply(run_id, fault_plan.action, targets)
        after = _now()
        self._event("fault", action=fault_plan.action, phase="after", target_type=fault_plan.target_type, target=fault_plan.target, targets=targets, at=after)
        return {"status": "OK", "targets": targets, "before": before, "after": after, "result": result}

    def _event(self, event_type, **fields):
        if self.event_recorder is not None:
            self.event_recorder.append(event_type, **fields)


def _now():
    return datetime.datetime.now(datetime.timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")
