"""
STEP 18 — deterministic software ordering of STEP 17 batch results.

This module does NOT calculate a clinical compatibility score.

It only sorts already computed STEP 17 summary counts by one explicitly
selected representation level and one explicitly selected count field.

Supported levels:
    CANONICAL / LGX / G / P

Supported metrics:
    donor-only
    shared
    recipient-only

AUTO order:
    shared         -> descending
    donor-only     -> ascending
    recipient-only -> ascending

Equal primary values receive the same software_rank. A deterministic
candidate external_id / typing_id tie-break is used only to make output
stable; it has no medical meaning.
"""

from __future__ import annotations

import copy


SORT_LEVELS = ("canonical", "lgx", "G", "P")
SORT_METRICS = ("donor-only", "shared", "recipient-only")
SORT_ORDERS = ("auto", "asc", "desc")

DEFAULT_SORT_LEVEL = "lgx"

LEVEL_LABELS = {
    "canonical": "CANONICAL",
    "lgx": "LGX",
    "G": "G",
    "P": "P",
}

METRIC_KEYS = {
    "donor-only": "donor_only_count",
    "shared": "shared_count",
    "recipient-only": "recipient_only_count",
}

METRIC_LABELS = {
    "donor-only": "donor_only_count",
    "shared": "shared_count",
    "recipient-only": "recipient_only_count",
}


class BatchRankingError(ValueError):
    """Невалидна STEP 18 software-ordering конфигурация."""


def normalize_sort_level(value):
    if value is None:
        return DEFAULT_SORT_LEVEL

    if not isinstance(value, str):
        raise BatchRankingError(
            "sort level трябва да бъде текст."
        )

    normalized = value.strip().lower()

    mapping = {
        "canonical": "canonical",
        "lgx": "lgx",
        "g": "G",
        "p": "P",
    }

    if normalized not in mapping:
        raise BatchRankingError(
            "Невалидно sort level. Допустими: "
            "canonical, lgx, G, P."
        )

    return mapping[normalized]


def normalize_sort_metric(value):
    if not isinstance(value, str):
        raise BatchRankingError(
            "sort metric трябва да бъде текст."
        )

    normalized = (
        value.strip()
        .lower()
        .replace("_count", "")
        .replace("_", "-")
    )

    aliases = {
        "donor-only": "donor-only",
        "donoronly": "donor-only",
        "shared": "shared",
        "recipient-only": "recipient-only",
        "recipientonly": "recipient-only",
    }

    if normalized not in aliases:
        raise BatchRankingError(
            "Невалидно sort metric. Допустими: "
            "donor-only, shared, recipient-only."
        )

    return aliases[normalized]


def normalize_sort_order(value):
    if value is None:
        return "auto"

    if not isinstance(value, str):
        raise BatchRankingError(
            "sort order трябва да бъде текст."
        )

    normalized = value.strip().lower()

    if normalized not in SORT_ORDERS:
        raise BatchRankingError(
            "Невалиден sort order. Допустими: auto, asc, desc."
        )

    return normalized


def resolve_sort_order(metric, requested_order="auto"):
    metric = normalize_sort_metric(metric)
    requested_order = normalize_sort_order(requested_order)

    if requested_order != "auto":
        return requested_order

    if metric == "shared":
        return "desc"

    return "asc"


def normalize_display_limit(value):
    if value is None:
        return None

    if isinstance(value, bool) or not isinstance(value, int):
        raise BatchRankingError(
            "display limit трябва да бъде цяло число."
        )

    if value <= 0:
        raise BatchRankingError(
            "display limit трябва да бъде > 0."
        )

    return value


def _criterion_value(row, level, metric_key):
    if not isinstance(row, dict):
        raise BatchRankingError(
            "Batch row трябва да бъде dict."
        )

    summary = row.get("summary")

    if not isinstance(summary, dict) or level not in summary:
        raise BatchRankingError(
            f"Batch row няма summary за {LEVEL_LABELS[level]}."
        )

    level_summary = summary[level]

    if metric_key not in level_summary:
        raise BatchRankingError(
            f"Batch row няма metric {metric_key!r}."
        )

    value = level_summary[metric_key]

    if isinstance(value, bool) or not isinstance(value, int):
        raise BatchRankingError(
            f"{metric_key} трябва да бъде integer."
        )

    return value


