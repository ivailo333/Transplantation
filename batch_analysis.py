"""
STEP 17 — batch DONOR↔RECIPIENT analysis.

Two directions are supported:

    one RECIPIENT vs many DONOR subjects
    one DONOR vs many RECIPIENT subjects

All comparisons use the RAW/CANONICAL/LGX/G/P representations already
stored in SQLite. py-ard is not called again during batch analysis.

Default mode computes a batch in memory and does NOT create analysis_runs.
Use --save to persist the whole batch atomically.

The totals produced here are copy-sensitive software-comparison totals.
They are NOT a clinical organ-allocation, crossmatch, DSA, eplet, cPRA,
or transplant-compatibility score.
"""

from __future__ import annotations

from dataclasses import dataclass

import database
from config import HLA_LOCI
from hla_comparison import build_comparison_results_from_bundles


RESULT_LEVELS = ("canonical", "lgx", "G", "P")

LEVEL_LABELS = {
    "canonical": "CANONICAL",
    "lgx": "LGX",
    "G": "G",
    "P": "P",
}

BATCH_DIRECTIONS = ("recipient", "donor")


class BatchAnalysisError(ValueError):
    """Обща грешка при STEP 17 batch analysis."""


class BatchNoCandidatesError(BatchAnalysisError):
    """Няма подходящи subjects за batch сравнение."""


class BatchCandidateError(BatchAnalysisError):
    """Невалиден или неподходящ candidate subject."""


def normalize_batch_direction(value):
    if not isinstance(value, str):
        raise BatchAnalysisError(
            "Batch direction трябва да бъде текст."
        )

    normalized = value.strip().lower()

    if normalized not in BATCH_DIRECTIONS:
        raise BatchAnalysisError(
            "Невалидна batch direction. Допустими: recipient, donor."
        )

    return normalized


def _roles_for_direction(direction):
    direction = normalize_batch_direction(direction)

    if direction == "recipient":
        return {
            "anchor_role": "RECIPIENT",
            "candidate_role": "DONOR",
        }

    return {
        "anchor_role": "DONOR",
        "candidate_role": "RECIPIENT",
    }


def summarize_comparison_results(results):
    """
    Aggregates the six locus-level result dictionaries into one
    summary per representation level.
    """
    if not isinstance(results, dict):
        raise BatchAnalysisError("results трябва да бъде dict.")

    summary = {}

    for level in RESULT_LEVELS:
        if level not in results:
            raise BatchAnalysisError(
                f"results няма ниво {level!r}."
            )

        level_results = results[level]

        if set(level_results) != set(HLA_LOCI):
            raise BatchAnalysisError(
                f"{level}: очакват се точно локусите "
                + ", ".join(HLA_LOCI)
            )

        shared = 0
        donor_only = 0
        recipient_only = 0

        for locus in HLA_LOCI:
            result = level_results[locus]
            shared += int(result["shared_count"])
            donor_only += int(result["mismatch_count"])
            recipient_only += int(result["recipient_only_count"])

        summary[level] = {
            "shared_count": shared,
            "donor_only_count": donor_only,
            "recipient_only_count": recipient_only,
        }

    return summary


def _candidate_subjects(
    database_path,
    candidate_role,
    candidate_external_ids=None,
):
    """
    Returns candidate subjects in deterministic subject_id order.

    If candidate_external_ids is supplied, only those IDs are used,
    in the order requested by the caller.
    """
    all_subjects = database.list_subjects(database_path)
    by_external_id = {
        item["external_id"]: item
        for item in all_subjects
    }

    if candidate_external_ids:
        seen = set()
        requested = []

        for raw_id in candidate_external_ids:
            if not isinstance(raw_id, str) or not raw_id.strip():
                raise BatchCandidateError(
                    "Candidate external_id не може да бъде празен."
                )

            external_id = raw_id.strip()

            if external_id in seen:
                continue

            seen.add(external_id)

            item = by_external_id.get(external_id)

            if item is None:
                raise BatchCandidateError(
                    f"Не е намерен candidate subject {external_id!r}."
                )

            if item["subject_type"] != candidate_role:
                raise BatchCandidateError(
                    f"Candidate {external_id!r} е "
                    f"{item['subject_type']}, а се очаква "
                    f"{candidate_role}."
                )

            requested.append(item)

        return requested

    return [
        item
        for item in all_subjects
        if item["subject_type"] == candidate_role
    ]


