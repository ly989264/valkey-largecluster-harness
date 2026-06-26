from __future__ import annotations

from collections import defaultdict
from typing import Any


def ascii_topology(plan: dict[str, Any] | None) -> str:
    if not plan:
        return "MISSING"
    nodes = plan.get("nodes")
    if not isinstance(nodes, list) or not nodes:
        return "MISSING"
    by_az: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for node in nodes:
        by_az[str(node.get("virtual_az_id", "MISSING"))].append(node)
    lines: list[str] = []
    for az_id in sorted(by_az):
        lines.append(f"+ virtual AZ {az_id}")
        for node in sorted(by_az[az_id], key=lambda item: str(item.get("id"))):
            role = node.get("role", "MISSING")
            host = node.get("host_id", "MISSING")
            port = node.get("client_port", "MISSING")
            primary = node.get("primary_id") or "-"
            lines.append(f"  - {node.get('id', 'MISSING')} {role} host={host} port={port} primary={primary}")
    return "\n".join(lines)
