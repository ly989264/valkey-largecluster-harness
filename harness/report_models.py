"""Report data models with explicit validation states."""

from dataclasses import dataclass, field


REPORT_STATUSES = ("PASS", "FAIL", "MISSING", "INCONCLUSIVE", "NOT_VALIDATED", "SKIPPED_RESOURCE")


@dataclass(frozen=True)
class ReportItem:
    name: str
    status: str
    evidence: str = ""

    def __post_init__(self):
        if self.status not in REPORT_STATUSES:
            raise ValueError(f"unknown report status {self.status}")

    def to_dict(self):
        return {"name": self.name, "status": self.status, "evidence": self.evidence}


@dataclass(frozen=True)
class ReportSection:
    name: str
    items: tuple = field(default_factory=tuple)

    def to_dict(self):
        return {"name": self.name, "items": [item.to_dict() for item in self.items]}


@dataclass(frozen=True)
class HarnessReport:
    report_id: str
    sections: tuple
    raw_artifacts_index: tuple

    def to_dict(self):
        return {
            "report_id": self.report_id,
            "sections": [section.to_dict() for section in self.sections],
            "raw_artifacts_index": list(self.raw_artifacts_index),
        }

    def status_counts(self):
        counts = {status: 0 for status in REPORT_STATUSES}
        for section in self.sections:
            for item in section.items:
                counts[item.status] += 1
        return counts
