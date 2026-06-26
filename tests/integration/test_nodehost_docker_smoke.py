from __future__ import annotations

import shutil
import subprocess

import pytest


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
    result = subprocess.run(
        ["docker", "build", "-f", "docker/nodehost.Dockerfile", "-t", "valkey-nodehost:test", "."],
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
    )
    assert result.returncode == 0, result.stdout
