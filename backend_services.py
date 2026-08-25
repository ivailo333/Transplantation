from __future__ import annotations

from pathlib import Path
from typing import Any

import audit_bundle
import database
import doctor
import hla_matrix
import step27_reporting
import step28_report_comparison
from backend_config import BackendSettings, load_backend_settings


BACKEND_RESPONSE_SCHEMA = "hla-backend-response-v1"
NON_CLINICAL_NOTICE = (
    "This backend exposes deterministic NON-CLINICAL HLA software artifacts. "
    "It does not provide transplant suitability, allocation, crossmatch, DSA, "
    "eplet, cPRA, risk, or treatment decisions."
)


class BackendServiceError(ValueError):
    """Invalid backend service request."""


def _settings(settings=None):
    return settings if settings is not None else load_backend_settings()


def _jsonable(value):
    if isinstance(value, Path):
        return str(value)
    if isinstance(value, dict):
        return {key: _jsonable(item) for key, item in value.items()}
    if isinstance(value, (list, tuple)):
        return [_jsonable(item) for item in value]
    return value


def envelope(data, *, request_id=None):
    return {
        "schema": BACKEND_RESPONSE_SCHEMA,
        "request_id": request_id,
        "clinical": False,
        "notice": NON_CLINICAL_NOTICE,
        "data": _jsonable(data),
    }


def ensure_database_ready(settings=None):
    settings = _settings(settings)
    if settings.auto_migrate:
        database.migrate_database(settings.database_path)
    database.verify_database_is_current(settings.database_path)
    return database.get_database_schema_status(settings.database_path)


def backend_metadata(settings=None, *, request_id=None):
    settings = _settings(settings)
    return envelope(
        {
            "name": settings.app_name,
            "component": "hla-transplantation-backend",
            "database_path": settings.database_path,
            "export_dir": settings.export_dir,
            "auto_migrate": settings.auto_migrate,
            "api_key_required": settings.api_key is not None,
            "supported_endpoints": [
                "/health",
                "/doctor",
                "/reports/live",
                "/reports/batch",
                "/comparisons/levels",
                "/comparisons/batches",
                "/audit/live",
                "/audit/batches",
            ],
        },
        request_id=request_id,
    )


def health(settings=None, *, request_id=None):
    settings = _settings(settings)
    schema_status = database.get_database_schema_status(settings.database_path)
    doctor_report = doctor.run_doctor(settings.database_path)
    ready = bool(
        schema_status.get("exists")
        and schema_status.get("is_current")
        and doctor_report["summary"][doctor.STATUS_FAIL] == 0
    )
    return envelope(
        {
            "ready": ready,
            "database_path": settings.database_path,
            "schema_status": schema_status,
            "doctor_summary": doctor_report["summary"],
        },
        request_id=request_id,
    )


def doctor_status(settings=None, *, request_id=None):
    settings = _settings(settings)
    return envelope(
        {
            "doctor": doctor.run_doctor(settings.database_path),
        },
        request_id=request_id,
    )


def _export_output_dir(settings, request):
    value = request.get("output_dir")
    return Path(value) if value else settings.export_dir


def _export_name(request):
    value = request.get("export_name")
    return value if value else None


def _maybe_export_report(settings, report, request):
    export_format = request.get("export_format")
    if export_format is None:
        return None
    return step27_reporting.export_report(
        report,
        output_dir=_export_output_dir(settings, request),
        export_format=export_format,
        export_name=_export_name(request),
        overwrite=bool(request.get("overwrite", False)),
    )


def _maybe_export_comparison(settings, comparison, request):
    export_format = request.get("export_format")
    if export_format is None:
        return None
    return step28_report_comparison.export_comparison(
        comparison,
        output_dir=_export_output_dir(settings, request),
        export_format=export_format,
        export_name=_export_name(request),
        overwrite=bool(request.get("overwrite", False)),
    )


def build_live_report(settings, request, *, request_id=None):
    settings = _settings(settings)
    ensure_database_ready(settings)
    report = step27_reporting.build_live_report(
        database_path=settings.database_path,
        direction=request["direction"],
        anchor_external_id=request["external_id"],
        anchor_typing_id=request.get("typing_id"),
        candidate_external_ids=request.get("candidate_external_ids"),
        level=request.get("level", hla_matrix.DEFAULT_LEVEL),
        loci=request.get("loci"),
        sort_by=request.get("sort_by"),
        sort_order=request.get("sort_order", "auto"),
    )
    return envelope(
        {
            "report": report,
            "text": step27_reporting.render_report(report)
            if request.get("include_text")
            else None,
            "export": _maybe_export_report(settings, report, request),
        },
        request_id=request_id,
    )


