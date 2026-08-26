# Проект На Problem Resolution И CAPA Plan

Статус: Draft за планиране на клинична готовност. Не е одобрен за клинична употреба.

Този документ дефинира начална рамка за software problem resolution, incident handling, complaint intake и corrective/preventive action (CAPA) interface. Той не е approved CAPA procedure, vigilance procedure или regulatory reporting decision tree.

## Цел

Целта е да се дефинира как дефекти, suspected incorrect outputs, security findings, data incidents, user feedback и clinical workflow concerns трябва да се записват, triage-ват, investigate-ват и затварят с evidence.

Problem resolution трябва да бъде свързан с:

- risk management;
- requirements and traceability;
- verification and validation;
- cybersecurity and data governance;
- release/deployment records;
- maintenance planning;
- CAPA and post-release monitoring.

## Изходни Документи

Вътрешни source документи:

- [Български Clinical Readiness Обзор](bg-readiness-overview.md)
- [Quality System Draft](quality-system.md)
- [Risk Management And Initial Risk Register](risk-register.md)
- [Software Lifecycle Draft](software-lifecycle.md)
- [Software Requirements Specification Draft](software-requirements.md)
- [Traceability Matrix Draft](traceability-matrix.md)
- [Verification Plan Draft](verification-plan.md)
- [Validation Plan Draft](validation-plan.md)
- [Cybersecurity Plan Draft](cybersecurity-plan.md)
- [Data Governance Plan Draft](data-governance.md)
- [SOUP And Dependency Register Draft](soup-dependency-register.md)
- [Release And Deployment Plan Draft](release-deployment-plan.md)
- [Maintenance Plan Draft](maintenance-plan.md)
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
- FDA, eMDR - Electronic Medical Device Reporting, updated April 2026:
  https://www.fda.gov/medical-devices/mandatory-reporting-requirements-manufacturers-importers-and-device-user-facilities/emdr-electronic-medical-device-reporting
- FDA, Medical Device Reporting: How to Report Medical Device Problems:
  https://www.fda.gov/medical-devices/medical-device-safety/medical-device-reporting-mdr-how-report-medical-device-problems
- FDA, Postmarket Surveillance Under Section 522 of the FD&C Act:
  https://www.fda.gov/regulatory-information/search-fda-guidance-documents/postmarket-surveillance-under-section-522-federal-food-drug-and-cosmetic-act
- European Commission MDCG guidance index, including PMS/vigilance and CAPA templates:
  https://health.ec.europa.eu/medical-devices-sector/new-regulations/guidance-mdcg-endorsed-documents-and-other-guidance_en

## Scope

Current scope:

- non-clinical defects and documentation issues;
- backend/API/frontend prototype anomalies;
- deterministic output discrepancies found during testing;
- security or dependency findings;
- data-governance concerns involving local/demo artifacts.

Future clinical-intended scope, if approved:

- complaints and suspected device problems;
- suspected incorrect outputs in clinical workflow;
- user-interface use errors and near misses;
- security vulnerabilities and data incidents;
- deployment, availability and rollback incidents;
- regulatory reporting evaluation by qualified roles;
- CAPA initiation, effectiveness checks and management review.

## Problem Resolution Controls

| ID | Control | Linked risk areas | Evidence needed |
| --- | --- | --- | --- |
| PROB-001 | Every anomaly or complaint must receive a unique record ID. | AUD, OPS, VAL | Problem record |
| PROB-002 | Record affected version, commit, environment and request ID when available. | AUD, OPS | Investigation evidence |
| PROB-003 | Preserve enough data to reproduce the issue without uncontrolled PHI exposure. | DATA, SEC, AUD | Reproduction package review |
| PROB-004 | Classify safety, security, privacy, regulatory and availability impact. | RM-013, RM-014, RM-016, RM-021 | Triage record |
| PROB-005 | Link affected requirements, risks, architecture, verification and validation items. | RM-006, RM-008, RM-018 | Traceability update |
| PROB-006 | Determine containment action before root-cause work when urgent risk exists. | RM-016, RM-017, RM-024 | Containment record |
| PROB-007 | Determine whether CAPA is required based on recurrence, severity or systemic cause. | QMS, RM | CAPA decision |
| PROB-008 | Determine whether regulatory/vigilance reporting evaluation is required. | REG, PMS | Regulatory assessment |
| PROB-009 | Verify fixes with regression tests or documented review. | VAL, OPS | Verification evidence |
| PROB-010 | Assess validation/usability impact for user-facing or clinical workflow issues. | RM-010, RM-020, RM-025 | Validation impact record |
| PROB-011 | Update release notes, known issues and user communication where needed. | OPS, REG | Communication record |
| PROB-012 | Close records only after evidence review and approval. | QMS | Closure approval |
| PROB-013 | Trend problem records for recurring issues. | PMS, CAPA | Trend review |
| PROB-014 | Feed serious or recurring issues back into risk management. | RM | Risk-file update |

## Triage Classes

