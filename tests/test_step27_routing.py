import unittest

import cli


class TestStep27Routing(unittest.TestCase):

    def test_report_registered(self):
        self.assertIn(
            "report",
            cli.STEP15_COMMAND_GROUPS,
        )

    def test_report_recipient_command_style(self):
        self.assertTrue(
            cli.uses_command_style(
                ["report", "recipient", "RECIP-001"]
            )
        )

    def test_report_batch_command_style(self):
        self.assertTrue(
            cli.uses_command_style(
                ["report", "batch", "3"]
            )
        )

    def test_stats_still_registered(self):
        self.assertIn(
            "stats",
            cli.STEP15_COMMAND_GROUPS,
        )

    def test_summary_still_registered(self):
        self.assertIn(
            "summary",
            cli.STEP15_COMMAND_GROUPS,
        )

    def test_matrix_still_registered(self):
        self.assertIn(
            "matrix",
            cli.STEP15_COMMAND_GROUPS,
        )

    def test_pairs_still_registered(self):
        self.assertIn(
            "pairs",
            cli.STEP15_COMMAND_GROUPS,
        )


if __name__ == "__main__":
    unittest.main()
