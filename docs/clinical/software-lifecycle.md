# Software Lifecycle Draft

Status: Draft for clinical-readiness planning. This is not a completed IEC
62304 software lifecycle file. Not approved for clinical use.

This document defines the initial software lifecycle approach for the HLA
Transplantation Simulation project if it continues toward clinical-intended
medical device software development.

## Purpose

The purpose of this document is to define how software development,
verification, release, maintenance, and problem resolution should be controlled
as the project moves from non-clinical prototype toward potential medical device
software.

This document does not authorize clinical use and does not replace a full IEC
62304-compliant software development plan.

## Source Documents Reviewed

Internal project documents:

- [Intended Use](intended-use.md)
- [Regulatory Classification Draft](regulatory-classification.md)
- [Quality System Draft](quality-system.md)
- [Risk Management And Initial Risk Register](risk-register.md)
- [Backend API Component](../backend.md)
- [Backend Integration Guide](../backend-integration.md)
- [Data Policy](../data.md)
- [Software Requirements Specification Draft](software-requirements.md)
- [Traceability Matrix Draft](traceability-matrix.md)
- [Software Architecture Draft](software-architecture.md)
- [Verification Plan Draft](verification-plan.md)
- [Usability Engineering File Draft](usability-engineering.md)
- [Validation Plan Draft](validation-plan.md)
- [Cybersecurity Plan Draft](cybersecurity-plan.md)
- [Data Governance Plan Draft](data-governance.md)
- [SOUP And Dependency Register Draft](soup-dependency-register.md)

Official external references checked for this draft:

- IEC 62304:2006, Medical device software - Software life cycle processes:
  https://www.iso.org/standard/38421.html
- IEC 62304 product page, including scope for development and maintenance of
  medical device software:
  https://webstore.iec.ch/en/publication/6792
- ISO 14971:2019, Medical devices - Application of risk management to medical
  devices:
  https://www.iso.org/standard/72704.html
- IEC/TR 80002-1:2009, Medical device software - Guidance on applying ISO 14971
  to medical device software:
  https://www.iso.org/standard/54146.html
- European Commission MDCG guidance index, including medical device software,
  clinical evaluation/performance evaluation, cybersecurity, and PMS/vigilance:
  https://health.ec.europa.eu/medical-devices-sector/new-regulations/guidance-mdcg-endorsed-documents-and-other-guidance_en

## Lifecycle Scope

Current scope:

- non-clinical CLI and backend API;
- deterministic HLA comparison, reporting, export, and audit features;
- SQLite persistence;
- synthetic, demo, anonymized, or validation-planning data;
- GitHub-hosted source control and CI.

Future clinical-intended scope, if approved:

- clinical workflow frontend;
- role-based access and audit trail;
- controlled release packages;
- LIS/EHR/FHIR/HL7 integrations if required;
- validated runtime environments;
- post-release maintenance and anomaly handling;
- software lifecycle evidence linked to risk and requirements.

## Safety Class Working Assumption

IEC 62304 software safety class is not finalized in this draft.

Current planning assumptions:

- Current non-clinical prototype: no clinical software safety class assigned.
- Future clinical display/workflow support: at least a formal safety class
  assessment is required.
- Future donor suitability, donor acceptance/rejection, allocation, or clinical
  decision-support claims: conservative working assumption is the highest
  practical scrutiny until risk analysis and regulatory review determine the
  final safety class.

Because transplantation-related incorrect information can plausibly contribute
to serious harm if relied upon, safety classification must be reviewed by
clinical, risk, quality, software, and regulatory leads before clinical-intended
work proceeds.

## Software Lifecycle Processes

The project should establish these processes before clinical-intended release:

1. Software development planning.
2. Software requirements analysis.
3. Software architecture and design.
4. Software unit implementation and verification.
5. Software integration and integration testing.
6. Software system testing.
7. Software release.
8. Software maintenance.
9. Software risk management interface.
10. Software configuration management.
11. Software problem resolution.
12. SOUP and third-party dependency management.

## Lifecycle Deliverables

Minimum deliverables for a clinical-intended software lifecycle:

