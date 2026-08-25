"""
STEP 28 — HLA Report Comparison / Multi-Report Analysis.

Compares already-derived STEP 27 analytical reports in two non-clinical modes:

1. LEVELS
   Compare the same live donor/recipient scope across representation levels:
   CANONICAL / LGX / G / P.

2. BATCHES
   Compare two persisted historical batches at one selected representation level.

The module only compares deterministic software counts and descriptive
STEP 25 classifications contained in STEP 27 reports. It does not calculate
clinical compatibility, risk, virtual crossmatch, DSA, eplet mismatch, cPRA,
allocation priority, or transplant suitability.
"""

from __future__ import annotations

import csv
import json
from pathlib import Path

import hla_matrix
import html_reports
import mismatch_summary
import step27_reporting


COMPARISON_SCHEMA = "hla-report-comparison-v1"
DEFAULT_EXPORT_DIR = Path(__file__).with_name("exports") / "comparisons"
VALID_EXPORT_FORMATS = ("json", "csv", "html", "both", "all")
VALID_MODES = ("levels", "batches")

_LEVEL_ORDER = ("canonical", "lgx", "G", "P")
DELTA_SHARED_LABEL = "d_shared"
DELTA_DONOR_LABEL = "d_donor"
DELTA_RECIPIENT_LABEL = "d_recipient"
DELTA_COMPLETE_LABEL = "d_complete"
DELTA_PARTIAL_LABEL = "d_partial"
DELTA_NO_SHARED_LABEL = "d_no_shared"


class ReportComparisonError(ValueError):
    """Invalid STEP 28 comparison request."""


class ReportComparisonExportError(RuntimeError):
    """STEP 28 export error."""


class ReportComparisonExportExistsError(ReportComparisonExportError):
    """STEP 28 target export already exists."""


def normalize_levels(values):
    if values is None:
        return list(_LEVEL_ORDER)

    if not isinstance(values, (list, tuple)):
        values = [values]

    normalized = []
    seen = set()

    for value in values:
        level = hla_matrix.normalize_level(value)
        if level not in seen:
            seen.add(level)
            normalized.append(level)

    if len(normalized) < 2:
        raise ReportComparisonError(
            "STEP 28 level comparison изисква поне две различни нива."
        )

    return normalized


def _pair_map(report):
    return {
        row["candidate_external_id"]: row
        for row in report.get("pair_rows", [])
    }


def _locus_map(report):
    return {
        row["locus"]: row
        for row in report.get("locus_rows", [])
    }


def _report_scope(report):
    return {
        "source": report["source"],
        "direction": report["direction"],
        "anchor_external_id": report["anchor"]["external_id"],
        "anchor_typing_id": report["anchor"]["typing_id"],
        "imgthla_version": report["hla_reference"]["ipd_imgt_hla_version"],
        "loci": list(report["hla_reference"]["loci"]),
        "pair_count": report["pair_count"],
        "candidate_ids": sorted(_pair_map(report)),
    }


def _validate_level_reports(reports):
    if not reports or len(reports) < 2:
        raise ReportComparisonError(
            "STEP 28 level comparison изисква поне два STEP 27 reports."
        )

    for report in reports:
        if report.get("schema") != step27_reporting.REPORT_SCHEMA:
            raise ReportComparisonError(
                "STEP 28 изисква STEP 27 report payloads."
            )

    base = _report_scope(reports[0])
    for report in reports[1:]:
        scope = _report_scope(report)
        for key in (
            "source",
            "direction",
            "anchor_external_id",
            "anchor_typing_id",
            "imgthla_version",
            "loci",
            "pair_count",
            "candidate_ids",
        ):
            if scope[key] != base[key]:
                raise ReportComparisonError(
                    "STEP 28 level-comparison scope mismatch за "
                    f"{key}: {base[key]!r} != {scope[key]!r}."
                )


