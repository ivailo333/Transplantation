"""
STEP 16 — HLA typing import from JSON / CSV files.

Supported JSON forms:

1. Single typing object:
{
  "external_id": "DONOR-002",
  "subject_type": "DONOR",
  "hla": {
    "A": ["A*02:01", "A*24:02"],
    "B": ["B*07:02", "B*44:02"],
    "C": ["C*07:02", "C*05:01"],
    "DRB1": ["DRB1*15:01", "DRB1*04:01"],
    "DQB1": ["DQB1*06:02", "DQB1*03:02"],
    "DPB1": ["DPB1*04:01", "DPB1*02:01"]
  }
}

2. List of typing objects.

3. Wrapper:
{
  "typings": [
    { ... },
    { ... }
  ]
}

Supported CSV is one row per typing (wide format):
external_id,subject_type,imgthla_version,A1,A2,B1,B2,C1,C2,
DRB1_1,DRB1_2,DQB1_1,DQB1_2,DPB1_1,DPB1_2

imgthla_version is optional. If present, it must match the active
py-ard / IPD-IMGT/HLA database version.
"""

from __future__ import annotations

import copy
import csv
import json
from pathlib import Path

import database
from config import HLA_LOCI, SUBJECT_TYPES
from hla_validation import canonicalize_person, get_ard
from hla_reduction import reduce_person


SUPPORTED_IMPORT_FORMATS = ("auto", "json", "csv")

CSV_REQUIRED_COLUMNS = (
    "external_id",
    "subject_type",
    "A1",
    "A2",
    "B1",
    "B2",
    "C1",
    "C2",
    "DRB1_1",
    "DRB1_2",
    "DQB1_1",
    "DQB1_2",
    "DPB1_1",
    "DPB1_2",
)

CSV_OPTIONAL_COLUMNS = (
    "imgthla_version",
)


class HLAImportError(ValueError):
    """Обща грешка при import на HLA typing файл."""


class ImportFileFormatError(HLAImportError):
    """Файлът е с неподдържан или неразпознаваем формат."""


class ImportRecordError(HLAImportError):
    """Един import record е структурно невалиден."""


class ImportVersionError(HLAImportError):
    """Подадената IPD-IMGT/HLA версия не съвпада с активната."""


def normalize_import_format(value):
    if value is None:
        return "auto"

    if not isinstance(value, str):
        raise ImportFileFormatError(
            "Import format трябва да бъде текст."
        )

    normalized = value.strip().lower()

    if normalized not in SUPPORTED_IMPORT_FORMATS:
        raise ImportFileFormatError(
            "Невалиден import format. Допустими: auto, json, csv."
        )

    return normalized


def detect_import_format(path, explicit_format="auto"):
    path = Path(path)
    explicit_format = normalize_import_format(explicit_format)

    if explicit_format != "auto":
        return explicit_format

    suffix = path.suffix.lower()

    if suffix == ".json":
        return "json"

    if suffix == ".csv":
        return "csv"

    raise ImportFileFormatError(
        f"Не може да се определи форматът от разширението {suffix!r}. "
        "Използвайте --format json или --format csv."
    )


def _require_input_file(path):
    path = Path(path)

    if not path.exists():
        raise HLAImportError(
            f"Import файлът не съществува: {path}"
        )

    if not path.is_file():
        raise HLAImportError(
            f"Import path не е файл: {path}"
        )

    return path


def _normalize_external_id(value, record_label):
    if not isinstance(value, str):
        raise ImportRecordError(
            f"{record_label}: external_id трябва да бъде текст."
        )

    normalized = value.strip()

    if not normalized:
        raise ImportRecordError(
            f"{record_label}: external_id не може да бъде празен."
        )

    return normalized


def _normalize_subject_type(value, record_label):
    if not isinstance(value, str):
        raise ImportRecordError(
            f"{record_label}: subject_type трябва да бъде текст."
        )

    normalized = value.strip().upper()

    if normalized not in SUBJECT_TYPES:
        raise ImportRecordError(
            f"{record_label}: невалиден subject_type {value!r}. "
            f"Допустими: {', '.join(SUBJECT_TYPES)}."
        )

    return normalized


def _normalize_hla_key(key):
    if not isinstance(key, str):
        return None

    normalized = key.strip().upper()

    if normalized.startswith("HLA-"):
        normalized = normalized[4:]

    if normalized in HLA_LOCI:
        return normalized

    return None