| Deliverable | Purpose | Status |
| --- | --- | --- |
| Software development plan | Defines lifecycle process, roles, tools, and deliverables | Not started |
| Software requirements specification | Defines testable software requirements | Draft started in step 7 |
| Traceability matrix | Links intended use, requirements, risks, controls, tests, validation, release | Draft started in step 7 |
| Software architecture document | Defines components, data flows, interfaces, failure modes | Draft started in step 8 |
| Detailed design records | Defines behavior for safety-related modules | Not started |
| Verification plan | Defines unit, integration, system, API, migration, and security tests | Draft started in step 8 |
| Verification report | Records executed tests and results | Not started |
| Usability engineering file | Defines safety-related user tasks, foreseeable use errors, UI controls and usability evidence | Draft started in step 9 |
| Validation plan | Defines clinical workflow validation and representative cases | Draft started in step 9 |
| Validation report | Records validation results and deviations | Not started |
| Release checklist | Confirms release readiness and approvals | Not started |
| Cybersecurity plan | Defines threat, vulnerability, access, secrets, logging and incident controls | Draft started in step 10 |
| Data-governance plan | Defines health-data classes, provenance, retention, access and incident controls | Draft started in step 10 |
| Maintenance plan | Defines change, patch, and anomaly handling after release | Not started |
| SOUP/dependency register | Controls third-party software, data sources and supplier review | Draft started in step 10 |

## Current Repository Controls

The current repository already has useful non-clinical engineering controls:

- Git version control;
- GitHub remote history;
- CI workflow on Windows;
- unit tests;
- backend API tests;
- OpenAPI smoke test;
- wheel/package smoke tests;
- non-clinical API envelopes;
- structured error handling;
- readiness/liveness probes;
- audit bundle generation;
- ignored runtime database, exports, pycache, and secrets;
- planning-level cybersecurity, data-governance and SOUP/dependency records.

These are helpful foundations, but they are not sufficient for a clinical
software lifecycle without controlled requirements, risk traceability,
validation evidence, release records, and maintenance/problem-resolution
processes.

## Software Requirements Process

Each software requirement should be:

- uniquely identified;
- testable;
- linked to intended use;
- linked to one or more risks when safety-related;
- linked to design/architecture;
- linked to verification tests;
- linked to validation evidence if workflow or clinical interpretation is
  affected;
- reviewed before implementation;
- change-controlled after baseline.

Requirement types should include:

- functional requirements;
- data requirements;
- API requirements;
- frontend workflow requirements;
- audit/logging requirements;
- security/access-control requirements;
- performance/availability requirements;
- interoperability requirements;
- usability requirements;
- non-clinical boundary/claims-control requirements.

## Architecture And Design Process

Architecture records should define:

- system boundaries;
- CLI, backend API, database, export, audit, and future frontend components;
- data-flow diagrams;
- external interfaces;
- trust boundaries;
- safety-related components;
- SOUP/dependency boundaries;
- failure handling;
- logging and audit design;
- migration and schema management;
- deployment environments.

Safety-related design decisions must link to risk controls and verification
coverage.

## Implementation Controls

Implementation should require:

- code review for all clinical-readiness changes;
- branch or pull-request workflow;
- no direct release from unreviewed local changes;
- static checks where feasible;
- unit tests for deterministic logic;
- integration tests for database/API/report/export behavior;
- migration tests for database changes;
- security review for authentication, authorization, secrets, logging, and data
  handling;
- documented rationale for any safety-related behavior.

## Verification Strategy

Verification should demonstrate that software requirements and design controls
are implemented correctly.

Required verification categories:

- unit tests for HLA comparison/reduction logic;
- database migration and schema tests;
- CLI command tests;
- backend API contract tests;
- structured error tests;
- export consistency tests;
- audit reproducibility tests;
- dependency/configuration tests;
- security and access-control tests;
- frontend workflow tests when UI exists;
- regression tests for every resolved safety-related defect.

Every safety-related requirement must have explicit verification evidence.

## Validation Boundary

IEC 62304-style software verification is not the same as clinical validation.

Clinical-intended validation must separately evaluate whether the software is
suitable for the intended workflow and users. Validation should be defined in a
validation plan and should use representative cases, expected outputs, clinical
review, usability evidence, and documented deviations.

No clinical validation claim is made by this lifecycle draft.

## Release Process

A release candidate should require:

