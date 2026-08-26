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
- [Software Architecture Draft](software-architecture.md)
- [Verification Plan Draft](verification-plan.md)
- [Usability Engineering File Draft](usability-engineering.md)
- [Validation Plan Draft](validation-plan.md)
- [Cybersecurity Plan Draft](cybersecurity-plan.md)
- [Data Governance Plan Draft](data-governance.md)
- [SOUP And Dependency Register Draft](soup-dependency-register.md)
- [Release And Deployment Plan Draft](release-deployment-plan.md)
- [Maintenance Plan Draft](maintenance-plan.md)
- [Problem Resolution And CAPA Plan Draft](problem-resolution-capa.md)
- [Document Control Index Draft](document-control-index.md)
- [Approval Matrix Draft](approval-matrix.md)
- [Claims Control Matrix Draft](claims-control-matrix.md)
- [Change Impact Checklist Draft](change-impact-checklist.md)
- [Clinical Readiness Gate Checklist Draft](clinical-readiness-gate-checklist.md)
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
| RM-005 Incorrect reduction interpretation | CLM-001, CLM-003, CLM-005, FUNC-002, UI-003 | `hla_reduction.py`, `step28_report_comparison.py`, `frontend/` | Level comparison tests; claims wording review | Usability task on level interpretation | Controls present; formal wording approval missing |
| RM-006 Software comparison defect | DATA-003, FUNC-001, FUNC-002, VAL-001 | `hla_comparison.py`, `hla_matrix.py`, `tests/` | Independent expected-case fixtures; regression tests | Clinical reviewer challenge cases | Unit coverage present; independent clinical fixtures missing |
| RM-007 Export/report mismatch | FUNC-003, FUNC-004 | `exporters.py`, `html_reports.py`, `audit_bundle.py` | Cross-format parity tests; audit manifest tests | Artifact review task during validation | Partial automated coverage; parity matrix not baselined |
| RM-008 Audit trail incomplete | DATA-005, API-002, FUNC-003, AUD-001, AUD-002, OPS-003, OPS-005, OPS-006 | `audit_bundle.py`, `backend_app.py`, `backend_services.py` | Audit bundle tests; metadata tests; release checklist | Audit investigation drill | Bundle present; clinical release record not defined |
| RM-009 API misuse as clinical decision engine | CLM-001, CLM-002, CLM-005, FUNC-002, INT-001, OPS-008, VAL-004 | `backend_app.py`, `docs/backend-integration.md`, `docs/clinical/intended-use.md` | API contract tests; OpenAPI review; claims review | Integration validation with downstream app | Non-clinical envelope present; integration contract not baselined |
| RM-010 Frontend UI implies recommendation | CLM-001, CLM-003, CLM-004, CLM-005, UI-005, UI-006, OPS-008, VAL-003 | `frontend/`, `frontend-prototype.md` | UI text review; visual state review; disabled approval test | Usability comprehension validation | Prototype control and usability file draft present; formal usability validation/claims approval missing |
| RM-011 Wrong sort/ranking interpretation | CLM-003, FUNC-005, UI-001, UI-005, VAL-003 | `step27_reporting.py`, `frontend/index.html`, `frontend/app.js` | Sort disclosure tests; report wording review | User task on sorted output interpretation | Prototype only; rank/sort labelling needs deeper validation |
| RM-012 Database schema mismatch | API-004, API-005, OPS-002, OPS-003, OPS-004, VAL-001 | `database.py`, `migrations.py`, `backend_services.py` | Migration tests; readiness tests; deployment dry run | Operator readiness workflow validation | Technical checks and gate checklist draft present; release gate not approved/enforced |
| RM-013 Unauthorized access | API-003, API-004, SEC-001, SEC-002, SEC-003, OPS-007 | `backend_config.py`, `backend.env.example`, `backend_app.py` | Auth tests; security review; deployment review | Access review process validation | API key present; RBAC/TLS/production controls missing |
| RM-014 Identifiable clinical data without governance | DATA-001, DATA-006, SEC-001, SEC-002, SEC-003, OPS-007, OPS-008 | `.gitignore`, `docs/data.md`, `frontend-prototype.md` | Repo secret/PHI scan; config review | Data-governance approval workflow | Non-clinical policy present; clinical governance not approved |
| RM-015 Dependency vulnerability | AUD-002, SEC-004, OPS-003, OPS-007 | `pyproject.toml`, `requirements*.txt`, `Dockerfile` | Dependency audit; SBOM review; image scan | Release review of vulnerability decisions | Dependency list present; controlled monitoring not implemented |
| RM-016 Service unavailable during donor review | API-004, UI-002, OPS-001, OPS-002, OPS-003, OPS-004 | `backend_app.py`, `frontend/serve.py`, `frontend/app.js` | Probe tests; proxy error tests; deployment smoke tests | Downtime procedure simulation | Probes and release/deployment draft present; downtime SOP not approved/rehearsed |
| RM-017 Error handling hides root cause | API-005, API-006, UI-002, OPS-001, OPS-004, OPS-005 | `backend_app.py`, `backend_services.py`, `frontend/app.js` | Error-path tests; log/request ID review | Support workflow validation | Structured errors and problem-resolution draft present; support SOP not approved/enforced |
| RM-018 Incorrect clinical expansion of scope | CLM-001, CLM-002, CLM-003, CLM-004, CLM-005, INT-001, OPS-006, OPS-007, OPS-008, VAL-004 | `docs/clinical/`, `backend_app.py`, `frontend/` | Claims matrix review; change-impact review | Clinical governance review | Draft controls present; formal claims approval missing |
| RM-019 Validation dataset bias | VAL-002 | `docs/clinical/software-requirements.md` | Dataset inventory review; edge-case checklist | Validation protocol/report with representative cases | Validation and data-governance drafts present; representative dataset not approved |
| RM-020 User training insufficient | CLM-001, CLM-005, DATA-001, OPS-008, VAL-003 | `README.md`, `docs/clinical/intended-use.md`, `frontend/` | Training material review; UI warning checks | Role-based competency assessment | Warnings present; training program missing |
| RM-021 Logs or audit bundles leak sensitive data | DATA-006, API-006, AUD-001, SEC-002, SEC-003, OPS-005, OPS-007 | `.gitignore`, `audit_bundle.py`, `backend_app.py` | Log review; export review; access-control test | Privacy workflow validation | Ignored files present; retention/access controls missing |
| RM-022 Concurrency or stale view issue | DATA-002, DATA-005, UI-001, UI-003, UI-004, INT-002 | `backend_services.py`, `step27_reporting.py`, `frontend/app.js` | Timestamp/request metadata tests; refresh tests | User stale-report recognition task | Metadata present; stale-view warning not complete |
| RM-023 Human oversight bypassed | CLM-002, CLM-004, CLM-005, API-003, INT-001, OPS-008, VAL-004 | `backend_app.py`, `frontend/index.html`, `docs/backend-integration.md` | API contract review; disabled approval test; integration tests | Human-signoff workflow validation | Prototype blocks approval; clinical sign-off process missing |
| RM-024 Incorrect environment configuration | API-005, OPS-001, OPS-002, OPS-003, OPS-004, OPS-005, OPS-006, OPS-007, SEC-001, SEC-003 | `backend_config.py`, `backend.env.example`, `Dockerfile` | Config tests; readiness tests; deployment checklist | Operator deployment rehearsal | Env examples present; production checklist not baselined |
| RM-025 Report language ambiguity | CLM-001, CLM-003, CLM-005, FUNC-005, UI-005, OPS-007, VAL-003 | `step27_reporting.py`, `step28_report_comparison.py`, `frontend/`, `docs/clinical/` | Report wording tests; claims review | User comprehension validation | Non-clinical wording present; formal label/claims review missing |

