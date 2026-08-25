import tempfile
from pathlib import Path
import unittest

import command_cli
import database
from test_helpers import make_test_bundle


class Step24CLIFixture(unittest.TestCase):

    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        root = Path(self.temp.name)
        self.db = root / "step24.db"
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


class TestStep24CLI(Step24CLIFixture):

    def test_matrix_recipient(self):
        code, text = self.run_cli(
            "matrix",
            "recipient",
            "RECIP-001",
        )
        self.assertEqual(code, 0)
        self.assertIn(
            "STEP 24 — HLA COMPARISON MATRIX",
            text,
        )
        self.assertIn("DONOR-001", text)

    def test_matrix_donor(self):
        code, text = self.run_cli(
            "matrix",
            "donor",
            "DONOR-001",
        )
        self.assertEqual(code, 0)
        self.assertIn("RECIP-001", text)

    def test_matrix_locus_filter(self):
        code, text = self.run_cli(
            "matrix",
            "recipient",
            "RECIP-001",
            "--locus",
            "DRB1",
        )
        self.assertEqual(code, 0)
        self.assertIn("loci=DRB1", text)

    def test_matrix_candidate_filter(self):
        code, text = self.run_cli(
            "matrix",
            "recipient",
            "RECIP-001",
            "--candidate",
            "DONOR-001",
        )
        self.assertEqual(code, 0)
        self.assertIn("pairs=1", text)

    def test_matrix_export(self):
        code, text = self.run_cli(
            "matrix",
            "recipient",
            "RECIP-001",
            "--locus",
            "A",
            "--export",
            "--format",
            "both",
            "--output-dir",
            str(self.out),
        )
        self.assertEqual(code, 0)
        self.assertIn(
            "HLA MATRIX EXPORT COMPLETE",
            text,
        )

    def test_invalid_locus_controlled_error(self):
        code, text = self.run_cli(
            "matrix",
            "recipient",
            "RECIP-001",
            "--locus",
            "X",
        )
        self.assertEqual(code, 5)
        self.assertIn("Невалиден HLA locus", text)

    def test_sort_order_without_sort_by_errors(self):
        code, text = self.run_cli(
            "matrix",
            "recipient",
            "RECIP-001",
            "--sort-order",
            "desc",
        )
        self.assertEqual(code, 5)
        self.assertIn("--sort-order", text)

    def test_step23_pairs_still_works(self):
        code, text = self.run_cli(
            "pairs",
            "show",
            "DONOR-001",
            "RECIP-001",
            "--level",
            "lgx",
            "--locus",
            "A",
        )
        self.assertEqual(code, 0)
        self.assertIn("STEP 23", text)

    def test_root_help_mentions_matrix(self):
        help_text = command_cli.command_help_text()
        self.assertIn("STEP 24", help_text)
        self.assertIn("matrix recipient", help_text)
        self.assertIn("matrix batch", help_text)


if __name__ == "__main__":
    unittest.main()
