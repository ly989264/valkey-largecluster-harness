"""Append-only event JSONL recorder and replay."""

import json


EVENT_TYPES = ("run", "command", "node", "cluster", "fault", "failover", "metric", "assertion")


class EventRecorder:
    def __init__(self, path):
        self.path = path
        self.path.parent.mkdir(parents=True, exist_ok=True)

    def append(self, event_type, **fields):
        if event_type not in EVENT_TYPES:
            raise ValueError(f"unknown event_type {event_type}")
        event = {"event_type": event_type}
        event.update(fields)
        with self.path.open("a", encoding="utf-8") as f:
            f.write(json.dumps(event, sort_keys=True, separators=(",", ":")) + "\n")
        return event


def replay_events(path):
    records = []
    with path.open(encoding="utf-8") as f:
        for lineno, line in enumerate(f, 1):
            raw = line.rstrip("\n")
            if not raw:
                continue
            try:
                event = json.loads(raw)
                records.append({"valid": True, "line": lineno, "event": event})
            except json.JSONDecodeError as exc:
                records.append({"valid": False, "line": lineno, "raw": raw, "reason": str(exc)})
    return records
