"""Small JSON output helpers for CLI commands."""

import json
import sys


def emit(payload, *, stream=None):
    target = stream or sys.stdout
    target.write(json.dumps(payload, sort_keys=True, separators=(",", ":")) + "\n")


def base_payload(command, status="OK", **extra):
    payload = {"command": command, "status": status}
    payload.update(extra)
    return payload
