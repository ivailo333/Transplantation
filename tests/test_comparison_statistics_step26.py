import copy
import tempfile
from pathlib import Path
import unittest

import database
import comparison_statistics
import mismatch_summary

from test_helpers import make_test_bundle


def changed_bundle(*loci):
    bundle = copy.deepcopy(make_test_bundle())

    for representation in ("canonical", "lgx", "G", "P"):
        for locus in loci:
            bundle[representation][locus] = [
                f"{locus}*90:01-{representation}",
                f"{locus}*91:01-{representation}",
            ]

    for locus in loci:
        bundle["raw"][locus] = [
            f"{locus}*90:01",
            f"{locus}*91:01",
        ]

    return bundle


def empty_summary():
    return {
        "schema": mismatch_summary.SUMMARY_SCHEMA,
        "source": "TEST",
        "batch_id": None,
        "direction": "recipient",
        "anchor_external_id": "RECIP-EMPTY",
        "anchor_typing_id": 1,
        "imgthla_version": "3650",
        "level": "lgx",
        "level_label": "LGX",
        "loci": ["A", "DRB1"],
        "pair_count": 0,
        "rows": [],
    }


class Step26Fixture(unittest.TestCase):

    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        root = Path(self.temp.name)
        self.db = root / "step26.db"
        self.out = root / "exports"

        database.initialize_database(self.db)

        database.save_subject_typing(
            self.db,
            "DONOR-FULL",
            "DONOR",
            "3650",
            make_test_bundle(),
        )
        database.save_subject_typing(
            self.db,
            "DONOR-A",
            "DONOR",
            "3650",
            changed_bundle("A"),
        )
        database.save_subject_typing(
            self.db,
            "DONOR-AB",
            "DONOR",
            "3650",
            changed_bundle("A", "B"),
        )
        database.save_subject_typing(
            self.db,
            "RECIP-001",
            "RECIPIENT",
            "3650",
            make_test_bundle(),
        )

    def tearDown(self):
        self.temp.cleanup()


class TestStep26NumericStatistics(unittest.TestCase):

    def test_multiple_values(self):
        stats = comparison_statistics.calculate_numeric_statistics(
            [1, 3, 5]
        )
        self.assertEqual(stats["count"], 3)
        self.assertEqual(stats["sum"], 9)
        self.assertEqual(stats["min"], 1)
        self.assertEqual(stats["max"], 5)
        self.assertEqual(stats["mean"], 3.0)
        self.assertEqual(stats["median"], 3)

    def test_even_median(self):
        stats = comparison_statistics.calculate_numeric_statistics(
            [1, 3]
        )
        self.assertEqual(stats["median"], 2.0)

    def test_single_value(self):
        stats = comparison_statistics.calculate_numeric_statistics(
            [7]
        )
        self.assertEqual(stats["count"], 1)
        self.assertEqual(stats["sum"], 7)
        self.assertEqual(stats["min"], 7)
        self.assertEqual(stats["max"], 7)
        self.assertEqual(stats["mean"], 7.0)
        self.assertEqual(stats["median"], 7)

    def test_empty_values(self):
        stats = comparison_statistics.calculate_numeric_statistics([])
        self.assertEqual(stats["count"], 0)
        self.assertEqual(stats["sum"], 0)
        self.assertIsNone(stats["min"])
        self.assertIsNone(stats["max"])
        self.assertIsNone(stats["mean"])
        self.assertIsNone(stats["median"])

    def test_non_numeric_rejected(self):
        with self.assertRaises(
            comparison_statistics.ComparisonStatisticsError
        ):
            comparison_statistics.calculate_numeric_statistics(
                [1, "x"]
            )