1. Frozen release scope.
2. Linked intended-use version.
3. Linked regulatory-classification draft/version.
4. Requirements baseline.
5. Risk register review.
6. Verification completion.
7. Validation status review.
8. Known-issues review.
9. Dependency/SOUP review.
10. Security/privacy review.
11. Migration review.
12. User documentation review.
13. Release notes.
14. Tagged commit.
15. Approval by quality, software, regulatory, and clinical roles when
    clinical-intended.

Current releases are non-clinical only.

## Maintenance Process

Maintenance should control:

- bug fixes;
- dependency updates;
- security patches;
- HLA nomenclature/source data changes;
- database migrations;
- API contract changes;
- report wording changes;
- UI wording and layout changes;
- deployment configuration changes;
- operational incidents;
- CAPA-driven changes.

Each maintenance change must include impact analysis for:

- intended use;
- claims;
- regulatory classification;
- risk controls;
- requirements;
- verification;
- validation;
- cybersecurity;
- data protection;
- release notes and user communication.

## Problem Resolution Process

Anomalies should be recorded with:

- unique ID;
- affected version;
- environment;
- reporter;
- description;
- reproducibility;
- safety/security/privacy impact;
- linked risks and requirements;
- root cause when known;
- containment action;
- corrective action;
- verification of fix;
- regression test;
- closure approval.

Safety-related anomalies must trigger risk-register review.

## Configuration Management

Configuration items should include:

- source code;
- controlled documentation;
- requirements;
- risk register;
- tests;
- CI configuration;
- Dockerfile and deployment files;
- database migrations;
- pyproject/requirements files;
- release artifacts;
- SOUP/dependency versions;
- external data versions such as IMGT/HLA and py-ard data;
- validation datasets, if governed and allowed.

Configuration items must be identifiable and retrievable for each release.

## SOUP And Dependency Management

SOUP/dependencies include third-party software and data used without full
internal design control. The first register is now started in
[SOUP And Dependency Register Draft](soup-dependency-register.md).

Initial SOUP/dependency candidates:

- Python runtime;
- py-ard;
- FastAPI;
- uvicorn;
- SQLite;
- Python packaging/build tools;
- Docker base image;
- IPD-IMGT/HLA and py-ard data;
- future frontend framework;
- future authentication/authorization provider;
- future LIS/EHR/FHIR/HL7 libraries.

Each dependency should be listed with:

- name;
- version/source;
- intended use;
- risk relevance;
- verification approach;
- update policy;
- vulnerability monitoring;
- fallback/mitigation strategy.

## Lifecycle Traceability

The lifecycle process must trace:

```text
Intended Use
  -> Regulatory Classification
  -> Requirements
  -> Risks / Risk Controls
  -> Architecture / Design
  -> Implementation
  -> Verification
  -> Validation
  -> Release
  -> Maintenance / PMS feedback
```

The requirements specification and traceability matrix are now drafted at
planning level. They still require formal review, owner assignment, controlled
baseline, and links to architecture, verification, validation, release, and
maintenance records.

## Clinical-Use Blockers

Clinical use remains blocked until:

- software safety class is assessed;
- software development plan is approved;
- requirements specification is baselined;
- risk controls are linked to requirements and verification;
- architecture and data-flow records are approved;
- verification plan/report are complete;
- validation plan/report are complete;
- cybersecurity, data-governance and SOUP/dependency records are approved;
- maintenance and problem-resolution procedures are approved;
- release approval process is implemented;
- controlled clinical claims and labelling are approved.

## Open Lifecycle Decisions

- What IEC 62304 software safety class applies if clinical-intended use is
  pursued?
- Which issue tracker will be the controlled anomaly/problem-resolution system?
- Which branch/review model will be controlled for clinical development?
- Which requirements tool or format will be used?
- How will validation datasets be versioned and governed?
- Which CI checks are mandatory for release candidates?
- How will SOUP vulnerability monitoring be performed?
- How will hotfixes be handled in production clinical environments?
- Which artifacts form the software release package?

## Draft Conclusion

The project now has an initial software lifecycle planning document. It remains
a non-clinical project and does not yet have a completed IEC 62304 software
lifecycle file.

The usability engineering file, validation plan, cybersecurity plan,
data-governance plan and SOUP/dependency register are now drafted at planning
level. The next readiness step should create release, deployment, maintenance,
problem-resolution and CAPA planning artifacts, because controlled release
approval, rollback, incident handling and post-release monitoring remain open
before clinical use can be considered.
