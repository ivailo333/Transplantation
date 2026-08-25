"""
STEP 20 — persistent batch history.

A STEP 20 batch groups the analysis_runs created together by one saved
STEP 17/18 batch command. It preserves:

    * direction and exact anchor typing;
    * exact analysis_run IDs;
    * candidate typing IDs;
    * full software-order metadata, when STEP 18 ordering was used;
    * skipped-candidate information;
    * enough metadata to reload and re-export the batch without py-ard
      recalculation.

CLI persistence is atomic across:

    batch_runs
    + N analysis_runs
    + N × 24 analysis_results
    + N batch_run_items

The stored software ordering is not a clinical compatibility ranking.
"""

from __future__ import annotations

import copy
import json

import analyses
import database
from config import HLA_LOCI


class BatchRunNotFoundError(LookupError):
    """Не е намерен persistent batch_run с подадения batch_id."""


class BatchHistoryError(ValueError):
    """Невалидни данни за STEP 20 persistent batch."""


class BatchHistoryIntegrityError(RuntimeError):
    """Записан persistent batch е непълен или вътрешно несъвместим."""


_DIRECTION_ROLES = {
    "recipient": ("RECIPIENT", "DONOR"),
    "donor": ("DONOR", "RECIPIENT"),
}


def _positive_int(value, name):
    if isinstance(value, bool):
        raise BatchHistoryError(
            f"{name} трябва да бъде положително цяло число."
        )

    try:
        result = int(value)
    except (TypeError, ValueError) as exc:
        raise BatchHistoryError(
            f"{name} трябва да бъде положително цяло число."
        ) from exc

    if result <= 0:
        raise BatchHistoryError(
            f"{name} трябва да бъде положително цяло число."
        )

    return result


def _summary_from_results(results):
    summary = {}

    for level in ("canonical", "lgx", "G", "P"):
        shared = 0
        donor_only = 0
        recipient_only = 0

        for locus in HLA_LOCI:
            result = results[level][locus]
            shared += result["shared_count"]
            donor_only += result["mismatch_count"]
            recipient_only += result["recipient_only_count"]

        summary[level] = {
            "shared_count": shared,
            "donor_only_count": donor_only,
            "recipient_only_count": recipient_only,
        }

    return summary


def _ordering_metadata(batch):
    ordering = batch.get("software_ordering")

    if ordering is None:
        return {
            "sort_level": None,
            "sort_metric": None,
            "sort_order": None,
            "requested_sort_order": None,
            "display_limit": None,
        }

    required = {
        "level",
        "metric",
        "order",
        "requested_order",
    }

    missing = required - set(ordering)

    if missing:
        raise BatchHistoryError(
            "software_ordering липсва полета: "
            + ", ".join(sorted(missing))
        )

    level = ordering["level"]
    metric = ordering["metric"]
    order = ordering["order"]
    requested = ordering["requested_order"]

    if level not in ("canonical", "lgx", "G", "P"):
        raise BatchHistoryError("Невалидно persistent sort_level.")

    if metric not in ("donor-only", "shared", "recipient-only"):
        raise BatchHistoryError("Невалидно persistent sort_metric.")

    if order not in ("asc", "desc"):
        raise BatchHistoryError("Невалидно persistent sort_order.")

    if requested not in ("auto", "asc", "desc"):
        raise BatchHistoryError(
            "Невалидно persistent requested_sort_order."
        )

    display_limit = ordering.get("display_limit")

    if display_limit is not None:
        display_limit = _positive_int(
            display_limit,
            "display_limit",
        )

    return {
        "sort_level": level,
        "sort_metric": metric,
        "sort_order": order,
        "requested_sort_order": requested,
        "display_limit": display_limit,
    }


