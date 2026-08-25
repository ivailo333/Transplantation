import tempfile
from pathlib import Path
import unittest

import batch_analysis
import batch_history
import database
import mismatch_summary
from test_helpers import make_test_bundle

class TestPersistentSummary(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory(); root=Path(self.temp.name)
        self.db=root/"s25.db"
        database.initialize_database(self.db)
        database.save_subject_typing(self.db,"DONOR-001","DONOR","3650",make_test_bundle())
        database.save_subject_typing(self.db,"DONOR-002","DONOR","3650",make_test_bundle())
        database.save_subject_typing(self.db,"RECIP-001","RECIPIENT","3650",make_test_bundle())
        batch=batch_analysis.run_batch_analysis(self.db,"recipient","RECIP-001",save=False)
        saved=batch_history.persist_batch_with_runs(self.db,batch)
        self.batch_id=saved["batch_id"]
    def tearDown(self): self.temp.cleanup()
    def test_batch_id(self):
        s=mismatch_summary.build_persistent_summary(self.db,self.batch_id)
        self.assertEqual(s["batch_id"],self.batch_id)
    def test_source(self):
        s=mismatch_summary.build_persistent_summary(self.db,self.batch_id)
        self.assertEqual(s["source"],"PERSISTENT-BATCH")
    def test_pair_count(self):
        s=mismatch_summary.build_persistent_summary(self.db,self.batch_id)
        self.assertEqual(s["pair_count"],2)
    def test_no_pyard(self):
        s=mismatch_summary.build_persistent_summary(self.db,self.batch_id)
        self.assertFalse(s["recalculated_py_ard"])

if __name__ == "__main__": unittest.main()
