"""
STEP 27 — HLA Analytical Reporting.

Composes already-derived STEP 24, STEP 25, and STEP 26 data into one
deterministic analytical report.

Pipeline:
    STEP 24 matrix
        -> STEP 25 mismatch summary / descriptive classification
        -> STEP 26 descriptive statistics
        -> STEP 27 report

STEP 27 performs scope and aggregate consistency validation but does NOT
recalculate HLA representations, call py-ard reductions, create analysis
runs, or produce clinical compatibility/risk/allocation decisions.
"""

from __future__ import annotations

import csv
import json
from pathlib import Path

import comparison_statistics
import html_reports
import hla_matrix
import mismatch_summary


REPORT_SCHEMA = "hla-analytical-report-v1"
REPORT_TYPE = "HLA_ANALYTICAL_REPORT"
DEFAULT_EXPORT_DIR = Path(__file__).with_name("exports") / "reports"
VALID_EXPORT_FORMATS = ("json", "csv", "html", "both", "all")


class ReportingError(ValueError):
    """Invalid or inconsistent STEP 27 reporting request."""


class ReportingExportError(RuntimeError):
    """STEP 27 export error."""


class ReportingExportExistsError(ReportingExportError):
    """STEP 27 target export already exists."""


_SCOPE_KEYS = (
    "source",
    "batch_id",
    "direction",
    "anchor_external_id",
    "anchor_typing_id",
    "imgthla_version",
    "level",
    "level_label",
    "loci",
    "pair_count",
)


def _candidate_ids_from_matrix(matrix):
    return [
        row["candidate_external_id"]
        for row in matrix.get("rows", [])
    ]


def _candidate_ids_from_summary(summary):
    return [
        row["candidate_external_id"]
        for row in summary.get("rows", [])
    ]


def _validate_scope(matrix, summary, stats):
    if matrix.get("schema") != hla_matrix.MATRIX_SCHEMA:
        raise ReportingError("STEP 27 изисква STEP 24 matrix payload.")

    if summary.get("schema") != mismatch_summary.SUMMARY_SCHEMA:
        raise ReportingError("STEP 27 изисква STEP 25 summary payload.")

    if stats.get("schema") != comparison_statistics.STATISTICS_SCHEMA:
        raise ReportingError("STEP 27 изисква STEP 26 statistics payload.")

    for key in _SCOPE_KEYS:
        matrix_value = matrix.get(key)
        summary_value = summary.get(key)
        stats_value = stats.get(key)

        if key == "loci":
            matrix_value = list(matrix_value or [])
            summary_value = list(summary_value or [])
            stats_value = list(stats_value or [])

        if not (
            matrix_value == summary_value == stats_value
        ):
            raise ReportingError(
                "STEP 27 scope mismatch за "
                f"{key}: matrix={matrix_value!r}, "
                f"summary={summary_value!r}, "
                f"stats={stats_value!r}."
            )

    matrix_candidates = _candidate_ids_from_matrix(matrix)
    summary_candidates = _candidate_ids_from_summary(summary)

    if matrix_candidates != summary_candidates:
        raise ReportingError(
            "STEP 27 candidate order/scope mismatch между "
            "STEP 24 matrix и STEP 25 summary."
        )

    if stats.get("details_included"):
        stats_candidates = [
            row["candidate_external_id"]
            for row in stats.get("details", [])
        ]
        if stats_candidates != matrix_candidates:
            raise ReportingError(
                "STEP 27 candidate order/scope mismatch между "
                "STEP 24 matrix и STEP 26 details."
            )


