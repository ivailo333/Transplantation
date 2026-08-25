import copy
import csv
import json
import sqlite3
import tempfile
from pathlib import Path
import unittest
from unittest.mock import patch

import command_cli
import database
import importers

from test_helpers import make_test_bundle


def raw_hla_profile():
    return {
        "A": ["A*02:01", "A*24:02"],
        "B": ["B*07:02", "B*44:02"],
        "C": ["C*07:02", "C*05:01"],
        "DRB1": ["DRB1*15:01", "DRB1*04:01"],
        "DQB1": ["DQB1*06:02", "DQB1*03:02"],
        "DPB1": ["DPB1*04:01", "DPB1*02:01"],
    }


def normalized_record(
    external_id="DONOR-IMPORT-001",
    subject_type="DONOR",
    version=None,
):
    return {
        "external_id": external_id,
        "subject_type": subject_type,
        "imgthla_version": version,
        "raw_profile": raw_hla_profile(),
        "source_record_number": 1,
    }


def prepared_record(
    external_id="DONOR-IMPORT-001",
    subject_type="DONOR",
    version="3650",
    source_record_number=1,
):
    return {
        "external_id": external_id,
        "subject_type": subject_type,
        "imgthla_version": version,
        "bundle": make_test_bundle(),
        "source_record_number": source_record_number,
    }


class TestImportFormat(unittest.TestCase):

    def test_json_extension_is_detected(self):
        self.assertEqual(
            importers.detect_import_format("typing.JSON"),
            "json",
        )

    def test_csv_extension_is_detected(self):
        self.assertEqual(
            importers.detect_import_format("typing.csv"),
            "csv",
        )

    def test_explicit_format_overrides_extension(self):
        self.assertEqual(
            importers.detect_import_format(
                "typing.unknown",
                "json",
            ),
            "json",
        )

    def test_unknown_extension_is_rejected(self):
        with self.assertRaises(
            importers.ImportFileFormatError
        ):
            importers.detect_import_format("typing.txt")


class TestJSONParsing(unittest.TestCase):

    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()

    def tearDown(self):
        self.temp_dir.cleanup()

    def write_json(self, payload):
        path = Path(self.temp_dir.name) / "typing.json"

        with path.open("w", encoding="utf-8") as handle:
            json.dump(payload, handle)

        return path

    def test_single_json_object_is_loaded(self):
        path = self.write_json(
            {
                "external_id": "DONOR-002",
                "subject_type": "donor",
                "hla": raw_hla_profile(),
            }
        )

        records = importers.load_json_records(path)

        self.assertEqual(len(records), 1)
        self.assertEqual(
            records[0]["external_id"],
            "DONOR-002",
        )
        self.assertEqual(
            records[0]["subject_type"],
            "DONOR",
        )

    def test_json_list_is_loaded(self):
        payload = [
            {
                "external_id": "DONOR-002",
                "subject_type": "DONOR",
                "hla": raw_hla_profile(),
            },
            {
                "external_id": "RECIP-002",
                "subject_type": "RECIPIENT",
                "hla": raw_hla_profile(),
            },
        ]

        path = self.write_json(payload)
        records = importers.load_json_records(path)

        self.assertEqual(len(records), 2)

    def test_json_typings_wrapper_is_loaded(self):
        path = self.write_json(
            {
                "typings": [
                    {
                        "external_id": "DONOR-002",
                        "subject_type": "DONOR",
                        "hla": raw_hla_profile(),
                    }
                ]
            }
        )

        records = importers.load_json_records(path)

        self.assertEqual(len(records), 1)

    def test_hla_prefixed_keys_are_accepted(self):
        hla = {
            f"HLA-{locus}": values
            for locus, values in raw_hla_profile().items()
        }

        path = self.write_json(
            {
                "external_id": "DONOR-002",
                "subject_type": "DONOR",
                "hla": hla,
            }
        )

        records = importers.load_json_records(path)

        self.assertEqual(
            tuple(records[0]["raw_profile"]),
            database.HLA_LOCI,
        )

    def test_missing_hla_locus_is_rejected(self):
        hla = raw_hla_profile()
        del hla["DPB1"]

        path = self.write_json(
            {
                "external_id": "DONOR-002",
                "subject_type": "DONOR",
                "hla": hla,
            }
        )

        with self.assertRaises(
            importers.ImportRecordError
        ):
            importers.load_json_records(path)

    def test_empty_json_list_is_rejected(self):
        path = self.write_json([])

        with self.assertRaises(
            importers.ImportRecordError
        ):
            importers.load_json_records(path)


