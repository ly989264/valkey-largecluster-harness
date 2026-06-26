from __future__ import annotations

from harness.inventory import parse_inventory
from harness.planner import TOTAL_SLOTS, build_cluster_plan
from harness.scenario import parse_scenario


def test_planner_assigns_all_slots_evenly_for_smoke() -> None:
    inventory = parse_inventory(_inventory("single_az", {"vaz-a": ["h1"]}))
    scenario = parse_scenario(_scenario("single_az", 6, "primary_replica", 1))

    plan = build_cluster_plan(inventory, scenario)

    primaries = [node for node in plan["nodes"] if node["role"] == "primary"]
    assert len(plan["nodes"]) == 6
    assert len(primaries) == 3
    assert primaries[0]["slots"] == [{"start": 0, "end": 5461}]
    assert primaries[-1]["slots"] == [{"start": 10923, "end": 16383}]
    covered = sum(r["end"] - r["start"] + 1 for node in primaries for r in node["slots"])
    assert covered == TOTAL_SLOTS


def test_planner_records_degraded_replica_affinity_when_single_host() -> None:
    inventory = parse_inventory(_inventory("single_az", {"vaz-a": ["h1"]}))
    scenario = parse_scenario(_scenario("single_az", 6, "primary_replica", 1))

    plan = build_cluster_plan(inventory, scenario)

    assert plan["placement_degraded"] is True
    assert plan["placement_degraded_reasons"]


def test_planner_supports_physical_aligned_virtual_azs() -> None:
    inventory = parse_inventory(_inventory("physical_aligned", {"vaz-a": ["h1"], "vaz-b": ["h2"]}))
    scenario = parse_scenario(_scenario("physical_aligned", 6, "primary_replica", 1))

    plan = build_cluster_plan(inventory, scenario)

    primaries = [node for node in plan["nodes"] if node["role"] == "primary"]
    assert [node["virtual_az_id"] for node in primaries] == ["vaz-a", "vaz-b", "vaz-a"]
    assert plan["placement_degraded"] is False


def test_planner_supports_interleaved_hosts() -> None:
    inventory = parse_inventory(
        _inventory("interleaved", {"vaz-a": ["h1", "h2"], "vaz-b": ["h2", "h1"]})
    )
    scenario = parse_scenario(_scenario("interleaved", 4, "primary_replica", 1))

    plan = build_cluster_plan(inventory, scenario)

    primaries = [node for node in plan["nodes"] if node["role"] == "primary"]
    assert [(node["virtual_az_id"], node["host_id"]) for node in primaries] == [
        ("vaz-a", "h1"),
        ("vaz-b", "h1"),
    ]


def _inventory(mode: str, az_hosts: dict[str, list[str]]) -> dict:
    hosts = sorted({host_id for host_ids in az_hosts.values() for host_id in host_ids})
    return {
        "name": "test-inventory",
        "topology_mode": mode,
        "virtual_azs": [
            {
                "id": az_id,
                "host_ids": host_ids,
                "node_port_start": 7000 + index * 100,
                "node_port_end": 7099 + index * 100,
                "bus_port_offset": 10000,
            }
            for index, (az_id, host_ids) in enumerate(az_hosts.items())
        ],
        "hosts": [
            {
                "id": host_id,
                "address": "127.0.0.1",
                "access": {"method": "localhost"},
                "platform": {"os": "macos"},
                "hardware": {
                    "cpu_model": "example",
                    "cpu_cores": 8,
                    "memory_bytes": 17179869184,
                },
                "network": {"primary_interface": "lo0"},
                "storage": {"data_dir": "/tmp"},
            }
            for host_id in hosts
        ],
    }


def _scenario(mode: str, node_count: int, topology: str, replicas: int) -> dict:
    return {
        "name": "test-scenario",
        "run_id": "test-run",
        "topology_mode": mode,
        "topology": topology,
        "node_count": node_count,
        "replicas_per_primary": replicas,
        "validation": {"duration_seconds": 1},
        "traffic": {"profile": "none"},
        "virtual_az_placement": {"mode": mode},
    }
