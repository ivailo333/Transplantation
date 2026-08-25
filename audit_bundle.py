from __future__ import annotations

from datetime import datetime, timezone
import json
from pathlib import Path
import re
import zipfile

import database
import doctor
import hla_matrix
import step27_reporting
import step28_report_comparison


AUDIT_SCHEMA = "hla-audit-bundle-v1"
DEFAULT_EXPORT_DIR = Path(__file__).with_name("exports") / "audit"


class AuditBundleError(RuntimeError):
    """Audit bundle creation failed."""


class AuditBundleExistsError(AuditBundleError):
    """Audit bundle target already exists."""


def _timestamp():
    return datetime.now(timezone.utc).isoformat(timespec="seconds").replace(
        "+00:00",
        "Z",
    )


def _safe_name(value):
    value = str(value).strip()
    value = re.sub(r"[^A-Za-z0-9_.-]+", "_", value)
    return value.strip("._-") or "audit_bundle"


def _default_live_name(direction, external_id, level):
    return _safe_name(f"audit_{direction}_{external_id}_{level}")


def _default_batch_name(left_batch_id, right_batch_id, level):
    return _safe_name(f"audit_batches_{left_batch_id}_{right_batch_id}_{level}")


def _write_text(path, text):
    tmp = path.with_name(path.name + ".tmp")
    try:
        tmp.write_text(text + "\n", encoding="utf-8")
        tmp.replace(path)
    finally:
        if tmp.exists():
            tmp.unlink()


def _write_json(path, payload):
    tmp = path.with_name(path.name + ".tmp")
    try:
        tmp.write_text(
            json.dumps(payload, ensure_ascii=False, indent=2, default=str) + "\n",
            encoding="utf-8",
        )
        tmp.replace(path)
    finally:
        if tmp.exists():
            tmp.unlink()


def _prepare_bundle_dir(output_dir, bundle_name, overwrite):
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    bundle_dir = output_dir / _safe_name(bundle_name)
    if bundle_dir.exists() and not overwrite:
        raise AuditBundleExistsError(
            "Audit bundle директория вече съществува. "
            f"Използвайте --overwrite: {bundle_dir}"
        )
    bundle_dir.mkdir(parents=True, exist_ok=True)
    return bundle_dir


def _remember(files, bundle_dir, key, path):
    if path is None:
        return
    path = Path(path)
    files[key] = str(path.relative_to(bundle_dir))


def _zip_bundle(bundle_dir, overwrite):
    zip_path = bundle_dir.with_suffix(".zip")
    if zip_path.exists():
        if not overwrite:
            raise AuditBundleExistsError(
                "Audit bundle ZIP вече съществува. "
                f"Използвайте --overwrite: {zip_path}"
            )
        zip_path.unlink()

    tmp = zip_path.with_name(zip_path.name + ".tmp")
    try:
        with zipfile.ZipFile(
            tmp,
            "w",
            compression=zipfile.ZIP_DEFLATED,
        ) as archive:
            for path in sorted(bundle_dir.rglob("*")):
                if path.is_file():
                    archive.write(path, path.relative_to(bundle_dir))
        tmp.replace(zip_path)
    finally:
        if tmp.exists():
            tmp.unlink()
    return zip_path


def _write_doctor_and_schema(bundle_dir, database_path, files):
    doctor_report = doctor.run_doctor(database_path)
    schema_status = database.get_database_schema_status(database_path)

    path = bundle_dir / "doctor.txt"
    _write_text(path, doctor.render_doctor(doctor_report))
    _remember(files, bundle_dir, "doctor_text", path)

    path = bundle_dir / "doctor.json"
    _write_json(path, doctor_report)
    _remember(files, bundle_dir, "doctor_json", path)

    path = bundle_dir / "schema_status.json"
    _write_json(path, schema_status)
    _remember(files, bundle_dir, "schema_status_json", path)

    return doctor_report, schema_status


