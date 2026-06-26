from __future__ import annotations

import json
import os
from pathlib import Path

from nodehost.nodehostctl import main


def test_nodehost_local_runtime_with_fake_valkey(tmp_path: Path) -> None:
    plan = json.loads(Path("tests/fixtures/minimal_run/cluster_plan.json").read_text(encoding="utf-8"))
    plan["nodes"] = plan["nodes"][:1]
    plan_path = tmp_path / "cluster_plan.json"
    plan_path.write_text(json.dumps(plan), encoding="utf-8")
    fake_server = tmp_path / "fake-valkey-server"
    fake_server.write_text(
        "#!/usr/bin/env python3\n"
        "import signal, time\n"
        "running = True\n"
        "signal.signal(signal.SIGTERM, lambda *_: globals().__setitem__('running', False))\n"
        "while running:\n"
        "    time.sleep(0.05)\n",
        encoding="utf-8",
    )
    fake_server.chmod(fake_server.stat().st_mode | 0o111)
    run_dir = tmp_path / "run"

    assert main(["gen-configs", "--plan", str(plan_path), "--run-dir", str(run_dir)]) == 0
    assert (run_dir / "conf" / "node-0001.conf").exists()

    assert (
        main(
            [
                "start",
                "--plan",
                str(plan_path),
                "--run-dir",
                str(run_dir),
                "--valkey-server",
                str(fake_server),
            ]
        )
        == 0
    )
    rows = json.loads((run_dir / "processes.json").read_text(encoding="utf-8"))
    assert rows[0]["port"] == 7000
    assert rows[0]["virtual_az_id"] == "vaz-a"

    assert main(["status", "--run-dir", str(run_dir), "--json"]) == 0
    assert main(["metrics", "--run-dir", str(run_dir), "--json"]) == 0
    assert main(["stop", "--run-dir", str(run_dir)]) == 0
    stopped = json.loads((run_dir / "processes.json").read_text(encoding="utf-8"))
    assert stopped[0]["alive"] is False
    try:
        os.kill(int(stopped[0]["pid"]), 0)
    except ProcessLookupError:
        pass
