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


class TestStep13BDatabasePersistence(unittest.TestCase):

    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.db_path = Path(self.temp_dir.name) / "step13b.db"
        database.initialize_database(self.db_path)

    def tearDown(self):
        self.temp_dir.cleanup()

    def test_step13b_schema_is_compatible(self):
        self.assertTrue(
            database.verify_schema_compatibility(self.db_path)
        )

    def test_save_subject_typing_creates_subject(self):
        result = database.save_subject_typing(
            self.db_path,
            "DONOR-001",
            "DONOR",
            "3650",
            make_test_bundle(),
        )

        self.assertGreater(result["subject_id"], 0)
        self.assertGreater(result["typing_id"], 0)
        self.assertTrue(result["subject_created"])

    def test_one_typing_saves_exactly_12_allele_rows(self):
        result = database.save_subject_typing(
            self.db_path,
            "DONOR-001",
            "DONOR",
            "3650",
            make_test_bundle(),
        )

        with closing(database.connect_db(self.db_path)) as conn:
            count = conn.execute(
                """
                SELECT COUNT(*)
                FROM hla_alleles
                WHERE typing_id = ?
                """,
                (result["typing_id"],),
            ).fetchone()[0]

        self.assertEqual(count, 12)

    def test_raw_and_canonical_are_stored_separately(self):
        bundle = make_test_bundle(prefix="  ")
        bundle["raw"]["A"][0] = "  A*02:01  "
        bundle["canonical"]["A"][0] = "A*02:01"

        result = database.save_subject_typing(
            self.db_path,
            "DONOR-001",
            "DONOR",
            "3650",
            bundle,
        )

        with closing(database.connect_db(self.db_path)) as conn:
            row = conn.execute(
                """
                SELECT raw_value, canonical_value
                FROM hla_alleles
                WHERE typing_id = ?
                  AND locus = 'A'
                  AND allele_number = 1
                """,
                (result["typing_id"],),
            ).fetchone()

        self.assertEqual(row[0], "  A*02:01  ")
        self.assertEqual(row[1], "A*02:01")

    def test_imgthla_version_is_stored(self):
        result = database.save_subject_typing(
            self.db_path,
            "DONOR-001",
            "DONOR",
            "3650",
            make_test_bundle(),
        )

        with closing(database.connect_db(self.db_path)) as conn:
            version = conn.execute(
                """
                SELECT imgthla_version
                FROM hla_typings
                WHERE id = ?
                """,
                (result["typing_id"],),
            ).fetchone()[0]

        self.assertEqual(version, "3650")

    def test_existing_subject_can_receive_new_typing(self):
        first = database.save_subject_typing(
            self.db_path,
            "DONOR-001",
            "DONOR",
            "3650",
            make_test_bundle(),
        )
        second = database.save_subject_typing(
            self.db_path,
            "DONOR-001",
            "DONOR",
            "3650",
            make_test_bundle(),
        )

        self.assertEqual(first["subject_id"], second["subject_id"])
        self.assertNotEqual(first["typing_id"], second["typing_id"])
        self.assertFalse(second["subject_created"])

    def test_subject_type_conflict_is_rejected(self):
        database.save_subject_typing(
            self.db_path,
            "SUBJECT-001",
            "DONOR",
            "3650",
            make_test_bundle(),
        )

        with self.assertRaises(database.SubjectTypeConflictError):
            database.save_subject_typing(
                self.db_path,
                "SUBJECT-001",
                "RECIPIENT",
                "3650",
                make_test_bundle(),
            )

    def test_pair_save_creates_24_allele_rows(self):
        result = database.save_donor_recipient_typings(
            database_path=self.db_path,
            donor_external_id="DONOR-001",
            recipient_external_id="RECIP-001",
            imgthla_version="3650",
            donor_bundle=make_test_bundle(),
            recipient_bundle=make_test_bundle(),
        )

        typing_ids = (
            result["donor"]["typing_id"],
            result["recipient"]["typing_id"],
        )

        with closing(database.connect_db(self.db_path)) as conn:
            count = conn.execute(
                """
                SELECT COUNT(*)
                FROM hla_alleles
                WHERE typing_id IN (?, ?)
                """,
                typing_ids,
            ).fetchone()[0]

        self.assertEqual(count, 24)

    def test_pair_save_is_atomic_on_second_subject_failure(self):
        # Existing RECIPIENT ID deliberately conflicts with the DONOR type
        # requested for the first argument below.
        database.save_subject_typing(
            self.db_path,
            "CONFLICT-ID",
            "RECIPIENT",
            "3650",
            make_test_bundle(),
        )

        with closing(database.connect_db(self.db_path)) as conn:
            before_subjects = conn.execute(
                "SELECT COUNT(*) FROM subjects"
            ).fetchone()[0]
            before_typings = conn.execute(
                "SELECT COUNT(*) FROM hla_typings"
            ).fetchone()[0]

        with self.assertRaises(database.SubjectTypeConflictError):
            database.save_donor_recipient_typings(
                database_path=self.db_path,
                donor_external_id="CONFLICT-ID",
                recipient_external_id="RECIP-NEW",
                imgthla_version="3650",
                donor_bundle=make_test_bundle(),
                recipient_bundle=make_test_bundle(),
            )

        with closing(database.connect_db(self.db_path)) as conn:
            after_subjects = conn.execute(
                "SELECT COUNT(*) FROM subjects"
            ).fetchone()[0]
            after_typings = conn.execute(
                "SELECT COUNT(*) FROM hla_typings"
            ).fetchone()[0]

        self.assertEqual(after_subjects, before_subjects)
        self.assertEqual(after_typings, before_typings)

    def test_incompatible_existing_schema_is_detected(self):
        bad_db = Path(self.temp_dir.name) / "bad.db"

        conn = sqlite3.connect(str(bad_db))
        try:
            conn.execute(
                """
                CREATE TABLE subjects (
                    id INTEGER PRIMARY KEY,
                    external_id TEXT
                )
                """
            )
            conn.commit()
        finally:
            conn.close()

        with self.assertRaises(database.DatabaseSchemaError):
            database.verify_schema_compatibility(bad_db)
