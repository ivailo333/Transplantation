import copy
import tempfile
from pathlib import Path
import unittest

import comparison_statistics
import database
import hla_matrix
import mismatch_summary
import step27_reporting

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


class Step27Fixture(unittest.TestCase):

    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        root = Path(self.temp.name)
        self.db = root / "step27.db"
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
            "RECIP-001",
            "RECIPIENT",
            "3650",
            make_test_bundle(),
        )

    def tearDown(self):
        self.temp.cleanup()

    def components(self, *, loci=None):
        matrix = hla_matrix.build_live_matrix(
            self.db,
            "recipient",
            "RECIP-001",
            loci=loci,
        )
        summary = mismatch_summary.build_summary_from_matrix(
            matrix
        )
        stats = comparison_statistics.build_statistics_from_summary(
            summary,
            details=True,
        )
        return matrix, summary, stats


class TestStep27Build(Step27Fixture):

    def test_build_live_report(self):
        report = step27_reporting.build_live_report(
            self.db,
            "recipient",
            "RECIP-001",
        )
        self.assertEqual(
            report["schema"],
            step27_reporting.REPORT_SCHEMA,
        )
        self.assertEqual(report["step"], 27)
        self.assertFalse(report["clinical"])

    def test_pair_count(self):
        report = step27_reporting.build_live_report(
            self.db,
            "recipient",
            "RECIP-001",
        )
        self.assertEqual(report["pair_count"], 2)

    def test_pair_rows(self):
        report = step27_reporting.build_live_report(
            self.db,
            "recipient",
            "RECIP-001",
        )
        self.assertEqual(len(report["pair_rows"]), 2)

    def test_locus_rows(self):
        report = step27_reporting.build_live_report(
            self.db,
            "recipient",
            "RECIP-001",
        )
        self.assertEqual(len(report["locus_rows"]), 6)

    def test_candidate_filter(self):
        report = step27_reporting.build_live_report(
            self.db,
            "recipient",
            "RECIP-001",
            candidate_external_ids=["DONOR-FULL"],
        )
        self.assertEqual(report["pair_count"], 1)
        self.assertEqual(
            report["pair_rows"][0]["candidate_external_id"],
            "DONOR-FULL",
        )

    def test_locus_filter(self):
        report = step27_reporting.build_live_report(
            self.db,
            "recipient",
            "RECIP-001",
            loci=["A", "DRB1"],
        )
        self.assertEqual(
            report["hla_reference"]["loci"],
            ["A", "DRB1"],
        )
        self.assertEqual(len(report["locus_rows"]), 2)

    def test_level_filter(self):
        report = step27_reporting.build_live_report(
            self.db,
            "recipient",
            "RECIP-001",
            level="G",
        )
        self.assertEqual(
            report["hla_reference"]["level"],
            "G",
        )

    def test_provenance_flags(self):
        report = step27_reporting.build_live_report(
            self.db,
            "recipient",
            "RECIP-001",
        )
        self.assertTrue(
            report["provenance"]["scope_validated"]
        )
        self.assertTrue(
            report["provenance"]["aggregates_validated"]
        )
        self.assertFalse(
            report["provenance"]["pyard_recalculated"]
        )
        self.assertFalse(
            report["provenance"][
                "analysis_run_created_by_step27"
            ]
        )

    def test_sorting_preserved_as_software_order(self):
        report = step27_reporting.build_live_report(
            self.db,
            "recipient",
            "RECIP-001",
            sort_by="donor-only",
        )
        self.assertEqual(
            report["software_ordering"]["metric"],
            "donor-only",
        )

    def test_render_contains_sections(self):
        report = step27_reporting.build_live_report(
            self.db,
            "recipient",
            "RECIP-001",
        )
        text = step27_reporting.render_report(report)
        self.assertIn("STEP 27", text)
        self.assertIn("PAIR OVERVIEW", text)
        self.assertIn("LOCUS OVERVIEW", text)
        self.assertIn("REPORT PROVENANCE / INTEGRITY", text)
        self.assertIn("NON-CLINICAL", text)