def _validate_batch_reports(left, right):
    for report in (left, right):
        if report.get("schema") != step27_reporting.REPORT_SCHEMA:
            raise ReportComparisonError(
                "STEP 28 batch comparison изисква STEP 27 report payloads."
            )
        if report.get("source") != "PERSISTENT-BATCH":
            raise ReportComparisonError(
                "STEP 28 batch comparison изисква persistent reports."
            )

    if left["direction"] != right["direction"]:
        raise ReportComparisonError(
            "STEP 28 batch comparison изисква еднаква direction."
        )

    if (
        left["anchor"]["external_id"]
        != right["anchor"]["external_id"]
    ):
        raise ReportComparisonError(
            "STEP 28 batch comparison изисква еднакъв anchor external_id."
        )

    if (
        list(left["hla_reference"]["loci"])
        != list(right["hla_reference"]["loci"])
    ):
        raise ReportComparisonError(
            "STEP 28 batch comparison изисква еднакъв locus scope."
        )

    if (
        left["hla_reference"]["level"]
        != right["hla_reference"]["level"]
    ):
        raise ReportComparisonError(
            "STEP 28 batch comparison изисква еднакво representation level."
        )


def _level_summary_row(report):
    pair_rows = report.get("pair_rows", [])
    return {
        "level": report["hla_reference"]["level"],
        "level_label": report["hla_reference"]["level_label"],
        "pair_count": report["pair_count"],
        "shared_sum": sum(row["shared_count"] for row in pair_rows),
        "donor_only_sum": sum(
            row["donor_only_count"] for row in pair_rows
        ),
        "recipient_only_sum": sum(
            row["recipient_only_count"] for row in pair_rows
        ),
        "complete_count": report[
            "pair_classification_distribution"
        ][mismatch_summary.CLASS_COMPLETE]["count"],
        "partial_count": report[
            "pair_classification_distribution"
        ][mismatch_summary.CLASS_PARTIAL]["count"],
        "no_shared_count": report[
            "pair_classification_distribution"
        ][mismatch_summary.CLASS_NONE]["count"],
    }


def _delta_row(candidate_id, from_label, to_label, left, right):
    return {
        "candidate_external_id": candidate_id,
        "from": from_label,
        "to": to_label,
        "shared_delta": (
            right["shared_count"] - left["shared_count"]
        ),
        "donor_only_delta": (
            right["donor_only_count"] - left["donor_only_count"]
        ),
        "recipient_only_delta": (
            right["recipient_only_count"]
            - left["recipient_only_count"]
        ),
        "from_classification": left["classification"],
        "to_classification": right["classification"],
        "classification_changed": (
            left["classification"] != right["classification"]
        ),
    }


def _locus_delta_rows(left_report, right_report, from_label, to_label):
    left_map = _locus_map(left_report)
    right_map = _locus_map(right_report)
    rows = []

    for locus in left_report["hla_reference"]["loci"]:
        left = left_map[locus]
        right = right_map[locus]
        rows.append(
            {
                "locus": locus,
                "from": from_label,
                "to": to_label,
                "shared_sum_delta": (
                    right["shared_sum"] - left["shared_sum"]
                ),
                "donor_only_sum_delta": (
                    right["donor_only_sum"]
                    - left["donor_only_sum"]
                ),
                "recipient_only_sum_delta": (
                    right["recipient_only_sum"]
                    - left["recipient_only_sum"]
                ),
                "complete_count_delta": (
                    right["complete_count"]
                    - left["complete_count"]
                ),
                "partial_count_delta": (
                    right["partial_count"]
                    - left["partial_count"]
                ),
                "no_shared_count_delta": (
                    right["no_shared_count"]
                    - left["no_shared_count"]
                ),
            }
        )

    return rows


