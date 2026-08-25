import importlib.util
import tempfile
from pathlib import Path
import unittest
from unittest.mock import patch

import audit_bundle
from backend_config import BackendSettings
import database
import doctor

from test_helpers import make_test_bundle


FASTAPI_AVAILABLE = (
    importlib.util.find_spec("fastapi") is not None
    and importlib.util.find_spec("httpx") is not None
)


FAKE_DOCTOR = {
    "schema": "hla-project-doctor-v1",
    "checks": [],
    "summary": {
        doctor.STATUS_OK: 1,
        doctor.STATUS_WARN: 0,
        doctor.STATUS_FAIL: 0,
    },
}


@unittest.skipUnless(FASTAPI_AVAILABLE, "FastAPI/httpx not installed")
class TestBackendApp(unittest.TestCase):

    def setUp(self):
        from fastapi.testclient import TestClient
        from backend_app import create_app

        self.temp = tempfile.TemporaryDirectory()
        root = Path(self.temp.name)
        self.db = root / "api.db"
        self.out = root / "exports"
        self.settings = BackendSettings(
            database_path=self.db,
            export_dir=self.out,
            api_key="secret",
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
        self.client = TestClient(create_app(self.settings))

    def tearDown(self):
        self.temp.cleanup()

    def headers(self):
        return {
            "X-API-Key": "secret",
            "X-Request-ID": "test-request",
        }

    def test_api_key_is_required(self):
        response = self.client.get("/health")
        self.assertEqual(response.status_code, 401)
        payload = response.json()
        self.assertEqual(payload["schema"], "hla-backend-api-v1")
        self.assertEqual(payload["error"], "Unauthorized")

        response = self.client.get("/v1/health")
        self.assertEqual(response.status_code, 401)

    def test_liveness_endpoint_does_not_require_api_key(self):
        response = self.client.get(
            "/v1/live",
            headers={"X-Request-ID": "probe-live"},
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.headers["X-Request-ID"], "probe-live")
        payload = response.json()
        self.assertEqual(payload["data"]["status"], "live")
        self.assertEqual(payload["data"]["api_version"], "v1")
        self.assertFalse(payload["clinical"])

    def test_readiness_endpoint_returns_probe_status(self):
        with patch("backend_services.doctor.run_doctor", return_value=FAKE_DOCTOR):
            response = self.client.get(
                "/v1/ready",
                headers={"X-Request-ID": "probe-ready"},
            )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.headers["X-Request-ID"], "probe-ready")
        payload = response.json()
        self.assertTrue(payload["data"]["ready"])
        self.assertEqual(payload["data"]["status"], "ready")

    def test_readiness_endpoint_returns_503_when_not_ready(self):
        from fastapi.testclient import TestClient
        from backend_app import create_app

        missing_db = Path(self.temp.name) / "missing.db"
        settings = BackendSettings(database_path=missing_db)
        client = TestClient(create_app(settings))
        response = client.get("/v1/ready")
        self.assertEqual(response.status_code, 503)
        self.assertFalse(response.json()["data"]["ready"])

    def test_health_endpoint(self):
        with patch("backend_services.doctor.run_doctor", return_value=FAKE_DOCTOR):
            response = self.client.get("/health", headers=self.headers())
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.headers["X-Request-ID"], "test-request")
        payload = response.json()
        self.assertTrue(payload["data"]["ready"])
        self.assertFalse(payload["clinical"])

    def test_v1_health_endpoint(self):
        with patch("backend_services.doctor.run_doctor", return_value=FAKE_DOCTOR):
            response = self.client.get("/v1/health", headers=self.headers())
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.json()["data"]["ready"])

    def test_live_report_endpoint(self):
        response = self.client.post(
            "/reports/live",
            headers=self.headers(),
            json={
                "direction": "recipient",
                "external_id": "RECIP-001",
                "include_text": True,
            },
        )
        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertEqual(payload["data"]["report"]["step"], 27)
        self.assertIn("STEP 27", payload["data"]["text"])

    def test_v1_live_report_endpoint(self):
        response = self.client.post(
            "/v1/reports/live",
            headers=self.headers(),
            json={
                "direction": "recipient",
                "external_id": "RECIP-001",
                "include_text": True,
            },
        )
        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertEqual(payload["data"]["report"]["step"], 27)
        self.assertIn("STEP 27", payload["data"]["text"])

    def test_level_comparison_endpoint(self):
        response = self.client.post(
            "/comparisons/levels",
            headers=self.headers(),
            json={
                "direction": "recipient",
                "external_id": "RECIP-001",
                "levels": ["lgx", "G"],
            },
        )
        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertEqual(payload["data"]["comparison"]["step"], 28)

    def test_audit_live_endpoint(self):
        with patch.object(audit_bundle.doctor, "run_doctor", return_value=FAKE_DOCTOR):
            response = self.client.post(
                "/audit/live",
                headers=self.headers(),
                json={
                    "direction": "recipient",
                    "external_id": "RECIP-001",
                    "bundle_name": "api-audit",
                    "zip_bundle": True,
                },
            )
        self.assertEqual(response.status_code, 200)
        info = response.json()["data"]["audit_bundle"]
        self.assertTrue(Path(info["bundle_dir"]).exists())
        self.assertTrue(Path(info["zip_path"]).exists())

    def test_io_error_uses_structured_response(self):
        with patch("backend_services.build_live_report", side_effect=OSError("disk full")):
            response = self.client.post(
                "/v1/reports/live",
                headers=self.headers(),
                json={
                    "direction": "recipient",
                    "external_id": "RECIP-001",
                },
            )
        payload = response.json()
        self.assertEqual(response.status_code, 503)
        self.assertEqual(payload["schema"], "hla-backend-api-v1")
        self.assertEqual(payload["request_id"], "test-request")
        self.assertFalse(payload["clinical"])
        self.assertEqual(payload["error"], "OSError")

    def test_encoding_error_uses_structured_response(self):
        error = UnicodeEncodeError("ascii", "Ж", 0, 1, "not encodable")
        with patch("backend_services.build_live_report", side_effect=error):
            response = self.client.post(
                "/v1/reports/live",
                headers=self.headers(),
                json={
                    "direction": "recipient",
                    "external_id": "RECIP-001",
                },
            )
        payload = response.json()
        self.assertEqual(response.status_code, 400)
        self.assertEqual(payload["schema"], "hla-backend-api-v1")
        self.assertEqual(payload["request_id"], "test-request")
        self.assertFalse(payload["clinical"])
        self.assertEqual(payload["error"], "UnicodeEncodeError")

    def test_validation_error_uses_structured_response(self):
        response = self.client.post(
            "/v1/reports/live",
            headers=self.headers(),
            json={},
        )
        payload = response.json()
        self.assertEqual(response.status_code, 422)
        self.assertEqual(payload["schema"], "hla-backend-api-v1")
        self.assertEqual(payload["error"], "RequestValidationError")
        self.assertEqual(payload["message"], "Request validation failed.")
        self.assertIn("details", payload)

    def test_openapi_contract_includes_versioned_paths(self):
        response = self.client.get("/openapi.json")
        self.assertEqual(response.status_code, 200)
        paths = response.json()["paths"]
        expected_paths = {
            "/v1",
            "/v1/live",
            "/v1/ready",
            "/v1/health",
            "/v1/doctor",
            "/v1/reports/live",
            "/v1/reports/batch",
            "/v1/comparisons/levels",
            "/v1/comparisons/batches",
            "/v1/audit/live",
            "/v1/audit/batches",
        }
        self.assertTrue(expected_paths.issubset(paths.keys()))
        self.assertNotIn("/reports/live", paths)
        self.assertIn("post", paths["/v1/reports/live"])
        self.assertIn("get", paths["/v1/ready"])


if __name__ == "__main__":
    unittest.main()
