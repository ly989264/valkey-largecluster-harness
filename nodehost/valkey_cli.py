from __future__ import annotations

import subprocess
from dataclasses import dataclass


@dataclass(frozen=True)
class ValkeyCli:
    path: str = "valkey-cli"

    def run(self, host: str, port: int, *args: str) -> subprocess.CompletedProcess[str]:
        return subprocess.run(
            [self.path, "-h", host, "-p", str(port), *args],
            check=False,
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )
