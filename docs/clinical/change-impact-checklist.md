# Проект На Change Impact Checklist

Статус: Draft за controlled-baseline planning. Не е одобрен QMS form и не разрешава клинична употреба.

Този документ дефинира начална change-impact checklist форма за промени по HLA Transplantation Simulation проекта. Тя трябва да се използва преди baseline или release decisions, когато промяна може да засегне intended use, claims, requirements, risk, validation, cybersecurity, data governance, SOUP/dependencies, release или clinical workflow.

## Цел

Целта е всяка значима промяна да бъде оценена преди merge/release, вместо impact analysis да се прави постфактум.

Този checklist е draft template. Реален controlled process изисква owner, approval route, record storage и enforcement в branch/release workflow.

## Изходни Документи

- [Document Control Index Draft](document-control-index.md)
- [Approval Matrix Draft](approval-matrix.md)
- [Claims Control Matrix Draft](claims-control-matrix.md)
- [Clinical Readiness Gate Checklist Draft](clinical-readiness-gate-checklist.md)
- [Quality System Draft](quality-system.md)
- [Risk Management And Initial Risk Register](risk-register.md)
- [Software Requirements Specification Draft](software-requirements.md)
- [Traceability Matrix Draft](traceability-matrix.md)
- [Release And Deployment Plan Draft](release-deployment-plan.md)
- [Maintenance Plan Draft](maintenance-plan.md)
- [Problem Resolution And CAPA Plan Draft](problem-resolution-capa.md)

Официални външни references, проверени на 2026-08-26:

- ISO 13485:2016, Medical devices - quality management systems:
  https://www.iso.org/standard/59752.html
- IEC 62304:2006+AMD1:2015, Medical device software - software life cycle processes:
  https://webstore.iec.ch/en/publication/22794
- ISO 14971:2019, Medical devices - application of risk management:
  https://www.iso.org/standard/72704.html
- FDA Quality Management System Regulation (QMSR):
  https://www.fda.gov/medical-devices/postmarket-requirements-devices/quality-management-system-regulation-qmsr
- MDCG 2019-11 rev.1, software qualification and classification:
  https://health.ec.europa.eu/latest-updates/update-mdcg-2019-11-rev1-qualification-and-classification-software-regulation-eu-2017745-and-2025-06-17_en

## Change Impact Controls

| ID | Control | Required output |
| --- | --- | --- |
| IMPACT-001 | Identify change type, owner and affected files/documents. | Change record |
| IMPACT-002 | Assess intended-use impact. | Intended-use decision |
| IMPACT-003 | Assess claims and labeling impact. | Claims matrix update or no-impact rationale |
| IMPACT-004 | Assess regulatory classification impact. | Regulatory review decision |
| IMPACT-005 | Assess risk-management impact. | Risk update or no-impact rationale |
| IMPACT-006 | Assess requirements and traceability impact. | Updated links or no-impact rationale |
| IMPACT-007 | Assess architecture/design impact. | Design update or no-impact rationale |
| IMPACT-008 | Assess verification impact. | Test plan/update decision |
| IMPACT-009 | Assess validation/usability impact. | Validation/usability decision |
| IMPACT-010 | Assess cybersecurity impact. | Security review decision |
| IMPACT-011 | Assess data-governance/privacy impact. | Data review decision |
| IMPACT-012 | Assess SOUP/dependency/SBOM impact. | SOUP/SBOM update decision |
| IMPACT-013 | Assess release/deployment/rollback impact. | Release/deployment decision |
| IMPACT-014 | Assess maintenance/problem/CAPA impact. | Problem/CAPA link decision |
| IMPACT-015 | Identify required approvers before merge or release. | Approval matrix link |
| IMPACT-016 | Record residual open issues, deviations and blockers. | Release/gate impact |

## Change Record Header

| Field | Value |
| --- | --- |
| Change ID | TBD |
| Title | TBD |
| Requester | TBD |
| Owner | TBD |
| Date opened | TBD |
| Target release or baseline | TBD |
| Affected commit/branch | TBD |
| Change type | TBD |
| Emergency change | Yes/No/TBD |
| Clinical-intended impact | Yes/No/TBD |
| Real or pseudonymized health data impact | Yes/No/TBD |

