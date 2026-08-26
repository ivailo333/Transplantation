# Проект На Maintenance Plan

Статус: Draft за планиране на клинична готовност. Не е одобрен за клинична употреба.

Този документ дефинира начална maintenance рамка за HLA Transplantation Simulation проекта. Той не е approved maintenance procedure, post-market surveillance plan или production support contract.

## Цел

Целта е да се опише как промените след release трябва да бъдат triaged, reviewed, implemented, verified, validated and released, ако проектът се развива към clinical-intended software component.

Maintenance planning трябва да обхване:

- defect fixes;
- cybersecurity patches;
- dependency and SOUP updates;
- HLA source-data updates;
- database migrations;
- backend API changes;
- frontend workflow changes;
- documentation and claims changes;
- operational incidents;
- user feedback and post-release monitoring.

## Изходни Документи

Вътрешни source документи:

- [Български Clinical Readiness Обзор](bg-readiness-overview.md)
- [Quality System Draft](quality-system.md)
- [Risk Management And Initial Risk Register](risk-register.md)
- [Software Lifecycle Draft](software-lifecycle.md)
- [Software Requirements Specification Draft](software-requirements.md)
- [Traceability Matrix Draft](traceability-matrix.md)
- [Software Architecture Draft](software-architecture.md)
- [Verification Plan Draft](verification-plan.md)
- [Validation Plan Draft](validation-plan.md)
- [Cybersecurity Plan Draft](cybersecurity-plan.md)
- [Data Governance Plan Draft](data-governance.md)
- [SOUP And Dependency Register Draft](soup-dependency-register.md)
- [Release And Deployment Plan Draft](release-deployment-plan.md)
- [Problem Resolution And CAPA Plan Draft](problem-resolution-capa.md)
- [Document Control Index Draft](document-control-index.md)
- [Approval Matrix Draft](approval-matrix.md)
- [Claims Control Matrix Draft](claims-control-matrix.md)
- [Change Impact Checklist Draft](change-impact-checklist.md)
- [Clinical Readiness Gate Checklist Draft](clinical-readiness-gate-checklist.md)

Официални външни references, проверени на 2026-08-26:

- ISO 13485:2016, Medical devices - quality management systems:
  https://committee.iso.org/standard/59752.html
- IEC 62304:2006, Medical device software - software life cycle processes:
  https://committee.iso.org/standard/38421.html
- ISO 14971:2019, Medical devices - application of risk management:
  https://www.iso.org/standard/72704.html
- ISO/TR 24971:2020, guidance on the application of ISO 14971:
  https://www.iso.org/standard/74437.html
- FDA, Postmarket Management of Cybersecurity in Medical Devices:
  https://www.fda.gov/regulatory-information/search-fda-guidance-documents/postmarket-management-cybersecurity-medical-devices
- FDA, Postmarket Requirements for Devices:
  https://www.fda.gov/medical-devices/device-advice-comprehensive-regulatory-assistance/postmarket-requirements-devices
- European Commission MDCG guidance index, including PMS/vigilance guidance:
  https://health.ec.europa.eu/medical-devices-sector/new-regulations/guidance-mdcg-endorsed-documents-and-other-guidance_en

## Maintenance Scope

Current scope:

- non-clinical project maintenance;
- documentation and planning updates;
- bug fixes for CLI/backend/frontend prototype behavior;
- dependency updates for development/runtime safety;
- test and CI maintenance.

Future clinical-intended scope, if approved:

- maintenance under controlled QMS;
- post-release monitoring and feedback intake;
- anomaly/problem resolution;
- CAPA interface;
- cybersecurity vulnerability handling;
- source-data and dependency updates with risk impact analysis;
- controlled release of patches and updates;
- user communication when safety, security or workflow impact exists.

## Maintenance Controls

| ID | Control | Linked risk areas | Evidence needed |
| --- | --- | --- | --- |
| MNT-001 | Maintain a controlled maintenance plan before any clinical-intended release. | OPS, SEC, AUD, VAL | Approved maintenance procedure |
| MNT-002 | Classify every change by safety, security, privacy, clinical workflow and regulatory impact. | RM-013, RM-014, RM-015, RM-018, RM-024 | Change-impact assessment |
| MNT-003 | Require requirements/risk/traceability impact review for maintained items. | RM-006, RM-008, RM-018 | Traceability update record |
| MNT-004 | Require verification for every software maintenance change. | RM-006, RM-007, RM-012, RM-017 | Verification evidence |
| MNT-005 | Require validation/usability impact review for clinical workflow or user-facing changes. | RM-010, RM-011, RM-020, RM-025 | Validation/usability decision |
| MNT-006 | Control HLA source-data and py-ard updates as safety-relevant maintenance. | RM-004, RM-006, RM-015 | Data-source update review |
| MNT-007 | Control dependency and container updates through SOUP/SBOM review. | RM-015 | SBOM and vulnerability review |
| MNT-008 | Control database migrations with migration, backup, restore and rollback evidence. | RM-012, RM-024 | Migration test and restore test |
| MNT-009 | Maintain backward-compatible API behavior unless breaking change is approved. | RM-009, RM-017, RM-023 | API contract tests and release note |
| MNT-010 | Maintain logs, audit bundles and release records for investigation. | RM-008, RM-017, RM-021 | Record retention evidence |
| MNT-011 | Triage cybersecurity vulnerabilities with safety and privacy impact. | RM-013, RM-015, RM-021 | Vulnerability triage record |
| MNT-012 | Define emergency hotfix path that still records evidence and approvals. | RM-016, RM-017, RM-024 | Hotfix record |
| MNT-013 | Feed post-release monitoring into risk management and CAPA. | RM-006, RM-014, RM-019, RM-021 | Monitoring review record |
| MNT-014 | Retire or archive unsupported versions with user communication and retrieval of records. | RM-016, RM-024 | Retirement record |

