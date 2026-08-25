from dataclasses import dataclass
import sqlite3


CURRENT_SCHEMA_VERSION = 3

MIGRATIONS_TABLE = "schema_migrations"
UNIQUE_RESULTS_INDEX = "uq_analysis_results_run_level_locus"
BATCH_RUNS_TABLE = "batch_runs"
BATCH_RUN_ITEMS_TABLE = "batch_run_items"

BATCH_HISTORY_SCHEMA_SQL = """
CREATE TABLE IF NOT EXISTS batch_runs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    direction TEXT NOT NULL
        CHECK(direction IN ('recipient', 'donor')),
    anchor_typing_id INTEGER NOT NULL,
    imgthla_version TEXT NOT NULL,
    pair_count INTEGER NOT NULL CHECK(pair_count > 0),
    skipped_count INTEGER NOT NULL DEFAULT 0 CHECK(skipped_count >= 0),
    skipped_json TEXT NOT NULL DEFAULT '[]',
    sort_level TEXT
        CHECK(sort_level IS NULL OR sort_level IN ('canonical', 'lgx', 'G', 'P')),
    sort_metric TEXT
        CHECK(sort_metric IS NULL OR sort_metric IN ('donor-only', 'shared', 'recipient-only')),
    sort_order TEXT
        CHECK(sort_order IS NULL OR sort_order IN ('asc', 'desc')),
    requested_sort_order TEXT
        CHECK(requested_sort_order IS NULL OR requested_sort_order IN ('auto', 'asc', 'desc')),
    display_limit INTEGER
        CHECK(display_limit IS NULL OR display_limit > 0),
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY(anchor_typing_id) REFERENCES hla_typings(id)
);

CREATE TABLE IF NOT EXISTS batch_run_items (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    batch_id INTEGER NOT NULL,
    analysis_run_id INTEGER NOT NULL UNIQUE,
    candidate_typing_id INTEGER NOT NULL,
    item_position INTEGER NOT NULL CHECK(item_position > 0),
    software_position INTEGER
        CHECK(software_position IS NULL OR software_position > 0),
    software_rank INTEGER
        CHECK(software_rank IS NULL OR software_rank > 0),
    criterion_value INTEGER
        CHECK(criterion_value IS NULL OR criterion_value >= 0),
    FOREIGN KEY(batch_id) REFERENCES batch_runs(id) ON DELETE CASCADE,
    FOREIGN KEY(analysis_run_id) REFERENCES analysis_runs(id),
    FOREIGN KEY(candidate_typing_id) REFERENCES hla_typings(id),
    UNIQUE(batch_id, item_position),
    UNIQUE(batch_id, analysis_run_id)
);

CREATE INDEX IF NOT EXISTS idx_batch_runs_anchor_typing_id
    ON batch_runs(anchor_typing_id);
CREATE INDEX IF NOT EXISTS idx_batch_run_items_batch_id
    ON batch_run_items(batch_id);
CREATE INDEX IF NOT EXISTS idx_batch_run_items_candidate_typing_id
    ON batch_run_items(candidate_typing_id);
"""


class MigrationError(RuntimeError):
    """Обща грешка при database migration."""


class MigrationConflictError(MigrationError):
    """Migration не може безопасно да бъде приложена върху текущите данни."""


@dataclass(frozen=True)
class Migration:
    version: int
    name: str
    apply: object


def _table_exists(conn, table_name):
    row = conn.execute(
        """
        SELECT 1
        FROM sqlite_master
        WHERE type = 'table'
          AND name = ?
        """,
        (table_name,),
    ).fetchone()

    return row is not None


