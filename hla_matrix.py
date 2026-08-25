"""
STEP 24 — HLA Comparison Matrix.

Creates a compact multi-pair matrix from:
  * a live one-to-many STEP 17 batch, or
  * a persisted STEP 20 batch loaded entirely from SQLite.

Each matrix cell is:
    shared_count / donor_only_count / recipient_only_count

The matrix operates on ONE representation level at a time:
    CANONICAL / LGX / G / P

Optional locus filtering is supported.

Optional deterministic software ordering reuses STEP 18 semantics:
    donor-only      -> ascending by default
    shared          -> descending by default
    recipient-only  -> ascending by default

This module does NOT calculate a clinical compatibility score, virtual
crossmatch, DSA, eplet mismatch, cPRA, allocation priority, or transplant
eligibility.
"""

from __future__ import annotations

import csv
import json
from pathlib import Path

import batch_analysis
import batch_history
import batch_ranking
from config import HLA_LOCI


MATRIX_SCHEMA = "hla-comparison-matrix-v1"
MATRIX_LEVELS = ("canonical", "lgx", "G", "P")
LEVEL_LABELS = {
    "canonical": "CANONICAL",
    "lgx": "LGX",
    "G": "G",
    "P": "P",
}
DEFAULT_LEVEL = "lgx"

VALID_EXPORT_FORMATS = ("json", "csv", "both")
DEFAULT_EXPORT_DIR = Path(__file__).with_name("exports") / "matrix"

CSV_BASE_COLUMNS = (
    "source",
    "batch_id",
    "direction",
    "anchor_external_id",
    "anchor_typing_id",
    "candidate_external_id",
    "candidate_typing_id",
    "donor_external_id",
    "donor_typing_id",
    "recipient_external_id",
    "recipient_typing_id",
    "imgthla_version",
    "level",
    "total_shared_count",
    "total_donor_only_count",
    "total_recipient_only_count",
    "software_position",
    "software_rank",
    "software_sort_metric",
    "software_sort_order",
)


class MatrixError(ValueError):
    """Invalid STEP 24 matrix request."""


class MatrixExportError(RuntimeError):
    """STEP 24 export error."""


class MatrixExportExistsError(MatrixExportError):
    """Target matrix export already exists."""


def normalize_level(value):
    if value is None:
        return DEFAULT_LEVEL

    if not isinstance(value, str):
        raise MatrixError("matrix level трябва да бъде текст.")

    mapping = {
        "canonical": "canonical",
        "lgx": "lgx",
        "g": "G",
        "p": "P",
    }
    key = value.strip().lower()

    if key not in mapping:
        raise MatrixError(
            "Невалидно matrix level. Допустими: canonical, lgx, G, P."
        )

    return mapping[key]


def normalize_loci(values):
    if values is None:
        return list(HLA_LOCI)

    if not isinstance(values, (list, tuple)):
        values = [values]

    result = []
    seen = set()

    for value in values:
        if not isinstance(value, str) or not value.strip():
            raise MatrixError("matrix locus трябва да бъде непразен текст.")

        locus = value.strip().upper()

        if locus not in HLA_LOCI:
            raise MatrixError(
                "Невалиден HLA locus. Допустими: "
                + ", ".join(HLA_LOCI)
                + "."
            )

        if locus not in seen:
            seen.add(locus)
            result.append(locus)

    if not result:
        raise MatrixError("Трябва да има поне един HLA locus.")

    # Canonical HLA order, independent of CLI argument order.
    return [locus for locus in HLA_LOCI if locus in seen]


def normalize_export_format(value):
    if value is None:
        return "both"

    if not isinstance(value, str):
        raise MatrixError("matrix export format трябва да бъде текст.")

    value = value.strip().lower()

    if value not in VALID_EXPORT_FORMATS:
        raise MatrixError(
            "Невалиден export format. Допустими: json, csv, both."
        )

    return value


def _validate_count(value, name):
    if isinstance(value, bool) or not isinstance(value, int) or value < 0:
        raise MatrixError(f"{name} трябва да бъде integer >= 0.")
    return value


