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


class TestStep13GDatabaseMigrations(unittest.TestCase):

    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.db_path = Path(self.temp_dir.name) / "step13g.db"

    def tearDown(self):
        self.temp_dir.cleanup()

    def test_fresh_database_reaches_current_schema_version(self):
        database.initialize_database(self.db_path)

        status = database.get_database_schema_status(
            self.db_path
        )

        self.assertTrue(status["is_current"])
        self.assertEqual(
            status["current_version"],
            migrations.CURRENT_SCHEMA_VERSION,
        )

    def test_schema_migrations_table_is_created(self):
        database.initialize_database(self.db_path)

        self.assertIn(
            "schema_migrations",
            database.get_table_names(self.db_path),
        )

    def test_fresh_database_records_three_migrations(self):
        database.initialize_database(self.db_path)

        history = database.get_migration_history(
            self.db_path
        )

        self.assertEqual(
            [item["version"] for item in history],
            [1, 2, 3],
        )

    def test_no_pending_migrations_after_initialize(self):
        database.initialize_database(self.db_path)

        status = database.get_database_schema_status(
            self.db_path
        )

        self.assertEqual(status["pending"], [])

    def test_initialize_database_is_migration_idempotent(self):
        database.initialize_database(self.db_path)
        first = database.get_migration_history(self.db_path)

        database.initialize_database(self.db_path)
        second = database.get_migration_history(self.db_path)

        self.assertEqual(first, second)

    def test_unique_analysis_results_key_exists(self):
        database.initialize_database(self.db_path)

        status = database.get_database_schema_status(
            self.db_path
        )

        self.assertTrue(
            status["analysis_results_unique_key"]
        )

    def test_nonexistent_database_status_is_read_only(self):
        status = database.get_database_schema_status(
            self.db_path
        )

        self.assertFalse(status["exists"])
        self.assertEqual(status["current_version"], 0)
        self.assertFalse(self.db_path.exists())

    def test_legacy_database_is_migrated(self):
        conn = sqlite3.connect(str(self.db_path))

        try:
            conn.execute(
                """
                CREATE TABLE analysis_results (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    run_id INTEGER NOT NULL,
                    level TEXT NOT NULL,
                    locus TEXT NOT NULL,
                    shared_count INTEGER NOT NULL,
                    donor_only_count INTEGER NOT NULL,
                    recipient_only_count INTEGER NOT NULL,
                    shared_values TEXT NOT NULL,
                    donor_only_values TEXT NOT NULL,
                    recipient_only_values TEXT NOT NULL
                )
                """
            )
            conn.commit()
        finally:
            conn.close()

        before = database.get_database_schema_status(
            self.db_path
        )

        self.assertEqual(before["current_version"], 0)
        self.assertFalse(
            before["analysis_results_unique_key"]
        )

        database.migrate_database(self.db_path)

        after = database.get_database_schema_status(
            self.db_path
        )

        self.assertTrue(after["is_current"])
        self.assertTrue(
            after["analysis_results_unique_key"]
        )

    def test_duplicate_legacy_rows_block_unique_migration(self):
        conn = sqlite3.connect(str(self.db_path))

        try:
            conn.execute(
                """
                CREATE TABLE analysis_results (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    run_id INTEGER NOT NULL,
                    level TEXT NOT NULL,
                    locus TEXT NOT NULL,
                    shared_count INTEGER NOT NULL,
                    donor_only_count INTEGER NOT NULL,
                    recipient_only_count INTEGER NOT NULL,
                    shared_values TEXT NOT NULL,
                    donor_only_values TEXT NOT NULL,
                    recipient_only_values TEXT NOT NULL
                )
                """
            )

            row = (
                1,
                "CANONICAL",
                "A",
                0,
                2,
                2,
                "[]",
                "[]",
                "[]",
            )

            insert_sql = """
                INSERT INTO analysis_results (
                    run_id,
                    level,
                    locus,
                    shared_count,
                    donor_only_count,
                    recipient_only_count,
                    shared_values,
                    donor_only_values,
                    recipient_only_values
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """

            conn.execute(insert_sql, row)
            conn.execute(insert_sql, row)
            conn.commit()
        finally:
            conn.close()

        with self.assertRaises(
            database.MigrationConflictError
        ):
            database.migrate_database(self.db_path)

        status = database.get_database_schema_status(
            self.db_path
        )

        self.assertEqual(status["current_version"], 1)
        self.assertFalse(
            status["analysis_results_unique_key"]
        )

    def test_verify_database_is_current_passes_after_migration(self):
        database.initialize_database(self.db_path)

        self.assertTrue(
            database.verify_database_is_current(
                self.db_path
            )
        )

    def test_verify_database_is_current_rejects_missing_db(self):
        with self.assertRaises(database.DatabaseSchemaError):
            database.verify_database_is_current(
                self.db_path
            )

    def test_named_unique_index_is_created(self):
        database.initialize_database(self.db_path)

        with closing(database.connect_db(self.db_path)) as conn:
            names = {
                row[1]
                for row in conn.execute(
                    "PRAGMA index_list('analysis_results')"
                ).fetchall()
            }

        self.assertIn(
            migrations.UNIQUE_RESULTS_INDEX,
            names,
        )

    def test_migrate_database_second_run_applies_nothing(self):
        first = database.migrate_database(self.db_path)
        second = database.migrate_database(self.db_path)

        self.assertEqual(
            [item["version"] for item in first["applied"]],
            [1, 2, 3],
        )
        self.assertEqual(second["applied"], [])

    def test_schema_status_reports_required_version(self):
        database.initialize_database(self.db_path)

        status = database.get_database_schema_status(
            self.db_path
        )

        self.assertEqual(
            status["required_version"],
            migrations.CURRENT_SCHEMA_VERSION,
        )
