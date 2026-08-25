import json

import database
import subjects
import typings
from config import HLA_LOCI


class AnalysisRunNotFoundError(LookupError):
    """Не е намерен analysis_run с подадения ID."""


class AnalysisTypingRoleError(ValueError):
    """Typing е използвана в неправилна DONOR/RECIPIENT роля."""


class AnalysisVersionMismatchError(ValueError):
    """DONOR и RECIPIENT typings са от различни IPD-IMGT/HLA версии."""


class AnalysisResultsError(ValueError):
    """Невалидна структура или съдържание на analysis_results."""


class AnalysisResultsNotFoundError(LookupError):
    """За посочения analysis_run още няма записани analysis_results."""


RESULT_LEVEL_MAP = {
    "canonical": "CANONICAL",
    "lgx": "LGX",
    "G": "G",
    "P": "P",
}

DB_LEVEL_TO_RESULT_KEY = {
    value: key
    for key, value in RESULT_LEVEL_MAP.items()
}


def _positive_int(value, name):
    try:
        result = int(value)
    except (TypeError, ValueError) as exc:
        raise ValueError(f"{name} трябва да бъде цяло число.") from exc

    if result <= 0:
        raise ValueError(f"{name} трябва да бъде положително цяло число.")

    return result


def _get_typing_for_analysis(conn, typing_id, expected_subject_type):
    typing_id = _positive_int(typing_id, "typing_id")
    subjects._validate_subject_type(expected_subject_type)

    row = conn.execute(
        """
        SELECT
            t.id,
            t.subject_id,
            t.imgthla_version,
            t.created_at,
            s.external_id,
            s.subject_type,
            COUNT(a.id) AS allele_row_count
        FROM hla_typings AS t
        JOIN subjects AS s
            ON s.id = t.subject_id
        LEFT JOIN hla_alleles AS a
            ON a.typing_id = t.id
        WHERE t.id = ?
        GROUP BY
            t.id,
            t.subject_id,
            t.imgthla_version,
            t.created_at,
            s.external_id,
            s.subject_type
        """,
        (typing_id,),
    ).fetchone()

    if row is None:
        raise typings.TypingNotFoundError(
            f"Не е намерена HLA typing с typing_id={typing_id}."
        )

    if row[5] != expected_subject_type:
        raise AnalysisTypingRoleError(
            f"typing_id={typing_id} принадлежи на {row[5]}, "
            f"а за тази роля се очаква {expected_subject_type}."
        )

    if row[6] != 12:
        raise typings.IncompleteTypingError(
            f"typing_id={typing_id} съдържа {row[6]} allele rows "
            f"вместо очакваните 12."
        )

    return {
        "typing_id": row[0],
        "subject_id": row[1],
        "imgthla_version": row[2],
        "typing_created_at": row[3],
        "external_id": row[4],
        "subject_type": row[5],
        "allele_row_count": row[6],
    }


def create_analysis_run(
    database_path,
    donor_typing_id,
    recipient_typing_id,
    imgthla_version=None,
):
    """
    Създава analysis_runs ред, който свързва точно една DONOR typing
    с точно една RECIPIENT typing.

    STEP 13D записва само metadata връзката.
    Самите comparison results ще се записват в STEP 13E.
    """
    database.initialize_database(database_path)
    database.verify_schema_compatibility(database_path)

    donor_typing_id = _positive_int(
        donor_typing_id,
        "donor_typing_id",
    )
    recipient_typing_id = _positive_int(
        recipient_typing_id,
        "recipient_typing_id",
    )

    conn = database.connect_db(database_path)

    try:
        with conn:
            donor = _get_typing_for_analysis(
                conn,
                donor_typing_id,
                "DONOR",
            )
            recipient = _get_typing_for_analysis(
                conn,
                recipient_typing_id,
                "RECIPIENT",
            )

            if donor["imgthla_version"] != recipient["imgthla_version"]:
                raise AnalysisVersionMismatchError(
                    "DONOR и RECIPIENT typings използват различни "
                    "IPD-IMGT/HLA версии: "
                    f"{donor['imgthla_version']} срещу "
                    f"{recipient['imgthla_version']}."
                )

            resolved_version = donor["imgthla_version"]

            if imgthla_version is not None:
                requested_version = str(imgthla_version).strip()

                if not requested_version:
                    raise ValueError(
                        "imgthla_version не може да бъде празна."
                    )

                if requested_version != resolved_version:
                    raise AnalysisVersionMismatchError(
                        "Подадената analysis версия "
                        f"{requested_version!r} не съвпада с typing "
                        f"версията {resolved_version!r}."
                    )

            cursor = conn.execute(
                """
                INSERT INTO analysis_runs (
                    donor_typing_id,
                    recipient_typing_id,
                    imgthla_version,
                    created_at
                )
                VALUES (?, ?, ?, CURRENT_TIMESTAMP)
                """,
                (
                    donor_typing_id,
                    recipient_typing_id,
                    resolved_version,
                ),
            )

            run_id = cursor.lastrowid

        return {
            "run_id": run_id,
            "donor": donor,
            "recipient": recipient,
            "imgthla_version": resolved_version,
        }
    finally:
        conn.close()