def validate_batch_for_persistence(batch):
    if not isinstance(batch, dict):
        raise BatchHistoryError("batch трябва да бъде dict.")

    required = {
        "direction",
        "anchor_role",
        "candidate_role",
        "anchor_external_id",
        "anchor_typing_id",
        "imgthla_version",
        "pair_count",
        "rows",
        "skipped",
    }

    missing = required - set(batch)

    if missing:
        raise BatchHistoryError(
            "batch липсва полета: "
            + ", ".join(sorted(missing))
        )

    direction = batch["direction"]

    if direction not in _DIRECTION_ROLES:
        raise BatchHistoryError(
            "direction трябва да бъде recipient или donor."
        )

    anchor_role, candidate_role = _DIRECTION_ROLES[direction]

    if batch["anchor_role"] != anchor_role:
        raise BatchHistoryError(
            "anchor_role не съвпада с batch direction."
        )

    if batch["candidate_role"] != candidate_role:
        raise BatchHistoryError(
            "candidate_role не съвпада с batch direction."
        )

    if not isinstance(batch["anchor_external_id"], str) or not batch["anchor_external_id"].strip():
        raise BatchHistoryError(
            "anchor_external_id не може да бъде празен."
        )

    _positive_int(batch["anchor_typing_id"], "anchor_typing_id")

    version = str(batch["imgthla_version"]).strip()

    if not version:
        raise BatchHistoryError("imgthla_version не може да бъде празна.")

    rows = batch["rows"]

    if not isinstance(rows, list) or not rows:
        raise BatchHistoryError(
            "Persistent batch трябва да съдържа поне една pair row."
        )

    if batch["pair_count"] != len(rows):
        raise BatchHistoryError(
            "pair_count трябва да съвпада с пълния брой rows."
        )

    if not isinstance(batch["skipped"], list):
        raise BatchHistoryError("skipped трябва да бъде list.")

    ordering = batch.get("software_ordering")
    _ordering_metadata(batch)

    expected_positions = list(range(1, len(rows) + 1))
    actual_positions = []

    for index, row in enumerate(rows, start=1):
        if not isinstance(row, dict):
            raise BatchHistoryError(
                f"rows[{index}] трябва да бъде dict."
            )

        row_required = {
            "donor_external_id",
            "donor_typing_id",
            "recipient_external_id",
            "recipient_typing_id",
            "candidate_external_id",
            "candidate_typing_id",
            "imgthla_version",
            "results",
        }

        row_missing = row_required - set(row)

        if row_missing:
            raise BatchHistoryError(
                f"rows[{index}] липсва полета: "
                + ", ".join(sorted(row_missing))
            )

        analyses.validate_analysis_results_structure(row["results"])

        if str(row["imgthla_version"]).strip() != version:
            raise BatchHistoryError(
                f"rows[{index}] използва различна IPD-IMGT/HLA версия."
            )

        for field in (
            "donor_typing_id",
            "recipient_typing_id",
            "candidate_typing_id",
        ):
            _positive_int(row[field], f"rows[{index}].{field}")

        if ordering is not None:
            info = row.get("software_order")

            if not isinstance(info, dict):
                raise BatchHistoryError(
                    f"rows[{index}] няма software_order metadata."
                )

            position = _positive_int(
                info.get("position"),
                f"rows[{index}].software_order.position",
            )
            _positive_int(
                info.get("rank"),
                f"rows[{index}].software_order.rank",
            )

            criterion = info.get("criterion_value")

            if isinstance(criterion, bool) or not isinstance(criterion, int) or criterion < 0:
                raise BatchHistoryError(
                    f"rows[{index}].criterion_value трябва да бъде int >= 0."
                )

            actual_positions.append(position)

    if ordering is not None and actual_positions != expected_positions:
        raise BatchHistoryError(
            "software_position трябва да бъде непрекъсната 1..N последователност."
        )

    # Must be JSON serializable before any SQL write.
    try:
        json.dumps(batch["skipped"], ensure_ascii=False)
    except (TypeError, ValueError) as exc:
        raise BatchHistoryError(
            "skipped metadata не може да бъде JSON сериализирана."
        ) from exc

    return True


def _insert_analysis_pair(conn, row, index):
    donor_typing_id = _positive_int(
        row["donor_typing_id"],
        f"rows[{index}].donor_typing_id",
    )
    recipient_typing_id = _positive_int(
        row["recipient_typing_id"],
        f"rows[{index}].recipient_typing_id",
    )

    donor = analyses._get_typing_for_analysis(
        conn,
        donor_typing_id,
        "DONOR",
    )
    recipient = analyses._get_typing_for_analysis(
        conn,
        recipient_typing_id,
        "RECIPIENT",
    )

    requested_version = str(row["imgthla_version"]).strip()

    if donor["imgthla_version"] != recipient["imgthla_version"]:
        raise analyses.AnalysisVersionMismatchError(
            f"rows[{index}]: DONOR/RECIPIENT typing versions differ."
        )

    if requested_version != donor["imgthla_version"]:
        raise analyses.AnalysisVersionMismatchError(
            f"rows[{index}]: batch version does not match typing version."
        )

    if donor["external_id"] != row["donor_external_id"]:
        raise BatchHistoryError(
            f"rows[{index}]: donor external_id does not match typing_id."
        )

    if recipient["external_id"] != row["recipient_external_id"]:
        raise BatchHistoryError(
            f"rows[{index}]: recipient external_id does not match typing_id."
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

    for result_key, db_level in analyses.RESULT_LEVEL_MAP.items():
        for locus in HLA_LOCI:
            result = row["results"][result_key][locus]

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
                    json.dumps(result["shared"], ensure_ascii=False),
                    json.dumps(result["donor_only"], ensure_ascii=False),
                    json.dumps(result["recipient_only"], ensure_ascii=False),
                ),
            )

    row_count = conn.execute(
        "SELECT COUNT(*) FROM analysis_results WHERE run_id = ?",
        (run_id,),
    ).fetchone()[0]

    if row_count != 24:
        raise BatchHistoryIntegrityError(
            f"run_id={run_id} has {row_count} results instead of 24."
        )

    return {
        "run_id": run_id,
        "donor": donor,
        "recipient": recipient,
    }


