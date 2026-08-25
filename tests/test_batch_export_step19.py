import copy
import csv
import json
import tempfile
from pathlib import Path
import unittest

import batch_analysis
import batch_exporters
import batch_ranking
import command_cli
import database

from test_helpers import make_test_bundle


def bundle_with_mismatched_loci(*loci):
    bundle = copy.deepcopy(make_test_bundle())

    for representation in (
        "canonical",
        "lgx",
        "G",
        "P",
    ):
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


class Step19Fixture(unittest.TestCase):

    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        root = Path(self.temp_dir.name)

        self.db_path = root / "step19.db"
        self.export_dir = root / "exports"

        database.initialize_database(
            self.db_path
        )

        database.save_subject_typing(
            self.db_path,
            "DONOR-FULL",
            "DONOR",
            "3650",
            make_test_bundle(),
        )
        database.save_subject_typing(
            self.db_path,
            "DONOR-A",
            "DONOR",
            "3650",
            bundle_with_mismatched_loci("A"),
        )
        database.save_subject_typing(
            self.db_path,
            "DONOR-AB",
            "DONOR",
            "3650",
            bundle_with_mismatched_loci("A", "B"),
        )
        database.save_subject_typing(
            self.db_path,
            "RECIP-001",
            "RECIPIENT",
            "3650",
            make_test_bundle(),
        )

    def tearDown(self):
        self.temp_dir.cleanup()

    def base_batch(self, save=False):
        return batch_analysis.run_batch_analysis(
            self.db_path,
            "recipient",
            "RECIP-001",
            save=save,
        )

    def ordered_batch(self, save=False):
        return batch_ranking.apply_batch_ordering(
            self.base_batch(save=save),
            level="lgx",
            metric="donor-only",
            display_limit=None,
        )

    def run_cli(self, *args):
        output = []

        code = command_cli.run_command_cli(
            [
                "--db",
                str(self.db_path),
                *args,
            ],
            output_func=output.append,
        )

        return code, "\n".join(output)


class TestStep19FormatAndNames(Step19Fixture):

    def test_export_format_defaults_to_both(self):
        self.assertEqual(
            batch_exporters.normalize_batch_export_format(
                None
            ),
            "both",
        )

    def test_invalid_export_format_is_rejected(self):
        with self.assertRaises(
            batch_exporters.BatchExportError
        ):
            batch_exporters.normalize_batch_export_format(
                "xlsx"
            )

    def test_filename_sanitization_removes_windows_forbidden_chars(self):
        value = batch_exporters.sanitize_export_component(
            'RECIP:001/ABC*?'
        )

        self.assertNotIn(":", value)
        self.assertNotIn("/", value)
        self.assertNotIn("*", value)
        self.assertNotIn("?", value)

    def test_default_name_contains_direction_anchor_and_typing(self):
        batch = self.base_batch()

        name = batch_exporters.default_batch_export_name(
            batch
        )

        self.assertIn("recipient", name)
        self.assertIn("RECIP-001", name)
        self.assertIn("typing", name)

    def test_ranked_default_name_contains_sort_criterion(self):
        batch = self.ordered_batch()

        name = batch_exporters.default_batch_export_name(
            batch
        )

        self.assertIn("sorted", name)
        self.assertIn("lgx", name)
        self.assertIn("donor-only", name)


class TestStep19Payload(Step19Fixture):

    def test_json_payload_has_schema_and_all_pairs(self):
        batch = self.base_batch()

        payload = batch_exporters.build_batch_export_payload(
            batch
        )

        self.assertEqual(
            payload["schema"],
            "hla-batch-export-v1",
        )
        self.assertEqual(
            payload["batch"]["pair_count"],
            3,
        )
        self.assertEqual(
            len(payload["pairs"]),
            3,
        )

    def test_json_payload_preserves_full_results(self):
        payload = batch_exporters.build_batch_export_payload(
            self.base_batch()
        )

        pair = payload["pairs"][0]

        self.assertEqual(
            set(pair["results"]),
            {"canonical", "lgx", "G", "P"},
        )
        self.assertEqual(
            len(pair["results"]["lgx"]),
            6,
        )

    def test_json_payload_contains_nonclinical_warning(self):
        payload = batch_exporters.build_batch_export_payload(
            self.base_batch()
        )

        self.assertFalse(
            payload["interpretation"]["clinical_score"]
        )
        self.assertIn(
            "not an organ-allocation score",
            payload["interpretation"]["warning"],
        )

    def test_ranked_payload_preserves_software_order(self):
        payload = batch_exporters.build_batch_export_payload(
            self.ordered_batch()
        )

        self.assertIsNotNone(
            payload["batch"]["software_ordering"]
        )
        self.assertEqual(
            payload["pairs"][0]["software_order"]["position"],
            1,
        )

    def test_truncated_ranked_view_is_rejected_for_export(self):
        truncated = batch_ranking.apply_batch_ordering(
            self.base_batch(),
            metric="donor-only",
            display_limit=1,
        )

        with self.assertRaises(
            batch_exporters.BatchExportStructureError
        ):
            batch_exporters.build_batch_export_payload(
                truncated
            )


