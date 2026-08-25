import copy
import unittest

import batch_selection


def row(candidate, shared, donor_only, recipient_only):
    summary = {}
    for level in ("canonical", "lgx", "G", "P"):
        summary[level] = {
            "shared_count": shared,
            "donor_only_count": donor_only,
            "recipient_only_count": recipient_only,
        }
    return {
        "candidate_external_id": candidate,
        "candidate_typing_id": 1,
        "donor_external_id": candidate,
        "donor_typing_id": 1,
        "recipient_external_id": "RECIP-001",
        "recipient_typing_id": 2,
        "imgthla_version": "3650",
        "summary": summary,
        "results": {},
        "run_id": None,
    }


class TestStep22Normalization(unittest.TestCase):

    def test_level_is_case_insensitive(self):
        self.assertEqual(
            batch_selection.normalize_selection_level("LGX"),
            "lgx",
        )
        self.assertEqual(
            batch_selection.normalize_selection_level("g"),
            "G",
        )

    def test_invalid_level_rejected(self):
        with self.assertRaises(
            batch_selection.BatchSelectionError
        ):
            batch_selection.normalize_selection_level("x")

    def test_negative_threshold_rejected(self):
        with self.assertRaises(
            batch_selection.BatchSelectionError
        ):
            batch_selection.normalize_nonnegative_int(
                -1, "threshold"
            )

    def test_duplicate_excludes_removed(self):
        self.assertEqual(
            batch_selection.normalize_excluded_ids(
                ["D1", "D1", "D2"]
            ),
            ["D1", "D2"],
        )


class TestStep22Selection(unittest.TestCase):

    def setUp(self):
        self.rows = [
            row("D1", 4, 8, 8),
            row("D2", 3, 9, 9),
            row("D3", 1, 11, 11),
        ]

    def test_max_donor_only(self):
        selected = batch_selection.select_batch_rows(
            self.rows,
            max_donor_only=9,
        )
        self.assertEqual(
            [r["candidate_external_id"] for r in selected],
            ["D1", "D2"],
        )

    def test_min_shared(self):
        selected = batch_selection.select_batch_rows(
            self.rows,
            min_shared=3,
        )
        self.assertEqual(
            [r["candidate_external_id"] for r in selected],
            ["D1", "D2"],
        )

    def test_max_recipient_only(self):
        selected = batch_selection.select_batch_rows(
            self.rows,
            max_recipient_only=8,
        )
        self.assertEqual(
            [r["candidate_external_id"] for r in selected],
            ["D1"],
        )

    def test_predicates_are_combined_with_and(self):
        selected = batch_selection.select_batch_rows(
            self.rows,
            max_donor_only=9,
            min_shared=4,
        )
        self.assertEqual(
            [r["candidate_external_id"] for r in selected],
            ["D1"],
        )

    def test_exclude_candidate(self):
        selected = batch_selection.select_batch_rows(
            self.rows,
            exclude_candidate_ids=["D2"],
        )
        self.assertEqual(
            [r["candidate_external_id"] for r in selected],
            ["D1", "D3"],
        )

    def test_order_is_preserved(self):
        selected = batch_selection.select_batch_rows(
            self.rows,
            max_donor_only=20,
        )
        self.assertEqual(
            [r["candidate_external_id"] for r in selected],
            ["D1", "D2", "D3"],
        )

    def test_input_not_mutated(self):
        original = copy.deepcopy(self.rows)
        batch_selection.select_batch_rows(
            self.rows,
            min_shared=1,
        )
        self.assertEqual(self.rows, original)


class TestStep22BatchView(unittest.TestCase):

    def test_apply_changes_pair_count_but_preserves_source_count(self):
        batch = {
            "pair_count": 3,
            "rows": [
                row("D1", 4, 8, 8),
                row("D2", 3, 9, 9),
                row("D3", 1, 11, 11),
            ],
        }

        selected = batch_selection.apply_batch_selection(
            batch,
            max_donor_only=9,
        )

        self.assertEqual(selected["pair_count"], 2)
        self.assertEqual(selected["source_pair_count"], 3)
        self.assertEqual(
            selected["step22_selection"]["rejected_pair_count"],
            1,
        )

    def test_selection_does_not_mutate_batch(self):
        batch = {
            "pair_count": 1,
            "rows": [row("D1", 4, 8, 8)],
        }
        original = copy.deepcopy(batch)

        batch_selection.apply_batch_selection(
            batch,
            min_shared=1,
        )

        self.assertEqual(batch, original)

    def test_render_summary_is_nonclinical(self):
        batch = {
            "pair_count": 1,
            "rows": [row("D1", 4, 8, 8)],
        }
        selected = batch_selection.apply_batch_selection(
            batch,
            max_donor_only=8,
        )
        text = batch_selection.render_selection_summary(
            selected["step22_selection"]
        )
        self.assertIn("STEP 22", text)
        self.assertIn("selected=1/1", text)


if __name__ == "__main__":
    unittest.main()
