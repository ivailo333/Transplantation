# Проект На SOUP И Dependency Register

Статус: Draft за планиране на клинична готовност. Не е одобрен за клинична употреба.

Този документ започва Software of Unknown Provenance (SOUP), third-party dependency и supplier register за HLA Transplantation Simulation проекта. Той не е завършен SBOM, не доказва dependency safety/security и не замества supplier qualification или vulnerability-management process.

## Цел

Целта е да се опишат текущите third-party software, data и platform dependencies, тяхната употреба, risk relevance, текущ controls и evidence gaps преди controlled release.

SOUP/dependency records трябва да бъдат linked към:

- software lifecycle;
- cybersecurity plan;
- data-governance plan;
- risk register;
- verification plan;
- release checklist;
- maintenance and vulnerability management.

## Изходни Документи

Вътрешни source документи:

- [Български Clinical Readiness Обзор](bg-readiness-overview.md)
- [Risk Management And Initial Risk Register](risk-register.md)
- [Software Requirements Specification Draft](software-requirements.md)
- [Traceability Matrix Draft](traceability-matrix.md)
- [Software Architecture Draft](software-architecture.md)
- [Verification Plan Draft](verification-plan.md)
- [Cybersecurity Plan Draft](cybersecurity-plan.md)
- [Data Governance Plan Draft](data-governance.md)
- [Backend API Component](../backend.md)
- [Backend Integration Guide](../backend-integration.md)
- [Data Policy](../data.md)
- [Release And Deployment Plan Draft](release-deployment-plan.md)
- [Maintenance Plan Draft](maintenance-plan.md)
- [Problem Resolution And CAPA Plan Draft](problem-resolution-capa.md)
- [Document Control Index Draft](document-control-index.md)
- [Approval Matrix Draft](approval-matrix.md)
- [Claims Control Matrix Draft](claims-control-matrix.md)
- [Change Impact Checklist Draft](change-impact-checklist.md)
- [Clinical Readiness Gate Checklist Draft](clinical-readiness-gate-checklist.md)
- [`pyproject.toml`](../../pyproject.toml)
- [`requirements.txt`](../../requirements.txt)
- [`requirements-api.txt`](../../requirements-api.txt)
- [`Dockerfile`](../../Dockerfile)

Официални външни references, проверени на 2026-08-26:

- IEC 62304:2006, Medical device software - software life cycle processes:
  https://committee.iso.org/standard/38421.html
- FDA, Off-The-Shelf Software Use in Medical Devices, final guidance, August 2023:
  https://www.fda.gov/regulatory-information/search-fda-guidance-documents/shelf-software-use-medical-devices
- FDA, Cybersecurity in Medical Devices: Quality Management System Considerations and Content of Premarket Submissions, final guidance, February 2026:
  https://www.fda.gov/regulatory-information/search-fda-guidance-documents/cybersecurity-medical-devices-quality-management-system-considerations-and-content-premarket
- IMDRF/CYBER WG/N73, Principles and Practices for Software Bill of Materials for Medical Device Cybersecurity:
  https://www.imdrf.org/documents/principles-and-practices-software-bill-materials-medical-device-cybersecurity
- NIST SP 800-218, Secure Software Development Framework:
  https://csrc.nist.gov/pubs/sp/800/218/final

## Definitions

| Term | Working definition |
| --- | --- |
| SOUP | Software or data used in the product without full internal development control. |
| Dependency | Runtime, build, test, data or platform component needed to develop, run, verify or package the project. |
| Supplier | External maintainer, package ecosystem, hosting provider, data provider or platform operator relevant to a dependency. |
| SBOM | Structured inventory of software components, versions, suppliers and relationships for a release. |

## Current Register

Exact resolved versions are not baselined in this draft. A controlled release must capture installed versions, hashes where practical, license data, vulnerability status and source location.