class TestStep19CSV(Step19Fixture):

    def test_csv_iterator_produces_24_rows_per_pair(self):
        payload = batch_exporters.build_batch_export_payload(
            self.base_batch()
        )

        rows = list(
            batch_exporters.iter_batch_csv_rows(
                payload
            )
        )

        self.assertEqual(len(rows), 72)

    def test_csv_rank_fields_are_blank_without_ordering(self):
        payload = batch_exporters.build_batch_export_payload(
            self.base_batch()
        )

        row = next(
            batch_exporters.iter_batch_csv_rows(
                payload
            )
        )

        self.assertEqual(
            row["software_position"],
            "",
        )
        self.assertEqual(
            row["software_rank"],
            "",
        )

    def test_csv_rank_fields_are_present_with_ordering(self):
        payload = batch_exporters.build_batch_export_payload(
            self.ordered_batch()
        )

        row = next(
            batch_exporters.iter_batch_csv_rows(
                payload
            )
        )

        self.assertEqual(
            row["software_position"],
            1,
        )
        self.assertEqual(
            row["software_rank"],
            1,
        )
        self.assertEqual(
            row["sort_metric"],
            "donor_only_count",
        )


class TestStep19Files(Step19Fixture):

    def test_json_export_is_created(self):
        info = batch_exporters.export_batch(
            self.base_batch(),
            output_dir=self.export_dir,
            export_format="json",
        )

        path = info["files"]["json"]

        self.assertTrue(path.exists())

        with path.open(
            "r",
            encoding="utf-8",
        ) as handle:
            payload = json.load(handle)

        self.assertEqual(
            payload["batch"]["pair_count"],
            3,
        )

    def test_csv_export_is_created_with_72_data_rows(self):
        info = batch_exporters.export_batch(
            self.base_batch(),
            output_dir=self.export_dir,
            export_format="csv",
        )

        path = info["files"]["csv"]

        with path.open(
            "r",
            encoding="utf-8-sig",
            newline="",
        ) as handle:
            rows = list(csv.DictReader(handle))

        self.assertEqual(len(rows), 72)

    def test_both_export_creates_json_and_csv(self):
        info = batch_exporters.export_batch(
            self.base_batch(),
            output_dir=self.export_dir,
            export_format="both",
        )

        self.assertEqual(
            set(info["files"]),
            {"json", "csv"},
        )

    def test_existing_export_is_not_overwritten_by_default(self):
        batch = self.base_batch()

        batch_exporters.export_batch(
            batch,
            output_dir=self.export_dir,
            export_format="json",
        )

        with self.assertRaises(
            batch_exporters.BatchExportFileExistsError
        ):
            batch_exporters.export_batch(
                batch,
                output_dir=self.export_dir,
                export_format="json",
            )

    def test_overwrite_true_allows_reexport(self):
        batch = self.base_batch()

        batch_exporters.export_batch(
            batch,
            output_dir=self.export_dir,
            export_format="json",
        )

        info = batch_exporters.export_batch(
            batch,
            output_dir=self.export_dir,
            export_format="json",
            overwrite=True,
        )

        self.assertTrue(
            info["files"]["json"].exists()
        )

    def test_custom_export_name_is_used(self):
        info = batch_exporters.export_batch(
            self.base_batch(),
            output_dir=self.export_dir,
            export_format="json",
            export_name="my_batch",
        )

        self.assertEqual(
            info["files"]["json"].name,
            "my_batch.json",
        )


class TestStep19PersistenceSemantics(Step19Fixture):

    def test_no_save_export_does_not_create_analysis_runs(self):
        batch = self.base_batch(save=False)

        batch_exporters.export_batch(
            batch,
            output_dir=self.export_dir,
            export_format="json",
        )

        self.assertEqual(
            database.list_analysis_runs(
                self.db_path
            ),
            [],
        )

    def test_saved_batch_export_contains_run_ids(self):
        batch = self.base_batch(save=True)

        payload = batch_exporters.build_batch_export_payload(
            batch
        )

        run_ids = [
            pair["run_id"]
            for pair in payload["pairs"]
        ]

        self.assertTrue(
            all(
                isinstance(run_id, int)
                for run_id in run_ids
            )
        )

    def test_export_does_not_add_extra_runs_after_saved_batch(self):
        batch = self.base_batch(save=True)
        before = len(
            database.list_analysis_runs(
                self.db_path
            )
        )

        batch_exporters.export_batch(
            batch,
            output_dir=self.export_dir,
            export_format="json",
        )

        after = len(
            database.list_analysis_runs(
                self.db_path
            )
        )

        self.assertEqual(before, after)


