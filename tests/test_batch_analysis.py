import copy
import tempfile
from pathlib import Path
import unittest

import batch_analysis
import command_cli
import database

from test_helpers import make_test_bundle


def different_bundle():
    bundle = copy.deepcopy(make_test_bundle())

    for representation in ("canonical", "lgx", "G", "P"):
        bundle[representation]["A"] = [
            f"A*30:01-{representation}",
            f"A*31:01-{representation}",
        ]

    # RAW is not used by the comparison engine but remains valid shape.
    bundle["raw"]["A"] = ["A*30:01", "A*31:01"]
    return bundle


class BatchFixture(unittest.TestCase):

    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.db_path = Path(self.temp_dir.name) / "step17.db"
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
            "DONOR-002",
            "DONOR",
            "3650",
            different_bundle(),
        )
        database.save_subject_typing(
            self.db_path,
            "RECIP-001",
            "RECIPIENT",
            "3650",
            make_test_bundle(),
        )
        database.save_subject_typing(
            self.db_path,
            "RECIP-002",
            "RECIPIENT",
            "3650",
            different_bundle(),
        )

    def tearDown(self):
        self.temp_dir.cleanup()


class TestStep17Summary(unittest.TestCase):

    def test_summary_has_four_levels(self):
        from hla_comparison import build_comparison_results_from_bundles

        results = build_comparison_results_from_bundles(
            make_test_bundle(),
            make_test_bundle(),
        )

        summary = batch_analysis.summarize_comparison_results(
            results
        )

        self.assertEqual(
            set(summary),
            {"canonical", "lgx", "G", "P"},
        )

    def test_full_match_totals_are_12_shared(self):
        from hla_comparison import build_comparison_results_from_bundles

        results = build_comparison_results_from_bundles(
            make_test_bundle(),
            make_test_bundle(),
        )

        summary = batch_analysis.summarize_comparison_results(
            results
        )

        for level in summary.values():
            self.assertEqual(level["shared_count"], 12)
            self.assertEqual(level["donor_only_count"], 0)
            self.assertEqual(level["recipient_only_count"], 0)

    def test_invalid_direction_is_rejected(self):
        with self.assertRaises(
            batch_analysis.BatchAnalysisError
        ):
            batch_analysis.normalize_batch_direction("sideways")


class TestStep17Planning(BatchFixture):

    def test_recipient_plan_finds_all_donors(self):
        plan = batch_analysis.build_batch_plan(
            self.db_path,
            "recipient",
            "RECIP-001",
        )

        self.assertEqual(plan["anchor_role"], "RECIPIENT")
        self.assertEqual(plan["candidate_role"], "DONOR")
        self.assertEqual(len(plan["eligible"]), 2)

    def test_donor_plan_finds_all_recipients(self):
        plan = batch_analysis.build_batch_plan(
            self.db_path,
            "donor",
            "DONOR-001",
        )

        self.assertEqual(plan["anchor_role"], "DONOR")
        self.assertEqual(plan["candidate_role"], "RECIPIENT")
        self.assertEqual(len(plan["eligible"]), 2)

    def test_candidate_filter_limits_batch(self):
        plan = batch_analysis.build_batch_plan(
            self.db_path,
            "recipient",
            "RECIP-001",
            candidate_external_ids=["DONOR-002"],
        )

        self.assertEqual(len(plan["eligible"]), 1)
        self.assertEqual(
            plan["eligible"][0]["candidate_external_id"],
            "DONOR-002",
        )

    def test_duplicate_candidate_ids_are_deduplicated(self):
        plan = batch_analysis.build_batch_plan(
            self.db_path,
            "recipient",
            "RECIP-001",
            candidate_external_ids=[
                "DONOR-001",
                "DONOR-001",
            ],
        )

        self.assertEqual(len(plan["eligible"]), 1)

    def test_wrong_role_candidate_is_rejected(self):
        with self.assertRaises(
            batch_analysis.BatchCandidateError
        ):
            batch_analysis.build_batch_plan(
                self.db_path,
                "recipient",
                "RECIP-001",
                candidate_external_ids=["RECIP-002"],
            )

    def test_missing_candidate_is_rejected(self):
        with self.assertRaises(
            batch_analysis.BatchCandidateError
        ):
            batch_analysis.build_batch_plan(
                self.db_path,
                "recipient",
                "RECIP-001",
                candidate_external_ids=["DONOR-404"],
            )

    def test_version_mismatch_candidate_is_skipped(self):
        database.save_subject_typing(
            self.db_path,
            "DONOR-OLD",
            "DONOR",
            "9999",
            make_test_bundle(),
        )

        plan = batch_analysis.build_batch_plan(
            self.db_path,
            "recipient",
            "RECIP-001",
        )

        skipped_ids = {
            item["external_id"]
            for item in plan["skipped"]
        }

        self.assertIn("DONOR-OLD", skipped_ids)
        self.assertEqual(len(plan["eligible"]), 2)