| ID | Component | Declared source | Use in project | Risk relevance | Current control | Evidence gap |
| --- | --- | --- | --- | --- | --- | --- |
| SOUP-001 | Python runtime | `requires-python >=3.10`; Docker uses `python:3.12-slim` | CLI, backend, tests and packaging | Runtime behavior, security updates, Unicode/IO behavior | Version constraint and Docker base image | Release-specific Python version and vulnerability review |
| SOUP-002 | py-ard | `py-ard>=2.3.1` | HLA allele validation and reduction support | Output semantics and reference-data interpretation | Declared dependency and doctor checks | Version lock, supplier/source review, update impact record |
| SOUP-003 | IPD-IMGT/HLA / py-ard data | `pyard-data/` configured local data | Reference data for validation/reduction | Stale or mismatched HLA nomenclature may alter outputs | Local data path and data policy | Version provenance, checksum, update review |
| SOUP-004 | SQLite | Python standard library `sqlite3` and local `.db` files | Persistence for subjects, typings, analyses and batch history | Data integrity, migrations, concurrency limits | Migration/status tests | Production database decision and backup/restore evidence |
| SOUP-005 | FastAPI | `fastapi>=0.115` optional API dependency | HTTP API framework | Request validation, error handling, OpenAPI, dependency vulnerabilities | API tests and dependency declaration | Exact version, vulnerability monitoring, compatibility review |
| SOUP-006 | Pydantic | Transitive through FastAPI | Request/response model validation | Validation behavior and error details | API tests | Exact version and behavior-change review |
| SOUP-007 | Starlette | Transitive through FastAPI | ASGI routing/middleware layer | HTTP/security behavior and dependency vulnerabilities | API tests | Exact version and security advisory monitoring |
| SOUP-008 | Uvicorn | `uvicorn[standard]>=0.30` optional API dependency | Local/backend ASGI server | Availability, HTTP behavior, production suitability | Declared dependency | Production server/gateway decision and vulnerability review |
| SOUP-009 | uvicorn standard extras | Transitive optional packages | Performance/watch/HTTP/WebSocket support as installed | Attack surface may vary by resolved environment | Not individually controlled | SBOM and release-specific package inventory |
| SOUP-010 | setuptools | `setuptools>=69` build-system dependency | Build backend | Build integrity and packaging behavior | Declared build dependency | Build environment record and vulnerability review |
| SOUP-011 | wheel | `wheel` build-system dependency | Build artifact generation | Build integrity | Declared build dependency | Build artifact provenance |
| SOUP-012 | build | `build>=1.2` dev dependency | Local/source and wheel build | Build reproducibility | Declared dev dependency | Release build procedure and pinned version |
| SOUP-013 | httpx | `httpx>=0.27` dev dependency | Backend/API tests | Test reliability, not runtime clinical dependency | Declared dev dependency and tests | Test environment version capture |
| SOUP-014 | pytest | `pytest>=8.0` dev dependency | Optional test runner | Test reliability, not runtime clinical dependency | Declared dev dependency | Test environment version capture |
| SOUP-015 | GitHub Actions hosted runner | `.github/workflows/ci.yml` | CI checks on Windows | Build/test integrity and supply-chain reliance | CI workflow | Branch protection, workflow pinning and artifact retention |
| SOUP-016 | Docker base image | `python:3.12-slim` | Backend container packaging | OS/library vulnerabilities and runtime behavior | Dockerfile | Digest pinning, image scan and update policy |
| SOUP-017 | Browser runtime | User browser for static frontend prototype | UI execution | Browser compatibility and privacy behavior | Static HTML/JS/CSS, local prototype only | Supported browser matrix and frontend validation |
| SOUP-018 | Future identity provider | Planned external component | Authentication, RBAC, sessions | Unauthorized access if misconfigured | Not selected | Supplier qualification and integration tests |
| SOUP-019 | Future LIS/EHR/FHIR/HL7 libraries | Planned external components | Clinical data integration | Data provenance, transformation and dependency risk | Not selected | Supplier qualification and interface validation |
| SOUP-020 | Future hosting/logging/backup providers | Planned external services | Deployment operations | Availability, confidentiality, retention and incident response | Not selected | Supplier risk review and contracts |

## Minimum Fields For Controlled SOUP Records

Each controlled SOUP/dependency entry should include:

- unique ID;
- component name;
- supplier/maintainer;
- source URL or repository;
- exact version;
- package hash or image digest where practical;
- license;
- intended use;
- runtime/build/test/data classification;
- safety, security and privacy relevance;
- known limitations;
- vulnerability status;
- update policy;
- verification impact;
- validation impact;
- fallback or mitigation strategy;
- owner and review date.

## SBOM Plan

Before controlled release:

- generate an SBOM for Python packages and container image contents where practical;
- include direct and transitive dependencies;
- store SBOM as a release artifact;
- link SBOM to release commit/tag and verification run;
- review known vulnerabilities before release approval;
- record accepted vulnerabilities with rationale, compensating controls and expiration date;
- update SBOM when dependencies or base images change.

## Dependency Update Policy Draft

| Change type | Review expectation |
| --- | --- |
| Patch update with no known behavior impact | Dependency review, automated tests, vulnerability check |
| Minor update | Dependency review, automated tests, targeted behavior review |
| Major update | Change-impact assessment, requirements/design review, regression tests |
| Security update | Vulnerability triage, expedited tests, release-impact decision |
| py-ard or HLA reference-data update | Output comparison review, report metadata review, validation impact assessment |
| Docker base image update | Image scan, smoke tests, deployment review |
| Auth/provider dependency update | Security review, auth tests, access-control regression |

## Vulnerability Monitoring Plan

Monitoring sources should include:

- package ecosystem advisories;
- GitHub Dependabot or equivalent;
- vulnerability scanner reports;
- FDA/IMDRF medical-device cybersecurity guidance updates;
- supplier release notes;
- hospital/provider security bulletins if deployed in healthcare environment.

Vulnerability triage must assess:

- exploitability;
- patient-safety impact;
- privacy impact;
- availability impact;
- affected versions;
- exposed deployment configurations;
- workaround availability;
- patch availability;
- need for user/customer communication.

## Supplier Review Draft

Suppliers and external components should be reviewed for:

- intended use fit;
- maintenance activity and release history;
- security advisory process;
- license compatibility;
- documented support or community maturity;
- availability and exit strategy;
- data-processing role if the supplier handles health data;
- impact on validation, verification and regulatory evidence.

Future clinical deployment must not add hosting, identity, logging, backup or integration suppliers without privacy, security, quality and regulatory review.

## Release Gate

A release candidate should not be considered clinical-intended unless:

- SOUP register is updated;
- SBOM is generated and reviewed;
- dependency vulnerabilities are triaged;
- base image vulnerabilities are reviewed;
- py-ard/IPD-IMGT/HLA source-data version is recorded;
- dependency changes are linked to verification and validation impact;
- accepted dependency risks have owner and expiry/review date;
- release record includes dependency/SOUP approval.

## Clinical-Use Blockers

Clinical workflow use remains blocked until:

- controlled SOUP register is baselined;
- exact dependency versions are locked or otherwise justified;
- SBOM process is implemented;
- vulnerability monitoring is operating;
- update/patch process is approved;
- suppliers for auth, hosting, logging, backup and integrations are qualified;
- dependency changes are integrated with risk, verification, validation and release records.

## Step 10 Conclusion

This document establishes the first SOUP/dependency register for the project. It identifies current runtime, API, build, test, data and future supplier dependencies, but it does not replace a release-specific SBOM or supplier qualification process.
