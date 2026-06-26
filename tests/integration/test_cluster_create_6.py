from __future__ import annotations

from pathlib import Path

from harness.cluster.check import check_cluster
from harness.cluster.create import create_cluster
from harness.inventory import load_inventory
from harness.planner import build_cluster_plan
from harness.scenario import load_scenario


class FakeClusterClient:
    def __init__(self) -> None:
        self.commands: list[tuple[str, int, tuple[str, ...]]] = []

    def command(self, host: str, port: int, *args: str) -> str:
        self.commands.append((host, port, args))
        if args == ("CLUSTER", "INFO"):
            return (
                "cluster_state:ok\n"
                "cluster_slots_assigned:16384\n"
                "cluster_slots_ok:16384\n"
                "cluster_known_nodes:6\n"
            )
        if args == ("CLUSTER", "SLOTS"):
            return "0 16383 127.0.0.1 7000 node-0001\n"
        return "OK\n"


def test_cluster_create_uses_explicit_cluster_commands(tmp_path: Path) -> None:
    plan = _fixture_plan()
    events = tmp_path / "events.jsonl"
    client = FakeClusterClient()

    result = create_cluster(plan, client, events, convergence_timeout_seconds=0.5)

    assert result.ok is True
    flattened = [command for _, _, command in client.commands]
    assert ("CLUSTER", "MEET", "mac-local", "7001") in flattened
    assert ("CLUSTER", "ADDSLOTSRANGE", "0", "5461") in flattened
    assert any(command[:2] == ("CLUSTER", "REPLICATE") for command in flattened)
    assert "cluster_meet" in events.read_text(encoding="utf-8")


def test_cluster_check_verifies_required_cluster_info(tmp_path: Path) -> None:
    plan = _fixture_plan()
    events = tmp_path / "events.jsonl"

    result = check_cluster(plan, FakeClusterClient(), events)

    assert result.ok is True
    assert result.checks["cluster_state"] == "ok"
    assert result.checks["cluster_slots_assigned"] == 16384


def _fixture_plan() -> dict:
    return build_cluster_plan(
        load_inventory("inventories/single-mac.dev.yaml"),
        load_scenario("scenarios/smoke-6.yaml"),
    )
