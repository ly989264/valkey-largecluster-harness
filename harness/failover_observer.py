"""Reconstruct failover timeline from recorded events."""

from harness.failover_timeline import FailoverTimeline


ACTION_TO_FIELD = {
    "fault_injected": "fault_injected_at",
    "pfail_observed": "first_pfail_observed_at",
    "fail_observed": "first_fail_observed_at",
    "replica_promoted": "replica_promoted_at",
    "slots_recovered": "slots_recovered_at",
    "cluster_ok": "cluster_ok_at",
    "client_success_restored": "client_success_restored_at",
}


class FailoverObserver:
    def reconstruct(self, records):
        values = {field: None for field in ACTION_TO_FIELD.values()}
        unavailable_slots = 0
        stale_owner_duration_ms = 0
        for record in records:
            event = record.get("event", record) if isinstance(record, dict) else record
            if not isinstance(event, dict):
                continue
            action = event.get("action")
            if action in ACTION_TO_FIELD and values[ACTION_TO_FIELD[action]] is None:
                values[ACTION_TO_FIELD[action]] = event.get("at")
            if "unavailable_slots_count" in event:
                unavailable_slots = max(unavailable_slots, int(event["unavailable_slots_count"]))
            if "stale_owner_duration_ms" in event:
                stale_owner_duration_ms = max(stale_owner_duration_ms, int(event["stale_owner_duration_ms"]))
        return FailoverTimeline(
            unavailable_slots_count_max=unavailable_slots,
            stale_owner_duration_ms=stale_owner_duration_ms,
            **values,
        )
