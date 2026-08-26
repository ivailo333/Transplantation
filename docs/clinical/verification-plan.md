# Проект На Verification Plan

Статус: Draft за планиране на клинична готовност. Не е одобрен за клинична употреба.

Този документ дефинира начална verification стратегия за текущия неклиничен
CLI/backend/frontend проект и за бъдещо използване като backend компонент в
по-голямо приложение. Това не е изпълнен verification report и не доказва
clinical validation.

## Цел

Verification трябва да отговори на въпроса: построен ли е софтуерът правилно
спрямо одобрените requirements и design controls? Този draft задава test IDs,
acceptance criteria, evidence expectations и връзки към risks, requirements и
architecture identifiers.

## Изходни Документи

- [Български Clinical Readiness Обзор](bg-readiness-overview.md)
- [Software Requirements Specification Draft](software-requirements.md)
- [Traceability Matrix Draft](traceability-matrix.md)
- [Software Architecture Draft](software-architecture.md)
- [Risk Management And Initial Risk Register](risk-register.md)
- [Software Lifecycle Draft](software-lifecycle.md)
- [Frontend Prototype Draft](frontend-prototype.md)
- [Backend API Component](../backend.md)
- [Backend Integration Guide](../backend-integration.md)

Официални външни references, проверени на 2026-08-26:

- IEC 62304:2006, Medical device software - software life cycle processes:
  https://committee.iso.org/standard/38421.html
- ISO 14971:2019, Medical devices - application of risk management:
  https://www.iso.org/standard/72704.html
- IEC 62366-1:2015, Medical devices - usability engineering:
  https://webstore.iec.ch/en/publication/21863
- European Commission MDCG guidance index for MDR/IVDR:
  https://health.ec.europa.eu/medical-devices-sector/new-regulations/guidance-mdcg-endorsed-documents-and-other-guidance_en

## Verification Scope

Current verification scope:

- CLI routing, output boundaries and backward compatibility;
- HLA validation, reduction and deterministic comparison;
- SQLite schema, migrations and persistence behavior;
- batch workflows, ranking and selection;
- STEP 24-28 matrices, summaries, statistics, reports and comparisons;
- deterministic JSON/CSV/HTML/text exports;
- audit bundle creation and metadata;
- FastAPI backend `/v1` API, request IDs, structured errors and OpenAPI;
- frontend static assets, browser logic and local proxy smoke behavior;
- documentation/claims boundary checks.

Out of current verification scope:

- clinical validation;
- production clinical deployment;
- RBAC/session management;
- LIS/EHR/FHIR/HL7 integrations;
- identifiable patient/donor/recipient data governance;
- cybersecurity penetration testing;
- usability summative validation;
- clinical release approval.

## Verification Methods

| Code | Method | Use |
| --- | --- | --- |
| UNIT | Unit or focused module tests | Deterministic functions, validation, comparison, export helpers |
| INT | Integration tests | CLI/backend/database/API workflows |
| SYS | System smoke tests | End-to-end local backend/frontend checks |
| STATIC | Static checks | Compilation, syntax, whitespace, link and controlled-symbol checks |
| REVIEW | Documented review | Claims, architecture, code, security, QMS and risk-control review |
| VAL-LINK | Validation linkage | Evidence placeholder for tasks requiring future usability/clinical validation |

## General Acceptance Criteria

Before a controlled release candidate can be considered, verification evidence
must show:

1. All requirements planned for the release have assigned verification methods.
2. All automated tests pass in a clean environment.
3. `git diff --check` and relevant syntax/compile checks pass.
4. `/v1` OpenAPI contract exposes only intended versioned endpoints for new
   integrations.
5. API responses preserve `schema`, `request_id`, `clinical: false` and
   non-clinical notice where applicable.
6. No API, report, frontend label or documentation change adds unapproved
   clinical claims.
7. Audit bundle evidence is reproducible from controlled inputs.
8. Runtime databases, exports, logs, secrets and identifiable data are excluded
   from source control.
9. Known gaps are listed with risk impact and release decision.

## Verification Test Matrix

