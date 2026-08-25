from pathlib import Path
import sqlite3

import migrations as migrations
from config import HLA_LOCI, ANALYSIS_LEVELS, SUBJECT_TYPES

DEFAULT_DATABASE_PATH = Path(__file__).with_name("transplant.db")

CURRENT_SCHEMA_VERSION = migrations.CURRENT_SCHEMA_VERSION
MigrationError = migrations.MigrationError
MigrationConflictError = migrations.MigrationConflictError


class DatabaseSchemaError(RuntimeError):
    """Съществуващата SQLite схема не е съвместима с приложението."""


SCHEMA_SQL = """
CREATE TABLE IF NOT EXISTS subjects (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    external_id TEXT NOT NULL UNIQUE,
    subject_type TEXT NOT NULL
        CHECK(subject_type IN ('DONOR', 'RECIPIENT')),
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS hla_typings (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    subject_id INTEGER NOT NULL,
    imgthla_version TEXT NOT NULL,
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY(subject_id) REFERENCES subjects(id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS hla_alleles (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    typing_id INTEGER NOT NULL,
    locus TEXT NOT NULL
        CHECK(locus IN ('A', 'B', 'C', 'DRB1', 'DQB1', 'DPB1')),
    allele_number INTEGER NOT NULL
        CHECK(allele_number IN (1, 2)),
    raw_value TEXT NOT NULL,
    canonical_value TEXT NOT NULL,
    lgx_value TEXT NOT NULL,
    g_value TEXT NOT NULL,
    p_value TEXT NOT NULL,
    FOREIGN KEY(typing_id) REFERENCES hla_typings(id) ON DELETE CASCADE,
    UNIQUE(typing_id, locus, allele_number)
);

CREATE TABLE IF NOT EXISTS analysis_runs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    donor_typing_id INTEGER NOT NULL,
    recipient_typing_id INTEGER NOT NULL,
    imgthla_version TEXT NOT NULL,
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY(donor_typing_id) REFERENCES hla_typings(id),
    FOREIGN KEY(recipient_typing_id) REFERENCES hla_typings(id)
);

CREATE TABLE IF NOT EXISTS analysis_results (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    run_id INTEGER NOT NULL,
    level TEXT NOT NULL
        CHECK(level IN ('CANONICAL', 'LGX', 'G', 'P')),
    locus TEXT NOT NULL
        CHECK(locus IN ('A', 'B', 'C', 'DRB1', 'DQB1', 'DPB1')),
    shared_count INTEGER NOT NULL CHECK(shared_count >= 0),
    donor_only_count INTEGER NOT NULL CHECK(donor_only_count >= 0),
    recipient_only_count INTEGER NOT NULL CHECK(recipient_only_count >= 0),
    shared_values TEXT NOT NULL,
    donor_only_values TEXT NOT NULL,
    recipient_only_values TEXT NOT NULL,
    FOREIGN KEY(run_id) REFERENCES analysis_runs(id) ON DELETE CASCADE,
    UNIQUE(run_id, level, locus)
);

CREATE INDEX IF NOT EXISTS idx_hla_typings_subject_id
    ON hla_typings(subject_id);
CREATE INDEX IF NOT EXISTS idx_hla_alleles_typing_id
    ON hla_alleles(typing_id);
CREATE INDEX IF NOT EXISTS idx_analysis_runs_donor_typing_id
    ON analysis_runs(donor_typing_id);
CREATE INDEX IF NOT EXISTS idx_analysis_runs_recipient_typing_id
    ON analysis_runs(recipient_typing_id);
CREATE INDEX IF NOT EXISTS idx_analysis_results_run_id
    ON analysis_results(run_id);
""" + migrations.BATCH_HISTORY_SCHEMA_SQL


