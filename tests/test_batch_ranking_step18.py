import copy
import tempfile
from pathlib import Path
import unittest

import batch_analysis
import batch_ranking
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


def synthetic_row(
    candidate_id,
    donor_only,
    shared,
    recipient_only=None,
):
    if recipient_only is None:
        recipient_only = donor_only

    summary = {}

    for level in ("canonical", "lgx", "G", "P"):
        summary[level] = {
            "shared_count": shared,
            "donor_only_count": donor_only,
            "recipient_only_count": recipient_only,
        }

    return {
        "candidate_external_id": candidate_id,
        "candidate_typing_id": 1,
        "donor_external_id": candidate_id,
        "donor_typing_id": 1,
        "recipient_external_id": "RECIP-001",
        "recipient_typing_id": 10,
        "imgthla_version": "3650",
        "results": {},
        "summary": summary,
        "run_id": None,
    }


class TestStep18Normalization(unittest.TestCase):

    def test_sort_levels_are_case_insensitive(self):
        self.assertEqual(
            batch_ranking.normalize_sort_level("CANONICAL"),
            "canonical",
        )
        self.assertEqual(
            batch_ranking.normalize_sort_level("LGX"),
            "lgx",
        )
        self.assertEqual(
            batch_ranking.normalize_sort_level("g"),
            "G",
        )
        self.assertEqual(
            batch_ranking.normalize_sort_level("p"),
            "P",
        )

    def test_invalid_sort_level_is_rejected(self):
        with self.assertRaises(
            batch_ranking.BatchRankingError
        ):
            batch_ranking.normalize_sort_level("ARD99")

    def test_metric_aliases_are_normalized(self):
        self.assertEqual(
            batch_ranking.normalize_sort_metric(
                "donor_only_count"
            ),
            "donor-only",
        )
        self.assertEqual(
            batch_ranking.normalize_sort_metric(
                "recipient_only"
            ),
            "recipient-only",
        )
        self.assertEqual(
            batch_ranking.normalize_sort_metric("shared_count"),
            "shared",
        )

    def test_invalid_metric_is_rejected(self):
        with self.assertRaises(
            batch_ranking.BatchRankingError
        ):
            batch_ranking.normalize_sort_metric("clinical-score")

    def test_auto_order_for_shared_is_desc(self):
        self.assertEqual(
            batch_ranking.resolve_sort_order(
                "shared",
                "auto",
            ),
            "desc",
        )

    def test_auto_order_for_donor_only_is_asc(self):
        self.assertEqual(
            batch_ranking.resolve_sort_order(
                "donor-only",
                "auto",
            ),
            "asc",
        )

    def test_auto_order_for_recipient_only_is_asc(self):
        self.assertEqual(
            batch_ranking.resolve_sort_order(
                "recipient-only",
                "auto",
            ),
            "asc",
        )

    def test_invalid_order_is_rejected(self):
        with self.assertRaises(
            batch_ranking.BatchRankingError
        ):
            batch_ranking.normalize_sort_order("best-first")

    def test_zero_display_limit_is_rejected(self):
        with self.assertRaises(
            batch_ranking.BatchRankingError
        ):
            batch_ranking.normalize_display_limit(0)


