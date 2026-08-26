# Проект На Cybersecurity Plan

Статус: Draft за планиране на клинична готовност. Не е одобрен за клинична употреба.

Този документ дефинира начална cybersecurity рамка за HLA Transplantation Simulation проекта като неклиничен backend компонент и като бъдещ компонент в по-голямо clinical workflow приложение. Той не представлява завършена cybersecurity risk assessment, penetration test, production hardening record или regulatory submission evidence.

## Цел

Целта на този draft е да дефинира security controls, evidence needs и open blockers преди проектът да обработва identifiable health data или да бъде използван в клиничен workflow при евентуална донорска ситуация.

Security planning трябва да бъде свързан с:

- intended use и claims;
- risk management file;
- software requirements;
- software architecture и trust boundaries;
- verification, validation и usability evidence;
- SOUP/dependency register;
- data-governance controls;
- release, maintenance, vulnerability disclosure и incident response.

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
- [Data Governance Plan Draft](data-governance.md)
- [SOUP And Dependency Register Draft](soup-dependency-register.md)
- [Backend API Component](../backend.md)
- [Backend Integration Guide](../backend-integration.md)
- [Data Policy](../data.md)

Официални външни references, проверени на 2026-08-26:

- FDA, Cybersecurity in Medical Devices: Quality Management System Considerations and Content of Premarket Submissions, final guidance, February 2026:
  https://www.fda.gov/regulatory-information/search-fda-guidance-documents/cybersecurity-medical-devices-quality-management-system-considerations-and-content-premarket
- FDA, Postmarket Management of Cybersecurity in Medical Devices, final guidance, December 2016:
  https://www.fda.gov/regulatory-information/search-fda-guidance-documents/postmarket-management-cybersecurity-medical-devices
- FDA, Cybersecurity in Medical Devices FAQ:
  https://www.fda.gov/medical-devices/digital-health-center-excellence/cybersecurity-medical-devices-frequently-asked-questions-faqs
- MDCG 2019-16 rev.1, Guidance on cybersecurity for medical devices, listed in the European Commission MDCG guidance index:
  https://health.ec.europa.eu/medical-devices-sector/new-regulations/guidance-mdcg-endorsed-documents-and-other-guidance_en
- IMDRF/CYBER WG/N60, Principles and Practices for Medical Device Cybersecurity:
  https://www.imdrf.org/documents/principles-and-practices-medical-device-cybersecurity
- IMDRF/CYBER WG/N73, Principles and Practices for Software Bill of Materials for Medical Device Cybersecurity:
  https://www.imdrf.org/documents/principles-and-practices-software-bill-materials-medical-device-cybersecurity
- NIST SP 800-218, Secure Software Development Framework:
  https://csrc.nist.gov/pubs/sp/800/218/final
- NIST Cybersecurity Framework 2.0 resource center:
  https://www.nist.gov/cyberframework
- ISO/IEC 27001:2022, Information security management systems:
  https://www.iso.org/standard/27001
- ISO 27799:2025, Health informatics - information security controls in health:
  https://www.iso.org/standard/84647.html

## Cybersecurity Scope

Current in-scope system:

- local CLI;
- FastAPI backend API with `/v1` endpoints;
- static frontend validation prototype and local proxy;
- SQLite persistence;
- deterministic exports and audit bundles;
- runtime configuration through environment values or `backend.env`;
- local py-ard and IPD-IMGT/HLA data.

Future in-scope system, if clinical-intended development proceeds:

- authenticated clinical frontend in the larger application;
- role-based workflows and human review;
- production API gateway, TLS and network segmentation;
- secrets management;
- monitored logs and audit events;
- backup, restore and retention controls;
- vulnerability monitoring and patch process;
- coordinated vulnerability disclosure;
- supplier and dependency management;
- incident response and postmarket cybersecurity monitoring.

Out of scope for this draft:

- completed threat model;
- completed penetration test;
- production cloud architecture approval;
- formal cyber risk acceptability;
- legal/regulatory determination of whether the future system is a cyber device;
- authorization for identifiable health data processing.

## Current Security Posture

| Area | Current control | Clinical-use gap |
| --- | --- | --- |
| API exposure | Local default host `127.0.0.1`, versioned `/v1` endpoints, optional `X-API-Key` for protected endpoints | No clinical RBAC, no session management, no production identity provider |
| Transport | Local HTTP for prototype use | TLS must be enforced by gateway or deployment platform before clinical use |
| Configuration | `backend.env.example`, environment overrides, examples without secrets | Secrets vault, rotation and access review not implemented |
| Logs | Request IDs and structured backend logging | PHI-safe logging rules, log retention and monitoring not approved |
| Runtime data | `*.db`, logs, exports and env files ignored in Git | Production storage controls, backup/restore and retention not approved |
| Dependency control | `pyproject.toml`, `requirements*.txt`, `Dockerfile` | SBOM, vulnerability monitoring and supplier review not baselined |
| Error handling | Structured API errors with request IDs and specific encoding/IO mapping | Support workflow, incident routing and log review process not approved |
| Clinical workflow | Non-clinical notices and no clinical decision fields | Human sign-off, authorization and audit trail must be owned by larger app |

