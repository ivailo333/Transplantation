import copy
import csv
import json
import sqlite3
import tempfile
from contextlib import closing
from pathlib import Path
import unittest
from unittest.mock import patch

import hla_match as hla
import database as database
import exporters as exporters
import migrations as migrations

from test_helpers import make_test_bundle, make_comparison_results


class TestStep13FExport(unittest.TestCase):

    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.db_path = Path(self.temp_dir.name) / "step13f.db"
        self.export_dir = Path(self.temp_dir.name) / "exports"

        database.initialize_database(self.db_path)

        pair = database.save_donor_recipient_typings(
            database_path=self.db_path,
            donor_external_id="DONOR-001",
            recipient_external_id="RECIP-001",
            imgthla_version="3650",
            donor_bundle=make_test_bundle(),
            recipient_bundle=make_test_bundle(),
        )

        run = database.create_analysis_run(
            self.db_path,
            pair["donor"]["typing_id"],
            pair["recipient"]["typing_id"],
        )
        self.run_id = run["run_id"]

        linked = database.load_analysis_run_typings(
            self.db_path,
            self.run_id,
        )

        results = hla.build_comparison_results_from_bundles(
            linked["donor"]["bundle"],
            linked["recipient"]["bundle"],
        )

        database.save_analysis_results(
            self.db_path,
            self.run_id,
            results,
        )

    def tearDown(self):
        self.temp_dir.cleanup()

    def test_normalize_export_format_defaults_to_both(self):
        self.assertEqual(
            exporters.normalize_export_format(None),
            "both",
        )

    def test_invalid_export_format_is_rejected(self):
        with self.assertRaises(ValueError):
            exporters.normalize_export_format("pdf")

    def test_build_export_payload_contains_run_metadata(self):
        payload = exporters.build_export_payload(
            self.db_path,
            self.run_id,
        )

        self.assertEqual(payload["schema"], "hla-analysis-export-v1")
        self.assertEqual(payload["run"]["run_id"], self.run_id)
        self.assertEqual(
            payload["run"]["donor"]["external_id"],
            "DONOR-001",
        )
        self.assertEqual(
            payload["run"]["recipient"]["external_id"],
            "RECIP-001",
        )
        self.assertEqual(
            payload["run"]["analysis_result_count"],
            24,
        )

    def test_json_export_is_created(self):
        info = exporters.export_analysis(
            self.db_path,
            self.run_id,
            output_dir=self.export_dir,
            export_format="json",
        )

        self.assertTrue(info["files"]["json"].exists())
        self.assertNotIn("csv", info["files"])

    def test_json_export_contains_four_levels(self):
        info = exporters.export_analysis(
            self.db_path,
            self.run_id,
            output_dir=self.export_dir,
            export_format="json",
        )

        with info["files"]["json"].open(
            "r",
            encoding="utf-8",
        ) as handle:
            payload = json.load(handle)

        self.assertEqual(
            set(payload["results"]),
            {"canonical", "lgx", "G", "P"},
        )

        for level in payload["results"]:
            self.assertEqual(
                set(payload["results"][level]),
                set(database.HLA_LOCI),
            )

    def test_json_preserves_lists_as_json_arrays(self):
        info = exporters.export_analysis(
            self.db_path,
            self.run_id,
            output_dir=self.export_dir,
            export_format="json",
        )

        with info["files"]["json"].open(
            "r",
            encoding="utf-8",
        ) as handle:
            payload = json.load(handle)

        self.assertIsInstance(
            payload["results"]["canonical"]["A"]["shared"],
            list,
        )

    def test_csv_export_is_created(self):
        info = exporters.export_analysis(
            self.db_path,
            self.run_id,
            output_dir=self.export_dir,
            export_format="csv",
        )

        self.assertTrue(info["files"]["csv"].exists())
        self.assertNotIn("json", info["files"])

    def test_csv_has_exactly_24_data_rows(self):
        info = exporters.export_analysis(
            self.db_path,
            self.run_id,
            output_dir=self.export_dir,
            export_format="csv",
        )

        with info["files"]["csv"].open(
            "r",
            encoding="utf-8-sig",
            newline="",
        ) as handle:
            rows = list(csv.DictReader(handle))

        self.assertEqual(len(rows), 24)

    def test_csv_has_expected_columns(self):
        info = exporters.export_analysis(
            self.db_path,
            self.run_id,
            output_dir=self.export_dir,
            export_format="csv",
        )

        with info["files"]["csv"].open(
            "r",
            encoding="utf-8-sig",
            newline="",
        ) as handle:
            reader = csv.DictReader(handle)
            self.assertEqual(
                tuple(reader.fieldnames),
                exporters.CSV_COLUMNS,
            )

    def test_both_export_creates_json_and_csv(self):
        info = exporters.export_analysis(
            self.db_path,
            self.run_id,
            output_dir=self.export_dir,
            export_format="both",
        )

        self.assertTrue(info["files"]["json"].exists())
        self.assertTrue(info["files"]["csv"].exists())
        self.assertEqual(info["row_count"], 24)

    def test_export_creates_output_directory(self):
        nested = (
            Path(self.temp_dir.name)
            / "a"
            / "b"
            / "exports"
        )

        exporters.export_analysis(
            self.db_path,
            self.run_id,
            output_dir=nested,
            export_format="json",
        )

        self.assertTrue(nested.is_dir())

    def test_existing_export_is_not_overwritten_by_default(self):
        exporters.export_analysis(
            self.db_path,
            self.run_id,
            output_dir=self.export_dir,
            export_format="json",
        )

        with self.assertRaises(exporters.ExportFileExistsError):
            exporters.export_analysis(
                self.db_path,
                self.run_id,
                output_dir=self.export_dir,
                export_format="json",
            )

    def test_overwrite_true_allows_reexport(self):
        exporters.export_analysis(
            self.db_path,
            self.run_id,
            output_dir=self.export_dir,
            export_format="json",
        )

        info = exporters.export_analysis(
            self.db_path,
            self.run_id,
            output_dir=self.export_dir,
            export_format="json",
            overwrite=True,
        )

        self.assertTrue(info["files"]["json"].exists())

    def test_export_filename_contains_run_id(self):
        info = exporters.export_analysis(
            self.db_path,
            self.run_id,
            output_dir=self.export_dir,
            export_format="both",
        )

        self.assertEqual(
            info["files"]["json"].name,
            f"analysis_run_{self.run_id}.json",
        )
        self.assertEqual(
            info["files"]["csv"].name,
            f"analysis_run_{self.run_id}.csv",
        )

    def test_export_requires_saved_analysis_results(self):
        pair = database.save_donor_recipient_typings(
            database_path=self.db_path,
            donor_external_id="DONOR-002",
            recipient_external_id="RECIP-002",
            imgthla_version="3650",
            donor_bundle=make_test_bundle(),
            recipient_bundle=make_test_bundle(),
        )

        run = database.create_analysis_run(
            self.db_path,
            pair["donor"]["typing_id"],
            pair["recipient"]["typing_id"],
        )

        with self.assertRaises(
            database.AnalysisResultsNotFoundError
        ):
            exporters.export_analysis(
                self.db_path,
                run["run_id"],
                output_dir=self.export_dir,
                export_format="json",
            )
