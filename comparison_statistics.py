"""
STEP 26 — HLA Comparison Statistics / Aggregation.

Consumes STEP 25 mismatch summaries and produces deterministic descriptive
statistics for multiple donor↔recipient software comparisons.

Statistics are computed for:
  * pair totals
  * each selected HLA locus
  * STEP 25 descriptive classification distributions

Numeric summaries:
  * count
  * sum
  * min
  * max
  * mean
  * median

This module is strictly NON-CLINICAL. It does not calculate clinical
compatibility, risk, virtual crossmatch, DSA, eplet mismatch, cPRA,
allocation priority, or transplant suitability.
"""

from __future__ import annotations

import csv
import json
import statistics
from collections import Counter
from pathlib import Path

import hla_matrix
import mismatch_summary


STATISTICS_SCHEMA = "hla-comparison-statistics-v1"
DEFAULT_EXPORT_DIR = Path(__file__).with_name("exports") / "stats"
VALID_EXPORT_FORMATS = ("json", "csv", "both")

COUNT_FIELDS = (
    "shared_count",
    "donor_only_count",
    "recipient_only_count",
)


class ComparisonStatisticsError(ValueError):
    """Invalid STEP 26 statistics request."""


class ComparisonStatisticsExportError(RuntimeError):
    """STEP 26 export error."""


class ComparisonStatisticsExportExistsError(ComparisonStatisticsExportError):
    """STEP 26 target export already exists."""


def calculate_numeric_statistics(values):
    """
    Return deterministic descriptive statistics.

    Empty input:
      count=0, sum=0, min/max/mean/median=None
    """
    if values is None:
        raise ComparisonStatisticsError("values не може да бъде None.")

    values = list(values)

    for value in values:
        if isinstance(value, bool) or not isinstance(value, (int, float)):
            raise ComparisonStatisticsError(
                "Статистическите стойности трябва да бъдат числа."
            )

    if not values:
        return {
            "count": 0,
            "sum": 0,
            "min": None,
            "max": None,
            "mean": None,
            "median": None,
        }

    total = sum(values)

    return {
        "count": len(values),
        "sum": total,
        "min": min(values),
        "max": max(values),
        "mean": statistics.fmean(values),
        "median": statistics.median(values),
    }


def calculate_class_distribution(labels):
    labels = list(labels)
    counter = Counter(labels)
    total = len(labels)

    result = {}

    for label in mismatch_summary.CLASSIFICATIONS:
        count = counter.get(label, 0)
        percentage = (count / total * 100.0) if total else 0.0
        result[label] = {
            "count": count,
            "percentage": percentage,
        }

    unknown = sorted(
        label
        for label in counter
        if label not in mismatch_summary.CLASSIFICATIONS
    )

    if unknown:
        raise ComparisonStatisticsError(
            "Непознати STEP 25 classification labels: "
            + ", ".join(unknown)
        )

    return result


def _metric_bundle(rows, accessor):
    return {
        field: calculate_numeric_statistics(
            accessor(row, field) for row in rows
        )
        for field in COUNT_FIELDS
    }


