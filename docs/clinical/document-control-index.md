# Проект На Document Control Index

Статус: Draft за controlled-baseline planning. Не е одобрен controlled record и не разрешава клинична употреба.

Този документ създава начална document-control рамка за clinical-readiness материалите на HLA Transplantation Simulation проекта. Той не замества ISO 13485/QMS процедура и не доказва, че документите са formally approved или baselined.

## Цел

Целта е да има един централен индекс за:

- controlled document candidates;
- owners and approvers;
- draft/baseline status;
- version and review expectations;
- change-control route;
- release and clinical-readiness gates.

Документите в този repository остават planning drafts, докато не бъдат reviewed, approved, versioned и поставени под реален document-control process.

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
- [Maintenance Plan Draft](maintenance-plan.md)
- [Problem Resolution And CAPA Plan Draft](problem-resolution-capa.md)
- [Approval Matrix Draft](approval-matrix.md)
- [Claims Control Matrix Draft](claims-control-matrix.md)
- [Change Impact Checklist Draft](change-impact-checklist.md)
- [Clinical Readiness Gate Checklist Draft](clinical-readiness-gate-checklist.md)

Официални външни references, проверени на 2026-08-26:

- ISO 13485:2016, Medical devices - quality management systems:
  https://www.iso.org/standard/59752.html
- FDA Quality Management System Regulation (QMSR), updated 2026-02-02:
  https://www.fda.gov/medical-devices/postmarket-requirements-devices/quality-management-system-regulation-qmsr
- IEC 62304:2006+AMD1:2015, Medical device software - software life cycle processes:
  https://webstore.iec.ch/en/publication/22794
- ISO 14971:2019, Medical devices - application of risk management:
  https://www.iso.org/standard/72704.html
- MDCG guidance index for MDR/IVDR, including software, PMS/vigilance and PRRC guidance:
  https://health.ec.europa.eu/medical-devices-sector/new-regulations/guidance-mdcg-endorsed-documents-and-other-guidance_en

## Document Control Requirements

| ID | Requirement | Current status | Evidence needed |
| --- | --- | --- | --- |
| DOCCTRL-001 | Every controlled document candidate shall have unique title, path and purpose. | Draft index started | Approved document-control index |
| DOCCTRL-002 | Every controlled document candidate shall have an assigned owner role. | Role placeholders drafted | Named owner assignment |
| DOCCTRL-003 | Every controlled document candidate shall have approver roles before baseline. | Draft approver matrix started | Approval records |
| DOCCTRL-004 | Document status shall distinguish draft, review, approved baseline, obsolete and retired. | Draft values defined | Controlled status log |
| DOCCTRL-005 | Baseline versions shall be linked to exact Git commit SHA or release tag. | Planned | Baseline record |
| DOCCTRL-006 | Changes after baseline shall require change-impact assessment. | Draft checklist started | Completed change-impact records |
| DOCCTRL-007 | Clinical claims shall be controlled through a claims matrix. | Draft matrix started | Approved claims matrix |
| DOCCTRL-008 | Obsolete documents shall remain retrievable but not current. | Planned | Archive/retention process |
| DOCCTRL-009 | Clinical-intended release shall use only approved current documents. | Planned | Release checklist evidence |
| DOCCTRL-010 | Document localization shall preserve technical IDs and meaning. | Draft rule present | Localization review record |
| DOCCTRL-011 | Document reviews shall include quality, clinical, regulatory, software and security/data roles when relevant. | Draft rule present | Review signatures or equivalent approvals |
| DOCCTRL-012 | The document-control index shall be reviewed before any clinical pilot or donor-situation workflow. | Planned | Gate checklist evidence |

## Baseline Rules

| ID | Rule | Meaning |
| --- | --- | --- |
| BASE-001 | Draft | Work-in-progress planning material; not controlled or approved. |
| BASE-002 | Review candidate | Ready for assigned reviewers but not approved. |
| BASE-003 | Approved baseline | Approved by required roles and linked to commit/tag. |
| BASE-004 | Superseded | Replaced by a newer approved baseline. |
| BASE-005 | Obsolete | Not current and must not be used for active release decisions. |
| BASE-006 | Retired | Preserved for history but outside active lifecycle scope. |
| BASE-007 | Baseline package | Set of mutually consistent approved documents for a defined release or gate. |
| BASE-008 | Change freeze | Period where only approved changes may enter the baseline candidate. |
| BASE-009 | Baseline deviation | Known gap or mismatch accepted only with owner, rationale and expiry/review date. |
| BASE-010 | Localization baseline | Translated record reviewed to preserve original controlled meaning. |
| BASE-011 | Release baseline | Baseline package used for a release candidate. |
| BASE-012 | Clinical-readiness baseline | Baseline package used to decide whether clinical pilot work may proceed. |

## Controlled Document Candidates