def build_level_comparison_from_reports(reports):
    _validate_level_reports(reports)

    base = reports[0]
    base_label = base["hla_reference"]["level_label"]
    base_pairs = _pair_map(base)

    level_rows = [_level_summary_row(report) for report in reports]
    pair_deltas = []
    locus_deltas = []

    for report in reports[1:]:
        target_label = report["hla_reference"]["level_label"]
        target_pairs = _pair_map(report)

        for candidate_id in sorted(base_pairs):
            pair_deltas.append(
                _delta_row(
                    candidate_id,
                    base_label,
                    target_label,
                    base_pairs[candidate_id],
                    target_pairs[candidate_id],
                )
            )

        locus_deltas.extend(
            _locus_delta_rows(
                base,
                report,
                base_label,
                target_label,
            )
        )

    stable_counts = 0
    stable_class = 0
    candidate_ids = sorted(base_pairs)

    for candidate_id in candidate_ids:
        rows = [
            _pair_map(report)[candidate_id]
            for report in reports
        ]
        count_tuples = {
            (
                row["shared_count"],
                row["donor_only_count"],
                row["recipient_only_count"],
            )
            for row in rows
        }
        classes = {
            row["classification"]
            for row in rows
        }
        if len(count_tuples) == 1:
            stable_counts += 1
        if len(classes) == 1:
            stable_class += 1

    return {
        "schema": COMPARISON_SCHEMA,
        "step": 28,
        "mode": "levels",
        "clinical": False,
        "source": base["source"],
        "direction": base["direction"],
        "anchor": dict(base["anchor"]),
        "imgthla_version": base[
            "hla_reference"
        ]["ipd_imgt_hla_version"],
        "loci": list(base["hla_reference"]["loci"]),
        "levels": [
            report["hla_reference"]["level"]
            for report in reports
        ],
        "level_labels": [
            report["hla_reference"]["level_label"]
            for report in reports
        ],
        "reference_level": base[
            "hla_reference"
        ]["level"],
        "reference_level_label": base_label,
        "pair_count": base["pair_count"],
        "level_rows": level_rows,
        "pair_delta_rows": pair_deltas,
        "locus_delta_rows": locus_deltas,
        "stability": {
            "candidate_count": len(candidate_ids),
            "identical_total_counts_across_levels": stable_counts,
            "stable_pair_classification_across_levels": stable_class,
        },
        "provenance": {
            "step27_reports_compared": len(reports),
            "pyard_recalculated_by_step28": False,
            "analysis_run_created_by_step28": False,
        },
    }


def build_live_level_comparison(
    database_path,
    direction,
    anchor_external_id,
    *,
    anchor_typing_id=None,
    candidate_external_ids=None,
    levels=None,
    loci=None,
    sort_by=None,
    sort_order="auto",
):
    levels = normalize_levels(levels)
    reports = [
        step27_reporting.build_live_report(
            database_path=database_path,
            direction=direction,
            anchor_external_id=anchor_external_id,
            anchor_typing_id=anchor_typing_id,
            candidate_external_ids=candidate_external_ids,
            level=level,
            loci=loci,
            sort_by=sort_by,
            sort_order=sort_order,
        )
        for level in levels
    ]
    return build_level_comparison_from_reports(reports)