def create_analysis_run_for_subjects(
    database_path,
    donor_external_id,
    recipient_external_id,
    donor_typing_id=None,
    recipient_typing_id=None,
):
    """
    Създава analysis_run по external_id.

    Ако typing_id не е подаден, използва най-новата typing
    за съответния subject.
    """
    donor_loaded = typings.load_subject_typing(
        database_path=database_path,
        external_id=donor_external_id,
        subject_type="DONOR",
        typing_id=donor_typing_id,
    )
    recipient_loaded = typings.load_subject_typing(
        database_path=database_path,
        external_id=recipient_external_id,
        subject_type="RECIPIENT",
        typing_id=recipient_typing_id,
    )

    return create_analysis_run(
        database_path=database_path,
        donor_typing_id=donor_loaded["typing"]["typing_id"],
        recipient_typing_id=recipient_loaded["typing"]["typing_id"],
    )


def load_analysis_run(
    database_path,
    run_id,
):
    """Зарежда metadata за един analysis_run."""
    database.verify_schema_compatibility(database_path)
    run_id = _positive_int(run_id, "run_id")

    conn = database.connect_db(database_path)

    try:
        row = conn.execute(
            """
            SELECT
                ar.id,
                ar.donor_typing_id,
                ar.recipient_typing_id,
                ar.imgthla_version,
                ar.created_at,

                ds.id,
                ds.external_id,
                ds.subject_type,

                rs.id,
                rs.external_id,
                rs.subject_type

            FROM analysis_runs AS ar

            JOIN hla_typings AS dt
                ON dt.id = ar.donor_typing_id
            JOIN subjects AS ds
                ON ds.id = dt.subject_id

            JOIN hla_typings AS rt
                ON rt.id = ar.recipient_typing_id
            JOIN subjects AS rs
                ON rs.id = rt.subject_id

            WHERE ar.id = ?
            """,
            (run_id,),
        ).fetchone()

        if row is None:
            raise AnalysisRunNotFoundError(
                f"Не е намерен analysis_run с run_id={run_id}."
            )

        result_count = conn.execute(
            """
            SELECT COUNT(*)
            FROM analysis_results
            WHERE run_id = ?
            """,
            (run_id,),
        ).fetchone()[0]

        return {
            "run_id": row[0],
            "donor_typing_id": row[1],
            "recipient_typing_id": row[2],
            "imgthla_version": row[3],
            "created_at": row[4],
            "donor": {
                "subject_id": row[5],
                "external_id": row[6],
                "subject_type": row[7],
            },
            "recipient": {
                "subject_id": row[8],
                "external_id": row[9],
                "subject_type": row[10],
            },
            "analysis_result_count": result_count,
        }
    finally:
        conn.close()


