from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from harness.report.charts import ascii_topology


MISSING = "MISSING"


def generate_report(run_id: str, artifacts_dir: str | Path, reports_root: str | Path = "reports") -> Path:
    artifacts = Path(artifacts_dir)
    output_dir = Path(reports_root) / run_id
    output_dir.mkdir(parents=True, exist_ok=True)

    plan = _read_json(artifacts / "cluster_plan.json")
    summary = _read_json(artifacts / "report_summary.json") or {}
    events = _read_jsonl(artifacts / "events.jsonl")
    context = _build_context(run_id, artifacts, plan, summary, events)
    template = Path("harness/report/templates/report.md.j2").read_text(encoding="utf-8")
    report = template
    for key, value in context.items():
        report = report.replace("{{ " + key + " }}", str(value))
    path = output_dir / "report.md"
    path.write_text(report, encoding="utf-8")
    return path


def _build_context(
    run_id: str,
    artifacts: Path,
    plan: dict[str, Any] | None,
    summary: dict[str, Any],
    events: list[dict[str, Any]],
) -> dict[str, str]:
    validation = summary.get("validation", {}) if isinstance(summary, dict) else {}
    environment = summary.get("environment", {}) if isinstance(summary, dict) else {}
    tests = summary.get("test_matrix", []) if isinstance(summary, dict) else []
    resource_metrics = summary.get("resource_metrics", {}) if isinstance(summary, dict) else {}

    return {
        "run_id": run_id,
        "executive_summary": _value(summary.get("executive_summary")),
        "environment_parameters": _mapping(environment),
        "virtual_az_topology": ascii_topology(plan),
        "cluster_plan": _cluster_plan_summary(plan),
        "test_matrix": _list(tests),
        "cluster_formation": _value(summary.get("cluster_formation")),
        "failover": _value(summary.get("failover")),
        "migration": _value(summary.get("migration")),
        "resource_metrics": _mapping(resource_metrics),
        "validated": _list(validation.get("validated", [])),
        "not_validated": _list(validation.get("not_validated", [])),
        "inconclusive": _list(validation.get("inconclusive", [])),
        "reproduction_commands": _commands(run_id),
        "artifact_index": _artifact_index(artifacts, events),
    }


def _read_json(path: Path) -> dict[str, Any] | None:
    if not path.exists():
        return None
    return json.loads(path.read_text(encoding="utf-8"))


def _read_jsonl(path: Path) -> list[dict[str, Any]]:
    if not path.exists():
        return []
    events: list[dict[str, Any]] = []
    for line in path.read_text(encoding="utf-8").splitlines():
        if line.strip():
            events.append(json.loads(line))
    return events


def _value(value: Any) -> str:
    if value in (None, "", [], {}):
        return MISSING
    if isinstance(value, (dict, list)):
        return json.dumps(value, indent=2, sort_keys=True)
    return str(value)


def _mapping(value: Any) -> str:
    if not isinstance(value, dict) or not value:
        return MISSING
    lines = []
    for key in sorted(value):
        item = value[key]
        lines.append(f"- {key}: {_value(item)}")
    return "\n".join(lines)


def _list(value: Any) -> str:
    if not isinstance(value, list) or not value:
        return MISSING
    return "\n".join(f"- {_value(item)}" for item in value)


def _cluster_plan_summary(plan: dict[str, Any] | None) -> str:
    if not plan:
        return MISSING
    nodes = plan.get("nodes", [])
    primaries = [node for node in nodes if node.get("role") == "primary"]
    replicas = [node for node in nodes if node.get("role") == "replica"]
    degraded = plan.get("placement_degraded", MISSING)
    reasons = plan.get("placement_degraded_reasons", [])
    lines = [
        f"- Nodes: {len(nodes)}",
        f"- Primaries: {len(primaries)}",
        f"- Replicas: {len(replicas)}",
        f"- Slots: {plan.get('slot_count', MISSING)}",
        f"- Placement degraded: {degraded}",
    ]
    if reasons:
        lines.append("- Placement degraded reasons:")
        lines.extend(f"  - {reason}" for reason in reasons)
    return "\n".join(lines)


def _commands(run_id: str) -> str:
    return "\n".join(
        [
            "```sh",
            f"make report RUN_ID={run_id}",
            "```",
        ]
    )


def _artifact_index(artifacts: Path, events: list[dict[str, Any]]) -> str:
    files = sorted(path.name for path in artifacts.iterdir()) if artifacts.exists() else []
    lines = [f"- {name}" for name in files]
    lines.append(f"- JSONL events loaded: {len(events)}")
    return "\n".join(lines) if lines else MISSING
