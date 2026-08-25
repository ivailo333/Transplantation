import logging
from uuid import uuid4

from backend_config import BackendSettings, load_backend_settings
import backend_services


API_SCHEMA = "hla-backend-api-v1"
API_PREFIX = "/v1"
LOGGER = logging.getLogger("hla_backend")


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


def _error_content(request, error, message, *, details=None):
    request_id = getattr(request.state, "request_id", None)
    content = {
        "schema": API_SCHEMA,
        "request_id": request_id,
        "clinical": False,
        "notice": backend_services.NON_CLINICAL_NOTICE,
        "error": error,
        "message": message,
    }
    if details is not None:
        content["details"] = details
    return content


def create_app(settings: BackendSettings | None = None):
    try:
        from fastapi import Depends, FastAPI, Header, HTTPException, Request
        from fastapi.encoders import jsonable_encoder
        from fastapi.exceptions import RequestValidationError
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
            allow_headers=[
                "Authorization",
                "Content-Type",
                "X-API-Key",
                "X-Request-ID",
            ],
        )

    async def require_api_key(x_api_key: str | None = Header(default=None)):
        if settings.api_key is not None and x_api_key != settings.api_key:
            raise HTTPException(
                status_code=401,
                detail={
                    "error": "Unauthorized",
                    "message": "Missing or invalid X-API-Key header.",
                },
            )

    @app.middleware("http")
    async def request_id_middleware(request: Request, call_next):
        request_id = request.headers.get("X-Request-ID") or str(uuid4())
        request.state.request_id = request_id
        try:
            response = await call_next(request)
        except Exception:
            LOGGER.exception(
                "request_failed path=%s method=%s request_id=%s",
                request.url.path,
                request.method,
                request_id,
            )
            raise
        response.headers["X-Request-ID"] = request_id
        LOGGER.info(
            "request_complete method=%s path=%s status=%s request_id=%s",
            request.method,
            request.url.path,
            response.status_code,
            request_id,
        )
        return response

    async def http_exception_handler(request: Request, exc: HTTPException):
        detail = exc.detail if isinstance(exc.detail, dict) else {}
        return JSONResponse(
            status_code=exc.status_code,
            content=_error_content(
                request,
                detail.get("error", exc.__class__.__name__),
                detail.get("message", str(exc.detail)),
            ),
            headers=getattr(exc, "headers", None),
        )

    async def validation_error_handler(request: Request, exc: RequestValidationError):
        return JSONResponse(
            status_code=422,
            content=_error_content(
                request,
                "RequestValidationError",
                "Request validation failed.",
                details=jsonable_encoder(exc.errors()),
            ),
        )

    async def service_error_handler(request: Request, exc: Exception):
        return JSONResponse(
            status_code=_service_status(exc),
            content=_error_content(
                request,
                exc.__class__.__name__,
                str(exc),
            ),
        )

    app.add_exception_handler(HTTPException, http_exception_handler)
    app.add_exception_handler(RequestValidationError, validation_error_handler)
    for exc_type in backend_services.SERVICE_ERROR_TYPES:
        app.add_exception_handler(exc_type, service_error_handler)

    secured = [Depends(require_api_key)]

    @app.get("/", dependencies=secured, include_in_schema=False)
    @app.get(f"{API_PREFIX}", dependencies=secured, tags=["metadata"])
    def root(request: Request):
        return backend_services.backend_metadata(
            settings,
            request_id=request.state.request_id,
        )

    @app.get("/live", include_in_schema=False)
    @app.get(f"{API_PREFIX}/live", tags=["probes"])
    def live(request: Request):
        return backend_services.liveness(
            settings,
            request_id=request.state.request_id,
        )

    @app.get("/ready", include_in_schema=False)
    @app.get(f"{API_PREFIX}/ready", tags=["probes"])
    def ready(request: Request):
        response = backend_services.readiness(
            settings,
            request_id=request.state.request_id,
        )
        return JSONResponse(
            status_code=backend_services.readiness_status_code(response),
            content=response,
        )

    @app.get("/health", dependencies=secured, include_in_schema=False)
    @app.get(f"{API_PREFIX}/health", dependencies=secured, tags=["probes"])
    def health(request: Request):
        return backend_services.health(
            settings,
            request_id=request.state.request_id,
        )

    @app.get("/doctor", dependencies=secured, include_in_schema=False)
    @app.get(f"{API_PREFIX}/doctor", dependencies=secured, tags=["diagnostics"])
    def doctor_status(request: Request):
        return backend_services.doctor_status(
            settings,
            request_id=request.state.request_id,
        )

    @app.post("/reports/live", dependencies=secured, include_in_schema=False)
    @app.post(f"{API_PREFIX}/reports/live", dependencies=secured, tags=["reports"])
    def reports_live(payload: LiveReportRequest, request: Request):
        return backend_services.build_live_report(
            settings,
            _payload(payload),
            request_id=request.state.request_id,
        )

    @app.post("/reports/batch", dependencies=secured, include_in_schema=False)
    @app.post(f"{API_PREFIX}/reports/batch", dependencies=secured, tags=["reports"])
    def reports_batch(payload: BatchReportRequest, request: Request):
        return backend_services.build_batch_report(
            settings,
            _payload(payload),
            request_id=request.state.request_id,
        )

    @app.post("/comparisons/levels", dependencies=secured, include_in_schema=False)
    @app.post(
        f"{API_PREFIX}/comparisons/levels",
        dependencies=secured,
        tags=["comparisons"],
    )
    def comparisons_levels(payload: LevelComparisonRequest, request: Request):
        return backend_services.build_level_comparison(
            settings,
            _payload(payload),
            request_id=request.state.request_id,
        )

    @app.post("/comparisons/batches", dependencies=secured, include_in_schema=False)
    @app.post(
        f"{API_PREFIX}/comparisons/batches",
        dependencies=secured,
        tags=["comparisons"],
    )
    def comparisons_batches(payload: BatchComparisonRequest, request: Request):
        return backend_services.build_batch_comparison(
            settings,
            _payload(payload),
            request_id=request.state.request_id,
        )

    @app.post("/audit/live", dependencies=secured, include_in_schema=False)
    @app.post(f"{API_PREFIX}/audit/live", dependencies=secured, tags=["audit"])
    def audit_live(payload: LiveAuditRequest, request: Request):
        return backend_services.create_live_audit(
            settings,
            _payload(payload),
            request_id=request.state.request_id,
        )

    @app.post("/audit/batches", dependencies=secured, include_in_schema=False)
    @app.post(f"{API_PREFIX}/audit/batches", dependencies=secured, tags=["audit"])
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


def _configure_logging(settings):
    level = getattr(logging, settings.log_level.upper(), logging.INFO)
    logging.basicConfig(
        level=level,
        format="%(asctime)s %(levelname)s %(name)s %(message)s",
    )


def main():
    try:
        import uvicorn
    except ModuleNotFoundError as exc:  # pragma: no cover - dependency gate
        raise SystemExit(
            "FastAPI backend dependencies are not installed. "
            "Install with: python -m pip install -e .[api]"
        ) from exc

    settings = load_backend_settings()
    _configure_logging(settings)
    uvicorn.run(
        "backend_app:app",
        host=settings.host,
        port=settings.port,
        reload=False,
        log_level=settings.log_level.lower(),
    )


if __name__ == "__main__":
    main()