def build_batch_comparison_from_reports(left, right):
    _validate_batch_reports(left, right)

    left_pairs = _pair_map(left)
    right_pairs = _pair_map(right)

    left_ids = set(left_pairs)
    right_ids = set(right_pairs)

    common = sorted(left_ids & right_ids)
    only_left = sorted(left_ids - right_ids)
    only_right = sorted(right_ids - left_ids)

    pair_deltas = [
        _delta_row(
            candidate_id,
            f"batch-{left['batch_id']}",
            f"batch-{right['batch_id']}",
            left_pairs[candidate_id],
            right_pairs[candidate_id],
        )
        for candidate_id in common
    ]

    return {
        "schema": COMPARISON_SCHEMA,
        "step": 28,
        "mode": "batches",
        "clinical": False,
        "source": "PERSISTENT-BATCH-COMPARISON",
        "direction": left["direction"],
        "anchor_external_id": left["anchor"]["external_id"],
        "left": {
            "batch_id": left["batch_id"],
            "anchor_typing_id": left["anchor"]["typing_id"],
            "imgthla_version": left[
                "hla_reference"
            ]["ipd_imgt_hla_version"],
            "pair_count": left["pair_count"],
        },
        "right": {
            "batch_id": right["batch_id"],
            "anchor_typing_id": right["anchor"]["typing_id"],
            "imgthla_version": right[
                "hla_reference"
            ]["ipd_imgt_hla_version"],
            "pair_count": right["pair_count"],
        },
        "level": left["hla_reference"]["level"],
        "level_label": left["hla_reference"]["level_label"],
        "loci": list(left["hla_reference"]["loci"]),
        "common_candidates": common,
        "only_left_candidates": only_left,
        "only_right_candidates": only_right,
        "pair_delta_rows": pair_deltas,
        "locus_delta_rows": _locus_delta_rows(
            left,
            right,
            f"batch-{left['batch_id']}",
            f"batch-{right['batch_id']}",
        ),
        "context_changes": {
            "anchor_typing_changed": (
                left["anchor"]["typing_id"]
                != right["anchor"]["typing_id"]
            ),
            "imgthla_version_changed": (
                left["hla_reference"]["ipd_imgt_hla_version"]
                != right["hla_reference"]["ipd_imgt_hla_version"]
            ),
            "candidate_membership_changed": bool(
                only_left or only_right
            ),
        },
        "provenance": {
            "step27_reports_compared": 2,
            "pyard_recalculated_by_step28": False,
            "analysis_run_created_by_step28": False,
        },
    }


def build_persistent_batch_comparison(
    database_path,
    left_batch_id,
    right_batch_id,
    *,
    level=hla_matrix.DEFAULT_LEVEL,
    loci=None,
    sort_by=None,
    sort_order="auto",
):
    if left_batch_id == right_batch_id:
        raise ReportComparisonError(
            "STEP 28 batch comparison изисква два различни batch_id."
        )

    left = step27_reporting.build_persistent_report(
        database_path=database_path,
        batch_id=left_batch_id,
        level=level,
        loci=loci,
        sort_by=sort_by,
        sort_order=sort_order,
    )
    right = step27_reporting.build_persistent_report(
        database_path=database_path,
        batch_id=right_batch_id,
        level=level,
        loci=loci,
        sort_by=sort_by,
        sort_order=sort_order,
    )
    return build_batch_comparison_from_reports(left, right)


def _signed(value):
    if value > 0:
        return f"+{value}"
    return str(value)


