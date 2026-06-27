"""P03 deterministic topology planner."""

from harness.config import ConfigError, load_document, load_inventory, load_scenario
from harness.cluster_plan import make_cluster_plan
from harness.topology import VirtualAZPlacement, build_matrix


class PlanError(ValueError):
    pass


def build_topology_plan(inventory_path, scenario_path):
    inventory = load_inventory(inventory_path)
    scenario = load_scenario(scenario_path)
    raw_scenario = load_document(scenario_path)
    placements, matrix_full, warnings = _placements(inventory, scenario, raw_scenario)
    expanded = _expanded_placements(placements)
    node_count = scenario.cluster.total_nodes
    node_drafts = []
    for node_index in range(node_count):
        placement = expanded[node_index % len(expanded)]
        node_drafts.append(
            {
                "node_index": node_index,
                "physical_host_id": placement.physical_host_id,
                "virtual_az_id": placement.virtual_az_id,
            }
        )
    node_drafts.sort(key=lambda item: (item["physical_host_id"], item["virtual_az_id"], item["node_index"]))
    host_ids = [host.id for host in inventory.physical_hosts]
    az_ids = sorted({p.virtual_az_id for p in placements})
    return {
        "inventory_id": inventory.inventory_id,
        "scenario_id": scenario.scenario_id,
        "topology_mode": scenario.topology_mode,
        "virtual_azs": az_ids,
        "placements": [p.to_dict() for p in sorted(placements, key=lambda p: p.sort_key())],
        "virtual_az_host_matrix": build_matrix(placements, host_ids, az_ids, full=matrix_full),
        "node_drafts": node_drafts,
        "warnings": warnings,
    }


def build_cluster_plan(inventory_path, scenario_path):
    inventory = load_inventory(inventory_path)
    scenario = load_scenario(scenario_path)
    topology_plan = build_topology_plan(inventory_path, scenario_path)
    cluster_plan = make_cluster_plan(inventory, scenario, topology_plan)
    merged = dict(topology_plan)
    merged["cluster_plan"] = cluster_plan.to_dict()
    merged["nodes"] = merged["cluster_plan"]["nodes"]
    merged["slot_ranges"] = merged["cluster_plan"]["slot_ranges"]
    merged["replica_placements"] = merged["cluster_plan"]["replica_placements"]
    merged["warnings"] = sorted(set(merged.get("warnings", []) + merged["cluster_plan"].get("warnings", [])))
    return merged


def _placements(inventory, scenario, raw_scenario):
    mode = scenario.topology_mode
    if mode == "single_az":
        az_id = inventory.virtual_az_ids()[0]
        host_id = sorted(host.id for host in inventory.physical_hosts)[0]
        return [VirtualAZPlacement(az_id, host_id, 1)], False, [
            "single_az places all nodes in one virtual AZ; no AZ isolation is claimed"
        ]
    if mode == "physical_aligned":
        placements = []
        for host in inventory.physical_hosts:
            for az_id in host.virtual_azs:
                placements.append(VirtualAZPlacement(az_id, host.id, 1))
        warnings = []
        if len(inventory.physical_hosts) < scenario.cluster.virtual_az_count:
            warnings.append("physical_aligned has fewer physical hosts than requested virtual AZs; physical isolation is weak")
        if len({p.physical_host_id for p in placements}) < len({p.virtual_az_id for p in placements}):
            warnings.append("multiple virtual AZs share at least one physical host")
        return _validated(placements), False, warnings
    if mode == "uniform_interleaved":
        az_ids = sorted(inventory.virtual_az_ids())[: scenario.cluster.virtual_az_count]
        placements = [VirtualAZPlacement(az_id, host.id, 1) for host in inventory.physical_hosts for az_id in az_ids]
        return _validated(placements), True, ["uniform_interleaved intentionally spreads each virtual AZ across every physical host"]
    if mode == "custom":
        custom = raw_scenario.get("custom_placement", [])
        placements = [
            VirtualAZPlacement(str(item.get("virtual_az_id", "")), str(item.get("physical_host_id", "")), int(item.get("weight", 1)))
            for item in custom
        ]
        if not placements:
            raise PlanError("custom topology requires custom_placement")
        return _validated(placements), False, []
    raise ConfigError(f"unsupported topology mode {mode}")


def _validated(placements):
    if not placements:
        raise PlanError("at least one virtual AZ placement is required")
    for placement in placements:
        placement.validate()
    return placements


def _expanded_placements(placements):
    expanded = []
    for placement in sorted(placements, key=lambda p: p.sort_key()):
        expanded.extend([placement] * placement.weight)
    return expanded