def ensure_migrations_table(conn):
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS schema_migrations (
            version INTEGER PRIMARY KEY,
            name TEXT NOT NULL,
            applied_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
        )
        """
    )


def get_applied_migrations(conn):
    if not _table_exists(conn, MIGRATIONS_TABLE):
        return []

    rows = conn.execute(
        """
        SELECT version, name, applied_at
        FROM schema_migrations
        ORDER BY version
        """
    ).fetchall()

    return [
        {
            "version": row[0],
            "name": row[1],
            "applied_at": row[2],
        }
        for row in rows
    ]


def get_applied_versions(conn):
    return {
        item["version"]
        for item in get_applied_migrations(conn)
    }


def get_current_schema_version(conn):
    versions = get_applied_versions(conn)
    return max(versions) if versions else 0


def has_analysis_results_unique_key(conn):
    """
    Проверява UNIQUE key върху точно:
        (run_id, level, locus)
    """
    if not _table_exists(conn, "analysis_results"):
        return False

    for row in conn.execute(
        "PRAGMA index_list('analysis_results')"
    ).fetchall():
        index_name = row[1]
        is_unique = bool(row[2])

        if not is_unique:
            continue

        columns = [
            info[2]
            for info in conn.execute(
                f'PRAGMA index_info("{index_name}")'
            ).fetchall()
        ]

        if columns == ["run_id", "level", "locus"]:
            return True

    return False



def has_batch_history_schema(conn):
    required = {
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

    for table_name, required_columns in required.items():
        if not _table_exists(conn, table_name):
            return False

        actual_columns = {
            row[1]
            for row in conn.execute(
                f'PRAGMA table_info("{table_name}")'
            ).fetchall()
        }

        if not required_columns.issubset(actual_columns):
            return False

    return True

def find_analysis_results_duplicates(conn):
    if not _table_exists(conn, "analysis_results"):
        return []

    rows = conn.execute(
        """
        SELECT
            run_id,
            level,
            locus,
            COUNT(*) AS row_count
        FROM analysis_results
        GROUP BY run_id, level, locus
        HAVING COUNT(*) > 1
        ORDER BY run_id, level, locus
        """
    ).fetchall()

    return [
        {
            "run_id": row[0],
            "level": row[1],
            "locus": row[2],
            "row_count": row[3],
        }
        for row in rows
    ]


def migration_001_schema_registry(conn):
    """
    Baseline: маркира базата като управлявана от migration system.
    """
    return None


def migration_002_analysis_results_unique_key(conn):
    """
    Добавя UNIQUE index към стари analysis_results таблици.
    """
    duplicates = find_analysis_results_duplicates(conn)

    if duplicates:
        preview = "; ".join(
            (
                f"run_id={item['run_id']}, "
                f"level={item['level']}, "
                f"locus={item['locus']}, "
                f"rows={item['row_count']}"
            )
            for item in duplicates[:10]
        )

        raise MigrationConflictError(
            "Migration 2 е блокирана: analysis_results съдържа "
            "duplicate (run_id, level, locus) комбинации. "
            f"Примери: {preview}"
        )

    conn.execute(
        f"""
        CREATE UNIQUE INDEX IF NOT EXISTS
            {UNIQUE_RESULTS_INDEX}
        ON analysis_results(run_id, level, locus)
        """
    )

    if not has_analysis_results_unique_key(conn):
        raise MigrationError(
            "Migration 2 не успя да осигури UNIQUE "
            "(run_id, level, locus)."
        )


def migration_003_persistent_batch_history(conn):
    """
    STEP 20: adds persistent batch_runs / batch_run_items history.
    """
    conn.executescript(BATCH_HISTORY_SCHEMA_SQL)

    if not has_batch_history_schema(conn):
        raise MigrationError(
            "Migration 3 не успя да създаде STEP 20 batch history schema."
        )


MIGRATIONS = (
    Migration(
        1,
        "schema_registry_baseline",
        migration_001_schema_registry,
    ),
    Migration(
        2,
        "analysis_results_unique_run_level_locus",
        migration_002_analysis_results_unique_key,
    ),
    Migration(
        3,
        "persistent_batch_history",
        migration_003_persistent_batch_history,
    ),
)


def validate_migration_history(conn):
    applied = get_applied_versions(conn)
    known = {migration.version for migration in MIGRATIONS}
    unknown = sorted(applied - known)

    if unknown:
        raise MigrationError(
            "Базата съдържа по-нови/непознати migration версии: "
            f"{unknown}. Не използвайте по-старо приложение "
            "върху по-нова база."
        )

    return True


def get_pending_migrations(conn):
    applied = get_applied_versions(conn)

    return [
        migration
        for migration in MIGRATIONS
        if migration.version not in applied
    ]


def apply_pending_migrations(conn):
    ensure_migrations_table(conn)
    conn.commit()

    validate_migration_history(conn)

    applied_now = []

    for migration in get_pending_migrations(conn):
        try:
            with conn:
                migration.apply(conn)

                conn.execute(
                    """
                    INSERT INTO schema_migrations (
                        version,
                        name
                    )
                    VALUES (?, ?)
                    """,
                    (
                        migration.version,
                        migration.name,
                    ),
                )

        except MigrationConflictError:
            raise
        except sqlite3.DatabaseError as exc:
            raise MigrationError(
                f"SQLite error при migration {migration.version} "
                f"({migration.name}): {exc}"
            ) from exc

        applied_now.append(
            {
                "version": migration.version,
                "name": migration.name,
            }
        )

    final_version = get_current_schema_version(conn)

    if final_version != CURRENT_SCHEMA_VERSION:
        raise MigrationError(
            f"Schema version след migration е {final_version}, "
            f"а приложението изисква {CURRENT_SCHEMA_VERSION}."
        )

    return applied_now


def inspect_database_status(conn):
    history = get_applied_migrations(conn)
    current_version = get_current_schema_version(conn)
    applied = {item["version"] for item in history}

    pending = [
        {
            "version": migration.version,
            "name": migration.name,
        }
        for migration in MIGRATIONS
        if migration.version not in applied
    ]

    return {
        "current_version": current_version,
        "required_version": CURRENT_SCHEMA_VERSION,
        "is_current": current_version == CURRENT_SCHEMA_VERSION,
        "pending": pending,
        "history": history,
        "analysis_results_unique_key": (
            has_analysis_results_unique_key(conn)
        ),
        "batch_history_schema": has_batch_history_schema(conn),
    }