REQUIRED_COLUMNS = {
    "schema_migrations": {
        "version",
        "name",
        "applied_at",
    },
    "subjects": {
        "id",
        "external_id",
        "subject_type",
        "created_at",
    },
    "hla_typings": {
        "id",
        "subject_id",
        "imgthla_version",
        "created_at",
    },
    "hla_alleles": {
        "id",
        "typing_id",
        "locus",
        "allele_number",
        "raw_value",
        "canonical_value",
        "lgx_value",
        "g_value",
        "p_value",
    },
    "analysis_runs": {
        "id",
        "donor_typing_id",
        "recipient_typing_id",
        "imgthla_version",
        "created_at",
    },
    "analysis_results": {
        "id",
        "run_id",
        "level",
        "locus",
        "shared_count",
        "donor_only_count",
        "recipient_only_count",
        "shared_values",
        "donor_only_values",
        "recipient_only_values",
    },
    "batch_runs": {
        "id",
        "direction",
        "anchor_typing_id",
        "imgthla_version",
        "pair_count",
        "skipped_count",
        "skipped_json",
        "sort_level",
        "sort_metric",
        "sort_order",
        "requested_sort_order",
        "display_limit",
        "created_at",
    },
    "batch_run_items": {
        "id",
        "batch_id",
        "analysis_run_id",
        "candidate_typing_id",
        "item_position",
        "software_position",
        "software_rank",
        "criterion_value",
    },
}


def connect_db(database_path=DEFAULT_DATABASE_PATH):
    """Отваря SQLite връзка и включва foreign-key проверките."""
    conn = sqlite3.connect(str(database_path))
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def initialize_database(database_path=DEFAULT_DATABASE_PATH):
    """
    Създава core schema и автоматично прилага pending migrations.
    """
    migrate_database(database_path)
    return Path(database_path)


def migrate_database(database_path=DEFAULT_DATABASE_PATH):
    """
    Осигурява core tables и прилага pending migrations.
    Подходящо е и за вече съществуващ transplant.db.
    """
    database_path = Path(database_path)
    database_path.parent.mkdir(parents=True, exist_ok=True)

    conn = connect_db(database_path)

    try:
        conn.executescript(SCHEMA_SQL)
        conn.commit()

        applied = migrations.apply_pending_migrations(conn)

        return {
            "database_path": database_path,
            "applied": applied,
            "current_version": (
                migrations.get_current_schema_version(conn)
            ),
            "required_version": migrations.CURRENT_SCHEMA_VERSION,
            "analysis_results_unique_key": (
                migrations.has_analysis_results_unique_key(conn)
            ),
            "batch_history_schema": (
                migrations.has_batch_history_schema(conn)
            ),
        }
    finally:
        conn.close()


def get_database_schema_status(
    database_path=DEFAULT_DATABASE_PATH,
):
    """
    Read-only status. Ако файлът не съществува, не го създава.
    """
    database_path = Path(database_path)

    if not database_path.exists():
        return {
            "database_path": database_path,
            "exists": False,
            "current_version": 0,
            "required_version": migrations.CURRENT_SCHEMA_VERSION,
            "is_current": False,
            "pending": [
                {
                    "version": migration.version,
                    "name": migration.name,
                }
                for migration in migrations.MIGRATIONS
            ],
            "history": [],
            "analysis_results_unique_key": False,
            "batch_history_schema": False,
        }

    conn = connect_db(database_path)

    try:
        status = migrations.inspect_database_status(conn)
        status["database_path"] = database_path
        status["exists"] = True
        return status
    finally:
        conn.close()


def get_migration_history(
    database_path=DEFAULT_DATABASE_PATH,
):
    database_path = Path(database_path)

    if not database_path.exists():
        return []

    conn = connect_db(database_path)

    try:
        return migrations.get_applied_migrations(conn)
    finally:
        conn.close()


