from __future__ import annotations

import json
from pathlib import Path
from typing import Any


def load_plan(path: str | Path) -> dict[str, Any]:
    return json.loads(Path(path).read_text(encoding="utf-8"))


def generate_configs(plan_path: str | Path, run_dir: str | Path) -> list[Path]:
    plan = load_plan(plan_path)
    base = Path(run_dir)
    conf_dir = base / "conf"
    data_dir = base / "data"
    conf_dir.mkdir(parents=True, exist_ok=True)
    data_dir.mkdir(parents=True, exist_ok=True)
    written: list[Path] = []
    for node in plan.get("nodes", []):
        node_dir = data_dir / node["id"]
        node_dir.mkdir(parents=True, exist_ok=True)
        conf_path = conf_dir / f"{node['id']}.conf"
        conf_path.write_text(_render_config(node, node_dir), encoding="utf-8")
        written.append(conf_path)
    return written


def _render_config(node: dict[str, Any], node_dir: Path) -> str:
    return "\n".join(
        [
            f"port {node['client_port']}",
            "cluster-enabled yes",
            f"cluster-config-file nodes-{node['id']}.conf",
            f"cluster-announce-port {node['client_port']}",
            f"cluster-announce-bus-port {node['bus_port']}",
            f"dir {node_dir}",
            "appendonly no",
            "protected-mode no",
            "",
        ]
    )
