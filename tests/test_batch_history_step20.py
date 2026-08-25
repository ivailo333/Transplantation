import copy
import csv
import json
import sqlite3
import tempfile
from pathlib import Path
import unittest

import batch_analysis
import batch_exporters
import batch_history
import batch_ranking
import command_cli
import database
import migrations

from test_helpers import make_test_bundle


def bundle_with_mismatched_loci(*loci):
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


class Step20Fixture(unittest.TestCase):

    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        root = Path(self.temp_dir.name)
        self.db_path = root / "step20.db"
        self.export_dir = root / "exports"
        database.initialize_database(self.db_path)

        database.save_subject_typing(
            self.db_path,
            "DONOR-FULL",
            "DONOR",
            "3650",
            make_test_bundle(),
        )
        database.save_subject_typing(
            self.db_path,
            "DONOR-A",
            "DONOR",
            "3650",
            bundle_with_mismatched_loci("A"),
        )
        database.save_subject_typing(
            self.db_path,
            "RECIP-001",
            "RECIPIENT",
            "3650",
            make_test_bundle(),
        )

    def tearDown(self):
        self.temp_dir.cleanup()

    def computed_batch(self, ranked=False, display_limit=None):
        batch = batch_analysis.run_batch_analysis(
            self.db_path,
            "recipient",
            "RECIP-001",
            save=False,
        )

        if ranked:
            batch = batch_ranking.apply_batch_ordering(
                batch,
                level="lgx",
                metric="donor-only",
                order="auto",
                display_limit=None,
            )
            batch["software_ordering"]["display_limit"] = display_limit

        return batch

    def run_cli(self, *args):
        output = []
        code = command_cli.run_command_cli(
            ["--db", str(self.db_path), *args],
            output_func=output.append,
        )
        return code, "\n".join(output)


class TestStep20Migration(unittest.TestCase):

    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.db_path = Path(self.temp_dir.name) / "migration.db"

    def tearDown(self):
        self.temp_dir.cleanup()

    def test_current_schema_version_is_three(self):
        self.assertEqual(migrations.CURRENT_SCHEMA_VERSION, 3)

    def test_fresh_database_has_batch_tables(self):
        database.initialize_database(self.db_path)
        names = set(database.get_table_names(self.db_path))
        self.assertIn("batch_runs", names)
        self.assertIn("batch_run_items", names)

    def test_fresh_database_reports_batch_history_schema(self):
        database.initialize_database(self.db_path)
        status = database.get_database_schema_status(self.db_path)
        self.assertTrue(status["batch_history_schema"])
        self.assertEqual(status["current_version"], 3)

    def test_fresh_database_records_three_migrations(self):
        database.initialize_database(self.db_path)
        history = database.get_migration_history(self.db_path)
        self.assertEqual([row["version"] for row in history], [1, 2, 3])

    def test_migration_is_idempotent(self):
        first = database.migrate_database(self.db_path)
        second = database.migrate_database(self.db_path)
        self.assertEqual([x["version"] for x in first["applied"]], [1, 2, 3])
        self.assertEqual(second["applied"], [])


class TestStep20Persistence(Step20Fixture):

    def test_persist_plain_batch_creates_batch_run(self):
        persisted = batch_history.persist_batch_with_runs(
            self.db_path,
            self.computed_batch(),
        )
        self.assertEqual(persisted["batch_id"], 1)
        self.assertTrue(persisted["save"])
        self.assertEqual(len(persisted["rows"]), 2)
        self.assertTrue(all(isinstance(row["run_id"], int) for row in persisted["rows"]))

    def test_persist_creates_24_results_per_pair(self):
        batch_history.persist_batch_with_runs(
            self.db_path,
            self.computed_batch(),
        )
        runs = database.list_analysis_runs(self.db_path)
        self.assertEqual(len(runs), 2)
        self.assertTrue(all(run["analysis_result_count"] == 24 for run in runs))

    def test_persist_ranked_batch_stores_ordering(self):
        persisted = batch_history.persist_batch_with_runs(
            self.db_path,
            self.computed_batch(ranked=True, display_limit=1),
        )
        saved = database.load_batch_run(self.db_path, persisted["batch_id"])
        self.assertEqual(saved["sort_level"], "lgx")
        self.assertEqual(saved["sort_metric"], "donor-only")
        self.assertEqual(saved["sort_order"], "asc")
        self.assertEqual(saved["requested_sort_order"], "auto")
        self.assertEqual(saved["display_limit"], 1)

    def test_persist_ranked_items_store_rank_and_criterion(self):
        persisted = batch_history.persist_batch_with_runs(
            self.db_path,
            self.computed_batch(ranked=True),
        )
        saved = database.load_batch_run(self.db_path, persisted["batch_id"])
        self.assertEqual(saved["items"][0]["software_position"], 1)
        self.assertEqual(saved["items"][0]["software_rank"], 1)
        self.assertIsInstance(saved["items"][0]["criterion_value"], int)

    def test_atomic_failure_rolls_back_batch_and_analysis_runs(self):
        batch = self.computed_batch()
        batch["rows"][1]["recipient_typing_id"] = 999999
        with self.assertRaises(database.TypingNotFoundError):
            batch_history.persist_batch_with_runs(self.db_path, batch)
        self.assertEqual(database.list_batch_runs(self.db_path), [])
        self.assertEqual(database.list_analysis_runs(self.db_path), [])

    def test_truncated_batch_is_rejected(self):
        batch = self.computed_batch(ranked=True)
        batch["rows"] = batch["rows"][:1]
        with self.assertRaises(batch_history.BatchHistoryError):
            batch_history.persist_batch_with_runs(self.db_path, batch)


