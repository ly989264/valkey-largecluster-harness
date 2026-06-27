"""Stability assertions for failover evidence."""


class StabilityAssertions:
    def evaluate(self, timeline):
        metrics = timeline.metrics()
        if metrics["status"] == "INCONCLUSIVE":
            return {"status": "INCONCLUSIVE", "reasons": [f"missing {field}" for field in metrics["missing"]]}
        reasons = []
        if metrics["stale_owner_duration_ms"] > 0:
            reasons.append("stale owner observed")
        if metrics["unavailable_slots_count_max"] > 0:
            reasons.append("slots unavailable during failover")
        if reasons:
            return {"status": "FAIL", "reasons": reasons, "metrics": metrics}
        return {"status": "PASS", "reasons": [], "metrics": metrics}
