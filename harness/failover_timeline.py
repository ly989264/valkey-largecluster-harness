"""Failover timeline and metric calculation."""

import datetime
from dataclasses import dataclass


TIMESTAMP_FIELDS = (
    "fault_injected_at",
    "first_pfail_observed_at",
    "first_fail_observed_at",
    "replica_promoted_at",
    "slots_recovered_at",
    "cluster_ok_at",
    "client_success_restored_at",
)


@dataclass(frozen=True)
class FailoverTimeline:
    fault_injected_at: str = None
    first_pfail_observed_at: str = None
    first_fail_observed_at: str = None
    replica_promoted_at: str = None
    slots_recovered_at: str = None
    cluster_ok_at: str = None
    client_success_restored_at: str = None
    unavailable_slots_count_max: int = 0
    stale_owner_duration_ms: int = 0

    def missing_fields(self):
        return [field for field in TIMESTAMP_FIELDS if getattr(self, field) is None]

    def metrics(self):
        missing = self.missing_fields()
        if missing:
            return {"status": "INCONCLUSIVE", "missing": missing}
        return {
            "status": "OK",
            "pfail_detection_ms": _delta(self.fault_injected_at, self.first_pfail_observed_at),
            "fail_confirmation_ms": _delta(self.first_pfail_observed_at, self.first_fail_observed_at),
            "promotion_ms": _delta(self.first_fail_observed_at, self.replica_promoted_at),
            "slot_recovery_ms": _delta(self.replica_promoted_at, self.slots_recovered_at),
            "cluster_recovery_ms": _delta(self.fault_injected_at, self.cluster_ok_at),
            "client_recovery_ms": _delta(self.fault_injected_at, self.client_success_restored_at),
            "unavailable_slots_count_max": self.unavailable_slots_count_max,
            "stale_owner_duration_ms": self.stale_owner_duration_ms,
        }


def _parse(value):
    return datetime.datetime.fromisoformat(value.replace("Z", "+00:00"))


def _delta(start, end):
    return int((_parse(end) - _parse(start)).total_seconds() * 1000)