def _validate_pair_aggregates(matrix, summary, stats):
    matrix_rows = matrix.get("rows", [])
    summary_rows = summary.get("rows", [])

    if len(matrix_rows) != len(summary_rows):
        raise ReportingError(
            "STEP 27 pair-count mismatch между matrix и summary."
        )

    for matrix_row, summary_row in zip(matrix_rows, summary_rows):
        if (
            matrix_row["candidate_external_id"]
            != summary_row["candidate_external_id"]
        ):
            raise ReportingError(
                "STEP 27 candidate mismatch при pair validation."
            )

        for field in comparison_statistics.COUNT_FIELDS:
            matrix_value = matrix_row["totals"][field]
            summary_value = summary_row["totals"][field]
            if matrix_value != summary_value:
                raise ReportingError(
                    "STEP 27 pair aggregate mismatch за "
                    f"{matrix_row['candidate_external_id']} / {field}."
                )

    for field in comparison_statistics.COUNT_FIELDS:
        values = [
            row["totals"][field]
            for row in summary_rows
        ]
        expected = comparison_statistics.calculate_numeric_statistics(
            values
        )
        actual = stats["pair_total_statistics"][field]
        if expected != actual:
            raise ReportingError(
                "STEP 27 statistics consistency error за "
                f"pair total {field}."
            )


def _validate_classification_aggregates(summary, stats):
    pair_distribution = (
        comparison_statistics.calculate_class_distribution(
            row["totals"]["classification"]
            for row in summary.get("rows", [])
        )
    )
    if pair_distribution != stats[
        "pair_classification_distribution"
    ]:
        raise ReportingError(
            "STEP 27 pair classification distribution mismatch."
        )

    all_locus_labels = [
        row["loci"][locus]["classification"]
        for row in summary.get("rows", [])
        for locus in summary.get("loci", [])
    ]
    locus_distribution = (
        comparison_statistics.calculate_class_distribution(
            all_locus_labels
        )
    )

    if locus_distribution != stats[
        "locus_classification_distribution"
    ]:
        raise ReportingError(
            "STEP 27 locus classification distribution mismatch."
        )

    observation_count = (
        summary.get("pair_count", 0)
        * len(summary.get("loci", []))
    )
    represented = sum(
        item["count"]
        for item in locus_distribution.values()
    )
    if represented != observation_count:
        raise ReportingError(
            "STEP 27 classification observation-count mismatch."
        )


def _validate_locus_aggregates(summary, stats):
    for locus in summary.get("loci", []):
        rows = [
            row["loci"][locus]
            for row in summary.get("rows", [])
        ]
        actual = stats["locus_statistics"][locus]

        if actual["pair_count"] != len(rows):
            raise ReportingError(
                f"STEP 27 locus pair_count mismatch за {locus}."
            )

        for field in comparison_statistics.COUNT_FIELDS:
            expected = (
                comparison_statistics.calculate_numeric_statistics(
                    row[field] for row in rows
                )
            )
            if actual["counts"][field] != expected:
                raise ReportingError(
                    "STEP 27 locus statistics mismatch за "
                    f"{locus}/{field}."
                )


def validate_report_inputs(matrix, summary, stats):
    """
    Validate that STEP 24/25/26 payloads describe one identical scope
    and have internally consistent aggregate values.
    """
    if not all(
        isinstance(item, dict)
        for item in (matrix, summary, stats)
    ):
        raise ReportingError(
            "STEP 27 inputs трябва да бъдат dict payloads."
        )

    _validate_scope(matrix, summary, stats)
    _validate_pair_aggregates(matrix, summary, stats)
    _validate_classification_aggregates(summary, stats)
    _validate_locus_aggregates(summary, stats)


def _build_pair_rows(summary):
    return [
        {
            "candidate_external_id": row[
                "candidate_external_id"
            ],
            "candidate_typing_id": row[
                "candidate_typing_id"
            ],
            "donor_external_id": row[
                "donor_external_id"
            ],
            "recipient_external_id": row[
                "recipient_external_id"
            ],
            "shared_count": row["totals"]["shared_count"],
            "donor_only_count": row[
                "totals"
            ]["donor_only_count"],
            "recipient_only_count": row[
                "totals"
            ]["recipient_only_count"],
            "classification": row[
                "totals"
            ]["classification"],
        }
        for row in summary.get("rows", [])
    ]


