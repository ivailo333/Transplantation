"""
STEP 22 — Batch Filtering & Selection.

This module creates a read-only selected view from a fully computed STEP 17
batch (optionally already ordered by STEP 18).

It does NOT calculate a clinical compatibility score.

Supported selection criteria:
    * exclude specific candidate external_ids;
    * max donor_only_count;
    * min shared_count;
    * max recipient_only_count;
    * representation level: CANONICAL / LGX / G / P.

Threshold predicates are combined with logical AND.

Important persistence/export semantics:
    * --save continues to persist ALL eligible computed pairs.
    * ordinary --export continues to export ALL computed pairs.
    * --export-selection explicitly exports only the STEP 22 selected view.
    * --limit / --display-limit remains display-only.

This separation prevents a non-clinical software filter from silently changing
the persistent audit history.
"""

from __future__ import annotations

import copy


SELECTION_LEVELS = ("canonical", "lgx", "G", "P")
DEFAULT_SELECTION_LEVEL = "lgx"

LEVEL_LABELS = {
    "canonical": "CANONICAL",
    "lgx": "LGX",
    "G": "G",
    "P": "P",
}


class BatchSelectionError(ValueError):
    """Invalid STEP 22 selection configuration."""


def normalize_selection_level(value):
    if value is None:
        return DEFAULT_SELECTION_LEVEL

    if not isinstance(value, str):
        raise BatchSelectionError(
            "selection level трябва да бъде текст."
        )

    normalized = value.strip().lower()
    mapping = {
        "canonical": "canonical",
        "lgx": "lgx",
        "g": "G",
        "p": "P",
    }

    if normalized not in mapping:
        raise BatchSelectionError(
            "Невалидно selection level. Допустими: "
            "canonical, lgx, G, P."
        )

    return mapping[normalized]


def normalize_nonnegative_int(value, name):
    if value is None:
        return None

    if isinstance(value, bool):
        raise BatchSelectionError(
            f"{name} трябва да бъде цяло число >= 0."
        )

    try:
        normalized = int(value)
    except (TypeError, ValueError) as exc:
        raise BatchSelectionError(
            f"{name} трябва да бъде цяло число >= 0."
        ) from exc

    if normalized < 0:
        raise BatchSelectionError(
            f"{name} трябва да бъде цяло число >= 0."
        )

    return normalized


def normalize_excluded_ids(values):
    if values is None:
        return []

    if not isinstance(values, (list, tuple)):
        raise BatchSelectionError(
            "excluded candidate IDs трябва да бъдат list/tuple."
        )

    seen = set()
    result = []

    for value in values:
        if not isinstance(value, str) or not value.strip():
            raise BatchSelectionError(
                "Excluded candidate external_id не може да бъде празен."
            )

        external_id = value.strip()

        if external_id in seen:
            continue

        seen.add(external_id)
        result.append(external_id)

    return result


def selection_requested(
    *,
    exclude_candidate_ids=None,
    max_donor_only=None,
    min_shared=None,
    max_recipient_only=None,
):
    return any(
        (
            bool(exclude_candidate_ids),
            max_donor_only is not None,
            min_shared is not None,
            max_recipient_only is not None,
        )
    )


def _criterion_values(row, level):
    if not isinstance(row, dict):
        raise BatchSelectionError(
            "Batch row трябва да бъде dict."
        )

    summary = row.get("summary")

    if not isinstance(summary, dict) or level not in summary:
        raise BatchSelectionError(
            f"Batch row няма summary за {LEVEL_LABELS[level]}."
        )

    values = summary[level]
    required = (
        "shared_count",
        "donor_only_count",
        "recipient_only_count",
    )

    for key in required:
        value = values.get(key)
        if isinstance(value, bool) or not isinstance(value, int):
            raise BatchSelectionError(
                f"{key} трябва да бъде integer."
            )

    return values