def verify_database_is_current(
    database_path=DEFAULT_DATABASE_PATH,
):
    status = get_database_schema_status(database_path)

    if not status["exists"]:
        raise DatabaseSchemaError(
            f"SQLite базата не съществува: {database_path}"
        )

    if not status["is_current"]:
        pending = [
            item["version"]
            for item in status["pending"]
        ]

        raise DatabaseSchemaError(
            "SQLite schema migration е необходима. "
            f"Current={status['current_version']}, "
            f"required={status['required_version']}, "
            f"pending={pending}."
        )

    if not status["analysis_results_unique_key"]:
        raise DatabaseSchemaError(
            "Липсва UNIQUE key върху "
            "analysis_results(run_id, level, locus)."
        )

    if not status.get("batch_history_schema", False):
        raise DatabaseSchemaError(
            "Липсва STEP 20 batch history schema "
            "(batch_runs / batch_run_items)."
        )

    return True


def get_table_names(database_path=DEFAULT_DATABASE_PATH):
    conn = connect_db(database_path)
    try:
        rows = conn.execute(
            """
            SELECT name
            FROM sqlite_master
            WHERE type = 'table'
              AND name NOT LIKE 'sqlite_%'
            ORDER BY name
            """
        ).fetchall()
        return [row[0] for row in rows]
    finally:
        conn.close()


def get_foreign_keys_enabled(database_path=DEFAULT_DATABASE_PATH):
    conn = connect_db(database_path)
    try:
        value = conn.execute("PRAGMA foreign_keys").fetchone()[0]
        return bool(value)
    finally:
        conn.close()


def integrity_check(database_path=DEFAULT_DATABASE_PATH):
    conn = connect_db(database_path)
    try:
        return conn.execute("PRAGMA integrity_check").fetchone()[0]
    finally:
        conn.close()


def verify_schema_compatibility(database_path=DEFAULT_DATABASE_PATH):
    """
    Проверява дали съществуващите таблици имат минимум нужните колони.

    Допълнителни колони са позволени. Нищо не се променя в базата.
    """
    conn = connect_db(database_path)
    try:
        tables = {
            row[0]
            for row in conn.execute(
                """
                SELECT name
                FROM sqlite_master
                WHERE type = 'table'
                  AND name NOT LIKE 'sqlite_%'
                """
            ).fetchall()
        }

        problems = []

        for table, required_columns in REQUIRED_COLUMNS.items():
            if table not in tables:
                problems.append(f"липсва таблица: {table}")
                continue

            # Името на таблицата идва само от константата REQUIRED_COLUMNS.
            rows = conn.execute(f'PRAGMA table_info("{table}")').fetchall()
            actual_columns = {row[1] for row in rows}
            missing = sorted(required_columns - actual_columns)

            if missing:
                problems.append(
                    f"{table}: липсващи колони: {', '.join(missing)}"
                )

        if problems:
            raise DatabaseSchemaError(
                "SQLite схемата не е съвместима със STEP 13B/13C:\n- "
                + "\n- ".join(problems)
            )

        return True
    finally:
        conn.close()


# Public compatibility facade.
# Domain logic lives in subjects.py, typings.py and analyses.py.
from subjects import (  # noqa: E402
    SubjectTypeConflictError,
    SubjectNotFoundError,
    list_subjects,
)
from typings import (  # noqa: E402
    TypingNotFoundError,
    IncompleteTypingError,
    validate_typing_bundle,
    save_subject_typing,
    save_typing_records_atomic,
    save_donor_recipient_typings,
    list_subject_typings,
    load_subject_typing,
    load_subject_profile,
)
from analyses import (  # noqa: E402
    AnalysisRunNotFoundError,
    AnalysisTypingRoleError,
    AnalysisVersionMismatchError,
    AnalysisResultsError,
    AnalysisResultsNotFoundError,
    create_analysis_run,
    create_analysis_run_for_subjects,
    load_analysis_run,
    list_analysis_runs,
    load_analysis_run_typings,
    validate_analysis_results_structure,
    save_analysis_results,
    save_batch_analysis_runs,
    load_analysis_results,
)

from batch_history import (  # noqa: E402
    BatchRunNotFoundError,
    BatchHistoryError,
    BatchHistoryIntegrityError,
    persist_batch_with_runs,
    list_batch_runs,
    load_batch_run,
    load_batch_results,
)