## Индекс Изискване Към Артефакт

| Група изисквания | Текущи implementation references | Основни липсващи evidence |
| --- | --- | --- |
| CLM claims controls | `README.md`, `docs/clinical/`, `docs/clinical/claims-control-matrix.md`, `backend_app.py`, `frontend/` | Approved claims matrix, clinical/regulatory approval, UI wording validation |
| DATA data controls | `database.py`, `subjects.py`, `typings.py`, `importers.py`, `.gitignore`, `docs/clinical/data-governance.md` | Clinical source traceability, missing-data requirements, data-governance approval |
| API service controls | `backend_app.py`, `backend_services.py`, `backend_config.py` | API contract tests, security review, production auth model |
| FUNC deterministic outputs | `step27_reporting.py`, `step28_report_comparison.py`, `audit_bundle.py`, `exporters.py` | Requirements-based regression suite, independent expected-case fixtures |
| UI workflow controls | `frontend/index.html`, `frontend/styles.css`, `frontend/app.js`, `frontend/serve.py` | Usability engineering file, workflow validation, accessibility review |
| AUD audit controls | `audit_bundle.py`, `backend_services.py` | Release metadata, retention policy, audit investigation rehearsal |
| SEC security controls | `backend_config.py`, `backend.env.example`, `.gitignore`, `Dockerfile`, `docs/clinical/cybersecurity-plan.md`, `docs/clinical/soup-dependency-register.md` | RBAC, threat model, secrets management, SBOM, vulnerability monitoring and security test evidence |
| OPS operational controls | `backend_app.py`, `doctor.py`, `migrations.py`, `Dockerfile`, `docs/clinical/release-deployment-plan.md`, `docs/clinical/maintenance-plan.md`, `docs/clinical/problem-resolution-capa.md`, `docs/clinical/document-control-index.md`, `docs/clinical/approval-matrix.md`, `docs/clinical/change-impact-checklist.md`, `docs/clinical/clinical-readiness-gate-checklist.md` | Release approval, deployment runbook, downtime SOP, rollback, maintenance, CAPA, document-control, approval and gate controls |
| INT integration controls | `docs/backend-integration.md`, `backend_app.py` | Downstream integration contract, LIS/EHR/FHIR/HL7 design |
| VAL validation controls | `docs/clinical/software-requirements.md`, `docs/clinical/validation-plan.md`, `docs/clinical/data-governance.md` | Representative dataset governance, validation execution, validation report |