def _cell_from_batch_row(row, level, locus):
    try:
        source = row["results"][level][locus]
    except (KeyError, TypeError) as exc:
        raise MatrixError(
            f"Липсва comparison result за {LEVEL_LABELS[level]}/{locus}."
        ) from exc

    return {
        "shared_count": _validate_count(
            source["shared_count"], "shared_count"
        ),
        "donor_only_count": _validate_count(
            source["mismatch_count"], "donor_only_count"
        ),
        "recipient_only_count": _validate_count(
            source["recipient_only_count"], "recipient_only_count"
        ),
    }


def _build_row(row, level, loci):
    cells = {}
    total_shared = 0
    total_donor_only = 0
    total_recipient_only = 0

    for locus in loci:
        cell = _cell_from_batch_row(row, level, locus)
        cells[locus] = cell
        total_shared += cell["shared_count"]
        total_donor_only += cell["donor_only_count"]
        total_recipient_only += cell["recipient_only_count"]

    result = {
        "candidate_external_id": row["candidate_external_id"],
        "candidate_typing_id": row["candidate_typing_id"],
        "donor_external_id": row["donor_external_id"],
        "donor_typing_id": row["donor_typing_id"],
        "recipient_external_id": row["recipient_external_id"],
        "recipient_typing_id": row["recipient_typing_id"],
        "imgthla_version": row["imgthla_version"],
        "run_id": row.get("run_id"),
        "cells": cells,
        "totals": {
            "shared_count": total_shared,
            "donor_only_count": total_donor_only,
            "recipient_only_count": total_recipient_only,
        },
    }

    if "software_order" in row:
        result["software_order"] = dict(row["software_order"])

    return result


def build_matrix_from_batch(
    batch,
    *,
    level=DEFAULT_LEVEL,
    loci=None,
    source="LIVE-STORED-TYPINGS",
):
    if not isinstance(batch, dict):
        raise MatrixError("batch трябва да бъде dict.")

    rows = batch.get("rows")
    if not isinstance(rows, list):
        raise MatrixError("batch['rows'] трябва да бъде list.")

    level = normalize_level(level)
    loci = normalize_loci(loci)

    matrix_rows = [
        _build_row(row, level, loci)
        for row in rows
    ]

    matrix = {
        "schema": MATRIX_SCHEMA,
        "source": source,
        "batch_id": batch.get("batch_id"),
        "direction": batch["direction"],
        "anchor_role": batch["anchor_role"],
        "candidate_role": batch["candidate_role"],
        "anchor_external_id": batch["anchor_external_id"],
        "anchor_typing_id": batch["anchor_typing_id"],
        "imgthla_version": batch["imgthla_version"],
        "level": level,
        "level_label": LEVEL_LABELS[level],
        "loci": loci,
        "pair_count": len(matrix_rows),
        "skipped_count": batch.get("skipped_count", 0),
        "rows": matrix_rows,
        "software_ordering": batch.get("software_ordering"),
        "recalculated_py_ard": False,
        "clinical_score": False,
    }

    return matrix


def build_live_matrix(
    database_path,
    direction,
    anchor_external_id,
    *,
    anchor_typing_id=None,
    candidate_external_ids=None,
    level=DEFAULT_LEVEL,
    loci=None,
    sort_by=None,
    sort_order="auto",
):
    level = normalize_level(level)

    batch = batch_analysis.run_batch_analysis(
        database_path=database_path,
        direction=direction,
        anchor_external_id=anchor_external_id,
        anchor_typing_id=anchor_typing_id,
        candidate_external_ids=candidate_external_ids,
        save=False,
    )

    if sort_by is not None:
        batch = batch_ranking.apply_batch_ordering(
            batch,
            level=level,
            metric=sort_by,
            order=sort_order,
            display_limit=None,
        )
    elif sort_order != "auto":
        raise MatrixError("--sort-order изисква --sort-by.")

    return build_matrix_from_batch(
        batch,
        level=level,
        loci=loci,
        source="LIVE-STORED-TYPINGS",
    )