| ID | Path | Purpose | Owner role | Approver roles | Current status |
| --- | --- | --- | --- | --- | --- |
| DOC-001 | `docs/clinical/intended-use.md` | Intended use and boundary | Product owner | Clinical, regulatory, quality | Draft |
| DOC-002 | `docs/clinical/regulatory-classification.md` | MDR/IVDR/FDA route planning | Regulatory lead | Clinical, quality, product | Draft |
| DOC-003 | `docs/clinical/quality-system.md` | QMS planning | Quality lead | Regulatory, product, software | Draft |
| DOC-004 | `docs/clinical/risk-register.md` | Risk management seed file | Quality lead | Clinical, software, security/data | Draft |
| DOC-005 | `docs/clinical/software-lifecycle.md` | IEC 62304-style lifecycle planning | Software lead | Quality, regulatory, validation | Draft |
| DOC-006 | `docs/clinical/software-requirements.md` | Software requirements | Software lead | Clinical, quality, validation, security/data | Draft |
| DOC-007 | `docs/clinical/traceability-matrix.md` | Risk/requirement/evidence traceability | Validation lead | Quality, software, clinical, security/data | Draft |
| DOC-008 | `docs/clinical/software-architecture.md` | Architecture, interfaces, trust boundaries | Software lead | Security/data, quality, validation | Draft |
| DOC-009 | `docs/clinical/verification-plan.md` | Verification strategy and test matrix | Verification lead | Software, quality, security/data | Draft |
| DOC-010 | `docs/clinical/usability-engineering.md` | Usability and use-error planning | Usability/validation lead | Clinical, quality, regulatory | Draft |
| DOC-011 | `docs/clinical/validation-plan.md` | Clinical workflow validation planning | Validation lead | Clinical, quality, regulatory | Draft |
| DOC-012 | `docs/clinical/cybersecurity-plan.md` | Cybersecurity planning | Security/data lead | Software, quality, regulatory | Draft |
| DOC-013 | `docs/clinical/data-governance.md` | Health-data governance planning | Security/data lead | Quality, regulatory, clinical | Draft |
| DOC-014 | `docs/clinical/soup-dependency-register.md` | SOUP/dependency inventory planning | Software lead | Security/data, quality | Draft |
| DOC-015 | `docs/clinical/release-deployment-plan.md` | Release and deployment planning | Operations lead | Quality, software, security/data | Draft |
| DOC-016 | `docs/clinical/maintenance-plan.md` | Maintenance and post-release planning | Software lead | Quality, operations, security/data | Draft |
| DOC-017 | `docs/clinical/problem-resolution-capa.md` | Problem resolution and CAPA interface | Quality lead | Regulatory, software, security/data | Draft |
| DOC-018 | `docs/clinical/claims-control-matrix.md` | Allowed/prohibited claims | Regulatory lead | Clinical, quality, product | Draft |
| DOC-019 | `docs/clinical/change-impact-checklist.md` | Change-impact checklist | Quality lead | Software, regulatory, security/data | Draft |
| DOC-020 | `docs/clinical/approval-matrix.md` | Owners and approval responsibilities | Quality lead | Product, regulatory, clinical | Draft |
| DOC-021 | `docs/clinical/clinical-readiness-gate-checklist.md` | Clinical-readiness gate checklist | Quality lead | Clinical, regulatory, software, security/data | Draft |
| DOC-022 | `README.md` | Root user-facing boundary and quick start | Product owner | Clinical/regulatory review if claims change | Draft |
| DOC-023 | `docs/backend.md` | Backend API component documentation | Software lead | Security/data, product | Draft |
| DOC-024 | `docs/backend-integration.md` | Integration guidance for larger app | Software lead | Security/data, clinical, regulatory | Draft |
| DOC-025 | `docs/data.md` | Repository data policy | Security/data lead | Quality, regulatory | Draft |

## Baseline Package Draft

Current baseline package state:

- Package ID: `BASEPKG-STEP12-DRAFT`.
- Scope: non-clinical clinical-readiness planning documents.
- Approval state: not approved.
- Release state: not clinical-intended.
- Allowed use: planning, review, gap analysis, future implementation planning.
- Prohibited use: clinical donor decision, clinical pilot, production deployment, marketing claim, regulatory submission without formal review.

## Required Baseline Metadata

Each approved baseline should record:

- baseline ID;
- document IDs included;
- file paths;
- document versions;
- Git commit SHA or release tag;
- review date;
- owner;
- approvers;
- deviations;
- expiry or next review date;
- allowed use;
- prohibited use;
- linked release or gate decision.

## Change Control Interface

After baseline, every document change must be classified using [Change Impact Checklist Draft](change-impact-checklist.md). Changes affecting intended use, claims, risk controls, validation, cybersecurity, data governance, release, clinical workflow or user-facing wording require assigned review before merge or release.

## Clinical-Use Blockers

Clinical workflow use remains blocked until:

- document-control owner is assigned;
- controlled document system or repository process is approved;
- document statuses are formally managed;
- required owners and approvers are named;
- baseline package is reviewed and approved;
- claims matrix is approved;
- change-impact process is enforced;
- clinical-readiness gate checklist is completed.

## Step 12 Conclusion

This document creates the planning-level document-control index and baseline package structure. It does not convert the repository documents into approved controlled records by itself.
