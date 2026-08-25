import tempfile
from pathlib import Path
import unittest

import batch_analysis
import batch_history
import command_cli
import database
from test_helpers import make_test_bundle


class Step28CLIFixture(unittest.TestCase):

    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        root = Path(self.temp.name)
        self.db = root / "step28.db"
        self.out = root / "exports"

        database.initialize_database(self.db)
        database.save_subject_typing(
            self.db, "DONOR-001", "DONOR", "3650", make_test_bundle()
        )
        database.save_subject_typing(
            self.db, "RECIP-001", "RECIPIENT", "3650", make_test_bundle()
        )

        batch1 = batch_analysis.run_batch_analysis(
            self.db, "recipient", "RECIP-001", save=False
        )
        self.batch1 = batch_history.persist_batch_with_runs(
            self.db, batch1
        )["batch_id"]

        batch2 = batch_analysis.run_batch_analysis(
            self.db, "recipient", "RECIP-001", save=False
        )
        self.batch2 = batch_history.persist_batch_with_runs(
            self.db, batch2
        )["batch_id"]

    def tearDown(self):
        self.temp.cleanup()

    def run_cli(self, *args):
        output = []
        code = command_cli.run_command_cli(
            ["--db", str(self.db), *args],
            output_func=output.append,
        )
        return code, "\n".join(output)


class TestStep28CLI(Step28CLIFixture):

    def test_compare_levels_recipient(self):
        code, text = self.run_cli(
            "compare", "levels", "recipient", "RECIP-001",
            "--level", "lgx", "--level", "G",
        )
        self.assertEqual(code, 0)
        self.assertIn("STEP 28", text)
        self.assertIn("Mode: LEVELS", text)

    def test_compare_levels_donor(self):
        code, text = self.run_cli(
            "compare", "levels", "donor", "DONOR-001",
            "--level", "lgx", "--level", "G",
        )
        self.assertEqual(code, 0)
        self.assertIn("Direction: donor", text)

    def test_compare_levels_candidate(self):
        code, text = self.run_cli(
            "compare", "levels", "recipient", "RECIP-001",
            "--candidate", "DONOR-001",
            "--level", "lgx", "--level", "G",
        )
        self.assertEqual(code, 0)
        self.assertIn("pairs=1", text)

    def test_compare_levels_locus(self):
        code, text = self.run_cli(
            "compare", "levels", "recipient", "RECIP-001",
            "--level", "lgx", "--level", "G",
            "--locus", "DRB1",
        )
        self.assertEqual(code, 0)
        self.assertIn("loci=DRB1", text)

    def test_compare_batches(self):
        code, text = self.run_cli(
            "compare", "batches",
            str(self.batch1), str(self.batch2),
        )
        self.assertEqual(code, 0)
        self.assertIn("Mode: BATCHES", text)

    def test_compare_export_bare_both(self):
        code, text = self.run_cli(
            "compare", "levels", "recipient", "RECIP-001",
            "--level", "lgx", "--level", "G",
            "--export",
            "--output-dir", str(self.out),
        )
        self.assertEqual(code, 0)
        self.assertIn("Format: BOTH", text)

    def test_compare_export_json(self):
        code, text = self.run_cli(
            "compare", "levels", "recipient", "RECIP-001",
            "--level", "lgx", "--level", "G",
            "--export", "json",
            "--output-dir", str(self.out),
        )
        self.assertEqual(code, 0)
        self.assertIn("Format: JSON", text)


    def test_compare_export_all(self):
        code, text = self.run_cli(
            "compare", "levels", "recipient", "RECIP-001",
            "--level", "lgx", "--level", "G",
            "--export", "all",
            "--output-dir", str(self.out),
        )
        self.assertEqual(code, 0)
        self.assertIn("Format: ALL", text)
        self.assertIn("JSON:", text)
        self.assertIn("CSV:", text)
        self.assertIn("HTML:", text)

    def test_compare_export_html(self):
        code, text = self.run_cli(
            "compare", "levels", "recipient", "RECIP-001",
            "--level", "lgx", "--level", "G",
            "--export", "html",
            "--output-dir", str(self.out),
        )
        self.assertEqual(code, 0)
        self.assertIn("Format: HTML", text)
        self.assertIn("HTML:", text)
        self.assertTrue(any(self.out.glob("*.html")))

    def test_report_step27_still_works(self):
        code, text = self.run_cli(
            "report", "recipient", "RECIP-001"
        )
        self.assertEqual(code, 0)
        self.assertIn("STEP 27", text)

    def test_stats_step26_still_works(self):
        code, text = self.run_cli(
            "stats", "recipient", "RECIP-001"
        )
        self.assertEqual(code, 0)
        self.assertIn("STEP 26", text)

    def test_root_help_mentions_step28(self):
        text = command_cli.command_help_text()
        self.assertIn("STEP 28", text)
        self.assertIn("compare levels", text)
        self.assertIn("compare batches", text)

    def test_output_encoding_error_is_reported_separately(self):
        output = []
        raised = {"done": False}

        def flaky_output(text):
            if not raised["done"]:
                raised["done"] = True
                raise UnicodeEncodeError(
                    "charmap",
                    "\u0394",
                    0,
                    1,
                    "character maps to <undefined>",
                )
            output.append(text)

        code = command_cli.run_command_cli(
            [
                "--db", str(self.db),
                "compare", "levels", "recipient", "RECIP-001",
                "--level", "lgx", "--level", "G",
            ],
            output_func=flaky_output,
        )

        text = "\n".join(output)
        self.assertEqual(code, 7)
        self.assertIn("OUTPUT ENCODING ERROR", text)
        self.assertNotIn("DATABASE / ANALYSIS ERROR", text)

    def test_io_error_is_reported_separately(self):
        output = []
        raised = {"done": False}

        def flaky_output(text):
            if not raised["done"]:
                raised["done"] = True
                raise OSError("simulated output stream failure")
            output.append(text)

        code = command_cli.run_command_cli(
            [
                "--db", str(self.db),
                "compare", "batches",
                str(self.batch1), str(self.batch2),
            ],
            output_func=flaky_output,
        )

        text = "\n".join(output)
        self.assertEqual(code, 7)
        self.assertIn("INPUT / OUTPUT ERROR", text)
        self.assertIn("simulated output stream failure", text)
        self.assertNotIn("DATABASE / ANALYSIS ERROR", text)


if __name__ == "__main__":
    unittest.main()
