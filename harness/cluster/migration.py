from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol


class MigrationClient(Protocol):
    def command(self, host: str, port: int, *args: str) -> str:
        ...


@dataclass(frozen=True)
class MigrationResult:
    status: str
    detail: str
    getslotmigrations: str
    observed_client_effects: list[str]


def run_atomic_slot_migration(
    client: MigrationClient,
    source: tuple[str, int],
    target: tuple[str, int],
    slot: int,
    key_count: int = 10,
    retry: bool = True,
) -> MigrationResult:
    if not _command_supported(client, source, "GETSLOTMIGRATIONS"):
        return MigrationResult("SKIPPED_SCOPE", "GETSLOTMIGRATIONS unsupported", "MISSING", [])
    if not _command_supported(client, source, "CLUSTER"):
        return MigrationResult("SKIPPED_SCOPE", "CLUSTER command unsupported", "MISSING", [])
    source_host, source_port = source
    target_host, target_port = target
    effects: list[str] = []
    try:
        client.command(
            source_host,
            source_port,
            "CLUSTER",
            "MIGRATESLOT",
            str(slot),
            target_host,
            str(target_port),
            str(key_count),
        )
    except Exception as exc:  # noqa: BLE001 - fake/real clients expose backend errors.
        effects.append(str(exc))
        if not retry:
            return MigrationResult("FAILED", str(exc), "MISSING", effects)
        client.command(source_host, source_port, "CLUSTER", "CANCELSLOTMIGRATION", str(slot))
        client.command(
            source_host,
            source_port,
            "CLUSTER",
            "MIGRATESLOT",
            str(slot),
            target_host,
            str(target_port),
            str(key_count),
        )
    migrations = client.command(source_host, source_port, "GETSLOTMIGRATIONS")
    return MigrationResult("VALIDATED", "atomic slot migration command accepted", migrations, effects)


def _command_supported(client: MigrationClient, endpoint: tuple[str, int], command: str) -> bool:
    host, port = endpoint
    output = client.command(host, port, "COMMAND", "INFO", command)
    return "unsupported" not in output.lower() and output.strip() not in {"", "[]"}