def render_comparison(comparison):
    lines = [
        "=" * 118,
        "STEP 28 - HLA REPORT COMPARISON / MULTI-REPORT ANALYSIS",
        "=" * 118,
    ]

    if comparison["mode"] == "levels":
        lines.extend(
            [
                "Mode: LEVELS",
                f"Source: {comparison['source']}",
                (
                    f"Direction: {comparison['direction']} | "
                    f"anchor={comparison['anchor']['external_id']} "
                    f"(typing {comparison['anchor']['typing_id']})"
                ),
                (
                    f"IPD-IMGT/HLA={comparison['imgthla_version']} | "
                    f"levels={','.join(comparison['level_labels'])} | "
                    f"reference={comparison['reference_level_label']} | "
                    f"pairs={comparison['pair_count']} | "
                    f"loci={','.join(comparison['loci'])}"
                ),
                "",
                "LEVEL OVERVIEW",
                "-" * 118,
                (
                    f"{'level':<12}{'pairs':>7}"
                    f"{'shared_sum':>13}"
                    f"{'donor_only_sum':>17}"
                    f"{'recipient_only_sum':>21}"
                    f"{'complete':>11}"
                    f"{'partial':>10}"
                    f"{'no_shared':>11}"
                ),
            ]
        )
        for row in comparison["level_rows"]:
            lines.append(
                f"{row['level_label']:<12}"
                f"{row['pair_count']:>7}"
                f"{row['shared_sum']:>13}"
                f"{row['donor_only_sum']:>17}"
                f"{row['recipient_only_sum']:>21}"
                f"{row['complete_count']:>11}"
                f"{row['partial_count']:>10}"
                f"{row['no_shared_count']:>11}"
            )

        lines.extend(
            [
                "",
                "PAIR DELTAS FROM REFERENCE LEVEL",
                "-" * 118,
                (
                    f"{'candidate':<24}{'from':<12}{'to':<12}"
                    f"{DELTA_SHARED_LABEL:>10}"
                    f"{DELTA_DONOR_LABEL:>10}"
                    f"{DELTA_RECIPIENT_LABEL:>13}  "
                    "classification_changed"
                ),
            ]
        )

        if comparison["pair_delta_rows"]:
            for row in comparison["pair_delta_rows"]:
                lines.append(
                    f"{row['candidate_external_id']:<24}"
                    f"{row['from']:<12}{row['to']:<12}"
                    f"{_signed(row['shared_delta']):>10}"
                    f"{_signed(row['donor_only_delta']):>10}"
                    f"{_signed(row['recipient_only_delta']):>13}  "
                    f"{'YES' if row['classification_changed'] else 'NO'}"
                )
        else:
            lines.append("(no represented pair deltas)")

        stability = comparison["stability"]
        lines.extend(
            [
                "",
                "CROSS-LEVEL STABILITY",
                "-" * 118,
                (
                    "Candidates represented: "
                    f"{stability['candidate_count']}"
                ),
                (
                    "Identical total counts across all levels: "
                    f"{stability['identical_total_counts_across_levels']}"
                ),
                (
                    "Stable pair classification across all levels: "
                    f"{stability['stable_pair_classification_across_levels']}"
                ),
            ]
        )

    elif comparison["mode"] == "batches":
        lines.extend(
            [
                "Mode: BATCHES",
                (
                    f"Direction: {comparison['direction']} | "
                    f"anchor={comparison['anchor_external_id']} | "
                    f"level={comparison['level_label']} | "
                    f"loci={','.join(comparison['loci'])}"
                ),
                (
                    f"Left batch: {comparison['left']['batch_id']} | "
                    f"typing={comparison['left']['anchor_typing_id']} | "
                    f"IPD-IMGT/HLA={comparison['left']['imgthla_version']} | "
                    f"pairs={comparison['left']['pair_count']}"
                ),
                (
                    f"Right batch: {comparison['right']['batch_id']} | "
                    f"typing={comparison['right']['anchor_typing_id']} | "
                    f"IPD-IMGT/HLA={comparison['right']['imgthla_version']} | "
                    f"pairs={comparison['right']['pair_count']}"
                ),
                "",
                "CANDIDATE MEMBERSHIP",
                "-" * 118,
                (
                    "Common: "
                    + (
                        ", ".join(comparison["common_candidates"])
                        if comparison["common_candidates"]
                        else "(none)"
                    )
                ),
                (
                    "Only left: "
                    + (
                        ", ".join(comparison["only_left_candidates"])
                        if comparison["only_left_candidates"]
                        else "(none)"
                    )
                ),
                (
                    "Only right: "
                    + (
                        ", ".join(comparison["only_right_candidates"])
                        if comparison["only_right_candidates"]
                        else "(none)"
                    )
                ),
                "",
                "COMMON-CANDIDATE DELTAS",
                "-" * 118,
                (
                    f"{'candidate':<24}"
                    f"{DELTA_SHARED_LABEL:>10}"
                    f"{DELTA_DONOR_LABEL:>10}"
                    f"{DELTA_RECIPIENT_LABEL:>13}  "
                    "classification_changed"
                ),
            ]
        )

        if comparison["pair_delta_rows"]:
            for row in comparison["pair_delta_rows"]:
                lines.append(
                    f"{row['candidate_external_id']:<24}"
                    f"{_signed(row['shared_delta']):>10}"
                    f"{_signed(row['donor_only_delta']):>10}"
                    f"{_signed(row['recipient_only_delta']):>13}  "
                    f"{'YES' if row['classification_changed'] else 'NO'}"
                )
        else:
            lines.append("(no common candidates)")

        changes = comparison["context_changes"]
        lines.extend(
            [
                "",
                "CONTEXT CHANGES",
                "-" * 118,
                (
                    "Anchor typing changed: "
                    f"{'YES' if changes['anchor_typing_changed'] else 'NO'}"
                ),
                (
                    "IPD-IMGT/HLA version changed: "
                    f"{'YES' if changes['imgthla_version_changed'] else 'NO'}"
                ),
                (
                    "Candidate membership changed: "
                    f"{'YES' if changes['candidate_membership_changed'] else 'NO'}"
                ),
            ]
        )
    else:
        raise ReportComparisonError(
            f"Непознат STEP 28 mode: {comparison.get('mode')!r}."
        )

    lines.extend(
        [
            "",
            "LOCUS AGGREGATE DELTAS",
            "-" * 118,
            (
                f"{'locus':<8}{'from':<14}{'to':<14}"
                f"{DELTA_SHARED_LABEL:>10}"
                f"{DELTA_DONOR_LABEL:>10}"
                f"{DELTA_RECIPIENT_LABEL:>13}"
                f"{DELTA_COMPLETE_LABEL:>12}"
                f"{DELTA_PARTIAL_LABEL:>11}"
                f"{DELTA_NO_SHARED_LABEL:>13}"
            ),
        ]
    )
    for row in comparison["locus_delta_rows"]:
        lines.append(
            f"{row['locus']:<8}"
            f"{row['from']:<14}{row['to']:<14}"
            f"{_signed(row['shared_sum_delta']):>10}"
            f"{_signed(row['donor_only_sum_delta']):>10}"
            f"{_signed(row['recipient_only_sum_delta']):>13}"
            f"{_signed(row['complete_count_delta']):>12}"
            f"{_signed(row['partial_count_delta']):>11}"
            f"{_signed(row['no_shared_count_delta']):>13}"
        )

    lines.extend(
        [
            "-" * 118,
            "STEP 28 compares deterministic NON-CLINICAL software reports only.",
            "Deltas show changes between software representations or persisted report scopes; they are NOT clinical improvement/deterioration, compatibility probabilities, risk estimates, allocation scores, virtual crossmatch, DSA, eplet, cPRA, or transplant-suitability decisions.",
            "STEP 28 does NOT recalculate py-ard reductions and does NOT create analysis_runs.",
            "=" * 118,
        ]
    )
    return "\n".join(lines)