class TestStep26Distribution(unittest.TestCase):

    def test_distribution_percentages(self):
        result = comparison_statistics.calculate_class_distribution(
            [
                mismatch_summary.CLASS_COMPLETE,
                mismatch_summary.CLASS_PARTIAL,
                mismatch_summary.CLASS_PARTIAL,
                mismatch_summary.CLASS_NONE,
            ]
        )
        self.assertEqual(
            result[mismatch_summary.CLASS_COMPLETE]["count"],
            1,
        )
        self.assertEqual(
            result[mismatch_summary.CLASS_PARTIAL]["percentage"],
            50.0,
        )
        self.assertEqual(
            result[mismatch_summary.CLASS_NONE]["percentage"],
            25.0,
        )

    def test_empty_distribution(self):
        result = comparison_statistics.calculate_class_distribution([])
        for label in mismatch_summary.CLASSIFICATIONS:
            self.assertEqual(result[label]["count"], 0)
            self.assertEqual(result[label]["percentage"], 0.0)

    def test_unknown_label_rejected(self):
        with self.assertRaises(
            comparison_statistics.ComparisonStatisticsError
        ):
            comparison_statistics.calculate_class_distribution(
                ["UNKNOWN"]
            )


class TestStep26BuildStatistics(Step26Fixture):

    def test_live_pair_count(self):
        stats = comparison_statistics.build_live_statistics(
            self.db,
            "recipient",
            "RECIP-001",
        )
        self.assertEqual(stats["pair_count"], 3)

    def test_default_level_is_lgx(self):
        stats = comparison_statistics.build_live_statistics(
            self.db,
            "recipient",
            "RECIP-001",
        )
        self.assertEqual(stats["level"], "lgx")
        self.assertEqual(stats["level_label"], "LGX")

    def test_candidate_filter_single_pair(self):
        stats = comparison_statistics.build_live_statistics(
            self.db,
            "recipient",
            "RECIP-001",
            candidate_external_ids=["DONOR-FULL"],
        )
        self.assertEqual(stats["pair_count"], 1)
        self.assertEqual(
            stats["pair_total_statistics"]["shared_count"]["count"],
            1,
        )

    def test_locus_filter_changes_total_basis(self):
        stats = comparison_statistics.build_live_statistics(
            self.db,
            "recipient",
            "RECIP-001",
            candidate_external_ids=["DONOR-A"],
            loci=["A"],
        )
        shared = stats["pair_total_statistics"]["shared_count"]
        donor_only = stats["pair_total_statistics"]["donor_only_count"]
        self.assertEqual(shared["sum"], 0)
        self.assertEqual(donor_only["sum"], 2)

    def test_all_loci_present(self):
        stats = comparison_statistics.build_live_statistics(
            self.db,
            "recipient",
            "RECIP-001",
        )
        self.assertEqual(
            stats["loci"],
            ["A", "B", "C", "DRB1", "DQB1", "DPB1"],
        )

    def test_locus_pair_count(self):
        stats = comparison_statistics.build_live_statistics(
            self.db,
            "recipient",
            "RECIP-001",
            loci=["A", "DRB1"],
        )
        self.assertEqual(
            stats["locus_statistics"]["A"]["pair_count"],
            3,
        )
        self.assertEqual(
            stats["locus_statistics"]["DRB1"]["pair_count"],
            3,
        )

    def test_pair_distribution_sums_to_pair_count(self):
        stats = comparison_statistics.build_live_statistics(
            self.db,
            "recipient",
            "RECIP-001",
        )
        total = sum(
            item["count"]
            for item in stats[
                "pair_classification_distribution"
            ].values()
        )
        self.assertEqual(total, stats["pair_count"])

    def test_locus_distribution_sums_to_pair_times_loci(self):
        stats = comparison_statistics.build_live_statistics(
            self.db,
            "recipient",
            "RECIP-001",
            loci=["A", "B"],
        )
        total = sum(
            item["count"]
            for item in stats[
                "locus_classification_distribution"
            ].values()
        )
        self.assertEqual(
            total,
            stats["pair_count"] * len(stats["loci"]),
        )

    def test_details_off_by_default(self):
        stats = comparison_statistics.build_live_statistics(
            self.db,
            "recipient",
            "RECIP-001",
        )
        self.assertFalse(stats["details_included"])
        self.assertEqual(stats["details"], [])

    def test_details_on(self):
        stats = comparison_statistics.build_live_statistics(
            self.db,
            "recipient",
            "RECIP-001",
            details=True,
        )
        self.assertTrue(stats["details_included"])
        self.assertEqual(len(stats["details"]), 3)

    def test_sort_does_not_change_aggregate_numbers(self):
        unsorted_stats = comparison_statistics.build_live_statistics(
            self.db,
            "recipient",
            "RECIP-001",
        )
        sorted_stats = comparison_statistics.build_live_statistics(
            self.db,
            "recipient",
            "RECIP-001",
            sort_by="donor-only",
        )
        self.assertEqual(
            unsorted_stats["pair_total_statistics"],
            sorted_stats["pair_total_statistics"],
        )
        self.assertEqual(
            unsorted_stats["pair_classification_distribution"],
            sorted_stats["pair_classification_distribution"],
        )

    def test_no_clinical_score(self):
        stats = comparison_statistics.build_live_statistics(
            self.db,
            "recipient",
            "RECIP-001",
        )
        self.assertFalse(stats["clinical_score"])
        self.assertFalse(stats["recalculated_py_ard"])

    def test_empty_summary_is_safe(self):
        stats = comparison_statistics.build_statistics_from_summary(
            empty_summary()
        )
        self.assertEqual(stats["pair_count"], 0)
        self.assertEqual(
            stats["pair_total_statistics"]["shared_count"]["sum"],
            0,
        )
        self.assertIsNone(
            stats["pair_total_statistics"]["shared_count"]["mean"]
        )
        for label in mismatch_summary.CLASSIFICATIONS:
            self.assertEqual(
                stats["pair_classification_distribution"][label][
                    "percentage"
                ],
                0.0,
            )