def persist_batch_with_runs(database_path, batch):
    """
    Atomically persists a full batch plus its analysis runs/results.

    The input batch must be the FULL, untruncated view. If STEP 18 ordering
    is active, the rows must already be in the full ordered sequence.
    """
    validate_batch_for_persistence(batch)
    database.initialize_database(database_path)
    database.verify_schema_compatibility(database_path)

    metadata = _ordering_metadata(batch)
    direction = batch["direction"]
    anchor_role, _ = _DIRECTION_ROLES[direction]
    anchor_typing_id = _positive_int(
        batch["anchor_typing_id"],
        "anchor_typing_id",
    )
    version = str(batch["imgthla_version"]).strip()

    conn = database.connect_db(database_path)
    persisted_rows = []

    try:
        with conn:
            anchor = analyses._get_typing_for_analysis(
                conn,
                anchor_typing_id,
                anchor_role,
            )

            if anchor["external_id"] != batch["anchor_external_id"]:
                raise BatchHistoryError(
                    "anchor_external_id не съвпада с anchor_typing_id."
                )

            if anchor["imgthla_version"] != version:
                raise analyses.AnalysisVersionMismatchError(
                    "Anchor typing версията не съвпада с batch версията."
                )

            cursor = conn.execute(
                """
                INSERT INTO batch_runs (
                    direction,
                    anchor_typing_id,
                    imgthla_version,
                    pair_count,
                    skipped_count,
                    skipped_json,
                    sort_level,
                    sort_metric,
                    sort_order,
                    requested_sort_order,
                    display_limit,
                    created_at
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
                """,
                (
                    direction,
                    anchor_typing_id,
                    version,
                    batch["pair_count"],
                    len(batch["skipped"]),
                    json.dumps(batch["skipped"], ensure_ascii=False),
                    metadata["sort_level"],
                    metadata["sort_metric"],
                    metadata["sort_order"],
                    metadata["requested_sort_order"],
                    metadata["display_limit"],
                ),
            )
            batch_id = cursor.lastrowid

            for item_position, row in enumerate(batch["rows"], start=1):
                saved = _insert_analysis_pair(
                    conn,
                    row,
                    item_position,
                )

                if direction == "recipient":
                    expected_candidate_typing_id = row["donor_typing_id"]
                    expected_candidate_external_id = row["donor_external_id"]
                else:
                    expected_candidate_typing_id = row["recipient_typing_id"]
                    expected_candidate_external_id = row["recipient_external_id"]

                if row["candidate_typing_id"] != expected_candidate_typing_id:
                    raise BatchHistoryError(
                        f"rows[{item_position}]: candidate_typing_id does not match direction."
                    )

                if row["candidate_external_id"] != expected_candidate_external_id:
                    raise BatchHistoryError(
                        f"rows[{item_position}]: candidate_external_id does not match direction."
                    )

                order_info = row.get("software_order")

                conn.execute(
                    """
                    INSERT INTO batch_run_items (
                        batch_id,
                        analysis_run_id,
                        candidate_typing_id,
                        item_position,
                        software_position,
                        software_rank,
                        criterion_value
                    )
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        batch_id,
                        saved["run_id"],
                        row["candidate_typing_id"],
                        item_position,
                        None if order_info is None else order_info["position"],
                        None if order_info is None else order_info["rank"],
                        None if order_info is None else order_info["criterion_value"],
                    ),
                )

                row_copy = copy.deepcopy(row)
                row_copy["run_id"] = saved["run_id"]
                persisted_rows.append(row_copy)

            item_count = conn.execute(
                "SELECT COUNT(*) FROM batch_run_items WHERE batch_id = ?",
                (batch_id,),
            ).fetchone()[0]

            if item_count != batch["pair_count"]:
                raise BatchHistoryIntegrityError(
                    f"batch_id={batch_id} has {item_count} items instead of {batch['pair_count']}."
                )

            created_at = conn.execute(
                "SELECT created_at FROM batch_runs WHERE id = ?",
                (batch_id,),
            ).fetchone()[0]

        result = copy.deepcopy(batch)
        result["save"] = True
        result["batch_id"] = batch_id
        result["batch_created_at"] = created_at
        result["rows"] = persisted_rows
        return result
    finally:
        conn.close()


def list_batch_runs(database_path=database.DEFAULT_DATABASE_PATH):
    database.verify_schema_compatibility(database_path)
    conn = database.connect_db(database_path)

    try:
        rows = conn.execute(
            """
            SELECT
                br.id,
                br.direction,
                br.anchor_typing_id,
                s.external_id,
                s.subject_type,
                br.imgthla_version,
                br.pair_count,
                br.skipped_count,
                br.sort_level,
                br.sort_metric,
                br.sort_order,
                br.requested_sort_order,
                br.display_limit,
                br.created_at,
                (SELECT COUNT(*) FROM batch_run_items bi WHERE bi.batch_id = br.id) AS item_count,
                (
                    SELECT COUNT(*)
                    FROM analysis_results res
                    JOIN batch_run_items bi2 ON bi2.analysis_run_id = res.run_id
                    WHERE bi2.batch_id = br.id
                ) AS result_count
            FROM batch_runs br
            JOIN hla_typings at ON at.id = br.anchor_typing_id
            JOIN subjects s ON s.id = at.subject_id
            ORDER BY br.id DESC
            """
        ).fetchall()

        return [
            {
                "batch_id": row[0],
                "direction": row[1],
                "anchor_typing_id": row[2],
                "anchor_external_id": row[3],
                "anchor_role": row[4],
                "imgthla_version": row[5],
                "pair_count": row[6],
                "skipped_count": row[7],
                "sort_level": row[8],
                "sort_metric": row[9],
                "sort_order": row[10],
                "requested_sort_order": row[11],
                "display_limit": row[12],
                "created_at": row[13],
                "item_count": row[14],
                "analysis_result_count": row[15],
            }
            for row in rows
        ]
    finally:
        conn.close()


def load_batch_run(database_path, batch_id):
    database.verify_schema_compatibility(database_path)
    batch_id = _positive_int(batch_id, "batch_id")
    conn = database.connect_db(database_path)

    try:
        row = conn.execute(
            """
            SELECT
                br.id,
                br.direction,
                br.anchor_typing_id,
                s.external_id,
                s.subject_type,
                br.imgthla_version,
                br.pair_count,
                br.skipped_count,
                br.skipped_json,
                br.sort_level,
                br.sort_metric,
                br.sort_order,
                br.requested_sort_order,
                br.display_limit,
                br.created_at
            FROM batch_runs br
            JOIN hla_typings at ON at.id = br.anchor_typing_id
            JOIN subjects s ON s.id = at.subject_id
            WHERE br.id = ?
            """,
            (batch_id,),
        ).fetchone()

        if row is None:
            raise BatchRunNotFoundError(
                f"Не е намерен persistent batch с batch_id={batch_id}."
            )

        try:
            skipped = json.loads(row[8])
        except json.JSONDecodeError as exc:
            raise BatchHistoryIntegrityError(
                f"batch_id={batch_id} contains invalid skipped_json."
            ) from exc

        items_rows = conn.execute(
            """
            SELECT
                bi.id,
                bi.analysis_run_id,
                bi.candidate_typing_id,
                cs.external_id,
                cs.subject_type,
                bi.item_position,
                bi.software_position,
                bi.software_rank,
                bi.criterion_value,
                ar.donor_typing_id,
                ds.external_id,
                ar.recipient_typing_id,
                rs.external_id,
                ar.imgthla_version,
                ar.created_at,
                (SELECT COUNT(*) FROM analysis_results res WHERE res.run_id = ar.id) AS result_count
            FROM batch_run_items bi
            JOIN hla_typings ct ON ct.id = bi.candidate_typing_id
            JOIN subjects cs ON cs.id = ct.subject_id
            JOIN analysis_runs ar ON ar.id = bi.analysis_run_id
            JOIN hla_typings dt ON dt.id = ar.donor_typing_id
            JOIN subjects ds ON ds.id = dt.subject_id
            JOIN hla_typings rt ON rt.id = ar.recipient_typing_id
            JOIN subjects rs ON rs.id = rt.subject_id
            WHERE bi.batch_id = ?
            ORDER BY bi.item_position
            """,
            (batch_id,),
        ).fetchall()
    finally:
        conn.close()

    items = [
        {
            "item_id": item[0],
            "analysis_run_id": item[1],
            "candidate_typing_id": item[2],
            "candidate_external_id": item[3],
            "candidate_role": item[4],
            "item_position": item[5],
            "software_position": item[6],
            "software_rank": item[7],
            "criterion_value": item[8],
            "donor_typing_id": item[9],
            "donor_external_id": item[10],
            "recipient_typing_id": item[11],
            "recipient_external_id": item[12],
            "imgthla_version": item[13],
            "analysis_created_at": item[14],
            "analysis_result_count": item[15],
        }
        for item in items_rows
    ]

    if len(items) != row[6]:
        raise BatchHistoryIntegrityError(
            f"batch_id={batch_id} has {len(items)} items instead of pair_count={row[6]}."
        )

    if not isinstance(skipped, list) or len(skipped) != row[7]:
        raise BatchHistoryIntegrityError(
            f"batch_id={batch_id} skipped metadata is inconsistent."
        )

    return {
        "batch_id": row[0],
        "direction": row[1],
        "anchor_typing_id": row[2],
        "anchor_external_id": row[3],
        "anchor_role": row[4],
        "candidate_role": _DIRECTION_ROLES[row[1]][1],
        "imgthla_version": row[5],
        "pair_count": row[6],
        "skipped_count": row[7],
        "skipped": skipped,
        "sort_level": row[9],
        "sort_metric": row[10],
        "sort_order": row[11],
        "requested_sort_order": row[12],
        "display_limit": row[13],
        "created_at": row[14],
        "items": items,
    }


def load_batch_results(database_path, batch_id):
    saved = load_batch_run(database_path, batch_id)
    rows = []

    for item in saved["items"]:
        loaded = analyses.load_analysis_results(
            database_path,
            item["analysis_run_id"],
        )
        results = loaded["results"]

        row = {
            "donor_external_id": item["donor_external_id"],
            "donor_typing_id": item["donor_typing_id"],
            "recipient_external_id": item["recipient_external_id"],
            "recipient_typing_id": item["recipient_typing_id"],
            "imgthla_version": item["imgthla_version"],
            "candidate_external_id": item["candidate_external_id"],
            "candidate_typing_id": item["candidate_typing_id"],
            "results": results,
            "summary": _summary_from_results(results),
            "run_id": item["analysis_run_id"],
        }

        if saved["sort_level"] is not None:
            metric_key = {
                "donor-only": "donor_only_count",
                "shared": "shared_count",
                "recipient-only": "recipient_only_count",
            }[saved["sort_metric"]]

            level_label = {
                "canonical": "CANONICAL",
                "lgx": "LGX",
                "G": "G",
                "P": "P",
            }[saved["sort_level"]]

            row["software_order"] = {
                "position": item["software_position"],
                "rank": item["software_rank"],
                "level": saved["sort_level"],
                "level_label": level_label,
                "metric": saved["sort_metric"],
                "metric_key": metric_key,
                "metric_label": metric_key,
                "criterion_value": item["criterion_value"],
                "order": saved["sort_order"],
                "requested_order": saved["requested_sort_order"],
            }

        rows.append(row)

    batch = {
        "batch_id": saved["batch_id"],
        "batch_created_at": saved["created_at"],
        "direction": saved["direction"],
        "anchor_role": saved["anchor_role"],
        "candidate_role": saved["candidate_role"],
        "anchor_external_id": saved["anchor_external_id"],
        "anchor_typing_id": saved["anchor_typing_id"],
        "imgthla_version": saved["imgthla_version"],
        "save": True,
        "pair_count": saved["pair_count"],
        "skipped_count": saved["skipped_count"],
        "rows": rows,
        "skipped": saved["skipped"],
    }

    if saved["sort_level"] is not None:
        level_label = {
            "canonical": "CANONICAL",
            "lgx": "LGX",
            "G": "G",
            "P": "P",
        }[saved["sort_level"]]
        metric_key = {
            "donor-only": "donor_only_count",
            "shared": "shared_count",
            "recipient-only": "recipient_only_count",
        }[saved["sort_metric"]]

        batch["software_ordering"] = {
            "enabled": True,
            "level": saved["sort_level"],
            "level_label": level_label,
            "metric": saved["sort_metric"],
            "metric_key": metric_key,
            "metric_label": metric_key,
            "requested_order": saved["requested_sort_order"],
            "order": saved["sort_order"],
            "display_limit": None,
            "original_display_limit": saved["display_limit"],
            "total_pair_count": saved["pair_count"],
            "displayed_pair_count": saved["pair_count"],
            "persistence_scope": "all eligible pairs",
        }

    return batch
