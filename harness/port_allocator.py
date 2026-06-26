from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass
class PortAllocator:
    virtual_azs: list[dict[str, Any]]
    _next_by_az: dict[str, int] = field(init=False)
    _used_client_ports: set[tuple[str, int]] = field(default_factory=set, init=False)
    _used_bus_ports: set[tuple[str, int]] = field(default_factory=set, init=False)

    def __post_init__(self) -> None:
        self._next_by_az = {
            str(az["id"]): int(az["node_port_start"]) for az in self.virtual_azs
        }

    def allocate(self, virtual_az_id: str) -> dict[str, int]:
        az = self._az(virtual_az_id)
        next_port = self._next_by_az[virtual_az_id]
        end = int(az["node_port_end"])
        offset = int(az["bus_port_offset"])
        while next_port <= end:
            client_port = next_port
            bus_port = client_port + offset
            self._next_by_az[virtual_az_id] = next_port + 1
            client_key = (virtual_az_id, client_port)
            bus_key = (virtual_az_id, bus_port)
            if client_key in self._used_client_ports or bus_key in self._used_bus_ports:
                next_port += 1
                continue
            if bus_port == client_port or (virtual_az_id, bus_port) in self._used_client_ports:
                next_port += 1
                continue
            self._used_client_ports.add(client_key)
            self._used_bus_ports.add(bus_key)
            return {"client_port": client_port, "bus_port": bus_port}
        raise ValueError(f"virtual AZ {virtual_az_id} has no available client ports")

    def _az(self, virtual_az_id: str) -> dict[str, Any]:
        for az in self.virtual_azs:
            if az["id"] == virtual_az_id:
                return az
        raise ValueError(f"unknown virtual AZ {virtual_az_id}")
