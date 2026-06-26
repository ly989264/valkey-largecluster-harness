from __future__ import annotations

from dataclasses import dataclass
from typing import Any


TIMESTAMP_FIELDS = [
    "fault_injected_at",
    "first_pfail_observed_at",
    "first_fail_observed_at",
    "replica_promoted_at",
    "slots_recovered_at",
    "cluster_ok_at",
    "client_success_restored_at",
]


@dataclass(frozen=True)
class FailoverTimeline:
    timestamps: dict[str, float | str]
    durations_ms: dict[str, int | str]
    status: str
    stale_owner_checks: list[dict[str, Any]]


def build_failover_timeline(
    timestamps: dict[str, float | None],
    stale_owner_checks: list[dict[str, Any]] | None = None,
) -> FailoverTimeline:
    normalized: dict[str, float | str] = {}
    for field in TIMESTAMP_FIELDS:
        value = timestamps.get(field)
        normalized[field] = value if value is not None else "MISSING"

    durations = {
        "pfail_detection_ms": _delta(normalized, "fault_injected_at", "first_pfail_observed_at"),
        "fail_confirmation_ms": _delta(normalized, "first_pfail_observed_at", "first_fail_observed_at"),
        "promotion_ms": _delta(normalized, "first_fail_observed_at", "replica_promoted_at"),
        "slot_recovery_ms": _delta(normalized, "replica_promoted_at", "slots_recovered_at"),
        "cluster_recovery_ms": _delta(normalized, "fault_injected_at", "cluster_ok_at"),
        "client_recovery_ms": _delta(normalized, "fault_injected_at", "client_success_restored_at"),
    }
    status = "INCONCLUSIVE" if any(value == "MISSING" for value in normalized.values()) else "VALIDATED"
    return FailoverTimeline(
        timestamps=normalized,
        durations_ms=durations,
        status=status,
        stale_owner_checks=stale_owner_checks or [],
    )


def _delta(values: dict[str, float | str], start: str, end: str) -> int | str:
    left = values[start]
    right = values[end]
    if not isinstance(left, (int, float)) or not isinstance(right, (int, float)):
        return "MISSING"
    return max(0, int((right - left) * 1000))
