import unittest

import cli


class TestStep23Routing(unittest.TestCase):

    def test_pairs_is_registered_command_group(self):
        self.assertIn("pairs", cli.STEP15_COMMAND_GROUPS)

    def test_pairs_is_command_style_group(self):
        self.assertTrue(
            cli.uses_command_style(
                ["pairs", "show", "DONOR-001", "RECIP-001"]
            )
        )


if __name__ == "__main__":
    unittest.main()
