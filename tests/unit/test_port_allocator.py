from __future__ import annotations

import pytest

from harness.port_allocator import PortAllocator


def test_port_allocator_is_deterministic_and_disjoint() -> None:
    allocator = PortAllocator(
        [
            {
                "id": "vaz-a",
                "node_port_start": 7000,
                "node_port_end": 7002,
                "bus_port_offset": 10000,
            }
        ]
    )

    first = allocator.allocate("vaz-a")
    second = allocator.allocate("vaz-a")

    assert first == {"client_port": 7000, "bus_port": 17000}
    assert second == {"client_port": 7001, "bus_port": 17001}
    assert first["client_port"] != first["bus_port"]


def test_port_allocator_errors_when_range_is_exhausted() -> None:
    allocator = PortAllocator(
        [
            {
                "id": "vaz-a",
                "node_port_start": 7000,
                "node_port_end": 7000,
                "bus_port_offset": 10000,
            }
        ]
    )

    allocator.allocate("vaz-a")
    with pytest.raises(ValueError, match="no available client ports"):
        allocator.allocate("vaz-a")
