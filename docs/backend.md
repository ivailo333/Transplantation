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
hla-api
```

or:

```powershell
python -m backend_app
```

The default URL is `http://127.0.0.1:8000`. FastAPI exposes OpenAPI at `/openapi.json` and interactive docs at `/docs`.

## Environment

See `backend.env.example`.

Key settings:

- `HLA_BACKEND_DATABASE_PATH`: SQLite database path.
- `HLA_BACKEND_EXPORT_DIR`: base directory for audit/export artifacts created by API requests.
- `HLA_BACKEND_AUTO_MIGRATE`: if `true`, mutating migration is allowed before report/comparison/audit requests. Default is `false`.
- `HLA_BACKEND_API_KEY`: if set, requests must include `X-API-Key`.
- `HLA_BACKEND_CORS_ORIGINS`: comma-separated origins for browser clients.
- `HLA_BACKEND_HOST` / `HLA_BACKEND_PORT`: server bind settings for `hla-api`.

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

Validation, database, report/export, encoding, and filesystem IO failures are returned as structured JSON errors instead of unhandled tracebacks. Schema, migration, and IO failures map to `503`; missing records map to `404`; duplicate resources map to `409`; request and encoding issues map to `400`.

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

## Endpoints

- `GET /`: component metadata.
- `GET /health`: readiness, schema status, and doctor summary.
- `GET /doctor`: full doctor report.
- `POST /reports/live`: STEP 27 live report.
- `POST /reports/batch`: STEP 27 persistent batch report.
- `POST /comparisons/levels`: STEP 28 live level comparison.
- `POST /comparisons/batches`: STEP 28 persistent batch comparison.
- `POST /audit/live`: live audit bundle.
- `POST /audit/batches`: batch audit bundle.

## Example

```powershell
Invoke-RestMethod -Method Post http://127.0.0.1:8000/reports/live `
  -ContentType 'application/json' `
  -Body '{"direction":"recipient","external_id":"RECIP-001","level":"lgx"}'
```

## Boundary

This backend is ready to be embedded as an analytics/reporting component. It is not a clinical decision system and must not be used to accept/reject donors, rank patients, allocate organs, perform crossmatch interpretation, evaluate DSA/eplets/cPRA, or determine transplant suitability.
