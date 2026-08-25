import copy
import csv
import json
import sqlite3
import tempfile
from contextlib import closing
from pathlib import Path
import unittest
from unittest.mock import patch

import hla_match as hla
import database as database
import exporters as exporters
import migrations as migrations

from test_helpers import make_test_bundle, make_comparison_results


class TestStep13DAnalysisRun(unittest.TestCase):

    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.db_path = Path(self.temp_dir.name) / "step13d.db"
        database.initialize_database(self.db_path)

    def tearDown(self):
        self.temp_dir.cleanup()

    def _save_pair(self, version="3650"):
        result = database.save_donor_recipient_typings(
            database_path=self.db_path,
            donor_external_id="DONOR-001",
            recipient_external_id="RECIP-001",
            imgthla_version=version,
            donor_bundle=make_test_bundle(),
            recipient_bundle=make_test_bundle(),
        )
        return result

    def test_create_analysis_run_saves_link(self):
        pair = self._save_pair()

        run = database.create_analysis_run(
            self.db_path,
            pair["donor"]["typing_id"],
            pair["recipient"]["typing_id"],
        )

        self.assertGreater(run["run_id"], 0)
        self.assertEqual(
            run["donor"]["typing_id"],
            pair["donor"]["typing_id"],
        )
        self.assertEqual(
            run["recipient"]["typing_id"],
            pair["recipient"]["typing_id"],
        )

    def test_analysis_run_stores_version(self):
        pair = self._save_pair(version="3650")

        run = database.create_analysis_run(
            self.db_path,
            pair["donor"]["typing_id"],
            pair["recipient"]["typing_id"],
        )

        self.assertEqual(run["imgthla_version"], "3650")

    def test_analysis_run_table_contains_exact_typing_ids(self):
        pair = self._save_pair()

        run = database.create_analysis_run(
            self.db_path,
            pair["donor"]["typing_id"],
            pair["recipient"]["typing_id"],
        )

        with closing(database.connect_db(self.db_path)) as conn:
            row = conn.execute(
                """
                SELECT donor_typing_id, recipient_typing_id
                FROM analysis_runs
                WHERE id = ?
                """,
                (run["run_id"],),
            ).fetchone()

        self.assertEqual(
            row,
            (
                pair["donor"]["typing_id"],
                pair["recipient"]["typing_id"],
            ),
        )

    def test_recipient_typing_cannot_be_used_as_donor(self):
        pair = self._save_pair()

        with self.assertRaises(database.AnalysisTypingRoleError):
            database.create_analysis_run(
                self.db_path,
                pair["recipient"]["typing_id"],
                pair["recipient"]["typing_id"],
            )

    def test_donor_typing_cannot_be_used_as_recipient(self):
        pair = self._save_pair()

        with self.assertRaises(database.AnalysisTypingRoleError):
            database.create_analysis_run(
                self.db_path,
                pair["donor"]["typing_id"],
                pair["donor"]["typing_id"],
            )

    def test_unknown_typing_id_is_rejected(self):
        pair = self._save_pair()

        with self.assertRaises(database.TypingNotFoundError):
            database.create_analysis_run(
                self.db_path,
                999999,
                pair["recipient"]["typing_id"],
            )

    def test_version_mismatch_is_rejected(self):
        donor = database.save_subject_typing(
            self.db_path,
            "DONOR-001",
            "DONOR",
            "3650",
            make_test_bundle(),
        )
        recipient = database.save_subject_typing(
            self.db_path,
            "RECIP-001",
            "RECIPIENT",
            "3651",
            make_test_bundle(),
        )

        with self.assertRaises(
            database.AnalysisVersionMismatchError
        ):
            database.create_analysis_run(
                self.db_path,
                donor["typing_id"],
                recipient["typing_id"],
            )

    def test_explicit_wrong_analysis_version_is_rejected(self):
        pair = self._save_pair(version="3650")

        with self.assertRaises(
            database.AnalysisVersionMismatchError
        ):
            database.create_analysis_run(
                self.db_path,
                pair["donor"]["typing_id"],
                pair["recipient"]["typing_id"],
                imgthla_version="9999",
            )

    def test_incomplete_typing_is_rejected(self):
        pair = self._save_pair()

        with closing(database.connect_db(self.db_path)) as conn:
            conn.execute(
                """
                DELETE FROM hla_alleles
                WHERE typing_id = ?
                  AND locus = 'DPB1'
                  AND allele_number = 2
                """,
                (pair["donor"]["typing_id"],),
            )
            conn.commit()

        with self.assertRaises(database.IncompleteTypingError):
            database.create_analysis_run(
                self.db_path,
                pair["donor"]["typing_id"],
                pair["recipient"]["typing_id"],
            )

    def test_create_analysis_for_subjects_uses_latest_typings(self):
        first = self._save_pair()
        second = self._save_pair()

        run = database.create_analysis_run_for_subjects(
            self.db_path,
            "DONOR-001",
            "RECIP-001",
        )

        self.assertNotEqual(
            first["donor"]["typing_id"],
            second["donor"]["typing_id"],
        )
        self.assertEqual(
            run["donor"]["typing_id"],
            second["donor"]["typing_id"],
        )
        self.assertEqual(
            run["recipient"]["typing_id"],
            second["recipient"]["typing_id"],
        )

    def test_create_analysis_for_subjects_can_use_specific_typings(self):
        first = self._save_pair()
        self._save_pair()

        run = database.create_analysis_run_for_subjects(
            self.db_path,
            "DONOR-001",
            "RECIP-001",
            donor_typing_id=first["donor"]["typing_id"],
            recipient_typing_id=first["recipient"]["typing_id"],
        )

        self.assertEqual(
            run["donor"]["typing_id"],
            first["donor"]["typing_id"],
        )
        self.assertEqual(
            run["recipient"]["typing_id"],
            first["recipient"]["typing_id"],
        )

    def test_load_analysis_run_returns_metadata(self):
        pair = self._save_pair()

        created = database.create_analysis_run(
            self.db_path,
            pair["donor"]["typing_id"],
            pair["recipient"]["typing_id"],
        )

        loaded = database.load_analysis_run(
            self.db_path,
            created["run_id"],
        )

        self.assertEqual(
            loaded["run_id"],
            created["run_id"],
        )
        self.assertEqual(
            loaded["donor"]["external_id"],
            "DONOR-001",
        )
        self.assertEqual(
            loaded["recipient"]["external_id"],
            "RECIP-001",
        )
        self.assertEqual(
            loaded["analysis_result_count"],
            0,
        )

    def test_missing_analysis_run_is_rejected(self):
        with self.assertRaises(
            database.AnalysisRunNotFoundError
        ):
            database.load_analysis_run(
                self.db_path,
                999999,
            )

    def test_list_analysis_runs_newest_first(self):
        pair = self._save_pair()

        first = database.create_analysis_run(
            self.db_path,
            pair["donor"]["typing_id"],
            pair["recipient"]["typing_id"],
        )
        second = database.create_analysis_run(
            self.db_path,
            pair["donor"]["typing_id"],
            pair["recipient"]["typing_id"],
        )

        runs = database.list_analysis_runs(self.db_path)

        self.assertEqual(
            [run["run_id"] for run in runs],
            [second["run_id"], first["run_id"]],
        )


