# Проект На Data Governance Plan

Статус: Draft за планиране на клинична готовност. Не е одобрен за клинична употреба.

Този документ дефинира начална data-governance рамка за HLA Transplantation Simulation проекта. Той не е GDPR DPIA, legal basis assessment, data-processing agreement, clinical data-management plan или approval за обработка на identifiable health data.

## Цел

Целта е да се дефинират data classes, allowed current use, бъдещи controls за identifiable или pseudonymized health data, retention, export handling, provenance, auditability и validation dataset governance.

Проектът остава неклиничен. Реални donor, recipient, patient, transplant-center или operational case данни не трябва да се въвеждат, записват, импортират, експортират или качват в този repository без одобрен governance process.

## Изходни Документи

Вътрешни source документи:

- [Български Clinical Readiness Обзор](bg-readiness-overview.md)
- [Intended Use](intended-use.md)
- [Risk Management And Initial Risk Register](risk-register.md)
- [Software Requirements Specification Draft](software-requirements.md)
- [Traceability Matrix Draft](traceability-matrix.md)
- [Software Architecture Draft](software-architecture.md)
- [Verification Plan Draft](verification-plan.md)
- [Usability Engineering File Draft](usability-engineering.md)
- [Validation Plan Draft](validation-plan.md)
- [Cybersecurity Plan Draft](cybersecurity-plan.md)
- [SOUP And Dependency Register Draft](soup-dependency-register.md)
- [Release And Deployment Plan Draft](release-deployment-plan.md)
- [Maintenance Plan Draft](maintenance-plan.md)
- [Problem Resolution And CAPA Plan Draft](problem-resolution-capa.md)
- [Backend API Component](../backend.md)
- [Backend Integration Guide](../backend-integration.md)
- [Data Policy](../data.md)

Официални външни references, проверени на 2026-08-26:

- Regulation (EU) 2016/679, General Data Protection Regulation:
  https://eur-lex.europa.eu/eli/reg/2016/679/oj/eng
- European Commission overview of EU data protection legal framework:
  https://commission.europa.eu/law/law-topic/data-protection/legal-framework-eu-data-protection_en
- Regulation (EU) 2025/327, European Health Data Space:
  https://eur-lex.europa.eu/legal-content/EN/ALL/?uri=CELEX%3A32025R0327
- European Commission EHDS overview:
  https://health.ec.europa.eu/ehealth-digital-health-and-care/european-health-data-space-regulation-ehds_en
- ISO 27799:2025, Health informatics - information security controls in health:
  https://www.iso.org/standard/84647.html
- ISO/IEC 27001:2022, Information security management systems:
  https://www.iso.org/standard/27001
- ENISA, Procurement guidelines for the cybersecurity of hospitals and healthcare providers, July 2026:
  https://www.enisa.europa.eu/publications/procurement-guidelines-for-the-cybersecurity-of-hospitals-and-healthcare-providers

## Data Governance Scope

Current approved project scope:

- synthetic, demo, anonymized or validation-planning data;
- small local runtime SQLite database excluded from Git;
- local py-ard/IPD-IMGT/HLA reference data for reproducible development;
- local generated exports and audit bundles excluded from Git unless intentionally promoted to fixtures;
- documentation and tests that do not contain real clinical identifiers.

Future scope requiring approval:

- real donor/recipient/patient data;
- pseudonymized retrospective validation datasets;
- identifiable clinical workflow records;
- integration with hospital, laboratory, registry, LIS, EHR, FHIR or HL7 systems;
- cross-institutional transfer or processing;
- secondary use of health data for research, validation or performance monitoring.

## Data Classes

| ID | Data class | Examples | Current repository rule | Future clinical rule |
| --- | --- | --- | --- | --- |
| DCLASS-001 | Synthetic/demo data | Local examples, test fixtures | Allowed if non-identifiable and minimal | May remain for tests/training |
| DCLASS-002 | Anonymized validation-planning data | Cases stripped of direct and indirect identifiers | Allowed only if re-identification risk is reviewed | Requires documented anonymization method and owner |
| DCLASS-003 | Pseudonymized health data | Coded donor/recipient records with key held elsewhere | Not allowed in current repository | Requires DPIA/legal basis/access controls |
| DCLASS-004 | Identifiable health data | Names, hospital IDs, national identifiers, dates tied to persons | Prohibited | Requires approved clinical/data governance environment |
| DCLASS-005 | Operational transplant data | donor situation timestamps, allocation workflow, center decisions | Prohibited | Requires approved system-of-record boundaries and audit |
| DCLASS-006 | Reference data | py-ard data, IPD-IMGT/HLA versioned data | Allowed as controlled technical input | Requires version and change-impact control |
| DCLASS-007 | Generated artifacts | reports, comparisons, exports, audit bundles | Allowed locally; ignored by Git unless fixture-approved | Requires retention, access and disclosure controls |
| DCLASS-008 | Security/support data | logs, request IDs, error details | Allowed locally if no real data | Requires PHI-safe logging and retention policy |

## Governance Controls