class TestCSVParsing(unittest.TestCase):

    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()

    def tearDown(self):
        self.temp_dir.cleanup()

    def csv_path(self):
        return Path(self.temp_dir.name) / "typing.csv"

    def write_rows(self, rows, fieldnames=None):
        path = self.csv_path()

        if fieldnames is None:
            fieldnames = [
                *importers.CSV_REQUIRED_COLUMNS,
                "imgthla_version",
            ]

        with path.open(
            "w",
            encoding="utf-8-sig",
            newline="",
        ) as handle:
            writer = csv.DictWriter(
                handle,
                fieldnames=fieldnames,
            )
            writer.writeheader()

            for row in rows:
                writer.writerow(row)

        return path

    def valid_row(self, external_id="DONOR-003"):
        return {
            "external_id": external_id,
            "subject_type": "DONOR",
            "imgthla_version": "3650",
            "A1": "A*02:01",
            "A2": "A*24:02",
            "B1": "B*07:02",
            "B2": "B*44:02",
            "C1": "C*07:02",
            "C2": "C*05:01",
            "DRB1_1": "DRB1*15:01",
            "DRB1_2": "DRB1*04:01",
            "DQB1_1": "DQB1*06:02",
            "DQB1_2": "DQB1*03:02",
            "DPB1_1": "DPB1*04:01",
            "DPB1_2": "DPB1*02:01",
        }

    def test_single_csv_row_is_loaded(self):
        path = self.write_rows([self.valid_row()])

        records = importers.load_csv_records(path)

        self.assertEqual(len(records), 1)
        self.assertEqual(
            records[0]["raw_profile"]["A"],
            ["A*02:01", "A*24:02"],
        )

    def test_multiple_csv_rows_are_loaded(self):
        first = self.valid_row("DONOR-003")
        second = self.valid_row("RECIP-003")
        second["subject_type"] = "RECIPIENT"

        path = self.write_rows([first, second])

        records = importers.load_csv_records(path)

        self.assertEqual(len(records), 2)

    def test_missing_required_csv_column_is_rejected(self):
        row = self.valid_row()
        fieldnames = [
            column
            for column in importers.CSV_REQUIRED_COLUMNS
            if column != "DPB1_2"
        ]
        row = {
            key: value
            for key, value in row.items()
            if key in fieldnames
        }

        path = self.write_rows(
            [row],
            fieldnames=fieldnames,
        )

        with self.assertRaises(
            importers.ImportFileFormatError
        ):
            importers.load_csv_records(path)

    def test_empty_allele_cell_is_rejected(self):
        row = self.valid_row()
        row["A1"] = ""

        path = self.write_rows([row])

        with self.assertRaises(
            importers.ImportRecordError
        ):
            importers.load_csv_records(path)


class TestPreparation(unittest.TestCase):

    def test_version_defaults_to_active_version(self):
        record = normalized_record(version=None)

        with patch.object(
            importers,
            "canonicalize_person",
            return_value=raw_hla_profile(),
        ), patch.object(
            importers,
            "reduce_person",
            side_effect=lambda profile, mode: copy.deepcopy(profile),
        ):
            prepared = importers.prepare_typing_record(
                record,
                active_version="3650",
            )

        self.assertEqual(
            prepared["imgthla_version"],
            "3650",
        )

    def test_version_mismatch_is_rejected(self):
        record = normalized_record(version="9999")

        with self.assertRaises(
            importers.ImportVersionError
        ):
            importers.prepare_typing_record(
                record,
                active_version="3650",
            )

    def test_prepare_typing_record_builds_five_representations(self):
        record = normalized_record()

        with patch.object(
            importers,
            "canonicalize_person",
            return_value=raw_hla_profile(),
        ), patch.object(
            importers,
            "reduce_person",
            side_effect=lambda profile, mode: copy.deepcopy(profile),
        ):
            prepared = importers.prepare_typing_record(
                record,
                active_version="3650",
            )

        self.assertEqual(
            set(prepared["bundle"]),
            {"raw", "canonical", "lgx", "G", "P"},
        )


