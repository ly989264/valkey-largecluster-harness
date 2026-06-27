"""Scenario runner for P10 fake smoke path."""

import json
from pathlib import Path

from harness.artifacts import ArtifactLayout
from harness.cluster_check import ClusterChecker
from harness.cluster_create import ClusterCreator
from harness.command_log import CommandLogWriter
from harness.config import validate_config
from harness.events import EventRecorder
from harness.nodehost_client import NodehostClient
from harness.planner import build_cluster_plan
from harness.preflight import check_backend
from harness.status import RunStatusWriter
from harness.valkey_cli import FakeValkeyCli


DEFAULT_RUN_ROOT = Path("/tmp") / "valkey-largecluster-harness-runs"
DEFAULT_NODEHOST_ROOT = Path("/tmp") / "valkey-largecluster-harness-nodehost"


class ScenarioRunner:
    def __init__(self, run_root=DEFAULT_RUN_ROOT, nodehost_root=DEFAULT_NODEHOST_ROOT):
        self.run_root = Path(run_root)
        self.nodehost_root = Path(nodehost_root)

    def run(self, inventory_path, scenario_path, run_id, backend="fake"):
        layout = ArtifactLayout.open(self.run_root, run_id)
        events = EventRecorder(layout.events_path)
        status_writer = RunStatusWriter(layout.status_path)
        commands = CommandLogWriter(layout.command_log_path)
        nodehost = NodehostClient(self.nodehost_root)
        try:
            preflight = check_backend(backend)
            events.append("run", action="preflight", backend=backend, status=preflight["status"])
            if preflight["status"] == "SKIPPED_RESOURCE":
                status_writer.write("SKIPPED_RESOURCE", reason=preflight["reason"], run_id=run_id)
                return {"status": "SKIPPED_RESOURCE", "reason": preflight["reason"], "artifacts": str(layout.run_dir)}
            validate_config(inventory_path, scenario_path)
            commands.append(["validate", str(inventory_path), str(scenario_path)], 0)
            plan = build_cluster_plan(inventory_path, scenario_path)
            layout.cluster_plan_path.write_text(json.dumps(plan["cluster_plan"], sort_keys=True, indent=2) + "\n", encoding="utf-8")
            commands.append(["plan", str(inventory_path), str(scenario_path)], 0)
            node_ids = [node["node_id"] for node in plan["cluster_plan"]["nodes"]]
            nodehost.prepare(run_id)
            nodehost.start(run_id, node_ids)
            events.append("node", action="nodehost_started", count=len(node_ids))
            cli = FakeValkeyCli()
            ClusterCreator(cli, events).create(plan["cluster_plan"])
            check = ClusterChecker().check(cli.cluster_info())
            if check["status"] != "OK":
                events.append("assertion", action="cluster_check", status="FAIL", reason=check["reason"])
                status_writer.write("FAIL", reason=check["reason"], run_id=run_id)
                return {"status": "FAIL", "reason": check["reason"], "artifacts": str(layout.run_dir)}
            events.append("assertion", action="cluster_check", status="PASS")
            status_writer.write("PASS", run_id=run_id, backend=backend)
            return {"status": "PASS", "artifacts": str(layout.run_dir), "cluster_check": check}
        except Exception as exc:
            events.append("run", action="failure", status="FAIL", reason=str(exc))
            status_writer.write("FAIL", reason=str(exc), run_id=run_id)
            return {"status": "FAIL", "reason": str(exc), "artifacts": str(layout.run_dir)}
        finally:
            nodehost.cleanup(run_id)
            events.append("node", action="cleanup", run_id=run_id)