def build_persistent_matrix(
    database_path,
    batch_id,
    *,
    level=DEFAULT_LEVEL,
    loci=None,
    sort_by=None,
    sort_order="auto",
):
    level = normalize_level(level)

    batch = batch_history.load_batch_results(
        database_path,
        batch_id,
    )

    if sort_by is not None:
        batch = batch_ranking.apply_batch_ordering(
            batch,
            level=level,
            metric=sort_by,
            order=sort_order,
            display_limit=None,
        )
    elif sort_order != "auto":
        raise MatrixError("--sort-order изисква --sort-by.")

    matrix = build_matrix_from_batch(
        batch,
        level=level,
        loci=loci,
        source="PERSISTENT-BATCH",
    )
    matrix["batch_id"] = int(batch_id)

    return matrix


def _cell_text(cell):
    return (
        f"{cell['shared_count']}/"
        f"{cell['donor_only_count']}/"
        f"{cell['recipient_only_count']}"
    )


def render_matrix(matrix):
    if not isinstance(matrix, dict):
        raise MatrixError("matrix трябва да бъде dict.")

    lines = [
        "=" * 118,
        "STEP 24 — HLA COMPARISON MATRIX",
        "=" * 118,
        f"Source: {matrix['source']}",
        (
            f"Direction: {matrix['direction']} | "
            f"anchor={matrix['anchor_external_id']} "
            f"(typing {matrix['anchor_typing_id']})"
        ),
        (
            f"IPD-IMGT/HLA={matrix['imgthla_version']} | "
            f"level={matrix['level_label']} | "
            f"pairs={matrix['pair_count']} | "
            f"loci={','.join(matrix['loci'])}"
        ),
    ]

    if matrix.get("batch_id") is not None:
        lines.append(f"Persistent batch_id: {matrix['batch_id']}")

    ordering = matrix.get("software_ordering")
    if ordering:
        lines.append(
            "Software ordering: "
            f"metric={ordering['metric']} | "
            f"order={ordering['order']} | "
            f"level={ordering['level_label']}"
        )
    else:
        lines.append("Software ordering: none")

    lines.append(
        "Cell format: shared_count/donor_only_count/recipient_only_count"
    )
    lines.append("-" * 118)

    header = ["candidate"] + list(matrix["loci"]) + [
        "TOTAL shared/donor_only/recipient_only"
    ]
    widths = [max(18, len(header[0]))]
    widths += [max(9, len(locus) + 4) for locus in matrix["loci"]]
    widths += [38]

    def format_line(values):
        return " | ".join(
            str(value).ljust(width)
            for value, width in zip(values, widths)
        )

    lines.append(format_line(header))
    lines.append("-" * 118)

    for row in matrix["rows"]:
        values = [row["candidate_external_id"]]
        values.extend(
            _cell_text(row["cells"][locus])
            for locus in matrix["loci"]
        )
        t = row["totals"]
        values.append(
            f"{t['shared_count']}/"
            f"{t['donor_only_count']}/"
            f"{t['recipient_only_count']}"
        )
        lines.append(format_line(values))

    lines.extend(
        [
            "-" * 118,
            "STEP 24 matrix is deterministic NON-CLINICAL software-comparison data.",
            "It is NOT an organ-allocation score, virtual crossmatch, DSA, eplet, cPRA, "
            "blood-group compatibility, or transplant-suitability decision.",
            "Stored representations/results are reused; py-ard reductions were NOT recalculated.",
            "=" * 118,
        ]
    )

    return "\n".join(lines)


def default_export_name(matrix):
    if matrix.get("batch_id") is not None:
        base = f"matrix_batch_{matrix['batch_id']}"
    else:
        base = (
            f"matrix_{matrix['direction']}_"
            f"{matrix['anchor_external_id']}_typing"
            f"{matrix['anchor_typing_id']}"
        )

    return f"{base}_{matrix['level']}"


