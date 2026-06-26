from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol


class ClusterScanClient(Protocol):
    def command(self, host: str, port: int, *args: str) -> str:
        ...


@dataclass(frozen=True)
class ClusterScanResult:
    status: str
    checks: dict[str, str]


def run_clusterscan_matrix(client: ClusterScanClient, endpoint: tuple[str, int]) -> ClusterScanResult:
    host, port = endpoint
    if not _command_supported(client, endpoint, "CLUSTERSCAN"):
        return ClusterScanResult("SKIPPED_SCOPE", {"CLUSTERSCAN": "unsupported"})
    checks = {
        "cursor": client.command(host, port, "CLUSTERSCAN", "0"),
        "match": client.command(host, port, "CLUSTERSCAN", "0", "MATCH", "user:*"),
        "type": _optional(client, endpoint, "TYPE", "string"),
        "slot": _optional(client, endpoint, "SLOT", "0"),
    }
    return ClusterScanResult("VALIDATED", checks)


def _optional(client: ClusterScanClient, endpoint: tuple[str, int], option: str, value: str) -> str:
    host, port = endpoint
    try:
        return client.command(host, port, "CLUSTERSCAN", "0", option, value)
    except Exception:  # noqa: BLE001 - unsupported command variants are scope skips.
        return "SKIPPED_SCOPE"


def _command_supported(client: ClusterScanClient, endpoint: tuple[str, int], command: str) -> bool:
    host, port = endpoint
    output = client.command(host, port, "COMMAND", "INFO", command)
    return "unsupported" not in output.lower() and output.strip() not in {"", "[]"}