def list_analysis_runs(database_path=database.DEFAULT_DATABASE_PATH):
    """Връща всички analysis runs, най-новият първи."""
    database.verify_schema_compatibility(database_path)

    conn = database.connect_db(database_path)

    try:
        rows = conn.execute(
            """
            SELECT
                ar.id,
                ar.donor_typing_id,
                ar.recipient_typing_id,
                ar.imgthla_version,
                ar.created_at,
                ds.external_id,
                rs.external_id,
                (
                    SELECT COUNT(*)
                    FROM analysis_results AS res
                    WHERE res.run_id = ar.id
                ) AS result_count
            FROM analysis_runs AS ar

            JOIN hla_typings AS dt
                ON dt.id = ar.donor_typing_id
            JOIN subjects AS ds
                ON ds.id = dt.subject_id

            JOIN hla_typings AS rt
                ON rt.id = ar.recipient_typing_id
            JOIN subjects AS rs
                ON rs.id = rt.subject_id

            ORDER BY ar.id DESC
            """
        ).fetchall()

        return [
            {
                "run_id": row[0],
                "donor_typing_id": row[1],
                "recipient_typing_id": row[2],
                "imgthla_version": row[3],
                "created_at": row[4],
                "donor_external_id": row[5],
                "recipient_external_id": row[6],
                "analysis_result_count": row[7],
            }
            for row in rows
        ]
    finally:
        conn.close()


def load_analysis_run_typings(database_path, run_id):
    """
    Зарежда analysis_run и точно двете typings, които той свързва.

    Важно: използва вече записаните RAW/CANONICAL/LGX/G/P стойности
    от SQLite, а не ги преизчислява с текуща py-ard версия.
    """
    run = load_analysis_run(database_path, run_id)

    donor = typings.load_subject_typing(
        database_path=database_path,
        external_id=run["donor"]["external_id"],
        subject_type="DONOR",
        typing_id=run["donor_typing_id"],
    )

    recipient = typings.load_subject_typing(
        database_path=database_path,
        external_id=run["recipient"]["external_id"],
        subject_type="RECIPIENT",
        typing_id=run["recipient_typing_id"],
    )

    if donor["typing"]["imgthla_version"] != run["imgthla_version"]:
        raise AnalysisVersionMismatchError(
            "DONOR typing версията не съвпада с analysis_run версията."
        )

    if recipient["typing"]["imgthla_version"] != run["imgthla_version"]:
        raise AnalysisVersionMismatchError(
            "RECIPIENT typing версията не съвпада с analysis_run версията."
        )

    return {
        "run": run,
        "donor": donor,
        "recipient": recipient,
    }


def _validate_result_list(value, label):
    if not isinstance(value, list):
        raise AnalysisResultsError(
            f"{label} трябва да бъде list."
        )

    if not all(isinstance(item, str) for item in value):
        raise AnalysisResultsError(
            f"{label} трябва да съдържа само текстови HLA стойности."
        )


