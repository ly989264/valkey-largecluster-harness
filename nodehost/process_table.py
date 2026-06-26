from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any


class ProcessTable:
    def __init__(self, run_dir: str | Path) -> None:
        self.run_dir = Path(run_dir)
        self.path = self.run_dir / "processes.json"

    def load(self) -> list[dict[str, Any]]:
        if not self.path.exists():
            return []
        return json.loads(self.path.read_text(encoding="utf-8"))

    def save(self, processes: list[dict[str, Any]]) -> None:
        self.run_dir.mkdir(parents=True, exist_ok=True)
        self.path.write_text(json.dumps(processes, indent=2, sort_keys=True) + "\n", encoding="utf-8")

    def alive(self, pid: int) -> bool:
        try:
            os.kill(pid, 0)
        except ProcessLookupError:
            return False
        except PermissionError:
            return True
        return True
