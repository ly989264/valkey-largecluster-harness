import hashlib
import json
import subprocess
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
EXPECTED_MANIFEST_SHA = "d34c3ae82d24fdfa64baf19779a405194f3c2bd9e559951d6b7350fcad478f30"


def run_cmd(*args):
    return subprocess.run(args, cwd=ROOT, text=True, capture_output=True)


class P00LoopControlTest(unittest.TestCase):
    def test_manifest_is_canonical_and_contiguous(self):
        path = ROOT / "codex" / "phase_manifest.json"
        self.assertEqual(hashlib.sha256(path.read_bytes()).hexdigest(), EXPECTED_MANIFEST_SHA)
        data = json.loads(path.read_text(encoding="utf-8"))
        self.assertEqual(data["version"], 2)
        self.assertEqual(data["phase_ids"], [f"P{i:02d}" for i in range(17)])
        p00 = next(p for p in data["phases"] if p["id"] == "P00")
        self.assertIn("scripts/project_quality_gate.py", p00["allowed_paths"])
        self.assertIn("tests/test_p00_loop_control.py", p00["allowed_paths"])
        self.assertFalse(any("phase_gate.py check" in c for c in p00["pre_gate_commands"]))

    def test_phase_cards_exist(self):
        for i in range(17):
            card = ROOT / "codex" / "phase_cards" / f"P{i:02d}.md"
            self.assertTrue(card.exists(), card)
            self.assertIn("## Allowed Paths", card.read_text(encoding="utf-8"))

    def test_next_and_gate_entrypoints_emit_json(self):
        for cmd in [
            [sys.executable, "scripts/codex_next.py", "status", "--json"],
            [sys.executable, "scripts/codex_next.py", "next", "--json"],
            [sys.executable, "scripts/phase_gate.py", "list", "--json"],
            [sys.executable, "scripts/diff_guard.py", "allowed-files", "--phase", "P00", "--json"],
        ]:
            cp = run_cmd(*cmd)
            self.assertEqual(cp.returncode, 0, cp.stderr + cp.stdout)
            payload = json.loads(cp.stdout)
            self.assertIn("status", payload)

    def test_pass_command_reruns_phase_gate(self):
        source = (ROOT / "scripts" / "codex_next.py").read_text(encoding="utf-8")
        self.assertIn("scripts/phase_gate.py", source)
        self.assertIn("check", source)
        self.assertNotIn("--force", source)


if __name__ == "__main__":
    unittest.main()
