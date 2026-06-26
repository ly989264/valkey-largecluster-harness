from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

from harness.simple_yaml import SimpleYamlError, load_yaml


TOPOLOGY_MODES = {"single_az", "physical_aligned", "interleaved"}


class ValidationError(ValueError):
    def __init__(self, errors: list[str]) -> None:
        super().__init__("\n".join(errors))
        self.errors = errors


@dataclass(frozen=True)
class Host:
    id: str
    address: str
    access: dict[str, Any]
    platform: dict[str, Any]
    hardware: dict[str, Any]
    network: dict[str, Any]
    storage: dict[str, Any]


@dataclass(frozen=True)
class Inventory:
    path: Path
    name: str
    topology_mode: str
    virtual_azs: list[dict[str, Any]]
    hosts: list[Host]

    @property
    def host_ids(self) -> set[str]:
        return {host.id for host in self.hosts}


def load_inventory(path: str | Path) -> Inventory:
    source = Path(path)
    try:
        data = load_yaml(source)
    except SimpleYamlError as exc:
        raise ValidationError([f"{source}: {exc}"]) from exc
    return parse_inventory(data, source)


def parse_inventory(data: dict[str, Any], path: str | Path = "<memory>") -> Inventory:
    errors: list[str] = []
    path_obj = Path(path)
    _require_keys(data, {"name", "topology_mode", "virtual_azs", "hosts"}, errors, "inventory")
    _reject_unknown(
        data,
        {"name", "topology_mode", "virtual_azs", "hosts"},
        errors,
        "inventory",
    )

    name = data.get("name")
    if not isinstance(name, str) or not name:
        errors.append("inventory.name must be a non-empty string")

    topology_mode = data.get("topology_mode")
    if topology_mode not in TOPOLOGY_MODES:
        errors.append(
            "inventory.topology_mode must be one of: "
            + ", ".join(sorted(TOPOLOGY_MODES))
        )

    hosts = _parse_hosts(data.get("hosts"), errors)
    host_ids = {host.id for host in hosts}
    virtual_azs = _parse_virtual_azs(data.get("virtual_azs"), host_ids, errors)

    if errors:
        raise ValidationError(errors)
    return Inventory(
        path=path_obj,
        name=name,
        topology_mode=topology_mode,
        virtual_azs=virtual_azs,
        hosts=hosts,
    )


def _parse_hosts(value: Any, errors: list[str]) -> list[Host]:
    if not isinstance(value, list) or not value:
        errors.append("inventory.hosts must be a non-empty list")
        return []
    hosts: list[Host] = []
    seen: set[str] = set()
    for index, raw in enumerate(value):
        ctx = f"inventory.hosts[{index}]"
        if not isinstance(raw, dict):
            errors.append(f"{ctx} must be a mapping")
            continue
        allowed = {"id", "address", "access", "platform", "hardware", "network", "storage"}
        _require_keys(raw, allowed, errors, ctx)
        _reject_unknown(raw, allowed, errors, ctx)
        host_id = raw.get("id")
        if not isinstance(host_id, str) or not host_id:
            errors.append(f"{ctx}.id must be a non-empty string")
        elif host_id in seen:
            errors.append(f"{ctx}.id duplicates host id {host_id!r}")
        else:
            seen.add(host_id)
        for section in ("access", "platform", "hardware", "network", "storage"):
            if not isinstance(raw.get(section), dict) or not raw.get(section):
                errors.append(f"{ctx}.{section} must be a non-empty mapping")
        hardware = raw.get("hardware", {})
        if isinstance(hardware, dict):
            for required in ("cpu_model", "cpu_cores", "memory_bytes"):
                if required not in hardware:
                    errors.append(f"{ctx}.hardware.{required} is required")
        if isinstance(host_id, str):
            hosts.append(
                Host(
                    id=host_id,
                    address=str(raw.get("address", "")),
                    access=dict(raw.get("access", {})),
                    platform=dict(raw.get("platform", {})),
                    hardware=dict(raw.get("hardware", {})),
                    network=dict(raw.get("network", {})),
                    storage=dict(raw.get("storage", {})),
                )
            )
    return hosts


def _parse_virtual_azs(value: Any, host_ids: set[str], errors: list[str]) -> list[dict[str, Any]]:
    if not isinstance(value, list) or not value:
        errors.append("inventory.virtual_azs must be a non-empty list")
        return []
    result: list[dict[str, Any]] = []
    seen: set[str] = set()
    for index, raw in enumerate(value):
        ctx = f"inventory.virtual_azs[{index}]"
        if not isinstance(raw, dict):
            errors.append(f"{ctx} must be a mapping")
            continue
        allowed = {"id", "host_ids", "node_port_start", "node_port_end", "bus_port_offset"}
        _require_keys(raw, allowed, errors, ctx)
        _reject_unknown(raw, allowed, errors, ctx)
        az_id = raw.get("id")
        if not isinstance(az_id, str) or not az_id:
            errors.append(f"{ctx}.id must be a non-empty string")
        elif az_id in seen:
            errors.append(f"{ctx}.id duplicates virtual AZ id {az_id!r}")
        else:
            seen.add(az_id)
        az_hosts = raw.get("host_ids")
        if not isinstance(az_hosts, list) or not az_hosts:
            errors.append(f"{ctx}.host_ids must be a non-empty list")
        else:
            for host_id in az_hosts:
                if host_id not in host_ids:
                    errors.append(f"{ctx}.host_ids references unknown host {host_id!r}")
        start = raw.get("node_port_start")
        end = raw.get("node_port_end")
        if not isinstance(start, int) or not isinstance(end, int) or start >= end:
            errors.append(f"{ctx} must define an increasing node_port_start/node_port_end range")
        offset = raw.get("bus_port_offset")
        if not isinstance(offset, int) or offset <= 0:
            errors.append(f"{ctx}.bus_port_offset must be a positive integer")
        result.append(dict(raw))
    return result


def _require_keys(
    mapping: dict[str, Any], required: set[str], errors: list[str], context: str
) -> None:
    for key in sorted(required - mapping.keys()):
        errors.append(f"{context}.{key} is required")


def _reject_unknown(
    mapping: dict[str, Any], allowed: set[str], errors: list[str], context: str
) -> None:
    for key in sorted(mapping.keys() - allowed):
        errors.append(f"{context}.{key} is not a supported field")
