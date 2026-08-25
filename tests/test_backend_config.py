from pathlib import Path
import tempfile
import unittest

from backend_config import (
    BackendConfigError,
    load_backend_settings,
    read_backend_env_file,
)


class TestBackendConfig(unittest.TestCase):

    def test_loads_settings_from_env(self):
        settings = load_backend_settings(
            {
                "HLA_BACKEND_DATABASE_PATH": "custom.db",
                "HLA_BACKEND_EXPORT_DIR": "out/audit",
                "HLA_BACKEND_AUTO_MIGRATE": "true",
                "HLA_BACKEND_API_KEY": "secret",
                "HLA_BACKEND_CORS_ORIGINS": "https://app.example, http://localhost:3000",
                "HLA_BACKEND_APP_NAME": "Custom Backend",
                "HLA_BACKEND_HOST": "0.0.0.0",
                "HLA_BACKEND_PORT": "9000",
                "HLA_BACKEND_LOG_LEVEL": "DEBUG",
            }
        )
        self.assertEqual(settings.database_path, Path("custom.db"))
        self.assertEqual(settings.export_dir, Path("out/audit"))
        self.assertTrue(settings.auto_migrate)
        self.assertEqual(settings.api_key, "secret")
        self.assertEqual(
            settings.cors_origins,
            ("https://app.example", "http://localhost:3000"),
        )
        self.assertEqual(settings.app_name, "Custom Backend")
        self.assertEqual(settings.host, "0.0.0.0")
        self.assertEqual(settings.port, 9000)
        self.assertEqual(settings.log_level, "DEBUG")

    def test_loads_settings_from_env_file(self):
        with tempfile.TemporaryDirectory() as temp:
            env_file = Path(temp) / "backend.env"
            env_file.write_text(
                "\n".join(
                    [
                        "# backend settings",
                        "HLA_BACKEND_DATABASE_PATH=file.db",
                        "HLA_BACKEND_EXPORT_DIR='file-exports'",
                        "HLA_BACKEND_PORT=8100",
                        "HLA_BACKEND_APP_NAME=File Backend",
                    ]
                ),
                encoding="utf-8",
            )
            settings = load_backend_settings(env={}, env_file=env_file)
        self.assertEqual(settings.database_path, Path("file.db"))
        self.assertEqual(settings.export_dir, Path("file-exports"))
        self.assertEqual(settings.port, 8100)
        self.assertEqual(settings.app_name, "File Backend")
        self.assertEqual(settings.env_file, env_file)

    def test_environment_overrides_env_file(self):
        with tempfile.TemporaryDirectory() as temp:
            env_file = Path(temp) / "backend.env"
            env_file.write_text(
                "HLA_BACKEND_DATABASE_PATH=file.db\nHLA_BACKEND_PORT=8100\n",
                encoding="utf-8",
            )
            settings = load_backend_settings(
                env={
                    "HLA_BACKEND_ENV_FILE": str(env_file),
                    "HLA_BACKEND_DATABASE_PATH": "override.db",
                }
            )
        self.assertEqual(settings.database_path, Path("override.db"))
        self.assertEqual(settings.port, 8100)
        self.assertEqual(settings.env_file, env_file)

    def test_missing_explicit_env_file_raises(self):
        with self.assertRaises(BackendConfigError):
            load_backend_settings(env={"HLA_BACKEND_ENV_FILE": "missing.env"})

    def test_invalid_port_raises(self):
        with self.assertRaises(BackendConfigError):
            load_backend_settings(env={"HLA_BACKEND_PORT": "not-a-port"})

    def test_invalid_env_file_line_raises(self):
        with tempfile.TemporaryDirectory() as temp:
            env_file = Path(temp) / "backend.env"
            env_file.write_text("BROKEN_LINE\n", encoding="utf-8")
            with self.assertRaises(BackendConfigError):
                read_backend_env_file(env_file)


if __name__ == "__main__":
    unittest.main()
