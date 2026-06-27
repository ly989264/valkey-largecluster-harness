"""Command log writer for auditable harness actions."""

import json


class CommandLogWriter:
    def __init__(self, path):
        self.path = path
        self.path.parent.mkdir(parents=True, exist_ok=True)

    def append(self, command, exit_code, **fields):
        record = {"command": list(command), "exit_code": int(exit_code)}
        record.update(fields)
        with self.path.open("a", encoding="utf-8") as f:
            f.write(json.dumps(record, sort_keys=True, separators=(",", ":")) + "\n")
        return record


def read_command_log(path):
    records = []
    with path.open(encoding="utf-8") as f:
        for line in f:
            if line.strip():
                records.append(json.loads(line))
    return records