def build_batch_report(settings, request, *, request_id=None):
    settings = _settings(settings)
    ensure_database_ready(settings)
    report = step27_reporting.build_persistent_report(
        database_path=settings.database_path,
        batch_id=request["batch_id"],
        level=request.get("level", hla_matrix.DEFAULT_LEVEL),
        loci=request.get("loci"),
        sort_by=request.get("sort_by"),
        sort_order=request.get("sort_order", "auto"),
    )
    return envelope(
        {
            "report": report,
            "text": step27_reporting.render_report(report)
            if request.get("include_text")
            else None,
            "export": _maybe_export_report(settings, report, request),
        },
        request_id=request_id,
    )


def build_level_comparison(settings, request, *, request_id=None):
    settings = _settings(settings)
    ensure_database_ready(settings)
    comparison = step28_report_comparison.build_live_level_comparison(
        database_path=settings.database_path,
        direction=request["direction"],
        anchor_external_id=request["external_id"],
        anchor_typing_id=request.get("typing_id"),
        candidate_external_ids=request.get("candidate_external_ids"),
        levels=request.get("levels"),
        loci=request.get("loci"),
        sort_by=request.get("sort_by"),
        sort_order=request.get("sort_order", "auto"),
    )
    return envelope(
        {
            "comparison": comparison,
            "text": step28_report_comparison.render_comparison(comparison)
            if request.get("include_text")
            else None,
            "export": _maybe_export_comparison(settings, comparison, request),
        },
        request_id=request_id,
    )


def build_batch_comparison(settings, request, *, request_id=None):
    settings = _settings(settings)
    ensure_database_ready(settings)
    comparison = step28_report_comparison.build_persistent_batch_comparison(
        database_path=settings.database_path,
        left_batch_id=request["left_batch_id"],
        right_batch_id=request["right_batch_id"],
        level=request.get("level", hla_matrix.DEFAULT_LEVEL),
        loci=request.get("loci"),
        sort_by=request.get("sort_by"),
        sort_order=request.get("sort_order", "auto"),
    )
    return envelope(
        {
            "comparison": comparison,
            "text": step28_report_comparison.render_comparison(comparison)
            if request.get("include_text")
            else None,
            "export": _maybe_export_comparison(settings, comparison, request),
        },
        request_id=request_id,
    )


def create_live_audit(settings, request, *, request_id=None):
    settings = _settings(settings)
    ensure_database_ready(settings)
    info = audit_bundle.create_live_audit_bundle(
        database_path=settings.database_path,
        direction=request["direction"],
        anchor_external_id=request["external_id"],
        anchor_typing_id=request.get("typing_id"),
        candidate_external_ids=request.get("candidate_external_ids"),
        level=request.get("level", hla_matrix.DEFAULT_LEVEL),
        comparison_levels=request.get("comparison_levels"),
        loci=request.get("loci"),
        sort_by=request.get("sort_by"),
        sort_order=request.get("sort_order", "auto"),
        output_dir=_export_output_dir(settings, request),
        bundle_name=request.get("bundle_name"),
        overwrite=bool(request.get("overwrite", False)),
        zip_bundle=bool(request.get("zip_bundle", False)),
    )
    return envelope({"audit_bundle": info}, request_id=request_id)


def create_batch_audit(settings, request, *, request_id=None):
    settings = _settings(settings)
    ensure_database_ready(settings)
    info = audit_bundle.create_batch_audit_bundle(
        database_path=settings.database_path,
        left_batch_id=request["left_batch_id"],
        right_batch_id=request["right_batch_id"],
        level=request.get("level", hla_matrix.DEFAULT_LEVEL),
        loci=request.get("loci"),
        sort_by=request.get("sort_by"),
        sort_order=request.get("sort_order", "auto"),
        output_dir=_export_output_dir(settings, request),
        bundle_name=request.get("bundle_name"),
        overwrite=bool(request.get("overwrite", False)),
        zip_bundle=bool(request.get("zip_bundle", False)),
    )
    return envelope({"audit_bundle": info}, request_id=request_id)


SERVICE_ERROR_TYPES = (
    BackendServiceError,
    database.DatabaseSchemaError,
    database.MigrationError,
    database.SubjectNotFoundError,
    database.TypingNotFoundError,
    database.IncompleteTypingError,
    database.AnalysisRunNotFoundError,
    database.AnalysisTypingRoleError,
    database.AnalysisVersionMismatchError,
    database.AnalysisResultsError,
    database.AnalysisResultsNotFoundError,
    step27_reporting.ReportingError,
    step27_reporting.ReportingExportError,
    step28_report_comparison.ReportComparisonError,
    step28_report_comparison.ReportComparisonExportError,
    audit_bundle.AuditBundleError,
    OSError,
    UnicodeError,
    ValueError,
)
