import database
import subjects
from config import HLA_LOCI


class TypingNotFoundError(LookupError):
    """Не е намерена исканата HLA типизация."""


class IncompleteTypingError(RuntimeError):
    """Записаната HLA типизация е непълна или структурно невалидна."""


REPRESENTATION_TO_COLUMN = {
    "raw": "raw_value",
    "canonical": "canonical_value",
    "lgx": "lgx_value",
    "G": "g_value",
    "P": "p_value",
}


def _validate_profile_shape(profile, profile_name):
    if not isinstance(profile, dict):
        raise ValueError(f"{profile_name} трябва да бъде dict.")

    missing = set(HLA_LOCI) - set(profile)
    extra = set(profile) - set(HLA_LOCI)

    if missing:
        raise ValueError(
            f"{profile_name}: липсващи локуси: {', '.join(sorted(missing))}"
        )

    if extra:
        raise ValueError(
            f"{profile_name}: неочаквани локуси: {', '.join(sorted(extra))}"
        )

    for locus in HLA_LOCI:
        values = profile[locus]

        if not isinstance(values, (list, tuple)) or len(values) != 2:
            raise ValueError(
                f"{profile_name} HLA-{locus} трябва да съдържа точно 2 алела."
            )

        if not all(isinstance(value, str) for value in values):
            raise ValueError(
                f"{profile_name} HLA-{locus}: всички стойности трябва да са текст."
            )


def validate_typing_bundle(bundle):
    """
    Проверява формата на RAW/CANONICAL/LGX/G/P пакета преди SQL запис.
    """
    required = {"raw", "canonical", "lgx", "G", "P"}

    if not isinstance(bundle, dict):
        raise ValueError("typing bundle трябва да бъде dict.")

    missing = required - set(bundle)
    extra = set(bundle) - required

    if missing:
        raise ValueError(
            "typing bundle: липсващи представяния: "
            + ", ".join(sorted(missing))
        )

    if extra:
        raise ValueError(
            "typing bundle: неочаквани представяния: "
            + ", ".join(sorted(extra))
        )

    for representation in ("raw", "canonical", "lgx", "G", "P"):
        _validate_profile_shape(
            bundle[representation],
            representation,
        )

    return True


