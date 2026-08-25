from __future__ import annotations

from dataclasses import dataclass
import os
from pathlib import Path

import audit_bundle
import database


TRUE_VALUES = {"1", "true", "yes", "on"}
DEFAULT_BACKEND_ENV_FILE = Path("backend.env")


class BackendConfigError(ValueError):
    """Invalid backend runtime configuration."""


@dataclass(frozen=True)
class BackendSettings:
    database_path: Path = database.DEFAULT_DATABASE_PATH
    export_dir: Path = audit_bundle.DEFAULT_EXPORT_DIR
    auto_migrate: bool = False
    api_key: str | None = None
    cors_origins: tuple[str, ...] = ()
    app_name: str = "HLA Transplantation Backend"
    host: str = "127.0.0.1"
    port: int = 8000
    log_level: str = "INFO"
    env_file: Path | None = None


def _bool_from_env(value, default=False):
    if value is None:
        return default
    return value.strip().lower() in TRUE_VALUES


def _int_from_env(value, *, default, name):
    if value is None or str(value).strip() == "":
        return default
    try:
        number = int(str(value).strip())
    except ValueError as exc:
        raise BackendConfigError(f"{name} must be an integer.") from exc
    if not 1 <= number <= 65535:
        raise BackendConfigError(f"{name} must be between 1 and 65535.")
    return number


def _origins_from_env(value):
    if not value:
        return ()
    return tuple(
        item.strip()
        for item in value.split(",")
        if item.strip()
    )


def _unquote_env_value(value):
    value = value.strip()
    if len(value) >= 2 and value[0] == value[-1] and value[0] in {"'", '"'}:
        return value[1:-1]
    return value


def read_backend_env_file(path):
    path = Path(path)
    values = {}
    try:
        lines = path.read_text(encoding="utf-8-sig").splitlines()
    except OSError as exc:
        raise BackendConfigError(f"Could not read backend env file: {path}") from exc

    for line_number, line in enumerate(lines, start=1):
        stripped = line.strip()
        if not stripped or stripped.startswith("#"):
            continue
        if "=" not in stripped:
            raise BackendConfigError(
                f"Invalid backend env line {line_number} in {path}: missing '='."
            )
        key, value = stripped.split("=", 1)
        key = key.strip()
        if not key:
            raise BackendConfigError(
                f"Invalid backend env line {line_number} in {path}: empty key."
            )
        values[key] = _unquote_env_value(value)
    return values


def load_backend_environment(env=None, env_file=None):
    runtime_env = os.environ if env is None else env
    runtime_values = {
        str(key): str(value)
        for key, value in runtime_env.items()
        if value is not None
    }

    explicit_env_file = env_file or runtime_values.get("HLA_BACKEND_ENV_FILE")
    if explicit_env_file:
        path = Path(explicit_env_file)
        required = True
    else:
        path = DEFAULT_BACKEND_ENV_FILE
        required = False

    file_values = {}
    loaded_env_file = None
    if path.exists():
        file_values = read_backend_env_file(path)
        loaded_env_file = path
    elif required:
        raise BackendConfigError(f"Backend env file does not exist: {path}")

    merged = dict(file_values)
    merged.update(runtime_values)
    return merged, loaded_env_file


def load_backend_settings(env=None, env_file=None):
    env, loaded_env_file = load_backend_environment(env=env, env_file=env_file)
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
        host=env.get("HLA_BACKEND_HOST", "127.0.0.1"),
        port=_int_from_env(
            env.get("HLA_BACKEND_PORT"),
            default=8000,
            name="HLA_BACKEND_PORT",
        ),
        log_level=env.get("HLA_BACKEND_LOG_LEVEL", "INFO"),
        env_file=loaded_env_file,
    )