class TestStep17Execution(BatchFixture):

    def test_no_save_creates_no_analysis_runs(self):
        before = database.list_analysis_runs(self.db_path)

        batch = batch_analysis.run_batch_analysis(
            self.db_path,
            "recipient",
            "RECIP-001",
            save=False,
        )

        after = database.list_analysis_runs(self.db_path)

        self.assertEqual(before, after)
        self.assertEqual(batch["pair_count"], 2)
        self.assertTrue(
            all(row["run_id"] is None for row in batch["rows"])
        )

    def test_recipient_batch_computes_two_pairs(self):
        batch = batch_analysis.run_batch_analysis(
            self.db_path,
            "recipient",
            "RECIP-001",
        )

        self.assertEqual(batch["pair_count"], 2)
        self.assertEqual(
            {
                row["donor_external_id"]
                for row in batch["rows"]
            },
            {"DONOR-001", "DONOR-002"},
        )

    def test_donor_batch_computes_two_pairs(self):
        batch = batch_analysis.run_batch_analysis(
            self.db_path,
            "donor",
            "DONOR-001",
        )

        self.assertEqual(batch["pair_count"], 2)
        self.assertEqual(
            {
                row["recipient_external_id"]
                for row in batch["rows"]
            },
            {"RECIP-001", "RECIP-002"},
        )

    def test_save_creates_one_run_per_pair(self):
        batch = batch_analysis.run_batch_analysis(
            self.db_path,
            "recipient",
            "RECIP-001",
            save=True,
        )

        runs = database.list_analysis_runs(self.db_path)

        self.assertEqual(len(runs), 2)
        self.assertTrue(
            all(row["run_id"] is not None for row in batch["rows"])
        )
        self.assertTrue(
            all(run["analysis_result_count"] == 24 for run in runs)
        )

    def test_saved_batch_results_can_be_loaded(self):
        batch = batch_analysis.run_batch_analysis(
            self.db_path,
            "recipient",
            "RECIP-001",
            candidate_external_ids=["DONOR-001"],
            save=True,
        )

        run_id = batch["rows"][0]["run_id"]
        loaded = database.load_analysis_results(
            self.db_path,
            run_id,
        )

        self.assertEqual(loaded["row_count"], 24)

    def test_summary_distinguishes_full_and_nonfull_match(self):
        batch = batch_analysis.run_batch_analysis(
            self.db_path,
            "recipient",
            "RECIP-001",
        )

        by_donor = {
            row["donor_external_id"]: row
            for row in batch["rows"]
        }

        self.assertEqual(
            by_donor["DONOR-001"]["summary"]["canonical"][
                "donor_only_count"
            ],
            0,
        )
        self.assertGreater(
            by_donor["DONOR-002"]["summary"]["canonical"][
                "donor_only_count"
            ],
            0,
        )


