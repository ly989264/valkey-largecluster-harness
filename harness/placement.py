from __future__ import annotations

from dataclasses import dataclass

from harness.inventory import Inventory


@dataclass(frozen=True)
class Placement:
    virtual_az_id: str
    host_id: str


class PlacementEngine:
    def __init__(self, inventory: Inventory) -> None:
        self.inventory = inventory
        self._virtual_azs = inventory.virtual_azs

    def primary_placement(self, index: int) -> Placement:
        az = self._virtual_azs[index % len(self._virtual_azs)]
        hosts = az["host_ids"]
        if self.inventory.topology_mode == "interleaved":
            host_id = hosts[index % len(hosts)]
        else:
            host_id = hosts[0]
        return Placement(virtual_az_id=str(az["id"]), host_id=str(host_id))

    def replica_placement(self, primary: Placement, index: int) -> tuple[Placement, str | None]:
        candidates = self._all_candidates(index)
        for candidate in candidates:
            if candidate.virtual_az_id != primary.virtual_az_id:
                return candidate, None
        for candidate in candidates:
            if candidate.host_id != primary.host_id:
                return candidate, "replica anti-affinity degraded: virtual AZ diversity unavailable"
        if candidates:
            return (
                candidates[0],
                "replica anti-affinity degraded: virtual AZ and host diversity unavailable",
            )
        raise ValueError("inventory has no placement candidates")

    def _all_candidates(self, index: int) -> list[Placement]:
        result: list[Placement] = []
        for az_offset in range(len(self._virtual_azs)):
            az = self._virtual_azs[(index + az_offset) % len(self._virtual_azs)]
            hosts = az["host_ids"]
            for host_offset in range(len(hosts)):
                host_id = hosts[(index + host_offset) % len(hosts)]
                result.append(Placement(virtual_az_id=str(az["id"]), host_id=str(host_id)))
        return result