def _export_report(bundle_dir, report, export_name, files, prefix):
    text_path = bundle_dir / f"{export_name}.txt"
    _write_text(text_path, step27_reporting.render_report(report))
    _remember(files, bundle_dir, f"{prefix}_text", text_path)

    info = step27_reporting.export_report(
        report,
        output_dir=bundle_dir,
        export_format="all",
        export_name=export_name,
        overwrite=True,
    )
    _remember(files, bundle_dir, f"{prefix}_json", info.get("json_path"))
    _remember(files, bundle_dir, f"{prefix}_csv", info.get("csv_path"))
    _remember(files, bundle_dir, f"{prefix}_html", info.get("html_path"))
    return info


def _export_comparison(bundle_dir, comparison, export_name, files, prefix):
    text_path = bundle_dir / f"{export_name}.txt"
    _write_text(text_path, step28_report_comparison.render_comparison(comparison))
    _remember(files, bundle_dir, f"{prefix}_text", text_path)

    info = step28_report_comparison.export_comparison(
        comparison,
        output_dir=bundle_dir,
        export_format="all",
        export_name=export_name,
        overwrite=True,
    )
    _remember(files, bundle_dir, f"{prefix}_json", info.get("json_path"))
    _remember(files, bundle_dir, f"{prefix}_csv", info.get("csv_path"))
    _remember(files, bundle_dir, f"{prefix}_html", info.get("html_path"))
    return info