## Step 8 Architecture And Verification Links

| Requirement group | Architecture links | Verification links | Remaining evidence gap |
| --- | --- | --- | --- |
| CLM | ARCH-002, ARCH-003, ARCH-008, ARCH-010, SAD-001, SAD-004, SAD-006 | VER-002, VER-012, VER-013, VER-014, VER-017 | Formal claims matrix and clinical/regulatory sign-off |
| DATA | ARCH-004, ARCH-006, ARCH-008, IF-003, IF-005, DF-001, DF-002 | VER-003, VER-004, VER-006, VER-018 | Clinical source-data governance and missing-data UI validation |
| API | ARCH-002, ARCH-003, ARCH-011, IF-002, IF-006, IF-007 | VER-012, VER-013, VER-015, VER-020 | Production auth, TLS/gateway and deployment runbook |
| FUNC | ARCH-005, ARCH-007, ARCH-008, DF-001, DF-002, DF-003 | VER-005, VER-007, VER-008, VER-009, VER-010, VER-016 | Independent expected-case fixtures and parity baseline |
| UI | ARCH-010, ARCH-011, DF-005, SAD-004, SAD-006 | VER-014, VER-015, VER-017, VER-022, VER-024 | Usability engineering file and user comprehension evidence |
| AUD | ARCH-009, IF-004, DF-004, SAD-005 | VER-011, VER-016, VER-018 | Retention policy and audit investigation rehearsal |
| SEC | ARCH-002, ARCH-013, ARCH-014, IF-006, IF-009, SAD-007 | VER-017, VER-018, VER-019, VER-020 | RBAC, secrets management, SBOM and cybersecurity risk assessment |
| OPS | ARCH-002, ARCH-003, ARCH-013, ARCH-014, SAD-003 | VER-012, VER-013, VER-020 | Downtime SOP, monitoring, rollback and support escalation |
| INT | ARCH-014, ARCH-015, IF-009, DF-006, SAD-007 | VER-021, VER-022 | Downstream integration contract and LIS/EHR/FHIR/HL7 design |
| VAL | ARCH-012 | VER-023, VER-024 | Representative validation dataset, usability plan and validation report |