class TestStep20Load(Step20Fixture):

    def setUp(self):
        super().setUp()
        self.persisted = batch_history.persist_batch_with_runs(
            self.db_path,
            self.computed_batch(ranked=True, display_limit=1),
        )
        self.batch_id = self.persisted["batch_id"]

    def test_list_batch_runs_returns_saved_batch(self):
        rows = database.list_batch_runs(self.db_path)
        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0]["batch_id"], self.batch_id)
        self.assertEqual(rows[0]["item_count"], 2)
        self.assertEqual(rows[0]["analysis_result_count"], 48)

    def test_load_batch_run_contains_exact_analysis_links(self):
        saved = database.load_batch_run(self.db_path, self.batch_id)
        self.assertEqual(saved["pair_count"], 2)
        self.assertEqual(len(saved["items"]), 2)
        self.assertTrue(all(item["analysis_result_count"] == 24 for item in saved["items"]))

    def test_load_batch_results_reconstructs_full_batch(self):
        batch = database.load_batch_results(self.db_path, self.batch_id)
        self.assertEqual(batch["batch_id"], self.batch_id)
        self.assertEqual(batch["pair_count"], 2)
        self.assertEqual(len(batch["rows"]), 2)
        self.assertEqual(set(batch["rows"][0]["results"]), {"canonical", "lgx", "G", "P"})

    def test_reload_preserves_software_order(self):
        batch = database.load_batch_results(self.db_path, self.batch_id)
        self.assertEqual(batch["rows"][0]["software_order"]["position"], 1)
        self.assertEqual(batch["software_ordering"]["metric"], "donor-only")
        self.assertEqual(batch["software_ordering"]["original_display_limit"], 1)

    def test_missing_batch_raises(self):
        with self.assertRaises(batch_history.BatchRunNotFoundError):
            database.load_batch_run(self.db_path, 999)


class TestStep20ReExport(Step20Fixture):

    def setUp(self):
        super().setUp()
        persisted = batch_history.persist_batch_with_runs(
            self.db_path,
            self.computed_batch(ranked=True),
        )
        self.batch_id = persisted["batch_id"]

    def test_reloaded_batch_exports_json_with_batch_id(self):
        batch = database.load_batch_results(self.db_path, self.batch_id)
        info = batch_exporters.export_batch(
            batch,
            output_dir=self.export_dir,
            export_format="json",
            export_name="saved_batch",
        )
        with info["files"]["json"].open("r", encoding="utf-8") as handle:
            payload = json.load(handle)
        self.assertEqual(payload["batch"]["batch_id"], self.batch_id)
        self.assertEqual(len(payload["pairs"]), 2)

    def test_reloaded_batch_exports_csv_with_batch_id(self):
        batch = database.load_batch_results(self.db_path, self.batch_id)
        info = batch_exporters.export_batch(
            batch,
            output_dir=self.export_dir,
            export_format="csv",
            export_name="saved_batch",
        )
        with info["files"]["csv"].open("r", encoding="utf-8-sig", newline="") as handle:
            rows = list(csv.DictReader(handle))
        self.assertEqual(len(rows), 48)
        self.assertTrue(all(row["batch_id"] == str(self.batch_id) for row in rows))


