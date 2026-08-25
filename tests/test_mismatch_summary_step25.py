import copy
import tempfile
from pathlib import Path
import unittest

import database
import mismatch_summary
from test_helpers import make_test_bundle


def changed_bundle(*loci):
    bundle = copy.deepcopy(make_test_bundle())
    for representation in ("canonical", "lgx", "G", "P"):
        for locus in loci:
            bundle[representation][locus] = [
                f"{locus}*90:01-{representation}",
                f"{locus}*91:01-{representation}",
            ]
    for locus in loci:
        bundle["raw"][locus] = [f"{locus}*90:01", f"{locus}*91:01"]
    return bundle


class F(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        root = Path(self.temp.name)
        self.db = root / "step25.db"
        self.out = root / "exports"
        database.initialize_database(self.db)
        database.save_subject_typing(self.db, "DONOR-FULL", "DONOR", "3650", make_test_bundle())
        database.save_subject_typing(self.db, "DONOR-A", "DONOR", "3650", changed_bundle("A"))
        database.save_subject_typing(self.db, "RECIP-001", "RECIPIENT", "3650", make_test_bundle())
    def tearDown(self):
        self.temp.cleanup()


class TestClassification(unittest.TestCase):
    def test_complete(self):
        self.assertEqual(mismatch_summary.classify_counts(2,0,0), mismatch_summary.CLASS_COMPLETE)
    def test_partial(self):
        self.assertEqual(mismatch_summary.classify_counts(1,1,1), mismatch_summary.CLASS_PARTIAL)
    def test_none(self):
        self.assertEqual(mismatch_summary.classify_counts(0,2,2), mismatch_summary.CLASS_NONE)
    def test_negative_rejected(self):
        with self.assertRaises(mismatch_summary.MismatchSummaryError):
            mismatch_summary.classify_counts(1,-1,0)


class TestSummary(F):
    def test_pair_count(self):
        s=mismatch_summary.build_live_summary(self.db,"recipient","RECIP-001")
        self.assertEqual(s["pair_count"],2)
    def test_identical_complete(self):
        s=mismatch_summary.build_live_summary(self.db,"recipient","RECIP-001",candidate_external_ids=["DONOR-FULL"])
        self.assertEqual(s["rows"][0]["totals"]["classification"], mismatch_summary.CLASS_COMPLETE)
    def test_changed_pair_partial(self):
        s=mismatch_summary.build_live_summary(self.db,"recipient","RECIP-001",candidate_external_ids=["DONOR-A"])
        self.assertEqual(s["rows"][0]["totals"]["classification"], mismatch_summary.CLASS_PARTIAL)
    def test_changed_locus_none(self):
        s=mismatch_summary.build_live_summary(self.db,"recipient","RECIP-001",candidate_external_ids=["DONOR-A"],loci=["A"])
        self.assertEqual(s["rows"][0]["loci"]["A"]["classification"], mismatch_summary.CLASS_NONE)
    def test_unchanged_locus_complete(self):
        s=mismatch_summary.build_live_summary(self.db,"recipient","RECIP-001",candidate_external_ids=["DONOR-A"],loci=["B"])
        self.assertEqual(s["rows"][0]["loci"]["B"]["classification"], mismatch_summary.CLASS_COMPLETE)
    def test_no_pyard(self):
        s=mismatch_summary.build_live_summary(self.db,"recipient","RECIP-001")
        self.assertFalse(s["recalculated_py_ard"])
    def test_render(self):
        s=mismatch_summary.build_live_summary(self.db,"recipient","RECIP-001")
        text=mismatch_summary.render_summary(s)
        self.assertIn("STEP 25",text); self.assertIn("NON-CLINICAL",text)
    def test_json_export(self):
        s=mismatch_summary.build_live_summary(self.db,"recipient","RECIP-001")
        info=mismatch_summary.export_summary(s,output_dir=self.out,export_format="json")
        self.assertTrue(info["json_path"].exists())
    def test_csv_export(self):
        s=mismatch_summary.build_live_summary(self.db,"recipient","RECIP-001")
        info=mismatch_summary.export_summary(s,output_dir=self.out,export_format="csv")
        self.assertEqual(len(info["csv_path"].read_text(encoding="utf-8").splitlines()),1+s["pair_count"])
    def test_overwrite_protection(self):
        s=mismatch_summary.build_live_summary(self.db,"recipient","RECIP-001")
        mismatch_summary.export_summary(s,output_dir=self.out,export_format="json")
        with self.assertRaises(mismatch_summary.MismatchSummaryExportExistsError):
            mismatch_summary.export_summary(s,output_dir=self.out,export_format="json")

if __name__ == "__main__": unittest.main()