class TestStep18Ordering(unittest.TestCase):

    def setUp(self):
        self.rows = [
            synthetic_row("DONOR-B", 4, 8),
            synthetic_row("DONOR-A", 0, 12),
            synthetic_row("DONOR-C", 2, 10),
        ]

    def test_donor_only_auto_sorts_ascending(self):
        ordered = batch_ranking.order_batch_rows(
            self.rows,
            level="lgx",
            metric="donor-only",
        )

        self.assertEqual(
            [
                row["candidate_external_id"]
                for row in ordered
            ],
            ["DONOR-A", "DONOR-C", "DONOR-B"],
        )

    def test_shared_auto_sorts_descending(self):
        ordered = batch_ranking.order_batch_rows(
            self.rows,
            level="G",
            metric="shared",
        )

        self.assertEqual(
            [
                row["candidate_external_id"]
                for row in ordered
            ],
            ["DONOR-A", "DONOR-C", "DONOR-B"],
        )

    def test_explicit_desc_overrides_auto(self):
        ordered = batch_ranking.order_batch_rows(
            self.rows,
            metric="donor-only",
            order="desc",
        )

        self.assertEqual(
            [
                row["candidate_external_id"]
                for row in ordered
            ],
            ["DONOR-B", "DONOR-C", "DONOR-A"],
        )

    def test_ties_use_deterministic_external_id_order(self):
        rows = [
            synthetic_row("DONOR-Z", 2, 10),
            synthetic_row("DONOR-A", 2, 10),
        ]

        ordered = batch_ranking.order_batch_rows(
            rows,
            metric="donor-only",
        )

        self.assertEqual(
            [
                row["candidate_external_id"]
                for row in ordered
            ],
            ["DONOR-A", "DONOR-Z"],
        )

    def test_equal_primary_values_receive_same_software_rank(self):
        rows = [
            synthetic_row("DONOR-Z", 2, 10),
            synthetic_row("DONOR-A", 2, 10),
            synthetic_row("DONOR-B", 4, 8),
        ]

        ordered = batch_ranking.order_batch_rows(
            rows,
            metric="donor-only",
        )

        self.assertEqual(
            [
                row["software_order"]["rank"]
                for row in ordered
            ],
            [1, 1, 3],
        )

    def test_positions_are_always_sequential(self):
        ordered = batch_ranking.order_batch_rows(
            self.rows,
            metric="donor-only",
        )

        self.assertEqual(
            [
                row["software_order"]["position"]
                for row in ordered
            ],
            [1, 2, 3],
        )

    def test_input_rows_are_not_mutated(self):
        original = copy.deepcopy(self.rows)

        batch_ranking.order_batch_rows(
            self.rows,
            metric="donor-only",
        )

        self.assertEqual(self.rows, original)

    def test_display_limit_applies_after_ordering(self):
        ordered = batch_ranking.order_batch_rows(
            self.rows,
            metric="donor-only",
            display_limit=2,
        )

        self.assertEqual(len(ordered), 2)
        self.assertEqual(
            ordered[0]["candidate_external_id"],
            "DONOR-A",
        )
        self.assertEqual(
            ordered[1]["candidate_external_id"],
            "DONOR-C",
        )


class TestStep18ApplyBatchOrdering(unittest.TestCase):

    def test_apply_adds_metadata_and_preserves_total_pair_count(self):
        batch = {
            "save": False,
            "pair_count": 3,
            "rows": [
                synthetic_row("DONOR-B", 4, 8),
                synthetic_row("DONOR-A", 0, 12),
                synthetic_row("DONOR-C", 2, 10),
            ],
        }

        ordered = batch_ranking.apply_batch_ordering(
            batch,
            metric="donor-only",
            display_limit=2,
        )

        self.assertEqual(ordered["pair_count"], 3)
        self.assertEqual(
            ordered["displayed_pair_count"],
            2,
        )
        self.assertEqual(
            ordered["software_ordering"]["total_pair_count"],
            3,
        )
        self.assertEqual(
            ordered["software_ordering"]["displayed_pair_count"],
            2,
        )

    def test_apply_does_not_mutate_original_batch(self):
        batch = {
            "save": False,
            "pair_count": 2,
            "rows": [
                synthetic_row("DONOR-B", 4, 8),
                synthetic_row("DONOR-A", 0, 12),
            ],
        }
        original = copy.deepcopy(batch)

        batch_ranking.apply_batch_ordering(
            batch,
            metric="shared",
        )

        self.assertEqual(batch, original)


class Step18DatabaseFixture(unittest.TestCase):

    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.db_path = Path(self.temp_dir.name) / "step18.db"
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
            [
                "--db",
                str(self.db_path),
                *args,
            ],
            output_func=output.append,
        )

        return code, "\n".join(output)


class TestStep18Integration(Step18DatabaseFixture):

    def test_batch_then_ordering_places_full_match_first(self):
        batch = batch_analysis.run_batch_analysis(
            self.db_path,
            "recipient",
            "RECIP-001",
        )

        ordered = batch_ranking.apply_batch_ordering(
            batch,
            level="lgx",
            metric="donor-only",
        )

        self.assertEqual(
            ordered["rows"][0]["candidate_external_id"],
            "DONOR-FULL",
        )

    def test_default_step17_batch_still_has_no_ordering_metadata(self):
        batch = batch_analysis.run_batch_analysis(
            self.db_path,
            "recipient",
            "RECIP-001",
        )

        self.assertNotIn(
            "software_ordering",
            batch,
        )

    def test_sorting_no_save_creates_no_analysis_runs(self):
        batch = batch_analysis.run_batch_analysis(
            self.db_path,
            "recipient",
            "RECIP-001",
            save=False,
        )

        batch_ranking.apply_batch_ordering(
            batch,
            metric="donor-only",
        )

        self.assertEqual(
            database.list_analysis_runs(self.db_path),
            [],
        )