def build_batch_plan(
    database_path,
    direction,
    anchor_external_id,
    anchor_typing_id=None,
    candidate_external_ids=None,
):
    """
    Resolves the anchor typing and the latest typing for every candidate.

    Version-incompatible candidates are returned in skipped[] instead of
    being compared. Missing/incomplete explicitly requested candidates
    still raise a clear error.
    """
    roles = _roles_for_direction(direction)
    anchor_role = roles["anchor_role"]
    candidate_role = roles["candidate_role"]

    anchor = database.load_subject_typing(
        database_path=database_path,
        external_id=anchor_external_id,
        subject_type=anchor_role,
        typing_id=anchor_typing_id,
    )

    subjects = _candidate_subjects(
        database_path,
        candidate_role,
        candidate_external_ids=candidate_external_ids,
    )

    eligible = []
    skipped = []

    for item in subjects:
        if item["latest_typing_id"] is None:
            skipped.append(
                {
                    "external_id": item["external_id"],
                    "reason": "subject has no saved HLA typing",
                }
            )
            continue

        try:
            loaded = database.load_subject_typing(
                database_path=database_path,
                external_id=item["external_id"],
                subject_type=candidate_role,
                typing_id=item["latest_typing_id"],
            )
        except (
            database.TypingNotFoundError,
            database.IncompleteTypingError,
        ) as exc:
            if candidate_external_ids:
                raise BatchCandidateError(
                    f"Candidate {item['external_id']!r}: {exc}"
                ) from exc

            skipped.append(
                {
                    "external_id": item["external_id"],
                    "reason": str(exc),
                }
            )
            continue

        anchor_version = anchor["typing"]["imgthla_version"]
        candidate_version = loaded["typing"]["imgthla_version"]

        if candidate_version != anchor_version:
            skipped.append(
                {
                    "external_id": item["external_id"],
                    "reason": (
                        "IPD-IMGT/HLA version mismatch: "
                        f"{candidate_version} != {anchor_version}"
                    ),
                }
            )
            continue

        if anchor_role == "RECIPIENT":
            donor = loaded
            recipient = anchor
        else:
            donor = anchor
            recipient = loaded

        eligible.append(
            {
                "donor": donor,
                "recipient": recipient,
                "candidate_external_id": item["external_id"],
                "candidate_typing_id": loaded["typing"]["typing_id"],
            }
        )

    if not eligible:
        raise BatchNoCandidatesError(
            f"Няма подходящи {candidate_role} typings за batch анализ."
        )

    return {
        "direction": normalize_batch_direction(direction),
        "anchor_role": anchor_role,
        "candidate_role": candidate_role,
        "anchor": anchor,
        "eligible": eligible,
        "skipped": skipped,
    }


def _compute_plan_results(plan):
    rows = []

    for pair in plan["eligible"]:
        donor = pair["donor"]
        recipient = pair["recipient"]

        results = build_comparison_results_from_bundles(
            donor["bundle"],
            recipient["bundle"],
        )

        rows.append(
            {
                "donor_external_id": donor["subject"]["external_id"],
                "donor_typing_id": donor["typing"]["typing_id"],
                "recipient_external_id": (
                    recipient["subject"]["external_id"]
                ),
                "recipient_typing_id": (
                    recipient["typing"]["typing_id"]
                ),
                "imgthla_version": donor["typing"]["imgthla_version"],
                "candidate_external_id": pair["candidate_external_id"],
                "candidate_typing_id": pair["candidate_typing_id"],
                "results": results,
                "summary": summarize_comparison_results(results),
                "run_id": None,
            }
        )

    return rows


def run_batch_analysis(
    database_path,
    direction,
    anchor_external_id,
    anchor_typing_id=None,
    candidate_external_ids=None,
    save=False,
):
    """
    Executes one-to-many HLA software comparisons.

    save=False:
        no analysis_runs / analysis_results are written.

    save=True:
        every pair is saved in ONE SQLite transaction via
        database.save_batch_analysis_runs(); if any pair fails,
        the whole persisted batch is rolled back.
    """
    database.migrate_database(database_path)
    database.verify_database_is_current(database_path)

    plan = build_batch_plan(
        database_path=database_path,
        direction=direction,
        anchor_external_id=anchor_external_id,
        anchor_typing_id=anchor_typing_id,
        candidate_external_ids=candidate_external_ids,
    )

    rows = _compute_plan_results(plan)

    if save:
        payloads = [
            {
                "donor_typing_id": row["donor_typing_id"],
                "recipient_typing_id": row["recipient_typing_id"],
                "imgthla_version": row["imgthla_version"],
                "results": row["results"],
            }
            for row in rows
        ]

        saved = database.save_batch_analysis_runs(
            database_path=database_path,
            pairs=payloads,
        )

        if len(saved) != len(rows):
            raise BatchAnalysisError(
                "Броят saved batch runs не съвпада с "
                "броя computed pairs."
            )

        for row, save_info in zip(rows, saved):
            row["run_id"] = save_info["run_id"]

    anchor = plan["anchor"]

    return {
        "direction": plan["direction"],
        "anchor_role": plan["anchor_role"],
        "candidate_role": plan["candidate_role"],
        "anchor_external_id": anchor["subject"]["external_id"],
        "anchor_typing_id": anchor["typing"]["typing_id"],
        "imgthla_version": anchor["typing"]["imgthla_version"],
        "save": bool(save),
        "pair_count": len(rows),
        "skipped_count": len(plan["skipped"]),
        "rows": rows,
        "skipped": plan["skipped"],
    }
