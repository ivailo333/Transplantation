import unittest

import step21_batch_history as step21


def record(
    batch_id,
    direction="recipient",
    anchor="RECIP-001",
    version="3650",
    sort_level=None,
):
    return {
        "batch_id": batch_id,
        "direction": direction,
        "anchor_external_id": anchor,
        "anchor_typing_id": 2,
        "anchor_role": "RECIPIENT" if direction == "recipient" else "DONOR",
        "imgthla_version": version,
        "pair_count": 2,
        "analysis_result_count": 48,
        "sort_level": sort_level,
        "sort_metric": "donor-only" if sort_level else None,
        "sort_order": "asc" if sort_level else None,
        "requested_sort_order": "auto" if sort_level else None,
        "created_at": f"2026-08-19 21:12:{30 + batch_id}",
    }


class TestStep21Search(unittest.TestCase):
    def setUp(self):
        self.records = [
            record(3, anchor="RECIP-002", version="3650", sort_level="lgx"),
            record(2, anchor="RECIP-001", version="3650"),
            record(1, direction="donor", anchor="DONOR-001", version="3650"),
        ]

    def test_query_matches_anchor(self):
        result = step21.search_batch_history(
            self.records, query="RECIP-002"
        )
        self.assertEqual([r["batch_id"] for r in result], [3])

    def test_direction_filter(self):
        result = step21.search_batch_history(
            self.records, direction="donor"
        )
        self.assertEqual([r["batch_id"] for r in result], [1])

    def test_anchor_filter_is_case_insensitive_substring(self):
        result = step21.search_batch_history(
            self.records, anchor="recip-001"
        )
        self.assertEqual([r["batch_id"] for r in result], [2])

    def test_version_filter(self):
        result = step21.search_batch_history(
            self.records, imgthla_version="3650"
        )
        self.assertEqual(len(result), 3)

    def test_sort_level_filter(self):
        result = step21.search_batch_history(
            self.records, sort_level="LGX"
        )
        self.assertEqual([r["batch_id"] for r in result], [3])

    def test_invalid_direction_rejected(self):
        with self.assertRaises(step21.BatchHistoryManagementError):
            step21.search_batch_history(self.records, direction="other")


class TestStep21Pagination(unittest.TestCase):
    def setUp(self):
        self.records = [record(3), record(2), record(1)]

    def test_default_preserves_newest_first(self):
        result = step21.paginate_batch_history(self.records)
        self.assertEqual([r["batch_id"] for r in result], [3, 2, 1])

    def test_offset_and_limit(self):
        result = step21.paginate_batch_history(
            self.records, limit=1, offset=1
        )
        self.assertEqual([r["batch_id"] for r in result], [2])

    def test_zero_limit_returns_empty(self):
        self.assertEqual(
            step21.paginate_batch_history(self.records, limit=0),
            [],
        )

    def test_negative_offset_rejected(self):
        with self.assertRaises(step21.BatchHistoryManagementError):
            step21.paginate_batch_history(self.records, offset=-1)


class TestStep21Summary(unittest.TestCase):
    def test_summary_counts_administrative_data(self):
        records = [
            record(2),
            record(1, direction="donor", anchor="DONOR-001"),
        ]
        summary = step21.summarize_batch_history(records)

        self.assertEqual(summary["batch_count"], 2)
        self.assertEqual(summary["total_pairs"], 4)
        self.assertEqual(summary["total_analysis_results"], 96)
        self.assertEqual(summary["newest_batch_id"], 2)
        self.assertEqual(summary["oldest_batch_id"], 1)
        self.assertEqual(summary["directions"]["recipient"], 1)
        self.assertEqual(summary["directions"]["donor"], 1)

    def test_empty_summary(self):
        summary = step21.summarize_batch_history([])
        self.assertEqual(summary["batch_count"], 0)
        self.assertIsNone(summary["newest_batch_id"])
        self.assertIsNone(summary["oldest_batch_id"])


class TestStep21Rendering(unittest.TestCase):
    def test_render_contains_history_header(self):
        text = step21.render_batch_history([record(1)])
        self.assertIn("STEP 21", text)
        self.assertIn("batch_id=1", text)
        self.assertIn("RECIP-001", text)

    def test_empty_history_is_explicit(self):
        text = step21.render_batch_history([])
        self.assertIn("No persistent batches found.", text)

    def test_render_is_nonclinical(self):
        text = step21.render_batch_history([record(1)])
        self.assertIn("non-clinical", text)


if __name__ == "__main__":
    unittest.main()
