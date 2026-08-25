import tempfile
from pathlib import Path
import unittest

import command_cli
import database
from test_helpers import make_test_bundle

class F(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory(); root=Path(self.temp.name)
        self.db=root/"s25.db"; self.out=root/"exports"
        database.initialize_database(self.db)
        database.save_subject_typing(self.db,"DONOR-001","DONOR","3650",make_test_bundle())
        database.save_subject_typing(self.db,"RECIP-001","RECIPIENT","3650",make_test_bundle())
    def tearDown(self): self.temp.cleanup()
    def run_cli(self,*args):
        out=[]
        code=command_cli.run_command_cli(["--db",str(self.db),*args],output_func=out.append)
        return code,"\n".join(out)

class TestCLI(F):
    def test_recipient(self):
        c,t=self.run_cli("summary","recipient","RECIP-001")
        self.assertEqual(c,0); self.assertIn("STEP 25",t)
    def test_donor(self):
        c,t=self.run_cli("summary","donor","DONOR-001")
        self.assertEqual(c,0); self.assertIn("RECIP-001",t)
    def test_locus(self):
        c,t=self.run_cli("summary","recipient","RECIP-001","--locus","DRB1")
        self.assertEqual(c,0); self.assertIn("loci=DRB1",t)
    def test_candidate(self):
        c,t=self.run_cli("summary","recipient","RECIP-001","--candidate","DONOR-001")
        self.assertEqual(c,0); self.assertIn("pairs=1",t)
    def test_export(self):
        c,t=self.run_cli("summary","recipient","RECIP-001","--export","--format","both","--output-dir",str(self.out))
        self.assertEqual(c,0); self.assertIn("MISMATCH SUMMARY EXPORT COMPLETE",t)
    def test_step24_still(self):
        c,t=self.run_cli("matrix","recipient","RECIP-001")
        self.assertEqual(c,0); self.assertIn("STEP 24",t)
    def test_help(self):
        t=command_cli.command_help_text()
        self.assertIn("STEP 25",t); self.assertIn("summary recipient",t); self.assertIn("summary batch",t)

if __name__ == "__main__": unittest.main()
