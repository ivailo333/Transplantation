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


class TestStep12InteractiveInput(unittest.TestCase):
    """Нови тестове за интерактивното въвеждане от STEP 12."""

    def test_prompt_allele_preserves_raw_value(self):
        raw = "  HLA-A*02:01  "
        outputs = []

        with patch.object(
            hla,
            "validate_allele",
            return_value="A*02:01",
        ):
            result = hla.prompt_allele(
                "DONOR",
                "A",
                1,
                input_func=lambda prompt: raw,
                output_func=outputs.append,
            )

        self.assertEqual(result, raw)
        self.assertTrue(
            any("canonical: A*02:01" in line for line in outputs)
        )

    def test_prompt_allele_retries_after_invalid_value(self):
        values = iter([
            "A*99:99",
            "A*02:01",
        ])
        outputs = []

        with patch.object(
            hla,
            "validate_allele",
            side_effect=[
                ValueError("HLA алелът не е валиден: A*99:99"),
                "A*02:01",
            ],
        ):
            result = hla.prompt_allele(
                "DONOR",
                "A",
                1,
                input_func=lambda prompt: next(values),
                output_func=outputs.append,
            )

        self.assertEqual(result, "A*02:01")
        self.assertTrue(any("ERROR:" in line for line in outputs))

    def test_prompt_allele_retries_after_empty_value(self):
        values = iter([
            "   ",
            "A*02:01",
        ])
        outputs = []

        with patch.object(
            hla,
            "validate_allele",
            return_value="A*02:01",
        ) as validator:
            result = hla.prompt_allele(
                "DONOR",
                "A",
                1,
                input_func=lambda prompt: next(values),
                output_func=outputs.append,
            )

        self.assertEqual(result, "A*02:01")
        # Празният вход не трябва да стига до py-ard validation.
        validator.assert_called_once_with("A", "A*02:01")

    def test_prompt_allele_q_cancels_input(self):
        with self.assertRaises(hla.InputCancelled):
            hla.prompt_allele(
                "DONOR",
                "A",
                1,
                input_func=lambda prompt: "q",
                output_func=lambda message: None,
            )

    def test_input_person_collects_complete_raw_profile(self):
        raw_values = [
            " HLA-A*02:01 ", "A*24:02",
            "B*07:02", "B*44:02",
            "C*07:02", "C*05:01",
            "DRB1*15:01", "DRB1*04:01",
            "DQB1*06:02", "DQB1*03:02",
            "DPB1*04:01", "DPB1*02:01",
        ]

        values = iter(raw_values)

        def fake_validate(locus, raw):
            # За този unit test ни интересува orchestration-ът,
            # не реалната py-ard база.
            return hla.clean_allele(raw)

        with patch.object(
            hla,
            "validate_allele",
            side_effect=fake_validate,
        ):
            profile = hla.input_person(
                "DONOR",
                input_func=lambda prompt: next(values),
                output_func=lambda message: None,
            )

        self.assertEqual(tuple(profile.keys()), hla.HLA_LOCI)
        self.assertEqual(profile["A"][0], " HLA-A*02:01 ")
        self.assertEqual(profile["A"][1], "A*24:02")
        self.assertEqual(profile["DPB1"], ["DPB1*04:01", "DPB1*02:01"])

        total_values = sum(
            len(profile[locus])
            for locus in hla.HLA_LOCI
        )
        self.assertEqual(total_values, 12)


class TestStep13CDisplayAndCLI(unittest.TestCase):

    def test_print_saved_typing_contains_metadata_and_representations(self):
        loaded = {
            "subject": {
                "subject_id": 1,
                "external_id": "DONOR-001",
                "subject_type": "DONOR",
                "created_at": "2026-08-19 10:00:00",
            },
            "typing": {
                "typing_id": 7,
                "imgthla_version": "3650",
                "created_at": "2026-08-19 10:01:00",
            },
            "bundle": make_test_bundle(),
        }
        output = []

        hla.print_saved_typing(
            loaded,
            output_func=output.append,
        )

        rendered = "\n".join(output)

        self.assertIn("DONOR-001", rendered)
        self.assertIn("typing_id: 7", rendered)
        self.assertIn("IPD-IMGT/HLA version: 3650", rendered)
        self.assertIn("RAW:", rendered)
        self.assertIn("CANONICAL:", rendered)
        self.assertIn("LGX:", rendered)

    def test_extract_optional_value_reads_typing_id(self):
        value, remaining = hla._extract_optional_value(
            ["--typing-id", "12", "--demo"],
            "--typing-id",
            cast=int,
        )

        self.assertEqual(value, 12)
        self.assertEqual(remaining, ["--demo"])

    def test_typing_id_without_load_returns_error(self):
        output = []

        result = hla.main(
            argv=["--typing-id", "4"],
            output_func=output.append,
        )

        self.assertEqual(result, 2)
        self.assertTrue(
            any("--typing-id" in line for line in output)
        )