## Критерии За Завършване На Стъпка 7

Този draft завършва step 7 на planning level, когато:

- всички начални рискове RM-001 до RM-025 имат поне един linked requirement;
- requirements включват текущите CLI/backend/frontend/audit controls и future clinical blockers;
- current implementation references са идентифицирани, когато са налични;
- verification и validation evidence gaps са видими;
- README и lifecycle documents сочат към новите requirements artifacts.



## Step 9 Usability And Validation Links

| Requirement group | Usability links | Validation links | Remaining evidence gap |
| --- | --- | --- | --- |
| CLM | USE-001, USE-002, UTASK-001, UERR-001 | VSCN-001, VACC-001, VACC-002 | Formal claims review and user comprehension evidence |
| DATA | USE-003, USE-005, UTASK-003, UTASK-004, UERR-002, UERR-003 | VDATA-002, VDATA-003, VSCN-003, VSCN-004, VACC-003, VACC-004 | Missing/stale data warning implementation and governed datasets |
| API | USE-001, USE-007, UTASK-002, UTASK-009, UERR-007 | VDATA-005, VSCN-002, VSCN-008, VACC-005 | Production auth and operational support process |
| FUNC | USE-002, USE-003, UTASK-005, UTASK-006, UERR-004, UERR-005 | VSCN-005, VSCN-006, VACC-002 | Independent expected-case fixtures and sort/ranking comprehension evidence |
| UI | USE-002, USE-003, USE-004, USE-005, UIE-004, UIE-005, UIE-007 | VSCN-001 through VSCN-010, VACC-001 through VACC-005 | Formative/summative usability execution not complete |
| AUD | USE-002, USE-006, UTASK-007, UERR-009 | VSCN-007, VACC-003, VACC-007 | Audit retention/access controls and investigation rehearsal |
| SEC | USE-007, UENV-003, UENV-004, UERR-009, UERR-010 | VSCN-012, VACC-007 | RBAC, PHI governance, cybersecurity and retention controls |
| OPS | USE-007, UENV-005, UTASK-002, UTASK-009, UERR-007 | VSCN-002, VSCN-008, VACC-005 | Downtime/degraded-mode validation and support SOP |
| INT | USE-003, USE-004, USE-005, UTASK-010, UERR-010 | VDATA-004, VSCN-010, VACC-008 | Downstream integration contract and clinical sign-off workflow |
| VAL | USE-003, USE-004, USE-005, UF-001 through UF-004 | VROLE-001 through VROLE-007, VDATA-001 through VDATA-005, VSCN-001 through VSCN-012, VACC-001 through VACC-008 | Formal validation execution and validation report not started |

## Критерии За Завършване На Стъпка 8 В Traceability

Стъпка 8 е отразена в тази matrix, когато:

- architecture documents са добавени като source records;
- requirement groups имат връзки към `ARCH-*`, `IF-*`, `DF-*` и `SAD-*`;
- verification plan е добавен като source record;
- requirement groups имат връзки към `VER-*` verification items;
- remaining evidence gaps са видими преди usability, validation и clinical release planning.


## Критерии За Завършване На Стъпка 9 В Traceability

Стъпка 9 е отразена в тази matrix, когато:

- usability engineering file е добавен като source record;
- validation plan е добавен като source record;
- requirement groups имат връзки към `USE-*`, `UTASK-*`, `UERR-*`, `UF-*`, `VROLE-*`, `VDATA-*`, `VSCN-*` и `VACC-*`;
- clinical-use blockers остават видими, защото validation execution и validation report не са изпълнени.

