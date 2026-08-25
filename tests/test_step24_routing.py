import unittest

import cli


class TestStep24Routing(unittest.TestCase):

    def test_matrix_is_registered_command_group(self):
        self.assertIn("matrix", cli.STEP15_COMMAND_GROUPS)

    def test_matrix_recipient_is_command_style(self):
        self.assertTrue(
            cli.uses_command_style(
                ["matrix", "recipient", "RECIP-001"]
            )
        )

    def test_matrix_batch_is_command_style(self):
        self.assertTrue(
            cli.uses_command_style(
                ["matrix", "batch", "3"]
            )
        )

    def test_pairs_remains_command_style(self):
        self.assertTrue(
            cli.uses_command_style(
                ["pairs", "show", "DONOR-001", "RECIP-001"]
            )
        )


if __name__ == "__main__":
    unittest.main()
