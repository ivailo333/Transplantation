import tempfile
from pathlib import Path
import unittest
from unittest.mock import patch

import audit_bundle
import backend_services
from backend_config import BackendSettings
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


class BackendServiceFixture(unittest.TestCase):

    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        root = Path(self.temp.name)
        self.db = root / "backend.db"
        self.out = root / "exports"
        self.settings = BackendSettings(
            database_path=self.db,
            export_dir=self.out,
        )
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


class TestBackendServices(BackendServiceFixture):

    def test_metadata_response_is_non_clinical(self):
        response = backend_services.backend_metadata(
            self.settings,
            request_id="rid-1",
        )
        self.assertEqual(
            response["schema"],
            backend_services.BACKEND_RESPONSE_SCHEMA,
        )
        self.assertEqual(response["request_id"], "rid-1")
        self.assertFalse(response["clinical"])
        self.assertIn("/reports/live", response["data"]["supported_endpoints"])

    def test_health_includes_schema_and_doctor_summary(self):
        with patch.object(
            backend_services.doctor,
            "run_doctor",
            return_value=FAKE_DOCTOR,
        ):
            response = backend_services.health(self.settings)
        self.assertTrue(response["data"]["ready"])
        self.assertTrue(response["data"]["schema_status"]["is_current"])
        self.assertEqual(
            response["data"]["doctor_summary"][doctor.STATUS_FAIL],
            0,
        )

    def test_live_report_response(self):
        response = backend_services.build_live_report(
            self.settings,
            {
                "direction": "recipient",
                "external_id": "RECIP-001",
                "include_text": True,
            },
            request_id="rid-2",
        )
        data = response["data"]
        self.assertEqual(response["request_id"], "rid-2")
        self.assertEqual(data["report"]["step"], 27)
        self.assertIn("STEP 27", data["text"])

    def test_live_report_can_export_all(self):
        response = backend_services.build_live_report(
            self.settings,
            {
                "direction": "recipient",
                "external_id": "RECIP-001",
                "export_format": "all",
                "export_name": "api-report",
            },
        )
        export = response["data"]["export"]
        self.assertEqual(export["format"], "ALL")
        self.assertTrue(Path(export["json_path"]).exists())
        self.assertTrue(Path(export["csv_path"]).exists())
        self.assertTrue(Path(export["html_path"]).exists())

    def test_level_comparison_response(self):
        response = backend_services.build_level_comparison(
            self.settings,
            {
                "direction": "recipient",
                "external_id": "RECIP-001",
                "levels": ["lgx", "G"],
            },
        )
        comparison = response["data"]["comparison"]
        self.assertEqual(comparison["step"], 28)
        self.assertEqual(comparison["mode"], "levels")

    def test_live_audit_response_serializes_paths(self):
        with patch.object(audit_bundle.doctor, "run_doctor", return_value=FAKE_DOCTOR):
            response = backend_services.create_live_audit(
                self.settings,
                {
                    "direction": "recipient",
                    "external_id": "RECIP-001",
                    "bundle_name": "api-audit",
                    "zip_bundle": True,
                },
            )
        info = response["data"]["audit_bundle"]
        self.assertIsInstance(info["bundle_dir"], str)
        self.assertTrue(Path(info["bundle_dir"]).exists())
        self.assertTrue(Path(info["zip_path"]).exists())


if __name__ == "__main__":
    unittest.main()
