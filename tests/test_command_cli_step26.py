import tempfile
from pathlib import Path
import unittest

import command_cli
import database
from test_helpers import make_test_bundle


class Step26CLIFixture(unittest.TestCase):

    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        root = Path(self.temp.name)
        self.db = root / "step26.db"
        self.out = root / "exports"

        database.initialize_database(self.db)
        database.save_subject_typing(
            self.db,
            "DONOR-001",
            "DONOR",
            "3650",
            make_test_bundle(),
        )
        database.save_subject_typing(
            self.db,
            "DONOR-002",
            "DONOR",
            "3650",
            make_test_bundle(),
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

    def run_cli(self, *args):
        output = []
        code = command_cli.run_command_cli(
            ["--db", str(self.db), *args],
            output_func=output.append,
        )
        return code, "\n".join(output)


class TestStep26CLI(Step26CLIFixture):

    def test_stats_recipient(self):
        code, text = self.run_cli(
            "stats",
            "recipient",
            "RECIP-001",
        )
        self.assertEqual(code, 0)
        self.assertIn("STEP 26", text)
        self.assertIn("PAIR TOTAL COUNT STATISTICS", text)

    def test_stats_donor(self):
        code, text = self.run_cli(
            "stats",
            "donor",
            "DONOR-001",
        )
        self.assertEqual(code, 0)
        self.assertIn("Direction: donor", text)
        self.assertIn("pairs=1", text)

    def test_stats_locus_filter(self):
        code, text = self.run_cli(
            "stats",
            "recipient",
            "RECIP-001",
            "--locus",
            "DRB1",
        )
        self.assertEqual(code, 0)
        self.assertIn("loci=DRB1", text)

    def test_stats_candidate_filter(self):
        code, text = self.run_cli(
            "stats",
            "recipient",
            "RECIP-001",
            "--candidate",
            "DONOR-001",
        )
        self.assertEqual(code, 0)
        self.assertIn("pairs=1", text)

    def test_stats_details(self):
        code, text = self.run_cli(
            "stats",
            "recipient",
            "RECIP-001",
            "--details",
        )
        self.assertEqual(code, 0)
        self.assertIn("PAIR DETAILS", text)

    def test_stats_sort(self):
        code, text = self.run_cli(
            "stats",
            "recipient",
            "RECIP-001",
            "--sort-by",
            "donor-only",
        )
        self.assertEqual(code, 0)
        self.assertIn("STEP 26", text)

    def test_stats_export(self):
        code, text = self.run_cli(
            "stats",
            "recipient",
            "RECIP-001",
            "--export",
            "--format",
            "both",
            "--output-dir",
            str(self.out),
        )
        self.assertEqual(code, 0)
        self.assertIn(
            "COMPARISON STATISTICS EXPORT COMPLETE",
            text,
        )

    def test_summary_step25_still_works(self):
        code, text = self.run_cli(
            "summary",
            "recipient",
            "RECIP-001",
        )
        self.assertEqual(code, 0)
        self.assertIn("STEP 25", text)

    def test_matrix_step24_still_works(self):
        code, text = self.run_cli(
            "matrix",
            "recipient",
            "RECIP-001",
        )
        self.assertEqual(code, 0)
        self.assertIn("STEP 24", text)

    def test_root_help_mentions_step26(self):
        text = command_cli.command_help_text()
        self.assertIn("STEP 26", text)
        self.assertIn("stats recipient", text)
        self.assertIn("stats batch", text)


if __name__ == "__main__":
    unittest.main()
