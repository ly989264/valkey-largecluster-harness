import tempfile
import unittest
from pathlib import Path

from harness.artifacts import ArtifactLayout
from harness.command_log import CommandLogWriter, read_command_log
from harness.events import EVENT_TYPES, EventRecorder, replay_events
from harness.status import RunStatusWriter, read_status


class ArtifactsEventsP06Test(unittest.TestCase):
    def test_artifact_layout_is_isolated_per_run_id(self):
        with tempfile.TemporaryDirectory() as td:
            one = ArtifactLayout.create(td, "run-one")
            two = ArtifactLayout.create(td, "run-two")
            self.assertNotEqual(one.run_dir, two.run_dir)
            self.assertTrue(one.run_dir.exists())
            self.assertTrue(two.run_dir.exists())
            self.assertEqual(one.events_path, Path(td) / "run-one" / "events.jsonl")

    def test_events_jsonl_appends_and_replays(self):
        with tempfile.TemporaryDirectory() as td:
            layout = ArtifactLayout.create(td, "run")
            recorder = EventRecorder(layout.events_path)
            recorder.append("run", status="STARTED")
            recorder.append("cluster", state="ok")
            records = replay_events(layout.events_path)
            self.assertEqual(len(records), 2)
            self.assertTrue(all(item["valid"] for item in records))
            self.assertEqual(records[1]["event"]["event_type"], "cluster")

    def test_corrupted_event_line_is_invalid_evidence(self):
        with tempfile.TemporaryDirectory() as td:
            layout = ArtifactLayout.create(td, "run")
            layout.events_path.write_text('{"event_type":"run"}\nnot-json\n', encoding="utf-8")
            records = replay_events(layout.events_path)
            self.assertTrue(records[0]["valid"])
            self.assertFalse(records[1]["valid"])
            self.assertIn("reason", records[1])

    def test_status_and_command_log_round_trip(self):
        with tempfile.TemporaryDirectory() as td:
            layout = ArtifactLayout.create(td, "run")
            RunStatusWriter(layout.status_path).write("PASS", run_id="run")
            CommandLogWriter(layout.command_log_path).append(["echo", "ok"], 0, phase="test")
            self.assertEqual(read_status(layout.status_path)["status"], "PASS")
            self.assertEqual(read_command_log(layout.command_log_path)[0]["command"], ["echo", "ok"])

    def test_event_taxonomy_contains_required_domains(self):
        self.assertEqual(set(EVENT_TYPES), {"run", "command", "node", "cluster", "fault", "failover", "metric", "assertion"})


if __name__ == "__main__":
    unittest.main()
