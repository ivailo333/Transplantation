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


class TestStep13CLoadTyping(unittest.TestCase):

    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.db_path = Path(self.temp_dir.name) / "step13c.db"
        database.initialize_database(self.db_path)

    def tearDown(self):
        self.temp_dir.cleanup()

    def _save(self, external_id="DONOR-001", subject_type="DONOR", version="3650"):
        return database.save_subject_typing(
            self.db_path,
            external_id,
            subject_type,
            version,
            make_test_bundle(),
        )

    def test_list_subjects_empty_database(self):
        self.assertEqual(
            database.list_subjects(self.db_path),
            [],
        )

    def test_list_subjects_returns_saved_subject(self):
        self._save()

        subjects = database.list_subjects(self.db_path)

        self.assertEqual(len(subjects), 1)
        self.assertEqual(subjects[0]["external_id"], "DONOR-001")
        self.assertEqual(subjects[0]["subject_type"], "DONOR")
        self.assertEqual(subjects[0]["typing_count"], 1)

    def test_load_latest_typing_round_trips_bundle(self):
        bundle = make_test_bundle()
        bundle["raw"]["A"][0] = "  A*02:01  "
        bundle["canonical"]["A"][0] = "A*02:01"

        saved = database.save_subject_typing(
            self.db_path,
            "DONOR-001",
            "DONOR",
            "3650",
            bundle,
        )

        loaded = database.load_subject_typing(
            self.db_path,
            "DONOR-001",
        )

        self.assertEqual(
            loaded["typing"]["typing_id"],
            saved["typing_id"],
        )
        self.assertEqual(loaded["bundle"], bundle)

    def test_latest_typing_is_selected_by_default(self):
        first = self._save(version="3650")
        second = self._save(version="3651")

        loaded = database.load_subject_typing(
            self.db_path,
            "DONOR-001",
        )

        self.assertNotEqual(first["typing_id"], second["typing_id"])
        self.assertEqual(
            loaded["typing"]["typing_id"],
            second["typing_id"],
        )
        self.assertEqual(
            loaded["typing"]["imgthla_version"],
            "3651",
        )

    def test_specific_older_typing_can_be_loaded(self):
        first = self._save(version="3650")
        self._save(version="3651")

        loaded = database.load_subject_typing(
            self.db_path,
            "DONOR-001",
            typing_id=first["typing_id"],
        )

        self.assertEqual(
            loaded["typing"]["typing_id"],
            first["typing_id"],
        )
        self.assertEqual(
            loaded["typing"]["imgthla_version"],
            "3650",
        )

    def test_missing_subject_raises(self):
        with self.assertRaises(database.SubjectNotFoundError):
            database.load_subject_typing(
                self.db_path,
                "UNKNOWN-001",
            )

    def test_typing_id_must_belong_to_subject(self):
        donor = self._save(
            external_id="DONOR-001",
            subject_type="DONOR",
        )

        database.save_subject_typing(
            self.db_path,
            "RECIP-001",
            "RECIPIENT",
            "3650",
            make_test_bundle(),
        )

        with self.assertRaises(database.TypingNotFoundError):
            database.load_subject_typing(
                self.db_path,
                "RECIP-001",
                typing_id=donor["typing_id"],
            )

    def test_list_subject_typings_returns_newest_first(self):
        first = self._save(version="3650")
        second = self._save(version="3651")

        typings = database.list_subject_typings(
            self.db_path,
            "DONOR-001",
        )

        self.assertEqual(
            [item["typing_id"] for item in typings],
            [second["typing_id"], first["typing_id"]],
        )
        self.assertEqual(
            [item["allele_row_count"] for item in typings],
            [12, 12],
        )

    def test_load_subject_profile_canonical(self):
        self._save()

        profile = database.load_subject_profile(
            self.db_path,
            "DONOR-001",
            representation="canonical",
        )

        self.assertEqual(
            profile["A"],
            ["A*02:01", "A*24:02"],
        )

    def test_load_subject_profile_accepts_lowercase_g(self):
        self._save()

        profile = database.load_subject_profile(
            self.db_path,
            "DONOR-001",
            representation="g",
        )

        self.assertEqual(
            profile["A"],
            ["A*02:01", "A*24:02"],
        )

    def test_invalid_representation_is_rejected(self):
        self._save()

        with self.assertRaises(ValueError):
            database.load_subject_profile(
                self.db_path,
                "DONOR-001",
                representation="XYZ",
            )

    def test_incomplete_typing_is_detected(self):
        saved = self._save()

        with closing(database.connect_db(self.db_path)) as conn:
            conn.execute(
                """
                DELETE FROM hla_alleles
                WHERE typing_id = ?
                  AND locus = 'DPB1'
                  AND allele_number = 2
                """,
                (saved["typing_id"],),
            )
            conn.commit()

        with self.assertRaises(database.IncompleteTypingError):
            database.load_subject_typing(
                self.db_path,
                "DONOR-001",
            )

    def test_loaded_metadata_contains_subject_and_version(self):
        saved = self._save(version="3650")

        loaded = database.load_subject_typing(
            self.db_path,
            "DONOR-001",
        )

        self.assertEqual(
            loaded["subject"]["external_id"],
            "DONOR-001",
        )
        self.assertEqual(
            loaded["subject"]["subject_type"],
            "DONOR",
        )
        self.assertEqual(
            loaded["typing"]["typing_id"],
            saved["typing_id"],
        )
        self.assertEqual(
            loaded["typing"]["imgthla_version"],
            "3650",
        )