class TestStep20CLI(Step20Fixture):

    def test_root_help_mentions_step20_and_batches(self):
        text = command_cli.command_help_text()
        self.assertIn("STEP 20", text)
        self.assertIn("batches list", text)
        self.assertIn("batches export", text)

    def test_batch_group_save_creates_persistent_batch(self):
        code, rendered = self.run_cli(
            "batch", "recipient", "RECIP-001", "--save"
        )
        self.assertEqual(code, 0)
        self.assertIn("Persistent batch_id: 1", rendered)
        self.assertEqual(len(database.list_batch_runs(self.db_path)), 1)
        self.assertEqual(len(database.list_analysis_runs(self.db_path)), 2)

    def test_no_save_creates_no_persistent_batch(self):
        code, _ = self.run_cli("batch", "recipient", "RECIP-001")
        self.assertEqual(code, 0)
        self.assertEqual(database.list_batch_runs(self.db_path), [])

    def test_save_rank_limit_persists_full_batch_and_metadata(self):
        code, rendered = self.run_cli(
            "batch", "recipient", "RECIP-001",
            "--sort-by", "donor-only",
            "--limit", "1",
            "--save",
        )
        self.assertEqual(code, 0)
        self.assertIn("displayed=1/2", rendered)
        saved = database.load_batch_run(self.db_path, 1)
        self.assertEqual(saved["pair_count"], 2)
        self.assertEqual(saved["display_limit"], 1)
        self.assertEqual(len(saved["items"]), 2)

    def test_batches_list_cli(self):
        self.run_cli("batch", "recipient", "RECIP-001", "--save")
        code, rendered = self.run_cli("batches", "list")
        self.assertEqual(code, 0)
        self.assertIn("PERSISTENT BATCH HISTORY", rendered)
        self.assertIn("batch_id=1", rendered)

    def test_batches_show_cli(self):
        self.run_cli("batch", "recipient", "RECIP-001", "--save")
        code, rendered = self.run_cli("batches", "show", "1")
        self.assertEqual(code, 0)
        self.assertIn("STEP 20 — PERSISTENT BATCH", rendered)
        self.assertIn("run_id=", rendered)
        self.assertIn("results=24", rendered)

    def test_batches_results_cli(self):
        self.run_cli(
            "batch", "recipient", "RECIP-001",
            "--sort-by", "donor-only", "--save"
        )
        code, rendered = self.run_cli("batches", "results", "1")
        self.assertEqual(code, 0)
        self.assertIn("RELOADED PERSISTENT BATCH RESULTS", rendered)
        self.assertIn("loaded entirely from SQLite", rendered)
        self.assertIn("software_rank", rendered)

    def test_batches_export_cli(self):
        self.run_cli("batch", "recipient", "RECIP-001", "--save")
        code, rendered = self.run_cli(
            "batches", "export", "1",
            "--format", "both",
            "--output-dir", str(self.export_dir),
        )
        self.assertEqual(code, 0)
        self.assertIn("PERSISTENT BATCH RE-EXPORT", rendered)
        self.assertTrue((self.export_dir / "batch_run_1.json").exists())
        self.assertTrue((self.export_dir / "batch_run_1.csv").exists())

    def test_batches_export_does_not_create_new_analysis_runs(self):
        self.run_cli("batch", "recipient", "RECIP-001", "--save")
        before = len(database.list_analysis_runs(self.db_path))
        code, _ = self.run_cli(
            "batches", "export", "1",
            "--format", "json",
            "--output-dir", str(self.export_dir),
        )
        after = len(database.list_analysis_runs(self.db_path))
        self.assertEqual(code, 0)
        self.assertEqual(before, after)

    def test_batches_missing_id_returns_error(self):
        code, rendered = self.run_cli("batches", "show", "999")
        self.assertEqual(code, 5)
        self.assertIn("batch_id=999", rendered)

    def test_step19_save_export_still_works_with_batch_id(self):
        code, rendered = self.run_cli(
            "batch", "recipient", "RECIP-001",
            "--sort-by", "donor-only",
            "--limit", "1",
            "--save",
            "--export",
            "--export-format", "json",
            "--export-dir", str(self.export_dir),
        )
        self.assertEqual(code, 0)
        self.assertIn("Persistent batch_id: 1", rendered)
        path = next(self.export_dir.glob("*.json"))
        with path.open("r", encoding="utf-8") as handle:
            payload = json.load(handle)
        self.assertEqual(payload["batch"]["batch_id"], 1)
        self.assertEqual(len(payload["pairs"]), 2)
