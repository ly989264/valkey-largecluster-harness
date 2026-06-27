"""nodehostctl CLI for local fake nodehost management."""

import argparse
import json
from pathlib import Path

from nodehost.local_process import LocalProcessManager


DEFAULT_ROOT = Path("/tmp") / "valkey-largecluster-nodehost"


def emit(payload):
    print(json.dumps(payload, sort_keys=True, separators=(",", ":")))


def manager(args):
    return LocalProcessManager.with_root(args.root)


def handle_status(args):
    emit({"status": "OK", "command": "status", "result": manager(args).status(args.run_id)})
    return 0


def handle_prepare(args):
    emit({"status": "OK", "command": "prepare", "result": manager(args).prepare(args.run_id)})
    return 0


def handle_start(args):
    emit({"status": "OK", "command": "start", "result": manager(args).start(args.run_id, args.node_id)})
    return 0


def handle_stop(args):
    emit({"status": "OK", "command": "stop", "result": manager(args).stop(args.run_id, args.node_id or None)})
    return 0


def handle_cleanup(args):
    emit({"status": "OK", "command": "cleanup", "result": manager(args).cleanup(args.run_id)})
    return 0


def handle_metrics(args):
    emit({"status": "OK", "command": "metrics", "result": manager(args).metrics(args.run_id)})
    return 0


def build_parser():
    parser = argparse.ArgumentParser(prog="nodehostctl")
    parser.add_argument("--root", type=Path, default=DEFAULT_ROOT)
    sub = parser.add_subparsers(dest="command", required=True)
    status = sub.add_parser("status")
    status.add_argument("--run-id")
    status.add_argument("--json", action="store_true")
    status.set_defaults(func=handle_status)
    for name, func in [
        ("prepare", handle_prepare),
        ("start", handle_start),
        ("stop", handle_stop),
        ("cleanup", handle_cleanup),
        ("metrics", handle_metrics),
    ]:
        cmd = sub.add_parser(name)
        cmd.add_argument("--run-id", required=True)
        cmd.add_argument("--json", action="store_true")
        if name in {"start", "stop"}:
            cmd.add_argument("--node-id", action="append", default=[])
        cmd.set_defaults(func=func)
    return parser


def main(argv=None):
    args = build_parser().parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    raise SystemExit(main())
