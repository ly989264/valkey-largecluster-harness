from __future__ import annotations

import shutil
import subprocess
from dataclasses import dataclass


@dataclass(frozen=True)
class PreflightResult:
    ok: bool
    checks: list[dict[str, str | bool]]


def preflight() -> PreflightResult:
    checks: list[dict[str, str | bool]] = []
    docker_path = shutil.which("docker")
    checks.append(
        {
            "name": "docker_cli_available",
            "ok": bool(docker_path),
            "detail": docker_path or "MISSING",
        }
    )
    if not docker_path:
        return PreflightResult(False, checks)

    version = _run(["docker", "version", "--format", "{{.Server.Version}}"])
    checks.append(
        {
            "name": "docker_engine_available",
            "ok": version.returncode == 0,
            "detail": version.stdout.strip() or version.stderr.strip() or "MISSING",
        }
    )
    hostnet = _run(
        [
            "docker",
            "run",
            "--rm",
            "--network",
            "host",
            "hello-world",
        ]
    )
    checks.append(
        {
            "name": "host_networking_capability",
            "ok": hostnet.returncode == 0,
            "detail": hostnet.stdout.strip() or hostnet.stderr.strip() or "MISSING",
        }
    )
    return PreflightResult(all(bool(check["ok"]) for check in checks), checks)


def _run(command: list[str]) -> subprocess.CompletedProcess[str]:
    try:
        return subprocess.run(command, text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    except FileNotFoundError as exc:
        return subprocess.CompletedProcess(command, 127, "", str(exc))
