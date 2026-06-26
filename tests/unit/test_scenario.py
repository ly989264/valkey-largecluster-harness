from __future__ import annotations

import pytest

from harness.scenario import ValidationError, load_scenario, parse_scenario


def test_load_sample_scenario() -> None:
    scenario = load_scenario("scenarios/smoke-6.yaml")

    assert scenario.name == "smoke-6"
    assert scenario.node_count == 6
    assert scenario.replicas_per_primary == 1


def test_scenario_rejects_unknown_fields() -> None:
    with pytest.raises(ValidationError) as exc:
        parse_scenario(
            {
                "name": "bad",
                "run_id": "bad",
                "topology_mode": "single_az",
                "topology": "primary_replica",
                "node_count": 6,
                "replicas_per_primary": 1,
                "validation": {},
                "traffic": {},
                "virtual_az_placement": {},
                "unknown": "nope",
            }
        )

    assert "scenario.unknown is not a supported field" in str(exc.value)


def test_scenario_requires_node_count_as_parameter() -> None:
    with pytest.raises(ValidationError) as exc:
        parse_scenario(
            {
                "name": "bad",
                "run_id": "bad",
                "topology_mode": "single_az",
                "topology": "primary_replica",
                "replicas_per_primary": 1,
                "validation": {},
                "traffic": {},
                "virtual_az_placement": {},
            }
        )

    assert "scenario.node_count is required" in str(exc.value)
