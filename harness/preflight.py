"""Scenario preflight checks."""

import shutil


def check_backend(backend):
    if backend == "fake":
        return {"status": "PASS", "backend": "fake", "reason": "fake backend requires no external runtime"}
    if shutil.which("valkey-server") is None:
        return {"status": "SKIPPED_RESOURCE", "backend": backend, "reason": "valkey-server binary not found"}
    return {"status": "PASS", "backend": backend, "reason": "valkey-server binary found"}
