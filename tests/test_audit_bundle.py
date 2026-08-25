import json
import tempfile
from pathlib import Path
import unittest
from unittest.mock import patch

import audit_bundle
import batch_analysis
import batch_history
import command_cli
import database
import doctor

from test_helpers import make_test_bundle


FAKE_DOCTOR = {
    "schema": "hla-project-doctor-v1",
    "checks": [],
    "summary": {
        doctor.STATUS_OK: 1,
        doctor.STATUS_WARN: 0,
        doctor.STATUS_FAIL: 0,
    },
}


class AuditBundleFixture(unittest.TestCase):

    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        root = Path(self.temp.name)
        self.db = root / "audit.db"
        self.out = root / "exports"
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
            "RECIP-001",
            "RECIPIENT",
            "3650",
            make_test_bundle(),
        )

    def tearDown(self):
        self.temp.cleanup()


class TestAuditBundle(AuditBundleFixture):

    def test_live_audit_bundle_creates_directory_and_zip(self):
        with patch.object(audit_bundle.doctor, "run_doctor", return_value=FAKE_DOCTOR):
            info = audit_bundle.create_live_audit_bundle(
                self.db,
                "recipient",
                "RECIP-001",
                output_dir=self.out,
                bundle_name="live-audit",
                zip_bundle=True,
            )

        self.assertEqual(info["mode"], "live")
        self.assertTrue(info["bundle_dir"].exists())
        self.assertTrue(info["zip_path"].exists())
        self.assertTrue((info["bundle_dir"] / "metadata.json").exists())
        self.assertTrue((info["bundle_dir"] / "step27_report.html").exists())
        self.assertTrue((info["bundle_dir"] / "step28_comparison.html").exists())
        metadata = json.loads(
            (info["bundle_dir"] / "metadata.json").read_text(encoding="utf-8")
        )
        self.assertEqual(metadata["schema"], audit_bundle.AUDIT_SCHEMA)
        self.assertEqual(metadata["mode"], "live")

    def test_existing_bundle_requires_overwrite(self):
        with patch.object(audit_bundle.doctor, "run_doctor", return_value=FAKE_DOCTOR):
            audit_bundle.create_live_audit_bundle(
                self.db,
                "recipient",
                "RECIP-001",
                output_dir=self.out,
                bundle_name="same-name",
            )
            with self.assertRaises(audit_bundle.AuditBundleExistsError):
                audit_bundle.create_live_audit_bundle(
                    self.db,
                    "recipient",
                    "RECIP-001",
                    output_dir=self.out,
                    bundle_name="same-name",
                )

    def test_batch_audit_bundle_creates_two_reports(self):
        batch1 = batch_analysis.run_batch_analysis(
            self.db,
            "recipient",
            "RECIP-001",
            save=False,
        )
        left = batch_history.persist_batch_with_runs(self.db, batch1)["batch_id"]
        batch2 = batch_analysis.run_batch_analysis(
            self.db,
            "recipient",
            "RECIP-001",
            save=False,
        )
        right = batch_history.persist_batch_with_runs(self.db, batch2)["batch_id"]

        with patch.object(audit_bundle.doctor, "run_doctor", return_value=FAKE_DOCTOR):
            info = audit_bundle.create_batch_audit_bundle(
                self.db,
                left,
                right,
                output_dir=self.out,
                bundle_name="batch-audit",
            )

        self.assertEqual(info["mode"], "batches")
        self.assertTrue((info["bundle_dir"] / "step27_left_report.html").exists())
        self.assertTrue((info["bundle_dir"] / "step27_right_report.html").exists())
        self.assertTrue((info["bundle_dir"] / "step28_comparison.html").exists())

    def test_cli_audit_recipient(self):
        output = []
        with patch.object(audit_bundle.doctor, "run_doctor", return_value=FAKE_DOCTOR):
            code = command_cli.run_command_cli(
                [
                    "--db", str(self.db),
                    "audit", "recipient", "RECIP-001",
                    "--output-dir", str(self.out),
                    "--name", "cli-audit",
                    "--zip",
                ],
                output_func=output.append,
            )

        rendered = "\n".join(output)
        self.assertEqual(code, 0)
        self.assertIn("HLA AUDIT BUNDLE CREATED", rendered)
        self.assertTrue((self.out / "cli-audit").exists())
        self.assertTrue((self.out / "cli-audit.zip").exists())


if __name__ == "__main__":
    unittest.main()
