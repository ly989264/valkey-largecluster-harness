"""Client and cluster-bus port allocation."""


class PortAllocationError(ValueError):
    pass


def allocate_ports(port_range, count):
    port_range.validate()
    if count > port_range.count:
        raise PortAllocationError("insufficient port range capacity for requested nodes")
    ports = []
    for offset in range(count):
        ports.append({"client_port": port_range.client_start + offset, "bus_port": port_range.bus_start + offset})
    client_ports = {p["client_port"] for p in ports}
    bus_ports = {p["bus_port"] for p in ports}
    if len(client_ports) != count or len(bus_ports) != count or client_ports & bus_ports:
        raise PortAllocationError("allocated client and bus ports must be unique and non-overlapping")
    return ports
