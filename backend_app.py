import os
from uuid import uuid4

from backend_config import BackendSettings, load_backend_settings
import backend_services


API_SCHEMA = "hla-backend-api-v1"


def _payload(model):
    if hasattr(model, "model_dump"):
        return model.model_dump(exclude_none=True)
    return model.dict(exclude_none=True)


def _service_status(exc):
    if isinstance(exc, UnicodeError):
        return 400
    if isinstance(exc, OSError):
        return 503
    name = exc.__class__.__name__
    if name in {"DatabaseSchemaError", "MigrationError"}:
        return 503
    if name.endswith("NotFoundError"):
        return 404
    if name.endswith("ExistsError"):
        return 409
    return 400


def create_app(settings: BackendSettings | None = None):
    try:
        from fastapi import Depends, FastAPI, Header, HTTPException, Request
        from fastapi.middleware.cors import CORSMiddleware
        from fastapi.responses import JSONResponse
        from pydantic import BaseModel
    except ModuleNotFoundError as exc:  # pragma: no cover - dependency gate
        raise RuntimeError(
            "FastAPI backend dependencies are not installed. "
            "Install with: python -m pip install -e .[api]"
        ) from exc

    settings = load_backend_settings() if settings is None else settings

    class ExportOptions(BaseModel):
        export_format: str | None = None
        output_dir: str | None = None
        export_name: str | None = None
        overwrite: bool = False
        include_text: bool = False

    class LiveReportRequest(ExportOptions):
        direction: str
        external_id: str
        typing_id: int | None = None
        candidate_external_ids: list[str] | None = None
        level: str = "lgx"
        loci: list[str] | None = None
        sort_by: str | None = None
        sort_order: str = "auto"

    class BatchReportRequest(ExportOptions):
        batch_id: int
        level: str = "lgx"
        loci: list[str] | None = None
        sort_by: str | None = None
        sort_order: str = "auto"

    class LevelComparisonRequest(ExportOptions):
        direction: str
        external_id: str
        typing_id: int | None = None
        candidate_external_ids: list[str] | None = None
        levels: list[str] | None = None
        loci: list[str] | None = None
        sort_by: str | None = None
        sort_order: str = "auto"

    class BatchComparisonRequest(ExportOptions):
        left_batch_id: int
        right_batch_id: int
        level: str = "lgx"
        loci: list[str] | None = None
        sort_by: str | None = None
        sort_order: str = "auto"

    class LiveAuditRequest(BaseModel):
        direction: str
        external_id: str
        typing_id: int | None = None
        candidate_external_ids: list[str] | None = None
        level: str = "lgx"
        comparison_levels: list[str] | None = None
        loci: list[str] | None = None
        sort_by: str | None = None
        sort_order: str = "auto"
        output_dir: str | None = None
        bundle_name: str | None = None
        overwrite: bool = False
        zip_bundle: bool = False

    class BatchAuditRequest(BaseModel):
        left_batch_id: int
        right_batch_id: int
        level: str = "lgx"
        loci: list[str] | None = None
        sort_by: str | None = None
        sort_order: str = "auto"
        output_dir: str | None = None
        bundle_name: str | None = None
        overwrite: bool = False
        zip_bundle: bool = False

    app = FastAPI(
        title=settings.app_name,
        version="0.1.0",
        description=(
            "NON-CLINICAL HLA analytics backend. It exposes deterministic "
            "software reports, comparisons, doctor checks, and audit bundles."
        ),
    )
    app.state.settings = settings

    if settings.cors_origins:
        app.add_middleware(
            CORSMiddleware,
            allow_origins=list(settings.cors_origins),
            allow_credentials=False,
            allow_methods=["GET", "POST"],
            allow_headers=["Authorization", "Content-Type", "X-API-Key", "X-Request-ID"],
        )

    async def require_api_key(x_api_key: str | None = Header(default=None)):
        if settings.api_key is not None and x_api_key != settings.api_key:
            raise HTTPException(
                status_code=401,
                detail={
                    "schema": API_SCHEMA,
                    "error": "unauthorized",
                    "message": "Missing or invalid X-API-Key header.",
                },
            )

    @app.middleware("http")
    async def request_id_middleware(request: Request, call_next):
        request_id = request.headers.get("X-Request-ID") or str(uuid4())
        request.state.request_id = request_id
        response = await call_next(request)
        response.headers["X-Request-ID"] = request_id
        return response

    async def service_error_handler(request: Request, exc: Exception):
        request_id = getattr(request.state, "request_id", None)
        return JSONResponse(
            status_code=_service_status(exc),
            content={
                "schema": API_SCHEMA,
                "request_id": request_id,
                "clinical": False,
                "notice": backend_services.NON_CLINICAL_NOTICE,
                "error": exc.__class__.__name__,
                "message": str(exc),
            },
        )

    for exc_type in backend_services.SERVICE_ERROR_TYPES:
        app.add_exception_handler(exc_type, service_error_handler)

    @app.get("/", dependencies=[Depends(require_api_key)])
    def root(request: Request):
        return backend_services.backend_metadata(
            settings,
            request_id=request.state.request_id,
        )

    @app.get("/health", dependencies=[Depends(require_api_key)])
    def health(request: Request):
        return backend_services.health(
            settings,
            request_id=request.state.request_id,
        )

    @app.get("/doctor", dependencies=[Depends(require_api_key)])
    def doctor_status(request: Request):
        return backend_services.doctor_status(
            settings,
            request_id=request.state.request_id,
        )

    @app.post("/reports/live", dependencies=[Depends(require_api_key)])
    def reports_live(payload: LiveReportRequest, request: Request):
        return backend_services.build_live_report(
            settings,
            _payload(payload),
            request_id=request.state.request_id,
        )

    @app.post("/reports/batch", dependencies=[Depends(require_api_key)])
    def reports_batch(payload: BatchReportRequest, request: Request):
        return backend_services.build_batch_report(
            settings,
            _payload(payload),
            request_id=request.state.request_id,
        )

    @app.post("/comparisons/levels", dependencies=[Depends(require_api_key)])
    def comparisons_levels(payload: LevelComparisonRequest, request: Request):
        return backend_services.build_level_comparison(
            settings,
            _payload(payload),
            request_id=request.state.request_id,
        )

    @app.post("/comparisons/batches", dependencies=[Depends(require_api_key)])
    def comparisons_batches(payload: BatchComparisonRequest, request: Request):
        return backend_services.build_batch_comparison(
            settings,
            _payload(payload),
            request_id=request.state.request_id,
        )

    @app.post("/audit/live", dependencies=[Depends(require_api_key)])
    def audit_live(payload: LiveAuditRequest, request: Request):
        return backend_services.create_live_audit(
            settings,
            _payload(payload),
            request_id=request.state.request_id,
        )

    @app.post("/audit/batches", dependencies=[Depends(require_api_key)])
    def audit_batches(payload: BatchAuditRequest, request: Request):
        return backend_services.create_batch_audit(
            settings,
            _payload(payload),
            request_id=request.state.request_id,
        )

    return app


try:
    app = create_app()
except RuntimeError:  # pragma: no cover - optional API dependencies
    app = None


def main():
    try:
        import uvicorn
    except ModuleNotFoundError as exc:  # pragma: no cover - dependency gate
        raise SystemExit(
            "FastAPI backend dependencies are not installed. "
            "Install with: python -m pip install -e .[api]"
        ) from exc

    host = os.environ.get("HLA_BACKEND_HOST", "127.0.0.1")
    port = int(os.environ.get("HLA_BACKEND_PORT", "8000"))
    uvicorn.run(
        "backend_app:app",
        host=host,
        port=port,
        reload=False,
    )


if __name__ == "__main__":
    main()
