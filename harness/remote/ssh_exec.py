from __future__ import annotations

import subprocess
from dataclasses import dataclass
from pathlib import Path
from typing import Protocol

from harness.events import append_event


@dataclass(frozen=True)
class CommandResult:
    returncode: int
    stdout: str
    stderr: str


class Executor(Protocol):
    def run(self, command: list[str]) -> CommandResult:
        ...


class LocalhostExecutor:
    def run(self, command: list[str]) -> CommandResult:
        result = subprocess.run(command, text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        return CommandResult(result.returncode, result.stdout, result.stderr)


@dataclass(frozen=True)
class SshExecutor:
    host: str
    user: str | None = None

    def run(self, command: list[str]) -> CommandResult:
        target = f"{self.user}@{self.host}" if self.user else self.host
        result = subprocess.run(
            ["ssh", target, *command],
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )
        return CommandResult(result.returncode, result.stdout, result.stderr)


def run_logged(
    executor: Executor,
    command: list[str],
    events_path: str | Path,
    run_id: str,
    host_id: str,
    dry_run: bool = False,
) -> CommandResult:
    append_event(
        events_path,
        run_id,
        "remote_command",
        host_id=host_id,
        command=command,
        dry_run=dry_run,
    )
    if dry_run:
        return CommandResult(0, "DRY_RUN", "")
    result = executor.run(command)
    append_event(
        events_path,
        run_id,
        "remote_command_result",
        host_id=host_id,
        returncode=result.returncode,
        stdout=result.stdout,
        stderr=result.stderr,
    )
    return result
