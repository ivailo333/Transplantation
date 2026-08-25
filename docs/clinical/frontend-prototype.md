# Frontend Prototype Draft

Status: Draft for clinical-readiness planning. Not approved for clinical use.

This document defines the initial non-clinical frontend prototype added in step
6. The prototype is a browser-based validation console for the backend API
component and is not a production clinical user interface.

## Source Documents

Internal source documents reviewed for this draft:

- [Intended Use](intended-use.md)
- [Regulatory Classification Draft](regulatory-classification.md)
- [Quality System Draft](quality-system.md)
- [Risk Management And Initial Risk Register](risk-register.md)
- [Software Lifecycle Draft](software-lifecycle.md)
- [Backend API Component](../backend.md)
- [Backend Integration Guide](../backend-integration.md)
- [Data Policy](../data.md)

## Prototype Location

The prototype source is stored in `frontend/`.

Key files:

- `frontend/index.html`: validation console markup.
- `frontend/styles.css`: responsive operational UI styling.
- `frontend/app.js`: browser logic for backend API calls and local review notes.
- `frontend/serve.py`: static development server and `/api/*` proxy to backend
  `/v1` endpoints.
- `frontend/README.md`: local run instructions.

## Scope

The prototype supports the following non-clinical workflow:

- backend liveness and readiness probes;
- donor-side or recipient-side case parameter entry;
- STEP 27 live report creation through `/v1/reports/live`;
- STEP 28 representation-level comparison through `/v1/comparisons/levels`;
- reproducible live audit bundle creation through `/v1/audit/live`;
- raw JSON response review;
- local-only validation notes.

The prototype is intended to help developers, technical evaluators, and
validation personnel inspect backend behavior during integration planning.

## Non-Intended Uses

The prototype must not be used for:

- clinical donor acceptance or rejection;
- organ allocation, prioritization, or waitlist decision-making;
- virtual crossmatch interpretation;
- DSA, MFI, unacceptable antigen, cPRA, eplet, or PIRCHE interpretation;
- graft outcome prediction;
- treatment recommendation;
- autonomous or semi-autonomous clinical decision support;
- storage of clinical approval or final clinical sign-off.

The visible UI includes a non-clinical status boundary and intentionally keeps
the clinical approval control disabled.

## Backend Dependency

The prototype depends on the backend API component being available. The default
proxy target is:

```text
http://127.0.0.1:8000/v1
```

The target can be overridden with `HLA_FRONTEND_BACKEND_URL`.

Local startup:

```powershell
hla-api
python .\frontend\serve.py
```

Open:

```text
http://127.0.0.1:4173/
```

## Safety And Claims Controls

The prototype includes these initial controls:

- explicit non-clinical labeling in the first screen;
- no clinical approval persistence;
- disabled clinical-use approval button;
- local-only reviewer note storage;
- raw backend response panel for traceability during validation;
- same-origin frontend proxy so browser calls do not require a separate CORS
  configuration during local evaluation;
- no scoring, recommendation, or acceptance/rejection language.

These controls are not sufficient for clinical release. They are planning and
prototype controls only.

## Usability Validation Notes

Future usability work should define and test user tasks before clinical use is
considered. Initial candidate tasks:

- verify backend readiness before reviewing a case;
- enter a donor or recipient identifier and create a report;
- compare representation levels and identify where deterministic software
  outputs differ;
- create an audit bundle and confirm its file manifest;
- record validation observations without implying clinical approval.

Usability validation must include representative intended users, realistic
workflow constraints, and documented pass/fail criteria.

## Data Governance Notes

The prototype is limited to synthetic, demo, anonymized, or validation-planning
records. Any use with identifiable donor, recipient, or patient data requires an
approved governance process, access controls, retention rules, audit review, and
legal basis for processing before data is entered into the system.

## Open Items Before Clinical Use

Before this can become part of a clinical workflow, the project still needs at
least:

- formally approved intended use and claims;
- regulatory classification confirmation;
- controlled software requirements linked to risk controls;
- role-based authentication and authorization;
- validated audit trail and retention behavior;
- clinical workflow hazard analysis;
- cybersecurity risk assessment;
- usability engineering file and formative/summative validation;
- verification and validation protocol with objective acceptance criteria;
- production deployment architecture and operational procedures;
- approved release, change-control, incident, and post-market processes.