## Step 10 Cybersecurity Data Governance And SOUP Links

| Requirement group | Cybersecurity links | Data-governance links | SOUP/dependency links | Remaining evidence gap |
| --- | --- | --- | --- | --- |
| CLM | SECPLAN-001, CYTH-008 | DGOV-002 | SOUP release gate | Clinical claims and release approval still not baselined |
| DATA | SECPLAN-002, SECPLAN-007, ASSET-003, ASSET-006 | DCLASS-001 through DCLASS-008, DGOV-001 through DGOV-012 | SOUP-002, SOUP-003, SOUP-004 | Source-data provenance, retention and validation dataset governance not approved |
| API | SECPLAN-003, SECPLAN-004, SECPLAN-005, SECPLAN-006, SECPLAN-012, CYTH-001 through CYTH-003, CYTH-010 | DGOV-004, DGOV-005, DGOV-007 | SOUP-005, SOUP-006, SOUP-007, SOUP-008, SOUP-009 | Production RBAC, TLS/gateway and auth/session tests not implemented |
| FUNC | SECPLAN-008, CYTH-005, CYTH-006 | DGOV-005, DGOV-009 | SOUP-002, SOUP-003, SOUP-004 | Dependency/source-data update impact on deterministic outputs not baselined |
| UI | SECPLAN-003, SECPLAN-006, SECPLAN-007 | DGOV-004, DGOV-007, DGOV-010 | SOUP-017, SOUP-018 | Clinical UI auth, browser support and PHI-safe display rules not validated |
| AUD | SECPLAN-006, SECPLAN-007, SECPLAN-010 | DGOV-006, DGOV-008, DGOV-010, DGOV-011 | SOUP-004, SOUP-020 | Audit/log retention, backup/restore and incident drill not complete |
| SEC | SECPLAN-001 through SECPLAN-012, ASSET-001 through ASSET-008, CYTH-001 through CYTH-010, CVER-001 through CVER-008 | DGOV-003, DGOV-007, DGOV-011 | SOUP-001 through SOUP-020 | Formal threat model, SBOM, vulnerability monitoring and security report not complete |
| OPS | SECPLAN-004, SECPLAN-010, SECPLAN-011, CYTH-007, CYTH-009, CVER-006 | DGOV-006, DGOV-008 | SOUP-008, SOUP-016, SOUP-020 | Deployment runbook draft started in step 11; rehearsal and approval not complete |
| INT | SECPLAN-003, SECPLAN-004, SECPLAN-006, SECPLAN-011, CYTH-008 | DGOV-005, DGOV-012 | SOUP-018, SOUP-019, SOUP-020 | Supplier qualification and downstream data/interface validation not started |
| VAL | SECPLAN-012, CVER-004, CVER-005, CVER-006 | DGOV-009 | SOUP-002, SOUP-003, SOUP-017 | Formal validation execution, dataset approval and validation report not started |

## Критерии За Завършване На Стъпка 10 В Traceability

Стъпка 10 е отразена в тази matrix, когато:

- cybersecurity plan е добавен като source record;
- data-governance plan е добавен като source record;
- SOUP/dependency register е добавен като source record;
- requirement groups имат връзки към `SECPLAN-*`, `ASSET-*`, `CYTH-*`, `CVER-*`, `DCLASS-*`, `DGOV-*` и `SOUP-*`;
- clinical-use blockers остават видими, защото threat model, SBOM, RBAC, TLS/gateway, retention, vulnerability monitoring и release evidence не са изпълнени.

## Step 11 Release Deployment Maintenance And CAPA Links