def _normalize_hla_mapping(value, record_label):
    if not isinstance(value, dict):
        raise ImportRecordError(
            f"{record_label}: hla трябва да бъде JSON object/dict."
        )

    normalized = {}

    for key, alleles in value.items():
        locus = _normalize_hla_key(key)

        if locus is None:
            raise ImportRecordError(
                f"{record_label}: непознат HLA locus key {key!r}."
            )

        if locus in normalized:
            raise ImportRecordError(
                f"{record_label}: HLA-{locus} е зададен повече от веднъж."
            )

        if not isinstance(alleles, (list, tuple)) or len(alleles) != 2:
            raise ImportRecordError(
                f"{record_label}: HLA-{locus} трябва да съдържа "
                "точно 2 алела."
            )

        clean_values = []

        for copy_number, allele in enumerate(alleles, start=1):
            if not isinstance(allele, str):
                raise ImportRecordError(
                    f"{record_label}: HLA-{locus} allele {copy_number} "
                    "трябва да бъде текст."
                )

            if not allele.strip():
                raise ImportRecordError(
                    f"{record_label}: HLA-{locus} allele {copy_number} "
                    "не може да бъде празен."
                )

            # Preserve RAW formatting exactly as imported.
            clean_values.append(allele)

        normalized[locus] = clean_values

    missing = [
        locus
        for locus in HLA_LOCI
        if locus not in normalized
    ]

    if missing:
        raise ImportRecordError(
            f"{record_label}: липсващи HLA локуси: "
            + ", ".join(missing)
        )

    return {
        locus: normalized[locus]
        for locus in HLA_LOCI
    }


def normalize_import_record(record, record_number=1):
    record_label = f"record {record_number}"

    if not isinstance(record, dict):
        raise ImportRecordError(
            f"{record_label}: записът трябва да бъде object/dict."
        )

    allowed = {
        "external_id",
        "subject_type",
        "imgthla_version",
        "hla",
    }

    extra = set(record) - allowed

    if extra:
        raise ImportRecordError(
            f"{record_label}: непознати полета: "
            + ", ".join(sorted(extra))
        )

    if "external_id" not in record:
        raise ImportRecordError(
            f"{record_label}: липсва external_id."
        )

    if "subject_type" not in record:
        raise ImportRecordError(
            f"{record_label}: липсва subject_type."
        )

    if "hla" not in record:
        raise ImportRecordError(
            f"{record_label}: липсва hla."
        )

    version = record.get("imgthla_version")

    if version is not None:
        version = str(version).strip()

        if not version:
            raise ImportRecordError(
                f"{record_label}: imgthla_version не може да бъде празна."
            )

    return {
        "external_id": _normalize_external_id(
            record["external_id"],
            record_label,
        ),
        "subject_type": _normalize_subject_type(
            record["subject_type"],
            record_label,
        ),
        "imgthla_version": version,
        "raw_profile": _normalize_hla_mapping(
            record["hla"],
            record_label,
        ),
        "source_record_number": record_number,
    }


def load_json_records(path):
    path = _require_input_file(path)

    try:
        with path.open(
            "r",
            encoding="utf-8-sig",
        ) as handle:
            payload = json.load(handle)
    except json.JSONDecodeError as exc:
        raise ImportFileFormatError(
            f"Невалиден JSON в {path}: "
            f"line {exc.lineno}, column {exc.colno}: {exc.msg}"
        ) from exc

    if isinstance(payload, dict) and "typings" in payload:
        if set(payload) != {"typings"}:
            extra = sorted(set(payload) - {"typings"})
            raise ImportRecordError(
                "JSON wrapper с 'typings' не трябва да съдържа "
                f"други top-level полета: {', '.join(extra)}"
            )

        records = payload["typings"]

        if not isinstance(records, list):
            raise ImportRecordError(
                "JSON полето 'typings' трябва да бъде list."
            )

    elif isinstance(payload, list):
        records = payload

    elif isinstance(payload, dict):
        records = [payload]

    else:
        raise ImportRecordError(
            "JSON root трябва да бъде typing object, list или "
            "{'typings': [...]}."
        )

    if not records:
        raise ImportRecordError(
            "Import файлът не съдържа HLA typing записи."
        )

    return [
        normalize_import_record(record, index)
        for index, record in enumerate(records, start=1)
    ]


def _csv_header_map(fieldnames):
    if fieldnames is None:
        raise ImportFileFormatError(
            "CSV файлът няма header row."
        )

    normalized = {}

    for original in fieldnames:
        if original is None:
            continue

        key = original.strip()

        if not key:
            continue

        normalized[key.lower()] = original

    missing = [
        column
        for column in CSV_REQUIRED_COLUMNS
        if column.lower() not in normalized
    ]

    if missing:
        raise ImportFileFormatError(
            "CSV липсва задължителни колони: "
            + ", ".join(missing)
        )

    return normalized


def _csv_value(row, header_map, column):
    original = header_map.get(column.lower())

    if original is None:
        return None

    return row.get(original)


