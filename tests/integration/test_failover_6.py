from __future__ import annotations

from harness.cluster.client_probe import ClientProbeResult, probe_client_success
from harness.metrics.collector import build_failover_timeline


class RedirectingClient:
    def set_get(self, key: str, value: str) -> str:
        raise RuntimeError("MOVED 42 127.0.0.1:7001")


class HealthyClient:
    def set_get(self, key: str, value: str) -> str:
        return value


def test_failover_timeline_calculates_durations() -> None:
    timeline = build_failover_timeline(
        {
            "fault_injected_at": 10.0,
            "first_pfail_observed_at": 10.2,
            "first_fail_observed_at": 10.7,
            "replica_promoted_at": 11.0,
            "slots_recovered_at": 11.4,
            "cluster_ok_at": 11.5,
            "client_success_restored_at": 11.6,
        },
        stale_owner_checks=[{"slot": 42, "stale": False}],
    )

    assert timeline.status == "VALIDATED"
    assert timeline.durations_ms["pfail_detection_ms"] == 199
    assert timeline.durations_ms["cluster_recovery_ms"] == 1500


def test_failover_timeline_marks_missing_timestamp_inconclusive() -> None:
    timeline = build_failover_timeline({"fault_injected_at": 1.0})

    assert timeline.status == "INCONCLUSIVE"
    assert timeline.timestamps["cluster_ok_at"] == "MISSING"
    assert timeline.durations_ms["cluster_recovery_ms"] == "MISSING"


def test_client_probe_observes_redirects_and_success() -> None:
    redirect = probe_client_success(RedirectingClient())
    healthy = probe_client_success(HealthyClient())

    assert redirect == ClientProbeResult(False, "MOVED 42 127.0.0.1:7001", "MOVED")
    assert healthy.ok is True
