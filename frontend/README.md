# Frontend Prototype

Status: Non-clinical validation prototype. Not approved for clinical use.

This directory contains a dependency-free browser prototype for reviewing the
backend API component during integration planning. It is intended for synthetic,
demo, anonymized, or validation-planning data only.

Start the backend first:

```powershell
hla-api
```

Then start the frontend proxy:

```powershell
python .\frontend\serve.py
```

Open `http://127.0.0.1:4173/`.

The frontend server serves static files from this directory and proxies `/api/*`
requests to the backend `/v1` API. Override the backend URL with
`HLA_FRONTEND_BACKEND_URL`, for example:

```powershell
$env:HLA_FRONTEND_BACKEND_URL = "http://127.0.0.1:8000/v1"
python .\frontend\serve.py
```
