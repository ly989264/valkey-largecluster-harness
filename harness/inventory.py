"""Inventory models for physical hosts and runtime port ranges."""

from dataclasses import dataclass


@dataclass(frozen=True)
class PortRange:
    client_start: int
    bus_start: int
    count: int

    def validate(self):
        if self.client_start <= 0 or self.bus_start <= 0 or self.count <= 0:
            raise ValueError("port_ranges client_start, bus_start, and count must be positive")
        client_end = self.client_start + self.count
        bus_end = self.bus_start + self.count
        if max(self.client_start, self.bus_start) < min(client_end, bus_end):
            raise ValueError("client and bus port ranges must not overlap")

    def to_dict(self):
        return {"client_start": self.client_start, "bus_start": self.bus_start, "count": self.count}


@dataclass(frozen=True)
class PhysicalHost:
    id: str
    address: str
    platform: str
    virtual_azs: tuple

    def validate(self):
        if not self.id:
            raise ValueError("physical_hosts[].id is required")
        if not self.address:
            raise ValueError("physical_hosts[].address is required")
        if self.platform not in {"darwin", "linux"}:
            raise ValueError("physical_hosts[].platform must be darwin or linux")
        if not self.virtual_azs:
            raise ValueError("physical_hosts[].virtual_azs must not be empty")

    def to_dict(self):
        return {"id": self.id, "address": self.address, "platform": self.platform, "virtual_azs": list(self.virtual_azs)}


@dataclass(frozen=True)
class Inventory:
    inventory_id: str
    physical_hosts: tuple
    port_ranges: PortRange
    runtime: str = "local"

    def validate(self):
        if not self.inventory_id:
            raise ValueError("inventory_id is required")
        if not self.physical_hosts:
            raise ValueError("physical_hosts is required")
        for host in self.physical_hosts:
            host.validate()
        self.port_ranges.validate()
        if self.runtime not in {"local", "ssh", "docker-hostnet"}:
            raise ValueError("runtime must be local, ssh, or docker-hostnet")

    def virtual_az_ids(self):
        ids = []
        for host in self.physical_hosts:
            for az in host.virtual_azs:
                if az not in ids:
                    ids.append(az)
        return tuple(ids)

    def to_dict(self):
        return {
            "inventory_id": self.inventory_id,
            "physical_hosts": [host.to_dict() for host in self.physical_hosts],
            "port_ranges": self.port_ranges.to_dict(),
            "runtime": self.runtime,
        }


def inventory_from_dict(data):
    hosts = tuple(
        PhysicalHost(
            id=str(item.get("id", "")),
            address=str(item.get("address", "")),
            platform=str(item.get("platform", "")),
            virtual_azs=tuple(item.get("virtual_azs", [])),
        )
        for item in data.get("physical_hosts", [])
    )
    ports = data.get("port_ranges", {})
    inv = Inventory(
        inventory_id=str(data.get("inventory_id", "")),
        physical_hosts=hosts,
        port_ranges=PortRange(
            client_start=int(ports.get("client_start", 0)),
            bus_start=int(ports.get("bus_start", 0)),
            count=int(ports.get("count", 0)),
        ),
        runtime=str(data.get("runtime", "local")),
    )
    inv.validate()
    return inv
