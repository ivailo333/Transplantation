"""
STEP 19 — JSON / CSV export for STEP 17/18 batch results.

Exports can be created from:
    * ordinary STEP 17 batch output;
    * STEP 18 software-ordered batch output;
    * NO SAVE batches;
    * SAVE batches.

Important semantics:
    * --limit / --display-limit remains DISPLAY ONLY.
    * STEP 19 exports ALL computed eligible pairs.
    * When software ordering is enabled, the export contains ALL pairs
      in the full software-ordered sequence, even if the CLI displays
      only the first N rows.
    * Exporting does not recalculate py-ard reductions.
    * Exporting does not create analysis_runs by itself.

CSV format:
    one row per pair × representation × locus
    = 24 rows per pair.

This is a software-comparison export, not a clinical compatibility report.
"""

from __future__ import annotations

import csv
import json
import re
from pathlib import Path

from config import HLA_LOCI


DEFAULT_BATCH_EXPORT_DIR = (
    Path(__file__).with_name("exports") / "batch"
)

VALID_BATCH_EXPORT_FORMATS = (
    "json",
    "csv",
    "both",
)

LEVELS = (
    ("canonical", "CANONICAL"),
    ("lgx", "LGX"),
    ("G", "G"),
    ("P", "P"),
)

BATCH_CSV_COLUMNS = (
    "batch_id",
    "batch_created_at",
    "direction",
    "anchor_role",
    "anchor_external_id",
    "anchor_typing_id",
    "candidate_role",
    "candidate_external_id",
    "candidate_typing_id",
    "donor_external_id",
    "donor_typing_id",
    "recipient_external_id",
    "recipient_typing_id",
    "imgthla_version",
    "run_id",
    "software_position",
    "software_rank",
    "sort_level",
    "sort_metric",
    "sort_order",
    "criterion_value",
    "level",
    "locus",
    "shared_count",
    "donor_only_count",
    "recipient_only_count",
    "shared_values_json",
    "donor_only_values_json",
    "recipient_only_values_json",
)


class BatchExportError(RuntimeError):
    """Обща грешка при STEP 19 batch export."""


class BatchExportFileExistsError(BatchExportError):
    """Target export file already exists and overwrite=False."""


class BatchExportStructureError(BatchExportError):
    """Batch data is incomplete or malformed for export."""


def normalize_batch_export_format(value):
    if value is None:
        return "both"

    if not isinstance(value, str):
        raise BatchExportError(
            "Batch export format трябва да бъде текст."
        )

    normalized = value.strip().lower()

    if normalized not in VALID_BATCH_EXPORT_FORMATS:
        raise BatchExportError(
            "Невалиден batch export format. "
            "Допустими: json, csv, both."
        )

    return normalized


def sanitize_export_component(value):
    """
    Make an external_id safe for a Windows/Linux filename while
    keeping it human-readable.
    """
    if not isinstance(value, str):
        value = str(value)

    value = value.strip()

    if not value:
        return "unnamed"

    value = re.sub(
        r'[<>:"/\\|?*\x00-\x1F]+',
        "_",
        value,
    )
    value = re.sub(r"\s+", "_", value)
    value = value.strip(" ._")

    return value or "unnamed"


def default_batch_export_name(batch):
    direction = batch.get("direction")
    anchor_external_id = batch.get("anchor_external_id")
    anchor_typing_id = batch.get("anchor_typing_id")

    if direction not in ("recipient", "donor"):
        raise BatchExportStructureError(
            "Batch няма валидна direction."
        )

    if not isinstance(anchor_external_id, str):
        raise BatchExportStructureError(
            "Batch няма валиден anchor_external_id."
        )

    if (
        isinstance(anchor_typing_id, bool)
        or not isinstance(anchor_typing_id, int)
        or anchor_typing_id <= 0
    ):
        raise BatchExportStructureError(
            "Batch няма валиден anchor_typing_id."
        )

    safe_id = sanitize_export_component(
        anchor_external_id
    )

    base = (
        f"batch_{direction}_{safe_id}"
        f"_typing{anchor_typing_id}"
    )

    ordering = batch.get("software_ordering")

    if ordering:
        level = sanitize_export_component(
            ordering["level_label"].lower()
        )
        metric = sanitize_export_component(
            ordering["metric"]
        )
        order = sanitize_export_component(
            ordering["order"]
        )

        base += (
            f"_sorted_{level}_{metric}_{order}"
        )

    return base