def build_statistics_from_summary(summary, *, details=False):
    if not isinstance(summary, dict):
        raise ComparisonStatisticsError("summary трябва да бъде dict.")

    if summary.get("schema") != mismatch_summary.SUMMARY_SCHEMA:
        raise ComparisonStatisticsError(
            "STEP 26 изисква STEP 25 mismatch summary."
        )

    rows = list(summary.get("rows", []))
    loci = list(summary.get("loci", []))

    pair_total_statistics = _metric_bundle(
        rows,
        lambda row, field: row["totals"][field],
    )

    pair_distribution = calculate_class_distribution(
        row["totals"]["classification"]
        for row in rows
    )

    locus_statistics = {}

    for locus in loci:
        locus_rows = [
            row["loci"][locus]
            for row in rows
        ]

        locus_statistics[locus] = {
            "pair_count": len(locus_rows),
            "counts": _metric_bundle(
                locus_rows,
                lambda row, field: row[field],
            ),
            "classification_distribution": calculate_class_distribution(
                row["classification"]
                for row in locus_rows
            ),
        }

    all_locus_labels = [
        row["loci"][locus]["classification"]
        for row in rows
        for locus in loci
    ]

    result = {
        "schema": STATISTICS_SCHEMA,
        "source_summary_schema": summary["schema"],
        "source": summary["source"],
        "batch_id": summary.get("batch_id"),
        "direction": summary["direction"],
        "anchor_external_id": summary["anchor_external_id"],
        "anchor_typing_id": summary["anchor_typing_id"],
        "imgthla_version": summary["imgthla_version"],
        "level": summary["level"],
        "level_label": summary["level_label"],
        "loci": loci,
        "pair_count": len(rows),
        "pair_total_statistics": pair_total_statistics,
        "pair_classification_distribution": pair_distribution,
        "locus_classification_distribution": (
            calculate_class_distribution(all_locus_labels)
        ),
        "locus_statistics": locus_statistics,
        "details_included": bool(details),
        "details": [],
        "recalculated_py_ard": False,
        "clinical_score": False,
    }

    if details:
        result["details"] = [
            {
                "candidate_external_id": row["candidate_external_id"],
                "candidate_typing_id": row["candidate_typing_id"],
                "donor_external_id": row["donor_external_id"],
                "recipient_external_id": row["recipient_external_id"],
                "shared_count": row["totals"]["shared_count"],
                "donor_only_count": row["totals"]["donor_only_count"],
                "recipient_only_count": row["totals"]["recipient_only_count"],
                "classification": row["totals"]["classification"],
            }
            for row in rows
        ]

    return result


