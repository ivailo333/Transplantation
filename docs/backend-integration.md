# Backend Integration Guide

This guide describes how to run the HLA backend as a component of a larger application. The component remains strictly non-clinical and returns deterministic software artifacts only.

## Local Service

```powershell
python -m pip install -e .[api]
Copy-Item backend.env.example backend.env
hla-api
```

The service listens on `http://127.0.0.1:8000` by default. It automatically reads `backend.env` from the working directory. Set `HLA_BACKEND_ENV_FILE` to load another file.

## Versioned API Contract

Use `/v1` endpoints for new integrations:

- `GET /v1/live`: liveness probe; no database access.
- `GET /v1/ready`: readiness probe; returns `200` when ready and `503` when not ready.
- `GET /v1/health`: detailed health report; secured when `HLA_BACKEND_API_KEY` is set.
- `GET /v1/doctor`: full doctor diagnostics.
- `POST /v1/reports/live`: STEP 27 live report.
- `POST /v1/reports/batch`: STEP 27 batch report.
- `POST /v1/comparisons/levels`: STEP 28 level comparison.
- `POST /v1/comparisons/batches`: STEP 28 batch comparison.
- `POST /v1/audit/live`: live audit bundle.
- `POST /v1/audit/batches`: batch audit bundle.

Legacy unversioned endpoints still work, but they are hidden from the OpenAPI contract.

## Request Correlation

Send `X-Request-ID` from the larger application. The backend echoes it in the response header and includes it in JSON envelopes. If omitted, the backend creates a UUID.

```powershell
Invoke-RestMethod http://127.0.0.1:8000/v1/live -Headers @{
  'X-Request-ID' = 'demo-request-1'
}
```

## Authentication

If `HLA_BACKEND_API_KEY` is set, secured endpoints require `X-API-Key`. Probe endpoints `/v1/live` and `/v1/ready` are intentionally unauthenticated so orchestrators can use them.

```powershell
Invoke-RestMethod -Method Post http://127.0.0.1:8000/v1/reports/live `
  -Headers @{'X-API-Key'='replace-with-a-secret'; 'X-Request-ID'='demo-report-1'} `
  -ContentType 'application/json' `
  -Body '{"direction":"recipient","external_id":"RECIP-001","level":"lgx"}'
```

## Docker

Build the image:

```powershell
docker build -t hla-transplantation-backend .
```

Run with mounted SQLite data, exports, and py-ard data:

```powershell
docker run --rm -p 8000:8000 `
  --env-file backend.env `
  -v ${PWD}\data:/app/data `
  -v ${PWD}\exports:/app/exports `
  -v ${PWD}\pyard-data:/app/pyard-data:ro `
  hla-transplantation-backend
```

For Docker, set these values in `backend.env`:

```text
HLA_BACKEND_HOST=0.0.0.0
HLA_BACKEND_DATABASE_PATH=/app/data/transplant.db
HLA_BACKEND_EXPORT_DIR=/app/exports
```

## Production Notes

- Keep `backend.env`, SQLite databases, audit bundles, and py-ard data out of Git.
- Put the API behind TLS and a gateway controlled by the larger application.
- Store `HLA_BACKEND_API_KEY` or stronger credentials in a secret manager.
- Treat `/v1/ready` as orchestration status, not as clinical availability.
- Preserve audit bundles and request IDs for traceability.

## Boundary

This backend is an analytics/reporting component, not a clinical decision system. It must not be used to accept or reject donors, allocate organs, interpret crossmatch/DSA/eplets/cPRA, or determine transplant suitability without the required clinical validation, governance, and regulatory process.