def create_live_audit_bundle(
    database_path,
    direction,
    anchor_external_id,
    *,
    anchor_typing_id=None,
    candidate_external_ids=None,
    level=hla_matrix.DEFAULT_LEVEL,
    comparison_levels=None,
    loci=None,
    sort_by=None,
    sort_order="auto",
    output_dir=DEFAULT_EXPORT_DIR,
    bundle_name=None,
    overwrite=False,
    zip_bundle=False,
):
    report = step27_reporting.build_live_report(
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
    comparison = step28_report_comparison.build_live_level_comparison(
        database_path=database_path,
        direction=direction,
        anchor_external_id=anchor_external_id,
        anchor_typing_id=anchor_typing_id,
        candidate_external_ids=candidate_external_ids,
        levels=comparison_levels,
        loci=loci,
        sort_by=sort_by,
        sort_order=sort_order,
    )

    name = bundle_name or _default_live_name(direction, anchor_external_id, level)
    bundle_dir = _prepare_bundle_dir(output_dir, name, overwrite)
    files = {}
    doctor_report, schema_status = _write_doctor_and_schema(
        bundle_dir,
        database_path,
        files,
    )
    report_info = _export_report(bundle_dir, report, "step27_report", files, "report")
    comparison_info = _export_comparison(
        bundle_dir,
        comparison,
        "step28_comparison",
        files,
        "comparison",
    )

    metadata = {
        "schema": AUDIT_SCHEMA,
        "generated_at": _timestamp(),
        "mode": "live",
        "database_path": str(Path(database_path)),
        "direction": direction,
        "anchor_external_id": anchor_external_id,
        "anchor_typing_id": anchor_typing_id,
        "report_level": level,
        "comparison_levels": comparison["levels"],
        "loci": list(report["hla_reference"]["loci"]),
        "pair_count": report["pair_count"],
        "doctor_summary": doctor_report["summary"],
        "schema_current": schema_status.get("is_current"),
    }
    files["metadata_json"] = "metadata.json"
    metadata["files"] = dict(sorted(files.items()))
    _write_json(bundle_dir / "metadata.json", metadata)

    zip_path = _zip_bundle(bundle_dir, overwrite) if zip_bundle else None
    return {
        "schema": AUDIT_SCHEMA,
        "mode": "live",
        "bundle_name": bundle_dir.name,
        "bundle_dir": bundle_dir,
        "zip_path": zip_path,
        "files": dict(sorted(files.items())),
        "doctor_summary": doctor_report["summary"],
        "report_export": report_info,
        "comparison_export": comparison_info,
    }


def create_batch_audit_bundle(
    database_path,
    left_batch_id,
    right_batch_id,
    *,
    level=hla_matrix.DEFAULT_LEVEL,
    loci=None,
    sort_by=None,
    sort_order="auto",
    output_dir=DEFAULT_EXPORT_DIR,
    bundle_name=None,
    overwrite=False,
    zip_bundle=False,
):
    if left_batch_id == right_batch_id:
        raise AuditBundleError(
            "Audit batch bundle изисква два различни batch_id."
        )

    left_report = step27_reporting.build_persistent_report(
        database_path=database_path,
        batch_id=left_batch_id,
        level=level,
        loci=loci,
        sort_by=sort_by,
        sort_order=sort_order,
    )
    right_report = step27_reporting.build_persistent_report(
        database_path=database_path,
        batch_id=right_batch_id,
        level=level,
        loci=loci,
        sort_by=sort_by,
        sort_order=sort_order,
    )
    comparison = step28_report_comparison.build_batch_comparison_from_reports(
        left_report,
        right_report,
    )

    name = bundle_name or _default_batch_name(left_batch_id, right_batch_id, level)
    bundle_dir = _prepare_bundle_dir(output_dir, name, overwrite)
    files = {}
    doctor_report, schema_status = _write_doctor_and_schema(
        bundle_dir,
        database_path,
        files,
    )
    left_info = _export_report(
        bundle_dir,
        left_report,
        "step27_left_report",
        files,
        "left_report",
    )
    right_info = _export_report(
        bundle_dir,
        right_report,
        "step27_right_report",
        files,
        "right_report",
    )
    comparison_info = _export_comparison(
        bundle_dir,
        comparison,
        "step28_comparison",
        files,
        "comparison",
    )

    metadata = {
        "schema": AUDIT_SCHEMA,
        "generated_at": _timestamp(),
        "mode": "batches",
        "database_path": str(Path(database_path)),
        "left_batch_id": left_batch_id,
        "right_batch_id": right_batch_id,
        "level": level,
        "loci": list(left_report["hla_reference"]["loci"]),
        "common_candidates": comparison["common_candidates"],
        "doctor_summary": doctor_report["summary"],
        "schema_current": schema_status.get("is_current"),
    }
    files["metadata_json"] = "metadata.json"
    metadata["files"] = dict(sorted(files.items()))
    _write_json(bundle_dir / "metadata.json", metadata)

    zip_path = _zip_bundle(bundle_dir, overwrite) if zip_bundle else None
    return {
        "schema": AUDIT_SCHEMA,
        "mode": "batches",
        "bundle_name": bundle_dir.name,
        "bundle_dir": bundle_dir,
        "zip_path": zip_path,
        "files": dict(sorted(files.items())),
        "doctor_summary": doctor_report["summary"],
        "left_report_export": left_info,
        "right_report_export": right_info,
        "comparison_export": comparison_info,
    }


def render_audit_summary(info):
    lines = [
        "=" * 96,
        "HLA AUDIT BUNDLE CREATED",
        "=" * 96,
        f"Mode: {info['mode'].upper()}",
        f"Bundle name: {info['bundle_name']}",
        f"Bundle directory: {Path(info['bundle_dir']).resolve()}",
    ]
    if info.get("zip_path") is not None:
        lines.append(f"ZIP: {Path(info['zip_path']).resolve()}")
    summary = info["doctor_summary"]
    lines.append(
        f"Doctor summary: OK={summary[doctor.STATUS_OK]} "
        f"WARN={summary[doctor.STATUS_WARN]} "
        f"FAIL={summary[doctor.STATUS_FAIL]}"
    )
    lines.append("Files:")
    for key, path in info["files"].items():
        lines.append(f"  {key}: {path}")
    lines.extend(
        [
            "Audit bundle contains NON-CLINICAL software artifacts only.",
            "=" * 96,
        ]
    )
    return "\n".join(lines)
