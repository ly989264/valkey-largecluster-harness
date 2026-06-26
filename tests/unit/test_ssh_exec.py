from __future__ import annotations

from pathlib import Path

from harness.remote.ssh_exec import CommandResult, run_logged


class FakeExecutor:
    def __init__(self) -> None:
        self.commands: list[list[str]] = []

    def run(self, command: list[str]) -> CommandResult:
        self.commands.append(command)
        return CommandResult(0, "ok", "")


def test_run_logged_supports_dry_run_without_executing(tmp_path: Path) -> None:
    fake = FakeExecutor()
    events = tmp_path / "events.jsonl"

    result = run_logged(fake, ["docker", "ps"], events, "run-1", "host-1", dry_run=True)

    assert result.stdout == "DRY_RUN"
    assert fake.commands == []
    assert "remote_command" in events.read_text(encoding="utf-8")


def test_run_logged_executes_and_records_result(tmp_path: Path) -> None:
    fake = FakeExecutor()
    events = tmp_path / "events.jsonl"

    result = run_logged(fake, ["docker", "ps"], events, "run-1", "host-1", dry_run=False)

    assert result.stdout == "ok"
    assert fake.commands == [["docker", "ps"]]
    text = events.read_text(encoding="utf-8")
    assert "remote_command_result" in text
