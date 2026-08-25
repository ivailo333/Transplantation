import json
import tempfile
from pathlib import Path
from types import SimpleNamespace
import unittest
from unittest.mock import patch

import command_cli
import database
import doctor


class TestDoctor(unittest.TestCase):

    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        root = Path(self.temp.name)
        self.db = root / "doctor.db"
        self.data_dir = root / "pyard-data"
        self.data_dir.mkdir()
        (self.data_dir / "pyard-3650.sqlite3").write_text(
            "placeholder",
            encoding="utf-8",
        )
        database.initialize_database(self.db)

    def tearDown(self):
        self.temp.cleanup()

    def test_run_doctor_reports_no_failures_for_ready_project(self):
        fake_pyard = SimpleNamespace(__version__="test")
        with patch.object(doctor, "pyard", fake_pyard), patch.object(
            doctor, "PYARD_DATA_DIR", self.data_dir
        ):
            report = doctor.run_doctor(self.db)

        self.assertEqual(report["schema"], "hla-project-doctor-v1")
        self.assertEqual(report["summary"][doctor.STATUS_FAIL], 0)
        self.assertEqual(doctor.doctor_exit_code(report), 0)
        rendered = doctor.render_doctor(report)
        self.assertIn("HLA PROJECT DOCTOR", rendered)
        self.assertIn("SQLite schema version", rendered)
        self.assertIn("Doctor is diagnostic only", rendered)

    def test_render_doctor_json(self):
        report = {
            "schema": "hla-project-doctor-v1",
            "checks": [],
            "summary": {
                doctor.STATUS_OK: 0,
                doctor.STATUS_WARN: 0,
                doctor.STATUS_FAIL: 0,
            },
        }
        payload = json.loads(doctor.render_doctor_json(report))
        self.assertEqual(payload["schema"], "hla-project-doctor-v1")
        self.assertEqual(payload["summary"][doctor.STATUS_FAIL], 0)

    def test_cli_doctor_json_renders_machine_readable_report(self):
        report = {
            "schema": "hla-project-doctor-v1",
            "checks": [],
            "summary": {
                doctor.STATUS_OK: 0,
                doctor.STATUS_WARN: 0,
                doctor.STATUS_FAIL: 0,
            },
        }
        output = []
        with patch.object(command_cli.doctor, "run_doctor", return_value=report):
            code = command_cli.run_command_cli(
                ["--db", str(self.db), "doctor", "--json"],
                output_func=output.append,
            )

        self.assertEqual(code, 0)
        payload = json.loads("\n".join(output))
        self.assertEqual(payload["schema"], "hla-project-doctor-v1")

    def test_cli_doctor_command_renders_report(self):
        report = {
            "schema": "hla-project-doctor-v1",
            "checks": [
                {
                    "name": "Python runtime",
                    "status": doctor.STATUS_OK,
                    "detail": "test",
                }
            ],
            "summary": {
                doctor.STATUS_OK: 1,
                doctor.STATUS_WARN: 0,
                doctor.STATUS_FAIL: 0,
            },
        }
        output = []
        with patch.object(command_cli.doctor, "run_doctor", return_value=report):
            code = command_cli.run_command_cli(
                ["--db", str(self.db), "doctor"],
                output_func=output.append,
            )

        self.assertEqual(code, 0)
        self.assertIn("HLA PROJECT DOCTOR", "\n".join(output))


if __name__ == "__main__":
    unittest.main()