class TestStep19CLI(Step19Fixture):

    def test_root_help_mentions_step19_and_previous_steps(self):
        text = command_cli.command_help_text()

        self.assertIn("STEP 19", text)
        self.assertIn("STEP 18", text)
        self.assertIn("STEP 17", text)
        self.assertIn("STEP 16", text)
        self.assertIn("STEP 15", text)

    def test_batch_help_mentions_export_options(self):
        text = command_cli._group_help("batch")

        self.assertIn("--export", text)
        self.assertIn("--export-format", text)
        self.assertIn("--export-dir", text)
        self.assertIn("--overwrite", text)
        self.assertIn("FULL computed batch", text)

    def test_cli_plain_batch_json_export(self):
        code, rendered = self.run_cli(
            "batch",
            "recipient",
            "RECIP-001",
            "--export",
            "--export-format",
            "json",
            "--export-dir",
            str(self.export_dir),
        )

        self.assertEqual(code, 0)
        self.assertIn("STEP 19", rendered)
        self.assertIn("Exported pairs: 3", rendered)

        files = list(
            self.export_dir.glob("*.json")
        )
        self.assertEqual(len(files), 1)

    def test_cli_ranked_export_contains_full_ordered_batch(self):
        code, rendered = self.run_cli(
            "batch",
            "recipient",
            "RECIP-001",
            "--sort-by",
            "donor-only",
            "--sort-level",
            "lgx",
            "--export",
            "--export-format",
            "json",
            "--export-dir",
            str(self.export_dir),
        )

        self.assertEqual(code, 0)
        self.assertIn(
            "Export ordering:",
            rendered,
        )

        path = next(
            self.export_dir.glob("*.json")
        )

        with path.open(
            "r",
            encoding="utf-8",
        ) as handle:
            payload = json.load(handle)

        self.assertEqual(
            payload["pairs"][0]["candidate"]["external_id"],
            "DONOR-FULL",
        )

    def test_cli_display_limit_does_not_truncate_export(self):
        code, rendered = self.run_cli(
            "batch",
            "recipient",
            "RECIP-001",
            "--sort-by",
            "donor-only",
            "--limit",
            "1",
            "--export",
            "--export-format",
            "json",
            "--export-dir",
            str(self.export_dir),
        )

        self.assertEqual(code, 0)
        self.assertIn(
            "displayed=1/3",
            rendered,
        )
        self.assertIn(
            "Exported pairs: 3",
            rendered,
        )
        self.assertIn(
            "does not truncate export",
            rendered,
        )

        path = next(
            self.export_dir.glob("*.json")
        )

        with path.open(
            "r",
            encoding="utf-8",
        ) as handle:
            payload = json.load(handle)

        self.assertEqual(
            len(payload["pairs"]),
            3,
        )

    def test_cli_export_options_without_export_are_rejected(self):
        code, rendered = self.run_cli(
            "batch",
            "recipient",
            "RECIP-001",
            "--export-format",
            "json",
        )

        self.assertEqual(code, 5)
        self.assertIn(
            "require --export",
            rendered,
        )

    def test_cli_overwrite_allows_second_export(self):
        common = (
            "batch",
            "recipient",
            "RECIP-001",
            "--export",
            "--export-format",
            "json",
            "--export-dir",
            str(self.export_dir),
        )

        first_code, _ = self.run_cli(*common)
        self.assertEqual(first_code, 0)

        second_code, _ = self.run_cli(
            *common,
            "--overwrite",
        )

        self.assertEqual(second_code, 0)

    def test_cli_existing_export_without_overwrite_errors(self):
        common = (
            "batch",
            "recipient",
            "RECIP-001",
            "--export",
            "--export-format",
            "json",
            "--export-dir",
            str(self.export_dir),
        )

        first_code, _ = self.run_cli(*common)
        self.assertEqual(first_code, 0)

        second_code, rendered = self.run_cli(
            *common
        )

        self.assertEqual(second_code, 5)
        self.assertIn(
            "вече съществува",
            rendered,
        )

    def test_cli_save_plus_export_preserves_all_runs_and_exports_all_pairs(self):
        code, rendered = self.run_cli(
            "batch",
            "recipient",
            "RECIP-001",
            "--sort-by",
            "donor-only",
            "--limit",
            "1",
            "--save",
            "--export",
            "--export-format",
            "csv",
            "--export-dir",
            str(self.export_dir),
        )

        self.assertEqual(code, 0)
        self.assertIn(
            "Persistence scope: ALL eligible pairs were saved",
            rendered,
        )
        self.assertIn(
            "CSV data rows represented: 72",
            rendered,
        )

        runs = database.list_analysis_runs(
            self.db_path
        )

        self.assertEqual(len(runs), 3)
        self.assertTrue(
            all(
                run["analysis_result_count"] == 24
                for run in runs
            )
        )

    def test_cli_export_summary_says_nonclinical(self):
        code, rendered = self.run_cli(
            "batch",
            "recipient",
            "RECIP-001",
            "--export",
            "--export-format",
            "json",
            "--export-dir",
            str(self.export_dir),
        )

        self.assertEqual(code, 0)
        self.assertIn(
            "NON-CLINICAL",
            rendered,
        )