def validate_analysis_results_structure(results):
    """
    Валидира вложената структура преди SQL запис.

    Очаква:
        results["canonical"|"lgx"|"G"|"P"][locus] = {
            "shared": [...],
            "donor_only": [...],
            "recipient_only": [...],
            "shared_count": int,
            "mismatch_count": int,
            "recipient_only_count": int,
        }
    """
    if not isinstance(results, dict):
        raise AnalysisResultsError("results трябва да бъде dict.")

    expected_levels = set(RESULT_LEVEL_MAP)
    actual_levels = set(results)

    if actual_levels != expected_levels:
        missing = sorted(expected_levels - actual_levels)
        extra = sorted(actual_levels - expected_levels)

        details = []
        if missing:
            details.append("липсващи нива: " + ", ".join(missing))
        if extra:
            details.append("неочаквани нива: " + ", ".join(extra))

        raise AnalysisResultsError("; ".join(details))

    for level_key in RESULT_LEVEL_MAP:
        level_results = results[level_key]

        if not isinstance(level_results, dict):
            raise AnalysisResultsError(
                f"results[{level_key!r}] трябва да бъде dict."
            )

        if set(level_results) != set(HLA_LOCI):
            missing = sorted(set(HLA_LOCI) - set(level_results))
            extra = sorted(set(level_results) - set(HLA_LOCI))
            details = []

            if missing:
                details.append("липсващи локуси: " + ", ".join(missing))
            if extra:
                details.append("неочаквани локуси: " + ", ".join(extra))

            raise AnalysisResultsError(
                f"{level_key}: " + "; ".join(details)
            )

        for locus in HLA_LOCI:
            result = level_results[locus]

            if not isinstance(result, dict):
                raise AnalysisResultsError(
                    f"{level_key}/{locus}: result трябва да бъде dict."
                )

            required_keys = {
                "shared",
                "donor_only",
                "recipient_only",
                "shared_count",
                "mismatch_count",
                "recipient_only_count",
            }

            if set(result) != required_keys:
                raise AnalysisResultsError(
                    f"{level_key}/{locus}: невалидни result keys."
                )

            _validate_result_list(
                result["shared"],
                f"{level_key}/{locus}/shared",
            )
            _validate_result_list(
                result["donor_only"],
                f"{level_key}/{locus}/donor_only",
            )
            _validate_result_list(
                result["recipient_only"],
                f"{level_key}/{locus}/recipient_only",
            )

            numeric_fields = (
                "shared_count",
                "mismatch_count",
                "recipient_only_count",
            )

            for field in numeric_fields:
                value = result[field]

                if not isinstance(value, int) or isinstance(value, bool):
                    raise AnalysisResultsError(
                        f"{level_key}/{locus}/{field} трябва да бъде int."
                    )

                if value < 0:
                    raise AnalysisResultsError(
                        f"{level_key}/{locus}/{field} не може да е отрицателно."
                    )

            if result["shared_count"] != len(result["shared"]):
                raise AnalysisResultsError(
                    f"{level_key}/{locus}: shared_count не съвпада "
                    "с броя shared стойности."
                )

            if result["mismatch_count"] != len(result["donor_only"]):
                raise AnalysisResultsError(
                    f"{level_key}/{locus}: mismatch_count не съвпада "
                    "с броя donor_only стойности."
                )

            if (
                result["recipient_only_count"]
                != len(result["recipient_only"])
            ):
                raise AnalysisResultsError(
                    f"{level_key}/{locus}: recipient_only_count не съвпада "
                    "с броя recipient_only стойности."
                )

    return True


def save_analysis_results(
    database_path,
    run_id,
    results,
):
    """
    Записва точно 24 rows:
        4 levels × 6 HLA loci.

    Операцията е idempotent за един run_id:
    повторното изпълнение обновява същите 24 UNIQUE реда
    чрез SQLite UPSERT, без дублиране.
    """
    database.verify_schema_compatibility(database_path)
    run_id = _positive_int(run_id, "run_id")
    validate_analysis_results_structure(results)

    # Потвърждаваме, че run съществува и typings са достъпни/съвместими.
    linked = load_analysis_run_typings(
        database_path,
        run_id,
    )

    conn = database.connect_db(database_path)

    try:
        with conn:
            for result_key, db_level in RESULT_LEVEL_MAP.items():
                for locus in HLA_LOCI:
                    result = results[result_key][locus]

                    conn.execute(
                        """
                        INSERT INTO analysis_results (
                            run_id,
                            level,
                            locus,
                            shared_count,
                            donor_only_count,
                            recipient_only_count,
                            shared_values,
                            donor_only_values,
                            recipient_only_values
                        )
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)

                        ON CONFLICT(run_id, level, locus)
                        DO UPDATE SET
                            shared_count = excluded.shared_count,
                            donor_only_count = excluded.donor_only_count,
                            recipient_only_count = excluded.recipient_only_count,
                            shared_values = excluded.shared_values,
                            donor_only_values = excluded.donor_only_values,
                            recipient_only_values = excluded.recipient_only_values
                        """,
                        (
                            run_id,
                            db_level,
                            locus,
                            result["shared_count"],
                            result["mismatch_count"],
                            result["recipient_only_count"],
                            json.dumps(
                                result["shared"],
                                ensure_ascii=False,
                            ),
                            json.dumps(
                                result["donor_only"],
                                ensure_ascii=False,
                            ),
                            json.dumps(
                                result["recipient_only"],
                                ensure_ascii=False,
                            ),
                        ),
                    )

            row_count = conn.execute(
                """
                SELECT COUNT(*)
                FROM analysis_results
                WHERE run_id = ?
                """,
                (run_id,),
            ).fetchone()[0]

            if row_count != 24:
                raise AnalysisResultsError(
                    f"run_id={run_id}: след save има {row_count} "
                    "analysis_result rows вместо 24."
                )

        return {
            "run_id": run_id,
            "row_count": 24,
            "donor_typing_id": linked["run"]["donor_typing_id"],
            "recipient_typing_id": linked["run"]["recipient_typing_id"],
            "imgthla_version": linked["run"]["imgthla_version"],
        }
    finally:
        conn.close()