| Requirement group | Release/deployment links | Maintenance links | Problem/CAPA links | Remaining evidence gap |
| --- | --- | --- | --- | --- |
| CLM | REL-004, REL-010, REL-011, RPKG-004, RCHK-006, RCHK-015 | CHG-001, CHG-011, MON-011, MON-012 | TRI-004, TRI-008, CAPA-010 | Claims matrix and controlled label review not baselined |
| DATA | REL-007, RPKG-012, DEP-006, DEP-007, DEP-008 | MNT-006, MNT-008, CHG-005, CHG-009, MON-007, MON-010 | PROB-003, PROB-004, TRI-006 | Approved data retention, source-data governance and incident workflow missing |
| API | REL-003, REL-012, RCHK-005, DEP-003, DEP-004, DEP-005, DEP-009 | MNT-004, MNT-009, CHG-004, CHG-007 | PROB-002, PROB-009, TRI-002, TRI-005 | Production auth/session/gateway tests and API compatibility gate missing |
| FUNC | REL-005, REL-012, RPKG-008, RCHK-005 | MNT-003, MNT-004, CHG-003, CHG-009, MON-005 | PROB-005, PROB-009, TRI-003, CAPA-006 | Independent expected-case regression and release evidence not baselined |
| UI | RCHK-007, RPKG-010, DEP-005 | MNT-005, CHG-006, MON-001, MON-011 | PROB-010, TRI-004 | Clinical UI usability validation and human workflow approval missing |
| AUD | REL-014, RPKG-015, DEP-007, DEP-010 | MNT-010, MON-003, MON-005 | PROB-001, PROB-002, PROB-012, CAPA-011 | Record-retention and investigation drill not approved |
| SEC | REL-007, RPKG-011, RPKG-013, RCHK-008, RCHK-010, DEP-002, DEP-003, DEP-014 | MNT-007, MNT-011, CHG-007, CHG-008, MON-006, MON-009 | TRI-005, PROB-004, CAPA-010 | Threat model, SBOM automation, vulnerability workflow and security report missing |
| OPS | REL-001 through REL-014, RROLE-001 through RROLE-008, RPKG-001 through RPKG-015, RCHK-001 through RCHK-016, DEP-001 through DEP-014 | MNT-001 through MNT-014, CHG-001 through CHG-012, MON-001 through MON-012 | PROB-001 through PROB-014, TRI-001 through TRI-008, CAPA-001 through CAPA-012 | Controlled release/deployment rehearsal, maintenance workflow and CAPA system not implemented |
| INT | DEP-003, DEP-004, DEP-005, RPKG-014 | CHG-004, CHG-010, MON-011 | PROB-002, PROB-011, TRI-008 | Downstream app integration release gate and supplier support model missing |
| VAL | REL-006, RPKG-008, RPKG-009, RPKG-010, RCHK-006, RCHK-007 | MNT-005, MON-008, MON-011 | PROB-010, CAPA-006, CAPA-008 | Formal validation execution, deviation handling and effectiveness checks not complete |

## Критерии За Завършване На Стъпка 11 В Traceability

Стъпка 11 е отразена в тази matrix, когато:

- release/deployment plan е добавен като source record;
- maintenance plan е добавен като source record;
- problem-resolution/CAPA plan е добавен като source record;
- requirement groups имат връзки към `REL-*`, `RROLE-*`, `RPKG-*`, `RCHK-*`, `DEP-*`, `MNT-*`, `CHG-*`, `MON-*`, `PROB-*`, `TRI-*` и `CAPA-*`;
- clinical-use blockers остават видими, защото release execution, deployment rehearsal, maintenance workflow, CAPA system и regulatory reporting decision trees не са изпълнени.

## Step 12 Controlled Baseline And Claims-Control Links

