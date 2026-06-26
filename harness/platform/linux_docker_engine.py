from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class PreflightResult:
    ok: bool
    checks: list[dict[str, str | bool]]


def preflight() -> PreflightResult:
    return PreflightResult(
        ok=False,
        checks=[
            {
                "name": "linux_docker_engine_adapter",
                "ok": False,
                "detail": "minimal stub; implement host-specific checks before Linux scale runs",
            }
        ],
    )
