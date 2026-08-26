# Quality System Draft

Status: Draft for clinical-readiness planning. This repository does not yet
implement a certified quality management system. Not approved for clinical use.

This document defines the quality-system foundation needed before the HLA
Transplantation Simulation project can be developed, validated, released, or
maintained as a clinical-intended software product.

## Purpose

The purpose of this draft is to define the minimum quality processes required to
control the project as it moves from a non-clinical software prototype toward a
possible medical-device software lifecycle.

This document does not certify the project, does not replace a full ISO 13485
quality management system, and does not authorize clinical use.

## Source Documents Reviewed

Internal project documents:

- [Intended Use](intended-use.md)
- [Regulatory Classification Draft](regulatory-classification.md)
- [Backend API Component](../backend.md)
- [Backend Integration Guide](../backend-integration.md)
- [Data Policy](../data.md)
- [Cybersecurity Plan Draft](cybersecurity-plan.md)
- [Data Governance Plan Draft](data-governance.md)
- [SOUP And Dependency Register Draft](soup-dependency-register.md)
- [Release And Deployment Plan Draft](release-deployment-plan.md)
- [Maintenance Plan Draft](maintenance-plan.md)
- [Problem Resolution And CAPA Plan Draft](problem-resolution-capa.md)

Official external references checked for this draft:

- ISO 13485:2016, Medical devices - Quality management systems - Requirements
  for regulatory purposes:
  https://www.iso.org/standard/59752.html
- ISO overview of ISO 13485 for medical devices:
  https://www.iso.org/iso-13485-medical-devices.html
- European Commission MDCG guidance index, including PRRC, PMS/vigilance,
  software, classification, cybersecurity, and standardisation guidance:
  https://health.ec.europa.eu/medical-devices-sector/new-regulations/guidance-mdcg-endorsed-documents-and-other-guidance_en
- MDCG 2019-7 rev.1, guidance on the Person Responsible for Regulatory
  Compliance (PRRC), December 2023:
  https://health.ec.europa.eu/latest-updates/update-mdcg-2019-7-rev1-guidance-article-15-medical-device-regulation-mdr-and-vitro-diagnostic-2023-12-19_en
- European Commission step-by-step guide for medical device manufacturers:
  https://health.ec.europa.eu/publications/step-step-guide-medical-device-manufacturers_en

## Quality Scope

Current scope:

- non-clinical software development;
- backend API and CLI maintenance;
- documentation for clinical-readiness planning;
- deterministic report, export, and audit artifacts;
- synthetic, demo, anonymized, or validation-planning data only.

Future controlled scope, if clinical-intended development proceeds:

- medical-device software planning and lifecycle controls;
- requirements, risk management, verification, validation, usability, release,
  post-release maintenance, and incident handling;
- clinical workflow and frontend controls;
- data governance and cybersecurity controls;
- supplier and dependency controls.

## Quality Policy Draft

The project should be controlled so that:

- intended use and claims are explicit and controlled;
- non-clinical boundaries remain visible until clinical use is approved;
- requirements are traceable to risks, implementation, tests, and validation;
- releases are reproducible and reviewed;
- changes are assessed for safety, security, regulatory, and clinical impact;
- defects, complaints, incidents, and feedback are captured and investigated;
- records are retained in a controlled way;
- clinical-intended use is blocked until required regulatory and validation gates
  are complete.

## Roles And Responsibilities

The following roles must be assigned before clinical-intended development:

| Role | Responsibility |
| --- | --- |
| Product owner | Owns intended use, product scope, and roadmap decisions |
| Clinical lead | Reviews clinical workflow, safety relevance, and clinical assumptions |
| Regulatory lead | Owns regulatory route, classification rationale, and claims control |
| Quality lead | Owns QMS process, document control, CAPA, release records, and audits |
| Software lead | Owns architecture, implementation controls, code review, and technical debt |
| Test/validation lead | Owns verification, validation protocols, test evidence, and traceability |
| Security/data lead | Owns access control, secrets, audit logs, backup, retention, and privacy controls |
| PRRC candidate | Assessed if a manufacturer route under MDR/IVDR is pursued |

