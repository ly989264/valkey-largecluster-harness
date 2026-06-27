"""Run status writer/reader."""

import json


class RunStatusWriter:
    def __init__(self, path):
        self.path = path
        self.path.parent.mkdir(parents=True, exist_ok=True)

    def write(self, status, **fields):
        payload = {"status": status}
        payload.update(fields)
        self.path.write_text(json.dumps(payload, sort_keys=True, indent=2) + "\n", encoding="utf-8")
        return payload


def read_status(path):
    with path.open(encoding="utf-8") as f:
        return json.load(f)
