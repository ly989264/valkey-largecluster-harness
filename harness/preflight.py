"""Scenario preflight checks."""

import shutil
from harness.docker_nodehost import DockerCapability


def check_backend(backend):
    if backend == "fake":
        return {"status": "PASS", "backend": "fake", "reason": "fake backend requires no external runtime"}
    if shutil.which("valkey-server") is None:
        return {"status": "SKIPPED_RESOURCE", "backend": backend, "reason": "valkey-server binary not found"}
    return {"status": "PASS", "backend": backend, "reason": "valkey-server binary found"}


def check_docker_hostnet(docker_cli=None, host_network=True):
    return DockerCapability(docker_cli=docker_cli, host_network=host_network).check()