No single developer action should approve clinical claims, clinical release, or
production clinical deployment without the responsible roles above.

## Required Quality Procedures

The following procedures must exist before clinical-intended release planning:

1. Document and record control.
2. Intended-use and claims control.
3. Requirements management.
4. Risk management interface.
5. Software design and development control.
6. Code review and branch control.
7. Verification and validation control.
8. Release and deployment control.
9. Supplier and dependency control.
10. Cybersecurity and data-protection control.
11. Complaint, feedback, incident, and CAPA control.
12. Post-market surveillance and vigilance planning, if placed on the market as
    a medical device.
13. Training and role authorization control.
14. Backup, restoration, and business-continuity control.
15. Internal audit and management review process.

## Document And Record Control

Controlled documents should include:

- intended use;
- regulatory classification rationale;
- quality system plan;
- requirements specification;
- risk management file;
- architecture and data-flow documents;
- software development plan;
- verification protocol and report;
- validation protocol and report;
- usability plan and report;
- cybersecurity plan and assessment;
- data-governance plan and privacy assessment records;
- SOUP/dependency register and SBOM records;
- release/deployment plan and release records;
- maintenance plan;
- problem-resolution and CAPA records;
- release notes;
- known-issues list;
- clinical evaluation or performance evaluation plan, if applicable;
- post-market surveillance and vigilance plans, if applicable.

Minimum controls:

- each controlled document has an owner;
- each controlled document has a version or revision history;
- changes require review and approval;
- obsolete documents remain retrievable but are not used as current process;
- release artifacts link to the exact document versions used.

## Change Control

Every change intended for clinical-readiness work must be assessed for:

- intended-use impact;
- claims impact;
- regulatory classification impact;
- risk impact;
- cybersecurity impact;
- data-protection impact;
- usability impact;
- test and validation impact;
- deployment impact;
- need for user communication or release notes.

Suggested change categories:

- documentation-only change;
- non-safety software change;
- safety-related software change;
- cybersecurity change;
- data model or migration change;
- clinical workflow change;
- claims or labelling change;
- release-blocking defect fix.

## Design And Development Controls

Before clinical-intended release, each feature should trace through:

1. Intended use.
2. User need.
3. Software requirement.
4. Risk control, if safety-related.
5. Architecture or design element.
6. Implementation reference.
7. Verification test.
8. Validation evidence, if workflow or clinical use is affected.
9. Release record.

The existing unit tests and CI are useful technical verification evidence, but
they are not sufficient clinical validation evidence.

## Software Configuration Management

Minimum configuration controls:

- Git is the source of truth for software and controlled documentation.
- All release commits are tagged.
- Release builds are reproducible from a tagged commit.
- Runtime data, SQLite databases, py-ard data, and secrets are not committed.
- Dependency versions are reviewed before release.
- CI status is captured for each release candidate.
- Backend API contract changes are versioned.
- Clinical-intended breaking changes require impact assessment.

## Supplier And Dependency Control

Potential suppliers/dependencies include:

- Python runtime;
- py-ard;
- FastAPI and uvicorn;
- SQLite;
- third-party Python packages;
- Docker base images;
- IPD-IMGT/HLA and py-ard data;
- future EHR/LIS/FHIR/HL7 integration libraries;
- hosting, logging, backup, and monitoring providers.

Each supplier/dependency should have:

- intended use in the product;
- version or source control;
- update policy;
- vulnerability monitoring approach;
- fallback or mitigation plan for critical dependencies;
- release-impact assessment when changed.

## Verification Controls

Verification should answer: did we build the software correctly?

Current verification evidence includes:

- unit tests;
- backend API tests;
- OpenAPI contract smoke tests;
- packaging smoke tests;
- CI workflow checks.

Before clinical-intended release, add:

- requirements-based tests;
- migration and rollback tests;
- API backward-compatibility tests;
- role/access-control tests;
- audit-log integrity tests;
- error-handling and downtime tests;
- security tests;
- frontend workflow tests, if a clinical UI exists.

## Validation Controls

Validation should answer: did we build the right software for the intended use?

Before clinical-intended release, validation must include:

