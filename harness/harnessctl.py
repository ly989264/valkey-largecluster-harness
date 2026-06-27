"""Minimal harnessctl command shell for P01."""

import argparse
import sys

from harness import __version__
from harness.errors import HarnessError
from harness.jsonio import base_payload, emit


COMMANDS = ("version", "doctor", "validate", "plan", "run-scenario", "report")


def command_payload(command, **extra):
    return base_payload(command, **extra)


def handle_version(args):
    emit(command_payload("version", version=__version__))
    return 0


def handle_doctor(args):
    if not args.dry_run:
        raise HarnessError("doctor currently requires --dry-run in P01", status="NOT_IMPLEMENTED")
    emit(
        command_payload(
            "doctor",
            mode="dry-run",
            reason="P01 dry-run only; no Docker, SSH, Valkey, or network access attempted",
            checks=[
                {"name": "package_import", "status": "PASS"},
                {"name": "external_runtime", "status": "NOT_VALIDATED"},
            ],
        )
    )
    return 0


def handle_not_implemented(command):
    def _handler(args):
        emit(command_payload(command, status="NOT_IMPLEMENTED", reason=f"{command} is introduced as a CLI shell in P01"))
        return 0

    return _handler


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

    for name in ("validate", "plan", "run-scenario", "report"):
        cmd = sub.add_parser(name, help=f"{name} command shell")
        cmd.add_argument("--json", action="store_true", help="emit JSON")
        cmd.set_defaults(func=handle_not_implemented(name))

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
