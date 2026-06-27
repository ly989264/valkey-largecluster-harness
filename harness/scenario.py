"""Scenario model for cluster scale and topology config."""

from dataclasses import dataclass


TOPOLOGY_MODES = {"single_az", "physical_aligned", "uniform_interleaved", "custom"}


@dataclass(frozen=True)
class ClusterSettings:
    total_nodes: int
    replicas_per_primary: int = 1
    virtual_az_count: int = 1
    node_timeout_ms: int = 15000

    def validate(self):
        if self.total_nodes <= 0:
            raise ValueError("cluster.total_nodes must be > 0")
        if self.replicas_per_primary < 0:
            raise ValueError("cluster.replicas_per_primary must be >= 0")
        group_size = self.replicas_per_primary + 1
        if self.total_nodes % group_size != 0:
            raise ValueError("cluster.total_nodes must be divisible by replicas_per_primary + 1")
        if self.virtual_az_count <= 0:
            raise ValueError("cluster.virtual_az_count must be > 0")
        if self.node_timeout_ms <= 0:
            raise ValueError("cluster.node_timeout_ms must be > 0")

    def to_dict(self):
        return {
            "total_nodes": self.total_nodes,
            "replicas_per_primary": self.replicas_per_primary,
            "virtual_az_count": self.virtual_az_count,
            "node_timeout_ms": self.node_timeout_ms,
        }


@dataclass(frozen=True)
class Scenario:
    scenario_id: str
    topology_mode: str
    cluster: ClusterSettings
    backend: str = "fake"

    def validate(self):
        if not self.scenario_id:
            raise ValueError("scenario_id is required")
        if self.topology_mode not in TOPOLOGY_MODES:
            raise ValueError("topology_mode must be one of custom, physical_aligned, single_az, uniform_interleaved")
        if self.backend not in {"fake", "local", "docker-hostnet", "ssh"}:
            raise ValueError("backend must be fake, local, docker-hostnet, or ssh")
        self.cluster.validate()

    def to_dict(self):
        return {
            "scenario_id": self.scenario_id,
            "topology_mode": self.topology_mode,
            "cluster": self.cluster.to_dict(),
            "backend": self.backend,
        }


def scenario_from_dict(data):
    cluster = data.get("cluster", {})
    scen = Scenario(
        scenario_id=str(data.get("scenario_id", "")),
        topology_mode=str(data.get("topology_mode", "")),
        cluster=ClusterSettings(
            total_nodes=int(cluster.get("total_nodes", 0)),
            replicas_per_primary=int(cluster.get("replicas_per_primary", 1)),
            virtual_az_count=int(cluster.get("virtual_az_count", 1)),
            node_timeout_ms=int(cluster.get("node_timeout_ms", 15000)),
        ),
        backend=str(data.get("backend", "fake")),
    )
    scen.validate()
    return scen