class TestStep17AtomicSave(BatchFixture):

    def test_atomic_batch_save_rolls_back_first_pair_if_second_fails(self):
        from hla_comparison import build_comparison_results_from_bundles

        good_results = build_comparison_results_from_bundles(
            make_test_bundle(),
            make_test_bundle(),
        )

        donor1 = database.load_subject_typing(
            self.db_path,
            "DONOR-001",
            subject_type="DONOR",
        )
        recipient1 = database.load_subject_typing(
            self.db_path,
            "RECIP-001",
            subject_type="RECIPIENT",
        )

        pairs = [
            {
                "donor_typing_id": donor1["typing"]["typing_id"],
                "recipient_typing_id": (
                    recipient1["typing"]["typing_id"]
                ),
                "imgthla_version": "3650",
                "results": good_results,
            },
            {
                "donor_typing_id": donor1["typing"]["typing_id"],
                "recipient_typing_id": 999999,
                "imgthla_version": "3650",
                "results": good_results,
            },
        ]

        with self.assertRaises(database.TypingNotFoundError):
            database.save_batch_analysis_runs(
                self.db_path,
                pairs,
            )

        self.assertEqual(
            database.list_analysis_runs(self.db_path),
            [],
        )

    def test_empty_atomic_batch_is_rejected(self):
        with self.assertRaises(ValueError):
            database.save_batch_analysis_runs(
                self.db_path,
                [],
            )


class TestStep17CLI(BatchFixture):

    def run_cli(self, *args):
        output = []

        code = command_cli.run_command_cli(
            [
                "--db",
                str(self.db_path),
                *args,
            ],
            output_func=output.append,
        )

        return code, "\n".join(output)

    def test_root_help_mentions_step17_and_batch(self):
        text = command_cli.command_help_text()

        self.assertIn("STEP 17", text)
        self.assertIn("batch recipient", text)
        self.assertIn("batch donor", text)

    def test_batch_group_help(self):
        text = command_cli._group_help("batch")

        self.assertIn("NO SAVE", text)
        self.assertIn("--save", text)

    def test_cli_recipient_batch_defaults_to_no_save(self):
        code, rendered = self.run_cli(
            "batch",
            "recipient",
            "RECIP-001",
        )

        self.assertEqual(code, 0)
        self.assertIn("STEP 17", rendered)
        self.assertIn("Mode: NO SAVE", rendered)
        self.assertIn("run_id=not-saved", rendered)
        self.assertEqual(
            database.list_analysis_runs(self.db_path),
            [],
        )

    def test_cli_recipient_batch_save(self):
        code, rendered = self.run_cli(
            "batch",
            "recipient",
            "RECIP-001",
            "--candidate",
            "DONOR-001",
            "--save",
        )

        self.assertEqual(code, 0)
        self.assertIn("Mode: SAVE", rendered)
        self.assertIn("run_id=", rendered)

        runs = database.list_analysis_runs(self.db_path)
        self.assertEqual(len(runs), 1)
        self.assertEqual(runs[0]["analysis_result_count"], 24)

    def test_cli_donor_batch_candidate_filter(self):
        code, rendered = self.run_cli(
            "batch",
            "donor",
            "DONOR-001",
            "--candidate",
            "RECIP-002",
        )

        self.assertEqual(code, 0)
        self.assertIn("RECIP-002", rendered)
        self.assertNotIn("RECIP-001 (typing", rendered)

    def test_cli_wrong_candidate_role_returns_error(self):
        code, rendered = self.run_cli(
            "batch",
            "recipient",
            "RECIP-001",
            "--candidate",
            "RECIP-002",
        )

        self.assertEqual(code, 5)
        self.assertIn("DATABASE / ANALYSIS ERROR", rendered)

    def test_cli_output_warns_not_clinical_score(self):
        code, rendered = self.run_cli(
            "batch",
            "recipient",
            "RECIP-001",
            "--candidate",
            "DONOR-001",
        )

        self.assertEqual(code, 0)
        self.assertIn("NOT a clinical", rendered)