def _summary_items(comparison):
    if comparison["mode"] == "levels":
        anchor = comparison["anchor"]
        return [
            ("Mode", "LEVELS"),
            ("Direction", comparison["direction"]),
            ("Anchor", f"{anchor['external_id']} / typing {anchor['typing_id']}"),
            ("Levels", ", ".join(comparison["levels"])),
            ("Pairs", comparison["pair_count"]),
            ("Loci", ", ".join(comparison["loci"])),
        ]
    return [
        ("Mode", "BATCHES"),
        ("Left batch", comparison["left"]["batch_id"]),
        ("Right batch", comparison["right"]["batch_id"]),
        ("Level", comparison["level_label"]),
        ("Common pairs", len(comparison["common_candidates"])),
        ("Loci", ", ".join(comparison["loci"])),
    ]


def render_comparison_html(comparison):
    level_columns = (
        ("level_label", "Level"),
        ("pair_count", "Pairs"),
        ("shared_sum", "Shared sum"),
        ("donor_only_sum", "Donor only sum"),
        ("recipient_only_sum", "Recipient only sum"),
        ("complete_count", "Complete"),
        ("partial_count", "Partial"),
        ("no_shared_count", "No shared"),
    )
    pair_columns = (
        ("candidate_external_id", "Candidate"),
        ("from", "From"),
        ("to", "To"),
        ("shared_delta", "d shared"),
        ("donor_only_delta", "d donor"),
        ("recipient_only_delta", "d recipient"),
        ("classification_changed", "Class changed"),
    )
    locus_columns = (
        ("locus", "Locus"),
        ("from", "From"),
        ("to", "To"),
        ("shared_sum_delta", "d shared sum"),
        ("donor_only_sum_delta", "d donor sum"),
        ("recipient_only_sum_delta", "d recipient sum"),
        ("complete_count_delta", "d complete"),
        ("partial_count_delta", "d partial"),
        ("no_shared_count_delta", "d no shared"),
    )

    sections = []
    if comparison["mode"] == "levels":
        sections.append(
            ("Level Overview", html_reports.render_table(level_columns, comparison["level_rows"]))
        )

    sections.extend(
        (
            ("Pair Deltas", html_reports.render_table(pair_columns, comparison["pair_delta_rows"])),
            ("Locus Deltas", html_reports.render_table(locus_columns, comparison["locus_delta_rows"])),
        )
    )

    if comparison["mode"] == "batches":
        membership_rows = [
            {"candidate_external_id": item, "membership": "ONLY_LEFT"}
            for item in comparison["only_left_candidates"]
        ] + [
            {"candidate_external_id": item, "membership": "ONLY_RIGHT"}
            for item in comparison["only_right_candidates"]
        ]
        sections.append(
            (
                "Candidate Membership",
                html_reports.render_table(
                    (
                        ("candidate_external_id", "Candidate"),
                        ("membership", "Membership"),
                    ),
                    membership_rows,
                ),
            )
        )

    return html_reports.render_page(
        "STEP 28 HLA Report Comparison",
        _summary_items(comparison),
        sections,
        (
            "STEP 28 compares deterministic NON-CLINICAL software reports only. "
            "It does not recalculate py-ard reductions and does not create analysis_runs."
        ),
        theme="blue",
    )


