from __future__ import annotations

import argparse
import json
from pathlib import Path

from nodehost.gen_configs import generate_configs
from nodehost.supervisor import metrics, start, status, stop


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="nodehostctl")
    subparsers = parser.add_subparsers(dest="command", required=True)

    gen = subparsers.add_parser("gen-configs")
    gen.add_argument("--plan", required=True)
    gen.add_argument("--run-dir", required=True)

    start_cmd = subparsers.add_parser("start")
    start_cmd.add_argument("--plan", required=True)
    start_cmd.add_argument("--run-dir", required=True)
    start_cmd.add_argument("--valkey-server", required=True)

    stop_cmd = subparsers.add_parser("stop")
    stop_cmd.add_argument("--run-dir", required=True)

    status_cmd = subparsers.add_parser("status")
    status_cmd.add_argument("--run-dir", required=True)
    status_cmd.add_argument("--json", action="store_true")

    metrics_cmd = subparsers.add_parser("metrics")
    metrics_cmd.add_argument("--run-dir", required=True)
    metrics_cmd.add_argument("--json", action="store_true")

    args = parser.parse_args(argv)
    if args.command == "gen-configs":
        written = generate_configs(args.plan, args.run_dir)
        print(f"Wrote {len(written)} configs to {Path(args.run_dir) / 'conf'}")
        return 0
    if args.command == "start":
        rows = start(args.plan, args.run_dir, args.valkey_server)
        _print(rows, as_json=True)
        return 0
    if args.command == "stop":
        rows = stop(args.run_dir)
        _print(rows, as_json=True)
        return 0
    if args.command == "status":
        _print(status(args.run_dir), as_json=args.json)
        return 0
    if args.command == "metrics":
        _print(metrics(args.run_dir), as_json=args.json)
        return 0
    parser.error(f"unknown command {args.command}")
    return 2


def _print(rows: list[dict], as_json: bool) -> None:
    if as_json:
        print(json.dumps(rows, indent=2, sort_keys=True))
        return
    for row in rows:
        print(row)


if __name__ == "__main__":
    raise SystemExit(main())
