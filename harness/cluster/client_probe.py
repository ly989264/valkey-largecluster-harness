from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol


class KeyValueClient(Protocol):
    def set_get(self, key: str, value: str) -> str:
        ...


@dataclass(frozen=True)
class ClientProbeResult:
    ok: bool
    detail: str
    observed_redirect: str | None = None


def probe_client_success(client: KeyValueClient, key: str = "failover-probe") -> ClientProbeResult:
    try:
        result = client.set_get(key, "1")
    except TimeoutError:
        return ClientProbeResult(False, "timeout")
    except Exception as exc:  # noqa: BLE001 - client adapters surface backend errors.
        message = str(exc)
        redirect = "MOVED" if "MOVED" in message else "ASK" if "ASK" in message else None
        return ClientProbeResult(False, message, redirect)
    return ClientProbeResult(result == "1", "ok" if result == "1" else result)