| ID | Control | Linked risks | Current status | Evidence needed |
| --- | --- | --- | --- | --- |
| DGOV-001 | Define data owner, controller/processor roles and governance approvers before real health data use. | RM-014, RM-021 | Not started | Governance decision record |
| DGOV-002 | Maintain current use restriction to synthetic, demo, anonymized or validation-planning records. | RM-014, RM-020, RM-021 | Present | README/data policy review |
| DGOV-003 | Require legal basis, DPIA/privacy assessment and institutional approval before identifiable or pseudonymized clinical data. | RM-014, RM-019, RM-021 | Not started | DPIA/legal review record |
| DGOV-004 | Apply data minimization to imports, persistence, logs, exports and audit bundles. | RM-014, RM-021 | Planned | Data-flow review and artifact review |
| DGOV-005 | Preserve donor/recipient role, source-system identity, timestamps, authoritativeness and transformation provenance. | RM-001, RM-002, RM-004, RM-022 | Partial | Integration data contract and provenance tests |
| DGOV-006 | Define retention, deletion and archival periods for databases, exports, audit bundles, logs and validation evidence. | RM-008, RM-014, RM-021 | Not started | Retention schedule and deletion test |
| DGOV-007 | Define access controls and access review for data stores, exports, logs, backups and validation datasets. | RM-013, RM-014, RM-021 | Not started | Access matrix and review record |
| DGOV-008 | Define backup, restore and disaster-recovery controls for clinical-intended environments. | RM-012, RM-016, RM-024 | Not started | Backup/restore test evidence |
| DGOV-009 | Define validation dataset inclusion/exclusion, representativeness, versioning and allowed use. | RM-019 | Draft started in validation plan | Dataset governance protocol |
| DGOV-010 | Keep exports and audit bundles out of Git unless promoted as controlled non-identifiable fixtures. | RM-014, RM-021 | Present | Git status/repo scan and fixture approval |
| DGOV-011 | Define breach/data incident triage and notification pathway with security and quality processes. | RM-014, RM-021 | Not started | Incident SOP and drill |
| DGOV-012 | Define cross-border, secondary-use and research reuse rules before multi-site or research validation work. | RM-014, RM-019, RM-021 | Not started | Legal/institutional review |

## Data Flow Governance

| Flow | Governance need | Current status |
| --- | --- | --- |
| CLI import to SQLite | Validate values, preserve source metadata, prevent real data in local prototype | Partial |
| Backend API request to report/comparison | Avoid unnecessary identifiers, include request ID, maintain non-clinical status | Partial |
| Report/export generation | Minimize sensitive fields, label non-clinical artifacts, control storage path | Partial |
| Audit bundle creation | Ensure reproducibility without uncontrolled PHI disclosure | Partial |
| Frontend validation UI | Avoid persistent clinical approval and uncontrolled browser storage | Prototype |
| Future LIS/EHR/FHIR/HL7 integration | Preserve source identity, timestamps, authoritativeness and transformation provenance | Not started |
| Future validation dataset | Version, access-control and document inclusion/exclusion rationale | Not started |

## Retention Draft

No clinical retention schedule is approved. Draft retention planning should separate:

- source code and controlled documentation;
- release records and verification evidence;
- validation datasets and expected-output records;
- runtime databases;
- generated reports and audit bundles;
- API/application logs;
- security event logs;
- backups and restore artifacts;
- incident/CAPA records.

Each class needs an owner, retention period, deletion method, legal hold rule and retrieval test.

## Validation Dataset Governance

Before representative validation cases are used:

- data source and permission must be documented;
- anonymization or pseudonymization method must be reviewed;
- inclusion/exclusion criteria must be approved;
- edge cases and missing-data cases must be intentionally sampled;
- dataset version must be immutable for a validation run;
- expected outputs must be reviewed by qualified experts;
- access must be limited to authorized validation roles;
- deviations and corrections must be documented.

Validation cases are evidence records, not demo data. They should not be mixed with local quick-start data or committed as ordinary examples.

## Export And Audit Bundle Rules

Current exports and audit bundles are local, ignored runtime artifacts. Before clinical workflow use:

- export purpose and audience must be defined;
- sensitive identifiers must be minimized or removed where possible;
- every exported artifact must include version/request metadata;
- storage location must be access-controlled;
- sharing outside the authorized environment must require approval;
- retention and deletion must be enforced;
- support review must use request IDs and controlled access, not ad hoc file sharing.

## Data Incident Handling

Potential data incidents include:

- real clinical data entered into the non-clinical prototype;
- export or audit bundle shared outside approved storage;
- log containing unexpected identifier;
- wrong source-system mapping;
- stale or incorrect reference-data version;
- validation dataset copied to uncontrolled location;
- unauthorized access to runtime database or backup.

Each incident must be triaged for privacy, safety, quality and security impact, then linked to CAPA/problem-resolution records where applicable.

## Clinical-Use Blockers

Clinical workflow use remains blocked until:

- data owner and governance approvers are assigned;
- lawful basis and DPIA/privacy assessment are complete where required;
- allowed data classes and environments are approved;
- access, retention, deletion and backup controls are implemented;
- source-system provenance and data-quality rules are verified;
- validation dataset governance is approved;
- PHI-safe logging/export/audit rules are verified;
- data incident process is rehearsed.

## Step 10 Conclusion

This document creates a planning-level data-governance file. It keeps the current repository limited to non-clinical data and defines the controls needed before any identifiable or pseudonymized health data can be used in a larger clinical-intended application.