| Requirement group | Document/baseline links | Claims/approval links | Change/gate links | Remaining evidence gap |
| --- | --- | --- | --- | --- |
| CLM | DOCCTRL-001, DOCCTRL-007, DOC-001, DOC-018, BASE-007 | CLAIM-001 through CLAIM-016, AC-001 through AC-008, PC-001 through PC-012, APPR-003 | IMPACT-002, IMPACT-003, IMPACT-016, GATE-001, GATE-002 | Claims matrix exists as draft; no approved clinical claims baseline |
| DATA | DOCCTRL-006, DOC-013, DOC-025 | APPR-007 | IMPACT-011, GATE-014 | Data governance still draft; no approved real-data route |
| API | DOCCTRL-005, DOC-023, DOC-024 | CLAIM-006, CLAIM-009, APPR-005 | IMPACT-006, IMPACT-013, GATE-016, GATE-019 | Integration/API claims and downstream contract not approved |
| FUNC | DOCCTRL-005, DOC-006, DOC-009 | CLAIM-004, CLAIM-005, APPR-004 | IMPACT-005, IMPACT-008, GATE-010 | Requirements-based expected cases and verification report not baselined |
| UI | DOCCTRL-010, DOC-018 | CLAIM-001, CLAIM-009, CLAIM-010, APPR-011 | IMPACT-009, GATE-012, GATE-018 | Clinical UI labeling/usability evidence not approved |
| AUD | DOCCTRL-008, DOCCTRL-014, DOC-007, DOC-015 | APPR-005, APPR-012 | IMPACT-014, GATE-016, GATE-017 | Controlled record-retention and release evidence not approved |
| SEC | DOC-012, DOC-013, DOC-014 | APPR-008, APPR-009 | IMPACT-010, IMPACT-012, GATE-013, GATE-015 | Threat model, SBOM and vulnerability process not implemented |
| OPS | DOCCTRL-001 through DOCCTRL-012, DOC-015 through DOC-021, BASE-001 through BASE-012 | APPR-001 through APPR-014 | IMPACT-001 through IMPACT-016, GATE-001 through GATE-020 | Owners are placeholders; no approved baseline or completed gate |
| INT | DOC-024 | CLAIM-006, CLAIM-012, APPR-006 | IMPACT-004, IMPACT-013, GATE-019 | Downstream integration contract and clinical pilot gate not approved |
| VAL | DOC-010, DOC-011, DOC-021 | APPR-010, APPR-011 | IMPACT-009, GATE-011, GATE-012, GATE-020 | Validation/usability execution and pilot approval not complete |

## Критерии За Завършване На Стъпка 12 В Traceability

Стъпка 12 е отразена в тази matrix, когато:

- document-control index е добавен като source record;
- approval matrix е добавен като source record;
- claims-control matrix е добавен като source record;
- change-impact checklist е добавен като source record;
- clinical-readiness gate checklist е добавен като source record;
- requirement groups имат връзки към `DOCCTRL-*`, `DOC-*`, `BASE-*`, `CLAIM-*`, `AC-*`, `PC-*`, `APPR-*`, `IMPACT-*` и `GATE-*`;
- clinical-use blockers остават видими, защото всички Step 12 records са drafts, role holders са `TBD`, baseline package не е approved и gate decision остава `Blocked`.

## Следваща Traceability Работа

Преди clinical-intended development да продължи:

1. Review и approval на requirement ID scheme.
2. Назначаване на requirement owners.
3. Прехвърляне на draft-а в избрания controlled traceability tool или format.
4. Review и baseline на добавените `ARCH-*`, `IF-*`, `DF-*`, `SAD-*`, `VER-*`, `USE-*`, `UTASK-*`, `UERR-*`, `VSCN-*`, `VACC-*`, `SECPLAN-*`, `ASSET-*`, `CYTH-*`, `CVER-*`, `DCLASS-*`, `DGOV-*`, `SOUP-*`, `REL-*`, `RROLE-*`, `RPKG-*`, `RCHK-*`, `DEP-*`, `MNT-*`, `CHG-*`, `MON-*`, `PROB-*`, `TRI-*`, `CAPA-*`, `DOCCTRL-*`, `DOC-*`, `BASE-*`, `CLAIM-*`, `AC-*`, `PC-*`, `APPR-*`, `IMPACT-*` и `GATE-*` links след стъпка 12.
5. Clinical/regulatory/quality/software/security/data-governance review.
6. Назначаване на real owners/approvers и approval route.
7. Добавяне на technical evidence automation за SBOM/dependency audit, secret/PHI scan и release evidence.
8. Freeze на baseline преди formal validation execution.
