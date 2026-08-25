import json
import tempfile
from pathlib import Path
import unittest

import analyses
import cli
import database
import pair_profiles
from test_helpers import make_test_bundle

class F(unittest.TestCase):
    def setUp(self):
        self.t = tempfile.TemporaryDirectory()
        root = Path(self.t.name)
        self.db = root/"s23.db"
        self.out = root/"exports"
        database.initialize_database(self.db)
        database.save_subject_typing(self.db,"DONOR-001","DONOR","3650",make_test_bundle())
        database.save_subject_typing(self.db,"RECIP-001","RECIPIENT","3650",make_test_bundle())
        self.run = analyses.create_analysis_run_for_subjects(self.db,"DONOR-001","RECIP-001")
        cli.analyze_and_save_existing_run(self.db,self.run["run_id"])
    def tearDown(self):
        self.t.cleanup()

class TestStep23Normalization(unittest.TestCase):
    def test_level(self): self.assertEqual(pair_profiles.normalize_level("LGX"),"lgx")
    def test_g(self): self.assertEqual(pair_profiles.normalize_level("g"),"G")
    def test_invalid_level(self):
        with self.assertRaises(pair_profiles.PairProfileError): pair_profiles.normalize_level("x")
    def test_locus(self): self.assertEqual(pair_profiles.normalize_locus("drb1"),"DRB1")
    def test_invalid_locus(self):
        with self.assertRaises(pair_profiles.PairProfileError): pair_profiles.normalize_locus("X")

class TestStep23Profiles(F):
    def test_full_24(self):
        p=pair_profiles.build_live_pair_profile(self.db,"DONOR-001","RECIP-001")
        self.assertEqual(sum(len(v) for v in p["results"].values()),24)
    def test_level_6(self):
        p=pair_profiles.build_live_pair_profile(self.db,"DONOR-001","RECIP-001",level="lgx")
        self.assertEqual(len(p["results"]["lgx"]),6)
    def test_locus_4(self):
        p=pair_profiles.build_live_pair_profile(self.db,"DONOR-001","RECIP-001",locus="A")
        self.assertEqual(sum(len(v) for v in p["results"].values()),4)
    def test_level_locus_1(self):
        p=pair_profiles.build_live_pair_profile(self.db,"DONOR-001","RECIP-001",level="P",locus="DQB1")
        self.assertEqual(sum(len(v) for v in p["results"].values()),1)
    def test_no_pyard(self):
        p=pair_profiles.build_live_pair_profile(self.db,"DONOR-001","RECIP-001")
        self.assertFalse(p["recalculated_py_ard"])
    def test_stored_source(self):
        p=pair_profiles.build_stored_run_profile(self.db,self.run["run_id"])
        self.assertEqual(p["source"],"STORED-ANALYSIS-RUN")
    def test_stored_live_equal(self):
        a=pair_profiles.build_live_pair_profile(self.db,"DONOR-001","RECIP-001")
        b=pair_profiles.build_stored_run_profile(self.db,self.run["run_id"])
        self.assertEqual(a["results"],b["results"])
    def test_render(self):
        p=pair_profiles.build_live_pair_profile(self.db,"DONOR-001","RECIP-001",level="lgx",locus="A")
        s=pair_profiles.render_pair_profile(p)
        self.assertIn("STEP 23",s); self.assertIn("HLA-A",s); self.assertIn("NON-CLINICAL",s)

class TestStep23Export(F):
    def test_json(self):
        p=pair_profiles.build_live_pair_profile(self.db,"DONOR-001","RECIP-001",level="lgx")
        i=pair_profiles.export_pair_profile(p,output_dir=self.out,export_format="json")
        self.assertTrue(i["json_path"].exists())
    def test_csv_one_row(self):
        p=pair_profiles.build_live_pair_profile(self.db,"DONOR-001","RECIP-001",level="lgx",locus="A")
        i=pair_profiles.export_pair_profile(p,output_dir=self.out,export_format="csv")
        self.assertEqual(i["row_count"],1)
        self.assertEqual(len(i["csv_path"].read_text(encoding="utf-8").splitlines()),2)
    def test_both_24(self):
        p=pair_profiles.build_stored_run_profile(self.db,self.run["run_id"])
        i=pair_profiles.export_pair_profile(p,output_dir=self.out,export_format="both")
        self.assertTrue(i["json_path"].exists()); self.assertTrue(i["csv_path"].exists()); self.assertEqual(i["row_count"],24)
    def test_overwrite_protection(self):
        p=pair_profiles.build_live_pair_profile(self.db,"DONOR-001","RECIP-001")
        pair_profiles.export_pair_profile(p,output_dir=self.out,export_format="json")
        with self.assertRaises(pair_profiles.PairProfileExportExistsError):
            pair_profiles.export_pair_profile(p,output_dir=self.out,export_format="json")

if __name__=="__main__": unittest.main()
