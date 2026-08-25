import copy
import tempfile
from pathlib import Path
import unittest

import database
import step27_reporting
import step28_report_comparison

from test_helpers import make_test_bundle


class Step28LiveFixture(unittest.TestCase):

    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        root = Path(self.temp.name)
        self.db = root / "step28.db"
        self.out = root / "exports"

        database.initialize_database(self.db)

        database.save_subject_typing(
            self.db, "DONOR-001", "DONOR", "3650", make_test_bundle()
        )
        database.save_subject_typing(
            self.db, "DONOR-002", "DONOR", "3650", make_test_bundle()
        )
        database.save_subject_typing(
            self.db, "RECIP-001", "RECIPIENT", "3650", make_test_bundle()
        )

    def tearDown(self):
        self.temp.cleanup()


class TestStep28NormalizeLevels(unittest.TestCase):

    def test_default_all_levels(self):
        self.assertEqual(
            step28_report_comparison.normalize_levels(None),
            ["canonical", "lgx", "G", "P"],
        )

    def test_case_normalization(self):
        self.assertEqual(
            step28_report_comparison.normalize_levels(["LGX", "g"]),
            ["lgx", "G"],
        )

    def test_duplicates_removed(self):
        self.assertEqual(
            step28_report_comparison.normalize_levels(
                ["lgx", "LGX", "G"]
            ),
            ["lgx", "G"],
        )

    def test_one_level_rejected(self):
        with self.assertRaises(
            step28_report_comparison.ReportComparisonError
        ):
            step28_report_comparison.normalize_levels(["lgx"])


class TestStep28LevelComparison(Step28LiveFixture):

    def test_build_default_levels(self):
        result = step28_report_comparison.build_live_level_comparison(
            self.db,
            "recipient",
            "RECIP-001",
        )
        self.assertEqual(result["mode"], "levels")
        self.assertEqual(
            result["level_labels"],
            ["CANONICAL", "LGX", "G", "P"],
        )

    def test_schema_and_step(self):
        result = step28_report_comparison.build_live_level_comparison(
            self.db, "recipient", "RECIP-001",
            levels=["canonical", "lgx"],
        )
        self.assertEqual(
            result["schema"],
            step28_report_comparison.COMPARISON_SCHEMA,
        )
        self.assertEqual(result["step"], 28)
        self.assertFalse(result["clinical"])

    def test_two_level_comparison(self):
        result = step28_report_comparison.build_live_level_comparison(
            self.db, "recipient", "RECIP-001",
            levels=["canonical", "lgx"],
        )
        self.assertEqual(len(result["level_rows"]), 2)
        self.assertEqual(result["reference_level"], "canonical")

    def test_pair_count(self):
        result = step28_report_comparison.build_live_level_comparison(
            self.db, "recipient", "RECIP-001",
            levels=["lgx", "G"],
        )
        self.assertEqual(result["pair_count"], 2)

    def test_candidate_filter(self):
        result = step28_report_comparison.build_live_level_comparison(
            self.db, "recipient", "RECIP-001",
            candidate_external_ids=["DONOR-001"],
            levels=["lgx", "G"],
        )
        self.assertEqual(result["pair_count"], 1)

    def test_locus_filter(self):
        result = step28_report_comparison.build_live_level_comparison(
            self.db, "recipient", "RECIP-001",
            levels=["lgx", "G"],
            loci=["DRB1"],
        )
        self.assertEqual(result["loci"], ["DRB1"])
        self.assertEqual(len(result["locus_delta_rows"]), 1)

    def test_pair_delta_count(self):
        result = step28_report_comparison.build_live_level_comparison(
            self.db, "recipient", "RECIP-001",
            levels=["canonical", "lgx", "G"],
        )
        self.assertEqual(
            len(result["pair_delta_rows"]),
            2 * 2,
        )

    def test_locus_delta_count(self):
        result = step28_report_comparison.build_live_level_comparison(
            self.db, "recipient", "RECIP-001",
            levels=["canonical", "lgx", "G"],
            loci=["A", "DRB1"],
        )
        self.assertEqual(
            len(result["locus_delta_rows"]),
            2 * 2,
        )

    def test_stability_candidate_count(self):
        result = step28_report_comparison.build_live_level_comparison(
            self.db, "recipient", "RECIP-001",
            levels=["lgx", "G"],
        )
        self.assertEqual(
            result["stability"]["candidate_count"],
            2,
        )

    def test_no_pyard_by_step28(self):
        result = step28_report_comparison.build_live_level_comparison(
            self.db, "recipient", "RECIP-001",
            levels=["lgx", "G"],
        )
        self.assertFalse(
            result["provenance"]["pyard_recalculated_by_step28"]
        )
        self.assertFalse(
            result["provenance"]["analysis_run_created_by_step28"]
        )

    def test_donor_direction(self):
        result = step28_report_comparison.build_live_level_comparison(
            self.db, "donor", "DONOR-001",
            levels=["lgx", "G"],
        )
        self.assertEqual(result["direction"], "donor")
        self.assertEqual(result["pair_count"], 1)

    def test_render_contains_nonclinical_boundary(self):
        result = step28_report_comparison.build_live_level_comparison(
            self.db, "recipient", "RECIP-001",
            levels=["lgx", "G"],
        )
        text = step28_report_comparison.render_comparison(result)
        self.assertIn("STEP 28", text)
        self.assertIn("Mode: LEVELS", text)
        self.assertIn("PAIR DELTAS", text)
        self.assertIn("NON-CLINICAL", text)

    def test_scope_mismatch_rejected(self):
        a = step27_reporting.build_live_report(
            self.db, "recipient", "RECIP-001", level="lgx"
        )
        b = step27_reporting.build_live_report(
            self.db, "recipient", "RECIP-001", level="G"
        )
        b = copy.deepcopy(b)
        b["anchor"]["external_id"] = "OTHER"
        with self.assertRaises(
            step28_report_comparison.ReportComparisonError
        ):
            step28_report_comparison.build_level_comparison_from_reports(
                [a, b]
            )


