from __future__ import annotations

from typing import Any


def slot_ranges_for_node(node: dict[str, Any]) -> list[tuple[int, int]]:
    return [(int(item["start"]), int(item["end"])) for item in node.get("slots", [])]


def assigned_slot_count(plan: dict[str, Any]) -> int:
    total = 0
    for node in plan.get("nodes", []):
        for start, end in slot_ranges_for_node(node):
            total += end - start + 1
    return total
