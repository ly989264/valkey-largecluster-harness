from __future__ import annotations

from typing import Any


def primaries(plan: dict[str, Any]) -> list[dict[str, Any]]:
    return [node for node in plan.get("nodes", []) if node.get("role") == "primary"]


def replicas(plan: dict[str, Any]) -> list[dict[str, Any]]:
    return [node for node in plan.get("nodes", []) if node.get("role") == "replica"]


def endpoint(node: dict[str, Any]) -> tuple[str, int]:
    return str(node.get("host_id", "127.0.0.1")), int(node["client_port"])
