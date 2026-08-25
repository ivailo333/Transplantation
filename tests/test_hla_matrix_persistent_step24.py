import tempfile
from pathlib import Path
import unittest

import batch_analysis
import batch_history
import database
import hla_matrix
from test_helpers import make_test_bundle


class TestStep24PersistentBatch(unittest.TestCase):

    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        root = Path(self.temp.name)
        self.db = root / "step24.db"

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

    def test_persistent_matrix_has_batch_id(self):
        matrix = hla_matrix.build_persistent_matrix(
            self.db,
            self.batch_id,
        )
        self.assertEqual(
            matrix["batch_id"],
            self.batch_id,
        )

    def test_persistent_source(self):
        matrix = hla_matrix.build_persistent_matrix(
            self.db,
            self.batch_id,
        )
        self.assertEqual(
            matrix["source"],
            "PERSISTENT-BATCH",
        )

    def test_persistent_pair_count(self):
        matrix = hla_matrix.build_persistent_matrix(
            self.db,
            self.batch_id,
        )
        self.assertEqual(matrix["pair_count"], 2)

    def test_persistent_filtered_locus(self):
        matrix = hla_matrix.build_persistent_matrix(
            self.db,
            self.batch_id,
            loci=["DPB1"],
        )
        self.assertEqual(matrix["loci"], ["DPB1"])

    def test_persistent_does_not_recalculate_pyard(self):
        matrix = hla_matrix.build_persistent_matrix(
            self.db,
            self.batch_id,
        )
        self.assertFalse(matrix["recalculated_py_ard"])


if __name__ == "__main__":
    unittest.main()
