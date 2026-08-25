import csv
import json
import tempfile
from pathlib import Path
import unittest

import cli
import command_cli
import database

from test_helpers import make_test_bundle


class Step15CommandFixture(unittest.TestCase):

    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.db_path = Path(self.temp_dir.name) / "step15.db"
        self.export_dir = Path(self.temp_dir.name) / "exports"

        database.initialize_database(self.db_path)

        pair = database.save_donor_recipient_typings(
            database_path=self.db_path,
            donor_external_id="DONOR-001",
            recipient_external_id="RECIP-001",
            imgthla_version="3650",
            donor_bundle=make_test_bundle(),
            recipient_bundle=make_test_bundle(),
        )

        run = database.create_analysis_run(
            database_path=self.db_path,
            donor_typing_id=pair["donor"]["typing_id"],
            recipient_typing_id=pair["recipient"]["typing_id"],
        )

        self.run_id = run["run_id"]

    def tearDown(self):
        self.temp_dir.cleanup()

    def run_cli(self, *args):
        output = []

        result = command_cli.run_command_cli(
            argv=[
                "--db",
                str(self.db_path),
                *args,
            ],
            output_func=output.append,
        )

        return result, "\n".join(output)


class TestStep15Detection(unittest.TestCase):

    def test_direct_command_style_is_detected(self):
        self.assertTrue(
            cli.uses_command_style(["db", "status"])
        )

    def test_command_style_after_db_option_is_detected(self):
        self.assertTrue(
            cli.uses_command_style(
                ["--db", "other.db", "subjects", "list"]
            )
        )

    def test_legacy_flag_is_not_command_style(self):
        self.assertFalse(
            cli.uses_command_style(["--db-status"])
        )

    def test_root_help_is_command_style(self):
        self.assertTrue(cli.uses_command_style(["--help"]))
        self.assertTrue(cli.uses_command_style(["-h"]))

    def test_root_help_after_db_option_is_command_style(self):
        self.assertTrue(
            cli.uses_command_style(["--db", "other.db", "--help"])
        )

    def test_empty_argv_is_not_command_style(self):
        self.assertFalse(cli.uses_command_style([]))


class TestStep15Help(unittest.TestCase):

    def test_root_help_returns_zero(self):
        output = []

        result = command_cli.run_command_cli(
            ["--help"],
            output_func=output.append,
        )

        rendered = "\n".join(output)

        self.assertEqual(result, 0)
        self.assertIn("STEP 15", rendered)
        self.assertIn("analyses export", rendered)

    def test_public_main_root_help_uses_command_help(self):
        output = []

        result = cli.main(
            ["--help"],
            output_func=output.append,
        )

        rendered = "\n".join(output)

        self.assertEqual(result, 0)
        self.assertIn("HLA donor/recipient comparison CLI", rendered)
        self.assertIn("compare levels", rendered)
        self.assertNotIn("hla_match_step13g_fixed.py", rendered)

    def test_missing_group_command_returns_two(self):
        output = []

        result = command_cli.run_command_cli(
            ["db"],
            output_func=output.append,
        )

        self.assertEqual(result, 2)
        self.assertTrue(
            any("missing command" in line for line in output)
        )

    def test_invalid_command_returns_two(self):
        output = []

        result = command_cli.run_command_cli(
            ["not-a-command"],
            output_func=output.append,
        )

        self.assertEqual(result, 2)
        self.assertTrue(
            any("ERROR:" in line for line in output)
        )


class TestStep15DatabaseCommands(Step15CommandFixture):

    def test_db_status(self):
        result, rendered = self.run_cli(
            "db",
            "status",
        )

        self.assertEqual(result, 0)
        self.assertIn("Schema version: 3 / 3", rendered)
        self.assertIn("Current: True", rendered)

    def test_db_migrate_is_idempotent(self):
        result, rendered = self.run_cli(
            "db",
            "migrate",
        )

        self.assertEqual(result, 0)
        self.assertIn("database already current", rendered)


class TestStep15SubjectTypingCommands(Step15CommandFixture):

    def test_subjects_list(self):
        result, rendered = self.run_cli(
            "subjects",
            "list",
        )

        self.assertEqual(result, 0)
        self.assertIn("DONOR-001", rendered)
        self.assertIn("RECIP-001", rendered)

    def test_typings_history(self):
        result, rendered = self.run_cli(
            "typings",
            "history",
            "DONOR-001",
        )

        self.assertEqual(result, 0)
        self.assertIn("HLA TYPING HISTORY", rendered)
        self.assertIn("typing_id=", rendered)

    def test_typings_show_latest(self):
        result, rendered = self.run_cli(
            "typings",
            "show",
            "DONOR-001",
        )

        self.assertEqual(result, 0)
        self.assertIn("DONOR-001", rendered)
        self.assertIn("CANONICAL:", rendered)


