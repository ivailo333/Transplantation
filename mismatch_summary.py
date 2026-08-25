"""STEP 25 — HLA Mismatch Summary / Classification Layer.

Consumes STEP 24 matrix data and produces deterministic, NON-CLINICAL
software summaries. No py-ard recalculation is performed here.
"""
from __future__ import annotations

import csv
import json
from collections import Counter
from pathlib import Path

import hla_matrix

SUMMARY_SCHEMA = "hla-mismatch-summary-v1"
DEFAULT_EXPORT_DIR = Path(__file__).with_name("exports") / "summary"
VALID_EXPORT_FORMATS = ("json", "csv", "both")

CLASS_COMPLETE = "COMPLETE-SOFTWARE-MATCH"
CLASS_PARTIAL = "PARTIAL-SOFTWARE-MATCH"
CLASS_NONE = "NO-SOFTWARE-SHARED"
CLASSIFICATIONS = (CLASS_COMPLETE, CLASS_PARTIAL, CLASS_NONE)


class MismatchSummaryError(ValueError):
    pass


class MismatchSummaryExportError(RuntimeError):
    pass


class MismatchSummaryExportExistsError(MismatchSummaryExportError):
    pass


def classify_counts(shared_count, donor_only_count, recipient_only_count):
    for value, name in (
        (shared_count, "shared_count"),
        (donor_only_count, "donor_only_count"),
        (recipient_only_count, "recipient_only_count"),
    ):
        if isinstance(value, bool) or not isinstance(value, int) or value < 0:
            raise MismatchSummaryError(f"{name} трябва да бъде integer >= 0.")
    if donor_only_count == 0 and recipient_only_count == 0:
        return CLASS_COMPLETE
    if shared_count > 0:
        return CLASS_PARTIAL
    return CLASS_NONE


def _summarize_locus(cell):
    s = int(cell["shared_count"])
    d = int(cell["donor_only_count"])
    r = int(cell["recipient_only_count"])
    return {
        "shared_count": s,
        "donor_only_count": d,
        "recipient_only_count": r,
        "classification": classify_counts(s, d, r),
    }


def _summarize_row(row, loci):
    locus_summaries = {locus: _summarize_locus(row["cells"][locus]) for locus in loci}
    totals = {
        "shared_count": int(row["totals"]["shared_count"]),
        "donor_only_count": int(row["totals"]["donor_only_count"]),
        "recipient_only_count": int(row["totals"]["recipient_only_count"]),
    }
    totals["classification"] = classify_counts(
        totals["shared_count"], totals["donor_only_count"], totals["recipient_only_count"]
    )
    counts = Counter(item["classification"] for item in locus_summaries.values())
    return {
        "candidate_external_id": row["candidate_external_id"],
        "candidate_typing_id": row["candidate_typing_id"],
        "donor_external_id": row["donor_external_id"],
        "donor_typing_id": row["donor_typing_id"],
        "recipient_external_id": row["recipient_external_id"],
        "recipient_typing_id": row["recipient_typing_id"],
        "run_id": row.get("run_id"),
        "loci": locus_summaries,
        "totals": totals,
        "locus_classification_counts": {label: counts.get(label, 0) for label in CLASSIFICATIONS},
    }


def build_summary_from_matrix(matrix):
    if not isinstance(matrix, dict) or matrix.get("schema") != hla_matrix.MATRIX_SCHEMA:
        raise MismatchSummaryError("STEP 25 изисква STEP 24 HLA comparison matrix.")
    loci = list(matrix["loci"])
    rows = [_summarize_row(row, loci) for row in matrix["rows"]]
    pair_counts = Counter(row["totals"]["classification"] for row in rows)
    locus_counts = Counter()
    for row in rows:
        for locus in loci:
            locus_counts[row["loci"][locus]["classification"]] += 1
    return {
        "schema": SUMMARY_SCHEMA,
        "source_matrix_schema": matrix["schema"],
        "source": matrix["source"],
        "batch_id": matrix.get("batch_id"),
        "direction": matrix["direction"],
        "anchor_external_id": matrix["anchor_external_id"],
        "anchor_typing_id": matrix["anchor_typing_id"],
        "imgthla_version": matrix["imgthla_version"],
        "level": matrix["level"],
        "level_label": matrix["level_label"],
        "loci": loci,
        "pair_count": len(rows),
        "rows": rows,
        "pair_classification_counts": {label: pair_counts.get(label, 0) for label in CLASSIFICATIONS},
        "locus_classification_counts": {label: locus_counts.get(label, 0) for label in CLASSIFICATIONS},
        "recalculated_py_ard": False,
        "clinical_score": False,
    }


