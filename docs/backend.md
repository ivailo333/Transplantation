# Backend API Component

The backend API exposes the existing HLA comparison engine as a larger-application component. It remains strictly non-clinical: all endpoints return deterministic software artifacts, reports, comparisons, doctor checks, and audit bundles only.

## Install

```powershell
python -m pip install -e .[api]
```

For development and API tests:

```powershell
python -m pip install -e .[dev]
```

## Run

```powershell
Copy-Item backend.env.example backend.env
hla-api
```

or:

```powershell
python -m backend_app
```

The default URL is `http://127.0.0.1:8000`. FastAPI exposes OpenAPI at `/openapi.json` and interactive docs at `/docs`.

## Environment

The backend automatically reads `backend.env` from the working directory when it exists. Runtime environment variables override file values. Set `HLA_BACKEND_ENV_FILE` to require and load another file.

See `backend.env.example`.

Key settings:

- `HLA_BACKEND_ENV_FILE`: optional path to a backend env file.
- `HLA_BACKEND_DATABASE_PATH`: SQLite database path.
- `HLA_BACKEND_EXPORT_DIR`: base directory for audit/export artifacts created by API requests.
- `HLA_BACKEND_AUTO_MIGRATE`: if `true`, mutating migration is allowed before report/comparison/audit requests. Default is `false`.
- `HLA_BACKEND_API_KEY`: if set, secured endpoints must include `X-API-Key`.
- `HLA_BACKEND_CORS_ORIGINS`: comma-separated origins for browser clients.
- `HLA_BACKEND_HOST` / `HLA_BACKEND_PORT`: server bind settings for `hla-api`.
- `HLA_BACKEND_LOG_LEVEL`: Python/uvicorn log level. Default is `INFO`.

## Response Contract

Every successful service response uses this envelope:

```json
{
  "schema": "hla-backend-response-v1",
  "request_id": "...",
  "clinical": false,
  "notice": "NON-CLINICAL ...",
  "data": {}
}
```

The API echoes or creates an `X-Request-ID` response header. Send `X-Request-ID` from the larger application to correlate logs and audit events.

Validation, database, report/export, encoding, and filesystem IO failures are returned as structured JSON errors instead of unhandled tracebacks. Schema, migration, and IO failures map to `503`; missing records map to `404`; duplicate resources map to `409`; request and encoding issues map to `400`; request validation maps to `422`.

Structured errors use:

```json
{
  "schema": "hla-backend-api-v1",
  "request_id": "...",
  "clinical": false,
  "notice": "NON-CLINICAL ...",
  "error": "ErrorClass",
  "message": "Human readable message"
}
```

## Versioned Endpoints

New integrations should use `/v1`:

- `GET /v1`: component metadata.
- `GET /v1/live`: liveness probe; does not touch the database and does not require API key.
- `GET /v1/ready`: readiness probe; returns `200` when ready and `503` when not ready.
- `GET /v1/health`: readiness, schema status, and doctor summary.
- `GET /v1/doctor`: full doctor report.
- `POST /v1/reports/live`: STEP 27 live report.
- `POST /v1/reports/batch`: STEP 27 persistent batch report.
- `POST /v1/comparisons/levels`: STEP 28 live level comparison.
- `POST /v1/comparisons/batches`: STEP 28 persistent batch comparison.
- `POST /v1/audit/live`: live audit bundle.
- `POST /v1/audit/batches`: batch audit bundle.

Legacy unversioned endpoints remain available for backward compatibility, but are hidden from the OpenAPI contract.

## Example

```powershell
Invoke-RestMethod -Method Post http://127.0.0.1:8000/v1/reports/live `
  -Headers @{'X-API-Key'='replace-with-a-secret'; 'X-Request-ID'='demo-report-1'} `
  -ContentType 'application/json' `
  -Body '{"direction":"recipient","external_id":"RECIP-001","level":"lgx"}'
```

## Docker

```powershell
docker build -t hla-transplantation-backend .
docker run --rm -p 8000:8000 --env-file backend.env hla-transplantation-backend
```

Mount `transplant.db`, export storage, and `pyard-data/` for real deployments. See [Backend integration guide](backend-integration.md), [Cybersecurity Plan](clinical/cybersecurity-plan.md), [Data Governance Plan](clinical/data-governance.md), [SOUP And Dependency Register](clinical/soup-dependency-register.md), [Release And Deployment Plan](clinical/release-deployment-plan.md), [Maintenance Plan](clinical/maintenance-plan.md), and [Problem Resolution And CAPA Plan](clinical/problem-resolution-capa.md).

## Boundary

This backend is ready to be embedded as an analytics/reporting component. It is not a clinical decision system and must not be used to accept/reject donors, rank patients, allocate organs, perform crossmatch interpretation, evaluate DSA/eplets/cPRA, or determine transplant suitability.
