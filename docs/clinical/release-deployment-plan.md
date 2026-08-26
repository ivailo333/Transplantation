# Проект На Release И Deployment Plan

Статус: Draft за планиране на клинична готовност. Не е одобрен за клинична употреба.

Този документ дефинира начална release и deployment рамка за HLA Transplantation Simulation проекта. Той не е approved release procedure, не е production deployment runbook и не разрешава употреба при реална донорска ситуация.

## Цел

Целта е да се опише как неклиничният backend/frontend prototype може да премине към controlled release candidate само след като requirements, risk controls, verification, validation, usability, cybersecurity, data governance, SOUP/dependency и QMS gates са изпълнени.

Този draft трябва да бъде използван за планиране на:

- release scope и freeze;
- release package contents;
- deployment environment controls;
- release approval roles;
- pre-release checks;
- rollback и downtime readiness;
- release record retention;
- clinical-use blockers.

## Изходни Документи

Вътрешни source документи:

- [Български Clinical Readiness Обзор](bg-readiness-overview.md)
- [Intended Use](intended-use.md)
- [Regulatory Classification Draft](regulatory-classification.md)
- [Quality System Draft](quality-system.md)
- [Risk Management And Initial Risk Register](risk-register.md)
- [Software Lifecycle Draft](software-lifecycle.md)
- [Software Requirements Specification Draft](software-requirements.md)
- [Traceability Matrix Draft](traceability-matrix.md)
- [Software Architecture Draft](software-architecture.md)
- [Verification Plan Draft](verification-plan.md)
- [Usability Engineering File Draft](usability-engineering.md)
- [Validation Plan Draft](validation-plan.md)
- [Cybersecurity Plan Draft](cybersecurity-plan.md)
- [Data Governance Plan Draft](data-governance.md)
- [SOUP And Dependency Register Draft](soup-dependency-register.md)
- [Maintenance Plan Draft](maintenance-plan.md)
- [Problem Resolution And CAPA Plan Draft](problem-resolution-capa.md)
- [Document Control Index Draft](document-control-index.md)
- [Approval Matrix Draft](approval-matrix.md)
- [Claims Control Matrix Draft](claims-control-matrix.md)
- [Change Impact Checklist Draft](change-impact-checklist.md)
- [Clinical Readiness Gate Checklist Draft](clinical-readiness-gate-checklist.md)
- [Backend API Component](../backend.md)
- [Backend Integration Guide](../backend-integration.md)
- [Data Policy](../data.md)

Официални външни references, проверени на 2026-08-26:

- ISO 13485:2016, Medical devices - quality management systems:
  https://committee.iso.org/standard/59752.html
- IEC 62304:2006, Medical device software - software life cycle processes:
  https://committee.iso.org/standard/38421.html
- ISO 14971:2019, Medical devices - application of risk management:
  https://www.iso.org/standard/72704.html
- ISO/TR 24971:2020, guidance on the application of ISO 14971:
  https://www.iso.org/standard/74437.html
- FDA, Remanufacturing and Servicing Medical Devices page noting QMSR effective 2026-02-02:
  https://www.fda.gov/medical-devices/quality-and-compliance-medical-devices/remanufacturing-and-servicing-medical-devices
- FDA, Cybersecurity in Medical Devices: Quality Management System Considerations and Content of Premarket Submissions, final guidance, February 2026:
  https://www.fda.gov/regulatory-information/search-fda-guidance-documents/cybersecurity-medical-devices-quality-management-system-considerations-and-content-premarket
- European Commission MDCG guidance index, including PMS/vigilance and software guidance:
  https://health.ec.europa.eu/medical-devices-sector/new-regulations/guidance-mdcg-endorsed-documents-and-other-guidance_en

## Release Scope

Current release scope:

- non-clinical CLI and backend API;
- deterministic HLA comparison/report/export/audit artifacts;
- static local frontend validation prototype;
- local SQLite runtime database;
- tests and planning documentation.

Future clinical-intended release scope, if approved:

- larger application integration boundary;
- production authentication/authorization;
- deployment topology and environment separation;
- controlled validation dataset and validation report;
- approved clinical workflow UI and human review;
- security, data-governance and SOUP release evidence;
- maintenance, incident, CAPA and post-release monitoring processes.

Out of scope until formally approved:

