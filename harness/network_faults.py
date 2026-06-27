"""Network fault backend contracts and command planning."""

from dataclasses import dataclass


@dataclass(frozen=True)
class NetworkFaultResult:
    status: str
    reason: str = ""
    evidence: str = ""
    commands: tuple = ()

    def to_dict(self):
        return {
            "status": self.status,
            "reason": self.reason,
            "evidence": self.evidence,
            "commands": [list(command) for command in self.commands],
        }


@dataclass(frozen=True)
class NetworkFaultTarget:
    node_id: str
    client_port: int
    bus_port: int
    virtual_az_id: str
    physical_host_id: str

    @classmethod
    def from_node(cls, node):
        return cls(
            node_id=node["node_id"],
            client_port=int(node["client_port"]),
            bus_port=int(node["bus_port"]),
            virtual_az_id=node["virtual_az_id"],
            physical_host_id=node["physical_host_id"],
        )

    def all_ports(self):
        return (self.client_port, self.bus_port)


class NetworkFaultBackend:
    name = "network"

    def capability(self):
        return NetworkFaultResult(status="OK", evidence=self.name)

    def isolate(self, targets):
        raise NotImplementedError

    def heal(self, targets):
        raise NotImplementedError

    def delay(self, targets, milliseconds):
        raise NotImplementedError

    def loss(self, targets, percent):
        raise NotImplementedError

    def clear(self, targets):
        raise NotImplementedError


class UnsupportedNetworkFaultBackend(NetworkFaultBackend):
    name = "unsupported"

    def __init__(self, reason, evidence=""):
        self.reason = reason
        self.evidence = evidence

    def capability(self):
        return NetworkFaultResult(status="SKIPPED_RESOURCE", reason=self.reason, evidence=self.evidence)

    def isolate(self, targets):
        return self.capability()

    def heal(self, targets):
        return self.capability()

    def delay(self, targets, milliseconds):
        return self.capability()

    def loss(self, targets, percent):
        return self.capability()

    def clear(self, targets):
        return self.capability()


def targets_for_virtual_az(cluster_plan, virtual_az_id):
    return tuple(
        NetworkFaultTarget.from_node(node)
        for node in cluster_plan["nodes"]
        if node.get("virtual_az_id") == virtual_az_id
    )
