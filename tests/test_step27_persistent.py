import tempfile
from pathlib import Path
import unittest

import batch_analysis
import batch_history
import database
import step27_reporting
from test_helpers import make_test_bundle


class TestStep27PersistentReporting(unittest.TestCase):

    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        root = Path(self.temp.name)
        self.db = root / "step27.db"

        database.initialize_database(self.db)
        database.save_subject_typing(
            self.db,
            "DONOR-001",
            "DONOR",
            "3650",
            make_test_bundle(),
        )
        database.save_subject_typing(
            self.db,
            "DONOR-002",
            "DONOR",
            "3650",
            make_test_bundle(),
        )
        database.save_subject_typing(
            self.db,
            "RECIP-001",
            "RECIPIENT",
            "3650",
            make_test_bundle(),
        )

        batch = batch_analysis.run_batch_analysis(
            self.db,
            "recipient",
            "RECIP-001",
            save=False,
        )
        saved = batch_history.persist_batch_with_runs(
            self.db,
            batch,
        )
        self.batch_id = saved["batch_id"]

    def tearDown(self):
        self.temp.cleanup()

    def test_persistent_report_source(self):
        report = step27_reporting.build_persistent_report(
            self.db,
            self.batch_id,
        )
        self.assertEqual(
            report["source"],
            "PERSISTENT-BATCH",
        )

    def test_persistent_batch_id(self):
        report = step27_reporting.build_persistent_report(
            self.db,
            self.batch_id,
        )
        self.assertEqual(
            report["batch_id"],
            self.batch_id,
        )

    def test_persistent_pair_count(self):
        report = step27_reporting.build_persistent_report(
            self.db,
            self.batch_id,
        )
        self.assertEqual(report["pair_count"], 2)

    def test_persistent_locus_filter(self):
        report = step27_reporting.build_persistent_report(
            self.db,
            self.batch_id,
            loci=["DPB1"],
        )
        self.assertEqual(
            report["hla_reference"]["loci"],
            ["DPB1"],
        )

    def test_persistent_no_pyard_recalculation(self):
        report = step27_reporting.build_persistent_report(
            self.db,
            self.batch_id,
        )
        self.assertFalse(
            report["provenance"]["pyard_recalculated"]
        )


if __name__ == "__main__":
    unittest.main()
