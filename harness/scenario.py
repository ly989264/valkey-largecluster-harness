from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

from harness.inventory import TOPOLOGY_MODES, ValidationError
from harness.simple_yaml import SimpleYamlError, load_yaml


TOPOLOGIES = {"primary_only", "primary_replica"}


@dataclass(frozen=True)
class Scenario:
    path: Path
    name: str
    run_id: str
    topology_mode: str
    topology: str
    node_count: int
    replicas_per_primary: int
    validation: dict[str, Any]
    traffic: dict[str, Any]
    virtual_az_placement: dict[str, Any]


def load_scenario(path: str | Path) -> Scenario:
    source = Path(path)
    try:
        data = load_yaml(source)
    except SimpleYamlError as exc:
        raise ValidationError([f"{source}: {exc}"]) from exc
    return parse_scenario(data, source)


def parse_scenario(data: dict[str, Any], path: str | Path = "<memory>") -> Scenario:
    errors: list[str] = []
    allowed = {
        "name",
        "run_id",
        "topology_mode",
        "topology",
        "node_count",
        "replicas_per_primary",
        "validation",
        "traffic",
        "virtual_az_placement",
        "timeouts",
        "tests",
    }
    required = allowed - {"timeouts", "tests"}
    _require_keys(data, required, errors, "scenario")
    _reject_unknown(data, allowed, errors, "scenario")

    name = data.get("name")
    if not isinstance(name, str) or not name:
        errors.append("scenario.name must be a non-empty string")
    run_id = data.get("run_id")
    if not isinstance(run_id, str) or not run_id:
        errors.append("scenario.run_id must be a non-empty string")
    topology_mode = data.get("topology_mode")
    if topology_mode not in TOPOLOGY_MODES:
        errors.append(
            "scenario.topology_mode must be one of: " + ", ".join(sorted(TOPOLOGY_MODES))
        )
    topology = data.get("topology")
    if topology not in TOPOLOGIES:
        errors.append("scenario.topology must be one of: " + ", ".join(sorted(TOPOLOGIES)))
    node_count = data.get("node_count")
    if not isinstance(node_count, int) or node_count <= 0:
        errors.append("scenario.node_count must be a positive integer")
    replicas_per_primary = data.get("replicas_per_primary")
    if not isinstance(replicas_per_primary, int) or replicas_per_primary < 0:
        errors.append("scenario.replicas_per_primary must be a non-negative integer")
    if topology == "primary_only" and replicas_per_primary != 0:
        errors.append("primary_only topology requires replicas_per_primary=0")
    if topology == "primary_replica" and replicas_per_primary != 1:
        errors.append("primary_replica topology currently requires replicas_per_primary=1")
    if isinstance(node_count, int) and isinstance(replicas_per_primary, int):
        group_size = 1 + replicas_per_primary
        if group_size <= 0 or node_count % group_size != 0:
            errors.append("scenario.node_count must divide evenly by primary plus replica count")

    for section in ("validation", "traffic", "virtual_az_placement"):
        if not isinstance(data.get(section), dict):
            errors.append(f"scenario.{section} must be a mapping")

    if errors:
        raise ValidationError(errors)

    return Scenario(
        path=Path(path),
        name=name,
        run_id=run_id,
        topology_mode=topology_mode,
        topology=topology,
        node_count=node_count,
        replicas_per_primary=replicas_per_primary,
        validation=dict(data["validation"]),
        traffic=dict(data["traffic"]),
        virtual_az_placement=dict(data["virtual_az_placement"]),
    )


def _require_keys(
    mapping: dict[str, Any], required: set[str], errors: list[str], context: str
) -> None:
    for key in sorted(required - mapping.keys()):
        errors.append(f"{context}.{key} is required")


def _reject_unknown(
    mapping: dict[str, Any], allowed: set[str], errors: list[str], context: str
) -> None:
    for key in sorted(mapping.keys() - allowed):
        errors.append(f"{context}.{key} is not a supported field")
