from __future__ import annotations

from pathlib import Path
import sys

import database
from config import IMGTHLA_VERSION, PYARD_DATA_DIR

try:
    import pyard
except ModuleNotFoundError:  # pragma: no cover - environment dependent
    pyard = None


STATUS_OK = "OK"
STATUS_WARN = "WARN"
STATUS_FAIL = "FAIL"


class DoctorError(RuntimeError):
    """Unexpected doctor command failure."""


def _check(name, status, detail):
    return {
        "name": name,
        "status": status,
        "detail": detail,
    }


def _count_rows(conn, table_name):
    row = conn.execute(
        f'SELECT COUNT(*) FROM "{table_name}"'
    ).fetchone()
    return int(row[0])


def run_doctor(database_path=database.DEFAULT_DATABASE_PATH):
    """Build a side-effect-light health report for the local project."""
    checks = []

    version = sys.version_info
    python_detail = (
        f"{version.major}.{version.minor}.{version.micro} "
        f"({sys.executable})"
    )
    checks.append(
        _check(
            "Python runtime",
            STATUS_OK if version >= (3, 10) else STATUS_FAIL,
            python_detail,
        )
    )

    if pyard is None:
        checks.append(
            _check(
                "py-ard package",
                STATUS_FAIL,
                "py-ard is not importable; install dependencies first.",
            )
        )
    else:
        checks.append(
            _check(
                "py-ard package",
                STATUS_OK,
                f"version {getattr(pyard, '__version__', 'unknown')}",
            )
        )

    data_dir = Path(PYARD_DATA_DIR)
    data_file = data_dir / f"pyard-{IMGTHLA_VERSION}.sqlite3"
    if data_file.exists():
        checks.append(
            _check(
                "py-ard data",
                STATUS_OK,
                str(data_file),
            )
        )
    elif data_dir.exists():
        checks.append(
            _check(
                "py-ard data",
                STATUS_FAIL,
                f"Missing expected data file: {data_file}",
            )
        )
    else:
        checks.append(
            _check(
                "py-ard data",
                STATUS_FAIL,
                f"Missing data directory: {data_dir}",
            )
        )

    database_path = Path(database_path)
    status = database.get_database_schema_status(database_path)
    if not status["exists"]:
        checks.append(
            _check(
                "SQLite database",
                STATUS_FAIL,
                f"Missing database: {database_path}",
            )
        )
    else:
        checks.append(
            _check(
                "SQLite database",
                STATUS_OK,
                str(database_path),
            )
        )
        checks.append(
            _check(
                "SQLite schema version",
                STATUS_OK if status["is_current"] else STATUS_FAIL,
                (
                    f"current={status['current_version']} "
                    f"required={status['required_version']}"
                ),
            )
        )
        checks.append(
            _check(
                "analysis_results unique key",
                STATUS_OK if status["analysis_results_unique_key"] else STATUS_FAIL,
                "UNIQUE(run_id, level, locus)",
            )
        )
        checks.append(
            _check(
                "batch history schema",
                STATUS_OK if status.get("batch_history_schema") else STATUS_FAIL,
                "batch_runs / batch_run_items",
            )
        )

        try:
            integrity = database.integrity_check(database_path)
        except Exception as exc:  # pragma: no cover - defensive guard
            checks.append(
                _check(
                    "SQLite integrity",
                    STATUS_FAIL,
                    str(exc),
                )
            )
        else:
            checks.append(
                _check(
                    "SQLite integrity",
                    STATUS_OK if integrity == "ok" else STATUS_FAIL,
                    integrity,
                )
            )

        try:
            conn = database.connect_db(database_path)
            try:
                subject_count = _count_rows(conn, "subjects")
                typing_count = _count_rows(conn, "hla_typings")
                analysis_count = _count_rows(conn, "analysis_runs")
                batch_count = _count_rows(conn, "batch_runs")
                subject_types = {
                    row[0]
                    for row in conn.execute(
                        "SELECT DISTINCT subject_type FROM subjects"
                    ).fetchall()
                }
            finally:
                conn.close()
        except Exception as exc:  # pragma: no cover - defensive guard
            checks.append(
                _check(
                    "Demo data",
                    STATUS_WARN,
                    f"Could not inspect demo data: {exc}",
                )
            )
        else:
            has_demo_pair = {"DONOR", "RECIPIENT"}.issubset(subject_types)
            checks.append(
                _check(
                    "Demo data",
                    STATUS_OK if has_demo_pair else STATUS_WARN,
                    (
                        f"subjects={subject_count}, typings={typing_count}, "
                        f"analysis_runs={analysis_count}, batches={batch_count}"
                    ),
                )
            )

    export_root = Path("exports")
    parent = export_root.parent.resolve()
    checks.append(
        _check(
            "Export location",
            STATUS_OK if parent.exists() else STATUS_FAIL,
            f"{export_root} can be created under {parent}",
        )
    )

    return {
        "schema": "hla-project-doctor-v1",
        "checks": checks,
        "summary": {
            STATUS_OK: sum(1 for item in checks if item["status"] == STATUS_OK),
            STATUS_WARN: sum(1 for item in checks if item["status"] == STATUS_WARN),
            STATUS_FAIL: sum(1 for item in checks if item["status"] == STATUS_FAIL),
        },
    }


def doctor_exit_code(report):
    return 0 if report["summary"][STATUS_FAIL] == 0 else 8


def render_doctor(report):
    lines = [
        "=" * 88,
        "HLA PROJECT DOCTOR",
        "=" * 88,
    ]
    for check in report["checks"]:
        lines.append(
            f"[{check['status']:<4}] {check['name']}: {check['detail']}"
        )
    summary = report["summary"]
    lines.extend(
        [
            "-" * 88,
            (
                "Summary: "
                f"OK={summary[STATUS_OK]} "
                f"WARN={summary[STATUS_WARN]} "
                f"FAIL={summary[STATUS_FAIL]}"
            ),
            "Doctor is diagnostic only; it does not migrate or modify data.",
            "=" * 88,
        ]
    )
    return "\n".join(lines)