class TestStep27Consistency(Step27Fixture):

    def test_valid_components_pass(self):
        matrix, summary, stats = self.components()
        step27_reporting.validate_report_inputs(
            matrix,
            summary,
            stats,
        )

    def test_mixed_level_rejected(self):
        matrix, summary, stats = self.components()
        stats = copy.deepcopy(stats)
        stats["level"] = "G"
        with self.assertRaises(step27_reporting.ReportingError):
            step27_reporting.validate_report_inputs(
                matrix,
                summary,
                stats,
            )

    def test_mixed_loci_rejected(self):
        matrix, summary, stats = self.components()
        stats = copy.deepcopy(stats)
        stats["loci"] = ["A"]
        with self.assertRaises(step27_reporting.ReportingError):
            step27_reporting.validate_report_inputs(
                matrix,
                summary,
                stats,
            )

    def test_mixed_anchor_rejected(self):
        matrix, summary, stats = self.components()
        summary = copy.deepcopy(summary)
        summary["anchor_external_id"] = "OTHER"
        with self.assertRaises(step27_reporting.ReportingError):
            step27_reporting.validate_report_inputs(
                matrix,
                summary,
                stats,
            )

    def test_mixed_source_rejected(self):
        matrix, summary, stats = self.components()
        stats = copy.deepcopy(stats)
        stats["source"] = "OTHER"
        with self.assertRaises(step27_reporting.ReportingError):
            step27_reporting.validate_report_inputs(
                matrix,
                summary,
                stats,
            )

    def test_pair_total_mismatch_rejected(self):
        matrix, summary, stats = self.components()
        summary = copy.deepcopy(summary)
        summary["rows"][0]["totals"]["shared_count"] += 1
        with self.assertRaises(step27_reporting.ReportingError):
            step27_reporting.validate_report_inputs(
                matrix,
                summary,
                stats,
            )

    def test_stats_mismatch_rejected(self):
        matrix, summary, stats = self.components()
        stats = copy.deepcopy(stats)
        stats["pair_total_statistics"]["shared_count"]["sum"] += 1
        with self.assertRaises(step27_reporting.ReportingError):
            step27_reporting.validate_report_inputs(
                matrix,
                summary,
                stats,
            )

    def test_pair_distribution_mismatch_rejected(self):
        matrix, summary, stats = self.components()
        stats = copy.deepcopy(stats)
        label = mismatch_summary.CLASS_PARTIAL
        stats["pair_classification_distribution"][label]["count"] += 1
        with self.assertRaises(step27_reporting.ReportingError):
            step27_reporting.validate_report_inputs(
                matrix,
                summary,
                stats,
            )

    def test_locus_distribution_mismatch_rejected(self):
        matrix, summary, stats = self.components()
        stats = copy.deepcopy(stats)
        label = mismatch_summary.CLASS_NONE
        stats["locus_classification_distribution"][label]["count"] += 1
        with self.assertRaises(step27_reporting.ReportingError):
            step27_reporting.validate_report_inputs(
                matrix,
                summary,
                stats,
            )

    def test_candidate_order_mismatch_rejected(self):
        matrix, summary, stats = self.components()
        summary = copy.deepcopy(summary)
        summary["rows"].reverse()
        with self.assertRaises(step27_reporting.ReportingError):
            step27_reporting.validate_report_inputs(
                matrix,
                summary,
                stats,
            )


class TestStep27Export(Step27Fixture):

    def test_json_export(self):
        report = step27_reporting.build_live_report(
            self.db,
            "recipient",
            "RECIP-001",
        )
        info = step27_reporting.export_report(
            report,
            output_dir=self.out,
            export_format="json",
        )
        self.assertTrue(info["json_path"].exists())

    def test_csv_export(self):
        report = step27_reporting.build_live_report(
            self.db,
            "recipient",
            "RECIP-001",
        )
        info = step27_reporting.export_report(
            report,
            output_dir=self.out,
            export_format="csv",
        )
        self.assertTrue(info["csv_path"].exists())

    def test_both_export(self):
        report = step27_reporting.build_live_report(
            self.db,
            "recipient",
            "RECIP-001",
        )
        info = step27_reporting.export_report(
            report,
            output_dir=self.out,
            export_format="both",
        )
        self.assertTrue(info["json_path"].exists())
        self.assertTrue(info["csv_path"].exists())

    def test_csv_contains_pair_and_locus_rows(self):
        report = step27_reporting.build_live_report(
            self.db,
            "recipient",
            "RECIP-001",
            loci=["A", "DRB1"],
        )
        info = step27_reporting.export_report(
            report,
            output_dir=self.out,
            export_format="csv",
        )
        text = info["csv_path"].read_text(
            encoding="utf-8"
        )
        self.assertIn("PAIR", text)
        self.assertIn("LOCUS", text)


    def test_all_export(self):
        report = step27_reporting.build_live_report(
            self.db,
            "recipient",
            "RECIP-001",
        )
        info = step27_reporting.export_report(
            report,
            output_dir=self.out,
            export_format="all",
        )
        self.assertTrue(info["json_path"].exists())
        self.assertTrue(info["csv_path"].exists())
        self.assertTrue(info["html_path"].exists())
        self.assertEqual(info["format"], "ALL")

    def test_html_export(self):
        report = step27_reporting.build_live_report(
            self.db,
            "recipient",
            "RECIP-001",
        )
        info = step27_reporting.export_report(
            report,
            output_dir=self.out,
            export_format="html",
        )
        self.assertTrue(info["html_path"].exists())
        html = info["html_path"].read_text(encoding="utf-8")
        self.assertIn("<html", html)
        self.assertIn("STEP 27 HLA Analytical Report", html)
        self.assertIn("NON-CLINICAL", html)

    def test_overwrite_protection(self):
        report = step27_reporting.build_live_report(
            self.db,
            "recipient",
            "RECIP-001",
        )
        step27_reporting.export_report(
            report,
            output_dir=self.out,
            export_format="json",
        )
        with self.assertRaises(
            step27_reporting.ReportingExportExistsError
        ):
            step27_reporting.export_report(
                report,
                output_dir=self.out,
                export_format="json",
            )


if __name__ == "__main__":
    unittest.main()
