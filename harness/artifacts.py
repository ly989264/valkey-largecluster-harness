"""Run artifact path layout."""

from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class ArtifactLayout:
    root: Path
    run_id: str

    @classmethod
    def create(cls, root, run_id):
        layout = cls(Path(root), run_id)
        layout.run_dir.mkdir(parents=True, exist_ok=False)
        return layout

    @classmethod
    def open(cls, root, run_id):
        layout = cls(Path(root), run_id)
        layout.run_dir.mkdir(parents=True, exist_ok=True)
        return layout

    @property
    def run_dir(self):
        return self.root / self.run_id

    @property
    def events_path(self):
        return self.run_dir / "events.jsonl"

    @property
    def status_path(self):
        return self.run_dir / "run_status.json"

    @property
    def command_log_path(self):
        return self.run_dir / "commands.jsonl"

    @property
    def cluster_plan_path(self):
        return self.run_dir / "cluster_plan.json"

    def path(self, *parts):
        return self.run_dir.joinpath(*parts)
