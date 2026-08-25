from __future__ import annotations

import csv
import json
from pathlib import Path
from typing import Iterable

import analyses
from config import HLA_LOCI


DEFAULT_EXPORT_DIR = Path(__file__).with_name("exports")

VALID_FORMATS = ("json", "csv", "both")

CSV_COLUMNS = (
    "run_id",
    "donor_external_id",
    "donor_typing_id",
    "recipient_external_id",
    "recipient_typing_id",
    "imgthla_version",
    "analysis_created_at",
    "level",
    "locus",
    "shared_count",
    "donor_only_count",
    "recipient_only_count",
    "shared_values_json",
    "donor_only_values_json",
    "recipient_only_values_json",
)


class ExportError(RuntimeError):
    """Обща грешка при export на analysis_run."""


class ExportFileExistsError(ExportError):
    """Export файл вече съществува и overwrite=False."""


def normalize_export_format(value):
    if value is None:
        return "both"

    if not isinstance(value, str):
        raise ValueError("Export format трябва да бъде текст.")

    normalized = value.strip().lower()

    if normalized not in VALID_FORMATS:
        raise ValueError(
            "Невалиден export format. Допустими: json, csv, both."
        )

    return normalized


def _target_paths(run_id, output_dir, export_format):
    run_id = int(run_id)
    output_dir = Path(output_dir)

    targets = {}

    if export_format in ("json", "both"):
        targets["json"] = output_dir / f"analysis_run_{run_id}.json"

    if export_format in ("csv", "both"):
        targets["csv"] = output_dir / f"analysis_run_{run_id}.csv"

    return targets


def _ensure_targets_available(targets, overwrite):
    if overwrite:
        return

    existing = [
        path
        for path in targets.values()
        if path.exists()
    ]

    if existing:
        joined = ", ".join(str(path) for path in existing)
        raise ExportFileExistsError(
            "Export файл вече съществува. "
            "Използвайте --overwrite за замяна: "
            + joined
        )


def build_export_payload(database_path, run_id):
    """
    Зарежда вече записаните 24 analysis_results от SQLite.

    Не преизчислява HLA редукции и не извиква py-ard.
    """
    loaded = analyses.load_analysis_results(
        database_path=database_path,
        run_id=run_id,
        require_complete=True,
    )

    run = loaded["run"]

    return {
        "schema": "hla-analysis-export-v1",
        "run": {
            "run_id": run["run_id"],
            "donor": {
                "external_id": run["donor"]["external_id"],
                "typing_id": run["donor_typing_id"],
            },
            "recipient": {
                "external_id": run["recipient"]["external_id"],
                "typing_id": run["recipient_typing_id"],
            },
            "imgthla_version": run["imgthla_version"],
            "created_at": run["created_at"],
            "analysis_result_count": loaded["row_count"],
        },
        "results": loaded["results"],
    }


def _atomic_write_text(path, text, encoding="utf-8"):
    """
    Записва чрез временен файл и Path.replace(), за да не остава
    частично записан export при прекъсване по време на write.
    """
    path = Path(path)
    temp_path = path.with_name(path.name + ".tmp")

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


def export_analysis_json(payload, path, overwrite=False):
    path = Path(path)

    if path.exists() and not overwrite:
        raise ExportFileExistsError(
            f"JSON export файлът вече съществува: {path}"
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


def iter_csv_rows(payload):
    run = payload["run"]

    levels = (
        ("canonical", "CANONICAL"),
        ("lgx", "LGX"),
        ("G", "G"),
        ("P", "P"),
    )

    for result_key, db_level in levels:
        for locus in HLA_LOCI:
            result = payload["results"][result_key][locus]

            yield {
                "run_id": run["run_id"],
                "donor_external_id": run["donor"]["external_id"],
                "donor_typing_id": run["donor"]["typing_id"],
                "recipient_external_id": run["recipient"]["external_id"],
                "recipient_typing_id": run["recipient"]["typing_id"],
                "imgthla_version": run["imgthla_version"],
                "analysis_created_at": run["created_at"],
                "level": db_level,
                "locus": locus,
                "shared_count": result["shared_count"],
                "donor_only_count": result["mismatch_count"],
                "recipient_only_count": result["recipient_only_count"],
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


def export_analysis_csv(payload, path, overwrite=False):
    path = Path(path)

    if path.exists() and not overwrite:
        raise ExportFileExistsError(
            f"CSV export файлът вече съществува: {path}"
        )

    temp_path = path.with_name(path.name + ".tmp")

    try:
        # utf-8-sig улеснява отварянето на CSV в Excel под Windows.
        with temp_path.open(
            "w",
            encoding="utf-8-sig",
            newline="",
        ) as handle:
            writer = csv.DictWriter(
                handle,
                fieldnames=CSV_COLUMNS,
            )
            writer.writeheader()

            for row in iter_csv_rows(payload):
                writer.writerow(row)

        temp_path.replace(path)
    finally:
        if temp_path.exists():
            temp_path.unlink()

    return path


def export_analysis(
    database_path,
    run_id,
    output_dir=DEFAULT_EXPORT_DIR,
    export_format="both",
    overwrite=False,
):
    """
    Export на един вече анализиран run_id.

    По подразбиране създава:
        exports/analysis_run_<id>.json
        exports/analysis_run_<id>.csv
    """
    export_format = normalize_export_format(export_format)
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    payload = build_export_payload(
        database_path,
        run_id,
    )

    targets = _target_paths(
        payload["run"]["run_id"],
        output_dir,
        export_format,
    )

    _ensure_targets_available(
        targets,
        overwrite,
    )

    created = {}

    if "json" in targets:
        created["json"] = export_analysis_json(
            payload,
            targets["json"],
            overwrite=overwrite,
        )

    if "csv" in targets:
        created["csv"] = export_analysis_csv(
            payload,
            targets["csv"],
            overwrite=overwrite,
        )

    return {
        "run_id": payload["run"]["run_id"],
        "output_dir": output_dir,
        "files": created,
        "row_count": payload["run"]["analysis_result_count"],
    }