def _candidate_tie_key(row):
    external_id = row.get("candidate_external_id")

    if not isinstance(external_id, str):
        external_id = ""

    typing_id = row.get("candidate_typing_id")

    if isinstance(typing_id, bool) or not isinstance(typing_id, int):
        typing_id = 0

    return (
        external_id.casefold(),
        external_id,
        typing_id,
    )


def order_batch_rows(
    rows,
    level=DEFAULT_SORT_LEVEL,
    metric="donor-only",
    order="auto",
    display_limit=None,
):
    """
    Returns a NEW ordered list. The input rows are not mutated.

    software_rank uses competition ranking:
        values 1, 1, 3 -> ranks 1, 1, 3

    software_position is always 1..N after deterministic sorting.
    """
    if not isinstance(rows, (list, tuple)):
        raise BatchRankingError(
            "rows трябва да бъде list/tuple."
        )

    level = normalize_sort_level(level)
    metric = normalize_sort_metric(metric)
    metric_key = METRIC_KEYS[metric]
    requested_order = normalize_sort_order(order)
    resolved_order = resolve_sort_order(
        metric,
        requested_order,
    )
    display_limit = normalize_display_limit(
        display_limit
    )

    decorated = []

    for row in rows:
        value = _criterion_value(
            row,
            level,
            metric_key,
        )

        primary = value if resolved_order == "asc" else -value

        decorated.append(
            (
                primary,
                _candidate_tie_key(row),
                value,
                row,
            )
        )

    decorated.sort(
        key=lambda item: (
            item[0],
            item[1],
        )
    )

    ranked = []
    previous_value = object()
    current_rank = 0

    for position, (_, _, value, row) in enumerate(
        decorated,
        start=1,
    ):
        if position == 1 or value != previous_value:
            current_rank = position

        row_copy = copy.deepcopy(row)
        row_copy["software_order"] = {
            "position": position,
            "rank": current_rank,
            "level": level,
            "level_label": LEVEL_LABELS[level],
            "metric": metric,
            "metric_key": metric_key,
            "metric_label": METRIC_LABELS[metric],
            "criterion_value": value,
            "order": resolved_order,
            "requested_order": requested_order,
        }

        ranked.append(row_copy)
        previous_value = value

    if display_limit is not None:
        ranked = ranked[:display_limit]

    return ranked


def apply_batch_ordering(
    batch,
    level=DEFAULT_SORT_LEVEL,
    metric="donor-only",
    order="auto",
    display_limit=None,
):
    """
    Adds STEP 18 ordering metadata without changing persistence semantics.

    Important:
      * Step 17 computation/save happens first.
      * --display-limit / --limit affects DISPLAY only.
      * When batch['save'] is True, ALL eligible pairs were saved before
        this function orders or truncates the displayed rows.
    """
    if not isinstance(batch, dict):
        raise BatchRankingError(
            "batch трябва да бъде dict."
        )

    rows = batch.get("rows")

    if not isinstance(rows, list):
        raise BatchRankingError(
            "batch['rows'] трябва да бъде list."
        )

    level = normalize_sort_level(level)
    metric = normalize_sort_metric(metric)
    requested_order = normalize_sort_order(order)
    resolved_order = resolve_sort_order(
        metric,
        requested_order,
    )
    display_limit = normalize_display_limit(
        display_limit
    )

    ordered_rows = order_batch_rows(
        rows,
        level=level,
        metric=metric,
        order=requested_order,
        display_limit=display_limit,
    )

    result = copy.deepcopy(batch)
    result["rows"] = ordered_rows
    result["displayed_pair_count"] = len(ordered_rows)
    result["software_ordering"] = {
        "enabled": True,
        "level": level,
        "level_label": LEVEL_LABELS[level],
        "metric": metric,
        "metric_key": METRIC_KEYS[metric],
        "metric_label": METRIC_LABELS[metric],
        "requested_order": requested_order,
        "order": resolved_order,
        "display_limit": display_limit,
        "total_pair_count": len(rows),
        "displayed_pair_count": len(ordered_rows),
        "persistence_scope": (
            "all eligible pairs"
            if batch.get("save")
            else "none"
        ),
    }

    return result
