import copy
import json
import tempfile
from pathlib import Path
import unittest

import command_cli
import database

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


class Step22CLIFixture(unittest.TestCase):

    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        root = Path(self.temp_dir.name)
        self.db_path = root / "step22.db"
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
            "DONOR-AB",
            "DONOR",
            "3650",
            bundle_with_mismatched_loci("A", "B"),
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

    def run_cli(self, *args):
        output = []
        code = command_cli.run_command_cli(
            ["--db", str(self.db_path), *args],
            output_func=output.append,
        )
        return code, "\n".join(output)


class TestStep22CLI(Step22CLIFixture):

    def test_filter_by_max_donor_only(self):
        code, text = self.run_cli(
            "batch", "recipient", "RECIP-001",
            "--filter-level", "lgx",
            "--max-donor-only", "2",
        )
        self.assertEqual(code, 0)
        self.assertIn("STEP 22 selection:", text)
        self.assertIn("selected=", text)

    def test_exclude_candidate(self):
        code, text = self.run_cli(
            "batch", "recipient", "RECIP-001",
            "--exclude-candidate", "DONOR-AB",
        )
        self.assertEqual(code, 0)
        self.assertNotIn("DONOR-AB (typing", text)

    def test_filter_level_without_predicate_errors(self):
        code, text = self.run_cli(
            "batch", "recipient", "RECIP-001",
            "--filter-level", "lgx",
        )
        self.assertEqual(code, 5)
        self.assertIn(
            "requires at least one STEP 22 selection predicate",
            text,
        )

    def test_export_selection_requires_export(self):
        code, text = self.run_cli(
            "batch", "recipient", "RECIP-001",
            "--max-donor-only", "2",
            "--export-selection",
        )
        self.assertEqual(code, 5)
        self.assertIn(
            "--export-selection requires --export",
            text,
        )

    def test_save_persists_all_pairs_even_when_display_selected(self):
        code, text = self.run_cli(
            "batch", "recipient", "RECIP-001",
            "--max-donor-only", "0",
            "--save",
        )
        self.assertEqual(code, 0)
        self.assertIn(
            "--save still persists all eligible computed pairs",
            text,
        )

        runs = database.list_analysis_runs(self.db_path)
        self.assertEqual(len(runs), 3)

    def test_normal_export_remains_full_batch(self):
        code, text = self.run_cli(
            "batch", "recipient", "RECIP-001",
            "--max-donor-only", "0",
            "--export",
            "--export-format", "json",
            "--export-dir", str(self.export_dir),
        )
        self.assertEqual(code, 0)
        self.assertIn(
            "STEP 22 export scope: FULL computed batch",
            text,
        )

        path = next(self.export_dir.glob("*.json"))
        payload = json.loads(path.read_text(encoding="utf-8"))
        self.assertEqual(len(payload["pairs"]), 3)

    def test_export_selection_exports_selected_subset(self):
        code, text = self.run_cli(
            "batch", "recipient", "RECIP-001",
            "--max-donor-only", "0",
            "--export",
            "--export-selection",
            "--export-format", "json",
            "--export-dir", str(self.export_dir),
        )
        self.assertEqual(code, 0)
        self.assertIn(
            "STEP 22 export scope: SELECTED pairs only",
            text,
        )

        path = next(self.export_dir.glob("*.json"))
        payload = json.loads(path.read_text(encoding="utf-8"))
        self.assertEqual(len(payload["pairs"]), 1)

    def test_step21_history_still_works(self):
        code, text = self.run_cli("batches", "list")
        self.assertEqual(code, 0)
        self.assertIn("STEP 21", text)

    def test_root_help_mentions_step22(self):
        text = command_cli.command_help_text()
        self.assertIn("STEP 22", text)
        self.assertIn("--max-donor-only", text)
        self.assertIn("--export-selection", text)


if __name__ == "__main__":
    unittest.main()
