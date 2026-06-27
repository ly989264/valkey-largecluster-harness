"""Command executor abstractions for platform adapters."""

import subprocess
from dataclasses import dataclass


@dataclass(frozen=True)
class CommandResult:
    command: tuple
    exit_code: int
    stdout: str = ""
    stderr: str = ""


class FakeExecutor:
    def __init__(self, results=None):
        self.results = list(results or [])
        self.commands = []

    def run(self, command):
        command = tuple(command)
        self.commands.append(command)
        if self.results:
            return self.results.pop(0)
        return CommandResult(command=command, exit_code=0, stdout="", stderr="")


class SubprocessExecutor:
    def run(self, command):
        command = tuple(command)
        cp = subprocess.run(command, text=True, capture_output=True)
        return CommandResult(command=command, exit_code=cp.returncode, stdout=cp.stdout, stderr=cp.stderr)
