import tempfile
from pathlib import Path
import unittest

import analyses
import cli
import command_cli
import database
from test_helpers import make_test_bundle

class F(unittest.TestCase):
    def setUp(self):
        self.t=tempfile.TemporaryDirectory()
        root=Path(self.t.name)
        self.db=root/"s23.db"; self.out=root/"exports"
        database.initialize_database(self.db)
        database.save_subject_typing(self.db,"DONOR-001","DONOR","3650",make_test_bundle())
        database.save_subject_typing(self.db,"RECIP-001","RECIPIENT","3650",make_test_bundle())
        self.run=analyses.create_analysis_run_for_subjects(self.db,"DONOR-001","RECIP-001")
        cli.analyze_and_save_existing_run(self.db,self.run["run_id"])
    def tearDown(self): self.t.cleanup()
    def execute_cli(self,*args):
        o=[]
        c=command_cli.run_command_cli(["--db",str(self.db),*args],output_func=o.append)
        return c,"\n".join(o)

class TestStep23CLI(F):
    def test_show(self):
        c,s=self.execute_cli("pairs","show","DONOR-001","RECIP-001")
        self.assertEqual(c,0); self.assertIn("STEP 23 — PAIR COMPARISON PROFILE",s)
    def test_filter(self):
        c,s=self.execute_cli("pairs","show","DONOR-001","RECIP-001","--level","lgx","--locus","DRB1")
        self.assertEqual(c,0); self.assertIn("level=LGX | locus=DRB1",s)
    def test_show_run(self):
        c,s=self.execute_cli("pairs","show-run",str(self.run["run_id"]))
        self.assertEqual(c,0); self.assertIn("STORED-ANALYSIS-RUN",s)
    def test_export(self):
        c,s=self.execute_cli("pairs","export","DONOR-001","RECIP-001","--level","lgx","--locus","A","--format","both","--output-dir",str(self.out))
        self.assertEqual(c,0); self.assertIn("Profile rows represented: 1",s)
    def test_export_run(self):
        c,s=self.execute_cli("pairs","export-run",str(self.run["run_id"]),"--format","json","--output-dir",str(self.out))
        self.assertEqual(c,0); self.assertIn("STORED-ANALYSIS-RUN",s)
    def test_bad_locus(self):
        c,s=self.execute_cli("pairs","show","DONOR-001","RECIP-001","--locus","X")
        self.assertEqual(c,5); self.assertIn("Невалиден HLA locus",s)
    def test_step22_still(self):
        c,s=self.execute_cli("batch","recipient","RECIP-001","--max-donor-only","0")
        self.assertEqual(c,0); self.assertIn("STEP 22 selection",s)
    def test_help(self):
        s=command_cli.command_help_text()
        self.assertIn("STEP 23",s); self.assertIn("pairs show",s)

if __name__=="__main__": unittest.main()