- donor acceptance/rejection;
- organ allocation;
- transplant suitability;
- virtual crossmatch, DSA, MFI, cPRA, eplet or PIRCHE interpretation;
- autonomous clinical recommendation;
- processing of identifiable clinical data in this repository.

## Release Principles

- REL-001: A release must be traceable to a unique Git commit and, for controlled releases, a release tag.
- REL-002: Release scope must be frozen before final verification and validation execution.
- REL-003: No clinical-intended release may proceed from unreviewed local changes.
- REL-004: Release records must include intended-use version, requirements baseline, risk file status and known limitations.
- REL-005: Release records must include verification status and unresolved deviations.
- REL-006: Release records must include validation and usability status when user workflow or clinical context is affected.
- REL-007: Release records must include cybersecurity, data-governance and SOUP/dependency review.
- REL-008: Release records must include migration, backup/restore and rollback readiness.
- REL-009: Release approval must be role-based and cannot be granted by implementation work alone.
- REL-010: Non-clinical releases must remain clearly labelled as non-clinical.
- REL-011: Clinical claims must not be added during release packaging unless claims are approved and traceable.
- REL-012: Release artifacts must be reproducible from the recorded commit and dependency set.
- REL-013: Emergency fixes must still be recorded, reviewed and verified according to risk.
- REL-014: Release evidence must remain retrievable for audit, investigation and maintenance.

## Release Roles

| ID | Role | Release responsibility |
| --- | --- | --- |
| RROLE-001 | Product owner | Confirms release scope and intended-use alignment |
| RROLE-002 | Clinical lead | Reviews clinical workflow impact and clinical limitations |
| RROLE-003 | Regulatory lead | Reviews claims, route and release constraints |
| RROLE-004 | Quality lead | Owns release record completeness and approval workflow |
| RROLE-005 | Software lead | Confirms source commit, build, architecture and code review status |
| RROLE-006 | Verification/validation lead | Confirms verification, validation, deviations and acceptance criteria |
| RROLE-007 | Security/data lead | Confirms cybersecurity, data-governance, SBOM and privacy evidence |
| RROLE-008 | Operations lead | Confirms deployment, monitoring, backup, rollback and support readiness |

## Release Package Contents

| ID | Package item | Required before clinical-intended release |
| --- | --- | --- |
| RPKG-001 | Release scope statement | Yes |
| RPKG-002 | Git commit SHA and release tag | Yes |
| RPKG-003 | Build artifacts or deployment image reference | Yes |
| RPKG-004 | Intended use and claims version | Yes |
| RPKG-005 | Requirements baseline and traceability matrix | Yes |
| RPKG-006 | Risk management file and residual-risk status | Yes |
| RPKG-007 | Architecture/design record versions | Yes |
| RPKG-008 | Verification report and failed-test/deviation review | Yes |
| RPKG-009 | Validation report and representative dataset record | Yes |
| RPKG-010 | Usability engineering summary/report | Yes |
| RPKG-011 | Cybersecurity review, threat model and security test evidence | Yes |
| RPKG-012 | Data-governance/privacy review and retention decision | Yes |
| RPKG-013 | SOUP register, SBOM and vulnerability review | Yes |
| RPKG-014 | Deployment runbook, rollback and downtime procedure | Yes |
| RPKG-015 | Known issues, release notes and approval record | Yes |

## Release Checklist Draft

| ID | Check | Evidence |
| --- | --- | --- |
| RCHK-001 | Working tree is clean except allowed ignored runtime files. | `git status --short --branch --ignored` |
| RCHK-002 | Correct release commit/tag is identified. | Git log/tag record |
| RCHK-003 | Requirements included in the release are frozen. | Requirements baseline |
| RCHK-004 | Risk controls for release scope are reviewed. | Risk review record |
| RCHK-005 | Automated verification checks pass. | CI and local verification report |
| RCHK-006 | Validation status is reviewed against intended use. | Validation report or explicit non-clinical restriction |
| RCHK-007 | Usability status is reviewed for user-facing changes. | Usability evidence |
| RCHK-008 | Cybersecurity review is complete. | Threat model/security report |
| RCHK-009 | Data-governance review is complete. | Privacy/data review |
| RCHK-010 | SOUP/SBOM review is complete. | SBOM and vulnerability report |
| RCHK-011 | Migration and schema compatibility are checked. | Migration/readiness evidence |
| RCHK-012 | Deployment environment is approved. | Deployment checklist |
| RCHK-013 | Backup/restore and rollback are ready. | Restore/rollback test |
| RCHK-014 | Known issues are reviewed for release impact. | Known-issues record |
| RCHK-015 | Release notes and user-facing limitations are prepared. | Release note |
| RCHK-016 | Required approvers sign off or reject release. | Approval record |

