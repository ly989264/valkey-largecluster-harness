"""ClusterPlan model and construction from P03 topology."""

from dataclasses import dataclass

from harness.port_allocator import allocate_ports
from harness.slot_allocator import allocate_slots
from harness.topology import VirtualAZPlacement


class ClusterPlanError(ValueError):
    pass


@dataclass(frozen=True)
class SlotRange:
    start: int
    end: int

    def to_dict(self):
        return {"start": self.start, "end": self.end}


@dataclass(frozen=True)
class NodeSpec:
    node_id: str
    node_index: int
    role: str
    physical_host_id: str
    virtual_az_id: str
    client_port: int
    bus_port: int
    slot_range: SlotRange = None
    primary_node_id: str = None

    def to_dict(self):
        data = {
            "node_id": self.node_id,
            "node_index": self.node_index,
            "role": self.role,
            "physical_host_id": self.physical_host_id,
            "virtual_az_id": self.virtual_az_id,
            "client_port": self.client_port,
            "bus_port": self.bus_port,
        }
        if self.slot_range is not None:
            data["slot_range"] = self.slot_range.to_dict()
        if self.primary_node_id is not None:
            data["primary_node_id"] = self.primary_node_id
        return data


@dataclass(frozen=True)
class ReplicaPlacement:
    replica_node_id: str
    primary_node_id: str
    anti_affinity: str

    def to_dict(self):
        return {
            "replica_node_id": self.replica_node_id,
            "primary_node_id": self.primary_node_id,
            "anti_affinity": self.anti_affinity,
        }


@dataclass(frozen=True)
class ClusterPlan:
    inventory_id: str
    scenario_id: str
    nodes: tuple
    slot_ranges: tuple
    replica_placements: tuple
    warnings: tuple

    def to_dict(self):
        return {
            "inventory_id": self.inventory_id,
            "scenario_id": self.scenario_id,
            "nodes": [node.to_dict() for node in self.nodes],
            "slot_ranges": [slot.to_dict() for slot in self.slot_ranges],
            "replica_placements": [replica.to_dict() for replica in self.replica_placements],
            "warnings": list(self.warnings),
        }


def make_cluster_plan(inventory, scenario, topology_plan):
    group_size = scenario.cluster.replicas_per_primary + 1
    if scenario.cluster.total_nodes % group_size != 0:
        raise ClusterPlanError("total_nodes must be divisible by replicas_per_primary + 1")
    primary_count = scenario.cluster.total_nodes // group_size
    ports = allocate_ports(inventory.port_ranges, scenario.cluster.total_nodes)
    slot_dicts = allocate_slots(primary_count)
    slot_ranges = tuple(SlotRange(item["start"], item["end"]) for item in slot_dicts)
    placements = [
        VirtualAZPlacement(item["virtual_az_id"], item["physical_host_id"], int(item.get("weight", 1)))
        for item in topology_plan["placements"]
    ]
    expanded = _expanded(placements)
    warnings = list(topology_plan.get("warnings", []))
    nodes = []
    primaries = []
    port_index = 0
    for idx in range(primary_count):
        placement = expanded[idx % len(expanded)]
        node = NodeSpec(
            node_id=f"node-{idx:04d}",
            node_index=idx,
            role="primary",
            physical_host_id=placement.physical_host_id,
            virtual_az_id=placement.virtual_az_id,
            client_port=ports[port_index]["client_port"],
            bus_port=ports[port_index]["bus_port"],
            slot_range=slot_ranges[idx],
        )
        port_index += 1
        primaries.append(node)
        nodes.append(node)
    replicas = []
    for primary_idx, primary in enumerate(primaries):
        for replica_ordinal in range(scenario.cluster.replicas_per_primary):
            placement, anti_affinity = _replica_placement(expanded, primary, primary_idx + replica_ordinal + 1)
            if anti_affinity != "virtual_az":
                warnings.append(f"replica for {primary.node_id} could not avoid primary virtual AZ")
            node_index = len(nodes)
            replica = NodeSpec(
                node_id=f"node-{node_index:04d}",
                node_index=node_index,
                role="replica",
                physical_host_id=placement.physical_host_id,
                virtual_az_id=placement.virtual_az_id,
                client_port=ports[port_index]["client_port"],
                bus_port=ports[port_index]["bus_port"],
                primary_node_id=primary.node_id,
            )
            port_index += 1
            nodes.append(replica)
            replicas.append(ReplicaPlacement(replica.node_id, primary.node_id, anti_affinity))
    return ClusterPlan(
        inventory_id=inventory.inventory_id,
        scenario_id=scenario.scenario_id,
        nodes=tuple(nodes),
        slot_ranges=slot_ranges,
        replica_placements=tuple(replicas),
        warnings=tuple(warnings),
    )


def _expanded(placements):
    expanded = []
    for placement in sorted(placements, key=lambda p: p.sort_key()):
        expanded.extend([placement] * placement.weight)
    if not expanded:
        raise ClusterPlanError("topology plan has no placements")
    return expanded


def _replica_placement(expanded, primary, offset):
    candidates = [p for p in expanded if p.virtual_az_id != primary.virtual_az_id]
    if candidates:
        return candidates[offset % len(candidates)], "virtual_az"
    return expanded[offset % len(expanded)], "none"