class TestStep13EAnalysisResults(unittest.TestCase):

    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.db_path = Path(self.temp_dir.name) / "step13e.db"
        database.initialize_database(self.db_path)

        pair = database.save_donor_recipient_typings(
            database_path=self.db_path,
            donor_external_id="DONOR-001",
            recipient_external_id="RECIP-001",
            imgthla_version="3650",
            donor_bundle=make_test_bundle(),
            recipient_bundle=make_test_bundle(),
        )

        self.run = database.create_analysis_run(
            self.db_path,
            pair["donor"]["typing_id"],
            pair["recipient"]["typing_id"],
        )

    def tearDown(self):
        self.temp_dir.cleanup()

    def _linked(self):
        return database.load_analysis_run_typings(
            self.db_path,
            self.run["run_id"],
        )

    def _results(self):
        linked = self._linked()
        return make_comparison_results(
            linked["donor"]["bundle"],
            linked["recipient"]["bundle"],
        )

    def test_load_analysis_run_typings_uses_exact_linked_typings(self):
        linked = self._linked()

        self.assertEqual(
            linked["donor"]["typing"]["typing_id"],
            self.run["donor"]["typing_id"],
        )
        self.assertEqual(
            linked["recipient"]["typing"]["typing_id"],
            self.run["recipient"]["typing_id"],
        )

    def test_build_comparison_results_has_four_levels_and_six_loci(self):
        results = self._results()

        self.assertEqual(
            set(results),
            {"canonical", "lgx", "G", "P"},
        )

        for level in results:
            self.assertEqual(
                set(results[level]),
                set(hla.HLA_LOCI),
            )

    def test_validate_analysis_results_accepts_valid_structure(self):
        self.assertTrue(
            database.validate_analysis_results_structure(
                self._results()
            )
        )

    def test_save_analysis_results_creates_exactly_24_rows(self):
        saved = database.save_analysis_results(
            self.db_path,
            self.run["run_id"],
            self._results(),
        )

        self.assertEqual(saved["row_count"], 24)

        with closing(database.connect_db(self.db_path)) as conn:
            count = conn.execute(
                """
                SELECT COUNT(*)
                FROM analysis_results
                WHERE run_id = ?
                """,
                (self.run["run_id"],),
            ).fetchone()[0]

        self.assertEqual(count, 24)

    def test_analysis_results_levels_are_6_each(self):
        database.save_analysis_results(
            self.db_path,
            self.run["run_id"],
            self._results(),
        )

        with closing(database.connect_db(self.db_path)) as conn:
            rows = conn.execute(
                """
                SELECT level, COUNT(*)
                FROM analysis_results
                WHERE run_id = ?
                GROUP BY level
                ORDER BY level
                """,
                (self.run["run_id"],),
            ).fetchall()

        self.assertEqual(
            dict(rows),
            {
                "CANONICAL": 6,
                "G": 6,
                "LGX": 6,
                "P": 6,
            },
        )

    def test_save_analysis_results_is_idempotent(self):
        results = self._results()

        database.save_analysis_results(
            self.db_path,
            self.run["run_id"],
            results,
        )
        database.save_analysis_results(
            self.db_path,
            self.run["run_id"],
            results,
        )

        with closing(database.connect_db(self.db_path)) as conn:
            count = conn.execute(
                """
                SELECT COUNT(*)
                FROM analysis_results
                WHERE run_id = ?
                """,
                (self.run["run_id"],),
            ).fetchone()[0]

        self.assertEqual(count, 24)

    def test_json_lists_round_trip(self):
        results = self._results()

        database.save_analysis_results(
            self.db_path,
            self.run["run_id"],
            results,
        )

        loaded = database.load_analysis_results(
            self.db_path,
            self.run["run_id"],
        )

        self.assertEqual(
            loaded["results"],
            results,
        )

    def test_load_results_reports_24_rows(self):
        database.save_analysis_results(
            self.db_path,
            self.run["run_id"],
            self._results(),
        )

        loaded = database.load_analysis_results(
            self.db_path,
            self.run["run_id"],
        )

        self.assertEqual(loaded["row_count"], 24)

    def test_load_results_without_saved_rows_raises(self):
        with self.assertRaises(
            database.AnalysisResultsNotFoundError
        ):
            database.load_analysis_results(
                self.db_path,
                self.run["run_id"],
            )

    def test_wrong_shared_count_is_rejected(self):
        results = self._results()
        results["canonical"]["A"]["shared_count"] += 1

        with self.assertRaises(database.AnalysisResultsError):
            database.save_analysis_results(
                self.db_path,
                self.run["run_id"],
                results,
            )

    def test_missing_level_is_rejected(self):
        results = self._results()
        del results["P"]

        with self.assertRaises(database.AnalysisResultsError):
            database.save_analysis_results(
                self.db_path,
                self.run["run_id"],
                results,
            )

    def test_missing_locus_is_rejected(self):
        results = self._results()
        del results["lgx"]["DPB1"]

        with self.assertRaises(database.AnalysisResultsError):
            database.save_analysis_results(
                self.db_path,
                self.run["run_id"],
                results,
            )

    def test_analysis_run_result_count_becomes_24(self):
        database.save_analysis_results(
            self.db_path,
            self.run["run_id"],
            self._results(),
        )

        run = database.load_analysis_run(
            self.db_path,
            self.run["run_id"],
        )

        self.assertEqual(
            run["analysis_result_count"],
            24,
        )

    def test_list_analysis_runs_reports_24_results(self):
        database.save_analysis_results(
            self.db_path,
            self.run["run_id"],
            self._results(),
        )

        runs = database.list_analysis_runs(self.db_path)

        self.assertEqual(
            runs[0]["analysis_result_count"],
            24,
        )

    def test_saved_db_level_is_uppercase_canonical(self):
        database.save_analysis_results(
            self.db_path,
            self.run["run_id"],
            self._results(),
        )

        with closing(database.connect_db(self.db_path)) as conn:
            levels = {
                row[0]
                for row in conn.execute(
                    """
                    SELECT DISTINCT level
                    FROM analysis_results
                    WHERE run_id = ?
                    """,
                    (self.run["run_id"],),
                ).fetchall()
            }

        self.assertEqual(
            levels,
            {"CANONICAL", "LGX", "G", "P"},
        )
