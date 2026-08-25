import unittest

import cli


class TestStep26Routing(unittest.TestCase):

    def test_stats_is_registered_command_group(self):
        self.assertIn("stats", cli.STEP15_COMMAND_GROUPS)

    def test_stats_recipient_is_command_style(self):
        self.assertTrue(
            cli.uses_command_style(
                ["stats", "recipient", "RECIP-001"]
            )
        )

    def test_stats_batch_is_command_style(self):
        self.assertTrue(
            cli.uses_command_style(
                ["stats", "batch", "3"]
            )
        )

    def test_summary_remains_registered(self):
        self.assertIn("summary", cli.STEP15_COMMAND_GROUPS)

    def test_matrix_remains_registered(self):
        self.assertIn("matrix", cli.STEP15_COMMAND_GROUPS)

    def test_pairs_remains_registered(self):
        self.assertIn("pairs", cli.STEP15_COMMAND_GROUPS)


if __name__ == "__main__":
    unittest.main()
