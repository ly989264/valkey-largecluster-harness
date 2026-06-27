import unittest

from harness.config import load_document, load_scenario
from harness.project_quality import run_project_quality
from harness.report_builder import REQUIRED_REPORT_SECTIONS, build_report, load_scale_ladder
from harness.report_models import ReportItem


class ReportAndScaleP16Test(unittest.TestCase):
    def test_scale_ladder_is_configuration_driven(self):
        ladder = load_scale_ladder("scenarios")
        by_id = {item["scenario_id"]: item for item in ladder}
        self.assertEqual(by_id["scale-300"]["total_nodes"], 300)
        self.assertEqual(by_id["scale-500"]["total_nodes"], 500)
        self.assertEqual(by_id["scale-1000"]["total_nodes"], 1000)
        self.assertEqual(by_id["scale-2000-empty"]["total_nodes"], 2000)
        load_scenario("scenarios/scale-2000-empty.yaml")

    def test_scale_2000_empty_does_not_claim_production_validation(self):
        data = load_document("scenarios/scale-2000-empty.yaml")
        not_validated = set(data["does_not_validate"])
        self.assertEqual(data["validation_profile"], "best-effort-empty-node-smoke")
        self.assertIn("throughput", not_validated)
        self.assertIn("production_latency", not_validated)
        self.assertIn("production_rto", not_validated)
        self.assertIn("physical_3az_durability", not_validated)

    def test_report_sections_and_status_vocabulary(self):
        report = build_report("artifacts", "scenarios")
        section_names = [section.name for section in report.sections]
        self.assertEqual(section_names, list(REQUIRED_REPORT_SECTIONS))
        counts = report.status_counts()
        for status in ("MISSING", "INCONCLUSIVE", "NOT_VALIDATED", "SKIPPED_RESOURCE", "FAIL"):
            self.assertGreater(counts[status], 0)
        self.assertTrue(any(item.name == "report status vocabulary" for section in report.sections for item in section.items))

    def test_report_item_rejects_unknown_status(self):
        with self.assertRaises(ValueError):
            ReportItem("bad", "UNKNOWN")

    def test_project_quality_gate_checks_current_tree_without_recursive_test_run(self):
        result = run_project_quality(candidate_phase="P16", run_tests=False)
        self.assertEqual(result["status"], "OK")
        self.assertTrue(all(check["ok"] for check in result["checks"]))


if __name__ == "__main__":
    unittest.main()
