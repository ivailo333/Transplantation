# Проект На Матрица За Проследимост

Статус: Draft за планиране на клинична готовност. Не е одобрен за клинична употреба.

Тази matrix свързва текущия intended use, началния risk register, software requirements, implementation references и evidence, които все още са нужни преди да се разглежда каквато и да е clinical workflow употреба.

## Цел

Traceability трябва да показва, че всяка safety-related или quality-critical тема е свързана с requirements, design, implementation, verification, validation и release evidence. Този draft започва структурата; той все още не е controlled traceability file.

## Изходни Документи

- [Intended Use](intended-use.md)
- [Risk Management And Initial Risk Register](risk-register.md)
- [Software Requirements Specification Draft](software-requirements.md)
- [Software Lifecycle Draft](software-lifecycle.md)
- [Frontend Prototype Draft](frontend-prototype.md)
- [Backend API Component](../backend.md)
- [Backend Integration Guide](../backend-integration.md)
- [Data Policy](../data.md)

## Traceability Полета

| Поле | Значение |
| --- | --- |
| Risk | Risk ID от initial risk register. |
| Requirement links | Software requirements, които implement или plan related controls. |
| Current references | Текущи repository files или documents, свързани с controls. |
| Verification evidence | Tests или review evidence, нужни за verification на implementation. |
| Validation evidence | Workflow/user evidence, нужна когато clinical или usability context е засегнат. |
| Gap status | Текущ gap преди clinical use. |

## Матрица Риск Към Изискване

| Риск | Връзки към изисквания | Текущи references | Verification evidence | Validation evidence | Gap status |
| --- | --- | --- | --- | --- | --- |
| RM-001 Incorrect HLA typing data | DATA-002, DATA-003, UI-003, INT-002 | `hla_validation.py`, `typings.py`, `importers.py`, `frontend/` | Import validation tests; invalid allele tests; API report fixtures | Case-entry validation study; source-data review workflow | Partial controls present; clinical source traceability not defined |
| RM-002 Donor/recipient identity mix-up | DATA-002, UI-001, INT-002 | `subjects.py`, `backend_services.py`, `frontend/index.html` | Direction/role tests; API request fixtures; UI smoke tests | Representative user task for donor/recipient review | Role labels present; clinical confirmation workflow missing |
| RM-003 Missing or partial HLA data | DATA-004, UI-004 | `step27_reporting.py`, `frontend-prototype.md` | Missing-data fixture tests; report warning tests | Usability validation for incomplete case handling | Planned; explicit UI warnings not fully implemented |
| RM-004 Stale IMGT/HLA or py-ard data | DATA-005, AUD-002, SEC-004, INT-002 | `doctor.py`, `backend_services.py`, `audit_bundle.py` | Metadata tests; doctor checks; dependency review | User comprehension of version metadata | Version metadata present; dependency register not controlled |
| RM-005 Incorrect reduction interpretation | CLM-001, CLM-003, FUNC-002, UI-003 | `hla_reduction.py`, `step28_report_comparison.py`, `frontend/` | Level comparison tests; claims wording review | Usability task on level interpretation | Controls present; formal wording approval missing |
| RM-006 Software comparison defect | DATA-003, FUNC-001, FUNC-002, VAL-001 | `hla_comparison.py`, `hla_matrix.py`, `tests/` | Independent expected-case fixtures; regression tests | Clinical reviewer challenge cases | Unit coverage present; independent clinical fixtures missing |
| RM-007 Export/report mismatch | FUNC-003, FUNC-004 | `exporters.py`, `html_reports.py`, `audit_bundle.py` | Cross-format parity tests; audit manifest tests | Artifact review task during validation | Partial automated coverage; parity matrix not baselined |
| RM-008 Audit trail incomplete | DATA-005, API-002, FUNC-003, AUD-001, AUD-002 | `audit_bundle.py`, `backend_app.py`, `backend_services.py` | Audit bundle tests; metadata tests; release checklist | Audit investigation drill | Bundle present; clinical release record not defined |
| RM-009 API misuse as clinical decision engine | CLM-001, CLM-002, FUNC-002, INT-001, VAL-004 | `backend_app.py`, `docs/backend-integration.md`, `docs/clinical/intended-use.md` | API contract tests; OpenAPI review; claims review | Integration validation with downstream app | Non-clinical envelope present; integration contract not baselined |
| RM-010 Frontend UI implies recommendation | CLM-001, CLM-003, CLM-004, UI-005, UI-006, VAL-003 | `frontend/`, `frontend-prototype.md` | UI text review; visual state review; disabled approval test | Usability comprehension validation | Prototype control present; formal usability file missing |
| RM-011 Wrong sort/ranking interpretation | CLM-003, FUNC-005, UI-001, UI-005, VAL-003 | `step27_reporting.py`, `frontend/index.html`, `frontend/app.js` | Sort disclosure tests; report wording review | User task on sorted output interpretation | Prototype only; rank/sort labelling needs deeper validation |
| RM-012 Database schema mismatch | API-004, API-005, OPS-002, VAL-001 | `database.py`, `migrations.py`, `backend_services.py` | Migration tests; readiness tests; deployment dry run | Operator readiness workflow validation | Technical checks present; release gate not controlled |
| RM-013 Unauthorized access | API-003, API-004, SEC-001, SEC-002, SEC-003 | `backend_config.py`, `backend.env.example`, `backend_app.py` | Auth tests; security review; deployment review | Access review process validation | API key present; RBAC/TLS/production controls missing |
| RM-014 Identifiable clinical data without governance | DATA-001, DATA-006, SEC-001, SEC-002, SEC-003 | `.gitignore`, `docs/data.md`, `frontend-prototype.md` | Repo secret/PHI scan; config review | Data-governance approval workflow | Non-clinical policy present; clinical governance not approved |
| RM-015 Dependency vulnerability | AUD-002, SEC-004 | `pyproject.toml`, `requirements*.txt`, `Dockerfile` | Dependency audit; SBOM review; image scan | Release review of vulnerability decisions | Dependency list present; controlled monitoring not implemented |
| RM-016 Service unavailable during donor review | API-004, UI-002, OPS-001, OPS-002 | `backend_app.py`, `frontend/serve.py`, `frontend/app.js` | Probe tests; proxy error tests; deployment smoke tests | Downtime procedure simulation | Probes present; downtime SOP missing |
| RM-017 Error handling hides root cause | API-005, API-006, UI-002, OPS-001 | `backend_app.py`, `backend_services.py`, `frontend/app.js` | Error-path tests; log/request ID review | Support workflow validation | Structured errors present; support SOP missing |
| RM-018 Incorrect clinical expansion of scope | CLM-001, CLM-002, CLM-003, CLM-004, INT-001, VAL-004 | `docs/clinical/`, `backend_app.py`, `frontend/` | Claims matrix review; change-impact review | Clinical governance review | Draft controls present; formal claims approval missing |
| RM-019 Validation dataset bias | VAL-002 | `docs/clinical/software-requirements.md` | Dataset inventory review; edge-case checklist | Validation protocol/report with representative cases | Not started beyond requirement identification |
| RM-020 User training insufficient | CLM-001, DATA-001, VAL-003 | `README.md`, `docs/clinical/intended-use.md`, `frontend/` | Training material review; UI warning checks | Role-based competency assessment | Warnings present; training program missing |
| RM-021 Logs or audit bundles leak sensitive data | DATA-006, API-006, AUD-001, SEC-002, SEC-003 | `.gitignore`, `audit_bundle.py`, `backend_app.py` | Log review; export review; access-control test | Privacy workflow validation | Ignored files present; retention/access controls missing |
| RM-022 Concurrency or stale view issue | DATA-002, DATA-005, UI-001, UI-003, UI-004, INT-002 | `backend_services.py`, `step27_reporting.py`, `frontend/app.js` | Timestamp/request metadata tests; refresh tests | User stale-report recognition task | Metadata present; stale-view warning not complete |
| RM-023 Human oversight bypassed | CLM-002, CLM-004, API-003, INT-001, VAL-004 | `backend_app.py`, `frontend/index.html`, `docs/backend-integration.md` | API contract review; disabled approval test; integration tests | Human-signoff workflow validation | Prototype blocks approval; clinical sign-off process missing |
| RM-024 Incorrect environment configuration | API-005, OPS-001, OPS-002, SEC-001, SEC-003 | `backend_config.py`, `backend.env.example`, `Dockerfile` | Config tests; readiness tests; deployment checklist | Operator deployment rehearsal | Env examples present; production checklist not baselined |
| RM-025 Report language ambiguity | CLM-001, CLM-003, FUNC-005, UI-005, VAL-003 | `step27_reporting.py`, `step28_report_comparison.py`, `frontend/`, `docs/clinical/` | Report wording tests; claims review | User comprehension validation | Non-clinical wording present; formal label/claims review missing |