def normalize_export_name(value, batch):
    if value is None:
        return default_batch_export_name(batch)

    if not isinstance(value, str):
        raise BatchExportError(
            "export name трябва да бъде текст."
        )

    normalized = sanitize_export_component(value)

    if not normalized:
        raise BatchExportError(
            "export name не може да бъде празно."
        )

    return normalized


def _target_paths(
    batch,
    output_dir,
    export_format,
    export_name=None,
):
    output_dir = Path(output_dir)
    export_format = normalize_batch_export_format(
        export_format
    )
    base_name = normalize_export_name(
        export_name,
        batch,
    )

    targets = {}

    if export_format in ("json", "both"):
        targets["json"] = (
            output_dir / f"{base_name}.json"
        )

    if export_format in ("csv", "both"):
        targets["csv"] = (
            output_dir / f"{base_name}.csv"
        )

    return targets


def _ensure_targets_available(
    targets,
    overwrite,
):
    if overwrite:
        return

    existing = [
        path
        for path in targets.values()
        if path.exists()
    ]

    if existing:
        raise BatchExportFileExistsError(
            "Batch export файл вече съществува. "
            "Използвайте --overwrite: "
            + ", ".join(
                str(path)
                for path in existing
            )
        )


def _atomic_write_text(
    path,
    text,
    encoding="utf-8",
):
    path = Path(path)
    temp_path = path.with_name(
        path.name + ".tmp"
    )

    try:
        with temp_path.open(
            "w",
            encoding=encoding,
            newline="",
        ) as handle:
            handle.write(text)

        temp_path.replace(path)
    finally:
        if temp_path.exists():
            temp_path.unlink()


def _validate_pair_result_structure(row):
    if not isinstance(row, dict):
        raise BatchExportStructureError(
            "Batch pair row трябва да бъде dict."
        )

    required = (
        "donor_external_id",
        "donor_typing_id",
        "recipient_external_id",
        "recipient_typing_id",
        "imgthla_version",
        "results",
        "summary",
        "candidate_external_id",
        "candidate_typing_id",
    )

    missing = [
        field
        for field in required
        if field not in row
    ]

    if missing:
        raise BatchExportStructureError(
            "Batch pair row липсва полета: "
            + ", ".join(missing)
        )

    results = row["results"]

    if not isinstance(results, dict):
        raise BatchExportStructureError(
            "Batch pair results трябва да бъде dict."
        )

    for result_key, _ in LEVELS:
        if result_key not in results:
            raise BatchExportStructureError(
                f"Batch pair results няма {result_key!r}."
            )

        level_results = results[result_key]

        if set(level_results) != set(HLA_LOCI):
            raise BatchExportStructureError(
                f"{result_key}: очакват се точно "
                + ", ".join(HLA_LOCI)
            )


def validate_batch_for_export(batch):
    if not isinstance(batch, dict):
        raise BatchExportStructureError(
            "Batch export source трябва да бъде dict."
        )

    required = (
        "direction",
        "anchor_role",
        "candidate_role",
        "anchor_external_id",
        "anchor_typing_id",
        "imgthla_version",
        "pair_count",
        "rows",
        "skipped",
    )

    missing = [
        field
        for field in required
        if field not in batch
    ]

    if missing:
        raise BatchExportStructureError(
            "Batch липсва полета: "
            + ", ".join(missing)
        )

    rows = batch["rows"]

    if not isinstance(rows, list):
        raise BatchExportStructureError(
            "batch['rows'] трябва да бъде list."
        )

    if batch["pair_count"] != len(rows):
        raise BatchExportStructureError(
            "За export batch['rows'] трябва да съдържа "
            "ВСИЧКИ computed pairs. pair_count не съвпада."
        )

    for row in rows:
        _validate_pair_result_structure(row)

    return batch


