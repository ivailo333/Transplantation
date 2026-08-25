import unittest
import cli

class TestStep25Routing(unittest.TestCase):
    def test_summary_registered(self): self.assertIn("summary",cli.STEP15_COMMAND_GROUPS)
    def test_recipient_command_style(self): self.assertTrue(cli.uses_command_style(["summary","recipient","RECIP-001"]))
    def test_batch_command_style(self): self.assertTrue(cli.uses_command_style(["summary","batch","3"]))
    def test_matrix_preserved(self): self.assertIn("matrix",cli.STEP15_COMMAND_GROUPS)
    def test_pairs_preserved(self): self.assertIn("pairs",cli.STEP15_COMMAND_GROUPS)

if __name__ == "__main__": unittest.main()