def _build_locus_rows(stats):
    rows = []

    for locus in stats.get("loci", []):
        item = stats["locus_statistics"][locus]
        counts = item["counts"]
        dist = item["classification_distribution"]

        rows.append(
            {
                "locus": locus,
                "pair_count": item["pair_count"],
                "shared_sum": counts[
                    "shared_count"
                ]["sum"],
                "shared_mean": counts[
                    "shared_count"
                ]["mean"],
                "donor_only_sum": counts[
                    "donor_only_count"
                ]["sum"],
                "donor_only_mean": counts[
                    "donor_only_count"
                ]["mean"],
                "recipient_only_sum": counts[
                    "recipient_only_count"
                ]["sum"],
                "recipient_only_mean": counts[
                    "recipient_only_count"
                ]["mean"],
                "complete_count": dist[
                    mismatch_summary.CLASS_COMPLETE
                ]["count"],
                "partial_count": dist[
                    mismatch_summary.CLASS_PARTIAL
                ]["count"],
                "no_shared_count": dist[
                    mismatch_summary.CLASS_NONE
                ]["count"],
            }
        )

    return rows


def build_report_from_components(matrix, summary, stats):
    validate_report_inputs(matrix, summary, stats)

    return {
        "schema": REPORT_SCHEMA,
        "step": 27,
        "report_type": REPORT_TYPE,
        "clinical": False,
        "source": matrix["source"],
        "batch_id": matrix.get("batch_id"),
        "direction": matrix["direction"],
        "anchor": {
            "external_id": matrix["anchor_external_id"],
            "typing_id": matrix["anchor_typing_id"],
        },
        "hla_reference": {
            "ipd_imgt_hla_version": matrix[
                "imgthla_version"
            ],
            "level": matrix["level"],
            "level_label": matrix["level_label"],
            "loci": list(matrix["loci"]),
        },
        "pair_count": matrix["pair_count"],
        "pair_rows": _build_pair_rows(summary),
        "locus_rows": _build_locus_rows(stats),
        "pair_classification_distribution": stats[
            "pair_classification_distribution"
        ],
        "locus_classification_distribution": stats[
            "locus_classification_distribution"
        ],
        "pair_total_statistics": stats[
            "pair_total_statistics"
        ],
        "software_ordering": matrix.get(
            "software_ordering"
        ),
        "provenance": {
            "step24_matrix_schema": matrix["schema"],
            "step25_summary_schema": summary["schema"],
            "step26_statistics_schema": stats["schema"],
            "pyard_recalculated": False,
            "analysis_run_created_by_step27": False,
            "scope_validated": True,
            "aggregates_validated": True,
        },
    }


def _compose_from_matrix(matrix):
    summary = mismatch_summary.build_summary_from_matrix(
        matrix
    )
    stats = comparison_statistics.build_statistics_from_summary(
        summary,
        details=True,
    )
    return build_report_from_components(
        matrix,
        summary,
        stats,
    )


