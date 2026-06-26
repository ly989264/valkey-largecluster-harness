from __future__ import annotations

from pathlib import Path

from harness.report.generator import generate_report


def test_report_generation_from_fixture(tmp_path: Path) -> None:
    path = generate_report(
        run_id="fixture-minimal",
        artifacts_dir="tests/fixtures/minimal_run",
        reports_root=tmp_path,
    )

    report = path.read_text(encoding="utf-8")
    assert "## Executive Summary" in report
    assert "## Virtual AZ Topology" in report
    assert "+ virtual AZ vaz-a" in report
    assert "MISSING" in report
    assert "## Artifact Index" in report