def build_live_statistics(
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
    details=False,
):
    summary = mismatch_summary.build_live_summary(
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

    return build_statistics_from_summary(
        summary,
        details=details,
    )


def build_persistent_statistics(
    database_path,
    batch_id,
    *,
    level=hla_matrix.DEFAULT_LEVEL,
    loci=None,
    sort_by=None,
    sort_order="auto",
    details=False,
):
    summary = mismatch_summary.build_persistent_summary(
        database_path=database_path,
        batch_id=batch_id,
        level=level,
        loci=loci,
        sort_by=sort_by,
        sort_order=sort_order,
    )

    return build_statistics_from_summary(
        summary,
        details=details,
    )


def _fmt_number(value):
    if value is None:
        return "n/a"

    if isinstance(value, float):
        return f"{value:.3f}"

    return str(value)


def _distribution_lines(title, distribution, denominator):
    lines = [
        title,
        "-" * 118,
    ]

    for label in mismatch_summary.CLASSIFICATIONS:
        item = distribution[label]
        lines.append(
            f"{label:<28} "
            f"{item['count']}/{denominator} = "
            f"{item['percentage']:.2f}%"
        )

    return lines


def render_statistics(stats):
    if not isinstance(stats, dict):
        raise ComparisonStatisticsError("stats трябва да бъде dict.")

    lines = [
        "=" * 118,
        "STEP 26 — HLA COMPARISON STATISTICS",
        "=" * 118,
        f"Source: {stats['source']}",
        (
            f"Direction: {stats['direction']} | "
            f"anchor={stats['anchor_external_id']} "
            f"(typing {stats['anchor_typing_id']})"
        ),
        (
            f"IPD-IMGT/HLA={stats['imgthla_version']} | "
            f"level={stats['level_label']} | "
            f"pairs={stats['pair_count']} | "
            f"loci={','.join(stats['loci'])}"
        ),
    ]

    if stats.get("batch_id") is not None:
        lines.append(f"Persistent batch_id: {stats['batch_id']}")

    lines.append("")

    lines.extend(
        _distribution_lines(
            "PAIR CLASSIFICATION DISTRIBUTION",
            stats["pair_classification_distribution"],
            stats["pair_count"],
        )
    )

    lines.extend(
        [
            "",
            "PAIR TOTAL COUNT STATISTICS",
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

    for field in COUNT_FIELDS:
        item = stats["pair_total_statistics"][field]
        lines.append(
            f"{field:<24}"
            f"{item['count']:>8}"
            f"{_fmt_number(item['sum']):>10}"
            f"{_fmt_number(item['min']):>10}"
            f"{_fmt_number(item['max']):>10}"
            f"{_fmt_number(item['mean']):>12}"
            f"{_fmt_number(item['median']):>12}"
        )

    lines.extend(
        [
            "",
            "LOCUS STATISTICS",
            "-" * 118,
            (
                f"{'LOCUS':<8}"
                f"{'pairs':>7}"
                f"{'sh_sum':>9}"
                f"{'sh_mean':>10}"
                f"{'do_sum':>9}"
                f"{'do_mean':>10}"
                f"{'ro_sum':>9}"
                f"{'ro_mean':>10}"
                f"{'complete':>11}"
                f"{'partial':>10}"
                f"{'no_shared':>11}"
            ),
        ]
    )

    for locus in stats["loci"]:
        item = stats["locus_statistics"][locus]
        counts = item["counts"]
        dist = item["classification_distribution"]
        lines.append(
            f"{locus:<8}"
            f"{item['pair_count']:>7}"
            f"{_fmt_number(counts['shared_count']['sum']):>9}"
            f"{_fmt_number(counts['shared_count']['mean']):>10}"
            f"{_fmt_number(counts['donor_only_count']['sum']):>9}"
            f"{_fmt_number(counts['donor_only_count']['mean']):>10}"
            f"{_fmt_number(counts['recipient_only_count']['sum']):>9}"
            f"{_fmt_number(counts['recipient_only_count']['mean']):>10}"
            f"{dist[mismatch_summary.CLASS_COMPLETE]['count']:>11}"
            f"{dist[mismatch_summary.CLASS_PARTIAL]['count']:>10}"
            f"{dist[mismatch_summary.CLASS_NONE]['count']:>11}"
        )

    total_locus_observations = stats["pair_count"] * len(stats["loci"])
    lines.extend(
        [
            "",
            *_distribution_lines(
                "LOCUS CLASSIFICATION DISTRIBUTION",
                stats["locus_classification_distribution"],
                total_locus_observations,
            ),
        ]
    )

    if stats["details_included"]:
        lines.extend(
            [
                "",
                "PAIR DETAILS",
                "-" * 118,
            ]
        )

        if stats["details"]:
            for row in stats["details"]:
                lines.append(
                    f"{row['candidate_external_id']} | "
                    f"shared={row['shared_count']} | "
                    f"donor_only={row['donor_only_count']} | "
                    f"recipient_only={row['recipient_only_count']} | "
                    f"class={row['classification']}"
                )
        else:
            lines.append("(no pairs)")

    lines.extend(
        [
            "-" * 118,
            "STEP 26 statistics are descriptive NON-CLINICAL software-comparison data.",
            "They are NOT transplant compatibility probabilities, clinical risk estimates, organ-allocation scores, virtual crossmatch results, DSA assessments, or transplant-suitability decisions.",
            "STEP 26 reuses STEP 25 / STEP 24 data and does NOT recalculate py-ard reductions.",
            "=" * 118,
        ]
    )

    return "\n".join(lines)


def normalize_export_format(value):
    if value is None:
        return "both"

    if not isinstance(value, str):
        raise ComparisonStatisticsError(
            "stats export format трябва да бъде текст."
        )

    value = value.strip().lower()
    if value not in VALID_EXPORT_FORMATS:
        raise ComparisonStatisticsError(
            "Невалиден export format. Допустими: json, csv, both."
        )

    return value


def default_export_name(stats):
    if stats.get("batch_id") is not None:
        base = f"stats_batch_{stats['batch_id']}"
    else:
        base = (
            f"stats_{stats['direction']}_"
            f"{stats['anchor_external_id']}_typing"
            f"{stats['anchor_typing_id']}"
        )

    return f"{base}_{stats['level']}"


def iter_csv_rows(stats):
    # One TOTAL row plus one row per selected locus.
    pair = stats["pair_total_statistics"]
    pair_dist = stats["pair_classification_distribution"]

    yield {
        "scope": "TOTAL",
        "locus": "",
        "pair_count": stats["pair_count"],
        **_flatten_numeric_fields(pair),
        **_flatten_distribution(pair_dist),
    }

    for locus in stats["loci"]:
        item = stats["locus_statistics"][locus]
        yield {
            "scope": "LOCUS",
            "locus": locus,
            "pair_count": item["pair_count"],
            **_flatten_numeric_fields(item["counts"]),
            **_flatten_distribution(
                item["classification_distribution"]
            ),
        }


def _flatten_numeric_fields(bundle):
    out = {}

    for field in COUNT_FIELDS:
        for statistic_name in (
            "count",
            "sum",
            "min",
            "max",
            "mean",
            "median",
        ):
            out[f"{field}_{statistic_name}"] = (
                bundle[field][statistic_name]
            )

    return out


def _flatten_distribution(distribution):
    return {
        "complete_count": distribution[
            mismatch_summary.CLASS_COMPLETE
        ]["count"],
        "complete_percentage": distribution[
            mismatch_summary.CLASS_COMPLETE
        ]["percentage"],
        "partial_count": distribution[
            mismatch_summary.CLASS_PARTIAL
        ]["count"],
        "partial_percentage": distribution[
            mismatch_summary.CLASS_PARTIAL
        ]["percentage"],
        "no_shared_count": distribution[
            mismatch_summary.CLASS_NONE
        ]["count"],
        "no_shared_percentage": distribution[
            mismatch_summary.CLASS_NONE
        ]["percentage"],
    }


def _csv_columns():
    columns = [
        "scope",
        "locus",
        "pair_count",
    ]

    for field in COUNT_FIELDS:
        for statistic_name in (
            "count",
            "sum",
            "min",
            "max",
            "mean",
            "median",
        ):
            columns.append(f"{field}_{statistic_name}")

    columns.extend(
        [
            "complete_count",
            "complete_percentage",
            "partial_count",
            "partial_percentage",
            "no_shared_count",
            "no_shared_percentage",
        ]
    )

    return columns


def export_statistics(
    stats,
    *,
    output_dir=DEFAULT_EXPORT_DIR,
    export_format="both",
    export_name=None,
    overwrite=False,
):
    export_format = normalize_export_format(export_format)
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    name = export_name or default_export_name(stats)
    if not isinstance(name, str) or not name.strip():
        raise ComparisonStatisticsError(
            "stats export name не може да бъде празно."
        )
    name = name.strip()

    targets = {}
    if export_format in ("json", "both"):
        targets["json"] = output_dir / f"{name}.json"
    if export_format in ("csv", "both"):
        targets["csv"] = output_dir / f"{name}.csv"

    if not overwrite:
        existing = [
            path for path in targets.values()
            if path.exists()
        ]
        if existing:
            raise ComparisonStatisticsExportExistsError(
                "STEP 26 statistics export файл вече съществува. "
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
                    stats,
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
                    fieldnames=_csv_columns(),
                )
                writer.writeheader()
                writer.writerows(iter_csv_rows(stats))
            tmp.replace(targets["csv"])
        finally:
            if tmp.exists():
                tmp.unlink()

    return {
        "format": export_format.upper(),
        "export_name": name,
        "output_dir": output_dir,
        "json_path": targets.get("json"),
        "csv_path": targets.get("csv"),
        "pair_count": stats["pair_count"],
        "locus_count": len(stats["loci"]),
        "level_label": stats["level_label"],
        "source": stats["source"],
        "batch_id": stats.get("batch_id"),
    }


def render_export_summary(info):
    lines = [
        "=" * 96,
        "STEP 26 — COMPARISON STATISTICS EXPORT COMPLETE",
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
        lines.append(f"Persistent batch_id: {info['batch_id']}")

    if info.get("json_path") is not None:
        lines.append(f"JSON: {info['json_path']}")

    if info.get("csv_path") is not None:
        lines.append(f"CSV: {info['csv_path']}")

    lines.extend(
        [
            "Export contains descriptive NON-CLINICAL statistics only.",
            "No py-ard reductions are recalculated.",
            "=" * 96,
        ]
    )

    return "\n".join(lines)
