import copy
import json
import tempfile
from pathlib import Path
import unittest

import batch_history
import database
import hla_matrix

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
        bundle["raw"][locus] = [
            f"{locus}*90:01",
            f"{locus}*91:01",
        ]

    return bundle


class Step24Fixture(unittest.TestCase):

    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        root = Path(self.temp.name)
        self.db = root / "step24.db"
        self.out = root / "exports"

        database.initialize_database(self.db)

        database.save_subject_typing(
            self.db,
            "DONOR-FULL",
            "DONOR",
            "3650",
            make_test_bundle(),
        )
        database.save_subject_typing(
            self.db,
            "DONOR-A",
            "DONOR",
            "3650",
            changed_bundle("A"),
        )
        database.save_subject_typing(
            self.db,
            "DONOR-AB",
            "DONOR",
            "3650",
            changed_bundle("A", "B"),
        )
        database.save_subject_typing(
            self.db,
            "RECIP-001",
            "RECIPIENT",
            "3650",
            make_test_bundle(),
        )

    def tearDown(self):
        self.temp.cleanup()


class TestStep24Normalization(unittest.TestCase):

    def test_default_level_is_lgx(self):
        self.assertEqual(
            hla_matrix.normalize_level(None),
            "lgx",
        )

    def test_level_case_insensitive(self):
        self.assertEqual(
            hla_matrix.normalize_level("G"),
            "G",
        )

    def test_invalid_level_rejected(self):
        with self.assertRaises(hla_matrix.MatrixError):
            hla_matrix.normalize_level("X")

    def test_loci_canonical_order(self):
        self.assertEqual(
            hla_matrix.normalize_loci(["DRB1", "A"]),
            ["A", "DRB1"],
        )

    def test_invalid_locus_rejected(self):
        with self.assertRaises(hla_matrix.MatrixError):
            hla_matrix.normalize_loci(["X"])


class TestStep24LiveMatrix(Step24Fixture):

    def test_recipient_matrix_has_three_pairs(self):
        matrix = hla_matrix.build_live_matrix(
            self.db,
            "recipient",
            "RECIP-001",
        )
        self.assertEqual(matrix["pair_count"], 3)

    def test_default_matrix_has_six_loci(self):
        matrix = hla_matrix.build_live_matrix(
            self.db,
            "recipient",
            "RECIP-001",
        )
        self.assertEqual(len(matrix["loci"]), 6)

    def test_locus_filter(self):
        matrix = hla_matrix.build_live_matrix(
            self.db,
            "recipient",
            "RECIP-001",
            loci=["A", "DRB1"],
        )
        self.assertEqual(matrix["loci"], ["A", "DRB1"])

    def test_candidate_filter(self):
        matrix = hla_matrix.build_live_matrix(
            self.db,
            "recipient",
            "RECIP-001",
            candidate_external_ids=["DONOR-A"],
        )
        self.assertEqual(matrix["pair_count"], 1)
        self.assertEqual(
            matrix["rows"][0]["candidate_external_id"],
            "DONOR-A",
        )

    def test_cell_has_three_counts(self):
        matrix = hla_matrix.build_live_matrix(
            self.db,
            "recipient",
            "RECIP-001",
            candidate_external_ids=["DONOR-FULL"],
            level="lgx",
            loci=["A"],
        )
        cell = matrix["rows"][0]["cells"]["A"]
        self.assertEqual(
            set(cell),
            {
                "shared_count",
                "donor_only_count",
                "recipient_only_count",
            },
        )

    def test_totals_equal_locus_sum(self):
        matrix = hla_matrix.build_live_matrix(
            self.db,
            "recipient",
            "RECIP-001",
            candidate_external_ids=["DONOR-AB"],
            level="lgx",
        )
        row = matrix["rows"][0]
        self.assertEqual(
            row["totals"]["donor_only_count"],
            sum(
                cell["donor_only_count"]
                for cell in row["cells"].values()
            ),
        )

    def test_sort_by_donor_only(self):
        matrix = hla_matrix.build_live_matrix(
            self.db,
            "recipient",
            "RECIP-001",
            level="lgx",
            sort_by="donor-only",
        )
        values = [
            row["totals"]["donor_only_count"]
            for row in matrix["rows"]
        ]
        self.assertEqual(values, sorted(values))

    def test_sort_order_requires_sort_by(self):
        with self.assertRaises(hla_matrix.MatrixError):
            hla_matrix.build_live_matrix(
                self.db,
                "recipient",
                "RECIP-001",
                sort_order="desc",
            )

    def test_no_clinical_score(self):
        matrix = hla_matrix.build_live_matrix(
            self.db,
            "recipient",
            "RECIP-001",
        )
        self.assertFalse(matrix["clinical_score"])
        self.assertFalse(matrix["recalculated_py_ard"])


class TestStep24RenderAndExport(Step24Fixture):

    def test_render_contains_cell_format(self):
        matrix = hla_matrix.build_live_matrix(
            self.db,
            "recipient",
            "RECIP-001",
            candidate_external_ids=["DONOR-FULL"],
            loci=["A"],
        )
        text = hla_matrix.render_matrix(matrix)
        self.assertIn("STEP 24", text)
        self.assertIn(
            "shared_count/donor_only_count/recipient_only_count",
            text,
        )
        self.assertIn("DONOR-FULL", text)

    def test_json_export(self):
        matrix = hla_matrix.build_live_matrix(
            self.db,
            "recipient",
            "RECIP-001",
            loci=["A"],
        )
        info = hla_matrix.export_matrix(
            matrix,
            output_dir=self.out,
            export_format="json",
        )
        self.assertTrue(info["json_path"].exists())
        payload = json.loads(
            info["json_path"].read_text(encoding="utf-8")
        )
        self.assertEqual(
            payload["schema"],
            hla_matrix.MATRIX_SCHEMA,
        )

    def test_csv_export_has_one_row_per_pair(self):
        matrix = hla_matrix.build_live_matrix(
            self.db,
            "recipient",
            "RECIP-001",
            loci=["A", "DRB1"],
        )
        info = hla_matrix.export_matrix(
            matrix,
            output_dir=self.out,
            export_format="csv",
        )
        lines = info["csv_path"].read_text(
            encoding="utf-8"
        ).splitlines()
        self.assertEqual(len(lines), 1 + matrix["pair_count"])

    def test_overwrite_protection(self):
        matrix = hla_matrix.build_live_matrix(
            self.db,
            "recipient",
            "RECIP-001",
            loci=["A"],
        )
        hla_matrix.export_matrix(
            matrix,
            output_dir=self.out,
            export_format="json",
        )
        with self.assertRaises(
            hla_matrix.MatrixExportExistsError
        ):
            hla_matrix.export_matrix(
                matrix,
                output_dir=self.out,
                export_format="json",
            )


if __name__ == "__main__":
    unittest.main()
