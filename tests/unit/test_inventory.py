from __future__ import annotations

import pytest

from harness.inventory import ValidationError, load_inventory, parse_inventory


def test_load_sample_inventory() -> None:
    inventory = load_inventory("inventories/single-mac.dev.yaml")

    assert inventory.name == "single-mac-dev"
    assert inventory.topology_mode == "single_az"
    assert inventory.hosts[0].hardware["memory_bytes"] > 0


def test_inventory_rejects_unknown_fields() -> None:
    with pytest.raises(ValidationError) as exc:
        parse_inventory(
            {
                "name": "bad",
                "topology_mode": "single_az",
                "virtual_azs": [],
                "hosts": [],
                "surprise": True,
            }
        )

    assert "inventory.surprise is not a supported field" in str(exc.value)


def test_inventory_requires_hardware_from_inventory() -> None:
    with pytest.raises(ValidationError) as exc:
        parse_inventory(
            {
                "name": "bad",
                "topology_mode": "single_az",
                "virtual_azs": [
                    {
                        "id": "vaz-a",
                        "host_ids": ["h1"],
                        "node_port_start": 7000,
                        "node_port_end": 7009,
                        "bus_port_offset": 10000,
                    }
                ],
                "hosts": [
                    {
                        "id": "h1",
                        "address": "127.0.0.1",
                        "access": {"method": "localhost"},
                        "platform": {"os": "macos"},
                        "hardware": {"cpu_model": "example"},
                        "network": {"primary_interface": "lo0"},
                        "storage": {"data_dir": "/tmp"},
                    }
                ],
            }
        )

    assert "hardware.cpu_cores is required" in str(exc.value)
    assert "hardware.memory_bytes is required" in str(exc.value)
