import tempfile
from pathlib import Path
import unittest

import batch_analysis
import batch_history
import database
import step28_report_comparison
from test_helpers import make_test_bundle


class Step28BatchFixture(unittest.TestCase):

    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        root = Path(self.temp.name)
        self.db = root / "step28.db"

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

        batch1 = batch_analysis.run_batch_analysis(
            self.db,
            "recipient",
            "RECIP-001",
            save=False,
        )
        self.batch1 = batch_history.persist_batch_with_runs(
            self.db, batch1
        )["batch_id"]

        batch2 = batch_analysis.run_batch_analysis(
            self.db,
            "recipient",
            "RECIP-001",
            candidate_external_ids=["DONOR-001"],
            save=False,
        )
        self.batch2 = batch_history.persist_batch_with_runs(
            self.db, batch2
        )["batch_id"]

    def tearDown(self):
        self.temp.cleanup()


class TestStep28BatchComparison(Step28BatchFixture):

    def test_build_batch_comparison(self):
        result = (
            step28_report_comparison.build_persistent_batch_comparison(
                self.db, self.batch1, self.batch2
            )
        )
        self.assertEqual(result["mode"], "batches")

    def test_batch_ids(self):
        result = (
            step28_report_comparison.build_persistent_batch_comparison(
                self.db, self.batch1, self.batch2
            )
        )
        self.assertEqual(result["left"]["batch_id"], self.batch1)
        self.assertEqual(result["right"]["batch_id"], self.batch2)

    def test_common_candidates(self):
        result = (
            step28_report_comparison.build_persistent_batch_comparison(
                self.db, self.batch1, self.batch2
            )
        )
        self.assertEqual(result["common_candidates"], ["DONOR-001"])

    def test_only_left_candidate(self):
        result = (
            step28_report_comparison.build_persistent_batch_comparison(
                self.db, self.batch1, self.batch2
            )
        )
        self.assertEqual(
            result["only_left_candidates"],
            ["DONOR-002"],
        )

    def test_only_right_empty(self):
        result = (
            step28_report_comparison.build_persistent_batch_comparison(
                self.db, self.batch1, self.batch2
            )
        )
        self.assertEqual(result["only_right_candidates"], [])

    def test_membership_changed(self):
        result = (
            step28_report_comparison.build_persistent_batch_comparison(
                self.db, self.batch1, self.batch2
            )
        )
        self.assertTrue(
            result["context_changes"]["candidate_membership_changed"]
        )

    def test_common_pair_delta_count(self):
        result = (
            step28_report_comparison.build_persistent_batch_comparison(
                self.db, self.batch1, self.batch2
            )
        )
        self.assertEqual(len(result["pair_delta_rows"]), 1)

    def test_locus_filter(self):
        result = (
            step28_report_comparison.build_persistent_batch_comparison(
                self.db, self.batch1, self.batch2,
                loci=["A", "DRB1"],
            )
        )
        self.assertEqual(result["loci"], ["A", "DRB1"])
        self.assertEqual(len(result["locus_delta_rows"]), 2)

    def test_same_batch_rejected(self):
        with self.assertRaises(
            step28_report_comparison.ReportComparisonError
        ):
            step28_report_comparison.build_persistent_batch_comparison(
                self.db, self.batch1, self.batch1
            )

    def test_render_batch(self):
        result = (
            step28_report_comparison.build_persistent_batch_comparison(
                self.db, self.batch1, self.batch2
            )
        )
        text = step28_report_comparison.render_comparison(result)
        self.assertIn("Mode: BATCHES", text)
        self.assertIn("CANDIDATE MEMBERSHIP", text)
        self.assertIn("CONTEXT CHANGES", text)

    def test_no_pyard_recalc(self):
        result = (
            step28_report_comparison.build_persistent_batch_comparison(
                self.db, self.batch1, self.batch2
            )
        )
        self.assertFalse(
            result["provenance"]["pyard_recalculated_by_step28"]
        )


if __name__ == "__main__":
    unittest.main()