def save_batch_analysis_runs(
    database_path,
    pairs,
):
    """
    Атомарно записва цял STEP 17 batch:

        N × analysis_runs
        N × 24 analysis_results

    Ако който и да е pair се провали, SQLite rollback-ва целия batch.
    """
    if not isinstance(pairs, (list, tuple)):
        raise ValueError("pairs трябва да бъде list/tuple.")

    if not pairs:
        raise ValueError("pairs не може да бъде празен.")

    # Validate every result structure before the first SQL write.
    for index, pair in enumerate(pairs, start=1):
        if not isinstance(pair, dict):
            raise ValueError(
                f"pairs[{index}] трябва да бъде dict."
            )

        required = {
            "donor_typing_id",
            "recipient_typing_id",
            "imgthla_version",
            "results",
        }

        missing = required - set(pair)

        if missing:
            raise ValueError(
                f"pairs[{index}]: липсващи полета: "
                + ", ".join(sorted(missing))
            )

        validate_analysis_results_structure(
            pair["results"]
        )

    database.initialize_database(database_path)
    database.verify_schema_compatibility(database_path)

    conn = database.connect_db(database_path)
    saved = []

    try:
        with conn:
            for index, pair in enumerate(pairs, start=1):
                donor_typing_id = _positive_int(
                    pair["donor_typing_id"],
                    f"pairs[{index}].donor_typing_id",
                )
                recipient_typing_id = _positive_int(
                    pair["recipient_typing_id"],
                    f"pairs[{index}].recipient_typing_id",
                )

                donor = _get_typing_for_analysis(
                    conn,
                    donor_typing_id,
                    "DONOR",
                )
                recipient = _get_typing_for_analysis(
                    conn,
                    recipient_typing_id,
                    "RECIPIENT",
                )

                if donor["imgthla_version"] != recipient["imgthla_version"]:
                    raise AnalysisVersionMismatchError(
                        f"pairs[{index}]: DONOR и RECIPIENT typings "
                        "са от различни IPD-IMGT/HLA версии."
                    )

                requested_version = str(
                    pair["imgthla_version"]
                ).strip()

                if not requested_version:
                    raise ValueError(
                        f"pairs[{index}].imgthla_version "
                        "не може да бъде празна."
                    )

                if requested_version != donor["imgthla_version"]:
                    raise AnalysisVersionMismatchError(
                        f"pairs[{index}]: analysis version "
                        f"{requested_version!r} не съвпада с typing "
                        f"версията {donor['imgthla_version']!r}."
                    )

                cursor = conn.execute(
                    """
                    INSERT INTO analysis_runs (
                        donor_typing_id,
                        recipient_typing_id,
                        imgthla_version,
                        created_at
                    )
                    VALUES (?, ?, ?, CURRENT_TIMESTAMP)
                    """,
                    (
                        donor_typing_id,
                        recipient_typing_id,
                        requested_version,
                    ),
                )

                run_id = cursor.lastrowid
                results = pair["results"]

                for result_key, db_level in RESULT_LEVEL_MAP.items():
                    for locus in HLA_LOCI:
                        result = results[result_key][locus]

                        conn.execute(
                            """
                            INSERT INTO analysis_results (
                                run_id,
                                level,
                                locus,
                                shared_count,
                                donor_only_count,
                                recipient_only_count,
                                shared_values,
                                donor_only_values,
                                recipient_only_values
                            )
                            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                            """,
                            (
                                run_id,
                                db_level,
                                locus,
                                result["shared_count"],
                                result["mismatch_count"],
                                result["recipient_only_count"],
                                json.dumps(
                                    result["shared"],
                                    ensure_ascii=False,
                                ),
                                json.dumps(
                                    result["donor_only"],
                                    ensure_ascii=False,
                                ),
                                json.dumps(
                                    result["recipient_only"],
                                    ensure_ascii=False,
                                ),
                            ),
                        )

                row_count = conn.execute(
                    """
                    SELECT COUNT(*)
                    FROM analysis_results
                    WHERE run_id = ?
                    """,
                    (run_id,),
                ).fetchone()[0]

                if row_count != 24:
                    raise AnalysisResultsError(
                        f"pairs[{index}] run_id={run_id}: "
                        f"{row_count} rows вместо 24."
                    )

                saved.append(
                    {
                        "run_id": run_id,
                        "row_count": 24,
                        "donor_typing_id": donor_typing_id,
                        "recipient_typing_id": recipient_typing_id,
                        "imgthla_version": requested_version,
                    }
                )

        return saved
    finally:
        conn.close()

