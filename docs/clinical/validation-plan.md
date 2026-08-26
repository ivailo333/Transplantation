# Проект На Validation Plan

Статус: Draft за планиране на клинична готовност. Не е одобрен за клинична употреба.

Този документ започва validation plan за HLA Transplantation Simulation проекта.
Той описва как бъдеща validation работа трябва да провери дали софтуерът е
подходящ за intended users, intended use и intended use environment. Документът
не е изпълнен validation report и не разрешава употреба при реална донорска
ситуация.

## Цел

Validation трябва да отговори на въпроса: построен ли е правилният софтуер за
предвидения workflow и потребители? За този проект това означава да се докаже,
че outputs се разбират като supporting software artifacts, че human review не
се заобикаля, че няма unapproved clinical claims и че representative cases
покриват важните edge conditions.

## Изходни Документи

- [Български Clinical Readiness Обзор](bg-readiness-overview.md)
- [Intended Use](intended-use.md)
- [Risk Management And Initial Risk Register](risk-register.md)
- [Software Requirements Specification Draft](software-requirements.md)
- [Traceability Matrix Draft](traceability-matrix.md)
- [Software Architecture Draft](software-architecture.md)
- [Verification Plan Draft](verification-plan.md)
- [Usability Engineering File Draft](usability-engineering.md)
- [Frontend Prototype Draft](frontend-prototype.md)
- [Backend API Component](../backend.md)
- [Backend Integration Guide](../backend-integration.md)

Официални външни references, проверени на 2026-08-26:

- ISO 14155:2026, Clinical investigation of medical devices for human subjects -
  Good clinical practice:
  https://www.iso.org/standard/83968.html
- IEC 62366-1:2015, Medical devices - application of usability engineering:
  https://www.iso.org/standard/63179.html
- ISO 14971:2019, Medical devices - application of risk management:
  https://www.iso.org/standard/72704.html
- European Commission MDCG guidance index, including clinical investigation,
  clinical evaluation, performance evaluation and medical device software:
  https://health.ec.europa.eu/medical-devices-sector/new-regulations/guidance-mdcg-endorsed-documents-and-other-guidance_en

## Validation Scope

Current validation planning scope:

- non-clinical validation of deterministic software artifacts;
- frontend workflow comprehension for Bulgarian local validation users;
- backend-as-component integration behavior;
- audit bundle reproducibility and traceability review;
- documentation and claims boundary review.

Future clinical-intended validation scope, if approved:

- representative transplant workflow tasks;
- clinical/HLA laboratory user interpretation of outputs;
- role-based human review and sign-off workflow;
- validation dataset representativeness and edge-case coverage;
- integration behavior with authoritative clinical source systems;
- operational workflow under downtime or degraded service conditions.

Out of scope until formal approval:

- real-time clinical donor acceptance/rejection;
- autonomous clinical decision support;
- validation with identifiable clinical data without governance approval;
- clinical investigation execution without approved protocol, ethics/legal
  review and site governance where required.

## Validation Roles

| ID | Role | Responsibility | Status |
| --- | --- | --- | --- |
| VROLE-001 | Clinical lead | Defines clinical workflow relevance and reviews clinical assumptions | Not assigned |
| VROLE-002 | HLA laboratory lead | Reviews typing, representation-level meaning and source-data assumptions | Not assigned |
| VROLE-003 | Regulatory lead | Confirms regulatory route, claims and validation evidence expectations | Not assigned |
| VROLE-004 | Quality lead | Controls validation protocol, deviations, approvals and records | Not assigned |
| VROLE-005 | Software lead | Ensures implementation baseline, test evidence and traceability | Not assigned |
| VROLE-006 | Security/privacy lead | Reviews data governance, access and identifiable-data controls | Not assigned |
| VROLE-007 | Validation lead | Owns validation protocol, execution, deviations and report | Not assigned |

## Validation Preconditions

Formal validation execution must not start until:

- intended use and non-intended uses are approved;
- regulatory route and claims are reviewed;
- requirements and traceability are baselined;
- software architecture and verification plan are reviewed;
- risk controls for validation scope are implemented or explicitly justified;
- usability engineering plan is reviewed;
- validation dataset governance is approved;
- software version, environment and dependencies are frozen for the run;
- protocol, acceptance criteria and deviation process are approved;
- clinical, quality, regulatory, software and security roles are assigned.

## Dataset Strategy

| ID | Dataset need | Purpose | Minimum controls |
| --- | --- | --- | --- |
| VDATA-001 | Synthetic smoke dataset | Repeatable local CLI/API/frontend checks | No PHI; deterministic expected outputs |
| VDATA-002 | Curated edge-case dataset | Missing/partial/ambiguous HLA data and representation differences | Documented case rationale and expected behavior |
| VDATA-003 | Retrospective anonymized/pseudonymized dataset | Future clinical workflow validation, if approved | Governance approval, data minimization, access control |
| VDATA-004 | Source-system integration fixture | Future LIS/EHR/FHIR/HL7 transformation validation | Source provenance, timestamp and authoritativeness metadata |
| VDATA-005 | Negative/error dataset | Invalid requests, stale schema, IO/encoding errors | Controlled expected error categories and request IDs |

No identifiable donor, recipient or patient data may be used until governance,
legal basis, access controls, retention and audit processes are approved.

## Validation Scenario Matrix