class TestAtomicPersistence(unittest.TestCase):

    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.db_path = Path(self.temp_dir.name) / "step16.db"
        database.initialize_database(self.db_path)

    def tearDown(self):
        self.temp_dir.cleanup()

    def test_atomic_save_persists_two_typings(self):
        records = [
            prepared_record(
                "DONOR-010",
                "DONOR",
                source_record_number=1,
            ),
            prepared_record(
                "RECIP-010",
                "RECIPIENT",
                source_record_number=2,
            ),
        ]

        saved = database.save_typing_records_atomic(
            self.db_path,
            records,
        )

        self.assertEqual(len(saved), 2)

        subjects = database.list_subjects(self.db_path)
        self.assertEqual(len(subjects), 2)

    def test_atomic_save_rolls_back_on_subject_type_conflict(self):
        database.save_subject_typing(
            self.db_path,
            "CONFLICT-001",
            "DONOR",
            "3650",
            make_test_bundle(),
        )

        records = [
            prepared_record(
                "NEW-001",
                "DONOR",
                source_record_number=1,
            ),
            prepared_record(
                "CONFLICT-001",
                "RECIPIENT",
                source_record_number=2,
            ),
        ]

        with self.assertRaises(
            database.SubjectTypeConflictError
        ):
            database.save_typing_records_atomic(
                self.db_path,
                records,
            )

        subjects = database.list_subjects(self.db_path)
        ids = {
            subject["external_id"]
            for subject in subjects
        }

        self.assertNotIn("NEW-001", ids)
        self.assertIn("CONFLICT-001", ids)


class TestImportWorkflow(unittest.TestCase):

    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.db_path = Path(self.temp_dir.name) / "step16.db"
        database.initialize_database(self.db_path)

        self.json_path = (
            Path(self.temp_dir.name)
            / "typing.json"
        )

        with self.json_path.open(
            "w",
            encoding="utf-8",
        ) as handle:
            json.dump(
                {
                    "external_id": "DONOR-FILE-001",
                    "subject_type": "DONOR",
                    "hla": raw_hla_profile(),
                },
                handle,
            )

    def tearDown(self):
        self.temp_dir.cleanup()

    def test_dry_run_does_not_write_to_database(self):
        prepared = prepared_record(
            "DONOR-FILE-001",
            "DONOR",
        )

        with patch.object(
            importers,
            "prepare_import_records",
            return_value=[prepared],
        ):
            info = importers.import_typings(
                database_path=self.db_path,
                input_path=self.json_path,
                dry_run=True,
            )

        self.assertEqual(info["saved_count"], 0)
        self.assertEqual(
            database.list_subjects(self.db_path),
            [],
        )

    def test_import_typings_saves_prepared_record(self):
        prepared = prepared_record(
            "DONOR-FILE-001",
            "DONOR",
        )

        with patch.object(
            importers,
            "prepare_import_records",
            return_value=[prepared],
        ):
            info = importers.import_typings(
                database_path=self.db_path,
                input_path=self.json_path,
            )

        self.assertEqual(info["saved_count"], 1)

        subjects = database.list_subjects(self.db_path)
        self.assertEqual(
            subjects[0]["external_id"],
            "DONOR-FILE-001",
        )


class TestCLI(unittest.TestCase):

    def test_typing_group_help_mentions_import(self):
        help_text = command_cli._group_help("typings")

        self.assertIn("typings import FILE", help_text)

    def test_root_help_mentions_json_csv_import(self):
        text = command_cli.command_help_text()

        self.assertIn("STEP 16", text)
        self.assertIn("STEP 15", text)
        self.assertIn("typings import", text)

    def test_cli_import_dry_run_dispatches(self):
        output = []

        fake_info = {
            "source_path": Path("typing.json"),
            "format": "json",
            "record_count": 1,
            "validated_count": 1,
            "saved_count": 0,
            "dry_run": True,
            "records": [],
            "saved": [],
        }

        with tempfile.TemporaryDirectory() as temp_dir:
            db_path = Path(temp_dir) / "cli.db"
            database.initialize_database(db_path)

            with patch.object(
                importers,
                "import_typings",
                return_value=fake_info,
            ) as importer:
                result = command_cli.run_command_cli(
                    [
                        "--db",
                        str(db_path),
                        "typings",
                        "import",
                        "typing.json",
                        "--dry-run",
                    ],
                    output_func=output.append,
                )

        self.assertEqual(result, 0)
        importer.assert_called_once()
        rendered = "\n".join(output)
        self.assertIn("DRY RUN", rendered)

    def test_cli_invalid_import_format_returns_two(self):
        output = []

        result = command_cli.run_command_cli(
            [
                "typings",
                "import",
                "typing.json",
                "--format",
                "xml",
            ],
            output_func=output.append,
        )

        self.assertEqual(result, 2)
        self.assertTrue(
            any("ERROR:" in line for line in output)
        )


class TestSamples(unittest.TestCase):

    def test_sample_json_and_csv_are_present(self):
        project_root = Path(__file__).resolve().parents[1]

        self.assertTrue(
            (
                project_root
                / "import_typing.json"
            ).exists()
        )
        self.assertTrue(
            (
                project_root
                / "import_typing.csv"
            ).exists()
        )
        
        self.assertTrue(
            (
                project_root
                / "import_typings_batch.json"
            ).exists()
        )