| ID | Class | Description | Minimum action |
| --- | --- | --- | --- |
| TRI-001 | Documentation issue | Wording, navigation or non-functional documentation defect | Documentation fix and review |
| TRI-002 | Non-safety software defect | Incorrect behavior without safety/security/privacy impact | Bug fix and regression test |
| TRI-003 | Safety-related output defect | Incorrect, missing, stale or misleading report/comparison output | Containment, risk review, fix verification |
| TRI-004 | Use error or usability issue | User misunderstands workflow, warning, sort order or boundary | Usability review and validation impact |
| TRI-005 | Security vulnerability | Auth, dependency, config, logging or exposure weakness | Security triage and vulnerability process |
| TRI-006 | Data/privacy incident | Real data exposure, uncontrolled export/log, wrong provenance | Data incident process and privacy review |
| TRI-007 | Availability/deployment incident | Readiness, migration, rollback, downtime or environment failure | Operations triage and deployment review |
| TRI-008 | Regulatory/complaint concern | Issue may meet complaint, vigilance or reporting criteria | Regulatory/quality evaluation |

## CAPA Controls

| ID | Control | Evidence |
| --- | --- | --- |
| CAPA-001 | Define CAPA initiation criteria for systemic, recurring, severe or regulatory-significant issues. | CAPA procedure |
| CAPA-002 | Record source of CAPA: complaint, audit, validation deviation, security issue, data incident or management review. | CAPA record |
| CAPA-003 | Perform root-cause analysis using documented method. | Root-cause record |
| CAPA-004 | Define corrective action that removes or controls the identified cause. | Corrective action plan |
| CAPA-005 | Define preventive action when process weakness could recur. | Preventive action plan |
| CAPA-006 | Link CAPA to affected risks, requirements, design, verification and validation. | Traceability update |
| CAPA-007 | Verify implementation of actions. | Verification evidence |
| CAPA-008 | Check effectiveness after appropriate time or data threshold. | Effectiveness check |
| CAPA-009 | Escalate unresolved or ineffective CAPA to management review. | Management review input |
| CAPA-010 | Assess need for field action, user communication or regulatory reporting. | Regulatory/communication assessment |
| CAPA-011 | Preserve CAPA records for required retention period. | Record retention evidence |
| CAPA-012 | Close CAPA only with quality approval. | Closure approval |

## Regulatory/Vigilance Interface

This draft does not decide whether an issue is reportable. Before clinical-intended or marketed use, a qualified regulatory/quality role must define jurisdiction-specific decision trees for:

- EU MDR/IVDR vigilance and PMS obligations;
- FDA MDR/eMDR obligations if a US route applies;
- serious incident, field safety corrective action, recall or advisory notices;
- cybersecurity vulnerability communication;
- data-protection incident notification;
- hospital/institutional reporting obligations.

For planning only, any suspected incorrect output, data breach, security vulnerability, serious workflow delay, or user-interface issue that could contribute to patient harm must be escalated for regulatory/quality assessment.

## Problem Record Template

Each problem record should include:

- problem ID;
- title;
- reporter and date;
- source: user, test, audit, validation, monitoring, security, data incident;
- affected version/commit/environment;
- request ID, report ID, batch ID or audit bundle ID if available;
- description and reproduction steps;
- expected vs actual result;
- screenshots/log snippets only if PHI-safe and approved;
- safety/security/privacy/regulatory classification;
- linked risks, requirements and tests;
- containment action;
- root cause or investigation status;
- corrective action;
- verification evidence;
- validation/usability impact decision;
- release impact and user communication decision;
- closure approver and date.

## CAPA Record Template

Each CAPA record should include:

- CAPA ID;
- linked problem IDs;
- trigger and initiation rationale;
- owner and due date;
- root-cause analysis;
- corrective action plan;
- preventive action plan;
- implementation evidence;
- verification of implementation;
- effectiveness-check method and date;
- affected controlled documents;
- affected release/version;
- regulatory/user communication assessment;
- closure approval.

## Escalation And Containment Draft

Immediate containment may include:

- disabling a feature or endpoint;
- withdrawing a release candidate;
- blocking clinical-intended deployment;
- adding a known-issue notice;
- requiring manual review before continued use;
- reverting a dependency, data-source or deployment change;
- revoking or rotating credentials;
- isolating logs, exports or audit bundles;
- initiating backup/restore or rollback.

Containment actions must be documented and followed by root-cause investigation.

## Clinical-Use Blockers

Clinical workflow use remains blocked until:

- problem-resolution owner is assigned;
- issue tracker or controlled record system is selected;
- CAPA initiation criteria are approved;
- regulatory/vigilance reporting decision tree is approved;
- data incident and cybersecurity vulnerability workflows are connected;
- effectiveness-check method is defined;
- trend review and management-review cadence are defined;
- staff responsibilities and training are documented.

## Step 11 Conclusion

This document establishes a planning-level problem-resolution and CAPA interface. The Step 12 baseline package now defines owner, approval, claims and gate controls that must govern problem/CAPA records. It does not implement a certified CAPA system or regulatory reporting workflow.
