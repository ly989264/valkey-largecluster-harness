from __future__ import annotations

import os
import signal
import time
from dataclasses import dataclass


@dataclass(frozen=True)
class FaultResult:
    applied: bool
    fault_injected_at: float | None
    detail: str


def kill_process(pid: int, apply: bool = False, sig: signal.Signals = signal.SIGTERM) -> FaultResult:
    if not apply:
        return FaultResult(False, None, f"planned kill pid={pid} signal={sig.name}")
    injected_at = time.monotonic()
    os.kill(pid, sig)
    return FaultResult(True, injected_at, f"killed pid={pid} signal={sig.name}")
