"""Run-scoped node process table."""

import json
from pathlib import Path


class ProcessTable:
    def __init__(self, root):
        self.root = Path(root)

    def run_dir(self, run_id):
        if not run_id:
            raise ValueError("run_id is required")
        return self.root / run_id

    def path(self, run_id):
        return self.run_dir(run_id) / "process_table.json"

    def load(self, run_id):
        path = self.path(run_id)
        if not path.exists():
            return {"run_id": run_id, "nodes": {}}
        with path.open(encoding="utf-8") as f:
            return json.load(f)

    def save(self, run_id, data):
        path = self.path(run_id)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(data, sort_keys=True, indent=2) + "\n", encoding="utf-8")
        return data

    def cleanup(self, run_id):
        path = self.path(run_id)
        if path.exists():
            path.unlink()
        run_dir = self.run_dir(run_id)
        if run_dir.exists() and not any(run_dir.iterdir()):
            run_dir.rmdir()
        return {"run_id": run_id, "removed": True}
