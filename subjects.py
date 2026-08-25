import database
from config import SUBJECT_TYPES


class SubjectTypeConflictError(ValueError):
    """Един external_id вече съществува с друг subject_type."""


class SubjectNotFoundError(LookupError):
    """Не е намерен subject с подадения external_id."""


def _validate_external_id(external_id):
    if not isinstance(external_id, str):
        raise ValueError("external_id трябва да бъде текст.")

    external_id = external_id.strip()

    if not external_id:
        raise ValueError("external_id не може да бъде празен.")

    return external_id


def _validate_subject_type(subject_type):
    if subject_type not in SUBJECT_TYPES:
        raise ValueError(
            f"Невалиден subject_type: {subject_type!r}. "
            f"Допустими: {', '.join(SUBJECT_TYPES)}"
        )


def _get_or_create_subject(conn, external_id, subject_type):
    external_id = _validate_external_id(external_id)
    _validate_subject_type(subject_type)

    row = conn.execute(
        """
        SELECT id, subject_type
        FROM subjects
        WHERE external_id = ?
        """,
        (external_id,),
    ).fetchone()

    if row is not None:
        subject_id, existing_type = row

        if existing_type != subject_type:
            raise SubjectTypeConflictError(
                f"external_id {external_id!r} вече съществува като "
                f"{existing_type}, а е поискан {subject_type}."
            )

        return subject_id, False

    cursor = conn.execute(
        """
        INSERT INTO subjects (
            external_id,
            subject_type
        )
        VALUES (?, ?)
        """,
        (external_id, subject_type),
    )

    return cursor.lastrowid, True


def list_subjects(database_path=database.DEFAULT_DATABASE_PATH):
    """
    Връща всички DONOR/RECIPIENT subjects.

    За всеки subject връща броя typings и metadata за най-новата typing.
    """
    database.verify_schema_compatibility(database_path)

    conn = database.connect_db(database_path)

    try:
        rows = conn.execute(
            """
            SELECT
                s.id,
                s.external_id,
                s.subject_type,
                s.created_at,
                COUNT(t.id) AS typing_count,
                (
                    SELECT t2.id
                    FROM hla_typings AS t2
                    WHERE t2.subject_id = s.id
                    ORDER BY t2.id DESC
                    LIMIT 1
                ) AS latest_typing_id,
                (
                    SELECT t2.imgthla_version
                    FROM hla_typings AS t2
                    WHERE t2.subject_id = s.id
                    ORDER BY t2.id DESC
                    LIMIT 1
                ) AS latest_imgthla_version,
                (
                    SELECT t2.created_at
                    FROM hla_typings AS t2
                    WHERE t2.subject_id = s.id
                    ORDER BY t2.id DESC
                    LIMIT 1
                ) AS latest_typing_created_at
            FROM subjects AS s
            LEFT JOIN hla_typings AS t
                ON t.subject_id = s.id
            GROUP BY
                s.id,
                s.external_id,
                s.subject_type,
                s.created_at
            ORDER BY s.id
            """
        ).fetchall()

        return [
            {
                "subject_id": row[0],
                "external_id": row[1],
                "subject_type": row[2],
                "created_at": row[3],
                "typing_count": row[4],
                "latest_typing_id": row[5],
                "latest_imgthla_version": row[6],
                "latest_typing_created_at": row[7],
            }
            for row in rows
        ]
    finally:
        conn.close()