def build_batch_export_payload(batch):
    """
    Creates a portable JSON structure from a full, untruncated batch.
    """
    validate_batch_for_export(batch)

    ordering = batch.get("software_ordering")

    export_ordering = None

    if ordering:
        export_ordering = {
            "enabled": True,
            "level": ordering["level"],
            "level_label": ordering["level_label"],
            "metric": ordering["metric"],
            "metric_key": ordering["metric_key"],
            "order": ordering["order"],
            "requested_order": ordering[
                "requested_order"
            ],
            "display_limit": None,
            "total_pair_count": batch["pair_count"],
            "exported_pair_count": batch["pair_count"],
            "note": (
                "STEP 19 exports the full software-ordered batch; "
                "CLI display limits are not applied to export."
            ),
        }

    pairs = []

    for row in batch["rows"]:
        pair = {
            "candidate": {
                "external_id": row[
                    "candidate_external_id"
                ],
                "typing_id": row[
                    "candidate_typing_id"
                ],
            },
            "donor": {
                "external_id": row[
                    "donor_external_id"
                ],
                "typing_id": row[
                    "donor_typing_id"
                ],
            },
            "recipient": {
                "external_id": row[
                    "recipient_external_id"
                ],
                "typing_id": row[
                    "recipient_typing_id"
                ],
            },
            "imgthla_version": row[
                "imgthla_version"
            ],
            "run_id": row.get("run_id"),
            "summary": row["summary"],
            "results": row["results"],
        }

        if "software_order" in row:
            pair["software_order"] = copy_software_order(
                row["software_order"]
            )

        pairs.append(pair)

    return {
        "schema": "hla-batch-export-v1",
        "batch": {
            "batch_id": batch.get("batch_id"),
            "batch_created_at": batch.get("batch_created_at"),
            "direction": batch["direction"],
            "anchor_role": batch["anchor_role"],
            "candidate_role": batch[
                "candidate_role"
            ],
            "anchor_external_id": batch[
                "anchor_external_id"
            ],
            "anchor_typing_id": batch[
                "anchor_typing_id"
            ],
            "imgthla_version": batch[
                "imgthla_version"
            ],
            "source_save_mode": bool(
                batch.get("save")
            ),
            "pair_count": batch["pair_count"],
            "exported_pair_count": len(pairs),
            "skipped_count": len(
                batch["skipped"]
            ),
            "skipped": batch["skipped"],
            "software_ordering": export_ordering,
        },
        "pairs": pairs,
        "interpretation": {
            "kind": (
                "copy-sensitive software-comparison export"
            ),
            "clinical_score": False,
            "warning": (
                "This export is not an organ-allocation score, "
                "virtual crossmatch, DSA assessment, eplet score, "
                "cPRA, transplant eligibility decision, or graft "
                "outcome prediction."
            ),
        },
    }


def copy_software_order(order_info):
    return {
        "position": order_info["position"],
        "rank": order_info["rank"],
        "level": order_info["level"],
        "level_label": order_info[
            "level_label"
        ],
        "metric": order_info["metric"],
        "metric_key": order_info[
            "metric_key"
        ],
        "criterion_value": order_info[
            "criterion_value"
        ],
        "order": order_info["order"],
    }


def export_batch_json(
    payload,
    path,
    overwrite=False,
):
    path = Path(path)

    if path.exists() and not overwrite:
        raise BatchExportFileExistsError(
            f"JSON batch export вече съществува: {path}"
        )

    text = json.dumps(
        payload,
        ensure_ascii=False,
        indent=2,
        sort_keys=False,
    )
    text += "\n"

    _atomic_write_text(
        path,
        text,
        encoding="utf-8",
    )

    return path


def _software_order_fields(pair):
    order_info = pair.get("software_order")

    if not order_info:
        return {
            "software_position": "",
            "software_rank": "",
            "sort_level": "",
            "sort_metric": "",
            "sort_order": "",
            "criterion_value": "",
        }

    return {
        "software_position": order_info[
            "position"
        ],
        "software_rank": order_info["rank"],
        "sort_level": order_info[
            "level_label"
        ],
        "sort_metric": order_info[
            "metric_key"
        ],
        "sort_order": order_info["order"],
        "criterion_value": order_info[
            "criterion_value"
        ],
    }