class TestStep26RenderAndExport(Step26Fixture):

    def test_render_has_sections(self):
        stats = comparison_statistics.build_live_statistics(
            self.db,
            "recipient",
            "RECIP-001",
        )
        text = comparison_statistics.render_statistics(stats)
        self.assertIn("STEP 26", text)
        self.assertIn(
            "PAIR CLASSIFICATION DISTRIBUTION",
            text,
        )
        self.assertIn("LOCUS STATISTICS", text)
        self.assertIn("NON-CLINICAL", text)

    def test_render_details(self):
        stats = comparison_statistics.build_live_statistics(
            self.db,
            "recipient",
            "RECIP-001",
            details=True,
        )
        text = comparison_statistics.render_statistics(stats)
        self.assertIn("PAIR DETAILS", text)
        self.assertIn("DONOR-FULL", text)

    def test_json_export(self):
        stats = comparison_statistics.build_live_statistics(
            self.db,
            "recipient",
            "RECIP-001",
        )
        info = comparison_statistics.export_statistics(
            stats,
            output_dir=self.out,
            export_format="json",
        )
        self.assertTrue(info["json_path"].exists())

    def test_csv_export_total_plus_loci(self):
        stats = comparison_statistics.build_live_statistics(
            self.db,
            "recipient",
            "RECIP-001",
            loci=["A", "DRB1"],
        )
        info = comparison_statistics.export_statistics(
            stats,
            output_dir=self.out,
            export_format="csv",
        )
        lines = info["csv_path"].read_text(
            encoding="utf-8"
        ).splitlines()
        self.assertEqual(len(lines), 1 + 1 + 2)

    def test_both_export(self):
        stats = comparison_statistics.build_live_statistics(
            self.db,
            "recipient",
            "RECIP-001",
        )
        info = comparison_statistics.export_statistics(
            stats,
            output_dir=self.out,
            export_format="both",
        )
        self.assertTrue(info["json_path"].exists())
        self.assertTrue(info["csv_path"].exists())

    def test_overwrite_protection(self):
        stats = comparison_statistics.build_live_statistics(
            self.db,
            "recipient",
            "RECIP-001",
        )
        comparison_statistics.export_statistics(
            stats,
            output_dir=self.out,
            export_format="json",
        )
        with self.assertRaises(
            comparison_statistics.ComparisonStatisticsExportExistsError
        ):
            comparison_statistics.export_statistics(
                stats,
                output_dir=self.out,
                export_format="json",
            )


if __name__ == "__main__":
    unittest.main()