## Security Objectives

| ID | Objective | Linked risks | Required evidence |
| --- | --- | --- | --- |
| SECPLAN-001 | Maintain explicit non-clinical boundary until clinical security, privacy, validation and release gates are complete. | RM-009, RM-018, RM-023 | Claims review, integration contract review, release gate |
| SECPLAN-002 | Identify assets, trust boundaries, data flows and security-relevant interfaces for each controlled release. | RM-013, RM-014, RM-015, RM-021, RM-024 | Threat model, architecture review, data-flow review |
| SECPLAN-003 | Define authentication, authorization, session and access-review controls before clinical workflow use. | RM-013, RM-014, RM-021, RM-023 | RBAC test plan, access matrix, user provisioning SOP |
| SECPLAN-004 | Protect data in transit using TLS and production network controls. | RM-013, RM-014, RM-021, RM-024 | Gateway configuration review, TLS scan, deployment checklist |
| SECPLAN-005 | Protect secrets through approved secret storage, rotation and least-privilege access. | RM-013, RM-014, RM-024 | Secrets inventory, rotation record, repo scan |
| SECPLAN-006 | Preserve auditability with request IDs, access events, administrative events and security-relevant system events. | RM-008, RM-017, RM-021, RM-023 | Audit log design, log integrity review, investigation drill |
| SECPLAN-007 | Minimize sensitive data exposure in logs, exports, audit bundles, exceptions and support artifacts. | RM-014, RM-017, RM-021 | PHI-safe logging review, export review, support SOP |
| SECPLAN-008 | Maintain dependency/SOUP inventory, SBOM and vulnerability monitoring for runtime and build dependencies. | RM-004, RM-015 | SOUP register, SBOM, dependency audit evidence |
| SECPLAN-009 | Define vulnerability triage, remediation, update and coordinated disclosure process. | RM-013, RM-015, RM-016, RM-021 | Vulnerability SOP, patch records, disclosure contact/process |
| SECPLAN-010 | Verify backup, restore, downtime and degraded-mode controls before clinical workflow dependency. | RM-012, RM-016, RM-017, RM-024 | Restore test, downtime drill, operational runbook |
| SECPLAN-011 | Require security review for changes affecting API, auth, data model, exports, logs, dependencies or deployment. | RM-013, RM-014, RM-015, RM-018, RM-024 | Change-impact checklist, code review record |
| SECPLAN-012 | Define security testing appropriate to release risk, including auth tests, config tests, dependency scans and abuse-case tests. | RM-013, RM-015, RM-021, RM-024 | Verification records, security test reports |

## Assets

| ID | Asset | Sensitivity | Current control | Gap |
| --- | --- | --- | --- | --- |
| ASSET-001 | Source code and controlled documentation | Integrity-critical | Git and GitHub remote | Branch protection/review rules not documented |
| ASSET-002 | SQLite runtime database | Potentially sensitive if real data is used | Ignored by Git; local prototype only | Production storage and access control not approved |
| ASSET-003 | HLA typing inputs and persisted subject records | Safety/privacy-relevant | Validation and role labels | Source-system provenance and clinical data governance missing |
| ASSET-004 | Reports, comparisons and audit bundles | Safety/privacy-relevant | Deterministic export and audit metadata | Retention, access control and PHI minimization not approved |
| ASSET-005 | API credentials and runtime secrets | Confidential | Example file excludes real secret | Secret vault, rotation and break-glass process missing |
| ASSET-006 | py-ard and IPD-IMGT/HLA data | Safety/reproducibility-critical | Local configured data path and doctor checks | Controlled source/version/change review missing |
| ASSET-007 | Dependency and container stack | Integrity/availability-critical | Declared dependencies and Dockerfile | SBOM and vulnerability monitoring missing |
| ASSET-008 | Backend logs and request IDs | Support/audit-relevant | Structured request logging | PHI-safe logging and retention rules missing |

## Foreseeable Threats And Abuse Cases

| ID | Threat / abuse case | Main impact | Required control |
| --- | --- | --- | --- |
| CYTH-001 | Unauthorized user calls protected report/audit endpoints. | Data exposure, misuse as clinical tool | RBAC, API gateway, access logging |
| CYTH-002 | API key is committed, reused or not rotated. | Unauthorized access | Secret vault, rotation, repo secret scan |
| CYTH-003 | Network traffic is intercepted in production. | Disclosure or manipulation | TLS, HSTS/gateway policy, network segmentation |
| CYTH-004 | Logs or support bundles contain identifiable clinical data. | Privacy breach | PHI-safe logging, minimization, retention |
| CYTH-005 | Dependency vulnerability enables code execution or data exposure. | Security compromise | SBOM, vulnerability monitoring, patch SOP |
| CYTH-006 | Outdated py-ard/IPD-IMGT/HLA data changes output semantics. | Misleading report artifact | Controlled data-source versioning and release review |
| CYTH-007 | Backend is unavailable during time-sensitive workflow. | Workflow delay or unsafe workaround | Downtime SOP, readiness checks, restore test |
| CYTH-008 | Downstream app treats backend artifact as automated clinical approval. | Human oversight bypass | Integration contract, no decision fields, validation |
| CYTH-009 | Admin/deployment misconfiguration points to wrong database/export path. | Wrong data or missing audit evidence | Environment checklist, deployment smoke test |
| CYTH-010 | Error details expose sensitive path/data or hide support-relevant cause. | Privacy/support failure | Structured sanitized errors, request IDs, log review |