def load_analysis_results(
    database_path,
    run_id,
    require_complete=True,
):
    """
    Зарежда записаните резултати и възстановява JSON масивите като list.

    Връща същата nested results форма, която използва compare_locus().
    """
    database.verify_schema_compatibility(database_path)
    run_id = _positive_int(run_id, "run_id")

    # Дава ясна грешка, ако run_id не съществува.
    run = load_analysis_run(database_path, run_id)

    conn = database.connect_db(database_path)

    try:
        rows = conn.execute(
            """
            SELECT
                level,
                locus,
                shared_count,
                donor_only_count,
                recipient_only_count,
                shared_values,
                donor_only_values,
                recipient_only_values
            FROM analysis_results
            WHERE run_id = ?
            ORDER BY
                CASE level
                    WHEN 'CANONICAL' THEN 1
                    WHEN 'LGX' THEN 2
                    WHEN 'G' THEN 3
                    WHEN 'P' THEN 4
                    ELSE 99
                END,
                CASE locus
                    WHEN 'A' THEN 1
                    WHEN 'B' THEN 2
                    WHEN 'C' THEN 3
                    WHEN 'DRB1' THEN 4
                    WHEN 'DQB1' THEN 5
                    WHEN 'DPB1' THEN 6
                    ELSE 99
                END
            """,
            (run_id,),
        ).fetchall()
    finally:
        conn.close()

    if not rows:
        raise AnalysisResultsNotFoundError(
            f"run_id={run_id} няма записани analysis_results."
        )

    if require_complete and len(rows) != 24:
        raise AnalysisResultsError(
            f"run_id={run_id} има {len(rows)} analysis_result rows "
            "вместо очакваните 24."
        )

    results = {
        "canonical": {},
        "lgx": {},
        "G": {},
        "P": {},
    }

    for row in rows:
        db_level = row[0]
        locus = row[1]

        if db_level not in DB_LEVEL_TO_RESULT_KEY:
            raise AnalysisResultsError(
                f"Неподдържано analysis level: {db_level!r}"
            )

        if locus not in HLA_LOCI:
            raise AnalysisResultsError(
                f"Неподдържан HLA locus: {locus!r}"
            )

        result_key = DB_LEVEL_TO_RESULT_KEY[db_level]

        try:
            shared = json.loads(row[5])
            donor_only = json.loads(row[6])
            recipient_only = json.loads(row[7])
        except json.JSONDecodeError as exc:
            raise AnalysisResultsError(
                f"run_id={run_id} съдържа невалиден JSON "
                f"за {db_level}/{locus}."
            ) from exc

        results[result_key][locus] = {
            "shared": shared,
            "donor_only": donor_only,
            "recipient_only": recipient_only,
            "shared_count": row[2],
            "mismatch_count": row[3],
            "recipient_only_count": row[4],
        }

    if require_complete:
        validate_analysis_results_structure(results)

    return {
        "run": run,
        "results": results,
        "row_count": len(rows),
    }