## Индекс Изискване Към Артефакт

| Група изисквания | Текущи implementation references | Основни липсващи evidence |
| --- | --- | --- |
| CLM claims controls | `README.md`, `docs/clinical/`, `backend_app.py`, `frontend/` | Claims matrix, clinical/regulatory approval, UI wording validation |
| DATA data controls | `database.py`, `subjects.py`, `typings.py`, `importers.py`, `.gitignore` | Clinical source traceability, missing-data requirements, data-governance approval |
| API service controls | `backend_app.py`, `backend_services.py`, `backend_config.py` | API contract tests, security review, production auth model |
| FUNC deterministic outputs | `step27_reporting.py`, `step28_report_comparison.py`, `audit_bundle.py`, `exporters.py` | Requirements-based regression suite, independent expected-case fixtures |
| UI workflow controls | `frontend/index.html`, `frontend/styles.css`, `frontend/app.js`, `frontend/serve.py` | Usability engineering file, workflow validation, accessibility review |
| AUD audit controls | `audit_bundle.py`, `backend_services.py` | Release metadata, retention policy, audit investigation rehearsal |
| SEC security controls | `backend_config.py`, `backend.env.example`, `.gitignore`, `Dockerfile` | RBAC, TLS, secrets management, vulnerability monitoring, SBOM |
| OPS operational controls | `backend_app.py`, `doctor.py`, `migrations.py`, `Dockerfile` | Deployment runbook, downtime SOP, rollback criteria |
| INT integration controls | `docs/backend-integration.md`, `backend_app.py` | Downstream integration contract, LIS/EHR/FHIR/HL7 design |
| VAL validation controls | `docs/clinical/software-requirements.md` | Validation plan, representative dataset, validation report |

## Критерии За Завършване На Стъпка 7

Този draft завършва step 7 на planning level, когато:

- всички начални рискове RM-001 до RM-025 имат поне един linked requirement;
- requirements включват текущите CLI/backend/frontend/audit controls и future clinical blockers;
- current implementation references са идентифицирани, когато са налични;
- verification и validation evidence gaps са видими;
- README и lifecycle documents сочат към новите requirements artifacts.

## Следваща Traceability Работа

Преди clinical-intended development да продължи:

1. Review и approval на requirement ID scheme.
2. Назначаване на requirement owners.
3. Прехвърляне на draft-а в избрания controlled traceability tool или format.
4. Добавяне на design IDs и test IDs след създаване на architecture и verification documents.
5. Clinical/regulatory/quality/software/security review.
6. Freeze на baseline преди formal validation execution.