class TestStep15AnalysisCommands(Step15CommandFixture):

    def test_analyses_list(self):
        result, rendered = self.run_cli(
            "analyses",
            "list",
        )

        self.assertEqual(result, 0)
        self.assertIn(f"run_id={self.run_id}", rendered)

    def test_analyses_show(self):
        result, rendered = self.run_cli(
            "analyses",
            "show",
            str(self.run_id),
        )

        self.assertEqual(result, 0)
        self.assertIn(f"run_id: {self.run_id}", rendered)
        self.assertIn("DONOR-001", rendered)
        self.assertIn("RECIP-001", rendered)

    def test_analyses_run_saves_24_results(self):
        result, rendered = self.run_cli(
            "analyses",
            "run",
            str(self.run_id),
        )

        self.assertEqual(result, 0)
        self.assertIn("Saved analysis_result rows: 24", rendered)

        loaded = database.load_analysis_run(
            self.db_path,
            self.run_id,
        )
        self.assertEqual(
            loaded["analysis_result_count"],
            24,
        )

    def test_analyses_results_displays_saved_results(self):
        self.run_cli(
            "analyses",
            "run",
            str(self.run_id),
        )

        result, rendered = self.run_cli(
            "analyses",
            "results",
            str(self.run_id),
        )

        self.assertEqual(result, 0)
        self.assertIn("SAVED ANALYSIS RESULTS", rendered)
        self.assertIn("HLA-A", rendered)
        self.assertIn("CANONICAL", rendered)

    def test_analyses_create_can_link_latest_typings(self):
        result, rendered = self.run_cli(
            "analyses",
            "create",
            "DONOR-001",
            "RECIP-001",
        )

        self.assertEqual(result, 0)
        self.assertIn("ANALYSIS RUN SAVED", rendered)

        runs = database.list_analysis_runs(self.db_path)
        self.assertEqual(len(runs), 2)

    def test_analyses_export_json(self):
        self.run_cli(
            "analyses",
            "run",
            str(self.run_id),
        )

        result, rendered = self.run_cli(
            "analyses",
            "export",
            str(self.run_id),
            "--format",
            "json",
            "--output-dir",
            str(self.export_dir),
        )

        self.assertEqual(result, 0)
        self.assertIn("ANALYSIS EXPORT COMPLETE", rendered)

        json_path = (
            self.export_dir
            / f"analysis_run_{self.run_id}.json"
        )
        self.assertTrue(json_path.exists())

        with json_path.open("r", encoding="utf-8") as handle:
            payload = json.load(handle)

        self.assertEqual(payload["run"]["run_id"], self.run_id)

    def test_analyses_export_csv_has_24_rows(self):
        self.run_cli(
            "analyses",
            "run",
            str(self.run_id),
        )

        result, _ = self.run_cli(
            "analyses",
            "export",
            str(self.run_id),
            "--format",
            "csv",
            "--output-dir",
            str(self.export_dir),
        )

        self.assertEqual(result, 0)

        csv_path = (
            self.export_dir
            / f"analysis_run_{self.run_id}.csv"
        )

        with csv_path.open(
            "r",
            encoding="utf-8-sig",
            newline="",
        ) as handle:
            rows = list(csv.DictReader(handle))

        self.assertEqual(len(rows), 24)


class TestStep15BackwardCompatibility(Step15CommandFixture):

    def test_public_main_dispatches_command_style(self):
        output = []

        result = cli.main(
            argv=[
                "--db",
                str(self.db_path),
                "subjects",
                "list",
            ],
            output_func=output.append,
        )

        self.assertEqual(result, 0)
        self.assertTrue(
            any("DONOR-001" in line for line in output)
        )

    def test_public_main_keeps_legacy_db_status(self):
        output = []

        result = cli.main(
            argv=[
                "--db",
                str(self.db_path),
                "--db-status",
            ],
            output_func=output.append,
        )

        self.assertEqual(result, 0)
        self.assertTrue(
            any("Schema version: 3 / 3" in line for line in output)
        )
