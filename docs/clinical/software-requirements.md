# Software Requirements Specification Draft

Status: Draft for clinical-readiness planning. Not approved for clinical use.

This document defines initial testable software requirements for the HLA
Transplantation Simulation project as it moves from a non-clinical CLI/backend
prototype toward a possible larger application. These requirements are not
baselined, not approved, and not sufficient for clinical release.

## Purpose

The purpose of this draft is to turn the intended use, risk register, backend
API, frontend prototype, and quality/lifecycle planning into requirements that
can later be reviewed, baselined, implemented, verified, validated, and placed
under change control.

## Source Documents Reviewed

Internal source documents:

- [Intended Use](intended-use.md)
- [Regulatory Classification Draft](regulatory-classification.md)
- [Quality System Draft](quality-system.md)
- [Risk Management And Initial Risk Register](risk-register.md)
- [Software Lifecycle Draft](software-lifecycle.md)
- [Frontend Prototype Draft](frontend-prototype.md)
- [Backend API Component](../backend.md)
- [Backend Integration Guide](../backend-integration.md)
- [Data Policy](../data.md)

Official external references checked on 2026-08-26:

- IEC 62304:2006, Medical device software - software life cycle processes:
  https://committee.iso.org/standard/38421.html
- ISO 14971:2019, Medical devices - application of risk management:
  https://www.iso.org/standard/72704.html
- IEC 62366-1:2015, Medical devices - usability engineering:
  https://webstore.iec.ch/en/publication/21863
- European Commission MDCG guidance index for MDR/IVDR:
  https://health.ec.europa.eu/medical-devices-sector/new-regulations/guidance-mdcg-endorsed-documents-and-other-guidance_en

## Requirement Status Values

| Status | Meaning |
| --- | --- |
| Present | The current repository appears to contain an initial implementation or control. |
| Prototype | Partly implemented for non-clinical validation, but not production-ready. |
| Planned | Requirement is identified but not implemented. |
| Blocker | Requirement is required before any clinical workflow use. |

## Verification Method Values

| Method | Meaning |
| --- | --- |
| Unit | Automated unit test or focused module test. |
| Integration | Backend/frontend/database/API integration test. |
| System | End-to-end workflow test in a controlled environment. |
| Review | Documented design, code, claims, security, or clinical review. |
| Validation | Representative user/workflow validation with predefined acceptance criteria. |

## Requirements

