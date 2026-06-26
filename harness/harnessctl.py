from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from harness.cluster.check import check_cluster
from harness.cluster.create import create_cluster
from harness.events import append_event
from harness.inventory import ValidationError, load_inventory
from harness.planner import build_cluster_plan, write_cluster_plan
from harness.report.generator import generate_report
from harness.scenario import load_scenario
from nodehost.valkey_cli import ValkeyCli


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="harnessctl")
    subparsers = parser.add_subparsers(dest="command", required=True)

    validate = subparsers.add_parser("validate", help="validate inventory and scenario")
    validate.add_argument("--inventory", required=True)
    validate.add_argument("--scenario", required=True)

    plan = subparsers.add_parser("plan", help="write deterministic cluster plan")
    plan.add_argument("--inventory", required=True)
    plan.add_argument("--scenario", required=True)
    plan.add_argument("--out-dir")

    report = subparsers.add_parser("report", help="generate report from run artifacts")
    report.add_argument("--run-id", required=True)
    report.add_argument("--artifacts-dir")
    report.add_argument("--reports-root", default="reports")

    create = subparsers.add_parser("create-cluster", help="create Valkey Cluster from a plan")
    create.add_argument("--plan", required=True)
    create.add_argument("--events", required=True)
    create.add_argument("--valkey-cli", default="valkey-cli")

    check = subparsers.add_parser("check", help="check Valkey Cluster state from a plan")
    check.add_argument("--plan", required=True)
    check.add_argument("--events", required=True)
    check.add_argument("--valkey-cli", default="valkey-cli")

    run = subparsers.add_parser("run", help="plan a run and emit artifacts/report")
    run.add_argument("--inventory", required=True)
    run.add_argument("--scenario", required=True)
    run.add_argument("--out-dir")

    args = parser.parse_args(argv)
    if args.command == "validate":
        return _validate(Path(args.inventory), Path(args.scenario))
    if args.command == "plan":
        return _plan(Path(args.inventory), Path(args.scenario), args.out_dir)
    if args.command == "report":
        return _report(args.run_id, args.artifacts_dir, args.reports_root)
    if args.command == "create-cluster":
        return _create_cluster(Path(args.plan), Path(args.events), args.valkey_cli)
    if args.command == "check":
        return _check_cluster(Path(args.plan), Path(args.events), args.valkey_cli)
    if args.command == "run":
        return _run(Path(args.inventory), Path(args.scenario), args.out_dir)
    parser.error(f"unknown command {args.command}")
    return 2


def _validate(inventory_path: Path, scenario_path: Path) -> int:
    try:
        inventory, scenario = _load_and_cross_validate(inventory_path, scenario_path)
    except ValidationError as exc:
        print("Validation failed:", file=sys.stderr)
        for error in exc.errors:
            print(f"- {error}", file=sys.stderr)
        return 1
    print(
        f"Validation passed: inventory={inventory.name} scenario={scenario.name} "
        f"nodes={scenario.node_count} virtual AZ mode={scenario.topology_mode}"
    )
    return 0


def _plan(inventory_path: Path, scenario_path: Path, out_dir: str | None) -> int:
    try:
        inventory, scenario = _load_and_cross_validate(inventory_path, scenario_path)
        target_dir = Path(out_dir) if out_dir else Path("artifacts") / scenario.run_id
        plan = build_cluster_plan(inventory, scenario)
        path = write_cluster_plan(plan, target_dir)
    except (ValidationError, ValueError) as exc:
        print("Planning failed:", file=sys.stderr)
        if isinstance(exc, ValidationError):
            for error in exc.errors:
                print(f"- {error}", file=sys.stderr)
        else:
            print(f"- {exc}", file=sys.stderr)
        return 1
    print(f"Wrote cluster plan: {path}")
    return 0


def _load_and_cross_validate(inventory_path: Path, scenario_path: Path):
    inventory = load_inventory(inventory_path)
    scenario = load_scenario(scenario_path)
    if inventory.topology_mode != scenario.topology_mode:
        raise ValidationError(
            [
                "inventory.topology_mode must match scenario.topology_mode "
                f"({inventory.topology_mode!r} != {scenario.topology_mode!r})"
            ]
        )
    return inventory, scenario


def _report(run_id: str, artifacts_dir: str | None, reports_root: str) -> int:
    source = Path(artifacts_dir) if artifacts_dir else Path("artifacts") / run_id
    if not source.exists() and run_id == "fixture-minimal":
        source = Path("tests/fixtures/minimal_run")
    if not source.exists():
        print(f"Report generation failed: artifacts directory not found: {source}", file=sys.stderr)
        return 1
    path = generate_report(run_id, source, reports_root)
    print(f"Wrote report: {path}")
    return 0


def _create_cluster(plan_path: Path, events_path: Path, valkey_cli: str) -> int:
    plan = json.loads(plan_path.read_text(encoding="utf-8"))
    result = create_cluster(plan, _CliAdapter(valkey_cli), events_path)
    return 0 if result.ok else 1


def _check_cluster(plan_path: Path, events_path: Path, valkey_cli: str) -> int:
    plan = json.loads(plan_path.read_text(encoding="utf-8"))
    result = check_cluster(plan, _CliAdapter(valkey_cli), events_path)
    return 0 if result.ok else 1


def _run(inventory_path: Path, scenario_path: Path, out_dir: str | None) -> int:
    try:
        inventory, scenario = _load_and_cross_validate(inventory_path, scenario_path)
        target_dir = Path(out_dir) if out_dir else Path("artifacts") / scenario.run_id
        plan = build_cluster_plan(inventory, scenario)
        plan_path = write_cluster_plan(plan, target_dir)
        events_path = target_dir / "events.jsonl"
        append_event(events_path, scenario.run_id, "plan_written", artifact_path=str(plan_path))
        summary_path = target_dir / "report_summary.json"
        summary_path.write_text(
            json.dumps(
                {
                    "executive_summary": "Run artifacts created. Cluster execution requires nodehost and Valkey runtime availability.",
                    "environment": {"inventory": inventory.name, "scenario": scenario.name},
                    "test_matrix": ["cluster_create_check"],
                    "cluster_formation": "SKIPPED_SCOPE: invoke create-cluster after nodehost runtime is started.",
                    "failover": "MISSING",
                    "migration": "MISSING",
                    "resource_metrics": {"rss_bytes": "MISSING", "fd_count": "MISSING"},
                    "validation": {
                        "validated": ["plan"],
                        "not_validated": ["live cluster creation"],
                        "inconclusive": ["runtime metrics"],
                    },
                },
                indent=2,
                sort_keys=True,
            )
            + "\n",
            encoding="utf-8",
        )
        report_path = generate_report(scenario.run_id, target_dir)
        append_event(events_path, scenario.run_id, "report_written", artifact_path=str(report_path))
    except (ValidationError, ValueError) as exc:
        print(f"Run failed: {exc}", file=sys.stderr)
        return 1
    print(f"Run artifacts: {target_dir}")
    print(f"Report: {report_path}")
    return 0


class _CliAdapter:
    def __init__(self, path: str) -> None:
        self.cli = ValkeyCli(path)

    def command(self, host: str, port: int, *args: str) -> str:
        result = self.cli.run(host, port, *args)
        if result.returncode != 0:
            raise RuntimeError(result.stderr.strip() or result.stdout.strip())
        return result.stdout


if __name__ == "__main__":
    raise SystemExit(main())
