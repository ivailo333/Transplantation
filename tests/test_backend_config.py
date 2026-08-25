from pathlib import Path
import unittest

from backend_config import load_backend_settings


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


if __name__ == "__main__":
    unittest.main()