def _csv_columns(matrix):
    columns = list(CSV_BASE_COLUMNS)

    for locus in matrix["loci"]:
        columns.extend(
            [
                f"{locus}_shared_count",
                f"{locus}_donor_only_count",
                f"{locus}_recipient_only_count",
            ]
        )

    return columns


def iter_csv_rows(matrix):
    ordering = matrix.get("software_ordering")

    for row in matrix["rows"]:
        software = row.get("software_order", {})
        out = {
            "source": matrix["source"],
            "batch_id": matrix.get("batch_id"),
            "direction": matrix["direction"],
            "anchor_external_id": matrix["anchor_external_id"],
            "anchor_typing_id": matrix["anchor_typing_id"],
            "candidate_external_id": row["candidate_external_id"],
            "candidate_typing_id": row["candidate_typing_id"],
            "donor_external_id": row["donor_external_id"],
            "donor_typing_id": row["donor_typing_id"],
            "recipient_external_id": row["recipient_external_id"],
            "recipient_typing_id": row["recipient_typing_id"],
            "imgthla_version": row["imgthla_version"],
            "level": matrix["level_label"],
            "total_shared_count": row["totals"]["shared_count"],
            "total_donor_only_count": row["totals"]["donor_only_count"],
            "total_recipient_only_count": row["totals"]["recipient_only_count"],
            "software_position": software.get("position"),
            "software_rank": software.get("rank"),
            "software_sort_metric": (
                ordering.get("metric") if ordering else None
            ),
            "software_sort_order": (
                ordering.get("order") if ordering else None
            ),
        }

        for locus in matrix["loci"]:
            cell = row["cells"][locus]
            out[f"{locus}_shared_count"] = cell["shared_count"]
            out[f"{locus}_donor_only_count"] = cell["donor_only_count"]
            out[f"{locus}_recipient_only_count"] = cell[
                "recipient_only_count"
            ]

        yield out


def export_matrix(
    matrix,
    *,
    output_dir=DEFAULT_EXPORT_DIR,
    export_format="both",
    export_name=None,
    overwrite=False,
):
    export_format = normalize_export_format(export_format)
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    name = export_name or default_export_name(matrix)
    if not isinstance(name, str) or not name.strip():
        raise MatrixError("matrix export name не може да бъде празно.")
    name = name.strip()

    targets = {}

    if export_format in ("json", "both"):
        targets["json"] = output_dir / f"{name}.json"

    if export_format in ("csv", "both"):
        targets["csv"] = output_dir / f"{name}.csv"

    if not overwrite:
        existing = [path for path in targets.values() if path.exists()]
        if existing:
            raise MatrixExportExistsError(
                "STEP 24 matrix export файл вече съществува. "
                "Използвайте --overwrite: "
                + ", ".join(str(path) for path in existing)
            )

    if "json" in targets:
        tmp = targets["json"].with_name(targets["json"].name + ".tmp")
        try:
            tmp.write_text(
                json.dumps(matrix, ensure_ascii=False, indent=2) + "\n",
                encoding="utf-8",
            )
            tmp.replace(targets["json"])
        finally:
            if tmp.exists():
                tmp.unlink()

    if "csv" in targets:
        tmp = targets["csv"].with_name(targets["csv"].name + ".tmp")
        try:
            with tmp.open("w", encoding="utf-8", newline="") as handle:
                writer = csv.DictWriter(
                    handle,
                    fieldnames=_csv_columns(matrix),
                )
                writer.writeheader()
                writer.writerows(iter_csv_rows(matrix))
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
        "pair_count": matrix["pair_count"],
        "locus_count": len(matrix["loci"]),
        "level_label": matrix["level_label"],
        "source": matrix["source"],
        "batch_id": matrix.get("batch_id"),
    }


def render_export_summary(info):
    lines = [
        "=" * 96,
        "STEP 24 — HLA MATRIX EXPORT COMPLETE",
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
            "Export does not recalculate py-ard reductions and does not create analysis_runs.",
            "=" * 96,
        ]
    )

    return "\n".join(lines)