class TestStep18CLI(Step18DatabaseFixture):

    def test_root_help_mentions_step18_and_old_steps(self):
        text = command_cli.command_help_text()

        self.assertIn("STEP 18", text)
        self.assertIn("STEP 17", text)
        self.assertIn("STEP 16", text)
        self.assertIn("STEP 15", text)

    def test_batch_help_mentions_sort_options_and_nonclinical_warning(self):
        text = command_cli._group_help("batch")

        self.assertIn("--sort-by", text)
        self.assertIn("--sort-level", text)
        self.assertIn("--sort-order", text)
        self.assertIn("--limit", text)
        self.assertIn("NOT a clinical", text)

    def test_cli_sort_donor_only_outputs_step18(self):
        code, rendered = self.run_cli(
            "batch",
            "recipient",
            "RECIP-001",
            "--sort-by",
            "donor-only",
            "--sort-level",
            "lgx",
        )

        self.assertEqual(code, 0)
        self.assertIn("STEP 18", rendered)
        self.assertIn(
            "metric=donor_only_count",
            rendered,
        )
        self.assertIn(
            "[position=1",
            rendered,
        )

    def test_cli_sort_shared_uses_desc_auto(self):
        code, rendered = self.run_cli(
            "batch",
            "recipient",
            "RECIP-001",
            "--sort-by",
            "shared",
            "--sort-level",
            "G",
        )

        self.assertEqual(code, 0)
        self.assertIn("order=DESC", rendered)

    def test_cli_full_match_is_displayed_before_two_locus_mismatch(self):
        code, rendered = self.run_cli(
            "batch",
            "recipient",
            "RECIP-001",
            "--sort-by",
            "donor-only",
        )

        self.assertEqual(code, 0)
        self.assertLess(
            rendered.index("DONOR-FULL"),
            rendered.index("DONOR-AB"),
        )

    def test_cli_limit_displays_only_one_pair(self):
        code, rendered = self.run_cli(
            "batch",
            "recipient",
            "RECIP-001",
            "--sort-by",
            "donor-only",
            "--limit",
            "1",
        )

        self.assertEqual(code, 0)
        self.assertIn("displayed=1/3", rendered)
        self.assertIn("DONOR-FULL", rendered)
        self.assertNotIn("DONOR-A (typing", rendered)
        self.assertNotIn("DONOR-AB (typing", rendered)

    def test_cli_limit_without_sort_by_returns_error(self):
        code, rendered = self.run_cli(
            "batch",
            "recipient",
            "RECIP-001",
            "--limit",
            "1",
        )

        self.assertEqual(code, 5)
        self.assertIn(
            "require --sort-by",
            rendered,
        )

    def test_cli_sort_level_without_sort_by_returns_error(self):
        code, rendered = self.run_cli(
            "batch",
            "recipient",
            "RECIP-001",
            "--sort-level",
            "P",
        )

        self.assertEqual(code, 5)
        self.assertIn(
            "require --sort-by",
            rendered,
        )

    def test_cli_invalid_sort_level_returns_error(self):
        code, rendered = self.run_cli(
            "batch",
            "recipient",
            "RECIP-001",
            "--sort-by",
            "donor-only",
            "--sort-level",
            "BAD",
        )

        self.assertEqual(code, 5)
        self.assertIn(
            "Невалидно sort level",
            rendered,
        )

    def test_cli_default_batch_remains_step17_output(self):
        code, rendered = self.run_cli(
            "batch",
            "recipient",
            "RECIP-001",
        )

        self.assertEqual(code, 0)
        self.assertIn(
            "STEP 17 — BATCH",
            rendered,
        )
        self.assertNotIn(
            "Software ordering:",
            rendered,
        )

    def test_save_with_display_limit_persists_all_eligible_pairs(self):
        code, rendered = self.run_cli(
            "batch",
            "recipient",
            "RECIP-001",
            "--sort-by",
            "donor-only",
            "--limit",
            "1",
            "--save",
        )

        self.assertEqual(code, 0)
        self.assertIn("displayed=1/3", rendered)
        self.assertIn(
            "ALL eligible pairs were saved",
            rendered,
        )

        runs = database.list_analysis_runs(
            self.db_path
        )

        self.assertEqual(len(runs), 3)
        self.assertTrue(
            all(
                run["analysis_result_count"] == 24
                for run in runs
            )
        )

    def test_cli_output_explicitly_says_ordering_is_nonclinical(self):
        code, rendered = self.run_cli(
            "batch",
            "recipient",
            "RECIP-001",
            "--sort-by",
            "donor-only",
        )

        self.assertEqual(code, 0)
        self.assertIn(
            "deterministic sort",
            rendered,
        )
        self.assertIn(
            "NOT a clinical",
            rendered,
        )