def normalize_export_format(value):
    if value is None:
        return "both"
    if not isinstance(value, str):
        raise ReportComparisonError(
            "comparison export format трябва да бъде текст."
        )
    value = value.strip().lower()
    if value not in VALID_EXPORT_FORMATS:
        raise ReportComparisonError(
            "Невалиден export format. Допустими: json, csv, html, both, all."
        )
    return value


def default_export_name(comparison):
    if comparison["mode"] == "levels":
        levels = "-".join(comparison["levels"])
        return (
            f"compare_levels_{comparison['direction']}_"
            f"{comparison['anchor']['external_id']}_"
            f"typing{comparison['anchor']['typing_id']}_{levels}"
        )
    return (
        f"compare_batches_{comparison['left']['batch_id']}_"
        f"{comparison['right']['batch_id']}_{comparison['level']}"
    )


_CSV_COLUMNS = (
    "record_type",
    "mode",
    "level",
    "level_label",
    "candidate_external_id",
    "locus",
    "from",
    "to",
    "pair_count",
    "shared_sum",
    "donor_only_sum",
    "recipient_only_sum",
    "complete_count",
    "partial_count",
    "no_shared_count",
    "shared_delta",
    "donor_only_delta",
    "recipient_only_delta",
    "shared_sum_delta",
    "donor_only_sum_delta",
    "recipient_only_sum_delta",
    "complete_count_delta",
    "partial_count_delta",
    "no_shared_count_delta",
    "classification_changed",
    "membership",
)


def iter_csv_rows(comparison):
    if comparison["mode"] == "levels":
        for row in comparison["level_rows"]:
            yield {
                "record_type": "LEVEL",
                "mode": "levels",
                **row,
            }

    for row in comparison["pair_delta_rows"]:
        yield {
            "record_type": "PAIR_DELTA",
            "mode": comparison["mode"],
            **row,
        }

    for row in comparison["locus_delta_rows"]:
        yield {
            "record_type": "LOCUS_DELTA",
            "mode": comparison["mode"],
            **row,
        }

    if comparison["mode"] == "batches":
        for candidate_id in comparison["only_left_candidates"]:
            yield {
                "record_type": "MEMBERSHIP",
                "mode": "batches",
                "candidate_external_id": candidate_id,
                "membership": "ONLY_LEFT",
            }
        for candidate_id in comparison["only_right_candidates"]:
            yield {
                "record_type": "MEMBERSHIP",
                "mode": "batches",
                "candidate_external_id": candidate_id,
                "membership": "ONLY_RIGHT",
            }


