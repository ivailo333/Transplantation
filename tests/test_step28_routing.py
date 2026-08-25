import unittest

import cli


class TestStep28Routing(unittest.TestCase):

    def test_compare_registered(self):
        self.assertIn("compare", cli.STEP15_COMMAND_GROUPS)

    def test_compare_levels_command_style(self):
        self.assertTrue(
            cli.uses_command_style(
                ["compare", "levels", "recipient", "RECIP-001"]
            )
        )

    def test_compare_batches_command_style(self):
        self.assertTrue(
            cli.uses_command_style(
                ["compare", "batches", "1", "2"]
            )
        )

    def test_report_still_registered(self):
        self.assertIn("report", cli.STEP15_COMMAND_GROUPS)

    def test_stats_still_registered(self):
        self.assertIn("stats", cli.STEP15_COMMAND_GROUPS)

    def test_summary_still_registered(self):
        self.assertIn("summary", cli.STEP15_COMMAND_GROUPS)

    def test_matrix_still_registered(self):
        self.assertIn("matrix", cli.STEP15_COMMAND_GROUPS)

    def test_pairs_still_registered(self):
        self.assertIn("pairs", cli.STEP15_COMMAND_GROUPS)


if __name__ == "__main__":
    unittest.main()