- frozen intended use;
- representative user workflows;
- anonymized or ethically approved retrospective cases;
- expected-output definitions reviewed by qualified experts;
- edge cases and missing-data cases;
- comparison against expert review where applicable;
- usability validation for clinical UI tasks;
- documented deviations and residual risk assessment;
- clinical stakeholder sign-off.

## Release Control

A release candidate must not be promoted to clinical-intended use unless the
release record includes:

- release commit/tag;
- build artifacts;
- dependency list;
- database migration status;
- verification results;
- validation status;
- known issues;
- risk file status;
- cybersecurity review status;
- data-protection review status;
- user documentation status;
- approval signatures or equivalent controlled approvals.

## CAPA, Feedback, And Incident Handling

The project must define how to capture and handle:

- user feedback;
- bug reports;
- complaints;
- suspected incorrect outputs;
- security vulnerabilities;
- data-protection incidents;
- clinical near-misses;
- production incidents;
- corrective and preventive actions.

Each record should include:

- unique identifier;
- reporter and date;
- affected version/environment;
- severity and safety impact;
- investigation outcome;
- containment action;
- corrective action;
- preventive action;
- verification of effectiveness;
- closure approval.

## Training And Authorization

Before clinical workflow use, the project must define:

- user roles;
- required training per role;
- authorized tasks per role;
- training records;
- access review frequency;
- offboarding process;
- emergency access process, if any.

## Data Governance And Privacy Interface

The quality system must interface with data governance for:

- identifiable vs anonymized/pseudonymized data;
- lawful basis for processing;
- data minimization;
- access logging;
- retention and deletion;
- backup and restoration;
- export control;
- audit-bundle storage;
- breach/incident response.

This draft does not replace a GDPR/data-protection assessment.

## Internal Audit And Management Review

Before clinical-intended release, establish:

- internal audit schedule;
- audit checklist for software lifecycle, risk, validation, security, and
  documentation controls;
- nonconformity handling;
- management review cadence;
- review inputs such as defects, CAPA status, validation status, supplier
  issues, cybersecurity issues, and user feedback;
- review outputs such as resourcing decisions, process changes, and release
  decisions.

## Minimum Repository Actions

Near-term actions that can be implemented in this repository:

- review and baseline the requirements traceability matrix;
- add risk register;
- add software development plan;
- review and baseline the verification plan;
- review and baseline the usability engineering file;
- add claims matrix;
- add release checklist template;
- add change impact checklist template;
- add CAPA/incident template;
- review and baseline supplier/dependency register and cybersecurity/data-governance records;
- review and baseline release/deployment, maintenance, problem-resolution and CAPA records;
- add document-control index, claims matrix, change-impact checklist and approval matrix;
- review and baseline architecture and data-flow records.

## Clinical-Use Blockers

Clinical use remains blocked until:

- intended use is frozen and approved;
- regulatory route and classification are reviewed;
- manufacturer/legal responsible entity is identified;
- QMS ownership is assigned;
- quality procedures are approved;
- requirements and risks are traceable;
- verification and validation evidence are complete;
- usability validation is complete for clinical UI;
- security and privacy controls are approved;
- release is approved under controlled process.

## Open Quality Decisions

- Who will own the QMS?
- Will ISO 13485 certification be pursued, or will an equivalent internal QMS be
  used for a limited in-house route?
- Who is the manufacturer or legal responsible entity?
- Who is the PRRC candidate if MDR/IVDR applies?
- Which documents are controlled records vs planning drafts?
- What release process will be used for clinical-intended builds?
- Where will validation evidence and audit records be stored?
- Which issue tracker will be the controlled complaint/CAPA system?
- What is the retention period for design, validation, release, and audit
  records?

## Draft Conclusion

The project now has a planning-level quality-system outline, but it does not yet
have an implemented or certified QMS.

The requirements specification, traceability matrix, architecture draft,
verification plan, usability engineering file, validation plan, cybersecurity
plan, data-governance plan, SOUP/dependency register, release/deployment plan,
maintenance plan and problem-resolution/CAPA plan are now drafted at planning
level. The next readiness step should create document-control, claims-control,
change-impact and approval-matrix records before implementation expands toward
clinical-intended workflows.