## Change Types

| ID | Change type | Examples | Minimum review |
| --- | --- | --- | --- |
| CHG-001 | Documentation-only | README, planning docs, usage notes | Claims, regulatory and QMS review if clinical wording changes |
| CHG-002 | Non-safety bug fix | Display typo, local helper issue | Code review and regression test |
| CHG-003 | Safety-related logic change | comparison, report semantics, missing-data behavior | Risk, requirements, verification and validation impact |
| CHG-004 | API contract change | endpoint, request/response schema, status mapping | API tests, integration review and release note |
| CHG-005 | Database/migration change | schema update, migration behavior | Migration tests, backup/restore and rollback review |
| CHG-006 | Frontend workflow change | clinical warning, review step, user note handling | Usability and validation impact review |
| CHG-007 | Security change | auth, CORS, logging, secrets, gateway | Security review and targeted tests |
| CHG-008 | Dependency/SOUP change | Python package, Docker base image | SOUP register, SBOM and vulnerability review |
| CHG-009 | HLA reference-data change | py-ard or IPD-IMGT/HLA version update | Output comparison, source-data review, validation impact |
| CHG-010 | Deployment/config change | host, storage, monitoring, environment | Deployment checklist and smoke tests |
| CHG-011 | Claims/labelling change | wording implying clinical use or benefit | Regulatory/clinical/quality approval |
| CHG-012 | Emergency hotfix | security or availability issue requiring rapid patch | Expedited triage, limited release approval, follow-up CAPA review |

## Maintenance Workflow

1. Intake change request, defect, vulnerability, data-source update or feedback.
2. Assign owner and unique ID.
3. Classify change type and impact.
4. Link affected requirements, risks, architecture and verification items.
5. Decide whether validation/usability/regulatory review is needed.
6. Implement under branch/review control.
7. Execute required tests and reviews.
8. Update controlled documents and traceability.
9. Prepare release package or patch record.
10. Approve, reject or defer the maintenance release.
11. Monitor post-release outcome.
12. Feed findings into risk management and CAPA if needed.

## HLA Source-Data Maintenance

Updates to py-ard or IPD-IMGT/HLA data can change output semantics. Before a controlled update:

- record old and new source-data version;
- record source and checksum where practical;
- run deterministic report/comparison regression cases;
- identify changed outputs and explain expected differences;
- review report metadata and user-facing wording;
- assess validation dataset impact;
- update SOUP register and release record;
- communicate impact to users if clinical workflow use is approved.

## Cybersecurity Maintenance

Security maintenance must include:

- monitoring dependency and platform advisories;
- vulnerability intake and triage;
- patch planning by severity and exploitability;
- verification of security fixes;
- release or mitigation decision;
- coordinated disclosure and user communication if applicable;
- review of whether the risk register, SOUP register or security plan changes.

## Post-Release Monitoring

| ID | Monitoring source | Review purpose |
| --- | --- | --- |
| MON-001 | User feedback | Identify usability, workflow and comprehension issues |
| MON-002 | Support tickets | Identify recurring defects or configuration issues |
| MON-003 | Error logs and request IDs | Detect error trends and failed workflows |
| MON-004 | Readiness/liveness monitoring | Detect availability and deployment issues |
| MON-005 | Audit bundle review | Confirm reproducibility and investigate discrepancies |
| MON-006 | Dependency advisories | Detect vulnerable packages and containers |
| MON-007 | HLA source-data release notes | Assess source-data update impact |
| MON-008 | Validation deviations | Identify needed maintenance or design changes |
| MON-009 | Security events | Detect unauthorized access or suspicious behavior |
| MON-010 | Data incidents | Identify privacy/data-governance breakdowns |
| MON-011 | Clinical review feedback | Detect unsafe interpretation or workflow mismatch |
| MON-012 | Regulatory guidance updates | Assess continued conformity of evidence strategy |

## Version Support Draft

Each release should have:

- version identifier;
- release date;
- supported environments;
- dependency set;
- known issues;
- support status;
- end-of-support date or review cadence;
- migration compatibility;
- rollback compatibility;
- record-retention status.

Unsupported versions must not remain in clinical workflow use without documented risk acceptance.

## Clinical-Use Blockers

Clinical workflow use remains blocked until:

- maintenance owner and process are approved;
- change-impact workflow is implemented;
- problem-resolution and CAPA workflow is implemented;
- vulnerability monitoring is active;
- source-data update process is verified;
- migration/rollback process is verified;
- post-release monitoring process is approved;
- user communication and version-support rules are defined.

## Step 11 Conclusion

This document establishes maintenance planning for future controlled releases. The Step 12 baseline package now defines owner, approval, claims and change-impact controls that must govern maintenance work. It does not create post-market approval, clinical support coverage or permission for donor-situation use.