| ID | Requirement | Status | Risk links | Verification |
| --- | --- | --- | --- | --- |
| CLM-001 | The software shall display and return explicit non-clinical status for current CLI, API, reports, audit bundles, and frontend prototype outputs. | Present | RM-005, RM-009, RM-010, RM-018, RM-020, RM-025 | Unit, Integration, Review |
| CLM-002 | The software shall not expose donor acceptance, donor rejection, transplant suitability, allocation, prioritization, treatment, or autonomous clinical decision fields. | Present | RM-009, RM-010, RM-018, RM-023 | Integration, Review |
| CLM-003 | User-facing labels, API fields, reports, and documentation shall avoid compatibility, recommendation, risk-score, or clinical ranking claims unless formally approved. | Prototype | RM-005, RM-010, RM-011, RM-018, RM-025 | Review, Validation |
| CLM-004 | Any clinical approval or sign-off workflow shall remain disabled or absent until intended use, regulatory, risk, usability, validation, and release gates are approved. | Prototype | RM-010, RM-018, RM-023 | Integration, Review |
| DATA-001 | Current use shall be limited to synthetic, demo, anonymized, or validation-planning records. | Present | RM-014, RM-021 | Review |
| DATA-002 | The software shall preserve donor/recipient direction and subject role labels through input, persistence, API, reports, frontend display, and audit artifacts. | Prototype | RM-002, RM-011, RM-022 | Unit, Integration, Validation |
| DATA-003 | HLA typing values shall be validated against the configured HLA validation path before being persisted or used for deterministic comparison. | Present | RM-001, RM-003, RM-006 | Unit, Integration |
| DATA-004 | Missing, partial, or ambiguous HLA typing data shall be represented explicitly and shall not be converted into clinical conclusions. | Planned | RM-003, RM-025 | Unit, System, Validation |
| DATA-005 | Reports and comparisons shall include source identifiers, representation level, request ID, generation metadata, and relevant HLA reference version metadata. | Present | RM-004, RM-008, RM-022 | Unit, Integration |
| DATA-006 | Identifiable clinical data, secrets, runtime databases, exports, audit bundles, and logs shall not be committed to source control. | Present | RM-014, RM-021 | Review, System |
| API-001 | Backend APIs intended for new integrations shall use versioned `/v1` endpoints and structured JSON request/response contracts. | Present | RM-009, RM-012, RM-017 | Integration |
| API-002 | Backend API responses shall include `schema`, `request_id`, `clinical: false`, and a non-clinical notice where applicable. | Present | RM-008, RM-009, RM-017, RM-020 | Integration |
| API-003 | Protected backend endpoints shall support API-key authentication in non-clinical deployments and shall be replaced or supplemented by role-based access control before clinical use. | Prototype | RM-013, RM-014, RM-023 | Integration, Review |
| API-004 | Liveness and readiness probes shall provide operational status without creating clinical claims or exposing unnecessary sensitive data. | Present | RM-012, RM-013, RM-016, RM-024 | Integration, Review |
| API-005 | Error responses shall distinguish validation, encoding, IO, schema, not-found, conflict, authorization, and service-unavailable conditions with request IDs. | Present | RM-012, RM-017, RM-024 | Unit, Integration |
| API-006 | Backend request handling shall propagate request IDs into response headers and logs for reproducibility and support review. | Present | RM-008, RM-017, RM-021 | Integration, Review |
| FUNC-001 | The software shall generate deterministic STEP 27 live and batch analytical reports from persisted donor/recipient HLA typing data. | Present | RM-001, RM-006, RM-007, RM-008 | Unit, Integration |
| FUNC-002 | The software shall compare representation levels for the same case and report deterministic pair/locus deltas without interpreting them as clinical suitability. | Present | RM-005, RM-006, RM-009, RM-025 | Unit, Integration, Review |
| FUNC-003 | The software shall create reproducible audit bundles containing report, comparison, doctor, schema, and metadata artifacts. | Present | RM-007, RM-008, RM-021 | Unit, Integration |
| FUNC-004 | JSON, CSV, HTML, text, API, and audit outputs for the same operation shall remain consistent for controlled fields. | Prototype | RM-007, RM-008 | Unit, Integration |
| FUNC-005 | Sorting and ranking fields shall be disclosed as software ordering only and shall not imply clinical prioritization. | Prototype | RM-011, RM-025 | Review, Validation |
| UI-001 | The frontend shall show donor/recipient direction, external ID, selected level, request ID, and backend status clearly during case review. | Prototype | RM-002, RM-011, RM-016, RM-022 | System, Validation |
| UI-002 | The frontend shall expose liveness/readiness checks before report review and shall surface backend/proxy errors without hiding request details. | Prototype | RM-016, RM-017, RM-024 | System |
| UI-003 | The frontend shall display report tables, locus summaries, comparison rows, and raw JSON response data for validation traceability. | Prototype | RM-001, RM-005, RM-008, RM-022 | System, Validation |
| UI-004 | The clinical workflow UI shall provide explicit warnings for missing, partial, stale, or inconsistent case data before any reviewed output is used. | Planned | RM-003, RM-004, RM-022 | System, Validation |
| UI-005 | The frontend shall use neutral language and visual states that do not imply accept/reject or suitability recommendations. | Prototype | RM-010, RM-011, RM-025 | Review, Validation |
| UI-006 | The frontend shall not store clinical approval. Prototype reviewer notes may be local-only and clearly labelled as validation notes. | Prototype | RM-010, RM-014, RM-021, RM-023 | System, Review |
| AUD-001 | Audit bundles shall include enough metadata to reproduce or investigate the generated software artifact. | Present | RM-008, RM-017, RM-021 | Unit, Integration |
| AUD-002 | Clinical-intended releases shall include immutable release identifiers, dependency versions, migration status, and approved configuration records. | Planned | RM-004, RM-008, RM-012, RM-015, RM-024 | Review, System |
| SEC-001 | Runtime configuration shall be supplied through environment/configuration files, with examples that do not contain secrets. | Present | RM-013, RM-014, RM-024 | Review |
| SEC-002 | Before clinical workflow use, the larger application shall implement role-based authentication, authorization, session management, and access review. | Blocker | RM-013, RM-014, RM-021, RM-023 | System, Review |
| SEC-003 | Before clinical workflow use, deployment shall use TLS, network segmentation, secret management, backup/restore controls, and monitored logs. | Blocker | RM-013, RM-014, RM-016, RM-021, RM-024 | System, Review |
| SEC-004 | The project shall maintain a dependency/SOUP register, vulnerability monitoring, and update policy before controlled release. | Planned | RM-004, RM-015 | Review |
| OPS-001 | The clinical workflow shall define downtime, degraded-mode, support, and escalation procedures before donor-situation use. | Blocker | RM-016, RM-017, RM-024 | Review, Validation |
| OPS-002 | Production-like deployment shall require readiness checks, migration checks, environment checks, smoke tests, and rollback criteria. | Planned | RM-012, RM-016, RM-024 | System, Review |
| INT-001 | Integration contracts shall state that downstream systems must not treat API outputs as autonomous clinical actions or automated sign-off. | Planned | RM-009, RM-018, RM-023 | Review, System |
| INT-002 | Future LIS/EHR/FHIR/HL7 integrations shall preserve source-system identity, data timestamps, authoritativeness, and transformation provenance. | Planned | RM-001, RM-002, RM-004, RM-022 | Integration, Review |
| VAL-001 | Verification shall include requirements-based tests for deterministic comparison, reporting, export parity, API contracts, migrations, errors, and audit bundles. | Planned | RM-006, RM-007, RM-008, RM-012, RM-017 | Unit, Integration |
| VAL-002 | Validation shall use representative cases, edge cases, and documented inclusion/exclusion rationale before clinical workflow use. | Blocker | RM-019 | Validation |
| VAL-003 | Usability engineering shall cover safety-related UI tasks, foreseeable use errors, warnings, neutral wording, and user comprehension. | Blocker | RM-010, RM-011, RM-020, RM-025 | Validation |
| VAL-004 | Clinical workflow validation shall verify that qualified human review remains mandatory and that no automated clinical action can bypass oversight. | Blocker | RM-009, RM-018, RM-023 | System, Validation |

## Baseline Rules

Before these requirements become controlled:

1. Assign requirement owner and approvers.
2. Confirm intended use and regulatory classification.
3. Review each requirement with clinical, HLA laboratory, regulatory, quality,
   software, security, and validation stakeholders.
4. Link each requirement to design, implementation, verification, validation,
   and risk controls in the traceability matrix.
5. Add version, approval, and change-control metadata.
6. Freeze a baseline before any clinical-intended validation protocol is run.

## Current Step 7 Conclusion

The project now has an initial requirements draft. The next readiness work
should turn these requirements into controlled architecture, verification, and
validation records, then expand the frontend and security model only under
change control.