class TestStep28Export(Step28LiveFixture):

    def test_json_export(self):
        result = step28_report_comparison.build_live_level_comparison(
            self.db, "recipient", "RECIP-001",
            levels=["lgx", "G"],
        )
        info = step28_report_comparison.export_comparison(
            result, output_dir=self.out, export_format="json"
        )
        self.assertTrue(info["json_path"].exists())

    def test_csv_export(self):
        result = step28_report_comparison.build_live_level_comparison(
            self.db, "recipient", "RECIP-001",
            levels=["lgx", "G"],
        )
        info = step28_report_comparison.export_comparison(
            result, output_dir=self.out, export_format="csv"
        )
        self.assertTrue(info["csv_path"].exists())

    def test_both_export(self):
        result = step28_report_comparison.build_live_level_comparison(
            self.db, "recipient", "RECIP-001",
            levels=["lgx", "G"],
        )
        info = step28_report_comparison.export_comparison(
            result, output_dir=self.out, export_format="both"
        )
        self.assertTrue(info["json_path"].exists())
        self.assertTrue(info["csv_path"].exists())


    def test_all_export(self):
        result = step28_report_comparison.build_live_level_comparison(
            self.db, "recipient", "RECIP-001",
            levels=["lgx", "G"],
        )
        info = step28_report_comparison.export_comparison(
            result, output_dir=self.out, export_format="all"
        )
        self.assertTrue(info["json_path"].exists())
        self.assertTrue(info["csv_path"].exists())
        self.assertTrue(info["html_path"].exists())
        self.assertEqual(info["format"], "ALL")

    def test_html_export(self):
        result = step28_report_comparison.build_live_level_comparison(
            self.db, "recipient", "RECIP-001",
            levels=["lgx", "G"],
        )
        info = step28_report_comparison.export_comparison(
            result, output_dir=self.out, export_format="html"
        )
        self.assertTrue(info["html_path"].exists())
        html = info["html_path"].read_text(encoding="utf-8")
        self.assertIn("<html", html)
        self.assertIn("STEP 28 HLA Report Comparison", html)
        self.assertIn("NON-CLINICAL", html)

    def test_overwrite_protection(self):
        result = step28_report_comparison.build_live_level_comparison(
            self.db, "recipient", "RECIP-001",
            levels=["lgx", "G"],
        )
        step28_report_comparison.export_comparison(
            result, output_dir=self.out, export_format="json"
        )
        with self.assertRaises(
            step28_report_comparison.ReportComparisonExportExistsError
        ):
            step28_report_comparison.export_comparison(
                result, output_dir=self.out, export_format="json"
            )

    def test_csv_has_level_and_delta_records(self):
        result = step28_report_comparison.build_live_level_comparison(
            self.db, "recipient", "RECIP-001",
            levels=["lgx", "G"],
        )
        info = step28_report_comparison.export_comparison(
            result, output_dir=self.out, export_format="csv"
        )
        text = info["csv_path"].read_text(encoding="utf-8")
        self.assertIn("LEVEL", text)
        self.assertIn("PAIR_DELTA", text)
        self.assertIn("LOCUS_DELTA", text)


if __name__ == "__main__":
    unittest.main()