def build_live_summary(database_path, direction, anchor_external_id, *, anchor_typing_id=None,
                       candidate_external_ids=None, level=hla_matrix.DEFAULT_LEVEL, loci=None,
                       sort_by=None, sort_order="auto"):
    matrix = hla_matrix.build_live_matrix(
        database_path=database_path, direction=direction, anchor_external_id=anchor_external_id,
        anchor_typing_id=anchor_typing_id, candidate_external_ids=candidate_external_ids,
        level=level, loci=loci, sort_by=sort_by, sort_order=sort_order,
    )
    return build_summary_from_matrix(matrix)


def build_persistent_summary(database_path, batch_id, *, level=hla_matrix.DEFAULT_LEVEL,
                             loci=None, sort_by=None, sort_order="auto"):
    matrix = hla_matrix.build_persistent_matrix(
        database_path=database_path, batch_id=batch_id, level=level, loci=loci,
        sort_by=sort_by, sort_order=sort_order,
    )
    return build_summary_from_matrix(matrix)


def render_summary(summary):
    lines = [
        "=" * 118,
        "STEP 25 — HLA MISMATCH SUMMARY / CLASSIFICATION",
        "=" * 118,
        f"Source: {summary['source']}",
        f"Direction: {summary['direction']} | anchor={summary['anchor_external_id']} (typing {summary['anchor_typing_id']})",
        f"IPD-IMGT/HLA={summary['imgthla_version']} | level={summary['level_label']} | pairs={summary['pair_count']} | loci={','.join(summary['loci'])}",
    ]
    if summary.get("batch_id") is not None:
        lines.append(f"Persistent batch_id: {summary['batch_id']}")
    lines.append("-" * 118)
    for row in summary["rows"]:
        total = row["totals"]
        lines.append(
            f"{row['candidate_external_id']} | TOTAL shared={total['shared_count']} | donor_only={total['donor_only_count']} | "
            f"recipient_only={total['recipient_only_count']} | class={total['classification']}"
        )
        parts = []
        for locus in summary["loci"]:
            item = row["loci"][locus]
            parts.append(
                f"{locus}:{item['shared_count']}/{item['donor_only_count']}/{item['recipient_only_count']}={item['classification']}"
            )
        lines.append("  " + " | ".join(parts))
    lines.append("-" * 118)
    pc = summary["pair_classification_counts"]
    lc = summary["locus_classification_counts"]
    lines.append("Pair classes: " + " | ".join(f"{label}={pc[label]}" for label in CLASSIFICATIONS))
    lines.append("Locus classes: " + " | ".join(f"{label}={lc[label]}" for label in CLASSIFICATIONS))
    lines += [
        "-" * 118,
        "STEP 25 classifications are descriptive NON-CLINICAL software labels only.",
        "They are NOT histocompatibility risk categories, allocation priority, virtual crossmatch, DSA, eplet, cPRA, or transplant-suitability decisions.",
        "STEP 25 reuses STEP 24 counts and does NOT recalculate py-ard reductions.",
        "=" * 118,
    ]
    return "\n".join(lines)


def normalize_export_format(value):
    if value is None:
        return "both"
    if not isinstance(value, str):
        raise MismatchSummaryError("summary export format трябва да бъде текст.")
    value = value.strip().lower()
    if value not in VALID_EXPORT_FORMATS:
        raise MismatchSummaryError("Невалиден export format. Допустими: json, csv, both.")
    return value


def default_export_name(summary):
    if summary.get("batch_id") is not None:
        base = f"summary_batch_{summary['batch_id']}"
    else:
        base = f"summary_{summary['direction']}_{summary['anchor_external_id']}_typing{summary['anchor_typing_id']}"
    return f"{base}_{summary['level']}"


def _csv_columns(summary):
    columns = [
        "source", "batch_id", "direction", "anchor_external_id", "anchor_typing_id",
        "candidate_external_id", "candidate_typing_id", "donor_external_id", "donor_typing_id",
        "recipient_external_id", "recipient_typing_id", "imgthla_version", "level",
        "total_shared_count", "total_donor_only_count", "total_recipient_only_count", "total_classification",
    ]
    for locus in summary["loci"]:
        columns.extend([
            f"{locus}_shared_count", f"{locus}_donor_only_count",
            f"{locus}_recipient_only_count", f"{locus}_classification",
        ])
    return columns


