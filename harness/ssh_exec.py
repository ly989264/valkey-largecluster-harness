"""SSH execution abstractions."""

from dataclasses import dataclass

from harness.executor import CommandResult, SubprocessExecutor


@dataclass(frozen=True)
class SSHCommand:
    host: str
    argv: tuple


class SSHExecutor:
    def __init__(self, executor=None):
        self.executor = executor or SubprocessExecutor()

    def run(self, host, argv):
        command = ("ssh", "-o", "BatchMode=yes", host, *argv)
        return self.executor.run(command)


class FakeSSHExecutor:
    def __init__(self):
        self.commands = []

    def run(self, host, argv):
        argv = tuple(argv)
        self.commands.append(SSHCommand(host, argv))
        return CommandResult(command=("ssh", host, *argv), exit_code=0, stdout="", stderr="")
