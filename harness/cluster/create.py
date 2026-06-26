from __future__ import annotations

import time
from dataclasses import dataclass
from pathlib import Path
from typing import Protocol

from harness.cluster.nodes import endpoint, primaries, replicas
from harness.cluster.slots import slot_ranges_for_node
from harness.events import append_event


class ClusterClient(Protocol):
    def command(self, host: str, port: int, *args: str) -> str:
        ...


@dataclass
class ClusterCreateResult:
    ok: bool
    phases: list[str]


def create_cluster(
    plan: dict,
    client: ClusterClient,
    events_path: str | Path,
    convergence_timeout_seconds: float = 30.0,
) -> ClusterCreateResult:
    run_id = str(plan["run_id"])
    phases: list[str] = []
    primary_nodes = primaries(plan)
    if not primary_nodes:
        append_event(events_path, run_id, "cluster_create_failed", phase="validate_plan")
        return ClusterCreateResult(False, phases)

    seed_host, seed_port = endpoint(primary_nodes[0])
    for node in plan.get("nodes", [])[1:]:
        host, port = endpoint(node)
        client.command(seed_host, seed_port, "CLUSTER", "MEET", host, str(port))
        phases.append("meet")
        append_event(events_path, run_id, "cluster_meet", node_id=node["id"], host=host, port=port)

    for node in primary_nodes:
        host, port = endpoint(node)
        for start, end in slot_ranges_for_node(node):
            client.command(host, port, "CLUSTER", "ADDSLOTSRANGE", str(start), str(end))
            phases.append("addslotsrange")
            append_event(
                events_path,
                run_id,
                "cluster_addslotsrange",
                node_id=node["id"],
                start=start,
                end=end,
            )

    for node in replicas(plan):
        host, port = endpoint(node)
        client.command(host, port, "CLUSTER", "REPLICATE", str(node["primary_id"]))
        phases.append("replicate")
        append_event(
            events_path,
            run_id,
            "cluster_replicate",
            node_id=node["id"],
            primary_id=node["primary_id"],
        )

    ok = wait_for_known_nodes(plan, client, convergence_timeout_seconds)
    append_event(events_path, run_id, "cluster_known_nodes_converged", ok=ok)
    return ClusterCreateResult(ok, phases)


def wait_for_known_nodes(plan: dict, client: ClusterClient, timeout_seconds: float) -> bool:
    expected = len(plan.get("nodes", []))
    deadline = time.monotonic() + timeout_seconds
    samples = primaries(plan)[: min(3, len(primaries(plan)))] or plan.get("nodes", [])[:1]
    while time.monotonic() < deadline:
        observed = []
        for node in samples:
            host, port = endpoint(node)
            output = client.command(host, port, "CLUSTER", "INFO")
            observed.append(_known_nodes(output))
        if observed and all(value >= expected for value in observed):
            return True
        time.sleep(0.1)
    return False


def _known_nodes(cluster_info: str) -> int:
    for line in cluster_info.splitlines():
        if line.startswith("cluster_known_nodes:"):
            return int(line.split(":", 1)[1])
    return 0
