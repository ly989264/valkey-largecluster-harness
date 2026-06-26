from __future__ import annotations

from harness.cluster.check import evaluate_stability_gates
from harness.inventory import load_inventory
from harness.metrics.sampler import SamplingPolicy
from harness.planner import build_cluster_plan
from harness.scenario import load_scenario


def test_scale_500_can_be_planned_from_two_mac_inventory() -> None:
    plan = build_cluster_plan(
        load_inventory("inventories/two-mac.physical-aligned.yaml"),
        load_scenario("scenarios/scale-500.yaml"),
    )

    assert len(plan["nodes"]) == 500
    assert plan["placement_degraded"] is False


def test_stability_gates_validate_stable_samples() -> None:
    result = evaluate_stability_gates(
        [
            {
                "cluster_state": "ok",
                "known_nodes": 100,
                "slots_ok": 16384,
                "rss_bytes": 100,
                "fd_count": 10,
                "socket_count": 10,
                "cluster_link_buffer_exceeded": False,
            },
            {
                "cluster_state": "ok",
                "known_nodes": 100,
                "slots_ok": 16384,
                "rss_bytes": 120,
                "fd_count": 11,
                "socket_count": 10,
                "cluster_link_buffer_exceeded": False,
            },
        ]
    )

    assert result.status == "VALIDATED"


def test_stability_gates_detect_growth_and_missing_metrics() -> None:
    failed = evaluate_stability_gates(
        [
            {
                "cluster_state": "ok",
                "known_nodes": 100,
                "slots_ok": 16384,
                "rss_bytes": 100,
                "fd_count": 10,
                "socket_count": 10,
                "cluster_link_buffer_exceeded": False,
            },
            {
                "cluster_state": "ok",
                "known_nodes": 100,
                "slots_ok": 16384,
                "rss_bytes": 250,
                "fd_count": 10,
                "socket_count": 10,
                "cluster_link_buffer_exceeded": False,
            },
        ]
    )
    missing = evaluate_stability_gates([{"cluster_state": "ok"}])

    assert failed.status == "FAILED"
    assert missing.status == "INCONCLUSIVE"
    assert missing.gates["known_nodes_stable"] == "MISSING"


def test_sampling_policy_separates_sampled_and_full_checks() -> None:
    policy = SamplingPolicy(sampled_check_seconds=30, full_check_seconds=300, stagger_seconds=0.1)

    assert policy.should_sample(60) is True
    assert policy.should_full_check(60) is False
    assert policy.should_full_check(300) is True
