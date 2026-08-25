"""
STEP 21 — Batch History Management.

This module adds a read-only management layer over the persistent STEP 20
batch history. It deliberately does NOT change the SQLite schema and does
not recalculate HLA reductions.

Supported operations:
    * search_batch_history()
    * paginate_batch_history()
    * latest_batch()
    * summarize_batch_history()
    * render_batch_history()

The underlying persistent records remain owned by batch_history.list_batch_runs().
"""

from __future__ import annotations

from collections import Counter


class BatchHistoryManagementError(ValueError):
    """Invalid STEP 21 history-management argument."""


def _positive_or_zero_int(value, name):
    if isinstance(value, bool):
        raise BatchHistoryManagementError(
            f"{name} must be a non-negative integer."
        )
    try:
        result = int(value)
    except (TypeError, ValueError) as exc:
        raise BatchHistoryManagementError(
            f"{name} must be a non-negative integer."
        ) from exc
    if result < 0:
        raise BatchHistoryManagementError(
            f"{name} must be a non-negative integer."
        )
    return result


def _normalize(value):
    if value is None:
        return ""
    return str(value).strip().casefold()


def _record_text(record):
    fields = (
        "batch_id",
        "direction",
        "anchor_external_id",
        "anchor_role",
        "imgthla_version",
        "sort_level",
        "sort_metric",
        "sort_order",
        "requested_sort_order",
        "created_at",
    )
    return " ".join(str(record.get(field, "")) for field in fields).casefold()


def search_batch_history(
    records,
    query=None,
    direction=None,
    anchor=None,
    imgthla_version=None,
    sort_level=None,
):
    """
    Search/filter already-loaded persistent batch metadata.

    No database write and no HLA recalculation occur here.
    """
    if not isinstance(records, list):
        raise BatchHistoryManagementError("records must be a list.")

    normalized_direction = _normalize(direction)
    normalized_anchor = _normalize(anchor)
    normalized_version = _normalize(imgthla_version)
    normalized_sort_level = _normalize(sort_level)
    normalized_query = _normalize(query)

    if normalized_direction and normalized_direction not in {
        "recipient",
        "donor",
    }:
        raise BatchHistoryManagementError(
            "direction must be recipient or donor."
        )

    if normalized_sort_level and normalized_sort_level not in {
        "canonical",
        "lgx",
        "g",
        "p",
    }:
        raise BatchHistoryManagementError(
            "sort_level must be canonical, lgx, G, or P."
        )

    result = []

    for record in records:
        if normalized_direction:
            if _normalize(record.get("direction")) != normalized_direction:
                continue

        if normalized_anchor:
            if normalized_anchor not in _normalize(
                record.get("anchor_external_id")
            ):
                continue

        if normalized_version:
            if _normalize(record.get("imgthla_version")) != normalized_version:
                continue

        if normalized_sort_level:
            if _normalize(record.get("sort_level")) != normalized_sort_level:
                continue

        if normalized_query and normalized_query not in _record_text(record):
            continue

        result.append(record)

    return result


def paginate_batch_history(records, limit=None, offset=0):
    """
    Return a stable slice of history records.

    list_batch_runs() already returns newest-first order, so this function
    preserves that order.
    """
    if not isinstance(records, list):
        raise BatchHistoryManagementError("records must be a list.")

    offset = _positive_or_zero_int(offset, "offset")

    if limit is None:
        end = None
    else:
        limit = _positive_or_zero_int(limit, "limit")
        if limit == 0:
            return []
        end = offset + limit

    return records[offset:end]


def latest_batch(records):
    """Return the newest batch or None for an empty history."""
    if not isinstance(records, list):
        raise BatchHistoryManagementError("records must be a list.")
    return records[0] if records else None


def summarize_batch_history(records):
    """
    Build non-clinical administrative statistics for the persistent history.

    These statistics describe stored software runs only.
    """
    if not isinstance(records, list):
        raise BatchHistoryManagementError("records must be a list.")

    direction_counts = Counter(
        _normalize(record.get("direction")) for record in records
    )
    version_counts = Counter(
        str(record.get("imgthla_version", ""))
        for record in records
    )

    total_pairs = sum(
        int(record.get("pair_count", 0) or 0)
        for record in records
    )
    total_results = sum(
        int(record.get("analysis_result_count", 0) or 0)
        for record in records
    )

    return {
        "batch_count": len(records),
        "total_pairs": total_pairs,
        "total_analysis_results": total_results,
        "directions": dict(sorted(direction_counts.items())),
        "imgthla_versions": dict(sorted(version_counts.items())),
        "newest_batch_id": records[0].get("batch_id") if records else None,
        "oldest_batch_id": records[-1].get("batch_id") if records else None,
    }


def render_batch_history(records, title="STEP 21 — BATCH HISTORY"):
    """Render compact deterministic terminal output."""
    if not isinstance(records, list):
        raise BatchHistoryManagementError("records must be a list.")

    lines = [
        "=" * 110,
        title,
        "=" * 110,
        f"Displayed batches: {len(records)}",
        "-" * 110,
    ]

    if not records:
        lines.append("No persistent batches found.")
        lines.append("=" * 110)
        return "\n".join(lines)

    for record in records:
        sort_info = "none"
        if record.get("sort_level") is not None:
            sort_info = (
                f"{record.get('sort_level')}/"
                f"{record.get('sort_metric')}/"
                f"{record.get('sort_order')}"
            )

        lines.append(
            "batch_id={batch_id} | direction={direction} | "
            "anchor={anchor} (typing {typing}) | pairs={pairs} | "
            "results={results} | sort={sort} | created_at={created}".format(
                batch_id=record.get("batch_id"),
                direction=record.get("direction"),
                anchor=record.get("anchor_external_id"),
                typing=record.get("anchor_typing_id"),
                pairs=record.get("pair_count"),
                results=record.get("analysis_result_count"),
                sort=sort_info,
                created=record.get("created_at"),
            )
        )

    lines.extend(
        [
            "-" * 110,
            "STEP 21 is administrative history management only.",
            "It does not recalculate py-ard reductions and does not create "
            "analysis_runs.",
            "Stored software ordering remains non-clinical metadata.",
            "=" * 110,
        ]
    )
    return "\n".join(lines)


def load_and_manage_history(
    database_path,
    batch_history_module,
    query=None,
    direction=None,
    anchor=None,
    imgthla_version=None,
    sort_level=None,
    limit=None,
    offset=0,
):
    """
    Convenience integration function for command_cli.py.

    batch_history_module is passed explicitly so the module remains easy to
    unit-test and avoids a hard import cycle.
    """
    records = batch_history_module.list_batch_runs(database_path)
    filtered = search_batch_history(
        records,
        query=query,
        direction=direction,
        anchor=anchor,
        imgthla_version=imgthla_version,
        sort_level=sort_level,
    )
    return paginate_batch_history(
        filtered,
        limit=limit,
        offset=offset,
    )
