from __future__ import annotations

import os
import signal
import subprocess
import time
from pathlib import Path
from typing import Any

from nodehost.gen_configs import generate_configs, load_plan
from nodehost.metrics import process_metrics
from nodehost.process_table import ProcessTable


def start(plan_path: str | Path, run_dir: str | Path, valkey_server: str) -> list[dict[str, Any]]:
    run_path = Path(run_dir)
    generate_configs(plan_path, run_path)
    table = ProcessTable(run_path)
    existing = [entry for entry in table.load() if table.alive(int(entry["pid"]))]
    existing_ids = {entry["node_id"] for entry in existing}
    plan = load_plan(plan_path)
    processes = list(existing)
    log_dir = run_path / "logs"
    log_dir.mkdir(parents=True, exist_ok=True)
    for node in plan.get("nodes", []):
        if node["id"] in existing_ids:
            continue
        conf_path = run_path / "conf" / f"{node['id']}.conf"
        stdout = (log_dir / f"{node['id']}.log").open("ab")
        proc = subprocess.Popen(
            [valkey_server, str(conf_path)],
            cwd=str(run_path),
            stdout=stdout,
            stderr=subprocess.STDOUT,
            start_new_session=True,
        )
        processes.append(_entry(node, proc.pid, conf_path))
    table.save(processes)
    return status(run_path)


def stop(run_dir: str | Path, timeout_seconds: float = 5.0) -> list[dict[str, Any]]:
    table = ProcessTable(run_dir)
    processes = table.load()
    signaled: set[int] = set()
    for entry in processes:
        pid = int(entry["pid"])
        if table.alive(pid):
            try:
                os.killpg(pid, signal.SIGTERM)
                signaled.add(pid)
            except ProcessLookupError:
                pass
            except PermissionError:
                try:
                    os.kill(pid, signal.SIGTERM)
                    signaled.add(pid)
                except (ProcessLookupError, PermissionError):
                    pass
    deadline = time.monotonic() + timeout_seconds
    while time.monotonic() < deadline:
        if all(not table.alive(int(entry["pid"])) for entry in processes):
            break
        time.sleep(0.05)
    for entry in processes:
        pid = int(entry["pid"])
        if table.alive(pid):
            try:
                os.killpg(pid, signal.SIGKILL)
                signaled.add(pid)
            except ProcessLookupError:
                pass
            except PermissionError:
                try:
                    os.kill(pid, signal.SIGKILL)
                    signaled.add(pid)
                except (ProcessLookupError, PermissionError):
                    pass
    current = []
    for entry in status(run_dir):
        if int(entry["pid"]) in signaled:
            entry["alive"] = False
        current.append(entry)
    table.save(current)
    return current


def status(run_dir: str | Path) -> list[dict[str, Any]]:
    table = ProcessTable(run_dir)
    result = []
    for entry in table.load():
        item = dict(entry)
        item["alive"] = table.alive(int(entry["pid"]))
        result.append(item)
    return result


def metrics(run_dir: str | Path) -> list[dict[str, Any]]:
    rows = []
    for entry in status(run_dir):
        row = dict(entry)
        if entry["alive"]:
            row.update(process_metrics(int(entry["pid"])))
        else:
            row.update({"rss_bytes": "MISSING", "fd_count": "MISSING"})
        rows.append(row)
    return rows


def _entry(node: dict[str, Any], pid: int, conf_path: Path) -> dict[str, Any]:
    return {
        "node_id": node["id"],
        "pid": pid,
        "alive": True,
        "port": node["client_port"],
        "bus_port": node["bus_port"],
        "virtual_az_id": node["virtual_az_id"],
        "host_id": node["host_id"],
        "config_path": str(conf_path),
    }