## Deployment Environment Controls

| ID | Control | Current status | Clinical-use gap |
| --- | --- | --- | --- |
| DEP-001 | Separate development, validation, staging and production environments. | Not implemented | Environment plan and access rules needed |
| DEP-002 | Require production configuration outside Git. | Partial | Secret store and deployment-managed config needed |
| DEP-003 | Enforce TLS through gateway or hosting platform. | Not implemented | TLS validation required |
| DEP-004 | Restrict CORS to approved origins. | Configurable | Approved origin inventory required |
| DEP-005 | Enforce RBAC/session controls in larger application. | Not implemented | Identity provider and access matrix needed |
| DEP-006 | Store runtime database in approved controlled storage. | Local only | Production data store decision needed |
| DEP-007 | Store exports and audit bundles in approved controlled storage. | Local ignored path | Access, retention and backup rules needed |
| DEP-008 | Mount py-ard/IPD-IMGT/HLA data read-only where practical. | Docker volume planned | Source-data version and checksum needed |
| DEP-009 | Run readiness and liveness probes without sensitive data exposure. | Present | Production monitoring integration needed |
| DEP-010 | Capture request IDs and operational logs. | Present | PHI-safe logging policy and retention needed |
| DEP-011 | Define backup and restore workflow. | Not implemented | Restore test required |
| DEP-012 | Define rollback workflow for application and data migrations. | Not implemented | Rollback drill required |
| DEP-013 | Define downtime/degraded-mode workflow. | Not implemented | Clinical operations approval required |
| DEP-014 | Prevent deployment from unapproved branches or local state. | Not implemented | CI/CD and branch protection needed |

## Deployment Runbook Draft

Each controlled deployment should record:

1. Deployment ID.
2. Release version, commit SHA and artifact reference.
3. Environment name and owner.
4. Configuration source and secret reference.
5. Database path/storage reference and migration state.
6. py-ard/IPD-IMGT/HLA data version.
7. SBOM and vulnerability-review reference.
8. Pre-deployment health/readiness results.
9. Deployment command or CI/CD job ID.
10. Post-deployment smoke checks.
11. Monitoring status.
12. Rollback decision point and owner.
13. Approvers and timestamp.
14. Deviations or anomalies.

## Rollback Criteria

Rollback should be triggered or formally considered when:

- service cannot start or readiness remains failed;
- database migration fails or produces unexpected schema state;
- report/comparison output differs from approved expected cases;
- authentication/authorization is broken;
- audit/export storage is unavailable;
- PHI/data-governance controls are violated;
- security scan finds release-blocking vulnerability;
- clinical workflow users cannot complete mandatory review tasks;
- critical defect or incident is discovered during deployment.

Rollback must preserve investigation evidence and must not delete records needed for CAPA or regulatory review.

## Release Decision States

| State | Meaning |
| --- | --- |
| Draft | Release package is being assembled. |
| Verification ready | Scope is frozen and ready for verification execution. |
| Validation ready | Verification blockers are closed and validation may proceed. |
| Release candidate | Release evidence is complete enough for approval review. |
| Approved non-clinical | Release is approved only for development, demo or validation planning. |
| Approved clinical-intended | Release is approved under controlled process for the defined clinical scope. |
| Rejected | Release is blocked by unresolved evidence, risk or approval issue. |
| Withdrawn | Release candidate is stopped and no longer current. |

## Clinical-Use Blockers

Clinical workflow deployment remains blocked until:

- release owner and approvers are assigned;
- controlled release checklist is approved;
- deployment runbook is approved and rehearsed;
- verification and validation reports are complete;
- cybersecurity/data/SOUP release evidence is complete;
- rollback, downtime and backup/restore procedures are tested;
- known issues and residual risks are reviewed;
- clinical and regulatory release approvals are recorded.

## Step 11 Conclusion

This document establishes the first release and deployment planning file. The Step 12 document-control, approval, claims-control, change-impact and gate-checklist drafts now define how this plan should be reviewed before any baseline or release decision. It does not promote the project beyond non-clinical use.
