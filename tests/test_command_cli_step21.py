import copy
import tempfile
from pathlib import Path
import unittest

import batch_analysis
import batch_history
import command_cli
import database

from test_helpers import make_test_bundle


class Step21CLIFixture(unittest.TestCase):

    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.db_path = Path(self.temp_dir.name) / "step21.db"
        database.initialize_database(self.db_path)

        database.save_subject_typing(
            self.db_path,
            "DONOR-001",
            "DONOR",
            "3650",
            make_test_bundle(),
        )
        database.save_subject_typing(
            self.db_path,
            "RECIP-001",
            "RECIPIENT",
            "3650",
            make_test_bundle(),
        )

        batch = batch_analysis.run_batch_analysis(
            self.db_path,
            "recipient",
            "RECIP-001",
            save=False,
        )
        batch_history.persist_batch_with_runs(
            self.db_path,
            batch,
        )

    def tearDown(self):
        self.temp_dir.cleanup()

    def run_cli(self, *args):
        output = []
        code = command_cli.run_command_cli(
            ["--db", str(self.db_path), *args],
            output_func=output.append,
        )
        return code, "\n".join(output)


class TestStep21CommandCLI(Step21CLIFixture):

    def test_list_is_step21_and_keeps_batch(self):
        code, text = self.run_cli("batches", "list")
        self.assertEqual(code, 0)
        self.assertIn("STEP 21", text)
        self.assertIn("batch_id=1", text)

    def test_search_finds_anchor(self):
        code, text = self.run_cli(
            "batches", "search", "RECIP-001"
        )
        self.assertEqual(code, 0)
        self.assertIn("batch_id=1", text)

    def test_direction_filter(self):
        code, text = self.run_cli(
            "batches", "list",
            "--direction", "recipient",
        )
        self.assertEqual(code, 0)
        self.assertIn("batch_id=1", text)

    def test_nonmatching_anchor_returns_empty(self):
        code, text = self.run_cli(
            "batches", "list",
            "--anchor", "RECIP-404",
        )
        self.assertEqual(code, 0)
        self.assertIn("No persistent batches found.", text)

    def test_latest(self):
        code, text = self.run_cli("batches", "latest")
        self.assertEqual(code, 0)
        self.assertIn("LATEST PERSISTENT BATCH", text)
        self.assertIn("batch_id=1", text)

    def test_summary(self):
        code, text = self.run_cli("batches", "summary")
        self.assertEqual(code, 0)
        self.assertIn("BATCH HISTORY SUMMARY", text)
        self.assertIn("Persistent batches: 1", text)

    def test_pagination(self):
        code, text = self.run_cli(
            "batches", "list",
            "--limit", "1",
            "--offset", "0",
        )
        self.assertEqual(code, 0)
        self.assertIn("Displayed batches: 1", text)

    def test_old_show_still_works(self):
        code, text = self.run_cli(
            "batches", "show", "1"
        )
        self.assertEqual(code, 0)
        self.assertIn("STEP 20 — PERSISTENT BATCH", text)

    def test_old_results_still_works(self):
        code, text = self.run_cli(
            "batches", "results", "1"
        )
        self.assertEqual(code, 0)
        self.assertIn(
            "RELOADED PERSISTENT BATCH RESULTS",
            text,
        )

    def test_root_help_mentions_step21(self):
        text = command_cli.command_help_text()
        self.assertIn("STEP 21", text)
        self.assertIn("batches search", text)
        self.assertIn("batches latest", text)
        self.assertIn("batches summary", text)


if __name__ == "__main__":
    unittest.main()