def export_comparison(
    comparison,
    *,
    output_dir=DEFAULT_EXPORT_DIR,
    export_format="both",
    export_name=None,
    overwrite=False,
):
    export_format = normalize_export_format(export_format)
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    name = export_name or default_export_name(comparison)
    if not isinstance(name, str) or not name.strip():
        raise ReportComparisonError(
            "comparison export name не може да бъде празно."
        )
    name = name.strip()

    targets = {}
    if export_format in ("json", "both", "all"):
        targets["json"] = output_dir / f"{name}.json"
    if export_format in ("csv", "both", "all"):
        targets["csv"] = output_dir / f"{name}.csv"
    if export_format in ("html", "all"):
        targets["html"] = output_dir / f"{name}.html"

    if not overwrite:
        existing = [
            path for path in targets.values()
            if path.exists()
        ]
        if existing:
            raise ReportComparisonExportExistsError(
                "STEP 28 comparison export файл вече съществува. "
                "Използвайте --overwrite: "
                + ", ".join(str(path) for path in existing)
            )

    if "json" in targets:
        tmp = targets["json"].with_name(
            targets["json"].name + ".tmp"
        )
        try:
            tmp.write_text(
                json.dumps(
                    comparison,
                    ensure_ascii=False,
                    indent=2,
                ) + "\n",
                encoding="utf-8",
            )
            tmp.replace(targets["json"])
        finally:
            if tmp.exists():
                tmp.unlink()

    if "csv" in targets:
        tmp = targets["csv"].with_name(
            targets["csv"].name + ".tmp"
        )
        try:
            with tmp.open(
                "w",
                encoding="utf-8",
                newline="",
            ) as handle:
                writer = csv.DictWriter(
                    handle,
                    fieldnames=_CSV_COLUMNS,
                    extrasaction="ignore",
                )
                writer.writeheader()
                writer.writerows(iter_csv_rows(comparison))
            tmp.replace(targets["csv"])
        finally:
            if tmp.exists():
                tmp.unlink()


    if "html" in targets:
        tmp = targets["html"].with_name(
            targets["html"].name + ".tmp"
        )
        try:
            tmp.write_text(
                render_comparison_html(comparison),
                encoding="utf-8",
            )
            tmp.replace(targets["html"])
        finally:
            if tmp.exists():
                tmp.unlink()

    return {
        "format": export_format.upper(),
        "export_name": name,
        "output_dir": output_dir,
        "json_path": targets.get("json"),
        "csv_path": targets.get("csv"),
        "html_path": targets.get("html"),
        "mode": comparison["mode"],
    }


def render_export_summary(info):
    lines = [
        "=" * 96,
        "STEP 28 - REPORT COMPARISON EXPORT COMPLETE",
        "=" * 96,
        f"Mode: {info['mode'].upper()}",
        f"Export name: {info['export_name']}",
        f"Format: {info['format']}",
        f"Output directory: {info['output_dir']}",
    ]
    if info.get("json_path") is not None:
        lines.append(f"JSON: {info['json_path']}")
    if info.get("csv_path") is not None:
        lines.append(f"CSV: {info['csv_path']}")
    if info.get("html_path") is not None:
        lines.append(f"HTML: {info['html_path']}")
    lines.extend(
        [
            "Export contains NON-CLINICAL software-report comparison data only.",
            "No py-ard reductions are recalculated and no analysis_runs are created.",
            "=" * 96,
        ]
    )
    return "\n".join(lines)
