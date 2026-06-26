from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

from harness.cluster.create import ClusterClient
from harness.cluster.nodes import endpoint, primaries
from harness.events import append_event


@dataclass(frozen=True)
class ClusterCheckResult:
    ok: bool
    checks: dict[str, str | int | bool]


@dataclass(frozen=True)
class StabilityGateResult:
    status: str
    gates: dict[str, str]


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


def evaluate_stability_gates(samples: list[dict[str, Any]]) -> StabilityGateResult:
    if not samples:
        return StabilityGateResult("INCONCLUSIVE", {"samples": "MISSING"})
    gates = {
        "cluster_state_no_flapping": _no_flapping(samples, "cluster_state", "ok"),
        "known_nodes_stable": _stable(samples, "known_nodes"),
        "slots_ok_16384": _all_equal(samples, "slots_ok", 16384),
        "rss_no_unbounded_growth": _bounded_growth(samples, "rss_bytes"),
        "fd_no_unbounded_growth": _bounded_growth(samples, "fd_count"),
        "socket_no_unbounded_growth": _bounded_growth(samples, "socket_count"),
        "cluster_link_buffer_not_exceeded": _all_false(samples, "cluster_link_buffer_exceeded"),
    }
    if any(value == "FAILED" for value in gates.values()):
        status = "FAILED"
    elif any(value == "MISSING" for value in gates.values()):
        status = "INCONCLUSIVE"
    else:
        status = "VALIDATED"
    return StabilityGateResult(status, gates)


def _no_flapping(samples: list[dict[str, Any]], key: str, expected: Any) -> str:
    values = [sample.get(key, "MISSING") for sample in samples]
    if "MISSING" in values:
        return "MISSING"
    return "VALIDATED" if all(value == expected for value in values) else "FAILED"


def _stable(samples: list[dict[str, Any]], key: str) -> str:
    values = [sample.get(key, "MISSING") for sample in samples]
    if "MISSING" in values:
        return "MISSING"
    return "VALIDATED" if len(set(values)) == 1 else "FAILED"


def _all_equal(samples: list[dict[str, Any]], key: str, expected: Any) -> str:
    values = [sample.get(key, "MISSING") for sample in samples]
    if "MISSING" in values:
        return "MISSING"
    return "VALIDATED" if all(value == expected for value in values) else "FAILED"


def _bounded_growth(samples: list[dict[str, Any]], key: str) -> str:
    values = [sample.get(key, "MISSING") for sample in samples]
    if "MISSING" in values:
        return "MISSING"
    numeric = [float(value) for value in values]
    baseline = max(numeric[0], 1.0)
    return "VALIDATED" if numeric[-1] <= baseline * 2 else "FAILED"


def _all_false(samples: list[dict[str, Any]], key: str) -> str:
    values = [sample.get(key, "MISSING") for sample in samples]
    if "MISSING" in values:
        return "MISSING"
    return "VALIDATED" if not any(values) else "FAILED"