def build_live_report(
    database_path,
    direction,
    anchor_external_id,
    *,
    anchor_typing_id=None,
    candidate_external_ids=None,
    level=hla_matrix.DEFAULT_LEVEL,
    loci=None,
    sort_by=None,
    sort_order="auto",
):
    """
    Build a live report from stored typings.

    The comparison matrix is computed once. STEP 25 and STEP 26 consume
    that same matrix-derived scope, preventing mixed-scope reports.
    """
    matrix = hla_matrix.build_live_matrix(
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
    return _compose_from_matrix(matrix)


def build_persistent_report(
    database_path,
    batch_id,
    *,
    level=hla_matrix.DEFAULT_LEVEL,
    loci=None,
    sort_by=None,
    sort_order="auto",
):
    matrix = hla_matrix.build_persistent_matrix(
        database_path=database_path,
        batch_id=batch_id,
        level=level,
        loci=loci,
        sort_by=sort_by,
        sort_order=sort_order,
    )
    return _compose_from_matrix(matrix)


def _fmt(value):
    if value is None:
        return "n/a"
    if isinstance(value, float):
        return f"{value:.3f}"
    return str(value)


def render_report(report):
    lines = [
        "=" * 118,
        "STEP 27 — HLA ANALYTICAL REPORT",
        "=" * 118,
        f"Source: {report['source']}",
        (
            f"Direction: {report['direction']} | "
            f"anchor={report['anchor']['external_id']} "
            f"(typing {report['anchor']['typing_id']})"
        ),
        (
            "IPD-IMGT/HLA="
            f"{report['hla_reference']['ipd_imgt_hla_version']} | "
            f"level={report['hla_reference']['level_label']} | "
            f"pairs={report['pair_count']} | "
            "loci="
            + ",".join(report["hla_reference"]["loci"])
        ),
    ]

    if report.get("batch_id") is not None:
        lines.append(
            f"Persistent batch_id: {report['batch_id']}"
        )

    ordering = report.get("software_ordering")
    if ordering:
        lines.append(
            "Software ordering: "
            f"metric={ordering['metric']} | "
            f"order={ordering['order']} | "
            f"level={ordering['level_label']}"
        )
    else:
        lines.append("Software ordering: none")

    lines.extend(
        [
            "",
            "PAIR OVERVIEW",
            "-" * 118,
            (
                f"{'candidate':<24}"
                f"{'shared':>8}"
                f"{'donor_only':>13}"
                f"{'recipient_only':>17}  "
                "software_class"
            ),
        ]
    )

    if report["pair_rows"]:
        for row in report["pair_rows"]:
            lines.append(
                f"{row['candidate_external_id']:<24}"
                f"{row['shared_count']:>8}"
                f"{row['donor_only_count']:>13}"
                f"{row['recipient_only_count']:>17}  "
                f"{row['classification']}"
            )
    else:
        lines.append("(no represented pairs)")

    lines.extend(
        [
            "",
            "LOCUS OVERVIEW",
            "-" * 118,
            (
                f"{'locus':<8}"
                f"{'pairs':>7}"
                f"{'shared_sum':>13}"
                f"{'donor_only_sum':>17}"
                f"{'recipient_only_sum':>21}"
                f"{'complete':>11}"
                f"{'partial':>10}"
                f"{'no_shared':>11}"
            ),
        ]
    )

    for row in report["locus_rows"]:
        lines.append(
            f"{row['locus']:<8}"
            f"{row['pair_count']:>7}"
            f"{_fmt(row['shared_sum']):>13}"
            f"{_fmt(row['donor_only_sum']):>17}"
            f"{_fmt(row['recipient_only_sum']):>21}"
            f"{row['complete_count']:>11}"
            f"{row['partial_count']:>10}"
            f"{row['no_shared_count']:>11}"
        )

    lines.extend(
        [
            "",
            "LOCUS CLASSIFICATION DISTRIBUTION",
            "-" * 118,
        ]
    )

    locus_observations = (
        report["pair_count"]
        * len(report["hla_reference"]["loci"])
    )
    for label in mismatch_summary.CLASSIFICATIONS:
        item = report[
            "locus_classification_distribution"
        ][label]
        lines.append(
            f"{label:<28} "
            f"{item['count']}/{locus_observations} = "
            f"{item['percentage']:.2f}%"
        )

    lines.extend(
        [
            "",
            "DESCRIPTIVE PAIR STATISTICS",
            "-" * 118,
            (
                f"{'metric':<24}"
                f"{'count':>8}"
                f"{'sum':>10}"
                f"{'min':>10}"
                f"{'max':>10}"
                f"{'mean':>12}"
                f"{'median':>12}"
            ),
        ]
    )

    for field in comparison_statistics.COUNT_FIELDS:
        item = report["pair_total_statistics"][field]
        lines.append(
            f"{field:<24}"
            f"{item['count']:>8}"
            f"{_fmt(item['sum']):>10}"
            f"{_fmt(item['min']):>10}"
            f"{_fmt(item['max']):>10}"
            f"{_fmt(item['mean']):>12}"
            f"{_fmt(item['median']):>12}"
        )

    lines.extend(
        [
            "",
            "REPORT PROVENANCE / INTEGRITY",
            "-" * 118,
            (
                "STEP 24 matrix schema: "
                f"{report['provenance']['step24_matrix_schema']}"
            ),
            (
                "STEP 25 summary schema: "
                f"{report['provenance']['step25_summary_schema']}"
            ),
            (
                "STEP 26 statistics schema: "
                f"{report['provenance']['step26_statistics_schema']}"
            ),
            "Scope consistency validated: YES",
            "Aggregate consistency validated: YES",
            "py-ard reductions recalculated by STEP 27: NO",
            "analysis_runs created by STEP 27: NO",
            "-" * 118,
            "STEP 27 is a deterministic NON-CLINICAL analytical software report.",
            "It is NOT an organ-allocation report, clinical compatibility/risk score, virtual crossmatch, DSA assessment, eplet analysis, cPRA calculation, blood-group compatibility assessment, or transplant-suitability decision.",
            "=" * 118,
        ]
    )

    return "\n".join(lines)


def _distribution_rows(distribution, total):
    return [
        {
            "classification": label,
            "count": distribution[label]["count"],
            "total": total,
            "percentage": f"{distribution[label]['percentage']:.2f}%",
        }
        for label in mismatch_summary.CLASSIFICATIONS
    ]


def render_report_html(report):
    reference = report["hla_reference"]
    anchor = report["anchor"]
    ordering = report.get("software_ordering")
    ordering_text = "none"
    if ordering:
        ordering_text = (
            f"metric={ordering['metric']}, "
            f"order={ordering['order']}, "
            f"level={ordering['level_label']}"
        )

    pair_columns = (
        ("candidate_external_id", "Candidate"),
        ("shared_count", "Shared"),
        ("donor_only_count", "Donor only"),
        ("recipient_only_count", "Recipient only"),
        ("classification", "Software class"),
    )
    locus_columns = (
        ("locus", "Locus"),
        ("pair_count", "Pairs"),
        ("shared_sum", "Shared sum"),
        ("donor_only_sum", "Donor only sum"),
        ("recipient_only_sum", "Recipient only sum"),
        ("complete_count", "Complete"),
        ("partial_count", "Partial"),
        ("no_shared_count", "No shared"),
    )
    distribution_columns = (
        ("classification", "Classification"),
        ("count", "Count"),
        ("total", "Total"),
        ("percentage", "Percentage"),
    )
    stats_rows = [
        {
            "metric": field,
            **report["pair_total_statistics"][field],
        }
        for field in comparison_statistics.COUNT_FIELDS
    ]
    stats_columns = (
        ("metric", "Metric"),
        ("count", "Count"),
        ("sum", "Sum"),
        ("min", "Min"),
        ("max", "Max"),
        ("mean", "Mean"),
        ("median", "Median"),
    )
    locus_observations = report["pair_count"] * len(reference["loci"])

    meta_items = (
        ("Source", report["source"]),
        ("Direction", report["direction"]),
        ("Anchor", f"{anchor['external_id']} / typing {anchor['typing_id']}"),
        ("IPD-IMGT/HLA", reference["ipd_imgt_hla_version"]),
        ("Level", reference["level_label"]),
        ("Pairs", report["pair_count"]),
        ("Loci", ", ".join(reference["loci"])),
        ("Software ordering", ordering_text),
    )
    sections = (
        ("Pair Overview", html_reports.render_table(pair_columns, report["pair_rows"])),
        ("Locus Overview", html_reports.render_table(locus_columns, report["locus_rows"])),
        (
            "Locus Classification Distribution",
            html_reports.render_table(
                distribution_columns,
                _distribution_rows(
                    report["locus_classification_distribution"],
                    locus_observations,
                ),
            ),
        ),
        ("Descriptive Pair Statistics", html_reports.render_table(stats_columns, stats_rows)),
    )
    return html_reports.render_page(
        "STEP 27 HLA Analytical Report",
        meta_items,
        sections,
        (
            "STEP 27 is a deterministic NON-CLINICAL analytical software report. "
            "It does not recalculate py-ard reductions and does not create analysis_runs."
        ),
        theme="teal",
    )


def normalize_export_format(value):
    if value is None:
        return None

    if not isinstance(value, str):
        raise ReportingError(
            "report export format трябва да бъде текст."
        )

    value = value.strip().lower()
    if value not in VALID_EXPORT_FORMATS:
        raise ReportingError(
            "Невалиден report export format. "
            "Допустими: json, csv, html, both, all."
        )

    return value


def default_export_name(report):
    if report.get("batch_id") is not None:
        base = f"report_batch_{report['batch_id']}"
    else:
        base = (
            f"report_{report['direction']}_"
            f"{report['anchor']['external_id']}_typing"
            f"{report['anchor']['typing_id']}"
        )

    return (
        f"{base}_{report['hla_reference']['level']}"
    )


_CSV_COLUMNS = (
    "record_type",
    "source",
    "batch_id",
    "direction",
    "anchor_external_id",
    "anchor_typing_id",
    "level",
    "candidate_external_id",
    "candidate_typing_id",
    "locus",
    "shared_count",
    "donor_only_count",
    "recipient_only_count",
    "classification",
    "pair_count",
    "shared_mean",
    "donor_only_mean",
    "recipient_only_mean",
    "complete_count",
    "partial_count",
    "no_shared_count",
)


def iter_csv_rows(report):
    base = {
        "source": report["source"],
        "batch_id": report.get("batch_id"),
        "direction": report["direction"],
        "anchor_external_id": report[
            "anchor"
        ]["external_id"],
        "anchor_typing_id": report[
            "anchor"
        ]["typing_id"],
        "level": report["hla_reference"]["level_label"],
    }

    for row in report["pair_rows"]:
        yield {
            **base,
            "record_type": "PAIR",
            "candidate_external_id": row[
                "candidate_external_id"
            ],
            "candidate_typing_id": row[
                "candidate_typing_id"
            ],
            "shared_count": row["shared_count"],
            "donor_only_count": row[
                "donor_only_count"
            ],
            "recipient_only_count": row[
                "recipient_only_count"
            ],
            "classification": row[
                "classification"
            ],
        }

    for row in report["locus_rows"]:
        yield {
            **base,
            "record_type": "LOCUS",
            "locus": row["locus"],
            "pair_count": row["pair_count"],
            "shared_count": row["shared_sum"],
            "donor_only_count": row[
                "donor_only_sum"
            ],
            "recipient_only_count": row[
                "recipient_only_sum"
            ],
            "shared_mean": row["shared_mean"],
            "donor_only_mean": row[
                "donor_only_mean"
            ],
            "recipient_only_mean": row[
                "recipient_only_mean"
            ],
            "complete_count": row[
                "complete_count"
            ],
            "partial_count": row[
                "partial_count"
            ],
            "no_shared_count": row[
                "no_shared_count"
            ],
        }


def export_report(
    report,
    *,
    output_dir=DEFAULT_EXPORT_DIR,
    export_format="both",
    export_name=None,
    overwrite=False,
):
    export_format = normalize_export_format(export_format)
    if export_format is None:
        raise ReportingError(
            "Липсва report export format."
        )

    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    name = export_name or default_export_name(report)
    if not isinstance(name, str) or not name.strip():
        raise ReportingError(
            "report export name не може да бъде празно."
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
            path
            for path in targets.values()
            if path.exists()
        ]
        if existing:
            raise ReportingExportExistsError(
                "STEP 27 report export файл вече съществува. "
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
                    report,
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
                writer.writerows(iter_csv_rows(report))
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
                render_report_html(report),
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
        "pair_count": report["pair_count"],
        "locus_count": len(
            report["hla_reference"]["loci"]
        ),
        "level_label": report[
            "hla_reference"
        ]["level_label"],
        "source": report["source"],
        "batch_id": report.get("batch_id"),
    }


def render_export_summary(info):
    lines = [
        "=" * 96,
        "STEP 27 — ANALYTICAL REPORT EXPORT COMPLETE",
        "=" * 96,
        f"Export name: {info['export_name']}",
        f"Format: {info['format']}",
        f"Source: {info['source']}",
        f"Level: {info['level_label']}",
        f"Pairs represented: {info['pair_count']}",
        f"Loci represented: {info['locus_count']}",
        f"Output directory: {info['output_dir']}",
    ]

    if info.get("batch_id") is not None:
        lines.append(
            f"Persistent batch_id: {info['batch_id']}"
        )
    if info.get("json_path") is not None:
        lines.append(f"JSON: {info['json_path']}")
    if info.get("csv_path") is not None:
        lines.append(f"CSV: {info['csv_path']}")
    if info.get("html_path") is not None:
        lines.append(f"HTML: {info['html_path']}")

    lines.extend(
        [
            "Export preserves validated NON-CLINICAL STEP 27 report data.",
            "No py-ard reductions are recalculated and no analysis_runs are created.",
            "=" * 96,
        ]
    )
    return "\n".join(lines)