## Authentication And Authorization Plan

Current API-key support is acceptable only as a prototype gate. Before clinical workflow use, the larger application must define and verify:

- named users, not shared accounts;
- role-based permissions for viewer, reviewer, admin, support and validation roles;
- least-privilege endpoint access;
- session timeout and reauthentication rules;
- account provisioning, deactivation and periodic access review;
- break-glass access, if allowed, with explicit audit;
- no automated clinical action without qualified human review;
- immutable audit trail for clinical workflow actions owned by the larger app.

The backend component must not become the system of record for clinical authorization until this model is formally designed, implemented, verified and validated.

## Network And Deployment Security Plan

Before production-like or clinical workflow use:

- the backend must sit behind a controlled API gateway or equivalent ingress;
- TLS must be enforced for browser/API traffic;
- CORS must be limited to approved frontend origins;
- database and export paths must be isolated per environment;
- development/demo/staging/production environments must be separated;
- readiness and liveness probes must not disclose sensitive data;
- administrative interfaces, if any, must not be public;
- deployment configuration must be reviewed for each release candidate.

## Secrets Management Plan

Secrets include API keys, future identity-provider secrets, database credentials, signing keys, backup credentials, monitoring tokens and integration credentials.

Minimum controls before clinical workflow use:

- no real secrets in Git;
- secret inventory with owner and purpose;
- approved secret store or deployment-managed secret mechanism;
- rotation frequency and emergency rotation process;
- least-privilege access to secrets;
- audit of secret access where supported;
- documented handling of compromised secrets.

## Logging, Audit And Monitoring Plan

Security-relevant events should include:

- authentication success/failure;
- authorization denial;
- report/comparison/audit request metadata;
- administrative configuration changes;
- export and audit bundle generation;
- readiness failures;
- dependency or vulnerability review decisions;
- backup/restore operations;
- incidents and support interventions.

Logs must avoid storing unnecessary identifiable clinical data. Request IDs should be retained so an investigation can connect user-facing errors, API responses, backend logs and audit artifacts.

## Vulnerability Management Plan

The project should define:

- vulnerability intake source: dependency scanner, GitHub advisories, vendor notices, user reports and security contact;
- severity assessment including patient-safety, privacy, availability and exploitability impact;
- remediation target timelines by severity;
- release-impact and rollback decisions;
- coordinated vulnerability disclosure path;
- post-release communication rules;
- evidence storage for triage and closure.

Critical vulnerabilities affecting auth, data exposure, remote code execution, dependency integrity or report manipulation must block clinical-intended release until fixed or formally risk-accepted.

## Security Verification Plan

Minimum verification before clinical workflow use:

| ID | Verification focus | Expected evidence |
| --- | --- | --- |
| CVER-001 | API auth and authorization behavior | Positive/negative tests for protected endpoints |
| CVER-002 | TLS/gateway and CORS configuration | Deployment checklist and technical scan |
| CVER-003 | Secret handling | Repo scan, config review and rotation drill |
| CVER-004 | PHI-safe logs/errors/exports | Review of logs, error bodies and generated artifacts |
| CVER-005 | Dependency/SBOM monitoring | SBOM artifact and vulnerability report |
| CVER-006 | Backup/restore and downtime | Restore test and downtime simulation |
| CVER-007 | Abuse-case handling | Tests for malformed requests, stale data and access denial |
| CVER-008 | Security change review | Completed change-impact checklist |

## Clinical-Use Blockers

Clinical workflow use remains blocked until:

- cybersecurity owner is assigned;
- threat model is completed and reviewed;
- RBAC and session management are implemented in the larger application;
- TLS/gateway/network segmentation are verified;
- secrets management is implemented;
- PHI-safe logging/export/audit rules are approved;
- SBOM and vulnerability monitoring are operating;
- incident response and coordinated disclosure processes are approved;
- backup/restore and downtime procedures are tested;
- residual cybersecurity risks are reviewed with safety and privacy impact.

## Step 10 Conclusion

This document establishes a planning-level cybersecurity file for the backend component and future larger application boundary. It does not authorize clinical use. The next controlled work should turn these draft controls into approved requirements, security test cases, deployment runbooks and release gates.