class TestStep13DCLI(unittest.TestCase):

    def test_extract_pair_values(self):
        pair, remaining = hla._extract_pair_values(
            [
                "--create-analysis",
                "DONOR-001",
                "RECIP-001",
                "--demo",
            ],
            "--create-analysis",
        )

        self.assertEqual(
            pair,
            ("DONOR-001", "RECIP-001"),
        )
        self.assertEqual(
            remaining,
            ["--demo"],
        )


class TestStep13ECLIAndDisplay(unittest.TestCase):

    def test_print_analysis_results_save_summary_mentions_24(self):
        analyzed = {
            "linked": {
                "run": {
                    "donor": {"external_id": "DONOR-001"},
                    "recipient": {"external_id": "RECIP-001"},
                }
            },
            "results": {},
            "save_info": {
                "run_id": 1,
                "row_count": 24,
                "donor_typing_id": 1,
                "recipient_typing_id": 2,
                "imgthla_version": "3650",
            },
        }

        output = []

        hla.print_analysis_results_save_summary(
            analyzed,
            output_func=output.append,
        )

        rendered = "\n".join(output)

        self.assertIn("run_id: 1", rendered)
        self.assertIn("Saved analysis_result rows: 24", rendered)
        self.assertIn("DONOR-001", rendered)
        self.assertIn("RECIP-001", rendered)

    def test_build_comparison_results_is_copy_sensitive(self):
        donor_bundle = {
            key: {
                locus: ["X", "X"]
                for locus in hla.HLA_LOCI
            }
            for key in ("canonical", "lgx", "G", "P")
        }

        recipient_bundle = {
            key: {
                locus: ["X", "Y"]
                for locus in hla.HLA_LOCI
            }
            for key in ("canonical", "lgx", "G", "P")
        }

        results = hla.build_comparison_results_from_bundles(
            donor_bundle,
            recipient_bundle,
        )

        self.assertEqual(
            results["canonical"]["A"]["shared_count"],
            1,
        )
        self.assertEqual(
            results["canonical"]["A"]["mismatch_count"],
            1,
        )


class TestStep13FCLIAndDisplay(unittest.TestCase):

    def test_print_export_summary_contains_paths(self):
        output = []

        info = {
            "run_id": 1,
            "row_count": 24,
            "output_dir": Path("exports"),
            "files": {
                "json": Path("exports/analysis_run_1.json"),
                "csv": Path("exports/analysis_run_1.csv"),
            },
        }

        hla.print_export_summary(
            info,
            output_func=output.append,
        )

        rendered = "\n".join(output)

        self.assertIn("STEP 13F", rendered)
        self.assertIn("analysis_run_1.json", rendered)
        self.assertIn("analysis_run_1.csv", rendered)
        self.assertIn("24", rendered)


class TestStep13GCLIAndDisplay(unittest.TestCase):

    def test_print_schema_status_contains_versions(self):
        output = []

        status = {
            "database_path": Path("transplant.db"),
            "exists": True,
            "current_version": 3,
            "required_version": 3,
            "is_current": True,
            "pending": [],
            "history": [
                {
                    "version": 1,
                    "name": "schema_registry_baseline",
                    "applied_at": "2026-08-19 10:00:00",
                },
                {
                    "version": 2,
                    "name": (
                        "analysis_results_unique_"
                        "run_level_locus"
                    ),
                    "applied_at": "2026-08-19 10:01:00",
                },
            ],
            "analysis_results_unique_key": True,
        }

        hla.print_database_schema_status(
            status,
            output_func=output.append,
        )

        rendered = "\n".join(output)

        self.assertIn("STEP 13G", rendered)
        self.assertIn("Schema version: 3 / 3", rendered)
        self.assertIn("Pending migrations: none", rendered)
