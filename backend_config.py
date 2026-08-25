from __future__ import annotations

from dataclasses import dataclass
import os
from pathlib import Path

import audit_bundle
import database


TRUE_VALUES = {"1", "true", "yes", "on"}


@dataclass(frozen=True)
class BackendSettings:
    database_path: Path = database.DEFAULT_DATABASE_PATH
    export_dir: Path = audit_bundle.DEFAULT_EXPORT_DIR
    auto_migrate: bool = False
    api_key: str | None = None
    cors_origins: tuple[str, ...] = ()
    app_name: str = "HLA Transplantation Backend"


def _bool_from_env(value, default=False):
    if value is None:
        return default
    return value.strip().lower() in TRUE_VALUES


def _origins_from_env(value):
    if not value:
        return ()
    return tuple(
        item.strip()
        for item in value.split(",")
        if item.strip()
    )


def load_backend_settings(env=None):
    env = os.environ if env is None else env
    return BackendSettings(
        database_path=Path(
            env.get("HLA_BACKEND_DATABASE_PATH", database.DEFAULT_DATABASE_PATH)
        ),
        export_dir=Path(
            env.get("HLA_BACKEND_EXPORT_DIR", audit_bundle.DEFAULT_EXPORT_DIR)
        ),
        auto_migrate=_bool_from_env(env.get("HLA_BACKEND_AUTO_MIGRATE")),
        api_key=env.get("HLA_BACKEND_API_KEY") or None,
        cors_origins=_origins_from_env(env.get("HLA_BACKEND_CORS_ORIGINS")),
        app_name=env.get("HLA_BACKEND_APP_NAME", "HLA Transplantation Backend"),
    )
