"""Build auditable harness reports from scenario and artifact files."""

import json
from pathlib import Path

from harness.config import load_document
from harness.report_models import HarnessReport, ReportItem, ReportSection, REPORT_STATUSES


REQUIRED_REPORT_SECTIONS = (
    "summary",
    "environment",
    "virtual AZ topology",
    "ClusterPlan",
    "test matrix",
    "cluster create",
    "fault/failover timeline",
    "migration/CLUSTERSCAN",
    "resource metrics",
    "stability gates",
    "verified/unverified",
    "failures/skips/inconclusive",
    "reproduce commands",
    "raw artifacts index",
)


def load_scale_ladder(scenarios_dir="scenarios"):
    scenarios = []
    for path in sorted(Path(scenarios_dir).glob("scale-*.yaml")):
        data = load_document(path)
        scenarios.append(
            {
                "path": path.as_posix(),
                "scenario_id": data["scenario_id"],
                "total_nodes": int(data["cluster"]["total_nodes"]),
                "backend": data.get("backend", "fake"),
                "validation_profile": data.get("validation_profile", "unspecified"),
                "does_not_validate": list(data.get("does_not_validate", [])),
            }
        )
    return scenarios


def build_report(artifacts_root="artifacts", scenarios_dir="scenarios", report_id="valkey-largecluster-report"):
    artifacts_root = Path(artifacts_root)
    raw_index = _artifact_index(artifacts_root)
    phase_results = _phase_results(artifacts_root)
    scale_ladder = load_scale_ladder(scenarios_dir)
    items_by_section = {
        "summary": _summary_items(phase_results),
        "environment": (
            ReportItem("real Valkey runtime", "NOT_VALIDATED", "current artifacts are unit/fake/command-contract focused"),
            ReportItem("unsupported resources", "SKIPPED_RESOURCE", "Docker, SSH, and Darwin network limitations remain explicit in phase artifacts"),
        ),
        "virtual AZ topology": (ReportItem("virtual AZ planner", _phase_status(phase_results, "P03"), "P03 result.json"),),
        "ClusterPlan": (ReportItem("cluster plan", _phase_status(phase_results, "P04"), "P04 result.json"),),
        "test matrix": tuple(
            ReportItem(item["scenario_id"], "NOT_VALIDATED" if item["backend"] == "fake" else "INCONCLUSIVE", item["path"])
            for item in scale_ladder
        ),
        "cluster create": (ReportItem("cluster create path", _phase_status(phase_results, "P09"), "P09 result.json"),),
        "fault/failover timeline": (ReportItem("failover metrics", _phase_status(phase_results, "P12"), "P12 result.json"),),
        "migration/CLUSTERSCAN": (ReportItem("migration and CLUSTERSCAN", "MISSING", "not implemented in canonical phases"),),
        "resource metrics": (ReportItem("production resource metrics", "NOT_VALIDATED", "no production runtime metrics collected"),),
        "stability gates": (ReportItem("phase gates", "PASS" if _all_prior_passed(phase_results) else "FAIL", "P00-P15 artifacts"),),
        "verified/unverified": _verified_unverified_items(phase_results, scale_ladder),
        "failures/skips/inconclusive": _non_pass_items(phase_results),
        "reproduce commands": _reproduce_items(phase_results),
        "raw artifacts index": tuple(ReportItem(path, "PASS", path) for path in raw_index[:50]),
    }
    sections = tuple(ReportSection(name, tuple(items_by_section[name])) for name in REQUIRED_REPORT_SECTIONS)
    return HarnessReport(report_id=report_id, sections=sections, raw_artifacts_index=tuple(raw_index))


def write_report(path, **kwargs):
    report = build_report(**kwargs)
    Path(path).write_text(json.dumps(report.to_dict(), ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return report


def _artifact_index(root):
    if not root.exists():
        return []
    return sorted(path.as_posix() for path in root.rglob("*") if path.is_file())


def _phase_results(root):
    results = {}
    for path in sorted(root.glob("phase-P*/result.json")):
        try:
            results[path.parent.name.removeprefix("phase-")] = json.loads(path.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            results[path.parent.name.removeprefix("phase-")] = {"status": "FAIL", "summary": "invalid result.json"}
    return results


def _phase_status(results, phase):
    return results.get(phase, {}).get("status", "MISSING")


def _all_prior_passed(results):
    return all(results.get(f"P{idx:02d}", {}).get("status") == "PASS" for idx in range(16))


def _summary_items(results):
    return (
        ReportItem("completed phases P00-P15", "PASS" if _all_prior_passed(results) else "FAIL", "phase result.json files"),
        ReportItem("report status vocabulary", "PASS", ", ".join(REPORT_STATUSES)),
    )


def _verified_unverified_items(results, scale_ladder):
    items = []
    for phase, result in sorted(results.items()):
        items.append(ReportItem(f"{phase} verified outputs", result.get("status", "MISSING"), result.get("summary", "")))
    for scale in scale_ladder:
        evidence = scale["path"]
        if scale["scenario_id"] == "scale-2000-empty":
            evidence += " does not validate throughput, production_latency, production_rto, or physical_3az_durability"
        items.append(ReportItem(scale["scenario_id"], "NOT_VALIDATED", evidence))
    return tuple(items)


def _non_pass_items(results):
    items = []
    for phase, result in sorted(results.items()):
        if result.get("status") != "PASS":
            items.append(ReportItem(phase, result.get("status", "MISSING"), result.get("summary", "")))
    items.extend(
        [
            ReportItem("missing migration/CLUSTERSCAN", "MISSING", "not implemented"),
            ReportItem("real runtime metrics", "NOT_VALIDATED", "not collected"),
            ReportItem("resource-dependent backends", "SKIPPED_RESOURCE", "see phase artifacts for capability limits"),
            ReportItem("production conclusion", "INCONCLUSIVE", "no production workload evidence"),
            ReportItem("failure preservation sentinel", "FAIL", "report keeps failing evidence as FAIL"),
        ]
    )
    return tuple(items)


def _reproduce_items(results):
    items = []
    for phase, result in sorted(results.items()):
        for command in result.get("commands", []):
            items.append(ReportItem(f"{phase}: {command['command']}", "PASS" if command.get("exit_code") == 0 else "FAIL", "recorded pre-gate command"))
    return tuple(items)
