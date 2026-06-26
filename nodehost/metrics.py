from __future__ import annotations

import os
import subprocess
from typing import Any


MISSING = "MISSING"


def process_metrics(pid: int) -> dict[str, Any]:
    return {
        "rss_bytes": _rss_bytes(pid),
        "fd_count": _fd_count(pid),
    }


def _rss_bytes(pid: int) -> int | str:
    try:
        output = subprocess.check_output(["ps", "-o", "rss=", "-p", str(pid)], text=True).strip()
    except (subprocess.CalledProcessError, FileNotFoundError, PermissionError):
        return MISSING
    if not output:
        return MISSING
    try:
        return int(output.splitlines()[-1].strip()) * 1024
    except ValueError:
        return MISSING


def _fd_count(pid: int) -> int | str:
    proc_fd = f"/proc/{pid}/fd"
    if os.path.isdir(proc_fd):
        try:
            return len(os.listdir(proc_fd))
        except OSError:
            return MISSING
    return MISSING