def iter_csv_rows(summary):
    for row in summary["rows"]:
        out = {
            "source": summary["source"], "batch_id": summary.get("batch_id"), "direction": summary["direction"],
            "anchor_external_id": summary["anchor_external_id"], "anchor_typing_id": summary["anchor_typing_id"],
            "candidate_external_id": row["candidate_external_id"], "candidate_typing_id": row["candidate_typing_id"],
            "donor_external_id": row["donor_external_id"], "donor_typing_id": row["donor_typing_id"],
            "recipient_external_id": row["recipient_external_id"], "recipient_typing_id": row["recipient_typing_id"],
            "imgthla_version": summary["imgthla_version"], "level": summary["level_label"],
            "total_shared_count": row["totals"]["shared_count"],
            "total_donor_only_count": row["totals"]["donor_only_count"],
            "total_recipient_only_count": row["totals"]["recipient_only_count"],
            "total_classification": row["totals"]["classification"],
        }
        for locus in summary["loci"]:
            item = row["loci"][locus]
            out[f"{locus}_shared_count"] = item["shared_count"]
            out[f"{locus}_donor_only_count"] = item["donor_only_count"]
            out[f"{locus}_recipient_only_count"] = item["recipient_only_count"]
            out[f"{locus}_classification"] = item["classification"]
        yield out


def export_summary(summary, *, output_dir=DEFAULT_EXPORT_DIR, export_format="both",
                   export_name=None, overwrite=False):
    export_format = normalize_export_format(export_format)
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    name = export_name or default_export_name(summary)
    if not isinstance(name, str) or not name.strip():
        raise MismatchSummaryError("summary export name не може да бъде празно.")
    name = name.strip()
    targets = {}
    if export_format in ("json", "both"):
        targets["json"] = output_dir / f"{name}.json"
    if export_format in ("csv", "both"):
        targets["csv"] = output_dir / f"{name}.csv"
    if not overwrite:
        existing = [path for path in targets.values() if path.exists()]
        if existing:
            raise MismatchSummaryExportExistsError(
                "STEP 25 summary export файл вече съществува. Използвайте --overwrite: "
                + ", ".join(str(path) for path in existing)
            )
    if "json" in targets:
        tmp = targets["json"].with_name(targets["json"].name + ".tmp")
        try:
            tmp.write_text(json.dumps(summary, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
            tmp.replace(targets["json"])
        finally:
            if tmp.exists():
                tmp.unlink()
    if "csv" in targets:
        tmp = targets["csv"].with_name(targets["csv"].name + ".tmp")
        try:
            with tmp.open("w", encoding="utf-8", newline="") as handle:
                writer = csv.DictWriter(handle, fieldnames=_csv_columns(summary))
                writer.writeheader()
                writer.writerows(iter_csv_rows(summary))
            tmp.replace(targets["csv"])
        finally:
            if tmp.exists():
                tmp.unlink()
    return {
        "format": export_format.upper(), "export_name": name, "output_dir": output_dir,
        "json_path": targets.get("json"), "csv_path": targets.get("csv"),
        "pair_count": summary["pair_count"], "locus_count": len(summary["loci"]),
        "level_label": summary["level_label"], "source": summary["source"],
        "batch_id": summary.get("batch_id"),
    }


def render_export_summary(info):
    lines = [
        "=" * 96, "STEP 25 — MISMATCH SUMMARY EXPORT COMPLETE", "=" * 96,
        f"Export name: {info['export_name']}", f"Format: {info['format']}",
        f"Source: {info['source']}", f"Level: {info['level_label']}",
        f"Pairs represented: {info['pair_count']}", f"Loci represented: {info['locus_count']}",
        f"Output directory: {info['output_dir']}",
    ]
    if info.get("batch_id") is not None:
        lines.append(f"Persistent batch_id: {info['batch_id']}")
    if info.get("json_path") is not None:
        lines.append(f"JSON: {info['json_path']}")
    if info.get("csv_path") is not None:
        lines.append(f"CSV: {info['csv_path']}")
    lines += [
        "Export preserves NON-CLINICAL STEP 25 descriptive classifications.",
        "No py-ard reductions are recalculated.", "=" * 96,
    ]
    return "\n".join(lines)