## Change Type Checklist

Select all that apply:

- documentation-only;
- claims or labeling;
- intended-use change;
- software logic;
- API contract;
- database/migration;
- frontend workflow;
- report/export/audit artifact;
- dependency/SOUP;
- HLA reference data;
- cybersecurity;
- data governance/privacy;
- deployment/configuration;
- maintenance/problem/CAPA;
- regulatory route;
- validation/usability evidence.

## Impact Questions

| Area | Question | Blocks release if unresolved |
| --- | --- | --- |
| Intended use | Does this change alter current or future intended use? | Yes |
| Claims | Could this imply clinical compatibility, recommendation, suitability or approval? | Yes |
| Regulatory | Could this change device/software classification or route? | Yes |
| Risk | Does this add, remove or change risk controls? | Yes |
| Requirements | Are requirements added, changed or retired? | Yes |
| Traceability | Are links to risks/design/tests/validation updated? | Yes |
| Architecture | Does this alter components, trust boundaries, interfaces or data flows? | Yes |
| Verification | Are new or changed tests required? | Yes |
| Validation | Does workflow/user interpretation or representative dataset evidence change? | Yes |
| Usability | Does user task, warning, wording or visual interpretation change? | Yes |
| Cybersecurity | Does auth, secrets, logs, network, dependency or vulnerability posture change? | Yes |
| Data governance | Does it affect identifiers, retention, exports, logs, backups or validation datasets? | Yes |
| SOUP | Does it change runtime/build/test/data dependencies or reference data? | Yes |
| Deployment | Does it affect environment configuration, migration, rollback or downtime? | Yes |
| CAPA | Is the change corrective/preventive action or linked to a recurring issue? | Yes |

## Required Evidence By Impact

| Impact type | Minimum evidence |
| --- | --- |
| Documentation-only | Document review and link check |
| Claims/labeling | Claims matrix update and regulatory/clinical/quality approval |
| Software logic | Code review, unit/integration tests and risk review |
| API contract | API contract tests, integration guide update and downstream impact review |
| Database/migration | Migration tests, backup/restore review and rollback decision |
| Frontend workflow | Usability review, visual/text review and validation impact decision |
| Cybersecurity | Security review, abuse-case tests, vulnerability/SBOM impact |
| Data governance | Privacy/data review, retention/access impact, artifact review |
| SOUP/dependency | SOUP register update, SBOM/vulnerability review, regression tests |
| Release/deployment | Release checklist, deployment runbook and smoke checks |
| CAPA/problem | Problem/CAPA record, root cause, corrective action and effectiveness plan |

## Approval Routing

Use [Approval Matrix Draft](approval-matrix.md) to determine approvers. As a minimum:

- claims changes require clinical, regulatory and quality review;
- security/data changes require security/data and quality review;
- safety-related software changes require software, quality and clinical/validation review;
- release/deployment changes require operations, software, quality and security/data review;
- CAPA closure requires quality approval.

## Change Decision Values

| Decision | Meaning |
| --- | --- |
| No impact | Documented rationale shows no affected controlled area. |
| Impact accepted | Impact exists and required evidence/approval is complete. |
| Impact pending | Required evidence or approval is incomplete. |
| Release blocker | Change cannot be merged/released under current state. |
| Deferred | Change moved out of current baseline/release scope. |
| Emergency accepted | Temporary expedited decision with follow-up CAPA/review required. |

## Clinical-Use Blockers

Clinical workflow use remains blocked until:

- change-impact checklist is approved;
- change categories and approval routing are enforced;
- branch/release workflow requires completed impact records;
- claims, risk, validation, cybersecurity and data impacts cannot bypass review;
- emergency change process is documented and rehearsed.

## Step 12 Conclusion

This checklist defines draft impact-analysis questions and routing. It does not implement a controlled change-management system by itself.
