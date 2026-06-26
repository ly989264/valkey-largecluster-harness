from __future__ import annotations

from harness.cluster.migration import run_atomic_slot_migration


class FakeMigrationClient:
    def __init__(self, fail_first: bool = False) -> None:
        self.fail_first = fail_first
        self.migrate_attempts = 0
        self.commands: list[tuple[str, ...]] = []

    def command(self, host: str, port: int, *args: str) -> str:
        self.commands.append(args)
        if args[:2] == ("COMMAND", "INFO"):
            return "supported"
        if args[:2] == ("CLUSTER", "MIGRATESLOT"):
            self.migrate_attempts += 1
            if self.fail_first and self.migrate_attempts == 1:
                raise RuntimeError("ASK during migration")
            return "OK"
        if args[0] == "GETSLOTMIGRATIONS":
            return "slot=42 state=done"
        return "OK"


def test_atomic_slot_migration_supports_cancel_and_retry() -> None:
    client = FakeMigrationClient(fail_first=True)

    result = run_atomic_slot_migration(client, ("127.0.0.1", 7000), ("127.0.0.1", 7001), 42)

    assert result.status == "VALIDATED"
    assert "ASK during migration" in result.observed_client_effects
    assert ("CLUSTER", "CANCELSLOTMIGRATION", "42") in client.commands
    assert result.getslotmigrations == "slot=42 state=done"
