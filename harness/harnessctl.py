"""harnessctl command shell."""

import argparse
import sys

from harness import __version__
from harness.config import ConfigError, validate_config
from harness.errors import HarnessError
from harness.jsonio import base_payload, emit
from harness.cluster_plan import ClusterPlanError
from harness.planner import PlanError, build_cluster_plan
from harness.platform_adapter import adapter_for_platform
from harness.report_builder import build_report, write_report
from harness.scenario_runner import ScenarioRunner


COMMANDS = ("version", "doctor", "validate", "plan", "run-scenario", "report")


def command_payload(command, **extra):
    return base_payload(command, **extra)


def handle_version(args):
    emit(command_payload("version", version=__version__))
    return 0


def handle_doctor(args):
    if not args.dry_run:
        raise HarnessError("doctor currently requires --dry-run in P01", status="NOT_IMPLEMENTED")
    adapter = adapter_for_platform()
    emit(
        command_payload(
            "doctor",
            mode="dry-run",
            reason="P01 dry-run only; no Docker, SSH, Valkey, or network access attempted",
            platform_capabilities=adapter.capabilities(),
            linux_migration_path={
                "platform": "linux",
                "network_fault_backend_hint": "linux-tc-netem",
                "host_network": True,
            },
            checks=[
                {"name": "package_import", "status": "PASS"},
                {"name": "external_runtime", "status": "NOT_VALIDATED"},
                {"name": "platform_adapter", "status": "PASS"},
            ],
        )
    )
    return 0


def handle_not_implemented(command):
    def _handler(args):
        emit(command_payload(command, status="NOT_IMPLEMENTED", reason=f"{command} is introduced as a CLI shell in P01"))
        return 0

    return _handler


def handle_validate(args):
    if not args.inventory or not args.scenario:
        emit(command_payload("validate", status="NOT_IMPLEMENTED", reason="P02 validate requires --inventory and --scenario"))
        return 0
    try:
        result = validate_config(args.inventory, args.scenario)
    except ConfigError as exc:
        emit(command_payload("validate", status="FAIL", reason=str(exc)), stream=sys.stderr)
        return 1
    emit(command_payload("validate", inventory=args.inventory, scenario=args.scenario, result=result))
    return 0


def handle_plan(args):
    if not args.inventory or not args.scenario:
        emit(command_payload("plan", status="NOT_IMPLEMENTED", reason="P03 plan requires --inventory and --scenario"))
        return 0
    try:
        plan = build_cluster_plan(args.inventory, args.scenario)
    except (ConfigError, PlanError, ClusterPlanError) as exc:
        emit(command_payload("plan", status="FAIL", reason=str(exc)), stream=sys.stderr)
        return 1
    emit(command_payload("plan", plan=plan))
    return 0


def handle_run_scenario(args):
    if not args.inventory or not args.scenario or not args.run_id:
        emit(command_payload("run-scenario", status="NOT_IMPLEMENTED", reason="P10 run-scenario requires --inventory, --scenario, and --run-id"))
        return 0
    result = ScenarioRunner().run(args.inventory, args.scenario, args.run_id, backend=args.backend)
    emit(command_payload("run-scenario", **result))
    return 0 if result["status"] in {"PASS", "SKIPPED_RESOURCE"} else 1


def handle_report(args):
    kwargs = {"artifacts_root": args.artifacts_root, "scenarios_dir": args.scenarios_dir}
    if args.output:
        report = write_report(args.output, **kwargs)
    else:
        report = build_report(**kwargs)
    emit(command_payload("report", report=report.to_dict(), status_counts=report.status_counts()))
    return 0


def build_parser():
    parser = argparse.ArgumentParser(prog="harnessctl")
    sub = parser.add_subparsers(dest="command", required=True)

    version = sub.add_parser("version", help="print harness version")
    version.add_argument("--json", action="store_true", help="emit JSON")
    version.set_defaults(func=handle_version)

    doctor = sub.add_parser("doctor", help="inspect harness environment without changing it")
    doctor.add_argument("--dry-run", action="store_true", help="avoid external probes")
    doctor.add_argument("--json", action="store_true", help="emit JSON")
    doctor.set_defaults(func=handle_doctor)

    validate = sub.add_parser("validate", help="validate inventory and scenario config")
    validate.add_argument("--inventory", help="inventory file path")
    validate.add_argument("--scenario", help="scenario file path")
    validate.add_argument("--json", action="store_true", help="emit JSON")
    validate.set_defaults(func=handle_validate)

    plan = sub.add_parser("plan", help="create a deterministic topology draft")
    plan.add_argument("--inventory", help="inventory file path")
    plan.add_argument("--scenario", help="scenario file path")
    plan.add_argument("--json", action="store_true", help="emit JSON")
    plan.set_defaults(func=handle_plan)

    run_scenario = sub.add_parser("run-scenario", help="run a scenario")
    run_scenario.add_argument("--inventory")
    run_scenario.add_argument("--scenario")
    run_scenario.add_argument("--run-id")
    run_scenario.add_argument("--backend", default="fake")
    run_scenario.add_argument("--json", action="store_true", help="emit JSON")
    run_scenario.set_defaults(func=handle_run_scenario)

    report = sub.add_parser("report", help="build an audit report from artifacts")
    report.add_argument("--artifacts-root", default="artifacts")
    report.add_argument("--scenarios-dir", default="scenarios")
    report.add_argument("--output")
    report.add_argument("--json", action="store_true", help="emit JSON")
    report.set_defaults(func=handle_report)

    return parser


def main(argv=None):
    parser = build_parser()
    args = parser.parse_args(argv)
    try:
        return args.func(args)
    except HarnessError as exc:
        emit(command_payload(args.command, status=exc.status, reason=exc.reason), stream=sys.stderr)
        return exc.exit_code


if __name__ == "__main__":
    raise SystemExit(main())