| ID | Verification item | Requirement links | Architecture links | Risk links | Method | Current evidence |
| --- | --- | --- | --- | --- | --- | --- |
| VER-001 | Repository hygiene and source-control exclusions | DATA-006, SEC-001 | ARCH-013 | RM-014, RM-021, RM-024 | STATIC, REVIEW | `.gitignore`, `git status --ignored`, `git diff --check` |
| VER-002 | CLI root help and command routing | CLM-001, CLM-003 | ARCH-001 | RM-009, RM-018, RM-025 | INT | `tests/test_cli.py`, `tests/test_command_cli_step*.py` |
| VER-003 | Database schema and migrations | API-004, API-005, OPS-002 | ARCH-006 | RM-012, RM-024 | UNIT, INT | `tests/test_database.py`, `tests/test_migrations.py`, STEP 20 tests |
| VER-004 | HLA validation and import handling | DATA-003, DATA-004 | ARCH-004, ARCH-006 | RM-001, RM-003, RM-006 | UNIT, INT | `tests/test_validation.py`, `tests/test_importers.py`, typing tests |
| VER-005 | Reduction and deterministic pair comparison | DATA-003, FUNC-001, FUNC-002 | ARCH-004, ARCH-005 | RM-005, RM-006 | UNIT | `tests/test_reduction.py`, `tests/test_comparison.py` |
| VER-006 | Analysis persistence and role safety | DATA-002, DATA-005 | ARCH-006 | RM-002, RM-022 | UNIT, INT | `tests/test_analyses.py`, subject/typing tests |
| VER-007 | Batch execution, selection, ranking and history | FUNC-001, FUNC-005 | ARCH-007 | RM-006, RM-011, RM-025 | UNIT, INT | `tests/test_batch_*.py`, STEP 18-22 tests |
| VER-008 | STEP 24-26 matrix, summary and statistics views | FUNC-001, FUNC-004 | ARCH-005 | RM-006, RM-007 | UNIT, INT | `tests/test_hla_matrix*.py`, `tests/test_mismatch_summary*.py`, `tests/test_comparison_statistics*.py` |
| VER-009 | STEP 27 report generation and export behavior | FUNC-001, FUNC-004, DATA-005 | ARCH-008 | RM-004, RM-006, RM-007, RM-008, RM-025 | UNIT, INT | `tests/test_step27_reporting.py`, persistent/routing tests |
| VER-010 | STEP 28 report comparison and export behavior | FUNC-002, FUNC-004 | ARCH-008 | RM-005, RM-006, RM-007, RM-025 | UNIT, INT | `tests/test_step28_report_comparison.py`, batch/routing tests |
| VER-011 | Audit bundle reproducibility | FUNC-003, AUD-001 | ARCH-009 | RM-007, RM-008, RM-021 | UNIT, INT | `tests/test_audit_bundle.py`, backend service audit tests |
| VER-012 | Backend service envelopes and readiness | API-002, API-004, API-006 | ARCH-003 | RM-008, RM-009, RM-016, RM-017 | UNIT, INT | `tests/test_backend_services.py` |
| VER-013 | FastAPI contract, authentication and structured errors | API-001, API-003, API-005, API-006 | ARCH-002 | RM-009, RM-012, RM-013, RM-017, RM-024 | INT | `tests/test_backend_app.py` |
| VER-014 | Frontend static syntax and Bulgarian UI boundary | CLM-001, UI-001, UI-005, UI-006 | ARCH-010 | RM-010, RM-011, RM-020, RM-025 | STATIC, REVIEW | `frontend/index.html`, `frontend/app.js`, HTML/JS syntax checks |
| VER-015 | Frontend proxy and local end-to-end smoke | UI-002, UI-003 | ARCH-010, ARCH-011 | RM-016, RM-017, RM-022 | SYS | Local `/api/live`, `/api/reports/live`, `/api/comparisons/levels` smoke checks |
| VER-016 | Export parity across JSON/CSV/HTML/text/API/audit | FUNC-004, AUD-001 | ARCH-008, ARCH-009 | RM-007, RM-008 | UNIT, INT | Existing export tests; parity matrix still needs baseline |
| VER-017 | Claims and labeling review | CLM-001, CLM-002, CLM-003, FUNC-005, UI-005 | ARCH-002, ARCH-008, ARCH-010 | RM-005, RM-009, RM-010, RM-011, RM-018, RM-025 | REVIEW, VAL-LINK | Draft docs and Bulgarian UI; formal review not complete |
| VER-018 | Data governance and PHI/secrets exclusion | DATA-001, DATA-006, SEC-001 | ARCH-006, ARCH-013 | RM-014, RM-021 | STATIC, REVIEW | `.gitignore`, data policy; controlled scan not complete |
| VER-019 | Dependency/SOUP and vulnerability review | SEC-004, AUD-002 | ARCH-013 | RM-004, RM-015 | REVIEW | `pyproject.toml`, `requirements*.txt`, Dockerfile; SOUP register not complete |
| VER-020 | Operational readiness and deployment smoke | OPS-001, OPS-002, SEC-003 | ARCH-002, ARCH-003, ARCH-013, ARCH-014 | RM-012, RM-016, RM-024 | SYS, REVIEW | Local probes and Docker docs; production runbook missing |
| VER-021 | Future integration contract | INT-001, INT-002 | ARCH-014, ARCH-015 | RM-001, RM-002, RM-004, RM-009, RM-018, RM-022, RM-023 | INT, REVIEW | Backend integration guide; formal downstream contract missing |
| VER-022 | Clinical workflow human oversight | CLM-004, UI-006, VAL-004 | ARCH-010, ARCH-014 | RM-010, RM-018, RM-023 | SYS, VAL-LINK | Frontend approval button disabled; clinical sign-off workflow missing |
| VER-023 | Validation dataset representativeness | VAL-002 | ARCH-012 | RM-019 | REVIEW, VAL-LINK | Not started beyond requirement identification |
| VER-024 | Usability and use-error controls | VAL-003, UI-001, UI-004, UI-005 | ARCH-010, ARCH-014 | RM-010, RM-011, RM-020, RM-025 | REVIEW, VAL-LINK | Prototype UI warnings; usability file not started |

