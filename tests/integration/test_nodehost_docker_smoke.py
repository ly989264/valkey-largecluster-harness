from __future__ import annotations

import json
import shutil
import subprocess
import os
import time
from pathlib import Path

import pytest

from harness.inventory import load_inventory
from harness.planner import build_cluster_plan, write_cluster_plan
from harness.scenario import load_scenario


def test_dockerfile_declares_nodehost_container_model() -> None:
    dockerfile = open("docker/nodehost.Dockerfile", encoding="utf-8").read()
    assert "/data/valkey-largecluster" in dockerfile
    assert "nodehost.nodehostctl" not in dockerfile


def test_nodehost_docker_build_smoke_when_docker_available() -> None:
    if shutil.which("docker") is None:
        pytest.skip("Docker CLI unavailable")
    info = subprocess.run(
        ["docker", "info"],
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
    )
    if info.returncode != 0:
        pytest.skip(f"Docker daemon unavailable: {info.stdout.strip()}")
    base_image = _base_image()
    result = subprocess.run(
        [
            "docker",
            "build",
            "--build-arg",
            f"BASE_IMAGE={base_image}",
            "-f",
            "docker/nodehost.Dockerfile",
            "-t",
            "valkey-nodehost:test",
            ".",
        ],
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
    )
    assert result.returncode == 0, result.stdout


def test_nodehost_container_runs_n6_status_with_fake_valkey(tmp_path: Path) -> None:
    if shutil.which("docker") is None:
        pytest.skip("Docker CLI unavailable")
    info = subprocess.run(
        ["docker", "info"],
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
    )
    if info.returncode != 0:
        pytest.skip(f"Docker daemon unavailable: {info.stdout.strip()}")

    image = "valkey-nodehost:test"
    build = subprocess.run(
        [
            "docker",
            "build",
            "--build-arg",
            f"BASE_IMAGE={_base_image()}",
            "-f",
            "docker/nodehost.Dockerfile",
            "-t",
            image,
            ".",
        ],
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
    )
    assert build.returncode == 0, build.stdout

    host_run_dir = tmp_path / "docker-nodehost"
    host_run_dir.mkdir()
    plan = build_cluster_plan(
        load_inventory("inventories/single-mac.dev.yaml"),
        load_scenario("scenarios/smoke-6.yaml"),
    )
    write_cluster_plan(plan, host_run_dir)
    fake_server = host_run_dir / "fake-valkey-server"
    fake_server.write_text(
        "#!/bin/sh\n"
        "trap 'exit 0' TERM INT\n"
        "while true; do sleep 1; done\n",
        encoding="utf-8",
    )
    fake_server.chmod(0o755)

    container = f"valkey-nodehost-test-{os.getpid()}"
    subprocess.run(["docker", "rm", "-f", container], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    try:
        run = subprocess.run(
            [
                "docker",
                "run",
                "-d",
                "--name",
                container,
                "--network",
                "host",
                "-v",
                f"{host_run_dir}:/data/valkey-largecluster/smoke",
                image,
                "start",
                "--plan",
                "/data/valkey-largecluster/smoke/cluster_plan.json",
                "--run-dir",
                "/data/valkey-largecluster/smoke/run",
                "--valkey-server",
                "/data/valkey-largecluster/smoke/fake-valkey-server",
            ],
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
        )
        assert run.returncode == 0, run.stdout
        rows = _status_rows(container)
        assert len(rows) == 6
        assert all(row["alive"] for row in rows)
        assert {row["virtual_az_id"] for row in rows} == {"vaz-a"}
    finally:
        subprocess.run(["docker", "rm", "-f", container], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)


def _base_image() -> str:
    configured = os.environ.get("NODEHOST_DOCKER_BASE_IMAGE")
    if configured:
        return configured
    local_fallback = "dev-rockylinux-9.5-backup:latest"
    inspect = subprocess.run(
        ["docker", "image", "inspect", local_fallback],
        text=True,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )
    if inspect.returncode == 0:
        return local_fallback
    return "python:3.11-slim"


def _status_rows(container: str) -> list[dict]:
    deadline = time.monotonic() + 20
    last_output = ""
    while time.monotonic() < deadline:
        result = subprocess.run(
            [
                "docker",
                "exec",
                container,
                "python3",
                "-m",
                "nodehost.nodehostctl",
                "status",
                "--run-dir",
                "/data/valkey-largecluster/smoke/run",
                "--json",
            ],
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
        )
        last_output = result.stdout
        if result.returncode == 0:
            rows = json.loads(result.stdout)
            if len(rows) == 6:
                return rows
        time.sleep(0.25)
    raise AssertionError(last_output)
