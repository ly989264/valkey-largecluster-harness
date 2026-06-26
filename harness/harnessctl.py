from __future__ import annotations

import argparse
import sys
from pathlib import Path

from harness.inventory import ValidationError, load_inventory
from harness.planner import build_cluster_plan, write_cluster_plan
from harness.scenario import load_scenario


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

    args = parser.parse_args(argv)
    if args.command == "validate":
        return _validate(Path(args.inventory), Path(args.scenario))
    if args.command == "plan":
        return _plan(Path(args.inventory), Path(args.scenario), args.out_dir)
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


if __name__ == "__main__":
    raise SystemExit(main())