## Current Automated Check Set

The current repository can use this non-clinical verification command set:

```powershell
git diff --check
python -B -c "from pathlib import Path; compile(Path('frontend/serve.py').read_text(encoding='utf-8'), 'frontend/serve.py', 'exec')"
node --check .\frontend\app.js
python -B -c "from html.parser import HTMLParser; from pathlib import Path; HTMLParser().feed(Path('frontend/index.html').read_text(encoding='utf-8'))"
python -m unittest discover -s tests
```

For backend/frontend local smoke checks:

```powershell
hla-api
python .\frontend\serve.py
Invoke-WebRequest -UseBasicParsing http://127.0.0.1:4173/
Invoke-WebRequest -UseBasicParsing http://127.0.0.1:4173/api/live
```

## Verification Evidence Record Template

Each controlled verification run should record:

- verification run ID;
- software version / commit SHA;
- environment and operating system;
- Python version and dependency versions;
- database fixture or dataset identifier;
- py-ard and IPD-IMGT/HLA data version;
- commands executed;
- pass/fail result;
- deviations and anomalies;
- linked requirements, risks and architecture IDs;
- reviewer and approval status.

## Handling Failures And Deviations

Any failed verification item must be triaged before release. The triage record
should include:

- affected requirements;
- affected risks and severity;
- reproducibility steps;
- root cause or investigation status;
- corrective action;
- regression test expectation;
- release impact decision.

For clinical-intended development, unresolved safety-related failures must block
release until reviewed and accepted through the controlled QMS process.

## Verification Vs Validation Boundary

This plan covers verification planning. It does not establish clinical
validation. Items marked `VAL-LINK` require future usability or clinical workflow
validation evidence, especially where user interpretation, human oversight,
clinical workflow or representative case coverage is involved.

## Step 8 Completion Criteria

Step 8 is complete at planning level when:

- architecture components and interfaces have IDs;
- verification items have `VER-*` IDs;
- requirements, risks and architecture IDs are linked to verification methods;
- current automated evidence and gaps are visible;
- lifecycle and traceability documents point to the new architecture and
  verification artifacts.

## Next Readiness Work

The next readiness step should create usability engineering and validation
planning artifacts. Those documents should define representative users, intended
clinical workflow tasks, foreseeable use errors, validation datasets, acceptance
criteria and clinical stakeholder review gates.
