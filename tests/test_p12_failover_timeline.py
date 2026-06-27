import unittest

from harness.failover_observer import FailoverObserver
from harness.stability_assertions import StabilityAssertions


def complete_events(**extra):
    events = [
        {"action": "fault_injected", "at": "2026-01-01T00:00:00Z"},
        {"action": "pfail_observed", "at": "2026-01-01T00:00:01Z"},
        {"action": "fail_observed", "at": "2026-01-01T00:00:03Z"},
        {"action": "replica_promoted", "at": "2026-01-01T00:00:05Z"},
        {"action": "slots_recovered", "at": "2026-01-01T00:00:08Z"},
        {"action": "cluster_ok", "at": "2026-01-01T00:00:09Z"},
        {"action": "client_success_restored", "at": "2026-01-01T00:00:10Z"},
    ]
    if extra:
        events.append(extra)
    return events


class FailoverTimelineP12Test(unittest.TestCase):
    def test_complete_timeline_computes_all_metrics(self):
        timeline = FailoverObserver().reconstruct(complete_events())
        metrics = timeline.metrics()
        self.assertEqual(metrics["status"], "OK")
        self.assertEqual(metrics["pfail_detection_ms"], 1000)
        self.assertEqual(metrics["fail_confirmation_ms"], 2000)
        self.assertEqual(metrics["promotion_ms"], 2000)
        self.assertEqual(metrics["slot_recovery_ms"], 3000)
        self.assertEqual(metrics["cluster_recovery_ms"], 9000)
        self.assertEqual(metrics["client_recovery_ms"], 10000)

    def test_missing_pfail_is_inconclusive_not_pass(self):
        events = [event for event in complete_events() if event["action"] != "pfail_observed"]
        result = StabilityAssertions().evaluate(FailoverObserver().reconstruct(events))
        self.assertEqual(result["status"], "INCONCLUSIVE")
        self.assertIn("missing first_pfail_observed_at", result["reasons"])

    def test_missing_promotion_is_inconclusive(self):
        events = [event for event in complete_events() if event["action"] != "replica_promoted"]
        result = StabilityAssertions().evaluate(FailoverObserver().reconstruct(events))
        self.assertEqual(result["status"], "INCONCLUSIVE")

    def test_client_not_recovered_is_inconclusive_even_if_cluster_ok(self):
        events = [event for event in complete_events() if event["action"] != "client_success_restored"]
        result = StabilityAssertions().evaluate(FailoverObserver().reconstruct(events))
        self.assertEqual(result["status"], "INCONCLUSIVE")
        self.assertIn("missing client_success_restored_at", result["reasons"])

    def test_stale_owner_fails(self):
        timeline = FailoverObserver().reconstruct(complete_events(stale_owner_duration_ms=250))
        result = StabilityAssertions().evaluate(timeline)
        self.assertEqual(result["status"], "FAIL")
        self.assertIn("stale owner observed", result["reasons"])


if __name__ == "__main__":
    unittest.main()