def _csv_row_to_record(row, header_map, row_number):
    def allele(column):
        value = _csv_value(row, header_map, column)

        if value is None or not isinstance(value, str) or not value.strip():
            raise ImportRecordError(
                f"CSV row {row_number}: {column} не може да бъде празна."
            )

        return value

    hla = {
        "A": [allele("A1"), allele("A2")],
        "B": [allele("B1"), allele("B2")],
        "C": [allele("C1"), allele("C2")],
        "DRB1": [allele("DRB1_1"), allele("DRB1_2")],
        "DQB1": [allele("DQB1_1"), allele("DQB1_2")],
        "DPB1": [allele("DPB1_1"), allele("DPB1_2")],
    }

    return normalize_import_record(
        {
            "external_id": _csv_value(
                row,
                header_map,
                "external_id",
            ),
            "subject_type": _csv_value(
                row,
                header_map,
                "subject_type",
            ),
            "imgthla_version": _csv_value(
                row,
                header_map,
                "imgthla_version",
            ),
            "hla": hla,
        },
        row_number - 1,
    )


def load_csv_records(path):
    path = _require_input_file(path)

    with path.open(
        "r",
        encoding="utf-8-sig",
        newline="",
    ) as handle:
        reader = csv.DictReader(handle)
        header_map = _csv_header_map(reader.fieldnames)

        records = []

        for row_number, row in enumerate(reader, start=2):
            # Ignore completely blank rows.
            if row and all(
                value is None or not str(value).strip()
                for value in row.values()
            ):
                continue

            records.append(
                _csv_row_to_record(
                    row,
                    header_map,
                    row_number,
                )
            )

    if not records:
        raise ImportRecordError(
            "CSV файлът не съдържа HLA typing записи."
        )

    return records


def load_import_records(
    path,
    import_format="auto",
):
    path = _require_input_file(path)
    resolved_format = detect_import_format(
        path,
        import_format,
    )

    if resolved_format == "json":
        records = load_json_records(path)
    elif resolved_format == "csv":
        records = load_csv_records(path)
    else:
        raise ImportFileFormatError(
            f"Неподдържан import format: {resolved_format}"
        )

    return {
        "path": path,
        "format": resolved_format,
        "records": records,
    }


def _active_imgthla_version():
    return str(get_ard().get_db_version()).strip()


def _resolve_record_version(
    requested_version,
    active_version,
    record_label,
):
    if requested_version is None:
        return active_version

    requested = str(requested_version).strip()

    if requested != active_version:
        raise ImportVersionError(
            f"{record_label}: imgthla_version={requested!r} "
            f"не съвпада с активната py-ard версия "
            f"{active_version!r}."
        )

    return requested


def prepare_typing_record(
    normalized_record,
    active_version=None,
):
    """
    Validates alleles via py-ard and creates RAW/CANONICAL/LGX/G/P.
    """
    if active_version is None:
        active_version = _active_imgthla_version()

    label = (
        f"{normalized_record['subject_type']} "
        f"{normalized_record['external_id']}"
    )

    version = _resolve_record_version(
        normalized_record.get("imgthla_version"),
        str(active_version),
        label,
    )

    raw_profile = copy.deepcopy(
        normalized_record["raw_profile"]
    )

    canonical = canonicalize_person(
        raw_profile,
        label,
    )

    bundle = {
        "raw": raw_profile,
        "canonical": canonical,
        "lgx": reduce_person(canonical, "lgx"),
        "G": reduce_person(canonical, "G"),
        "P": reduce_person(canonical, "P"),
    }

    return {
        "external_id": normalized_record["external_id"],
        "subject_type": normalized_record["subject_type"],
        "imgthla_version": version,
        "bundle": bundle,
        "source_record_number": normalized_record[
            "source_record_number"
        ],
    }


def prepare_import_records(records):
    """
    Prepare all records before the first SQL write.

    This means invalid allele/version input cannot cause a partial batch.
    """
    active_version = _active_imgthla_version()

    return [
        prepare_typing_record(
            record,
            active_version=active_version,
        )
        for record in records
    ]


def import_typings(
    database_path,
    input_path,
    import_format="auto",
    dry_run=False,
):
    """
    Imports one or more HLA typings.

    All records are parsed and py-ard validated before SQL writes.
    The SQL save itself is atomic across the whole file.
    """
    loaded = load_import_records(
        input_path,
        import_format=import_format,
    )

    prepared = prepare_import_records(
        loaded["records"]
    )

    if dry_run:
        saved = []
    else:
        saved = database.save_typing_records_atomic(
            database_path=database_path,
            records=prepared,
        )

    return {
        "source_path": loaded["path"],
        "format": loaded["format"],
        "record_count": len(prepared),
        "validated_count": len(prepared),
        "saved_count": len(saved),
        "dry_run": bool(dry_run),
        "records": prepared,
        "saved": saved,
    }
