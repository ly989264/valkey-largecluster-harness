from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from harness.inventory import Inventory
from harness.placement import PlacementEngine
from harness.port_allocator import PortAllocator
from harness.scenario import Scenario


TOTAL_SLOTS = 16384


def build_cluster_plan(inventory: Inventory, scenario: Scenario) -> dict[str, Any]:
    primaries = scenario.node_count // (1 + scenario.replicas_per_primary)
    placement = PlacementEngine(inventory)
    ports = PortAllocator(inventory.virtual_azs)
    nodes: list[dict[str, Any]] = []
    degraded_reasons: list[str] = []

    slot_ranges = _slot_ranges(primaries)
    primary_nodes: list[dict[str, Any]] = []
    for index in range(primaries):
        placed = placement.primary_placement(index)
        allocated = ports.allocate(placed.virtual_az_id)
        node = {
            "id": _node_id(len(nodes)),
            "role": "primary",
            "primary_id": None,
            "host_id": placed.host_id,
            "virtual_az_id": placed.virtual_az_id,
            "client_port": allocated["client_port"],
            "bus_port": allocated["bus_port"],
            "slots": [slot_ranges[index]],
        }
        nodes.append(node)
        primary_nodes.append(node)

    if scenario.topology == "primary_replica":
        for primary_index, primary in enumerate(primary_nodes):
            for replica_index in range(scenario.replicas_per_primary):
                placed, degraded = placement.replica_placement(
                    primary=_placement_from_node(primary),
                    index=primary_index + replica_index + 1,
                )
                if degraded:
                    degraded_reasons.append(f"{primary['id']}: {degraded}")
                allocated = ports.allocate(placed.virtual_az_id)
                nodes.append(
                    {
                        "id": _node_id(len(nodes)),
                        "role": "replica",
                        "primary_id": primary["id"],
                        "host_id": placed.host_id,
                        "virtual_az_id": placed.virtual_az_id,
                        "client_port": allocated["client_port"],
                        "bus_port": allocated["bus_port"],
                        "slots": [],
                    }
                )

    return {
        "schema_version": 1,
        "run_id": scenario.run_id,
        "inventory": {
            "name": inventory.name,
            "path": str(inventory.path),
            "topology_mode": inventory.topology_mode,
        },
        "scenario": {
            "name": scenario.name,
            "path": str(scenario.path),
            "topology": scenario.topology,
            "node_count": scenario.node_count,
            "replicas_per_primary": scenario.replicas_per_primary,
        },
        "slot_count": TOTAL_SLOTS,
        "placement_degraded": bool(degraded_reasons),
        "placement_degraded_reasons": degraded_reasons,
        "virtual_azs": inventory.virtual_azs,
        "nodes": nodes,
    }


def write_cluster_plan(plan: dict[str, Any], out_dir: str | Path) -> Path:
    path = Path(out_dir) / "cluster_plan.json"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(plan, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return path


def _slot_ranges(primary_count: int) -> list[dict[str, int]]:
    base = TOTAL_SLOTS // primary_count
    remainder = TOTAL_SLOTS % primary_count
    ranges: list[dict[str, int]] = []
    start = 0
    for index in range(primary_count):
        size = base + (1 if index < remainder else 0)
        end = start + size - 1
        ranges.append({"start": start, "end": end})
        start = end + 1
    return ranges


def _node_id(index: int) -> str:
    return f"node-{index + 1:04d}"


def _placement_from_node(node: dict[str, Any]):
    from harness.placement import Placement

    return Placement(virtual_az_id=node["virtual_az_id"], host_id=node["host_id"])
