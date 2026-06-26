from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from harness.cluster.create import ClusterClient
from harness.cluster.nodes import endpoint, primaries
from harness.events import append_event


@dataclass(frozen=True)
class ClusterCheckResult:
    ok: bool
    checks: dict[str, str | int | bool]


def check_cluster(plan: dict, client: ClusterClient, events_path: str | Path) -> ClusterCheckResult:
    run_id = str(plan["run_id"])
    sample = primaries(plan)[:1] or plan.get("nodes", [])[:1]
    if not sample:
        result = ClusterCheckResult(False, {"plan_nodes": 0})
        append_event(events_path, run_id, "cluster_check_failed", reason="plan has no nodes")
        return result
    host, port = endpoint(sample[0])
    info = _parse_info(client.command(host, port, "CLUSTER", "INFO"))
    checks: dict[str, str | int | bool] = {
        "cluster_state": info.get("cluster_state", "MISSING"),
        "cluster_slots_assigned": _int_or_missing(info.get("cluster_slots_assigned")),
        "cluster_slots_ok": _int_or_missing(info.get("cluster_slots_ok")),
    }
    slots_output = client.command(host, port, "CLUSTER", "SLOTS")
    checks["slot_owner_unique"] = _slot_owner_unique(slots_output)
    ok = (
        checks["cluster_state"] == "ok"
        and checks["cluster_slots_assigned"] == 16384
        and checks["cluster_slots_ok"] == 16384
        and checks["slot_owner_unique"] is True
    )
    append_event(events_path, run_id, "cluster_check", ok=ok, **checks)
    return ClusterCheckResult(ok, checks)


def _parse_info(output: str) -> dict[str, str]:
    result: dict[str, str] = {}
    for line in output.splitlines():
        if ":" in line:
            key, value = line.split(":", 1)
            result[key] = value
    return result


def _int_or_missing(value: str | None) -> int | str:
    if value is None:
        return "MISSING"
    try:
        return int(value)
    except ValueError:
        return "MISSING"


def _slot_owner_unique(output: str) -> bool | str:
    if not output.strip():
        return "MISSING"
    ranges: list[tuple[int, int]] = []
    for line in output.splitlines():
        parts = line.split()
        if len(parts) < 2:
            continue
        try:
            ranges.append((int(parts[0]), int(parts[1])))
        except ValueError:
            continue
    if not ranges:
        return "MISSING"
    seen: set[int] = set()
    for start, end in ranges:
        for slot in range(start, end + 1):
            if slot in seen:
                return False
            seen.add(slot)
    return len(seen) == 16384