| ID | Scenario | User/task links | Requirement links | Risk links | Acceptance criteria |
| --- | --- | --- | --- | --- | --- |
| VSCN-001 | User identifies non-clinical boundary before output review | UTASK-001 | CLM-001, CLM-003 | RM-009, RM-018, RM-020, RM-025 | User states outputs are not clinical decisions |
| VSCN-002 | Backend readiness checked before report review | UTASK-002 | API-004, UI-002, OPS-002 | RM-012, RM-016, RM-024 | User distinguishes readiness from clinical availability |
| VSCN-003 | Recipient-side live report generated with correct external ID | UTASK-003 | DATA-002, FUNC-001, UI-001 | RM-001, RM-002, RM-022 | Direction and external ID are correct in UI/report/audit metadata |
| VSCN-004 | Missing or partial HLA data is recognized and not over-interpreted | UTASK-004 | DATA-004, UI-004 | RM-003, RM-025 | User stops or escalates review when required data is missing |
| VSCN-005 | Representation-level comparison is interpreted as deterministic level difference | UTASK-005 | FUNC-002, UI-003, UI-005 | RM-005, RM-010, RM-025 | User does not describe comparison as compatibility |
| VSCN-006 | Sorted rows are interpreted as software ordering only | UTASK-006 | FUNC-005, UI-005 | RM-011, RM-025 | User can identify sort metric and denies allocation meaning |
| VSCN-007 | Audit bundle is created and reviewed for reproducibility | UTASK-007 | FUNC-003, AUD-001 | RM-007, RM-008, RM-021 | User locates bundle, manifest and request ID |
| VSCN-008 | Backend/proxy error is escalated with request ID | UTASK-009 | API-005, API-006, UI-002 | RM-017, RM-024 | User captures request ID and error category |
| VSCN-009 | Validation note is not confused with clinical approval | UTASK-008 | CLM-004, UI-006 | RM-010, RM-023 | User confirms local note is not sign-off |
| VSCN-010 | Future clinical sign-off cannot be bypassed by backend output | UTASK-010 | INT-001, VAL-004 | RM-009, RM-018, RM-023 | Downstream workflow requires qualified human review |
| VSCN-011 | Representative dataset covers known high-risk edge cases | VDATA-002, VDATA-003 | VAL-002 | RM-019 | Dataset rationale covers inclusion, exclusion and edge-case logic |
| VSCN-012 | Data governance blocks unauthorized identifiable-data use | VDATA-003, VDATA-004 | DATA-001, DATA-006, SEC-002 | RM-014, RM-021 | Validation run cannot proceed without governance approval |

## Acceptance Criteria Draft

| ID | Criterion | Release impact |
| --- | --- | --- |
| VACC-001 | All critical validation tasks pass without uncontrolled use error. | Blocks clinical-intended release |
| VACC-002 | Users do not interpret reports, comparisons, sorted rows or audit bundles as donor suitability or allocation recommendation. | Blocks clinical-intended release |
| VACC-003 | Donor/recipient direction and source identifiers remain correct across UI, API, report and audit outputs. | Blocks clinical-intended release |
| VACC-004 | Missing, partial, stale or inconsistent data is visible and handled according to approved workflow. | Blocks clinical-intended release |
| VACC-005 | Backend/API failure paths provide actionable request ID and error category. | Blocks production-like release if unresolved |
| VACC-006 | Validation dataset rationale is approved by clinical/HLA laboratory/regulatory/quality stakeholders. | Blocks formal validation completion |
| VACC-007 | Deviations are recorded, triaged and either resolved or formally justified. | Blocks release until dispositioned |
| VACC-008 | Clinical sign-off cannot be automated or bypassed by backend output. | Blocks clinical-intended release |

## Evidence To Collect

Each validation run should collect:

- validation protocol version;
- software commit SHA and release candidate ID;
- environment and configuration;
- dataset IDs and governance approval reference;
- participant roles and eligibility;
- task scripts and observed outcomes;
- pass/fail results for each `VSCN-*`;
- use errors, close calls and participant comments;
- deviations and corrective actions;
- linked requirements, risks, architecture and verification IDs;
- reviewer approvals and release impact.

## Deviation Handling

Any validation deviation must be logged with:

- deviation ID;
- affected scenario and acceptance criterion;
- affected risk and requirement;
- description and reproduction steps;
- initial severity;
- root cause or investigation status;
- corrective/preventive action;
- retest expectation;
- release decision.

Critical or safety-related validation deviations must block clinical-intended
release until reviewed through controlled QMS.

## Clinical Investigation Boundary

This validation plan does not initiate a clinical investigation or performance
study. If the project later requires prospective clinical investigation or
human-subject research, that work must follow the applicable regulatory,
ethical, institutional and data-protection process before execution.

## Validation Report Outline

The future validation report should include:

1. Protocol reference and deviations.
2. Software version and environment.
3. Dataset description and governance evidence.
4. Participant/user role summary.
5. Results by `VSCN-*` and `VACC-*`.
6. Use-error and residual-risk analysis.
7. Unresolved issues and release impact.
8. Clinical, regulatory, quality, software and security review signatures.

## Step 9 Conclusion

The project now has a planning-level validation plan. It defines validation
roles, preconditions, dataset strategy, validation scenarios, acceptance
criteria, evidence records and deviation handling. It does not establish
clinical validation, clinical investigation approval or release readiness.