def select_batch_rows(
    rows,
    *,
    level=DEFAULT_SELECTION_LEVEL,
    exclude_candidate_ids=None,
    max_donor_only=None,
    min_shared=None,
    max_recipient_only=None,
):
    """
    Return NEW selected row copies while preserving incoming row order.

    If STEP 18 has already ordered the batch, that order is preserved.
    """
    if not isinstance(rows, (list, tuple)):
        raise BatchSelectionError(
            "rows трябва да бъде list/tuple."
        )

    level = normalize_selection_level(level)
    excluded = set(
        normalize_excluded_ids(exclude_candidate_ids)
    )
    max_donor_only = normalize_nonnegative_int(
        max_donor_only,
        "max_donor_only",
    )
    min_shared = normalize_nonnegative_int(
        min_shared,
        "min_shared",
    )
    max_recipient_only = normalize_nonnegative_int(
        max_recipient_only,
        "max_recipient_only",
    )

    selected = []

    for row in rows:
        candidate_id = row.get("candidate_external_id")

        if candidate_id in excluded:
            continue

        values = _criterion_values(
            row,
            level,
        )

        if (
            max_donor_only is not None
            and values["donor_only_count"] > max_donor_only
        ):
            continue

        if (
            min_shared is not None
            and values["shared_count"] < min_shared
        ):
            continue

        if (
            max_recipient_only is not None
            and values["recipient_only_count"] > max_recipient_only
        ):
            continue

        row_copy = copy.deepcopy(row)
        row_copy["step22_selection"] = {
            "selected": True,
            "level": level,
            "level_label": LEVEL_LABELS[level],
            "shared_count": values["shared_count"],
            "donor_only_count": values["donor_only_count"],
            "recipient_only_count": values["recipient_only_count"],
        }
        selected.append(row_copy)

    return selected


def apply_batch_selection(
    batch,
    *,
    level=DEFAULT_SELECTION_LEVEL,
    exclude_candidate_ids=None,
    max_donor_only=None,
    min_shared=None,
    max_recipient_only=None,
):
    """
    Return a selected batch VIEW.

    The input batch is not mutated.

    pair_count becomes the number of selected rows because this returned
    object represents the selected view. `source_pair_count` preserves the
    number of fully computed eligible pairs.
    """
    if not isinstance(batch, dict):
        raise BatchSelectionError(
            "batch трябва да бъде dict."
        )

    rows = batch.get("rows")

    if not isinstance(rows, list):
        raise BatchSelectionError(
            "batch['rows'] трябва да бъде list."
        )

    level = normalize_selection_level(level)
    excluded = normalize_excluded_ids(
        exclude_candidate_ids
    )
    max_donor_only = normalize_nonnegative_int(
        max_donor_only,
        "max_donor_only",
    )
    min_shared = normalize_nonnegative_int(
        min_shared,
        "min_shared",
    )
    max_recipient_only = normalize_nonnegative_int(
        max_recipient_only,
        "max_recipient_only",
    )

    selected_rows = select_batch_rows(
        rows,
        level=level,
        exclude_candidate_ids=excluded,
        max_donor_only=max_donor_only,
        min_shared=min_shared,
        max_recipient_only=max_recipient_only,
    )

    result = copy.deepcopy(batch)
    source_pair_count = len(rows)

    result["rows"] = selected_rows
    result["source_pair_count"] = source_pair_count
    result["pair_count"] = len(selected_rows)
    result["selected_pair_count"] = len(selected_rows)
    result["step22_selection"] = {
        "enabled": True,
        "level": level,
        "level_label": LEVEL_LABELS[level],
        "exclude_candidate_ids": excluded,
        "max_donor_only": max_donor_only,
        "min_shared": min_shared,
        "max_recipient_only": max_recipient_only,
        "source_pair_count": source_pair_count,
        "selected_pair_count": len(selected_rows),
        "rejected_pair_count": source_pair_count - len(selected_rows),
        "combination": "AND",
        "clinical_score": False,
    }

    # A selected export is a new view, not the original persistent batch.
    # Do not carry persistent batch_id as if the selected subset were itself
    # a stored Step 20 batch.
    if len(selected_rows) != source_pair_count:
        result.pop("batch_id", None)
        result.pop("created_at", None)

    return result


def render_selection_summary(selection):
    if not isinstance(selection, dict):
        raise BatchSelectionError(
            "selection metadata трябва да бъде dict."
        )

    criteria = []

    if selection.get("max_donor_only") is not None:
        criteria.append(
            f"donor_only_count <= {selection['max_donor_only']}"
        )

    if selection.get("min_shared") is not None:
        criteria.append(
            f"shared_count >= {selection['min_shared']}"
        )

    if selection.get("max_recipient_only") is not None:
        criteria.append(
            "recipient_only_count <= "
            f"{selection['max_recipient_only']}"
        )

    excluded = selection.get(
        "exclude_candidate_ids",
        [],
    )
    if excluded:
        criteria.append(
            "exclude=" + ",".join(excluded)
        )

    if not criteria:
        criteria.append("no effective predicates")

    return (
        "STEP 22 selection: "
        f"level={selection['level_label']} | "
        f"criteria={' AND '.join(criteria)} | "
        f"selected={selection['selected_pair_count']}/"
        f"{selection['source_pair_count']} | "
        f"rejected={selection['rejected_pair_count']}"
    )