def _insert_typing(conn, subject_id, imgthla_version, bundle):
    validate_typing_bundle(bundle)

    version = str(imgthla_version).strip()

    if not version:
        raise ValueError("imgthla_version не може да бъде празна.")

    cursor = conn.execute(
        """
        INSERT INTO hla_typings (
            subject_id,
            imgthla_version
        )
        VALUES (?, ?)
        """,
        (subject_id, version),
    )

    typing_id = cursor.lastrowid

    for locus in HLA_LOCI:
        for index in range(2):
            conn.execute(
                """
                INSERT INTO hla_alleles (
                    typing_id,
                    locus,
                    allele_number,
                    raw_value,
                    canonical_value,
                    lgx_value,
                    g_value,
                    p_value
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    typing_id,
                    locus,
                    index + 1,
                    bundle["raw"][locus][index],
                    bundle["canonical"][locus][index],
                    bundle["lgx"][locus][index],
                    bundle["G"][locus][index],
                    bundle["P"][locus][index],
                ),
            )

    return typing_id


def save_subject_typing(
    database_path,
    external_id,
    subject_type,
    imgthla_version,
    bundle,
):
    """
    Записва един subject + една HLA typing + 12 HLA allele реда.

    Ако subject вече съществува със същия external_id и type,
    се използва съществуващият subject и се добавя нова typing.
    """
    database.initialize_database(database_path)
    database.verify_schema_compatibility(database_path)

    conn = database.connect_db(database_path)

    try:
        with conn:
            subject_id, created = subjects._get_or_create_subject(
                conn,
                external_id,
                subject_type,
            )

            typing_id = _insert_typing(
                conn,
                subject_id,
                imgthla_version,
                bundle,
            )

        return {
            "subject_id": subject_id,
            "typing_id": typing_id,
            "subject_created": created,
        }
    finally:
        conn.close()



def save_typing_records_atomic(
    database_path,
    records,
):
    """
    Атомарно записва произволен брой HLA typings.

    records:
        [
            {
                "external_id": "...",
                "subject_type": "DONOR" | "RECIPIENT",
                "imgthla_version": "3650",
                "bundle": {... RAW/CANONICAL/LGX/G/P ...},
            },
            ...
        ]

    Ако който и да е запис се провали, целият batch се rollback-ва.
    """
    if not isinstance(records, (list, tuple)):
        raise ValueError(
            "records трябва да бъде list/tuple."
        )

    if not records:
        raise ValueError(
            "records не може да бъде празен."
        )

    database.initialize_database(database_path)
    database.verify_schema_compatibility(database_path)

    conn = database.connect_db(database_path)

    saved = []

    try:
        with conn:
            for index, record in enumerate(records, start=1):
                if not isinstance(record, dict):
                    raise ValueError(
                        f"records[{index}] трябва да бъде dict."
                    )

                required = {
                    "external_id",
                    "subject_type",
                    "imgthla_version",
                    "bundle",
                }

                missing = required - set(record)

                if missing:
                    raise ValueError(
                        f"records[{index}]: липсващи полета: "
                        + ", ".join(sorted(missing))
                    )

                subject_id, created = subjects._get_or_create_subject(
                    conn,
                    record["external_id"],
                    record["subject_type"],
                )

                typing_id = _insert_typing(
                    conn,
                    subject_id,
                    record["imgthla_version"],
                    record["bundle"],
                )

                saved.append(
                    {
                        "external_id": record["external_id"],
                        "subject_type": record["subject_type"],
                        "imgthla_version": str(
                            record["imgthla_version"]
                        ),
                        "subject_id": subject_id,
                        "typing_id": typing_id,
                        "subject_created": created,
                        "source_record_number": record.get(
                            "source_record_number"
                        ),
                    }
                )

        return saved
    finally:
        conn.close()

def save_donor_recipient_typings(
    database_path,
    donor_external_id,
    recipient_external_id,
    imgthla_version,
    donor_bundle,
    recipient_bundle,
):
    """
    Атомарно записва DONOR и RECIPIENT typings.

    Ако вторият запис се провали, първият също се rollback-ва.
    """
    database.initialize_database(database_path)
    database.verify_schema_compatibility(database_path)

    conn = database.connect_db(database_path)

    try:
        with conn:
            donor_subject_id, donor_created = subjects._get_or_create_subject(
                conn,
                donor_external_id,
                "DONOR",
            )
            donor_typing_id = _insert_typing(
                conn,
                donor_subject_id,
                imgthla_version,
                donor_bundle,
            )

            recipient_subject_id, recipient_created = subjects._get_or_create_subject(
                conn,
                recipient_external_id,
                "RECIPIENT",
            )
            recipient_typing_id = _insert_typing(
                conn,
                recipient_subject_id,
                imgthla_version,
                recipient_bundle,
            )

        return {
            "donor": {
                "subject_id": donor_subject_id,
                "typing_id": donor_typing_id,
                "subject_created": donor_created,
            },
            "recipient": {
                "subject_id": recipient_subject_id,
                "typing_id": recipient_typing_id,
                "subject_created": recipient_created,
            },
        }
    finally:
        conn.close()


def _normalize_representation(representation):
    if not isinstance(representation, str):
        raise ValueError("representation трябва да бъде текст.")

    value = representation.strip()

    aliases = {
        "raw": "raw",
        "canonical": "canonical",
        "lgx": "lgx",
        "g": "G",
        "p": "P",
    }

    normalized = aliases.get(value.lower())

    if normalized is None:
        raise ValueError(
            "Невалидно representation. Допустими: "
            "raw, canonical, lgx, G, P."
        )

    return normalized


def list_subject_typings(
    database_path,
    external_id,
    subject_type=None,
):
    """Връща всички typings за конкретен subject, най-новата първа."""
    external_id = subjects._validate_external_id(external_id)

    if subject_type is not None:
        subjects._validate_subject_type(subject_type)

    database.verify_schema_compatibility(database_path)

    conn = database.connect_db(database_path)

    try:
        subject_query = """
            SELECT id, external_id, subject_type, created_at
            FROM subjects
            WHERE external_id = ?
        """
        params = [external_id]

        if subject_type is not None:
            subject_query += " AND subject_type = ?"
            params.append(subject_type)

        subject = conn.execute(
            subject_query,
            tuple(params),
        ).fetchone()

        if subject is None:
            raise subjects.SubjectNotFoundError(
                f"Не е намерен subject с external_id={external_id!r}."
            )

        rows = conn.execute(
            """
            SELECT
                t.id,
                t.subject_id,
                t.imgthla_version,
                t.created_at,
                COUNT(a.id) AS allele_row_count
            FROM hla_typings AS t
            LEFT JOIN hla_alleles AS a
                ON a.typing_id = t.id
            WHERE t.subject_id = ?
            GROUP BY
                t.id,
                t.subject_id,
                t.imgthla_version,
                t.created_at
            ORDER BY t.id DESC
            """,
            (subject[0],),
        ).fetchall()

        return [
            {
                "typing_id": row[0],
                "subject_id": row[1],
                "external_id": subject[1],
                "subject_type": subject[2],
                "imgthla_version": row[2],
                "created_at": row[3],
                "allele_row_count": row[4],
            }
            for row in rows
        ]
    finally:
        conn.close()


def _load_typing_metadata(
    conn,
    external_id,
    subject_type=None,
    typing_id=None,
):
    external_id = subjects._validate_external_id(external_id)

    if subject_type is not None:
        subjects._validate_subject_type(subject_type)

    sql = """
        SELECT
            s.id,
            s.external_id,
            s.subject_type,
            s.created_at,
            t.id,
            t.imgthla_version,
            t.created_at
        FROM subjects AS s
        JOIN hla_typings AS t
            ON t.subject_id = s.id
        WHERE s.external_id = ?
    """
    params = [external_id]

    if subject_type is not None:
        sql += " AND s.subject_type = ?"
        params.append(subject_type)

    if typing_id is not None:
        try:
            typing_id = int(typing_id)
        except (TypeError, ValueError) as exc:
            raise ValueError("typing_id трябва да бъде цяло число.") from exc

        if typing_id <= 0:
            raise ValueError("typing_id трябва да бъде положително цяло число.")

        sql += " AND t.id = ?"
        params.append(typing_id)

    sql += " ORDER BY t.id DESC LIMIT 1"

    row = conn.execute(sql, tuple(params)).fetchone()

    if row is None:
        subject_exists = conn.execute(
            """
            SELECT id
            FROM subjects
            WHERE external_id = ?
            """,
            (external_id,),
        ).fetchone()

        if subject_exists is None:
            raise subjects.SubjectNotFoundError(
                f"Не е намерен subject с external_id={external_id!r}."
            )

        if typing_id is not None:
            raise TypingNotFoundError(
                f"typing_id={typing_id} не принадлежи на "
                f"subject {external_id!r}."
            )

        raise TypingNotFoundError(
            f"Subject {external_id!r} няма записана HLA типизация."
        )

    return {
        "subject_id": row[0],
        "external_id": row[1],
        "subject_type": row[2],
        "subject_created_at": row[3],
        "typing_id": row[4],
        "imgthla_version": row[5],
        "typing_created_at": row[6],
    }


def load_subject_typing(
    database_path,
    external_id,
    subject_type=None,
    typing_id=None,
):
    """
    Зарежда най-новата или конкретна HLA typing от SQLite.

    Връща:
        {
            "subject": {...},
            "typing": {...},
            "bundle": {
                "raw": {...},
                "canonical": {...},
                "lgx": {...},
                "G": {...},
                "P": {...}
            }
        }
    """
    database.verify_schema_compatibility(database_path)

    conn = database.connect_db(database_path)

    try:
        metadata = _load_typing_metadata(
            conn,
            external_id=external_id,
            subject_type=subject_type,
            typing_id=typing_id,
        )

        rows = conn.execute(
            """
            SELECT
                locus,
                allele_number,
                raw_value,
                canonical_value,
                lgx_value,
                g_value,
                p_value
            FROM hla_alleles
            WHERE typing_id = ?
            ORDER BY
                CASE locus
                    WHEN 'A' THEN 1
                    WHEN 'B' THEN 2
                    WHEN 'C' THEN 3
                    WHEN 'DRB1' THEN 4
                    WHEN 'DQB1' THEN 5
                    WHEN 'DPB1' THEN 6
                    ELSE 99
                END,
                allele_number
            """,
            (metadata["typing_id"],),
        ).fetchall()

        if len(rows) != 12:
            raise IncompleteTypingError(
                f"typing_id={metadata['typing_id']} съдържа "
                f"{len(rows)} allele rows вместо очакваните 12."
            )

        bundle = {
            "raw": {locus: [None, None] for locus in HLA_LOCI},
            "canonical": {locus: [None, None] for locus in HLA_LOCI},
            "lgx": {locus: [None, None] for locus in HLA_LOCI},
            "G": {locus: [None, None] for locus in HLA_LOCI},
            "P": {locus: [None, None] for locus in HLA_LOCI},
        }

        seen = set()

        for row in rows:
            locus, allele_number = row[0], row[1]

            if locus not in HLA_LOCI:
                raise IncompleteTypingError(
                    f"typing_id={metadata['typing_id']} съдържа "
                    f"неподдържан locus {locus!r}."
                )

            if allele_number not in (1, 2):
                raise IncompleteTypingError(
                    f"typing_id={metadata['typing_id']} съдържа "
                    f"невалиден allele_number={allele_number}."
                )

            key = (locus, allele_number)

            if key in seen:
                raise IncompleteTypingError(
                    f"typing_id={metadata['typing_id']} съдържа "
                    f"дублиран запис {locus} allele {allele_number}."
                )

            seen.add(key)
            index = allele_number - 1

            bundle["raw"][locus][index] = row[2]
            bundle["canonical"][locus][index] = row[3]
            bundle["lgx"][locus][index] = row[4]
            bundle["G"][locus][index] = row[5]
            bundle["P"][locus][index] = row[6]

        expected_keys = {
            (locus, allele_number)
            for locus in HLA_LOCI
            for allele_number in (1, 2)
        }

        if seen != expected_keys:
            missing = sorted(expected_keys - seen)
            raise IncompleteTypingError(
                f"typing_id={metadata['typing_id']} има липсващи "
                f"locus/allele позиции: {missing}"
            )

        validate_typing_bundle(bundle)

        return {
            "subject": {
                "subject_id": metadata["subject_id"],
                "external_id": metadata["external_id"],
                "subject_type": metadata["subject_type"],
                "created_at": metadata["subject_created_at"],
            },
            "typing": {
                "typing_id": metadata["typing_id"],
                "imgthla_version": metadata["imgthla_version"],
                "created_at": metadata["typing_created_at"],
            },
            "bundle": bundle,
        }
    finally:
        conn.close()


def load_subject_profile(
    database_path,
    external_id,
    representation="canonical",
    subject_type=None,
    typing_id=None,
):
    """
    Връща само избраното HLA представяне като независим dict.

    representation:
        raw / canonical / lgx / G / P
    """
    representation = _normalize_representation(representation)

    loaded = load_subject_typing(
        database_path=database_path,
        external_id=external_id,
        subject_type=subject_type,
        typing_id=typing_id,
    )

    profile = loaded["bundle"][representation]

    return {
        locus: list(profile[locus])
        for locus in HLA_LOCI
    }
