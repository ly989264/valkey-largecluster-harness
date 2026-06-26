from __future__ import annotations

import argparse
import sys
from pathlib import Path

from harness.inventory import ValidationError, load_inventory
from harness.scenario import load_scenario


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="harnessctl")
    subparsers = parser.add_subparsers(dest="command", required=True)

    validate = subparsers.add_parser("validate", help="validate inventory and scenario")
    validate.add_argument("--inventory", required=True)
    validate.add_argument("--scenario", required=True)

    args = parser.parse_args(argv)
    if args.command == "validate":
        return _validate(Path(args.inventory), Path(args.scenario))
    parser.error(f"unknown command {args.command}")
    return 2


def _validate(inventory_path: Path, scenario_path: Path) -> int:
    try:
        inventory = load_inventory(inventory_path)
        scenario = load_scenario(scenario_path)
        if inventory.topology_mode != scenario.topology_mode:
            raise ValidationError(
                [
                    "inventory.topology_mode must match scenario.topology_mode "
                    f"({inventory.topology_mode!r} != {scenario.topology_mode!r})"
                ]
            )
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


if __name__ == "__main__":
    raise SystemExit(main())
