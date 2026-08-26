# Проект На Approval Matrix

Статус: Draft за controlled-baseline planning. Не е одобрен approval record и не разрешава клинична употреба.

Този документ дефинира начална owners/approvers matrix за clinical-readiness документите, software changes, release decisions и бъдеща clinical-readiness gate оценка. Имената на реални хора/институции не са зададени; всички роли са placeholders до формално назначаване.

## Цел

Целта е да се отдели who prepares, who reviews и who approves за критичните решения преди проектът да се разширява към clinical-intended workflow.

Нито един developer commit не може сам по себе си да одобри clinical claims, clinical release, identifiable-data processing или donor-situation use.

## Изходни Документи

- [Document Control Index Draft](document-control-index.md)
- [Claims Control Matrix Draft](claims-control-matrix.md)
- [Change Impact Checklist Draft](change-impact-checklist.md)
- [Clinical Readiness Gate Checklist Draft](clinical-readiness-gate-checklist.md)
- [Quality System Draft](quality-system.md)
- [Risk Management And Initial Risk Register](risk-register.md)
- [Software Lifecycle Draft](software-lifecycle.md)
- [Release And Deployment Plan Draft](release-deployment-plan.md)
- [Problem Resolution And CAPA Plan Draft](problem-resolution-capa.md)

Официални външни references, проверени на 2026-08-26:

- ISO 13485:2016, Medical devices - quality management systems:
  https://www.iso.org/standard/59752.html
- FDA Quality Management System Regulation (QMSR):
  https://www.fda.gov/medical-devices/postmarket-requirements-devices/quality-management-system-regulation-qmsr
- MDCG 2019-7 rev.1, guidance on PRRC:
  https://health.ec.europa.eu/latest-updates/update-mdcg-2019-7-rev1-guidance-article-15-medical-device-regulation-mdr-and-vitro-diagnostic-2023-12-19_en
- MDCG guidance index:
  https://health.ec.europa.eu/medical-devices-sector/new-regulations/guidance-mdcg-endorsed-documents-and-other-guidance_en

## Approval Controls

| ID | Control | Current status |
| --- | --- | --- |
| APPR-001 | Each controlled document shall have a single owner role. | Drafted |
| APPR-002 | Each controlled document shall have required approver roles before baseline. | Drafted |
| APPR-003 | Clinical claims require clinical, regulatory and quality approval. | Drafted |
| APPR-004 | Risk acceptability requires quality, clinical and technical approval. | Drafted |
| APPR-005 | Software release requires quality, software, validation and operations approval. | Drafted |
| APPR-006 | Clinical-intended release requires clinical, regulatory, quality, software, security/data and operations approval. | Drafted |
| APPR-007 | Identifiable or pseudonymized health-data use requires security/data, quality, regulatory and institutional approval. | Drafted |
| APPR-008 | Cybersecurity residual risk acceptance requires security/data, quality and software approval. | Drafted |
| APPR-009 | SOUP/dependency risk acceptance requires software, security/data and quality approval. | Drafted |
| APPR-010 | Validation protocol/report approval requires validation, clinical, quality and regulatory approval. | Drafted |
| APPR-011 | Usability validation approval requires usability/validation, clinical and quality approval. | Drafted |
| APPR-012 | CAPA closure requires quality approval and owner evidence. | Drafted |
| APPR-013 | Emergency hotfix release requires expedited but documented approval by quality, software and relevant risk owner. | Drafted |
| APPR-014 | Approval conflicts or missing owners block clinical-readiness gate completion. | Drafted |

## Role Matrix

| Role | Owns | Reviews | Approves |
| --- | --- | --- | --- |
| Product owner | product scope, roadmap, release intent | claims, user needs, release package | non-clinical release scope, product priorities |
| Clinical lead | clinical workflow assumptions | intended use, risks, validation, usability, labels | clinical assumptions and clinical-readiness gate |
| Regulatory lead | regulatory route, claims control | classification, labeling, PMS/vigilance, submissions | claims, route, regulatory gate |
| Quality lead | QMS process, document control, CAPA | all controlled records and release evidence | baseline package, release record, CAPA closure |
| Software lead | architecture, implementation, code review | requirements, verification, SOUP, maintenance | software technical readiness |
| Verification lead | verification protocol and report | requirements, test evidence, deviations | verification completion |
| Validation lead | validation protocol and report | validation dataset, workflow, usability evidence | validation completion |
| Security/data lead | cybersecurity, privacy, data governance | threat model, logs, SBOM, retention, access | security/data readiness |
| Operations lead | deployment, monitoring, rollback, support | release/deployment plan, downtime, backup/restore | operational readiness |
| PRRC candidate | regulatory compliance oversight if applicable | conformity and regulatory records | as defined by legal/regulatory route |

## Document Approval Matrix

| Document group | Owner | Required approvers before controlled baseline |
| --- | --- | --- |
| Intended use and claims | Product owner | Clinical, regulatory, quality |
| Regulatory classification | Regulatory lead | Clinical, quality, product |
| Quality system and document control | Quality lead | Regulatory, product, software |
| Risk management file | Quality lead | Clinical, software, security/data |
| Requirements and traceability | Software lead / validation lead | Clinical, quality, validation, security/data |
| Architecture and design | Software lead | Security/data, quality, validation |
| Verification plan/report | Verification lead | Software, quality, security/data |
| Validation plan/report | Validation lead | Clinical, quality, regulatory |
| Usability engineering file | Validation lead | Clinical, quality, regulatory |
| Cybersecurity and data governance | Security/data lead | Software, quality, regulatory |
| SOUP/dependency register | Software lead | Security/data, quality |
| Release/deployment records | Operations lead | Quality, software, validation, security/data |
| Maintenance/problem/CAPA records | Quality lead / software lead | Quality, regulatory, software, security/data |
| Clinical-readiness gate | Quality lead | Clinical, regulatory, software, validation, security/data, operations |

## Decision Approval Matrix

| Decision | Required approval | Blocks clinical use if missing |
| --- | --- | --- |
| Freeze intended use | Product, clinical, regulatory, quality | Yes |
| Approve clinical claims | Clinical, regulatory, quality | Yes |
| Approve risk acceptability | Quality, clinical, software/security as relevant | Yes |
| Approve validation protocol | Validation, clinical, quality, regulatory | Yes |
| Approve validation report | Validation, clinical, quality, regulatory | Yes |
| Approve cybersecurity residual risks | Security/data, quality, software | Yes |
| Approve data-governance route | Security/data, quality, regulatory, institution | Yes |
| Approve SOUP/SBOM review | Software, security/data, quality | Yes |
| Approve release candidate | Quality, software, validation, security/data, operations | Yes |
| Approve clinical pilot | Clinical, regulatory, quality, software, security/data, operations | Yes |
| Close CAPA | Quality plus responsible owner | Yes when safety/security/quality related |

## Current Assignment State

All roles are `TBD`. The current repository has planning documents only. Before any clinical-intended development or pilot:

- named role holders must be assigned;
- authority boundaries must be documented;
- conflicts of interest must be handled;
- approval records must be stored in a controlled system;
- fallback delegates must be identified;
- approvals must be linked to document versions and commits.

## Step 12 Conclusion

This approval matrix defines required responsibilities for controlled baseline planning. It does not assign real accountable individuals and does not approve clinical use.
