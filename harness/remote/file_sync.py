from __future__ import annotations

import shutil
from pathlib import Path


def sync_file(source: str | Path, destination: str | Path) -> Path:
    src = Path(source)
    dst = Path(destination)
    dst.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(src, dst)
    return dst


def sync_tree(source: str | Path, destination: str | Path) -> Path:
    src = Path(source)
    dst = Path(destination)
    if dst.exists():
        shutil.rmtree(dst)
    shutil.copytree(src, dst)
    return dst