def iter_batch_csv_rows(payload):
    batch = payload["batch"]

    for pair in payload["pairs"]:
        order_fields = _software_order_fields(
            pair
        )

        for result_key, db_level in LEVELS:
            for locus in HLA_LOCI:
                result = (
                    pair["results"][result_key][locus]
                )

                yield {
                    "batch_id": (
                        "" if batch.get("batch_id") is None
                        else batch.get("batch_id")
                    ),
                    "batch_created_at": (
                        "" if batch.get("batch_created_at") is None
                        else batch.get("batch_created_at")
                    ),
                    "direction": batch[
                        "direction"
                    ],
                    "anchor_role": batch[
                        "anchor_role"
                    ],
                    "anchor_external_id": batch[
                        "anchor_external_id"
                    ],
                    "anchor_typing_id": batch[
                        "anchor_typing_id"
                    ],
                    "candidate_role": batch[
                        "candidate_role"
                    ],
                    "candidate_external_id": pair[
                        "candidate"
                    ]["external_id"],
                    "candidate_typing_id": pair[
                        "candidate"
                    ]["typing_id"],
                    "donor_external_id": pair[
                        "donor"
                    ]["external_id"],
                    "donor_typing_id": pair[
                        "donor"
                    ]["typing_id"],
                    "recipient_external_id": pair[
                        "recipient"
                    ]["external_id"],
                    "recipient_typing_id": pair[
                        "recipient"
                    ]["typing_id"],
                    "imgthla_version": pair[
                        "imgthla_version"
                    ],
                    "run_id": (
                        ""
                        if pair["run_id"] is None
                        else pair["run_id"]
                    ),
                    **order_fields,
                    "level": db_level,
                    "locus": locus,
                    "shared_count": result[
                        "shared_count"
                    ],
                    "donor_only_count": result[
                        "mismatch_count"
                    ],
                    "recipient_only_count": result[
                        "recipient_only_count"
                    ],
                    "shared_values_json": json.dumps(
                        result["shared"],
                        ensure_ascii=False,
                    ),
                    "donor_only_values_json": json.dumps(
                        result["donor_only"],
                        ensure_ascii=False,
                    ),
                    "recipient_only_values_json": json.dumps(
                        result["recipient_only"],
                        ensure_ascii=False,
                    ),
                }


def export_batch_csv(
    payload,
    path,
    overwrite=False,
):
    path = Path(path)

    if path.exists() and not overwrite:
        raise BatchExportFileExistsError(
            f"CSV batch export вече съществува: {path}"
        )

    temp_path = path.with_name(
        path.name + ".tmp"
    )

    try:
        with temp_path.open(
            "w",
            encoding="utf-8-sig",
            newline="",
        ) as handle:
            writer = csv.DictWriter(
                handle,
                fieldnames=BATCH_CSV_COLUMNS,
            )
            writer.writeheader()

            for row in iter_batch_csv_rows(
                payload
            ):
                writer.writerow(row)

        temp_path.replace(path)
    finally:
        if temp_path.exists():
            temp_path.unlink()

    return path


def export_batch(
    batch,
    output_dir=DEFAULT_BATCH_EXPORT_DIR,
    export_format="both",
    export_name=None,
    overwrite=False,
):
    """
    Export a FULL Step 17/18 batch.

    `batch['rows']` must contain all computed pairs. A display-truncated
    Step 18 view is intentionally rejected to avoid silent data loss.
    """
    export_format = normalize_batch_export_format(
        export_format
    )
    validate_batch_for_export(batch)

    output_dir = Path(output_dir)
    output_dir.mkdir(
        parents=True,
        exist_ok=True,
    )

    payload = build_batch_export_payload(
        batch
    )

    targets = _target_paths(
        batch,
        output_dir,
        export_format,
        export_name=export_name,
    )

    _ensure_targets_available(
        targets,
        overwrite,
    )

    created = {}

    if "json" in targets:
        created["json"] = export_batch_json(
            payload,
            targets["json"],
            overwrite=overwrite,
        )

    if "csv" in targets:
        created["csv"] = export_batch_csv(
            payload,
            targets["csv"],
            overwrite=overwrite,
        )

    return {
        "output_dir": output_dir,
        "files": created,
        "format": export_format,
        "pair_count": payload["batch"][
            "pair_count"
        ],
        "csv_data_row_count": (
            payload["batch"]["pair_count"]
            * 24
        ),
        "software_ordering": payload[
            "batch"
        ]["software_ordering"],
        "source_save_mode": payload[
            "batch"
        ]["source_save_mode"],
        "export_name": normalize_export_name(
            export_name,
            batch,
        ),
    }
